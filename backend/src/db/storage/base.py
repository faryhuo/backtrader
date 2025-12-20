"""
Base Storage - Common base class for all storage layers.

Provides shared database initialization and session management.
"""

import logging
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy.orm import Session

from src.config.settings import DATABASE_URL
from src.db.models import init_database

logger = logging.getLogger(__name__)


class BaseStorage:
    """
    Base class for all storage layers.

    Provides common database initialization and session management
    to eliminate code duplication across storage classes.
    """

    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize storage with database connection.

        Args:
            database_url: SQLAlchemy database URL (defaults to DATABASE_URL from settings)
        """
        self.database_url = database_url or DATABASE_URL
        self._engine, self._SessionLocal = init_database(self.database_url)

    def get_db_session(self) -> Session:
        """
        Get a new database session.

        Returns:
            SQLAlchemy session instance

        Note:
            Caller is responsible for closing the session when using this method directly.
            Prefer using session_scope() context manager for automatic handling.
        """
        return self._SessionLocal()

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """
        Context manager for database sessions with automatic commit/rollback.

        Usage:
            with storage.session_scope() as db:
                # ... use db ...
            # auto-commits on success, rolls back on exception

        Yields:
            SQLAlchemy session
        """
        session = self.get_db_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def _manage_session(self, db: Optional[Session]):
        """
        Helper to determine if we should manage (close) a session.

        Args:
            db: Existing session or None

        Returns:
            Tuple of (session, should_close)
        """
        if db is None:
            return self.get_db_session(), True
        return db, False


__all__ = ["BaseStorage"]
