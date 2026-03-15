import json
import os
from datetime import datetime

LOG_FILE = os.path.join(os.path.expanduser("~"), ".file_organizer_log.json")

def write_log(moves):
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "moves": moves
    }

    logs = read_all_logs()
    logs.append(log_entry)

    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=2)

def read_last_log():
    logs = read_all_logs()
    if not logs:
        return None
    return logs[-1]

def read_all_logs():
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, "r") as f:
        return json.load(f)

def clear_last_log():
    logs = read_all_logs()
    if logs:
        logs.pop()
    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=2)