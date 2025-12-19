"""
Database migration to add credential fields to user_settings table.

This migration adds encrypted credential storage fields for:
- OpenAI API configuration
- Logto authentication configuration
- HTTP/HTTPS proxy settings
- CCXT exchange credentials (JSON structure)

Migration is safe to run multiple times (uses IF NOT EXISTS where applicable).

Usage:
    python -m src.db.migrations.add_credential_fields

Author: Generated for credential management feature
Date: 2025-12-16
"""

import sys
import os
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, text, Column, Text, String, Boolean, JSON
from sqlalchemy.orm import sessionmaker
from src.db.models import Base, UserSettingsModel
from src.config.settings import DATABASE_URL
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_migration(database_url: str = None):
    """
    Add credential fields to user_settings table.

    Args:
        database_url: Database connection string (defaults to DATABASE_URL from settings)
    """
    if not database_url:
        database_url = DATABASE_URL or "sqlite:///trading_sessions.db"

    logger.info(f"Starting migration on database: {database_url}")

    try:
        # Create engine and session
        engine = create_engine(database_url, echo=False)
        Session = sessionmaker(bind=engine)
        session = Session()

        # Detect database type
        is_sqlite = database_url.startswith("sqlite")
        is_postgresql = "postgresql" in database_url
        is_mysql = "mysql" in database_url

        logger.info(f"Database type detected: {'SQLite' if is_sqlite else 'PostgreSQL' if is_postgresql else 'MySQL' if is_mysql else 'Unknown'}")

        # Check if user_settings table exists
        with engine.connect() as conn:
            if is_sqlite:
                result = conn.execute(text(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='user_settings'"
                ))
            elif is_postgresql:
                result = conn.execute(text(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema='public' AND table_name='user_settings'"
                ))
            elif is_mysql:
                result = conn.execute(text(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema=DATABASE() AND table_name='user_settings'"
                ))
            else:
                raise ValueError("Unsupported database type")

            table_exists = result.fetchone() is not None

        if not table_exists:
            logger.info("user_settings table does not exist. Creating all tables...")
            Base.metadata.create_all(engine)
            logger.info("All tables created successfully!")
            return

        logger.info("user_settings table exists. Adding new columns...")

        # List of new columns to add
        columns_to_add = [
            ("openai_api_key", "TEXT"),
            ("openai_base_url", "VARCHAR(500)"),
            ("logto_issuer", "VARCHAR(500)"),
            ("logto_jwks_uri", "VARCHAR(500)"),
            ("logto_audience", "VARCHAR(500)"),
            ("logto_required_scopes", "VARCHAR(500)"),
            ("enable_login", "BOOLEAN" if not is_mysql else "TINYINT(1)"),
            ("http_proxy", "VARCHAR(500)"),
            ("https_proxy", "VARCHAR(500)"),
            ("ccxt_credentials", "JSON" if not is_sqlite else "TEXT"),  # SQLite doesn't have native JSON
        ]

        with engine.connect() as conn:
            for column_name, column_type in columns_to_add:
                try:
                    # Check if column exists
                    if is_sqlite:
                        result = conn.execute(text(
                            f"SELECT COUNT(*) FROM pragma_table_info('user_settings') WHERE name='{column_name}'"
                        ))
                        column_exists = result.fetchone()[0] > 0
                    elif is_postgresql:
                        result = conn.execute(text(
                            f"SELECT column_name FROM information_schema.columns "
                            f"WHERE table_name='user_settings' AND column_name='{column_name}'"
                        ))
                        column_exists = result.fetchone() is not None
                    elif is_mysql:
                        result = conn.execute(text(
                            f"SELECT column_name FROM information_schema.columns "
                            f"WHERE table_schema=DATABASE() AND table_name='user_settings' AND column_name='{column_name}'"
                        ))
                        column_exists = result.fetchone() is not None

                    if column_exists:
                        logger.info(f"  ✓ Column '{column_name}' already exists, skipping")
                        continue

                    # Add column
                    if is_sqlite:
                        # SQLite uses simpler ALTER TABLE syntax
                        conn.execute(text(
                            f"ALTER TABLE user_settings ADD COLUMN {column_name} {column_type}"
                        ))
                    else:
                        # PostgreSQL/MySQL syntax
                        conn.execute(text(
                            f"ALTER TABLE user_settings ADD COLUMN {column_name} {column_type}"
                        ))

                    conn.commit()
                    logger.info(f"  ✓ Added column '{column_name}' ({column_type})")

                except Exception as e:
                    logger.warning(f"  ⚠ Could not add column '{column_name}': {e}")
                    # Don't fail the entire migration if one column fails
                    continue

        logger.info("Migration completed successfully!")
        logger.info("\nNext steps:")
        logger.info("1. Set ENCRYPTION_KEY in your .env file:")
        logger.info("   python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\"")
        logger.info("2. Restart the backend server")
        logger.info("3. Configure credentials via Settings page UI")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise
    finally:
        if 'session' in locals():
            session.close()


def rollback_migration(database_url: str = None):
    """
    Rollback migration by removing credential fields.

    WARNING: This will delete all stored credentials!

    Args:
        database_url: Database connection string (defaults to DATABASE_URL from settings)
    """
    if not database_url:
        database_url = DATABASE_URL or "sqlite:///trading_sessions.db"

    logger.warning("ROLLBACK: Removing credential fields from user_settings table")
    logger.warning("This will DELETE all stored credentials!")

    try:
        engine = create_engine(database_url, echo=False)
        is_sqlite = database_url.startswith("sqlite")

        if is_sqlite:
            logger.error("SQLite does not support DROP COLUMN. Manual rollback required:")
            logger.error("1. Backup your database")
            logger.error("2. Recreate user_settings table without credential columns")
            logger.error("3. Copy old data to new table")
            return

        columns_to_drop = [
            "openai_api_key",
            "openai_base_url",
            "logto_issuer",
            "logto_jwks_uri",
            "logto_audience",
            "logto_required_scopes",
            "enable_login",
            "http_proxy",
            "https_proxy",
            "ccxt_credentials",
        ]

        with engine.connect() as conn:
            for column_name in columns_to_drop:
                try:
                    conn.execute(text(
                        f"ALTER TABLE user_settings DROP COLUMN {column_name}"
                    ))
                    conn.commit()
                    logger.info(f"  ✓ Dropped column '{column_name}'")
                except Exception as e:
                    logger.warning(f"  ⚠ Could not drop column '{column_name}': {e}")

        logger.info("Rollback completed!")

    except Exception as e:
        logger.error(f"Rollback failed: {e}")
        raise


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="User settings credential fields migration")
    parser.add_argument(
        "--rollback",
        action="store_true",
        help="Rollback migration (WARNING: deletes all credentials)"
    )
    parser.add_argument(
        "--database-url",
        type=str,
        help="Database URL (defaults to DATABASE_URL environment variable)"
    )

    args = parser.parse_args()

    if args.rollback:
        confirm = input("Are you sure you want to rollback? This will DELETE all credentials! (yes/no): ")
        if confirm.lower() == "yes":
            rollback_migration(args.database_url)
        else:
            logger.info("Rollback cancelled")
    else:
        run_migration(args.database_url)
