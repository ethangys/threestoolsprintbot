from config import PICKGUARD_STORAGE_DIR
from order_management import DESIGNS
import os
from commands.utils import gpt_request
import json

def check_knobs(order_data):
    
    customisations = order_data["customisations"]
    other_requests = order_data["other_requests"]
    colour = order_data["colour"]
    quantity = order_data["finish"]
    file_name = f"{quantity}, {colour}"
    name_list = [quantity, colour]
    
    flag = False
    if customisations:
        flag = True
        file_name += f" (Request: {customisations})"
    
    file_link = ""
    
    return flag, file_link, file_name, other_requests, [], name_list

def check_telecaster(order_data):
    
    design = order_data["design"]
    brand = order_data["brand"]
    model = order_data["model"]
    colour = order_data["colour"]
    finish = order_data["finish"]
    handed = order_data["handed"]
    holes = order_data["holes"]
    customisations = order_data["customisations"]
    other_requests = order_data["other_requests"]
    
    design_info = DESIGNS[design]
    
    name_list = [design, model, colour, finish, handed, f"{'With Holes' if holes == 'yes' else 'Without Holes'}"]

    file_name = " ".join(p for p in name_list if p)
    
    flag = False
    errors = []
    
    if customisations:
        flag = True
        file_name += f" (Request: {customisations})"
    
    if not brand or not model:
        flag = True
        errors.append("Brand/Model not given")
    
    if brand and brand not in design_info["model"].keys():
        flag = True
        errors.append(f"Brand not supported ({brand})")
    
    if model and model not in design_info["model"].get(brand, ""):
        flag = True
        errors.append(f"Model not supported ({model})")
    
    endpoint = "Holes.3mf" if holes == "yes" else "No Holes.3mf"
    
    if not flag:
        file_link = os.path.join(PICKGUARD_STORAGE_DIR, design, model, colour, handed, endpoint)
    else:
        file_link = ""
    
    return flag, file_link, file_name, other_requests, errors, name_list

def check_stratocaster(order_data):
    
    design = order_data["design"]
    brand = order_data["brand"]
    colour = order_data["colour"]
    finish = order_data["finish"]
    pickup_configuration = order_data["pickup_configuration"]
    handed = order_data["handed"]
    holes = order_data["holes"]
    customisations = order_data["customisations"]
    other_requests = order_data["other_requests"]
    
    design_info = DESIGNS[design]
    
    name_list = [design, pickup_configuration, colour, finish, handed, f"{'With Holes' if holes == 'yes' else 'Without Holes'}"]
    file_name = " ".join(p for p in name_list if p)
    
    flag = False
    errors = []
    
    
    if customisations:
        flag = True
        file_name += f" (Request: {customisations})"
    
    if brand and brand not in design_info["model"].keys() and holes == "yes":
        flag = True
        errors.append(f"Customer requested holes with unsupported brand: {brand.capitalize()}")
    
    if not pickup_configuration:
        flag = True
        errors.append("Customer did not provide pickup configuration")
    
    if pickup_configuration and pickup_configuration not in design_info["configuration"]:
        flag = True
        errors.append(f"Customer provided unsupported pickup configuration: {pickup_configuration})")
    
    endpoint = "Holes.3mf" if holes == "yes" else "No Holes.3mf"
    
    if not flag:
        file_link = os.path.join(PICKGUARD_STORAGE_DIR, design, pickup_configuration, colour, handed, endpoint)
    else:
        file_link = ""
    
    return flag, file_link, file_name, other_requests, errors, name_list

def check_stingray(order_data):
    
    design = order_data["design"]
    brand = order_data["brand"]
    model = order_data["model"]
    colour = order_data["colour"]
    finish = order_data["finish"]
    handed = order_data["handed"]
    holes = order_data["holes"]
    customisations = order_data["customisations"]
    other_requests = order_data["other_requests"]
    
    flag = False
    errors = []
    
    if design in ("Stingray", "Stingray Shark", "Stingray Lobster"):
        design_check = "Stingray"

    design_info = DESIGNS[design_check]   
    
    name_list = [design, brand, model, colour, finish, handed, f"{'With Holes' if holes == 'yes' else 'Without Holes'}"]
    file_name = " ".join(p for p in name_list if p)

    unsupported = design_info["unsupported"]
    
    if any(model in models for models in unsupported.values()):
        flag = True
        errors.append(f"Model not supported ({model})")
    if customisations:
        flag = True
        file_name += f" (Request: {customisations})"

        
    endpoint = "Holes.3mf" if holes == "yes" else "No Holes.3mf"
    
    if not flag:
        file_link = os.path.join(PICKGUARD_STORAGE_DIR, design, brand, model, colour, handed, endpoint)
    else:
        file_link = ""
    
    return flag, file_link, file_name, other_requests, errors, name_list
    
def check_default(order_data):
    
    design = order_data["design"]
    colour = order_data["colour"]
    finish = order_data["finish"]
    handed = order_data["handed"]
    holes = order_data["holes"]
    customisations = order_data["customisations"]
    other_requests = order_data["other_requests"]

    name_list = [design, colour, finish, handed, f"{'With Holes' if holes == 'yes' else 'Without Holes'}"]
    file_name = " ".join(p for p in name_list if p)
    if customisations:
        return True, "", f"{file_name} (Request: {customisations})", other_requests, []
    
    endpoint = "Holes.3mf" if holes == "yes" else "No Holes.3mf"
    
    file_link = os.path.join(PICKGUARD_STORAGE_DIR, design, colour, handed, endpoint)
    
    return False, file_link, file_name, other_requests, [], name_list
    
def model_check(order_data):
    design = order_data["design"]
    
    if design == "Knobs & Switches":
        return check_knobs(order_data)
    
    if design == "Telecaster":
        return check_telecaster(order_data)
    
    if design in ("Stratocaster", "Stratocaster Tiger"):
        return check_stratocaster(order_data)
    
    if design in ("Stingray", "Stingray 5", "Stingray Shark", "Lobster"):
        return check_stingray(order_data)

    return check_default(order_data)


def format_order(design, colour, finish, notes):
    
    # Use LLM to extract order information from notes
    prompt = f"design name: [{design}], {notes}"
    
    order_json = gpt_request(prompt)
    # print(order_json)
    order_data = json.loads(order_json)
    print(order_data)
    
    order_data["colour"] = colour if colour else ""
    order_data["finish"] = finish if finish else ""
        
    print(model_check(order_data))
    flag, file_path, file_name, requests, errors, name_list = model_check(order_data)
    return file_path, file_name, requests, errors, name_list