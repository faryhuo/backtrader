"""
Settings Base - Core settings storage functionality.

Contains the base SettingsStorage class with core AI settings methods.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.db.storage.base import BaseStorage
from src.db.models import UserSettingsModel

logger = logging.getLogger(__name__)

# Default settings matching frontend/src/pages/Settings.jsx
DEFAULT_SETTINGS = {
    "selected_models": "gpt-5.1,deepseek-v3.1",
    "code_analysis_prompt": (
        "Please analyze the following Backtrader strategy code. "
        "Explain its logic, potential pitfalls, and suggest improvements:\n\n{code}"
    ),
    "code_rewrite_prompt": (
        "Please rewrite and optimize the following Backtrader strategy code "
        "to follow best practices and fix potential issues. "
        "Return ONLY the python code, no markdown formatting or explanation:\n\n{code}"
    ),
    "full_strategy_analysis_prompt": (
        "Please analyze the trading strategy based on the following configurations, "
        "source code, performance metrics, the attached equity curve chart, "
        "and the recent trading logs.\n\n{contextText}\n\n{metricsText}\n\n{logsText}\n\n"
        "Provide a comprehensive assessment including:\n"
        "1. Overall Performance: Is it profitable and consistent?\n"
        "2. Risk Profile: analysis of drawdowns and volatility.\n"
        "3. Strengths & Weaknesses: What is working well and what isn't?\n"
        "4. Suggestions: Recommendations for improvement.\n"
        "5. Code Analysis: Comments on the strategy logic.\n"
        "6. Always return with Chinese.\n"
        "7. 不需要对策略代码逻辑进行点评"
    )
}


class SettingsStorageBase(BaseStorage):
    """
    Base storage layer for user settings.

    Provides core methods for AI configuration and prompt templates.
    """

    def __init__(self, database_url: Optional[str] = None):
        """Initialize settings storage.

        Args:
            database_url: SQLAlchemy database URL (defaults to DATABASE_URL from settings)
        """
        super().__init__(database_url)
        logger.info(f"SettingsStorage initialized with database: {self.database_url}")

    def get_settings(
        self,
        user_id: Optional[str] = None,
        db=None
    ) -> Dict[str, object]:
        """
        Get user settings from database.

        Args:
            user_id: User identifier (None or "anonymous" for anonymous users)
            db: Optional database session

        Returns:
            Dict with settings fields, or defaults if not found
        """
        with self.managed_session(db, commit_on_success=False) as session:
            normalized_user_id = self._normalize_user_id(user_id)

            settings = session.query(UserSettingsModel).filter(
                UserSettingsModel.user_id == normalized_user_id
            ).first()

            if settings:
                return self._model_to_dict(settings)
            else:
                logger.debug(f"No settings found for user {normalized_user_id}, returning defaults")
                return self._get_default_dict()

    def save_settings(
        self,
        selected_models: Optional[List[str]],
        code_analysis_prompt: str,
        code_rewrite_prompt: str,
        full_strategy_analysis_prompt: str,
        user_id: Optional[str] = None,
        db: Optional[Session] = None
    ) -> Dict[str, object]:
        """
        Save or update user settings.

        Args:
            selected_models: Legacy hidden list of AI model names
            code_analysis_prompt: Code analysis prompt template
            code_rewrite_prompt: Code rewrite prompt template
            full_strategy_analysis_prompt: Full analysis prompt template
            user_id: User identifier (None for anonymous)
            db: Optional database session

        Returns:
            Saved settings as dict
        """
        with self.managed_session(db) as session:
            try:
                normalized_user_id = self._normalize_user_id(user_id)
                models_str = ",".join(selected_models) if selected_models else DEFAULT_SETTINGS["selected_models"]

                existing = session.query(UserSettingsModel).filter(
                    UserSettingsModel.user_id == normalized_user_id
                ).first()

                if existing:
                    existing.selected_models = models_str
                    existing.code_analysis_prompt = code_analysis_prompt
                    existing.code_rewrite_prompt = code_rewrite_prompt
                    existing.full_strategy_analysis_prompt = full_strategy_analysis_prompt
                    existing.updated_at = datetime.utcnow()
                    logger.debug(f"Updated settings for user {normalized_user_id}")
                else:
                    new_settings = UserSettingsModel(
                        user_id=normalized_user_id,
                        selected_models=models_str,
                        code_analysis_prompt=code_analysis_prompt,
                        code_rewrite_prompt=code_rewrite_prompt,
                        full_strategy_analysis_prompt=full_strategy_analysis_prompt,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    session.add(new_settings)
                    logger.debug(f"Created settings for user {normalized_user_id}")

                session.flush()

                settings = session.query(UserSettingsModel).filter(
                    UserSettingsModel.user_id == normalized_user_id
                ).first()

                return self._model_to_dict(settings)

            except IntegrityError as e:
                logger.error(f"Integrity error saving settings for {normalized_user_id}: {e}")
                raise
            except Exception as e:
                logger.error(f"Failed to save settings for {normalized_user_id}: {e}")
                raise

    def reset_settings(
        self,
        user_id: Optional[str] = None,
        db: Optional[Session] = None
    ) -> Dict[str, object]:
        """
        Reset settings to defaults for a user.

        Args:
            user_id: User identifier
            db: Optional database session

        Returns:
            Default settings dict
        """
        with self.managed_session(db) as session:
            try:
                normalized_user_id = self._normalize_user_id(user_id)

                session.query(UserSettingsModel).filter(
                    UserSettingsModel.user_id == normalized_user_id
                ).delete()

                logger.info(f"Reset settings for user {normalized_user_id}")

                return self._get_default_dict()

            except Exception as e:
                logger.error(f"Failed to reset settings for {normalized_user_id}: {e}")
                raise

    def _normalize_user_id(self, user_id: Optional[str]) -> Optional[str]:
        """
        Normalize user ID for database storage.

        Anonymous users: None or "anonymous" -> None (NULL in DB)
        Authenticated users: Use their actual user_id
        """
        if user_id == "anonymous" or user_id is None or user_id == "":
            return None
        return user_id

    def _model_to_dict(self, model: UserSettingsModel) -> Dict[str, object]:
        """Convert database model to dict."""
        return {
            "selected_models": model.selected_models.split(",") if model.selected_models else [],
            "code_analysis_prompt": model.code_analysis_prompt,
            "code_rewrite_prompt": model.code_rewrite_prompt,
            "full_strategy_analysis_prompt": model.full_strategy_analysis_prompt,
            "created_at": model.created_at.isoformat() if model.created_at else None,
            "updated_at": model.updated_at.isoformat() if model.updated_at else None
        }

    def _get_default_dict(self) -> Dict[str, object]:
        """Get default settings as dict."""
        return {
            "selected_models": DEFAULT_SETTINGS["selected_models"].split(","),
            "code_analysis_prompt": DEFAULT_SETTINGS["code_analysis_prompt"],
            "code_rewrite_prompt": DEFAULT_SETTINGS["code_rewrite_prompt"],
            "full_strategy_analysis_prompt": DEFAULT_SETTINGS["full_strategy_analysis_prompt"]
        }

    def _is_encrypted_field(self, field_name: str) -> bool:
        """Check if a field should be encrypted."""
        encrypted_fields = {
            "openai_api_key",
            "eodhd_api_key",
        }
        return field_name in encrypted_fields

    def _get_or_create_settings(
        self,
        normalized_user_id: Optional[str],
        db: Session
    ) -> UserSettingsModel:
        """Get existing settings or create new with defaults.
        
        Note: Expects already-normalized user_id (call _normalize_user_id first).
        """
        settings = db.query(UserSettingsModel).filter(
            UserSettingsModel.user_id == normalized_user_id
        ).first()

        if not settings:
            settings = UserSettingsModel(
                user_id=normalized_user_id,
                selected_models=DEFAULT_SETTINGS["selected_models"],
                code_analysis_prompt=DEFAULT_SETTINGS["code_analysis_prompt"],
                code_rewrite_prompt=DEFAULT_SETTINGS["code_rewrite_prompt"],
                full_strategy_analysis_prompt=DEFAULT_SETTINGS["full_strategy_analysis_prompt"],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(settings)

        return settings
