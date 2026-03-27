"""
Credentials Mixin - Credential management methods for SettingsStorage.

Handles encryption, decryption, and storage of API keys and secrets.
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from src.db.models import UserSettingsModel
from src.utils.encryption import encrypt_value, decrypt_value, mask_credential

from .base import DEFAULT_SETTINGS

logger = logging.getLogger(__name__)

AI_PROVIDER_ENV_MAPPING = {
    "openai": {
        "api_key": ["OPENAI_API_KEY"],
        "base_url": ["OPENAI_BASE_URL"],
        "default_model_env": ["OPENAI_MODEL"],
        "default_base_url": "https://api.openai.com/v1",
        "default_model": "gpt-5.1",
    },
    "minimax": {
        "api_key": ["MINIMAX_API_KEY"],
        "base_url": ["MINIMAX_BASE_URL"],
        "default_model_env": ["MINIMAX_MODEL"],
        "default_base_url": "https://api.minimaxi.com/anthropic",
        "default_model": "MiniMax-M2.7",
    },
    "gemini": {
        "api_key": ["GEMINI_API_KEY"],
        "base_url": ["GEMINI_BASE_URL"],
        "default_model_env": ["GEMINI_MODEL"],
        "default_base_url": "https://generativelanguage.googleapis.com/v1beta",
        "default_model": "gemini-2.0-flash",
    },
    "claude": {
        "api_key": ["CLAUDE_API_KEY", "ANTHROPIC_API_KEY"],
        "base_url": ["CLAUDE_BASE_URL", "ANTHROPIC_BASE_URL"],
        "default_model_env": ["CLAUDE_MODEL"],
        "default_base_url": "https://api.anthropic.com/v1",
        "default_model": "claude-3-5-haiku-latest",
    },
}
DEFAULT_AI_PROVIDER_PRIORITY = ["openai", "minimax", "gemini", "claude"]


class CredentialsMixin:
    """Mixin providing credential management methods."""

    def get_ai_provider_priority(
        self,
        user_id: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> Tuple[list[str], str]:
        """Return enabled AI providers ordered by priority."""
        with self.managed_session(db, commit_on_success=False) as session:
            normalized_user_id = self._normalize_user_id(user_id)
            settings = session.query(UserSettingsModel).filter(
                UserSettingsModel.user_id == normalized_user_id
            ).first()

            if settings and settings.ai_provider_priority:
                priority = settings.ai_provider_priority
                if isinstance(priority, str):
                    try:
                        priority = json.loads(priority)
                    except json.JSONDecodeError:
                        priority = [item.strip() for item in priority.split(",") if item.strip()]
                if isinstance(priority, list) and priority:
                    return [str(item).lower() for item in priority], "database"

            if settings and settings.ai_provider:
                return [settings.ai_provider.lower()], "database_legacy"

            env_priority = os.getenv("AI_PROVIDER_PRIORITY")
            if env_priority:
                parsed = [item.strip().lower() for item in env_priority.split(",") if item.strip()]
                if parsed:
                    return parsed, "env"

            env_provider = os.getenv("AI_PROVIDER")
            if env_provider:
                return [env_provider.lower()], "env_legacy"

            return DEFAULT_AI_PROVIDER_PRIORITY.copy(), "default"

    def save_ai_provider_priority(
        self,
        priority: list[str],
        user_id: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> bool:
        """Persist ordered AI provider priority list."""
        with self.managed_session(db) as session:
            try:
                normalized_user_id = self._normalize_user_id(user_id)
                settings = self._get_or_create_settings(normalized_user_id, session)
                normalized_priority = [provider.lower() for provider in priority if provider]
                settings.ai_provider_priority = normalized_priority
                settings.ai_provider = normalized_priority[0] if normalized_priority else None
                flag_modified(settings, "ai_provider_priority")
                settings.updated_at = datetime.utcnow()
                return True
            except Exception as exc:
                logger.error(f"Failed to save AI provider priority for user {user_id}: {exc}")
                return False

    def _get_ai_provider_configs_db(
        self,
        settings: UserSettingsModel | None,
        mask_sensitive: bool = False,
    ) -> Dict[str, Dict[str, Any]]:
        """Load AI provider configs from DB and decrypt nested secrets."""
        configs: Dict[str, Dict[str, Any]] = {}
        raw_configs = settings.ai_provider_configs if settings else None

        if isinstance(raw_configs, str):
            try:
                raw_configs = json.loads(raw_configs)
            except json.JSONDecodeError:
                raw_configs = None

        if isinstance(raw_configs, dict):
            for provider, provider_config in raw_configs.items():
                if not isinstance(provider_config, dict):
                    continue
                configs[provider] = {
                    "api_key": None,
                    "base_url": provider_config.get("base_url"),
                    "default_model": provider_config.get("default_model"),
                }
                api_key = provider_config.get("api_key")
                if api_key:
                    decrypted_key = decrypt_value(api_key)
                    configs[provider]["api_key"] = (
                        mask_credential(decrypted_key)
                        if mask_sensitive and decrypted_key
                        else decrypted_key
                    )

        if settings and (settings.openai_api_key or settings.openai_base_url):
            openai_config = configs.setdefault(
                "openai",
                {"api_key": None, "base_url": None, "default_model": None},
            )
            if settings.openai_api_key and not openai_config.get("api_key"):
                decrypted_key = decrypt_value(settings.openai_api_key)
                openai_config["api_key"] = (
                    mask_credential(decrypted_key)
                    if mask_sensitive and decrypted_key
                    else decrypted_key
                )
            if settings.openai_base_url and not openai_config.get("base_url"):
                openai_config["base_url"] = settings.openai_base_url

        return configs

    def _get_ai_provider_env_config(self, provider: str, mask_sensitive: bool = False) -> Dict[str, Any]:
        """Load provider config from environment variables."""
        mapping = AI_PROVIDER_ENV_MAPPING.get(provider, {})
        api_key = None
        for env_key in mapping.get("api_key", []):
            env_value = os.getenv(env_key)
            if env_value:
                api_key = env_value
                break

        base_url = None
        for env_key in mapping.get("base_url", []):
            env_value = os.getenv(env_key)
            if env_value:
                base_url = env_value
                break

        if base_url is None:
            base_url = mapping.get("default_base_url")

        default_model = None
        for env_key in mapping.get("default_model_env", []):
            env_value = os.getenv(env_key)
            if env_value:
                default_model = env_value
                break

        if default_model is None:
            default_model = mapping.get("default_model")

        return {
            "api_key": mask_credential(api_key) if mask_sensitive and api_key else api_key,
            "base_url": base_url,
            "default_model": default_model,
        }

    def get_ai_provider(self, user_id: Optional[str] = None, db: Optional[Session] = None) -> Tuple[str, str]:
        """Return active AI provider and its source."""
        priority, source = self.get_ai_provider_priority(user_id=user_id, db=db)
        return (priority[0] if priority else "openai"), source

    def save_ai_provider(self, provider: str, user_id: Optional[str] = None, db: Optional[Session] = None) -> bool:
        """Persist active AI provider selection."""
        with self.managed_session(db) as session:
            try:
                normalized_user_id = self._normalize_user_id(user_id)
                settings = self._get_or_create_settings(normalized_user_id, session)
                settings.ai_provider = provider
                settings.updated_at = datetime.utcnow()
                return True
            except Exception as exc:
                logger.error(f"Failed to save AI provider for user {user_id}: {exc}")
                return False

    def get_ai_provider_config(
        self,
        provider: str,
        user_id: Optional[str] = None,
        mask_sensitive: bool = True,
        db: Optional[Session] = None,
    ) -> Tuple[Dict[str, Any], str]:
        """Get a single AI provider config with DB and env fallback."""
        with self.managed_session(db, commit_on_success=False) as session:
            normalized_user_id = self._normalize_user_id(user_id)
            settings = session.query(UserSettingsModel).filter(
                UserSettingsModel.user_id == normalized_user_id
            ).first()
            configs = self._get_ai_provider_configs_db(settings, mask_sensitive=mask_sensitive)
            config = configs.get(provider)
            if config and any(config.get(field) for field in ("api_key", "base_url", "default_model")):
                return config, "database"

            env_config = self._get_ai_provider_env_config(provider, mask_sensitive=mask_sensitive)
            if env_config.get("api_key") or env_config.get("base_url"):
                return env_config, "env"

            return {
                "api_key": None,
                "base_url": AI_PROVIDER_ENV_MAPPING.get(provider, {}).get("default_base_url"),
                "default_model": AI_PROVIDER_ENV_MAPPING.get(provider, {}).get("default_model"),
            }, "none"

    def save_ai_provider_config(
        self,
        provider: str,
        config: Dict[str, Any],
        user_id: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> bool:
        """Save one provider config inside the unified AI provider JSON blob."""
        with self.managed_session(db) as session:
            try:
                normalized_user_id = self._normalize_user_id(user_id)
                settings = self._get_or_create_settings(normalized_user_id, session)
                current_configs = settings.ai_provider_configs or {}
                if isinstance(current_configs, str):
                    try:
                        current_configs = json.loads(current_configs)
                    except json.JSONDecodeError:
                        current_configs = {}
                provider_config = dict(current_configs.get(provider, {}))

                for key in ("base_url", "default_model"):
                    if key in config:
                        provider_config[key] = config.get(key) or None

                if "api_key" in config:
                    api_key = config.get("api_key")
                    provider_config["api_key"] = encrypt_value(str(api_key)) if api_key else None

                current_configs[provider] = provider_config
                settings.ai_provider_configs = current_configs
                flag_modified(settings, "ai_provider_configs")
                settings.updated_at = datetime.utcnow()

                if provider == "openai":
                    if "api_key" in config:
                        settings.openai_api_key = provider_config.get("api_key")
                    if "base_url" in config:
                        settings.openai_base_url = provider_config.get("base_url")

                return True
            except Exception as exc:
                logger.error(f"Failed to save AI provider config for {provider}: {exc}")
                return False

    def get_all_ai_provider_configs(
        self,
        user_id: Optional[str] = None,
        mask_sensitive: bool = True,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """Get active provider and all provider configs with source info."""
        active_provider, active_source = self.get_ai_provider(user_id=user_id, db=db)
        provider_priority, provider_priority_source = self.get_ai_provider_priority(user_id=user_id, db=db)
        providers: Dict[str, Dict[str, Any]] = {}
        provider_sources: Dict[str, str] = {}

        for provider in AI_PROVIDER_ENV_MAPPING:
            config, source = self.get_ai_provider_config(
                provider,
                user_id=user_id,
                mask_sensitive=mask_sensitive,
                db=db,
            )
            providers[provider] = config
            provider_sources[provider] = source

        return {
            "active_provider": active_provider,
            "active_provider_source": active_source,
            "provider_priority": provider_priority,
            "provider_priority_source": provider_priority_source,
            "providers": providers,
            "provider_sources": provider_sources,
        }

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
        with self.managed_session(db, commit_on_success=False) as session:
            try:
                normalized_user_id = self._normalize_user_id(user_id)

                settings = session.query(UserSettingsModel).filter(
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
        with self.managed_session(db) as session:
            try:
                normalized_user_id = self._normalize_user_id(user_id)
                settings = self._get_or_create_settings(normalized_user_id, session)

                if value is not None and self._is_encrypted_field(credential_key):
                    value = encrypt_value(str(value))

                setattr(settings, credential_key, value)
                settings.updated_at = datetime.utcnow()

                logger.debug(f"Saved credential {credential_key} for user {normalized_user_id}")
                return True

            except Exception as e:
                logger.error(f"Failed to save credential {credential_key} for user {normalized_user_id}: {e}")
                return False

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
        with self.managed_session(db) as session:
            try:
                normalized_user_id = self._normalize_user_id(user_id)

                if not hasattr(UserSettingsModel, credential_key):
                    logger.error(f"Invalid credential key: {credential_key}")
                    return False

                settings = session.query(UserSettingsModel).filter(
                    UserSettingsModel.user_id == normalized_user_id
                ).first()

                if settings:
                    setattr(settings, credential_key, None)
                    settings.updated_at = datetime.utcnow()
                    logger.debug(f"Deleted credential {credential_key} for user {normalized_user_id}")
                else:
                    logger.debug(f"No settings found for user {normalized_user_id}, nothing to delete")

                return True

            except Exception as e:
                logger.error(f"Failed to delete credential {credential_key} for user {normalized_user_id}: {e}")
                return False

    def get_credential_with_fallback(
        self,
        credential_key: str,
        user_id: Optional[str] = None,
        db: Optional[Session] = None
    ) -> Tuple[Any, str]:
        """
        Get credential value with fallback chain:
        1. User-specific database value
        2. Global (anonymous) database value
        3. Environment variable
        
        Args:
            credential_key: Credential field name
            user_id: User identifier
            db: Optional database session

        Returns:
            Tuple of (value, source) where source is 'database', 'database_global', 'env', or 'none'
        """
        # 1. Try user-specific value from database
        db_value = self.get_credential(credential_key, user_id, db)
        if db_value is not None:
            return db_value, 'database'

        # 2. If user is not anonymous, try global (anonymous) user value
        normalized_user_id = self._normalize_user_id(user_id)
        if normalized_user_id != "anonymous":
            global_value = self.get_credential(credential_key, None, db)  # None -> anonymous
            if global_value is not None:
                return global_value, 'database_global'

        # 3. Fall back to environment variable
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
        with self.managed_session(db, commit_on_success=False) as session:
            result = {
                "ai_models": {},
                "openai": {},
                "logto": {},
                "proxies": {},
                "exchanges": {}
            }

            ai_models = self.get_all_ai_provider_configs(
                user_id=user_id,
                mask_sensitive=mask_sensitive,
                db=session,
            )
            result["ai_models"] = ai_models
            result["openai"] = {
                "api_key": ai_models["providers"]["openai"]["api_key"],
                "api_key_source": ai_models["provider_sources"]["openai"],
                "base_url": ai_models["providers"]["openai"]["base_url"],
                "base_url_source": ai_models["provider_sources"]["openai"],
            }

            # Logto credentials (both server-side and frontend OAuth)
            logto_fields = [
                "logto_issuer", "logto_jwks_uri", "logto_audience", "logto_required_scopes",
                "logto_endpoint", "logto_app_id", "logto_redirect_uri", "logto_post_logout_redirect_uri"
            ]
            for field in logto_fields:
                value, source = self.get_credential_with_fallback(field, user_id, session)
                key = field.replace("logto_", "")
                result["logto"][key] = value
                result["logto"][f"{key}_source"] = source

            enable_login, enable_login_source = self.get_credential_with_fallback("enable_login", user_id, session)
            result["logto"]["enable_login"] = enable_login
            result["logto"]["enable_login_source"] = enable_login_source

            # Proxy credentials
            http_proxy, http_source = self.get_credential_with_fallback("http_proxy", user_id, session)
            https_proxy, https_source = self.get_credential_with_fallback("https_proxy", user_id, session)

            result["proxies"]["http_proxy"] = http_proxy
            result["proxies"]["http_proxy_source"] = http_source
            result["proxies"]["https_proxy"] = https_proxy
            result["proxies"]["https_proxy_source"] = https_source

            # CCXT credentials
            ccxt_creds, ccxt_source = self.get_ccxt_credentials_all(user_id, mask_sensitive, session)
            result["exchanges"] = ccxt_creds
            result["exchanges_source"] = ccxt_source

            return result

    # ========== CCXT CREDENTIALS ==========

    def get_ccxt_credentials(
        self,
        exchange: str,
        mode: str,
        user_id: Optional[str] = None,
        db: Optional[Session] = None
    ) -> Optional[Dict[str, str]]:
        """Get CCXT credentials for a specific exchange and mode."""
        with self.managed_session(db, commit_on_success=False) as session:
            try:
                normalized_user_id = self._normalize_user_id(user_id)

                settings = session.query(UserSettingsModel).filter(
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

    def save_ccxt_credentials(
        self,
        exchange: str,
        mode: str,
        credentials: Dict[str, str],
        user_id: Optional[str] = None,
        db: Optional[Session] = None
    ) -> bool:
        """Save CCXT credentials for a specific exchange and mode."""
        with self.managed_session(db) as session:
            try:
                normalized_user_id = self._normalize_user_id(user_id)
                settings = self._get_or_create_settings(normalized_user_id, session)

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

                logger.debug(f"Saved CCXT credentials for {exchange}/{mode} (user {normalized_user_id})")
                return True

            except Exception as e:
                logger.error(f"Failed to save CCXT credentials for {exchange}/{mode}: {e}")
                return False

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
