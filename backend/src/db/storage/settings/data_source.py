"""
Data Source Mixin - Data source configuration methods for SettingsStorage.

Handles data source priority and EODHD API key management.
"""

import logging
import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any

from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from src.db.models import UserSettingsModel
from src.utils.encryption import encrypt_value, decrypt_value, mask_credential

from .base import DEFAULT_SETTINGS

logger = logging.getLogger(__name__)


class DataSourceMixin:
    """Mixin providing data source configuration methods."""

    DEFAULT_DATA_SOURCE_PRIORITY = ["yahoo", "database"]
    VALID_DATA_SOURCES = {"yahoo", "eodhd", "database"}

    def get_data_source_settings(
        self,
        user_id: Optional[str] = None,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Get data source configuration with fallback to defaults.

        Args:
            user_id: User identifier
            db: Optional database session

        Returns:
            Dict with data_source_priority list and eodhd_api_key (masked)
        """
        close_db = False
        if db is None:
            db = self.get_db_session()
            close_db = True

        try:
            normalized_user_id = self._normalize_user_id(user_id)

            settings = db.query(UserSettingsModel).filter(
                UserSettingsModel.user_id == normalized_user_id
            ).first()

            result = {
                "data_source_priority": self.DEFAULT_DATA_SOURCE_PRIORITY.copy(),
                "eodhd_api_key": None,
                "eodhd_api_key_source": "none",
            }

            if settings:
                if settings.data_source_priority:
                    priority = settings.data_source_priority
                    if isinstance(priority, str):
                        priority = json.loads(priority)
                    result["data_source_priority"] = priority

                if settings.eodhd_api_key:
                    decrypted = decrypt_value(settings.eodhd_api_key)
                    result["eodhd_api_key"] = mask_credential(decrypted) if decrypted else None
                    result["eodhd_api_key_source"] = "database"

            if result["eodhd_api_key"] is None:
                env_key = os.getenv("EODHD_API_KEY")
                if env_key:
                    result["eodhd_api_key"] = mask_credential(env_key)
                    result["eodhd_api_key_source"] = "env"

            return result

        finally:
            if close_db:
                db.close()

    def get_data_source_priority(
        self,
        user_id: Optional[str] = None,
        db: Optional[Session] = None
    ) -> List[str]:
        """
        Get the data source priority list (unmasked, for internal use).

        Args:
            user_id: User identifier
            db: Optional database session

        Returns:
            List of data source names in priority order
        """
        close_db = False
        if db is None:
            db = self.get_db_session()
            close_db = True

        try:
            normalized_user_id = self._normalize_user_id(user_id)

            settings = db.query(UserSettingsModel).filter(
                UserSettingsModel.user_id == normalized_user_id
            ).first()

            if settings and settings.data_source_priority:
                priority = settings.data_source_priority
                if isinstance(priority, str):
                    priority = json.loads(priority)
                return [s for s in priority if s in self.VALID_DATA_SOURCES]

            return self.DEFAULT_DATA_SOURCE_PRIORITY.copy()

        finally:
            if close_db:
                db.close()

    def get_eodhd_api_key(
        self,
        user_id: Optional[str] = None,
        db: Optional[Session] = None
    ) -> Optional[str]:
        """
        Get the EODHD API key (decrypted, for internal use).

        Args:
            user_id: User identifier
            db: Optional database session

        Returns:
            Decrypted API key or None
        """
        db_value = self.get_credential("eodhd_api_key", user_id, db)
        if db_value:
            return db_value

        return os.getenv("EODHD_API_KEY")

    def save_data_source_settings(
        self,
        data_source_priority: Optional[List[str]] = None,
        eodhd_api_key: Optional[str] = None,
        user_id: Optional[str] = None,
        db: Optional[Session] = None
    ) -> bool:
        """
        Save data source configuration.

        Args:
            data_source_priority: List of data sources in priority order
            eodhd_api_key: EODHD API key (will be encrypted)
            user_id: User identifier
            db: Optional database session

        Returns:
            True if successful, False otherwise
        """
        close_db = False
        if db is None:
            db = self.get_db_session()
            close_db = True

        try:
            normalized_user_id = self._normalize_user_id(user_id)
            settings = self._get_or_create_settings(normalized_user_id, db)

            if data_source_priority is not None:
                valid_priority = [s for s in data_source_priority if s in self.VALID_DATA_SOURCES]
                if not valid_priority:
                    valid_priority = self.DEFAULT_DATA_SOURCE_PRIORITY.copy()
                settings.data_source_priority = valid_priority
                flag_modified(settings, "data_source_priority")

            if eodhd_api_key is not None:
                if eodhd_api_key:
                    settings.eodhd_api_key = encrypt_value(eodhd_api_key)
                else:
                    settings.eodhd_api_key = None

            settings.updated_at = datetime.utcnow()
            db.commit()

            logger.info(f"Saved data source settings for user {normalized_user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to save data source settings: {e}")
            db.rollback()
            return False
        finally:
            if close_db:
                db.close()

    def reset_data_source_settings(
        self,
        user_id: Optional[str] = None,
        db: Optional[Session] = None
    ) -> bool:
        """
        Reset data source settings to defaults.

        Args:
            user_id: User identifier
            db: Optional database session

        Returns:
            True if successful, False otherwise
        """
        close_db = False
        if db is None:
            db = self.get_db_session()
            close_db = True

        try:
            normalized_user_id = self._normalize_user_id(user_id)

            settings = db.query(UserSettingsModel).filter(
                UserSettingsModel.user_id == normalized_user_id
            ).first()

            if settings:
                settings.data_source_priority = None
                settings.eodhd_api_key = None
                settings.updated_at = datetime.utcnow()
                db.commit()
                logger.info(f"Reset data source settings for user {normalized_user_id}")

            return True

        except Exception as e:
            logger.error(f"Failed to reset data source settings: {e}")
            db.rollback()
            return False
        finally:
            if close_db:
                db.close()
