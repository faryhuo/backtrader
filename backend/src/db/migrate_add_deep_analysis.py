"""
Database migration script to add deep_analysis column to backtest_history table.

Run this script once to upgrade existing databases:
    python -m src.db.migrate_add_deep_analysis
"""

import logging
from sqlalchemy import text

from src.config.settings import DATABASE_URL, DEFAULT_DB_URL
from src.db.models import init_database

logger = logging.getLogger(__name__)


def migrate_add_deep_analysis_column():
    """Add deep_analysis column to backtest_history table if not exists."""
    db_url = DATABASE_URL or DEFAULT_DB_URL
    engine, SessionLocal = init_database(db_url)

    session = SessionLocal()

    try:
        # Check if column already exists
        result = session.execute(text("PRAGMA table_info(backtest_history)"))
        columns = [row[1] for row in result.fetchall()]

        if "deep_analysis" in columns:
            logger.info("Column 'deep_analysis' already exists in backtest_history table")
            return

        # Add the column
        logger.info("Adding 'deep_analysis' column to backtest_history table...")
        session.execute(text(
            "ALTER TABLE backtest_history ADD COLUMN deep_analysis TEXT"
        ))
        session.commit()
        logger.info("Successfully added 'deep_analysis' column")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        session.rollback()
        raise
    finally:
        session.close()
        engine.dispose()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    migrate_add_deep_analysis_column()
    print("Migration completed successfully!")
