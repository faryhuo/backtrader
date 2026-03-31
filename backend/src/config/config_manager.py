"""
Configuration Manager - Centralized credential and configuration management.

Provides unified access to credentials with automatic fallback from:
1. Database (user-specific encrypted credentials)
2. Environment variables (.env file)
3. Default values (hardcoded fallbacks)

This allows users to configure credentials via UI while maintaining
backward compatibility with .env-based configuration.

Example usage:
    from src.config.config_manager import ConfigManager

    config_manager = ConfigManager(user_id="auth0|123456")
    ai_config = config_manager.get_ai_model_config()

    # Get CCXT credentials
    ccxt_creds = config_manager.get_ccxt_credentials("binance", "paper")
"""

import os
import logging
from typing import Dict, Optional, Any, Tuple

from src.db import SettingsStorage

logger = logging.getLogger(__name__)


class ConfigManager:
    """
    Centralized configuration manager with database-first fallback.

    Provides access to credentials and configuration with the following priority:
    1. Database (user_settings table) - encrypted, per-user
    2. Environment variables (.env file) - global fallback
    3. Default values - hardcoded fallbacks

    Thread-safe and can be used across multiple requests.
    """

    def __init__(self, user_id: Optional[str] = None, database_url: Optional[str] = None):
        """
        Initialize configuration manager.

        Args:
            user_id: User identifier for database lookup (None for anonymous/system)
            database_url: Optional database URL (defaults to DATABASE_URL env var)
        """
        self.user_id = user_id

        # Initialize settings storage
        if database_url:
            self.settings_storage = SettingsStorage(database_url)
        else:
            # Use default database URL from settings (already has fallback to DEFAULT_DB_URL)
            from src.config.settings import DATABASE_URL
            self.settings_storage = SettingsStorage(DATABASE_URL)

        logger.debug(f"ConfigManager initialized for user_id={user_id}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value with database-first fallback.

        Args:
            key: Configuration key (e.g., "OPENAI_API_KEY")
            default: Default value if not found anywhere

        Returns:
            Configuration value from database, env, or default
        """
        value, source = self.settings_storage.get_credential_with_fallback(
            key.lower(), self.user_id
        )
        if value is not None:
            logger.debug(f"Config '{key}' loaded from {source}")
            return value

        logger.debug(f"Config '{key}' not found, using default")
        return default

    def get_with_source(self, key: str, default: Any = None) -> Tuple[Any, str]:
        """
        Get configuration value with source indication.

        Args:
            key: Configuration key
            default: Default value if not found

        Returns:
            Tuple of (value, source) where source is 'database', 'env', 'default', or 'none'
        """
        value, source = self.settings_storage.get_credential_with_fallback(
            key.lower(), self.user_id
        )
        if value is not None:
            return value, source

        if default is not None:
            return default, 'default'

        return None, 'none'

    # ========== AI Model Configuration ==========

    def get_ai_model_config(self, provider: Optional[str] = None) -> Dict[str, str]:
        """
        Get AI model provider configuration.

        Returns:
            Dict with provider, api_key, base_url, and default_model keys
        """
        if hasattr(self.settings_storage, "get_ai_provider"):
            resolved_provider, _ = self.settings_storage.get_ai_provider(self.user_id)
        else:
            resolved_provider = os.getenv("AI_PROVIDER", "openai")
        provider_name = (provider or resolved_provider or "openai").lower()
        if hasattr(self.settings_storage, "get_ai_provider_config"):
            config, source = self.settings_storage.get_ai_provider_config(
                provider_name,
                user_id=self.user_id,
                mask_sensitive=False,
            )
        else:
            default_base_urls = {
                "openai": "https://api.openai.com/v1",
                "gemini": "https://generativelanguage.googleapis.com/v1beta",
                "claude": "https://api.anthropic.com/v1",
                "minimax": "https://api.minimaxi.com/anthropic",
            }
            default_models = {
                "openai": "gpt-5.1",
                "minimax": "MiniMax-M2.7",
                "gemini": "gemini-2.0-flash",
                "claude": "claude-3-5-haiku-latest",
            }
            config = {
                "api_key": self.get(f"{provider_name.upper()}_API_KEY"),
                "base_url": self.get(f"{provider_name.upper()}_BASE_URL", default_base_urls.get(provider_name)),
                "default_model": self.get(f"{provider_name.upper()}_MODEL", default_models.get(provider_name)),
            }
            source = "fallback"

        if not config.get("api_key"):
            logger.warning(f"AI provider '{provider_name}' API key not configured")

        return {
            "provider": provider_name,
            "api_key": config.get("api_key"),
            "base_url": config.get("base_url"),
            "default_model": config.get("default_model"),
            "source": source,
        }

    def get_ai_provider_priority(self) -> list[str]:
        """Get AI provider priority list."""
        if hasattr(self.settings_storage, "get_ai_provider_priority"):
            priority, _ = self.settings_storage.get_ai_provider_priority(self.user_id)
            return priority

        env_priority = os.getenv("AI_PROVIDER_PRIORITY")
        if env_priority:
            return [item.strip().lower() for item in env_priority.split(",") if item.strip()]

        return [os.getenv("AI_PROVIDER", "openai").lower()]

    def get_openai_config(self) -> Dict[str, str]:
        """Backward-compatible alias for the OpenAI provider config."""
        config = self.get_ai_model_config("openai")
        return {
            "api_key": config.get("api_key"),
            "base_url": config.get("base_url"),
        }

    # ========== Logto Authentication Configuration ==========

    def get_auth_config(self) -> Dict[str, Any]:
        """Get the active authentication configuration."""
        enable_login = self._get_enable_login()
        auth_provider = str(self.get("AUTH_PROVIDER", "") or "").strip().lower()
        if not auth_provider:
            auth_provider = "logto" if enable_login else "none"

        allow_registration = self.get("SYSTEM_AUTH_ALLOW_REGISTRATION")
        if isinstance(allow_registration, str):
            allow_registration = allow_registration.lower() in {"true", "1", "yes", "on"}

        logto_config = {
            "issuer": self.get("LOGTO_ISSUER"),
            "jwks_uri": self.get("LOGTO_JWKS_URI"),
            "audience": self.get("LOGTO_AUDIENCE"),
            "required_scopes": self.get("LOGTO_REQUIRED_SCOPES", ""),
        }
        return {
            "enable_login": enable_login,
            "auth_provider": auth_provider if enable_login else "none",
            "system_auth_allow_registration": allow_registration,
            "logto": logto_config,
        }

    def get_logto_config(self) -> Dict[str, Any]:
        """Backward-compatible Logto config accessor."""
        config = self.get_auth_config()
        return {
            **config["logto"],
            "enable_login": config["enable_login"],
            "auth_provider": config["auth_provider"],
            "system_auth_allow_registration": config["system_auth_allow_registration"],
        }

    def _get_enable_login(self) -> bool:
        """
        Get enable_login flag with proper boolean conversion.

        Returns:
            True if login is enabled, False otherwise
        """
        value, source = self.get_with_source("ENABLE_LOGIN", "true")

        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            return value.lower() in {"true", "1", "yes", "on"}

        return True  # Default to enabled

    # ========== Proxy Configuration ==========

    def get_proxy_config(self) -> Dict[str, Optional[str]]:
        """
        Get HTTP/HTTPS proxy configuration.

        Returns:
            Dict with 'http_proxy' and 'https_proxy' keys
        """
        return {
            "http_proxy": self.get("HTTP_PROXY"),
            "https_proxy": self.get("HTTPS_PROXY")
        }

    # ========== CCXT Exchange Credentials ==========

    def get_ccxt_credentials(self, exchange: str, mode: str) -> Dict[str, Optional[str]]:
        """
        Get CCXT credentials for a specific exchange and mode.

        Priority:
        1. Database (user_settings.ccxt_credentials JSON)
        2. Environment variables (CCXT_{EXCHANGE}_{MODE}_API_KEY, etc.)

        Args:
            exchange: Exchange ID (e.g., "binance", "okx", "bybit")
            mode: Trading mode ("paper" for testnet, "live" for production)

        Returns:
            Dict with 'api_key', 'secret', and optional 'passphrase' keys

        Example:
            >>> creds = manager.get_ccxt_credentials("binance", "paper")
            >>> exchange = ccxt.binance({
            ...     'apiKey': creds['api_key'],
            ...     'secret': creds['secret']
            ... })
        """
        # Try database first
        db_creds = self.settings_storage.get_ccxt_credentials(
            exchange, mode, self.user_id
        )
        if db_creds:
            logger.debug(f"Loaded CCXT credentials for {exchange}/{mode} from database")
            return db_creds

        # Fall back to environment variables
        exchange_upper = exchange.upper()
        mode_upper = mode.upper()

        api_key = os.getenv(f"CCXT_{exchange_upper}_{mode_upper}_API_KEY")
        secret = os.getenv(f"CCXT_{exchange_upper}_{mode_upper}_SECRET")
        passphrase = os.getenv(f"CCXT_{exchange_upper}_{mode_upper}_PASSPHRASE")

        if api_key or secret:
            logger.debug(f"Loaded CCXT credentials for {exchange}/{mode} from environment")
            return {
                "api_key": api_key,
                "secret": secret,
                "passphrase": passphrase
            }

        logger.debug(f"No CCXT credentials found for {exchange}/{mode}")
        return {
            "api_key": None,
            "secret": None,
            "passphrase": None
        }

    def has_ccxt_credentials(self, exchange: str, mode: str) -> bool:
        """
        Check if CCXT credentials are configured for an exchange/mode.

        Args:
            exchange: Exchange ID
            mode: Trading mode

        Returns:
            True if api_key and secret are configured, False otherwise
        """
        creds = self.get_ccxt_credentials(exchange, mode)
        return bool(creds.get("api_key") and creds.get("secret"))

    # ========== Live Trading Configuration ==========

    def get_live_trading_config(self) -> Dict[str, Any]:
        """
        Get live trading global configuration.

        Returns:
            Dict with live trading feature flags and defaults
        """
        live_enabled_str = os.getenv("LIVE_TRADING_ENABLED", "false")
        live_enabled = live_enabled_str.lower() in {"true", "1", "yes", "on"}

        return {
            "enabled": live_enabled,
            "default_exchange": os.getenv("DEFAULT_EXCHANGE", "binance"),
            "default_mode": os.getenv("DEFAULT_TRADE_MODE", "paper")
        }

    # ========== Database Configuration ==========

    def get_database_url(self) -> str:
        """
        Get database URL.

        Returns:
            Database connection string (from DATABASE_URL setting with absolute path fallback)
        """
        from src.config.settings import DATABASE_URL
        return DATABASE_URL

    # ========== Utility Methods ==========

    def reload(self):
        """
        Reload configuration from database.

        Useful if credentials were updated in another process.
        """
        # Settings storage queries fresh data on each call, so no action needed
        logger.info(f"Configuration reloaded for user {self.user_id}")

    def get_all_config_sources(self) -> Dict[str, str]:
        """
        Get source information for all configured values.

        Useful for debugging and displaying to users where values come from.

        Returns:
            Dict mapping config keys to their sources ('database', 'env', 'none')
        """
        sources = {}

        if hasattr(self.settings_storage, "get_all_ai_provider_configs"):
            ai_configs = self.settings_storage.get_all_ai_provider_configs(
                user_id=self.user_id,
                mask_sensitive=True,
            )
            sources["ai_provider"] = ai_configs["active_provider_source"]
            for provider, provider_source in ai_configs["provider_sources"].items():
                sources[f"ai_provider_{provider}"] = provider_source
            sources["openai_api_key"] = ai_configs["provider_sources"]["openai"]
            sources["openai_base_url"] = ai_configs["provider_sources"]["openai"]
        else:
            _, sources["openai_api_key"] = self.get_with_source("OPENAI_API_KEY")
            _, sources["openai_base_url"] = self.get_with_source("OPENAI_BASE_URL")

        # Logto
        _, sources["auth_provider"] = self.get_with_source("AUTH_PROVIDER")
        _, sources["system_auth_allow_registration"] = self.get_with_source("SYSTEM_AUTH_ALLOW_REGISTRATION")
        _, sources["logto_issuer"] = self.get_with_source("LOGTO_ISSUER")
        _, sources["logto_jwks_uri"] = self.get_with_source("LOGTO_JWKS_URI")
        _, sources["logto_audience"] = self.get_with_source("LOGTO_AUDIENCE")
        _, sources["logto_required_scopes"] = self.get_with_source("LOGTO_REQUIRED_SCOPES")
        _, sources["enable_login"] = self.get_with_source("ENABLE_LOGIN")

        # Proxies
        _, sources["http_proxy"] = self.get_with_source("HTTP_PROXY")
        _, sources["https_proxy"] = self.get_with_source("HTTPS_PROXY")

        return sources


# Singleton instance for global (non-user-specific) configuration
_global_config_manager: Optional[ConfigManager] = None


def get_global_config_manager() -> ConfigManager:
    """
    Get singleton config manager for global (system-wide) configuration.

    Use this for configuration that doesn't vary by user (e.g., Logto config).

    Returns:
        ConfigManager instance with user_id=None
    """
    global _global_config_manager
    if _global_config_manager is None:
        _global_config_manager = ConfigManager(user_id=None)
    return _global_config_manager


def get_user_config_manager(user_id: str) -> ConfigManager:
    """
    Get config manager for a specific user.

    Use this for user-specific configuration (e.g., OpenAI API keys).

    Args:
        user_id: User identifier from authentication

    Returns:
        ConfigManager instance for the user
    """
    return ConfigManager(user_id=user_id)
