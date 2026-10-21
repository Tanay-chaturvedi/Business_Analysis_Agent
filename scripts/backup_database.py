"""
scripts/backup_database.py
==========================
Creates a verified JSON snapshot backup of the MySQL database tables
(conversations and messages) prior to any schema alterations.
"""

import os
import sys
import json
import datetime

# Ensure project root in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.database import engine
from sqlalchemy import text


def create_backup():
    backup_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "backups"))
    os.makedirs(backup_dir, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(backup_dir, f"bizadvisor_mysql_backup_{timestamp}.json")

    backup_data = {
        "timestamp": datetime.datetime.now().isoformat(),
        "conversations": [],
        "messages": [],
    }

    with engine.connect() as conn:
        conv_rows = conn.execute(text("SELECT * FROM conversations")).mappings().all()
        for r in conv_rows:
            d = dict(r)
            for k, v in d.items():
                if isinstance(v, (datetime.datetime, datetime.date)):
                    d[k] = v.isoformat()
            backup_data["conversations"].append(d)

        msg_rows = conn.execute(text("SELECT * FROM messages")).mappings().all()
        for r in msg_rows:
            d = dict(r)
            for k, v in d.items():
                if isinstance(v, (datetime.datetime, datetime.date)):
                    d[k] = v.isoformat()
            backup_data["messages"].append(d)

    with open(backup_path, "w", encoding="utf-8") as f:
        json.dump(backup_data, f, indent=2, ensure_ascii=False)

    print(f"SUCCESS: Backup written to {backup_path}")
    print(f"Backed up {len(backup_data['conversations'])} conversations and {len(backup_data['messages'])} messages.")
    return backup_path


if __name__ == "__main__":
    create_backup()
