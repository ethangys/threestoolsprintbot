import json

UNPAID_ORDERS_FILE = "unpaid_orders.json"

def add_unpaid(order_id):
    with open(UNPAID_ORDERS_FILE, "r") as f:
        data = json.load(f)
        
    data.append(order_id)
    
    with open(UNPAID_ORDERS_FILE, "w") as f:
        json.dump(data, f)

def load_unpaid():
    try: 
        with open(UNPAID_ORDERS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        pass
            
def remove_unpaid(order_id):
    with open(UNPAID_ORDERS_FILE, "r") as f:
        data = json.load(f)
        
    data.remove(order_id)
    
    with open(UNPAID_ORDERS_FILE, "w") as f:
        json.dump(data, f)