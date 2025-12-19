"""
Database Migration: Add params column to backtest_history table.

This script adds the 'params' column to the existing backtest_history table
to store strategy parameter overrides.
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
    """Add params column to backtest_history table."""
    if not DB_PATH.exists():
        logger.info(f"Database does not exist: {DB_PATH}")
        logger.info("No migration needed - tables will be created with new schema on first run.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Check if backtest_history table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='backtest_history'")
        if not cursor.fetchone():
            logger.info("Table 'backtest_history' does not exist. It will be created by the ORM.")
            return

        logger.info(f"Migrating database: {DB_PATH}")

        # Add params column if it doesn't exist
        if not column_exists(cursor, "backtest_history", "params"):
            logger.info("Adding column: params (TEXT)")
            cursor.execute("ALTER TABLE backtest_history ADD COLUMN params TEXT")
            conn.commit()
            logger.info("Migration completed successfully!")
        else:
            logger.info("Column 'params' already exists. No migration needed.")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
