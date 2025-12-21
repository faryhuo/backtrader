"""
Strategy Version Storage - Database operations for strategy version management.

This module provides CRUD operations for strategy versions, enabling
version history tracking, diff comparison, and rollback functionality.
"""

import hashlib
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import desc
from sqlalchemy.exc import IntegrityError

from src.config.settings import DATABASE_URL
from src.db.storage.base import BaseStorage
from src.db.models import StrategyVersionModel, init_database

logger = logging.getLogger(__name__)


def compute_code_hash(code: str) -> str:
    """Compute SHA-256 hash of code for change detection."""
    return hashlib.sha256(code.encode('utf-8')).hexdigest()


def count_line_changes(old_code: str, new_code: str) -> tuple[int, int]:
    """Count lines added and removed between two code versions."""
    old_lines = set(old_code.splitlines()) if old_code else set()
    new_lines = set(new_code.splitlines())
    
    lines_added = len(new_lines - old_lines)
    lines_removed = len(old_lines - new_lines)
    
    return lines_added, lines_removed


class StrategyVersionStorage(BaseStorage):
    """Storage layer for strategy version management."""

    def __init__(self, database_url: str = None):
        """Initialize storage with database connection."""
        super().__init__(database_url)
        # Alias for backward compatibility with existing code
        self.engine = self._engine
        self.session_local = self._SessionLocal

    def _get_next_version_number(self, session, strategy_name: str, 
                                  user_id: str = None) -> int:
        """Get the next version number for a strategy."""
        query = session.query(StrategyVersionModel.version_number).filter(
            StrategyVersionModel.strategy_name == strategy_name
        )
        if user_id:
            query = query.filter(StrategyVersionModel.user_id == user_id)
        else:
            query = query.filter(StrategyVersionModel.user_id.is_(None))
        
        latest = query.order_by(desc(StrategyVersionModel.version_number)).first()
        return (latest[0] + 1) if latest else 1

    def _get_latest_version(self, session, strategy_name: str,
                            user_id: str = None) -> Optional[StrategyVersionModel]:
        """Get the latest version of a strategy."""
        query = session.query(StrategyVersionModel).filter(
            StrategyVersionModel.strategy_name == strategy_name
        )
        if user_id:
            query = query.filter(StrategyVersionModel.user_id == user_id)
        else:
            query = query.filter(StrategyVersionModel.user_id.is_(None))
        
        return query.order_by(desc(StrategyVersionModel.version_number)).first()

    def create_version(self, strategy_name: str, code: str,
                       user_id: str = None, commit_message: str = None) -> dict:
        """
        Create a new version of a strategy.
        
        Args:
            strategy_name: Name of the strategy
            code: Full source code of the strategy
            user_id: Optional user ID for multi-user support
            commit_message: Optional description of changes
            
        Returns:
            dict with version details including version_number, created_at
        """
        session = self.session_local()
        try:
            code_hash = compute_code_hash(code)
            
            # Check if code has actually changed
            latest = self._get_latest_version(session, strategy_name, user_id)
            if latest and latest.code_hash == code_hash:
                # No changes, return existing version info
                return {
                    "version_number": latest.version_number,
                    "created_at": latest.created_at.isoformat(),
                    "is_new": False,
                    "message": "No changes detected"
                }
            
            # Calculate change statistics
            previous_code = latest.code if latest else ""
            lines_added, lines_removed = count_line_changes(previous_code, code)
            
            # Get next version number
            version_number = self._get_next_version_number(
                session, strategy_name, user_id
            )
            
            # Create version record
            version = StrategyVersionModel(
                version_number=version_number,
                strategy_name=strategy_name,
                user_id=user_id,
                commit_message=commit_message,
                code=code,
                code_hash=code_hash,
                lines_added=lines_added,
                lines_removed=lines_removed,
                created_at=datetime.now(timezone.utc)
            )
            
            session.add(version)
            session.commit()
            
            logger.info(
                f"Created version {version_number} for strategy '{strategy_name}'"
            )
            
            return {
                "version_number": version_number,
                "created_at": version.created_at.isoformat(),
                "lines_added": lines_added,
                "lines_removed": lines_removed,
                "is_new": True
            }
            
        except IntegrityError as e:
            session.rollback()
            logger.error(f"Failed to create version: {e}")
            raise
        finally:
            session.close()

    def list_versions(self, strategy_name: str, user_id: str = None,
                      limit: int = 50, offset: int = 0) -> dict:
        """
        List all versions of a strategy.
        
        Args:
            strategy_name: Name of the strategy
            user_id: Optional user ID filter
            limit: Maximum number of versions to return
            offset: Number of versions to skip
            
        Returns:
            dict with versions list and pagination info
        """
        session = self.session_local()
        try:
            query = session.query(StrategyVersionModel).filter(
                StrategyVersionModel.strategy_name == strategy_name
            )
            if user_id:
                query = query.filter(StrategyVersionModel.user_id == user_id)
            else:
                query = query.filter(StrategyVersionModel.user_id.is_(None))
            
            # Get total count
            total = query.count()
            
            # Get versions with pagination
            versions = query.order_by(
                desc(StrategyVersionModel.version_number)
            ).offset(offset).limit(limit).all()
            
            return {
                "versions": [
                    {
                        "version_number": v.version_number,
                        "commit_message": v.commit_message,
                        "lines_added": v.lines_added,
                        "lines_removed": v.lines_removed,
                        "created_at": v.created_at.isoformat(),
                    }
                    for v in versions
                ],
                "total": total,
                "limit": limit,
                "offset": offset
            }
            
        finally:
            session.close()

    def get_version(self, strategy_name: str, version_number: int,
                    user_id: str = None) -> Optional[dict]:
        """
        Get a specific version of a strategy.
        
        Args:
            strategy_name: Name of the strategy
            version_number: Version number to retrieve
            user_id: Optional user ID filter
            
        Returns:
            dict with full version details including code, or None if not found
        """
        session = self.session_local()
        try:
            query = session.query(StrategyVersionModel).filter(
                StrategyVersionModel.strategy_name == strategy_name,
                StrategyVersionModel.version_number == version_number
            )
            if user_id:
                query = query.filter(StrategyVersionModel.user_id == user_id)
            else:
                query = query.filter(StrategyVersionModel.user_id.is_(None))
            
            version = query.first()
            
            if not version:
                return None
            
            return {
                "version_number": version.version_number,
                "strategy_name": version.strategy_name,
                "commit_message": version.commit_message,
                "code": version.code,
                "code_hash": version.code_hash,
                "lines_added": version.lines_added,
                "lines_removed": version.lines_removed,
                "created_at": version.created_at.isoformat(),
            }
            
        finally:
            session.close()

    def get_latest_version(self, strategy_name: str, 
                           user_id: str = None) -> Optional[dict]:
        """Get the most recent version of a strategy."""
        session = self.session_local()
        try:
            version = self._get_latest_version(session, strategy_name, user_id)
            
            if not version:
                return None
            
            return {
                "version_number": version.version_number,
                "strategy_name": version.strategy_name,
                "commit_message": version.commit_message,
                "code": version.code,
                "lines_added": version.lines_added,
                "lines_removed": version.lines_removed,
                "created_at": version.created_at.isoformat(),
            }
            
        finally:
            session.close()
