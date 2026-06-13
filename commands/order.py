from config import PICKGUARD_STORAGE_DIR
import os

def check_knobs(order_data):
    
    requests = order_data["requests"]
    colour = order_data["colour"]
    quantity = order_data["finish"]
    file_name = f"{quantity}, {colour}"
    name_list = [quantity, colour]
    
    flag = False
    if customisations:
        flag = True
        file_name += f" (Request: {requests})"
    
    file_link = ""
    
    return flag, file_link, file_name, other_requests, name_list

def check_telecaster(order_data):
    
    design = order_data["design"]
    model = order_data["model"]
    colour = order_data["colour"]
    finish = order_data["finish"]
    handed = order_data["handed"]
    requests = order_data["requests"]
    
    holes = (model != "No Screw Holes")
    
    name_list = [design, model, colour, finish, handed, f"{'With Holes' if holes else 'Without Holes'}"]

    file_name = " ".join(p for p in name_list if p)
    
    flag = False
    
    if requests:
        flag = True
        file_name += f" (Request: {requests})"
    
    endpoint = "Holes.3mf" if holes else "No Holes.3mf"
    
    if not flag:
        file_link = os.path.join(PICKGUARD_STORAGE_DIR, design, model, colour, handed, endpoint)
    else:
        file_link = ""
    
    return flag, file_link, file_name, requests, name_list

def check_stratocaster(order_data):
    
    design = order_data["design"]
    colour = order_data["colour"]
    finish = order_data["finish"]
    model = order_data["model"]
    pickup_configuration = order_data["pickup_configuration"]
    handed = order_data["handed"]
    requests = order_data["requests"]
    
    holes = (model != "No Screw Holes")
    
    name_list = [design, pickup_configuration, colour.title(), finish.title(), handed, f"{'With Holes' if holes else 'Without Holes'}"]
    
    file_name = " ".join(p for p in name_list if p)
    
    print(file_name)
    
    flag = False
    
    if requests:
        flag = True
        file_name += f" (Request: {requests})"
    
    endpoint = "Holes.3mf" if holes else "No Holes.3mf"
    
    if not flag:
        file_link = os.path.join(PICKGUARD_STORAGE_DIR, design, pickup_configuration, colour, handed, endpoint)
    else:
        file_link = ""
    
    return flag, file_link, file_name, requests, name_list

def check_stingray(order_data):
    
    design = order_data["design"]
    model = order_data["model"]
    colour = order_data["colour"]
    finish = order_data["finish"]
    handed = order_data["handed"]
    requests = order_data["requests"]
    accessory_colour = order_data["accessory_colour"]
    
    flag = False
    
    holes = (model != "No Screw Holes")
        
    finish_list = finish.split(" ")
    
    if len(finish_list) > 1 and finish_list[-1] != "Ear)":
        finish = f"{finish_list[0]} + {" ".join(accessory_colour.split(" ")[:-1])} {finish_list[-1]}"
    
    name_list = [design, model, colour.title(), finish.title(), handed, f"{'With Holes' if holes else 'Without Holes'}"]
    
    file_name = " ".join(p for p in name_list if p)
    if requests:
        flag = True
        file_name += f" (Request: {requests})"

    endpoint = "Holes.3mf" if holes else "No Holes.3mf"
    
    if not flag:
        file_link = os.path.join(PICKGUARD_STORAGE_DIR, design, model, colour, handed, endpoint)
    else:
        file_link = ""
    
    return flag, file_link, file_name, requests, name_list
    
def check_default(order_data):
    
    design = order_data["design"]
    colour = order_data["colour"]
    finish = order_data["finish"]
    handed = order_data["handed"]
    requests = order_data["requests"]
    accessory_colour = order_data["accessory_colour"]

    holes = (model != "No Screw Holes")
    
    finish_list = finish.split(" ")
    
    if len(finish_list) > 1 and finish_list[-1] != "Ear)":
        finish = f"{finish_list[0]} + {accessory_colour[:-1]} {finish_list[2]}"

    name_list = [design, colour.title(), finish.title(), handed, f"{'With Holes' if holes else 'Without Holes'}"]
    
    file_name = " ".join(p for p in name_list if p)
    
    if requests:
        return True, "", f"{file_name} (Request: {requests})", name_list
    
    endpoint = "Holes.3mf" if holes else "No Holes.3mf"
    
    file_link = os.path.join(PICKGUARD_STORAGE_DIR, design, colour, handed, endpoint)
    
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
        "handed": options.get("Handed", ""),
        "pickup_configuration": options.get("Pickup Configuration", ""),
        "accessory_colour": options.get("Accessory Colour", ""),
        "requests": options.get("Personalization", "")
    }
    
    if order_data["handed"] == "Right Handed":
        order_data["handed"] = "RH"
    if order_data["handed"] == "Left Handed":
        order_data["handed"] = "LH"
     
    print(order_data)
    
    if finish.startswith("Glossy"):
        glossy = 1
    else:
        glossy = 0
        
    flag, file_path, file_name, requests, name_list = model_check(order_data)
    return flag, file_path, file_name, requests, name_list, glossy