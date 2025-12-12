"""
Database migration script to clean up corrupted JSON data.

This script fixes records with invalid JSON in metrics and ai_analysis columns.
Run this after updating the models to use SafeJSON type.

Usage:
    python -m src.db.migrate_cleanup_json
"""

import logging
import os
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def cleanup_corrupted_json(database_url: str = "sqlite:///trading_sessions.db"):
    """
    Clean up corrupted JSON records in the database.

    Args:
        database_url: Database connection string
    """
    logger.info(f"Connecting to database: {database_url}")
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Delete records with NULL or empty metrics
        result = session.execute(
            text(
                "DELETE FROM backtest_history WHERE "
                "metrics IS NULL OR metrics = ''"
            )
        )
        deleted_metrics = result.rowcount

        # Delete records with empty ai_analysis (empty string, not NULL)
        result = session.execute(
            text(
                "DELETE FROM backtest_history WHERE "
                "ai_analysis = ''"
            )
        )
        deleted_ai = result.rowcount

        session.commit()

        total_deleted = max(deleted_metrics, deleted_ai)
        logger.info(f"✓ Deleted {total_deleted} corrupted records")

        # Count remaining records
        result = session.execute(text("SELECT COUNT(*) FROM backtest_history"))
        remaining = result.scalar()
        logger.info(f"✓ Remaining backtest records: {remaining}")

        return total_deleted

    except Exception as e:
        logger.error(f"✗ Migration failed: {e}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    # Use DATABASE_URL from environment if available
    database_url = os.getenv("DATABASE_URL", "sqlite:///trading_sessions.db")

    logger.info("=" * 60)
    logger.info("Starting JSON cleanup migration")
    logger.info("=" * 60)

    deleted = cleanup_corrupted_json(database_url)

    logger.info("=" * 60)
    logger.info(f"Migration completed successfully!")
    logger.info(f"Total records cleaned: {deleted}")
    logger.info("=" * 60)
