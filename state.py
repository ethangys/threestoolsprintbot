import json
from datetime import datetime, timezone

STATE_FILE = "poll_date.json"

def save_last_polled(last_time):
    data = {
        "last_polled": last_time
    }
    with open(STATE_FILE, "w") as f:
        json.dump(data, f)

def load_last_polled():
    try: 
        with open(STATE_FILE) as f:
            return json.load(f).get("last_polled")
    except FileNotFoundError:
        pass
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
