import sys
import json
import sqlite3
from datetime import datetime

DB_PATH = "/home/iwanzack/AI-DCAS/attendance_system.db"

def insert_log(device_name, event, message, payload):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO device_log (device_name, event, message, payload)
        VALUES (?, ?, ?, ?)
    """, (device_name, event, message, payload))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    # Dapat data JSON dari n8n
    data = json.loads(sys.argv[1])

    device = data.get("device", "Unknown Device")
    event = data.get("event", "Unknown Event")
    message = data.get("message", "")
    payload = json.dumps(data)

    insert_log(device, event, message, payload)
    print(f"✅ Log disimpan untuk {device} | {event} | {datetime.now()}")
