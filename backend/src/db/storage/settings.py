"""
Settings Storage - Persistence layer for user settings.

Provides database operations for saving and retrieving user AI
configuration, prompt templates, and encrypted credentials.
"""

import logging
import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.attributes import flag_modified

from src.config.settings import DATABASE_URL
from src.db.storage.base import BaseStorage
from src.db.models import UserSettingsModel, init_database
from src.utils.encryption import encrypt_value, decrypt_value, mask_credential, is_encryption_enabled

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


class SettingsStorage(BaseStorage):
    """
    Storage layer for user settings.

    Manages CRUD operations for user AI configuration and prompt templates.
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
        db: Optional[Session] = None
    ) -> Dict[str, any]:
        """
        Get user settings from database.

        Args:
            user_id: User identifier (None or "anonymous" for anonymous users)
            db: Optional database session

        Returns:
            Dict with settings fields, or defaults if not found
        """
        close_db = False
        if db is None:
            db = self.get_db_session()
            close_db = True

        try:
            # Normalize anonymous user ID
            normalized_user_id = self._normalize_user_id(user_id)

            # Query settings
            settings = db.query(UserSettingsModel).filter(
                UserSettingsModel.user_id == normalized_user_id
            ).first()

            if settings:
                return self._model_to_dict(settings)
            else:
                # Return defaults if no settings found
                logger.debug(f"No settings found for user {normalized_user_id}, returning defaults")
                return self._get_default_dict()

        finally:
            if close_db:
                db.close()

    def save_settings(
        self,
        selected_models: List[str],
        code_analysis_prompt: str,
        code_rewrite_prompt: str,
        full_strategy_analysis_prompt: str,
        user_id: Optional[str] = None,
        db: Optional[Session] = None
    ) -> Dict[str, any]:
        """
        Save or update user settings.

        Args:
            selected_models: List of AI model names
            code_analysis_prompt: Code analysis prompt template
            code_rewrite_prompt: Code rewrite prompt template
            full_strategy_analysis_prompt: Full analysis prompt template
            user_id: User identifier (None for anonymous)
            db: Optional database session

        Returns:
            Saved settings as dict
        """
        close_db = False
        if db is None:
            db = self.get_db_session()
            close_db = True

        try:
            # Normalize user ID
            normalized_user_id = self._normalize_user_id(user_id)

            # Convert model list to comma-separated string
            models_str = ",".join(selected_models) if selected_models else DEFAULT_SETTINGS["selected_models"]

            # Check if settings exist
            existing = db.query(UserSettingsModel).filter(
                UserSettingsModel.user_id == normalized_user_id
            ).first()

            if existing:
                # Update existing
                existing.selected_models = models_str
                existing.code_analysis_prompt = code_analysis_prompt
                existing.code_rewrite_prompt = code_rewrite_prompt
                existing.full_strategy_analysis_prompt = full_strategy_analysis_prompt
                existing.updated_at = datetime.utcnow()

                logger.debug(f"Updated settings for user {normalized_user_id}")
            else:
                # Create new
                new_settings = UserSettingsModel(
                    user_id=normalized_user_id,
                    selected_models=models_str,
                    code_analysis_prompt=code_analysis_prompt,
                    code_rewrite_prompt=code_rewrite_prompt,
                    full_strategy_analysis_prompt=full_strategy_analysis_prompt,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(new_settings)
                logger.debug(f"Created settings for user {normalized_user_id}")

            db.commit()

            # Refresh to get updated values
            settings = db.query(UserSettingsModel).filter(
                UserSettingsModel.user_id == normalized_user_id
            ).first()

            return self._model_to_dict(settings)

        except IntegrityError as e:
            logger.error(f"Integrity error saving settings for {normalized_user_id}: {e}")
            db.rollback()
            raise
        except Exception as e:
            logger.error(f"Failed to save settings for {normalized_user_id}: {e}")
            db.rollback()
            raise
        finally:
            if close_db:
                db.close()

    def reset_settings(
        self,
        user_id: Optional[str] = None,
        db: Optional[Session] = None
    ) -> Dict[str, any]:
        """
        Reset settings to defaults for a user.

        Args:
            user_id: User identifier
            db: Optional database session

        Returns:
            Default settings dict
        """
        close_db = False
        if db is None:
            db = self.get_db_session()
            close_db = True

        try:
            normalized_user_id = self._normalize_user_id(user_id)

            # Delete existing settings
            db.query(UserSettingsModel).filter(
                UserSettingsModel.user_id == normalized_user_id
            ).delete()

            db.commit()
            logger.info(f"Reset settings for user {normalized_user_id}")

            return self._get_default_dict()

        except Exception as e:
            logger.error(f"Failed to reset settings for {normalized_user_id}: {e}")
            db.rollback()
            raise
        finally:
            if close_db:
                db.close()

    def _normalize_user_id(self, user_id: Optional[str]) -> Optional[str]:
        """
        Normalize user ID for database storage.

        Anonymous users: None or "anonymous" -> None (NULL in DB)
        Authenticated users: Use their actual user_id
        """
        if user_id == "anonymous" or user_id is None or user_id == "":
            return None
        return user_id

    def _model_to_dict(self, model: UserSettingsModel) -> Dict[str, any]:
        """Convert database model to dict."""
        return {
            "selected_models": model.selected_models.split(",") if model.selected_models else [],
            "code_analysis_prompt": model.code_analysis_prompt,
            "code_rewrite_prompt": model.code_rewrite_prompt,
            "full_strategy_analysis_prompt": model.full_strategy_analysis_prompt,
            "created_at": model.created_at.isoformat() if model.created_at else None,
            "updated_at": model.updated_at.isoformat() if model.updated_at else None
        }

    def _get_default_dict(self) -> Dict[str, any]:
        """Get default settings as dict."""
        return {
            "selected_models": DEFAULT_SETTINGS["selected_models"].split(","),
            "code_analysis_prompt": DEFAULT_SETTINGS["code_analysis_prompt"],
            "code_rewrite_prompt": DEFAULT_SETTINGS["code_rewrite_prompt"],
            "full_strategy_analysis_prompt": DEFAULT_SETTINGS["full_strategy_analysis_prompt"]
        }

    # ========== CREDENTIAL MANAGEMENT METHODS ==========

    def get_credential(
        self,
        credential_key: str,
        user_id: Optional[str] = None,
        db: Optional[Session] = None
    ) -> Optional[str]:
        """
        Get a single credential value from database (decrypted).

        Args:
            credential_key: Credential field name (e.g., "openai_api_key")
            user_id: User identifier (None for anonymous)
            db: Optional database session

        Returns:
            Decrypted credential value, or None if not set
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

            if not settings:
                return None

            # Get the attribute value
            value = getattr(settings, credential_key, None)

            if value is None:
                return None

            # Decrypt if it's a sensitive field
            if self._is_encrypted_field(credential_key):
                return decrypt_value(value)
            else:
                return value

        except Exception as e:
            logger.error(f"Failed to get credential {credential_key} for user {normalized_user_id}: {e}")
            return None
        finally:
            if close_db:
                db.close()

    def save_credential(
        self,
        credential_key: str,
        value: Any,
        user_id: Optional[str] = None,
        db: Optional[Session] = None
    ) -> bool:
        """
        Save a credential value to database (encrypted if sensitive).

        Args:
            credential_key: Credential field name
            value: Value to save (will be encrypted if sensitive)
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

            # Get or create settings record
            settings = db.query(UserSettingsModel).filter(
                UserSettingsModel.user_id == normalized_user_id
            ).first()

            if not settings:
                # Create new record with default values
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

            # Encrypt value if it's a sensitive field
            if value is not None and self._is_encrypted_field(credential_key):
                value = encrypt_value(str(value))

            # Set the attribute
            setattr(settings, credential_key, value)
            settings.updated_at = datetime.utcnow()

            db.commit()
            logger.debug(f"Saved credential {credential_key} for user {normalized_user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to save credential {credential_key} for user {normalized_user_id}: {e}")
            db.rollback()
            return False
        finally:
            if close_db:
                db.close()

    def delete_credential(
        self,
        credential_key: str,
        user_id: Optional[str] = None,
        db: Optional[Session] = None
    ) -> bool:
        """
        Delete a credential value (sets to NULL in database).

        Args:
            credential_key: Credential field name
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

            # Check if the credential_key is a valid attribute of the model
            if not hasattr(UserSettingsModel, credential_key):
                logger.error(f"Invalid credential key: {credential_key}")
                return False

            settings = db.query(UserSettingsModel).filter(
                UserSettingsModel.user_id == normalized_user_id
            ).first()

            if settings:
                setattr(settings, credential_key, None)
                settings.updated_at = datetime.utcnow()
                db.commit()
                logger.debug(f"Deleted credential {credential_key} for user {normalized_user_id}")
            else:
                # No settings record exists, which is fine (nothing to delete)
                logger.debug(f"No settings found for user {normalized_user_id}, nothing to delete")

            return True

        except Exception as e:
            logger.error(f"Failed to delete credential {credential_key} for user {normalized_user_id}: {e}")
            import traceback
            traceback.print_exc()
            db.rollback()
            return False
        finally:
            if close_db:
                db.close()

    def get_all_credentials(
        self,
        user_id: Optional[str] = None,
        mask_sensitive: bool = True,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Get all credentials with optional masking and source indication.

        Args:
            user_id: User identifier
            mask_sensitive: Whether to mask sensitive values
            db: Optional database session

        Returns:
            Dict with credential values and their sources
        """
        close_db = False
        if db is None:
            db = self.get_db_session()
            close_db = True

        try:
            result = {
                "openai": {},
                "logto": {},
                "proxies": {},
                "exchanges": {}
            }

            # OpenAI credentials
            api_key, api_key_source = self.get_credential_with_fallback("openai_api_key", user_id, db)
            base_url, base_url_source = self.get_credential_with_fallback("openai_base_url", user_id, db)

            result["openai"]["api_key"] = mask_credential(api_key) if mask_sensitive and api_key else api_key
            result["openai"]["api_key_source"] = api_key_source
            result["openai"]["base_url"] = base_url
            result["openai"]["base_url_source"] = base_url_source

            # Logto credentials
            logto_fields = ["logto_issuer", "logto_jwks_uri", "logto_audience", "logto_required_scopes"]
            for field in logto_fields:
                value, source = self.get_credential_with_fallback(field, user_id, db)
                key = field.replace("logto_", "")
                result["logto"][key] = value
                result["logto"][f"{key}_source"] = source

            enable_login, enable_login_source = self.get_credential_with_fallback("enable_login", user_id, db)
            result["logto"]["enable_login"] = enable_login
            result["logto"]["enable_login_source"] = enable_login_source

            # Proxy credentials
            http_proxy, http_source = self.get_credential_with_fallback("http_proxy", user_id, db)
            https_proxy, https_source = self.get_credential_with_fallback("https_proxy", user_id, db)

            result["proxies"]["http_proxy"] = http_proxy
            result["proxies"]["http_proxy_source"] = http_source
            result["proxies"]["https_proxy"] = https_proxy
            result["proxies"]["https_proxy_source"] = https_source

            # CCXT credentials
            ccxt_creds, ccxt_source = self.get_ccxt_credentials_all(user_id, mask_sensitive, db)
            result["exchanges"] = ccxt_creds
            result["exchanges_source"] = ccxt_source

            return result

        finally:
            if close_db:
                db.close()

    def get_credential_with_fallback(
        self,
        credential_key: str,
        user_id: Optional[str] = None,
        db: Optional[Session] = None
    ) -> Tuple[Any, str]:
        """
        Get credential value with fallback to environment variable.

        Args:
            credential_key: Credential field name
            user_id: User identifier
            db: Optional database session

        Returns:
            Tuple of (value, source) where source is 'database', 'env', or 'default'
        """
        # Try database first
        db_value = self.get_credential(credential_key, user_id, db)
        if db_value is not None:
            return db_value, 'database'

        # Fall back to environment variable
        env_key = credential_key.upper()
        env_value = os.getenv(env_key)
        if env_value:
            # Convert string boolean to actual boolean for enable_login
            if credential_key == "enable_login":
                env_value = env_value.lower() in {"true", "1", "yes", "on"}
            return env_value, 'env'

        # Return None with appropriate source
        return None, 'none'

    def get_ccxt_credentials(
        self,
        exchange: str,
        mode: str,
        user_id: Optional[str] = None,
        db: Optional[Session] = None
    ) -> Optional[Dict[str, str]]:
        """
        Get CCXT credentials for a specific exchange and mode.

        Args:
            exchange: Exchange ID (e.g., "binance", "okx")
            mode: Trading mode ("paper" or "live")
            user_id: User identifier
            db: Optional database session

        Returns:
            Dict with api_key, secret, and optional passphrase (all decrypted)
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

            if not settings or not settings.ccxt_credentials:
                return None

            # Parse JSON credentials
            creds = settings.ccxt_credentials
            if isinstance(creds, str):
                creds = json.loads(creds)

            if exchange not in creds or mode not in creds[exchange]:
                return None

            encrypted_creds = creds[exchange][mode]

            # Decrypt values
            result = {}
            for key in ["api_key", "secret", "passphrase"]:
                if key in encrypted_creds and encrypted_creds[key]:
                    result[key] = decrypt_value(encrypted_creds[key])

            return result if result else None

        except Exception as e:
            logger.error(f"Failed to get CCXT credentials for {exchange}/{mode}: {e}")
            return None
        finally:
            if close_db:
                db.close()

    def save_ccxt_credentials(
        self,
        exchange: str,
        mode: str,
        credentials: Dict[str, str],
        user_id: Optional[str] = None,
        db: Optional[Session] = None
    ) -> bool:
        """
        Save CCXT credentials for a specific exchange and mode.

        Args:
            exchange: Exchange ID
            mode: Trading mode ("paper" or "live")
            credentials: Dict with api_key, secret, optional passphrase
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

            # Get or create settings
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
                    ccxt_credentials={},
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(settings)

            # Get existing CCXT credentials or create new structure
            creds = settings.ccxt_credentials or {}
            if isinstance(creds, str):
                creds = json.loads(creds)

            # Initialize exchange/mode structure
            if exchange not in creds:
                creds[exchange] = {}
            if mode not in creds[exchange]:
                creds[exchange][mode] = {}

            # Encrypt and store credentials
            for key in ["api_key", "secret", "passphrase"]:
                if key in credentials and credentials[key]:
                    creds[exchange][mode][key] = encrypt_value(credentials[key])
                elif key in credentials and credentials[key] is None:
                    # Allow explicit deletion
                    creds[exchange][mode].pop(key, None)

            # JSON fields do not reliably track nested mutations unless using
            # SQLAlchemy mutable types; explicitly flag as modified.
            settings.ccxt_credentials = creds
            flag_modified(settings, "ccxt_credentials")
            settings.updated_at = datetime.utcnow()

            db.commit()
            logger.debug(f"Saved CCXT credentials for {exchange}/{mode} (user {normalized_user_id})")
            return True

        except Exception as e:
            logger.error(f"Failed to save CCXT credentials for {exchange}/{mode}: {e}")
            db.rollback()
            return False
        finally:
            if close_db:
                db.close()

    def get_ccxt_credentials_all(
        self,
        user_id: Optional[str] = None,
        mask_sensitive: bool = True,
        db: Optional[Session] = None
    ) -> Tuple[Dict[str, Any], str]:
        """
        Get all CCXT credentials for all exchanges (with fallback to env).

        Args:
            user_id: User identifier
            mask_sensitive: Whether to mask API keys/secrets
            db: Optional database session

        Returns:
            Tuple of (credentials_dict, source) where source is 'database', 'env', or 'mixed'
        """
        exchanges = ["binance", "okx", "bybit"]
        modes = ["paper", "live"]
        result = {}
        sources = set()

        for exchange in exchanges:
            result[exchange] = {}
            for mode in modes:
                # Try database first
                db_creds = self.get_ccxt_credentials(exchange, mode, user_id, db)
                if db_creds:
                    if mask_sensitive:
                        db_creds = {k: mask_credential(v) for k, v in db_creds.items()}
                    result[exchange][mode] = db_creds
                    result[exchange][mode]["source"] = "database"
                    sources.add("database")
                else:
                    # Fall back to environment variables
                    env_key = f"CCXT_{exchange.upper()}_{mode.upper()}"
                    api_key = os.getenv(f"{env_key}_API_KEY")
                    secret = os.getenv(f"{env_key}_SECRET")
                    passphrase = os.getenv(f"{env_key}_PASSPHRASE")

                    if api_key or secret:
                        env_creds = {}
                        if api_key:
                            env_creds["api_key"] = mask_credential(api_key) if mask_sensitive else api_key
                        if secret:
                            env_creds["secret"] = mask_credential(secret) if mask_sensitive else secret
                        if passphrase:
                            env_creds["passphrase"] = mask_credential(passphrase) if mask_sensitive else passphrase

                        result[exchange][mode] = env_creds
                        result[exchange][mode]["source"] = "env"
                        sources.add("env")
                    else:
                        result[exchange][mode] = {"source": "none"}
                        sources.add("none")

        overall_source = "mixed" if len(sources) > 1 else sources.pop() if sources else "none"
        return result, overall_source

    def _is_encrypted_field(self, field_name: str) -> bool:
        """
        Check if a field should be encrypted.

        Args:
            field_name: Field name to check

        Returns:
            True if field should be encrypted, False otherwise
        """
        encrypted_fields = {
            "openai_api_key",
            "eodhd_api_key",
            # CCXT credentials are encrypted separately in JSON
        }
        return field_name in encrypted_fields

    # ========== SITE CONFIGURATION METHODS ==========

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
        close_db = False
        if db is None:
            db = self.get_db_session()
            close_db = True

        try:
            normalized_user_id = self._normalize_user_id(user_id)
            
            settings = db.query(UserSettingsModel).filter(
                UserSettingsModel.user_id == normalized_user_id
            ).first()

            result = {}
            sources = {}

            for field in self.SITE_CONFIG_FIELDS:
                # Try database first
                db_value = getattr(settings, field, None) if settings else None
                
                if db_value is not None:
                    result[field] = db_value
                    sources[field] = "database"
                else:
                    # Fall back to environment variable
                    env_key = self.SITE_CONFIG_ENV_MAPPING.get(field, field.upper())
                    env_value = os.getenv(env_key)
                    
                    if env_value:
                        result[field] = env_value
                        sources[field] = "env"
                    else:
                        # Use default
                        result[field] = self.SITE_CONFIG_DEFAULTS.get(field, "")
                        sources[field] = "default"

            return {"config": result, "sources": sources}

        finally:
            if close_db:
                db.close()

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
        close_db = False
        if db is None:
            db = self.get_db_session()
            close_db = True

        try:
            normalized_user_id = self._normalize_user_id(user_id)

            # Get or create settings
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

            # Update only valid site config fields
            for field in self.SITE_CONFIG_FIELDS:
                if field in config:
                    setattr(settings, field, config[field])

            settings.updated_at = datetime.utcnow()
            db.commit()
            
            logger.info(f"Saved site config for user {normalized_user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to save site config: {e}")
            db.rollback()
            return False
        finally:
            if close_db:
                db.close()

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
                for field in self.SITE_CONFIG_FIELDS:
                    setattr(settings, field, None)
                settings.updated_at = datetime.utcnow()
                db.commit()
                logger.info(f"Reset site config for user {normalized_user_id}")

            return True

        except Exception as e:
            logger.error(f"Failed to reset site config: {e}")
            db.rollback()
            return False
        finally:
            if close_db:
                db.close()

    # ========== DATA SOURCE CONFIGURATION METHODS ==========

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
                # Get priority from DB or use default
                if settings.data_source_priority:
                    priority = settings.data_source_priority
                    if isinstance(priority, str):
                        priority = json.loads(priority)
                    result["data_source_priority"] = priority

                # Get EODHD API key
                if settings.eodhd_api_key:
                    decrypted = decrypt_value(settings.eodhd_api_key)
                    result["eodhd_api_key"] = mask_credential(decrypted) if decrypted else None
                    result["eodhd_api_key_source"] = "database"

            # Fallback to env for EODHD API key
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
                # Validate sources
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
        # Try database first
        db_value = self.get_credential("eodhd_api_key", user_id, db)
        if db_value:
            return db_value

        # Fallback to environment variable
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

            # Get or create settings
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

            # Update priority if provided
            if data_source_priority is not None:
                # Validate and filter invalid sources
                valid_priority = [s for s in data_source_priority if s in self.VALID_DATA_SOURCES]
                if not valid_priority:
                    valid_priority = self.DEFAULT_DATA_SOURCE_PRIORITY.copy()
                settings.data_source_priority = valid_priority
                flag_modified(settings, "data_source_priority")

            # Update EODHD API key if provided
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

