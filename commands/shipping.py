from commands.utils import gpt_request
import gspread
from google.oauth2.service_account import Credentials
import json
from order_management import EU_CODES, EU_VAT, NO_VAT, UK_VAT

SERVICE_ACCOUNT_FILE = "service_account.json"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

NAME_COL = 1
BLOCK_COL = 3
STREET_COL = 4
BUILDING_COL = 5
TOWN_COL = 6
STATE_COL = 7
COUNTRY_COL = 8
ZIP_COL = 9
PHONE_COL = 10

ITEM1_START_COL = 24
ITEM2_START_COL = 30
QTY_COL_OFFSET = 1
WEIGHT_COL_OFFSET = 2
PRICE_COL_OFFSET = 3
ORIGIN_COL_OFFSET = 5

VAT_COL = 11

ITEM_TYPE_ROW = 17
CATEGORY_ROW = 18
ITEM_WEIGHT_ROW = 20
ITEM_LENGTH_ROW = 21
ITEM_WIDTH_ROW = 22
ITEM_HEIGHT_ROW = 23

SHIPPING_SERVICE_CODE = "WWPECO"
SERVICE_CODE_ROW = 46


creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
client = gspread.authorize(creds)
sheet = client.open("Singpost Shipping").sheet1
            
def get_shipping(order):
  
  shipping_info = order["shippingAddress"]
  
  prompt = f"""
  {shipping_info["address1"]}
  {shipping_info["address2"]}
  {shipping_info["province"]}
  """
  
  return gpt_request(prompt)

def parse_knobs(item):
  
  variants = item.get("variantTitle", "")
  name = [option.strip() for option in variants.split("/") if option.strip()][0]
  name_list = name.split(" ")
  quantity = int(name_list[0])
  if name_list[-1] == "Switch":
    quantity += 1
  return quantity
  

def get_product(item, item_name):
  
  price = item["discountedUnitPriceSet"]["shopMoney"]["amount"]
  item_type = "Plastic Guitar Knobs" if item_name == "Knobs & Switches" else "Plastic Guitar Pickguard"
  quantity = item.get("quantity", "")
  if item_type == "Plastic Guitar Knobs":
    quantity = quantity * parse_knobs(item)
  
  return item_type, price, quantity

def add_shipping(order, item, item_name):
  
  country_code = order["shippingAddress"]["countryCodeV2"]
  if country_code not in ("SG", "US") and not item["title"].startswith("Custom"):
    
    name = order["shippingAddress"]["name"]
    address_info = json.loads(get_shipping(order))
    source = order["channelInformation"]["app"]["title"]
    
    block = address_info.get("block_number", "")
    street = address_info.get("street_and_unit", "")
    building = address_info.get("building_name", "")
    town = order["shippingAddress"]["city"]
    state = order["shippingAddress"]["province"]
    postcode = order["shippingAddress"]["zip"]
    phone = order["phone"]
    item_type, price, quantity = get_product(item, item_name)
    
    vat_number = ""
    
    if source == "Shuttle - Sync with Etsy":
      if country_code == "NO":
        vat_number = NO_VAT
      elif country_code == "GB":
        vat_number = UK_VAT
      elif country_code in EU_CODES:
        vat_number = EU_VAT
      
    
    cell = sheet.find(name)
    if not cell: # new item
      row_data = [""] * SERVICE_CODE_ROW
      row_data[NAME_COL - 1] = name
      row_data[BLOCK_COL - 1] = block
      row_data[STREET_COL - 1] = street
      row_data[BUILDING_COL - 1] = building
      row_data[TOWN_COL - 1] = town
      row_data[STATE_COL - 1] = state
      row_data[COUNTRY_COL - 1] = country_code
      row_data[ZIP_COL - 1] = postcode
      row_data[PHONE_COL - 1] = phone
      row_data[VAT_COL - 1] = vat_number

      row_data[ITEM1_START_COL - 1] = item_type
      row_data[ITEM1_START_COL + QTY_COL_OFFSET - 1] = quantity
      row_data[ITEM1_START_COL + WEIGHT_COL_OFFSET - 1] = 0.2
      row_data[ITEM1_START_COL + PRICE_COL_OFFSET - 1] = price
      row_data[ITEM1_START_COL + ORIGIN_COL_OFFSET - 1] = "SG"

      row_data[SERVICE_CODE_ROW - 1] = SHIPPING_SERVICE_CODE
      row_data[ITEM_TYPE_ROW - 1] = item_type
      row_data[CATEGORY_ROW - 1] = "M"
      row_data[ITEM_WEIGHT_ROW - 1] = 0.2
      row_data[ITEM_LENGTH_ROW - 1] = 30
      row_data[ITEM_WIDTH_ROW - 1] = 30
      row_data[ITEM_HEIGHT_ROW - 1] = 2
      
      sheet.append_row(row_data)
      
    else:
      row = cell.row
      if item_type == "Plastic Guitar Pickguard" and sheet.cell(row, ITEM1_START_COL).value == "Plastic Guitar Pickguard": 
        
        value = float(sheet.cell(row, ITEM1_START_COL + PRICE_COL_OFFSET).value) + float(price)
        sheet.update_cell(row, ITEM1_START_COL + PRICE_COL_OFFSET, value)
        qty = int(sheet.cell(row, ITEM1_START_COL + QTY_COL_OFFSET).value)
        sheet.update_cell(row, ITEM1_START_COL + QTY_COL_OFFSET, qty + 1)
        
      elif item_type == "Plastic Guitar Knobs" and sheet.cell(row, ITEM1_START_COL).value == "Plastic Guitar Pickguard":
        
        updates = {
          ITEM1_START_COL + WEIGHT_COL_OFFSET: 0.15,
          ITEM2_START_COL: item_type,
          ITEM2_START_COL + QTY_COL_OFFSET: quantity,
          ITEM2_START_COL + WEIGHT_COL_OFFSET: 0.05,
          ITEM2_START_COL + PRICE_COL_OFFSET: price,
          ITEM2_START_COL + ORIGIN_COL_OFFSET: "SG"
        }
        
        sheet.batch_update([
          {
            "range": gspread.utils.rowcol_to_a1(row, col),
            "values": [[value]]
          }
          for col, value in updates.items()
        ])
        
      elif item_type == "Plastic Guitar Pickguard" and sheet.cell(row, ITEM1_START_COL).value == "Plastic Guitar Knobs":
        
        updates = {
          ITEM1_START_COL + WEIGHT_COL_OFFSET: 0.05,
          ITEM2_START_COL: item_type,
          ITEM2_START_COL + QTY_COL_OFFSET: quantity,
          ITEM2_START_COL + WEIGHT_COL_OFFSET: 0.15,
          ITEM2_START_COL + PRICE_COL_OFFSET: price,
          ITEM2_START_COL + ORIGIN_COL_OFFSET: "SG"
        }
        
        sheet.batch_update([
          {
            "range": gspread.utils.rowcol_to_a1(row, col),
            "values": [[value]]
          }
          for col, value in updates.items()
        ])
