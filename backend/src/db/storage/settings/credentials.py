"""
Credentials Mixin - Credential management methods for SettingsStorage.

Handles encryption, decryption, and storage of API keys and secrets.
"""

import logging
import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from src.db.models import UserSettingsModel
from src.utils.encryption import encrypt_value, decrypt_value, mask_credential

from .base import DEFAULT_SETTINGS

logger = logging.getLogger(__name__)


class CredentialsMixin:
    """Mixin providing credential management methods."""

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

            value = getattr(settings, credential_key, None)

            if value is None:
                return None

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
            settings = self._get_or_create_settings(normalized_user_id, db)

            if value is not None and self._is_encrypted_field(credential_key):
                value = encrypt_value(str(value))

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
                logger.debug(f"No settings found for user {normalized_user_id}, nothing to delete")

            return True

        except Exception as e:
            logger.error(f"Failed to delete credential {credential_key} for user {normalized_user_id}: {e}")
            db.rollback()
            return False
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
            Tuple of (value, source) where source is 'database', 'env', or 'none'
        """
        db_value = self.get_credential(credential_key, user_id, db)
        if db_value is not None:
            return db_value, 'database'

        env_key = credential_key.upper()
        env_value = os.getenv(env_key)
        if env_value:
            if credential_key == "enable_login":
                env_value = env_value.lower() in {"true", "1", "yes", "on"}
            return env_value, 'env'

        return None, 'none'

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

    # ========== CCXT CREDENTIALS ==========

    def get_ccxt_credentials(
        self,
        exchange: str,
        mode: str,
        user_id: Optional[str] = None,
        db: Optional[Session] = None
    ) -> Optional[Dict[str, str]]:
        """Get CCXT credentials for a specific exchange and mode."""
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

            creds = settings.ccxt_credentials
            if isinstance(creds, str):
                creds = json.loads(creds)

            if exchange not in creds or mode not in creds[exchange]:
                return None

            encrypted_creds = creds[exchange][mode]

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
        """Save CCXT credentials for a specific exchange and mode."""
        close_db = False
        if db is None:
            db = self.get_db_session()
            close_db = True

        try:
            normalized_user_id = self._normalize_user_id(user_id)
            settings = self._get_or_create_settings(normalized_user_id, db)

            creds = settings.ccxt_credentials or {}
            if isinstance(creds, str):
                creds = json.loads(creds)

            if exchange not in creds:
                creds[exchange] = {}
            if mode not in creds[exchange]:
                creds[exchange][mode] = {}

            for key in ["api_key", "secret", "passphrase"]:
                if key in credentials and credentials[key]:
                    creds[exchange][mode][key] = encrypt_value(credentials[key])
                elif key in credentials and credentials[key] is None:
                    creds[exchange][mode].pop(key, None)

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
        """Get all CCXT credentials for all exchanges (with fallback to env)."""
        exchanges = ["binance", "okx", "bybit"]
        modes = ["paper", "live"]
        result = {}
        sources = set()

        for exchange in exchanges:
            result[exchange] = {}
            for mode in modes:
                db_creds = self.get_ccxt_credentials(exchange, mode, user_id, db)
                if db_creds:
                    if mask_sensitive:
                        db_creds = {k: mask_credential(v) for k, v in db_creds.items()}
                    result[exchange][mode] = db_creds
                    result[exchange][mode]["source"] = "database"
                    sources.add("database")
                else:
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
