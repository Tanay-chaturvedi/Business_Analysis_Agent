"""
scripts/migrate_sqlite_to_mysql.py
==================================
Safe migration script to import historical conversations and messages
from the legacy SQLite database (`data/bizadvisor_history.db`) into the new
2-table MySQL database (`bizadvisor_db`).

- Does NOT delete or alter the SQLite database.
- Idempotent: checks for existing conversation IDs to prevent duplicate inserts.
"""

import os
import sys
import json
import sqlite3
import uuid
from datetime import datetime

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.database import init_db, SessionLocal, Conversation, Message

SQLITE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "bizadvisor_history.db"))


def parse_timestamp(ts_str):
    if not ts_str:
        return datetime.utcnow()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f"):
        try:
            return datetime.strptime(ts_str, fmt)
        except ValueError:
            pass
    try:
        return datetime.fromisoformat(ts_str.replace("Z", "+00:00")).replace(tzinfo=None)
    except Exception:
        return datetime.utcnow()


def run_migration():
    if not os.path.exists(SQLITE_PATH):
        print(f"No SQLite database found at {SQLITE_PATH}. Nothing to migrate.")
        return

    init_db()

    sqlite_conn = sqlite3.connect(SQLITE_PATH)
    sqlite_conn.row_factory = sqlite3.Row
    cursor = sqlite_conn.cursor()

    cursor.execute("""
        SELECT id, title, location, cuisine, approx_cost, prediction, opportunity_score,
               raw_parameters, analysis_data, messages, created_at, updated_at
        FROM analysis_history
    """)
    rows = cursor.fetchall()
    print(f"Found {len(rows)} legacy sessions in SQLite database.")

    db = SessionLocal()
    migrated_conv_count = 0
    migrated_msg_count = 0

    try:
        for r in rows:
            conv_id = r["id"]
            existing = db.query(Conversation).filter(Conversation.id == conv_id).first()
            if existing:
                continue

            raw_params = None
            if r["raw_parameters"]:
                try:
                    raw_params = json.loads(r["raw_parameters"])
                except Exception:
                    raw_params = {}

            analysis_data = None
            if r["analysis_data"]:
                try:
                    analysis_data = json.loads(r["analysis_data"])
                except Exception:
                    analysis_data = {}

            msg_list = []
            if r["messages"]:
                try:
                    msg_list = json.loads(r["messages"])
                except Exception:
                    msg_list = []

            c_created = parse_timestamp(r["created_at"])
            c_updated = parse_timestamp(r["updated_at"])
            last_msg_at = c_updated

            conversation = Conversation(
                id=conv_id,
                title=r["title"] or "Business Analysis Session",
                created_at=c_created,
                updated_at=c_updated,
                last_message_at=last_msg_at,
                parameters_json=raw_params,
                analysis_json=analysis_data,
            )
            db.add(conversation)
            migrated_conv_count += 1

            for idx, m in enumerate(msg_list):
                m_role = m.get("role", "user")
                m_content = m.get("content", "")
                m_mode = m.get("mode", "text")
                m_ts = parse_timestamp(m.get("timestamp")) or c_created
                m_id = str(m.get("id")) if m.get("id") else str(uuid.uuid4())

                # If m_id is already used or pure timestamp number, format cleanly
                if len(m_id) < 10:
                    m_id = f"{conv_id}-{idx}"

                meta = {
                    "mode": m_mode,
                    "analysis": m.get("analysis"),
                    "scenarioComparison": m.get("scenarioComparison"),
                    "parameters": m.get("parameters"),
                }

                msg_obj = Message(
                    id=m_id,
                    conversation_id=conv_id,
                    role=m_role,
                    content=m_content,
                    message_type=m_mode or "text",
                    metadata_json=meta,
                    created_at=m_ts,
                )
                db.add(msg_obj)
                migrated_msg_count += 1

        db.commit()
        print(f"Migration completed successfully!")
        print(f"  - Conversations imported: {migrated_conv_count}")
        print(f"  - Messages imported:      {migrated_msg_count}")

    except Exception as e:
        db.rollback()
        print(f"Migration error: {e}")
        raise
    finally:
        db.close()
        sqlite_conn.close()


if __name__ == "__main__":
    run_migration()
