"""
Database Migration - Add Multi-Asset Backtest Columns to portfolio_results table.

This migration adds new columns to support true multi-asset portfolio backtesting:
- equity_curve: Time-series portfolio value
- rebalancing_events: History of rebalancing operations
- asset_contributions: Per-asset return contribution
- optimization_history: Dynamic optimization history
- rebalance_frequency: Rebalancing schedule configuration
- optimization_method: Optimization algorithm used
- per_asset_params: Per-ticker strategy parameters

Run this script to apply the migration:
    python -m scripts.migrations.add_multi_asset_columns
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


def add_multi_asset_columns():
    """
    Add multi-asset backtest columns to portfolio_results table.

    New columns:
    1. equity_curve (JSON) - Time-series portfolio value {date: value}
    2. rebalancing_events (JSON) - [{date, weights, orders, cost}]
    3. asset_contributions (JSON) - {ticker: {return%, weight, contribution%}}
    4. optimization_history (JSON) - [{date, weights, method}]
    5. rebalance_frequency (VARCHAR) - monthly, quarterly, etc.
    6. optimization_method (VARCHAR) - equal_weight, risk_parity, min_variance, markowitz
    7. per_asset_params (JSON) - {ticker: {param: value}}
    """
    db_url = DATABASE_URL or DEFAULT_DB_URL
    engine, SessionLocal = init_database(db_url)

    logger.info("Adding multi-asset columns to portfolio_results table...")

    with engine.connect() as conn:
        # Check database dialect
        dialect = engine.dialect.name
        logger.info(f"Database dialect: {dialect}")

        # Define column additions
        columns_to_add = [
            ("equity_curve", "JSON", "Time-series portfolio value"),
            ("rebalancing_events", "JSON", "Rebalancing event history"),
            ("asset_contributions", "JSON", "Per-asset return contribution"),
            ("optimization_history", "JSON", "Dynamic optimization history"),
            ("rebalance_frequency", "VARCHAR(50)", "Rebalancing schedule"),
            ("optimization_method", "VARCHAR(50)", "Optimization algorithm"),
            ("per_asset_params", "JSON", "Per-ticker strategy parameters"),
        ]

        for column_name, column_type, description in columns_to_add:
            try:
                # Construct ALTER TABLE statement based on dialect
                if dialect == "sqlite":
                    # SQLite doesn't support IF NOT EXISTS for columns
                    # We'll try to add and catch error if exists
                    conn.execute(text(f"""
                        ALTER TABLE portfolio_results
                        ADD COLUMN {column_name} {column_type}
                    """))
                    conn.commit()
                    logger.info(f"✓ Added column: {column_name} ({description})")

                elif dialect == "postgresql":
                    # PostgreSQL supports IF NOT EXISTS
                    conn.execute(text(f"""
                        ALTER TABLE portfolio_results
                        ADD COLUMN IF NOT EXISTS {column_name} {column_type}
                    """))
                    conn.commit()
                    logger.info(f"✓ Added column: {column_name} ({description})")

                elif dialect == "mysql":
                    # MySQL doesn't support IF NOT EXISTS for ADD COLUMN
                    # Check if column exists first
                    check_result = conn.execute(text("""
                        SELECT COUNT(*)
                        FROM INFORMATION_SCHEMA.COLUMNS
                        WHERE TABLE_NAME = 'portfolio_results'
                        AND COLUMN_NAME = :col_name
                    """), {"col_name": column_name})

                    exists = check_result.scalar() > 0

                    if not exists:
                        conn.execute(text(f"""
                            ALTER TABLE portfolio_results
                            ADD COLUMN {column_name} {column_type}
                        """))
                        conn.execute(text("COMMIT"))
                        logger.info(f"✓ Added column: {column_name} ({description})")
                    else:
                        logger.info(f"✓ Column {column_name} already exists")

                else:
                    logger.warning(f"Unknown dialect {dialect}, using generic syntax")
                    conn.execute(text(f"""
                        ALTER TABLE portfolio_results
                        ADD COLUMN {column_name} {column_type}
                    """))
                    conn.commit()
                    logger.info(f"✓ Added column: {column_name} ({description})")

            except Exception as e:
                error_str = str(e).lower()
                # Check if error is due to column already existing
                if any(phrase in error_str for phrase in [
                    "already exists",
                    "duplicate column",
                    "duplicate",
                    "has already been created",
                    "cannot add"
                ]):
                    logger.info(f"✓ Column {column_name} already exists")
                else:
                    logger.error(f"Failed to add column {column_name}: {e}")
                    raise

        # Commit all changes
        try:
            conn.commit()
        except:
            pass  # Some dialects auto-commit

    logger.info("Migration completed successfully!")

    # Verify columns
    with engine.connect() as conn:
        if dialect == "sqlite":
            result = conn.execute(text("""
                PRAGMA table_info(portfolio_results)
            """))
            columns = [row[1] for row in result]  # Column name is at index 1
            logger.info(f"Current columns: {', '.join(columns)}")

        elif dialect == "postgresql":
            result = conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name='portfolio_results'
                ORDER BY ordinal_position
            """))
            columns = [row[0] for row in result]
            logger.info(f"Current columns: {', '.join(columns)}")

        elif dialect == "mysql":
            result = conn.execute(text("""
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME='portfolio_results'
                ORDER BY ORDINAL_POSITION
            """))
            columns = [row[0] for row in result]
            logger.info(f"Current columns: {', '.join(columns)}")

    engine.dispose()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    try:
        add_multi_asset_columns()
        print("\n✓ Migration completed successfully!")
        print("\nNew columns added to portfolio_results table:")
        print("  - equity_curve (JSON)")
        print("  - rebalancing_events (JSON)")
        print("  - asset_contributions (JSON)")
        print("  - optimization_history (JSON)")
        print("  - rebalance_frequency (VARCHAR)")
        print("  - optimization_method (VARCHAR)")
        print("  - per_asset_params (JSON)")
    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
