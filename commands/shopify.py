import requests
import time
from datetime import datetime, timedelta, timezone
from tokens import SHOPIFY_TOKEN, SHOPIFY_CLIENT_ID
import state as state
from order_management import SHOPIFY_ALIASES, ETSY_ALIASES
import commands.etsy as etsy
from commands.jobs import addjob
import asyncio
import aiohttp
import commands.stock as stock

SHOP = "threestools.myshopify.com"
TOKEN = SHOPIFY_TOKEN
CLIENT_ID = SHOPIFY_CLIENT_ID
POLL_INTERVAL = 600
ORDERS_FETCH_LIMIT = 50

ACCESS_TOKEN = ""
TOKEN_EXPIRY = datetime.now(timezone.utc)

def generate_access_token():
    global ACCESS_TOKEN, TOKEN_EXPIRY
    try:
        response = requests.post(
            f"https://{SHOP}/admin/oauth/access_token",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "client_credentials",
                "client_id": CLIENT_ID,
                "client_secret": TOKEN
            }
        )
        response.raise_for_status()
        ACCESS_TOKEN = response.json()["access_token"]
        TOKEN_EXPIRY = datetime.now(timezone.utc) + timedelta(hours=24) - timedelta(minutes=5)
        return True
        
    except Exception as e:
        print(f"Failed to generate access token: {e}")
        return False


async def get_valid_access_token():
    global ACCESS_TOKEN, TOKEN_EXPIRY
    while (not ACCESS_TOKEN or datetime.now(timezone.utc) >= TOKEN_EXPIRY):
        success = generate_access_token()
        if not success:
            await asyncio.sleep(5)
            
    print("Token generated successfully")

def get_current_time():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

async def shopify_post(url, headers, query, retries=3, delay=5):
    async with aiohttp.ClientSession() as session:
        for attempt in range(retries):
            try:
                async with session.post(url, headers=headers, json=query, timeout=10) as response:
                    response.raise_for_status()
                    data = await response.json()
                    if not data:
                        raise ValueError("Empty response from server")
                    return data
            
            except (aiohttp.ClientError, ValueError) as e:
                print(f"Attempt {attempt+1} failed: {e}")
                await asyncio.sleep(delay)
                
        print("Failed to fetch data after retries")
        return None

def update_stock(design_name, glossy, name_list, quantity):
    stock_available = False
    if design_name == "Knobs & Switches":
        knob_available = False
        switch_available = False
        knob_colour = name_list[1]
        parts_list = name_list[0][2:].split(" + ")
        knob_name = f"Knob - {knob_colour}"
        switch_name = f"Switch - {knob_colour}"
        if len(parts_list) == 2:
            knob_quantity = int(name_list[0][0])
            knob_available = stock.check_stock(knob_name, quantity*knob_quantity)[0]
            switch_available = stock.check_stock(switch_name)[0]
            if knob_available and switch_available:
                stock_available = True
                stock.update_stock(knob_name, quantity*knob_quantity)
                stock.update_stock(switch_name, quantity)
        else:
            if parts_list[0] in ("Knob", "Knobs"):
                knob_quantity = int(name_list[0][0])
                knob_available = stock.check_stock(knob_name, quantity*knob_quantity)[0]
                if knob_available:
                    stock_available = True
                    stock.update_stock(knob_name, knob_quantity*quantity)
            else:
                switch_available = stock.check_stock(switch_name, quantity)[0]
                if switch_available:
                    stock_available = True
                    stock.update_stock(switch_name, quantity)
    else:
        item_code = stock.generate_code(name_list)
        stock.update_frequency(item_code)
        if not glossy:
            if stock.check_stock(item_code, quantity)[0]:
                stock_available = True
                stock.update_stock(item_code, quantity)
        else:
            name_list.append("Glossy")
            item_code_glossy = stock.generate_code(name_list)
            if stock.check_stock(item_code_glossy, quantity)[0]:
                stock_available = True
                stock.update_stock(item_code_glossy, quantity)
            elif stock.check_stock(item_code, quantity)[0]:
                stock_available = True
                stock.update_stock(item_code, quantity)
                
    status = "Received"
    if stock_available:
        status = "Printed"
    return status

async def get_orders():
    while True:
        await get_valid_access_token()
        last_polled = state.load_last_polled()
        poll_time = get_current_time() 
        query = f"""
        {{
            orders(first: {ORDERS_FETCH_LIMIT}, sortKey: PROCESSED_AT, reverse: true){{
                edges {{
                    node {{
                        id
                        name
                        createdAt
                        channelInformation {{
                            app {{
                                title
                            }}
                        }}
                        shippingAddress {{
                            name
                            firstName
                            lastName
                        }}
                        lineItems(first: 10) {{
                            edges {{
                                node{{
                                    title
                                    variantTitle
                                    quantity
                                    customAttributes {{
                                        key
                                        value
                                    }}
                                }}
                            }}
                        }}
                    }}
                }}
            }}
        }}
        """

        url = f"https://{SHOP}/admin/api/2026-04/graphql.json"
        headers = {
            "X-Shopify-Access-Token": ACCESS_TOKEN,
            "Content-Type": "application/json"
        }

        try:
            data = await shopify_post(url, headers, {"query": query})
            
            orders = data.get("data", {}).get("orders", {}).get("edges", [])
            
            if orders:
                for edge in orders:
                    order = edge["node"]
                    if order["createdAt"] >= last_polled:
                        source = order["channelInformation"]["app"]["title"]
                        if source == "Shuttle - Sync with Etsy":
                            source = "Etsy"
                        customer_name = order["shippingAddress"]["name"]
                        for item_edge in order["lineItems"]["edges"]:
                            item = item_edge["node"]
                            quantity = item.get("quantity")
                            variants = item.get("variantTitle", "")
                            variant_arr = []
                            if variants:
                                variant_arr = [option.strip() for option in variants.split("/") if option.strip()]
                            if source == "Etsy":
                                item_name = ETSY_ALIASES.get(item["title"], item["title"])
                            else:
                                item_name = SHOPIFY_ALIASES.get(item["title"], item["title"])
                            item_string = f"  • {item_name} | Variant: {item['variantTitle']}"
                            if item.get("customAttributes", ""):
                                personalisation = item['customAttributes'][0]['value']
                                item_string += f" | Note: {personalisation}"
                            else:
                                personalisation = ""
                            colour, finish = (None, None)
                            if item_name == "Knobs & Switches":
                                finish = variant_arr[0]
                                colour = variant_arr[1]
                            else:
                                if variant_arr:
                                    if len(variant_arr) == 1:
                                        if variant_arr[0] in ("Glossy", "Standard", "Standard (Bent Ear)"):
                                            finish = variant_arr[0]
                                        else:
                                            colour = variant_arr[0]
                                    else:
                                        if variant_arr[0] in ("Glossy", "Standard", "Standard (Bent Ear)"):
                                            finish, colour = variant_arr
                                        else:
                                            colour, finish = variant_arr
                                            
                            print(customer_name)
                            print(item_string)
                            flag, file_path, file_name, requests, errors, name_list, glossy = etsy.format_order(design=item_name, colour=colour, finish=finish, notes=personalisation)
                            status = "Received"
                            isCustomOrder = file_name.startswith("Custom")
                            if not flag and not isCustomOrder:
                                status = update_stock(item_name, glossy, name_list, quantity)
                            if not glossy and status == "Printed":
                                status = "Complete"
                            if not isCustomOrder:
                                await addjob(customer_name, file_name, file_path, errors, requests, status, glossy, source)
                                
        except Exception as e:
            print(f"Error fetching orders: {e}")
        state.save_last_polled(poll_time)
        await asyncio.sleep(POLL_INTERVAL)
