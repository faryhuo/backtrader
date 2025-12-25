"""
Site Configuration Mixin - Site configuration methods for SettingsStorage.

Handles landing page content and branding settings.
"""

import logging
import os
from datetime import datetime
from typing import Dict, Optional, Any

from sqlalchemy.orm import Session

from src.db.models import UserSettingsModel

from .base import DEFAULT_SETTINGS

logger = logging.getLogger(__name__)


class SiteConfigMixin:
    """Mixin providing site configuration methods."""

    SITE_CONFIG_FIELDS = [
        "site_title", "site_description",
        "site_docs_url", "site_github_url", "site_twitter_url", "site_email",
        "site_stats_strategies", "site_stats_backtests", "site_stats_users"
    ]

    SITE_CONFIG_ENV_MAPPING = {
        "site_title": "SITE_TITLE",
        "site_description": "SITE_DESCRIPTION",
        "site_docs_url": "SITE_DOCS_URL",
        "site_github_url": "SITE_GITHUB_URL",
        "site_twitter_url": "SITE_TWITTER_URL",
        "site_email": "SITE_EMAIL",
        "site_stats_strategies": "SITE_STATS_STRATEGIES",
        "site_stats_backtests": "SITE_STATS_BACKTESTS",
        "site_stats_users": "SITE_STATS_USERS",
    }

    SITE_CONFIG_DEFAULTS = {
        "site_title": "Backtrader Pro",
        "site_description": "Professional quantitative trading platform",
        "site_docs_url": "",
        "site_github_url": "",
        "site_twitter_url": "",
        "site_email": "",
        "site_stats_strategies": "50+",
        "site_stats_backtests": "10K+",
        "site_stats_users": "1K+",
    }

    def get_site_config(
        self,
        user_id: Optional[str] = None,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Get site configuration with DB-first, env fallback.

        Args:
            user_id: User identifier (typically None for site-wide config)
            db: Optional database session

        Returns:
            Dict with site configuration and sources
        """
        with self.managed_session(db, commit_on_success=False) as session:
            normalized_user_id = self._normalize_user_id(user_id)
            
            settings = session.query(UserSettingsModel).filter(
                UserSettingsModel.user_id == normalized_user_id
            ).first()

            result = {}
            sources = {}

            for field in self.SITE_CONFIG_FIELDS:
                db_value = getattr(settings, field, None) if settings else None
                
                if db_value is not None:
                    result[field] = db_value
                    sources[field] = "database"
                else:
                    env_key = self.SITE_CONFIG_ENV_MAPPING.get(field, field.upper())
                    env_value = os.getenv(env_key)
                    
                    if env_value:
                        result[field] = env_value
                        sources[field] = "env"
                    else:
                        result[field] = self.SITE_CONFIG_DEFAULTS.get(field, "")
                        sources[field] = "default"

            return {"config": result, "sources": sources}

    def save_site_config(
        self,
        config: Dict[str, str],
        user_id: Optional[str] = None,
        db: Optional[Session] = None
    ) -> bool:
        """
        Save site configuration to database.

        Args:
            config: Dict with site config fields
            user_id: User identifier (typically None for site-wide config)
            db: Optional database session

        Returns:
            True if successful, False otherwise
        """
        with self.managed_session(db) as session:
            try:
                normalized_user_id = self._normalize_user_id(user_id)
                settings = self._get_or_create_settings(normalized_user_id, session)

                for field in self.SITE_CONFIG_FIELDS:
                    if field in config:
                        setattr(settings, field, config[field])

                settings.updated_at = datetime.utcnow()
                
                logger.info(f"Saved site config for user {normalized_user_id}")
                return True

            except Exception as e:
                logger.error(f"Failed to save site config: {e}")
                return False

    def reset_site_config(
        self,
        user_id: Optional[str] = None,
        db: Optional[Session] = None
    ) -> bool:
        """
        Reset site configuration to defaults (removes DB values).

        Args:
            user_id: User identifier
            db: Optional database session

        Returns:
            True if successful, False otherwise
        """
        with self.managed_session(db) as session:
            try:
                normalized_user_id = self._normalize_user_id(user_id)

                settings = session.query(UserSettingsModel).filter(
                    UserSettingsModel.user_id == normalized_user_id
                ).first()

                if settings:
                    for field in self.SITE_CONFIG_FIELDS:
                        setattr(settings, field, None)
                    settings.updated_at = datetime.utcnow()
                    logger.info(f"Reset site config for user {normalized_user_id}")

                return True

            except Exception as e:
                logger.error(f"Failed to reset site config: {e}")
                return False
