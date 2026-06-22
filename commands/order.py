from config import PICKGUARD_STORAGE_DIR
import os

def check_knobs(order_data):
    
    requests = order_data["requests"]
    colour = order_data["colour"]
    quantity = order_data["finish"]
    
    lever_sizes = {
        "3.5mm x 1mm": "S",
        "3.7mm x 1.3mm": "M",
        "5mm x 1.4mm": "L"
    }
    
    size = lever_sizes[order_data["switch_size"]]
    
    name_list = [quantity, colour, size]
    
    file_name = f"{quantity}, {colour}, {size}"
    
    flag = False
    if requests:
        flag = True
        file_name += f" (Request: {requests})"
    
    file_link = ""
    
    return flag, file_link, file_name, requests, name_list

def check_telecaster(order_data):
    
    design = order_data["design"]
    model = order_data["model"]
    colour = order_data["colour"]
    finish = order_data["finish"]
    orientation = order_data["orientation"]
    requests = order_data["requests"]
    
    holes = (model != "No Screw Holes")
    
    if not holes:
        model = ""
    
    name_list = [design, model, colour, finish, orientation, f"{'With Holes' if holes else 'Without Holes'}"]

    file_name = " ".join(p for p in name_list if p)
    
    flag = False
    
    if requests:
        flag = True
        file_name += f" (Request: {requests})"
    
    endpoint = "Holes.3mf" if holes else "No Holes.3mf"
    
    if not flag:
        file_link = os.path.join(PICKGUARD_STORAGE_DIR, design, model, colour, orientation, endpoint)
    else:
        file_link = ""
    
    return flag, file_link, file_name, requests, name_list

def check_stratocaster(order_data):
    
    design = order_data["design"]
    colour = order_data["colour"]
    finish = order_data["finish"]
    model = order_data["model"]
    pickup_configuration = order_data["pickup_configuration"]
    orientation = order_data["orientation"]
    requests = order_data["requests"]
    
    holes = (model != "No Screw Holes")
    
    name_list = [design, pickup_configuration, colour.title(), finish.title(), orientation, f"{'With Holes' if holes else 'Without Holes'}"]
    
    file_name = " ".join(p for p in name_list if p)
    
    flag = False
    
    if requests:
        flag = True
        file_name += f" (Request: {requests})"
    
    endpoint = "Holes.3mf" if holes else "No Holes.3mf"
    
    if not flag:
        file_link = os.path.join(PICKGUARD_STORAGE_DIR, design, pickup_configuration, colour, orientation, endpoint)
    else:
        file_link = ""
    
    return flag, file_link, file_name, requests, name_list

def check_stingray(order_data):
    
    design = order_data["design"]
    model = order_data["model"]
    colour = order_data["colour"]
    finish = order_data["finish"]
    orientation = order_data["orientation"]
    requests = order_data["requests"]
    accessory_colour = order_data["accessory_colour"]
    
    flag = False
    
    holes = (model != "No Screw Holes")
    
    if not holes:
        model = ""
        
    finish_list = finish.split(" ")
    
    if len(finish_list) > 1 and finish_list[-1] != "Ear)":
        finish = f"{finish_list[0]} + {" ".join(accessory_colour.split(" ")[:-1])} {finish_list[-1]}"
    
    name_list = [design, model, colour.title(), finish.title(), orientation, f"{'With Holes' if holes else 'Without Holes'}"]
    
    file_name = " ".join(p for p in name_list if p)
    if requests:
        flag = True
        file_name += f" (Request: {requests})"

    endpoint = "Holes.3mf" if holes else "No Holes.3mf"
    
    if not flag:
        file_link = os.path.join(PICKGUARD_STORAGE_DIR, design, model, colour, orientation, endpoint)
    else:
        file_link = ""
    
    return flag, file_link, file_name, requests, name_list
    
def check_default(order_data):
    
    design = order_data["design"]
    colour = order_data["colour"]
    finish = order_data["finish"]
    model = order_data["model"]
    orientation = order_data["orientation"]
    requests = order_data["requests"]
    accessory_colour = order_data["accessory_colour"]

    holes = (model != "No Screw Holes")
    
    finish_list = finish.split(" ")
    
    if len(finish_list) > 1 and finish_list[-1] != "Ear)":
        finish = f"{finish_list[0]} + {f'{accessory_colour} ' if accessory_colour else ''}{finish_list[-1]}"

    name_list = [design, colour.title(), finish.title(), orientation, f"{'With Holes' if holes else 'Without Holes'}"]
    
    file_name = " ".join(p for p in name_list if p)
    
    if requests:
        return True, "", f"{file_name} (Request: {requests})", name_list
    
    endpoint = "Holes.3mf" if holes else "No Holes.3mf"
    
    file_link = os.path.join(PICKGUARD_STORAGE_DIR, design, colour, orientation, endpoint)
    
    return False, file_link, file_name, requests, name_list
    
def model_check(order_data):
    design = order_data["design"]
    
    if design == "Knobs & Switches":
        return check_knobs(order_data)
    
    if design == "Telecaster":
        return check_telecaster(order_data)
    
    if design in ("Stratocaster", "Stratocaster Tiger"):
        return check_stratocaster(order_data)
    
    if design in ("Stingray", "Stingray 5", "Stingray Shark", "Stingray Lobster"):
        return check_stingray(order_data)
    
    return check_default(order_data)


def format_order(design, colour, finish, options):
    
    order_data = {
        "design": design,
        "colour": colour,
        "finish": finish,
        "model": options.get("Model", ""),
        "orientation": options.get("Orientation", ""),
        "pickup_configuration": options.get("Pickup Configuration", ""),
        "accessory_colour": options.get("Accessory Colour", ""),
        "requests": options.get("Personalization", ""),
        "switch_size": options.get("Switch Lever Size", "")
    }
    
    if order_data["orientation"] == "Right Handed":
        order_data["orientation"] = "RH"
    if order_data["orientation"] == "Left Handed":
        order_data["orientation"] = "LH"
     
    print(order_data)
    
    if finish.startswith("Glossy"):
        glossy = 1
    else:
        glossy = 0
        
    flag, file_path, file_name, requests, name_list = model_check(order_data)
    print(file_name)
    return flag, file_path, file_name, requests, name_list, glossy