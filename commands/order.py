from config import PICKGUARD_STORAGE_DIR
from order_management import SCREW_COUNT, NO_HOLES, DIFFERENT_MODELS
import os

def check_accessories(order_data):
    
    design = order_data["design"]
    colour = order_data["colour"]
    finish = order_data["finish"]
    
    name_list = [design, colour, finish]
    
    file_name = " ".join(p for p in name_list if p)
    
    file_link = os.path.join(PICKGUARD_STORAGE_DIR, design, colour)
    
    return file_link, file_name, "", name_list

def check_screws(order_data):
    colour = order_data["colour"]
    model = order_data["finish"]
    quantity = SCREW_COUNT.get(model, "")
    
    name_list = ["Screws", colour, quantity]
    
    file_name = f"{colour} Screws x{quantity}"
    
    return "", file_name, "", name_list

def check_knobs_toppers(order_data):
    
    design = order_data["design"]
    requests = order_data["requests"]
    colour = order_data["colour"]
    quantity = order_data["finish"]
    switch_dimension = order_data["switch_size"]
    
    lever_sizes = {
        "3.5mm x 1mm": "S",
        "3.7mm x 1.3mm": "M",
        "5mm x 1.4mm": "L"
    }
    
    size = lever_sizes.get(switch_dimension, "")
    
    if design == "Knobs & Switches":
        name_list = [quantity, colour, size]
    else:
        name_list = [quantity, colour]
    
    file_name = f"{quantity}, {colour}"
    if size:
        file_name += f", {size}"
    
    if requests:
        file_name += f" (Reference: {requests})"
    
    file_link = ""
    
    return file_link, file_name, requests, name_list


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
    
    if requests:
        file_name += f" (Reference: {requests})"
        file_link = ""
    else:
        file_link = os.path.join(PICKGUARD_STORAGE_DIR, design, pickup_configuration, colour.title(), orientation, f"{'Holes' if holes else 'No Holes'}.3mf")

    
    return file_link, file_name, requests, name_list

def check_jazzmaster(order_data):
    
    design = order_data["design"]
    colour = order_data["colour"]
    finish = order_data["finish"]
    model = order_data["model"]
    orientation = order_data["orientation"]
    requests = order_data["requests"]
    control_plate_colour = order_data["control_plate_colour"]

    holes = (model != "No Screw Holes")
    
    control_plate = f"{control_plate_colour} Control Plate"

    name_list = [design, colour.title(), control_plate, finish.title(), orientation, f"{'With Holes' if holes else 'Without Holes'}"]
    file_link = os.path.join(PICKGUARD_STORAGE_DIR, design, colour.title(), control_plate, orientation, f"{'Holes' if holes else 'No Holes'}.3mf")
    
    file_name = " ".join(p for p in name_list if p)
    
    if requests:
        file_name += f" (Reference: {requests})"
        file_link = ""
    
    return file_link, file_name, requests, name_list


def check_different_model(order_data):
    
    design = order_data["design"]
    model = order_data["model"]
    colour = order_data["colour"]
    finish = order_data["finish"]
    orientation = order_data["orientation"]
    requests = order_data["requests"]
    accessory_colour = order_data["accessory_colour"]
    
    holes = (model != "No Screw Holes")
    
    finish_list = finish.split(" ")
        
    if len(finish_list) > 1 and finish_list[-1].title() != "Ear)":
        finish = f"{finish_list[0]} + {f'{accessory_colour} ' if accessory_colour else ''}{finish_list[-1]}"
    
    if design in NO_HOLES or holes:
        name_list = [design, model, colour.title(), finish.title(), orientation]
        file_link = os.path.join(*(p for p in [PICKGUARD_STORAGE_DIR, design, model, colour.title(), f"{orientation}.3mf"] if p))
    else:
        name_list = [design, colour.title(), finish.title(), orientation, "Without Holes"]
        file_link = os.path.join(*(p for p in [PICKGUARD_STORAGE_DIR, design, "No Holes", colour.title(), f"{orientation}.3mf"] if p))
    
    file_name = " ".join(p for p in name_list if p)
    
    if requests:
        file_name += f" (Reference: {requests})"
        file_link = ""
    
    return file_link, file_name, requests, name_list

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
    
    if len(finish_list) > 1 and finish_list[-1].title() != "Ear)":
        finish = f"{finish_list[0]} + {f'{accessory_colour} ' if accessory_colour else ''}{finish_list[-1]}"
    
    if design in NO_HOLES:
        name_list = [design, colour.title(), finish.title(), orientation]
        file_link = os.path.join(*(p for p in [PICKGUARD_STORAGE_DIR, design, colour.title(), f"{orientation}.3mf"] if p))
    else:
        name_list = [design, colour.title(), finish.title(), orientation, f"{'With Holes' if holes else 'Without Holes'}"]
        file_link = os.path.join(*(p for p in [PICKGUARD_STORAGE_DIR, design, colour.title(), orientation, f"{'Holes' if holes else 'No Holes'}.3mf"] if p))
    
    if model == "":
        name_list = [design]
    
    file_name = " ".join(p for p in name_list if p)
    
    if requests:
        file_name += f" (Reference: {requests})"
        file_link = ""
    
    return file_link, file_name, requests, name_list

    
def model_check(order_data):
    design = order_data["design"]
    
    if design in ("Knobs & Switches", "Toppers"):
        return check_knobs_toppers(order_data)
    
    if design in ("Stratocaster", "Stratocaster Tiger", "Stratocaster Panda"):
        return check_stratocaster(order_data)
    
    if design == "Fish":
        return check_accessories(order_data)
    
    if design == "Screws":
        return check_screws(order_data)
    
    if design == "Squier Jazzmaster":
        return check_jazzmaster(order_data)
    
    if design in DIFFERENT_MODELS:
        return check_different_model(order_data)
    
    return check_default(order_data)


def format_order(design, colour, finish, options):
    
    order_data = {
        "design": design,
        "colour": colour if colour else "",
        "finish": finish if finish else "",
        "model": options.get("Model", ""),
        "orientation": options.get("Orientation", ""),
        "pickup_configuration": options.get("Pickup Configuration", ""),
        "accessory_colour": options.get("Accessory Colour", ""),
        "requests": options.get("Custom Order Reference", ""),
        "switch_size": options.get("Switch Lever Size", ""),
        "control_plate_colour": options.get("Control Plate Colour", "")
    }
    
    if order_data["orientation"] == "Right Handed":
        order_data["orientation"] = "RH"
    if order_data["orientation"] == "Left Handed":
        order_data["orientation"] = "LH"
     
    print(order_data)
    
    if order_data["finish"].startswith("Glossy"):
        glossy = 1
    else:
        glossy = 0
        
    file_path, file_name, requests, name_list = model_check(order_data)
    return file_path, file_name, requests, name_list, glossy