from config import PICKGUARD_STORAGE_DIR
from order_management import DESIGNS, ALIASES
import os
from commands.jobs import insert_job

def check_knobs(order_data):
    
    additional_requests = order_data["additional_requests"]
    colour = order_data["colour"]
    quantity = order_data["quantity"]
    file_name = f"Knobs & Switches, {colour}, {quantity}"
    if additional_requests:
        return True, "", f"{file_name} (Request: {additional_requests})"
    file_link = os.path.join(PICKGUARD_STORAGE_DIR, "Knobs & Switches", f"{colour}.3mf")
    return False, file_link, file_name

def check_telecaster(order_data):
    
    design = order_data["design"]
    brand = order_data["brand"]
    model = order_data["model"]
    colour = order_data["colour"]
    finish = order_data["finish"]
    handed = order_data["handed"]
    holes = order_data["holes"]
    additional_requests = order_data["additional_requests"]
    
    design_name = ALIASES[design]
    design_info = DESIGNS[design]
    
    name_list = [design_name, brand.capitalize(), model.upper(), colour.capitalize(), finish.capitalize(), handed, f"{'with holes' if holes == 'yes' else 'without holes'}"]
    file_name = " ".join(p for p in name_list if p)
    
    if additional_requests:
        return True, "", f"{file_name} (Request: {additional_requests})"
    
    if not brand or not model:
        return True, "", f"{file_name} (Brand/Model not given)"
    
    if brand not in design_info["model"]:
        return True, "", f"{file_name} (Brand not supported ({brand}))"
    
    if model not in design_info["model"][brand]:
        return True, "", f"{file_name} Model not supported ({model})"
    
    endpoint = "holes.3mf" if holes == "yes" else "no holes.3mf"
    
    file_link = os.path.join(PICKGUARD_STORAGE_DIR, design_name, brand, model, colour, handed, endpoint)
    
    return False, file_link, file_name

def check_stratocaster(order_data):
    
    design = order_data["design"]
    brand = order_data["brand"]
    colour = order_data["colour"]
    finish = order_data["finish"]
    pickup_configuration = order_data["pickup_configuration"]
    handed = order_data["handed"]
    holes = order_data["holes"]
    additional_requests = order_data["additional_requests"]
    
    design_name = ALIASES[design]
    design_info = DESIGNS[design]
    
    name_list = [design_name, pickup_configuration, colour.capitalize(), finish.capitalize(), handed, f"{'with holes' if holes == 'yes' else 'without holes'}"]
    file_name = " ".join(p for p in name_list if p)
    
    errors = []
    if additional_requests:
        errors.append(f"Request: {additional_requests}")
    
    if brand in design_info["unsupported"] and holes == "yes":
        errors.append(f"Customer requested holes with unsupported brand: {brand.capitalize()}")
    
    if not pickup_configuration:
        errors.append("Customer did not provide pickup configuration")
    
    if pickup_configuration not in design_info["configuration"]:
        errors.append(f"Customer provided unsupported pickup configuration: {pickup_configuration})")
    
    endpoint = "holes.3mf" if holes == "yes" else "no holes.3mf"
    
    file_link = os.path.join(PICKGUARD_STORAGE_DIR, design_name, colour, pickup_configuration, handed, endpoint)
    
    if errors:
        return "", file_name, errors
    
    return file_link, file_name, errors

def check_stingray(order_data):
    
    design = order_data["design"]
    brand = order_data["brand"]
    model = order_data["model"]
    colour = order_data["colour"]
    finish = order_data["finish"]
    handed = order_data["handed"]
    holes = order_data["holes"]
    
    design_name = ALIASES[design]
    design_info = DESIGNS[design]   
    
    name_list = [design_name, colour.capitalize(), finish.capitalize(), handed, f"{'with holes' if holes == 'yes' else 'without holes'}"]
    file_name = " ".join(p for p in name_list if p)

    if model in design_info.get(brand, []):
        return True, "", f"{file_name} (Model ({model}) not supported)"

    endpoint = "holes.3mf" if holes == "yes" else "no holes.3mf"
    
    file_link = os.path.join(PICKGUARD_STORAGE_DIR, design_name, colour, handed, endpoint)
    
    return False, file_link, file_name
    
def check_default(order_data):
    
    design = order_data["design"]
    brand = order_data["brand"]
    model = order_data["model"]
    colour = order_data["colour"]
    finish = order_data["finish"]
    handed = order_data["handed"]
    holes = order_data["holes"]
    pickup_configuration = order_data["pickup_configuration"]
    additional_requests = order_data["additional_requests"]
    
    design_name = ALIASES[design]
    
    name_list = [design_name, brand.capitalize(), model.capitalize(), pickup_configuration, colour.capitalize(), finish.capitalize(), handed, f"{'with holes' if holes == 'yes' else 'without holes'}"]
    file_name = " ".join(p for p in name_list if p)
    
    if additional_requests:
        return True, "", f"{file_name} (Request: {additional_requests})"
    
    endpoint = "holes.3mf" if holes == "yes" else "no holes.3mf"
    
    file_link = os.path.join(PICKGUARD_STORAGE_DIR, design_name, brand, model, pickup_configuration, colour, handed, endpoint)
    
    return False, file_link, file_name
    
def model_check(order_data):
    design = order_data["design"]
    design_name = ALIASES[design]
    
    if design_name == "Knobs & Switches":
        return check_knobs(order_data)
    
    if design_name == "Telecatster":
        return check_telecaster(order_data)
    
    if design_name in ("Stratocatster", "Stratocaster Tiger"):
        return check_stratocaster(order_data)
    
    if design_name in ("Stingray", "Stingray 5"):
        return check_stingray(order_data)

    return check_default(order_data)

            

def format_order(): # testing
    
    # Extract raw information from order
    product = 'Stratocaster Cat Pickguard, Fender Stratocatster'
    customer_name = "test"
    # notes = order[25]
    
    
    # Use LLM to extract order information from notes
    # prompt = f"design name: [{product}], {notes}"
    # order_json = await gpt_request(prompt)
    
    # Convert JSON object to dict
    order_data = {
        "design": 'Stratocaster Cat Pickguard, Fender Stratocatster',
        "colour": "black",
        "finish": "standard",
        "brand": "squire",
        "model": "affinity",
        "handed": "RH",
        "holes": "yes",
        "pickup_configuration": "HSH",
        "additional_requests": ""
    }
    
    file_link, file_name, errors = model_check(order_data)
    errors_string = "; ".join(errors)
    
    # insert_job(file_name, position=1, file_path=file_link, customer_name=customer_name, errors=errors_string)
    
        
            

# def get_orders():
#     # Access etsy orders
    
#     # Fetch most recent orders by comparing order id of last fetched order
#     orders = []
#     # Iterate through orders and extract information for DB
#     for order in orders:
#         if format_order(order):
#             pass