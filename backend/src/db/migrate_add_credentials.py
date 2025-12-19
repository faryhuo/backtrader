"""
Database Migration: Add credential columns to user_settings table.

This script adds the credential columns (openai_api_key, openai_base_url, etc.)
to the existing user_settings table if they don't already exist.
"""

import sqlite3
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database path
DB_PATH = Path(__file__).parent.parent.parent / "trading_sessions.db"


def column_exists(cursor, table_name, column_name):
    """Check if a column exists in a table."""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns


def migrate():
    """Add credential columns to user_settings table."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Check if user_settings table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_settings'")
        if not cursor.fetchone():
            logger.info("Table 'user_settings' does not exist. Creating it would be handled by the ORM.")
            return

        logger.info(f"Migrating database: {DB_PATH}")

        # List of columns to add
        columns_to_add = [
            ("openai_api_key", "TEXT"),
            ("openai_base_url", "VARCHAR(500)"),
            ("logto_issuer", "VARCHAR(500)"),
            ("logto_jwks_uri", "VARCHAR(500)"),
            ("logto_audience", "VARCHAR(500)"),
            ("logto_required_scopes", "VARCHAR(500)"),
            ("enable_login", "BOOLEAN"),
            ("http_proxy", "VARCHAR(500)"),
            ("https_proxy", "VARCHAR(500)"),
            ("ccxt_credentials", "TEXT"),  # JSON column stored as TEXT
        ]

        for column_name, column_type in columns_to_add:
            if not column_exists(cursor, "user_settings", column_name):
                logger.info(f"Adding column: {column_name} ({column_type})")
                cursor.execute(f"ALTER TABLE user_settings ADD COLUMN {column_name} {column_type}")
            else:
                logger.info(f"Column already exists: {column_name}")

        conn.commit()
        logger.info("Migration completed successfully!")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
