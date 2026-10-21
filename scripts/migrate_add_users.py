"""
scripts/migrate_add_users.py
============================
Non-destructive database migration script:
1. Creates the `users` table if it does not already exist.
2. Safely adds the nullable `user_id` foreign key column and index to `conversations`.
3. Preserves all existing conversations and messages without data loss.
4. Idempotent: safe to run multiple times.
"""

import os
import sys
import logging

# Ensure project root in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import inspect, text
from src.database import engine, Base, User, Conversation

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("migration")


def run_migration():
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    with engine.connect() as conn:
        # Step 1: Create users table if missing
        if "users" not in existing_tables:
            logger.info("Table 'users' not found. Creating 'users' table...")
            User.__table__.create(bind=engine, checkfirst=True)
            logger.info("Table 'users' created successfully.")
        else:
            logger.info("Table 'users' already exists.")

        # Step 2: Check for user_id column in conversations table
        conv_columns = [col["name"] for col in inspector.get_columns("conversations")]
        if "user_id" not in conv_columns:
            logger.info("Adding 'user_id' column to 'conversations' table...")
            conn.execute(text("ALTER TABLE conversations ADD COLUMN user_id VARCHAR(64) NULL;"))
            conn.commit()
            logger.info("Column 'user_id' added successfully.")

            # Add foreign key and index
            try:
                conn.execute(
                    text(
                        "ALTER TABLE conversations "
                        "ADD CONSTRAINT fk_conversations_user "
                        "FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;"
                    )
                )
                conn.commit()
                logger.info("Foreign key constraint 'fk_conversations_user' added successfully.")
            except Exception as e:
                logger.warning(f"Could not add foreign key constraint (may already exist or unsupported): {e}")

            try:
                conn.execute(text("CREATE INDEX idx_conversations_user_id ON conversations(user_id);"))
                conn.commit()
                logger.info("Index 'idx_conversations_user_id' created successfully.")
            except Exception as e:
                logger.warning(f"Could not create index (may already exist): {e}")
        else:
            logger.info("Column 'user_id' already exists in 'conversations'.")

        # Step 3: Verify existing data integrity
        conv_count = conn.execute(text("SELECT COUNT(*) FROM conversations")).scalar()
        msg_count = conn.execute(text("SELECT COUNT(*) FROM messages")).scalar()
        user_count = conn.execute(text("SELECT COUNT(*) FROM users")).scalar()

        logger.info(
            f"Migration verified: {user_count} users, {conv_count} conversations, {msg_count} messages."
        )


if __name__ == "__main__":
    run_migration()
