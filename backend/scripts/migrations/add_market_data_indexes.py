"""
Database Migration - Add Performance Indexes for market_data table.

This migration adds composite indexes to improve query performance for:
- market_data table: ticker + date queries (most common query pattern)

Run this script to apply the migration:
    python -m scripts.migrations.add_market_data_indexes
"""

import logging
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import text
from src.db.models import init_database
from src.config.settings import DATABASE_URL, DEFAULT_DB_URL

logger = logging.getLogger(__name__)


def add_market_data_indexes():
    """
    Add performance indexes to market_data table.
    
    Indexes created:
    1. idx_market_data_ticker_date_range - Composite index on (ticker, date DESC)
       - Optimizes queries filtering by ticker and date range
       - Supports efficient sorting by date
    """
    db_url = DATABASE_URL or DEFAULT_DB_URL
    engine, SessionLocal = init_database(db_url)
    
    logger.info("Adding performance indexes to market_data table...")
    
    with engine.connect() as conn:
        # Check database dialect
        dialect = engine.dialect.name
        logger.info(f"Database dialect: {dialect}")
        
        # Create composite index for ticker + date range queries
        # This is the most common query pattern in get_data_from_db()
        try:
            if dialect == "sqlite":
                # SQLite syntax
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_market_data_ticker_date_range
                    ON market_data(ticker, date DESC)
                """))
            elif dialect == "postgresql":
                # PostgreSQL syntax
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_market_data_ticker_date_range
                    ON market_data(ticker, date DESC)
                """))
            elif dialect == "mysql":
                # MySQL syntax
                conn.execute(text("""
                    CREATE INDEX idx_market_data_ticker_date_range
                    ON market_data(ticker, date DESC)
                """))
                conn.execute(text("COMMIT"))
            else:
                logger.warning(f"Unknown dialect {dialect}, using generic syntax")
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_market_data_ticker_date_range
                    ON market_data(ticker, date DESC)
                """))
            
            conn.commit()
            logger.info("✓ Created composite index: idx_market_data_ticker_date_range")
        
        except Exception as e:
            # Index might already exist
            if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                logger.info("✓ Index idx_market_data_ticker_date_range already exists")
            else:
                logger.error(f"Failed to create composite index: {e}")
                raise
    
    logger.info("Index migration completed successfully!")
    
    # Verify indexes
    with engine.connect() as conn:
        if dialect == "sqlite":
            result = conn.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='index' AND tbl_name='market_data'
                ORDER BY name
            """))
            indexes = [row[0] for row in result]
            logger.info(f"Current indexes on market_data: {indexes}")
        elif dialect == "postgresql":
            result = conn.execute(text("""
                SELECT indexname FROM pg_indexes 
                WHERE tablename='market_data'
                ORDER BY indexname
            """))
            indexes = [row[0] for row in result]
            logger.info(f"Current indexes on market_data: {indexes}")
    
    engine.dispose()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    try:
        add_market_data_indexes()
        print("\n✓ Migration completed successfully!")
    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        sys.exit(1)
