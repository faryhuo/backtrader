"""First-run setup wizard service."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, ValidationError as PydanticValidationError, model_validator

from src.config.settings import CONFIG_DIR, DEFAULT_DB_PATH, PROJECT_ROOT
from src.utils.encryption import generate_encryption_key, mask_credential

SITE_ENV_MAPPING = {
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

AI_PROVIDER_DEFAULTS = {
    "openai": {
        "api_key_env": "OPENAI_API_KEY",
        "base_url_env": "OPENAI_BASE_URL",
        "base_url": "https://api.openai.com/v1",
        "model_env": "OPENAI_MODEL",
        "default_model": "gpt-5.1",
    },
    "minimax": {
        "api_key_env": "MINIMAX_API_KEY",
        "base_url_env": "MINIMAX_BASE_URL",
        "base_url": "https://api.minimaxi.com/anthropic",
        "model_env": "MINIMAX_MODEL",
        "default_model": "MiniMax-M2.7",
    },
    "gemini": {
        "api_key_env": "GEMINI_API_KEY",
        "base_url_env": "GEMINI_BASE_URL",
        "base_url": "https://generativelanguage.googleapis.com/v1beta",
        "model_env": "GEMINI_MODEL",
        "default_model": "gemini-2.0-flash",
    },
    "claude": {
        "api_key_env": "CLAUDE_API_KEY",
        "base_url_env": "CLAUDE_BASE_URL",
        "base_url": "https://api.anthropic.com/v1",
        "model_env": "CLAUDE_MODEL",
        "default_model": "claude-3-5-haiku-latest",
    },
}
LEGACY_EXCHANGE_ENV_KEYS = (
    "CCXT_OKX_PAPER_API_KEY",
    "CCXT_OKX_PAPER_SECRET",
    "CCXT_OKX_PAPER_PASSPHRASE",
    "CCXT_OKX_LIVE_API_KEY",
    "CCXT_OKX_LIVE_SECRET",
    "CCXT_OKX_LIVE_PASSPHRASE",
    "CCXT_BYBIT_PAPER_API_KEY",
    "CCXT_BYBIT_PAPER_SECRET",
    "CCXT_BYBIT_LIVE_API_KEY",
    "CCXT_BYBIT_LIVE_SECRET",
)

DEFAULT_DATABASE_CONFIG = {
    "version": "1.0",
    "database": {
        "type": "sqlite",
        "sqlite": {
            "path": DEFAULT_DB_PATH.name,
            "wal_mode": True,
            "timeout_seconds": 30,
            "pool_size": 5,
            "max_overflow": 10,
        },
        "postgresql": {
            "host": "localhost",
            "port": 5432,
            "database": "trading",
            "username": "trading_user",
            "password": "",
            "ssl_mode": "prefer",
            "pool_size": 10,
            "max_overflow": 20,
        },
    },
}

DEFAULT_STRATEGY_CONFIG = {
    "strategy": {"filePath": "resources/strategy"},
    "sandbox": {
        "mode": "subprocess",
        "timeoutSeconds": 30.0,
        "maxMemoryMB": 512,
        "maxCpuPercent": 100,
        "allowNetwork": False,
        "allowFileWrite": False,
        "dockerImage": "python:3.11-slim",
    },
    "workerPool": {
        "enabled": True,
        "poolSize": 4,
        "taskTimeoutSeconds": 300,
        "maxMemoryMB": 1024,
        "heartbeatIntervalSeconds": 10,
        "shutdownTimeoutSeconds": 30,
        "maxQueueSize": 100,
        "allowNetwork": True,
        "allowFileWrite": True,
    },
}

DEFAULT_BROKER_CONFIG = {
    "version": "1.0",
    "exchanges": {
        "binance": {
            "enabled": True,
            "name": "Binance",
            "adapter": "ccxt",
            "ccxt_id": "binance",
            "markets": ["spot"],
            "default_market": "spot",
            "paper_mode": {
                "enabled": True,
                "sandbox_url": "https://testnet.binance.vision",
                "initial_balance_usdt": 10000,
            },
        }
    },
    "risk_management": {
        "position_limits": {
            "max_position_size_usd": 10000000,
            "max_positions_count": 5,
            "max_leverage": 1,
        },
        "loss_limits": {
            "max_daily_loss_usd": 500,
            "max_daily_loss_percent": 5,
            "max_drawdown_percent": 10,
        },
        "order_limits": {
            "min_order_size_usd": 10,
            "max_order_size_usd": 10000000,
            "max_slippage_percent": 1,
        },
    },
    "trading_settings": {
        "default_timeframe": "1m",
        "supported_timeframes": ["1s", "1m", "5m", "15m", "30m", "1h", "4h", "1d"],
    },
    "notifications": {
        "enabled": True,
        "channels": ["websocket"],
        "events": ["order_filled", "position_opened", "position_closed", "error", "risk_alert"],
    },
}

DEFAULT_REPORT_CONFIG = {
    "version": "1.0",
    "report": {
        "output_directory": "data/reports",
        "default_format": "html",
        "supported_formats": ["html", "pdf"],
    },
}

DEFAULT_LOGGER_CONFIG = {
    "version": "1.0",
    "logging": {
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "date_format": "%Y-%m-%d %H:%M:%S",
    },
}

DEFAULT_SITE = {
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

DEFAULT_BACKEND_ENV = {
    "ENCRYPTION_KEY": "",
    "ENABLE_LOGIN": "false",
    "AI_PROVIDER": "openai",
    "AI_PROVIDER_PRIORITY": "openai",
    "LOGTO_ISSUER": "",
    "LOGTO_JWKS_URI": "",
    "LOGTO_AUDIENCE": "",
    "LOGTO_REQUIRED_SCOPES": "",
    "LOGTO_ENDPOINT": "",
    "LOGTO_APP_ID": "",
    "LOGTO_REDIRECT_URI": "",
    "LOGTO_POST_LOGOUT_REDIRECT_URI": "",
    "EODHD_API_KEY": "",
    "OPENAI_API_KEY": "",
    "OPENAI_BASE_URL": AI_PROVIDER_DEFAULTS["openai"]["base_url"],
    "OPENAI_MODEL": AI_PROVIDER_DEFAULTS["openai"]["default_model"],
    "MINIMAX_API_KEY": "",
    "MINIMAX_BASE_URL": AI_PROVIDER_DEFAULTS["minimax"]["base_url"],
    "MINIMAX_MODEL": AI_PROVIDER_DEFAULTS["minimax"]["default_model"],
    "GEMINI_API_KEY": "",
    "GEMINI_BASE_URL": AI_PROVIDER_DEFAULTS["gemini"]["base_url"],
    "GEMINI_MODEL": AI_PROVIDER_DEFAULTS["gemini"]["default_model"],
    "CLAUDE_API_KEY": "",
    "CLAUDE_BASE_URL": AI_PROVIDER_DEFAULTS["claude"]["base_url"],
    "CLAUDE_MODEL": AI_PROVIDER_DEFAULTS["claude"]["default_model"],
    "HTTP_PROXY": "",
    "HTTPS_PROXY": "",
    "CORS_ALLOW_ORIGINS": "",
    "CORS_ALLOW_ORIGIN_REGEX": "",
    "CORS_ALLOW_CREDENTIALS": "false",
    "LIVE_TRADING_ENABLED": "false",
    "DEFAULT_EXCHANGE": "binance",
    "DEFAULT_TRADE_MODE": "paper",
    "REPORT_SHARE_SECRET": "",
    "REPORT_MAX_AGE_DAYS": "30",
    "CCXT_BINANCE_PAPER_API_KEY": "",
    "CCXT_BINANCE_PAPER_SECRET": "",
    "CCXT_BINANCE_LIVE_API_KEY": "",
    "CCXT_BINANCE_LIVE_SECRET": "",
}


def _is_truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"true", "1", "yes", "on"}


def _clean_string(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _load_json(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return copy.deepcopy(default)
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _deep_merge(base: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
    merged = copy.deepcopy(base)
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _read_env_file(path: Path, fallback_defaults: dict[str, str]) -> tuple[list[tuple[str, str | None]], dict[str, str]]:
    if not path.exists():
        return [], dict(fallback_defaults)

    lines = path.read_text(encoding="utf-8").splitlines()
    parsed_lines: list[tuple[str, str | None]] = []
    values = dict(fallback_defaults)
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in line:
            parsed_lines.append((line, None))
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        values[key] = value.strip().strip('"').strip("'")
        parsed_lines.append((line, key))
    return parsed_lines, values


def _write_env_file(path: Path, parsed_lines: list[tuple[str, str | None]], updates: dict[str, str]) -> None:
    lines: list[str] = []
    seen: set[str] = set()
    for raw_line, key in parsed_lines:
        if key is None:
            lines.append(raw_line)
            continue
        if key in updates:
            lines.append(f"{key}={updates[key]}")
            seen.add(key)
        else:
            lines.append(raw_line)
            seen.add(key)
    for key, value in updates.items():
        if key not in seen:
            lines.append(f"{key}={value}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _build_masked_secret(value: str | None) -> str:
    return mask_credential(value) if value else ""


def _resolve_secret(current_value: str | None, incoming_value: str | None) -> str:
    candidate = _clean_string(incoming_value)
    if current_value and candidate == mask_credential(current_value):
        return current_value
    return candidate


def _normalize_provider_priority(priority: list[str] | None) -> list[str]:
    normalized: list[str] = []
    for provider in priority or []:
        provider_name = _clean_string(provider).lower()
        if provider_name in AI_PROVIDER_DEFAULTS and provider_name not in normalized:
            normalized.append(provider_name)
    return normalized


def _resolve_provider_priority(env_values: dict[str, str]) -> list[str]:
    raw_priority = _clean_string(env_values.get("AI_PROVIDER_PRIORITY"))
    if raw_priority:
        normalized = _normalize_provider_priority(raw_priority.split(","))
        if normalized:
            return normalized

    legacy_provider = _clean_string(env_values.get("AI_PROVIDER")).lower()
    if legacy_provider in AI_PROVIDER_DEFAULTS:
        return [legacy_provider]

    configured = [
        provider
        for provider, defaults in AI_PROVIDER_DEFAULTS.items()
        if _clean_string(env_values.get(defaults["api_key_env"]))
    ]
    return configured or ["openai"]


def _build_default_ai_providers() -> dict[str, dict[str, str]]:
    return {
        provider: {
            "api_key": "",
            "base_url": defaults["base_url"],
            "default_model": defaults["default_model"],
        }
        for provider, defaults in AI_PROVIDER_DEFAULTS.items()
    }


def _deployment_requires_login(deployment_mode: str) -> bool:
    return deployment_mode == "public"


class PostgreSQLConfig(BaseModel):
    host: str = "localhost"
    port: int = 5432
    database: str = "trading"
    username: str = "trading_user"
    password: str = ""


class DatabaseSelection(BaseModel):
    mode: str = "sqlite"
    sqlite_path: str = DEFAULT_DB_PATH.name
    postgresql: PostgreSQLConfig = Field(default_factory=PostgreSQLConfig)


class SecurityConfig(BaseModel):
    encryption_key: str = ""
    enable_login: bool = False


class AuthConfig(BaseModel):
    logto_issuer: str = ""
    logto_jwks_uri: str = ""
    logto_audience: str = ""
    logto_required_scopes: str = ""
    logto_endpoint: str = ""
    logto_app_id: str = ""
    logto_redirect_uri: str = ""
    logto_post_logout_redirect_uri: str = ""


class DataSourceConfig(BaseModel):
    priority: list[str] = Field(default_factory=lambda: ["yahoo", "database"])
    eodhd_api_key: str = ""


class AIProviderConfig(BaseModel):
    api_key: str = ""
    base_url: str = ""
    default_model: str = ""


class AIConfig(BaseModel):
    enabled: bool = False
    provider_priority: list[str] = Field(default_factory=lambda: ["openai"])
    providers: dict[str, AIProviderConfig] = Field(
        default_factory=lambda: {
            provider: AIProviderConfig(base_url=defaults["base_url"])
            for provider, defaults in AI_PROVIDER_DEFAULTS.items()
        }
    )


class ExchangeCredential(BaseModel):
    api_key: str = ""
    secret: str = ""


class BinanceCredentials(BaseModel):
    paper: ExchangeCredential = Field(default_factory=ExchangeCredential)
    live: ExchangeCredential = Field(default_factory=ExchangeCredential)


class BinanceTradingConfig(BaseModel):
    enabled: bool = True
    markets: list[str] = Field(default_factory=lambda: ["spot"])
    default_market: str = "spot"
    paper_enabled: bool = True
    sandbox_url: str = "https://testnet.binance.vision"
    initial_balance_usdt: float = 10000


class TradingRiskConfig(BaseModel):
    max_position_size_usd: float = 10000000
    max_positions_count: int = 5
    max_leverage: int = 1
    max_daily_loss_usd: float = 500
    max_daily_loss_percent: float = 5
    max_drawdown_percent: float = 10
    min_order_size_usd: float = 10
    max_order_size_usd: float = 10000000
    max_slippage_percent: float = 1


class TradingConfig(BaseModel):
    live_trading_enabled: bool = False
    default_trade_mode: str = "paper"
    binance: BinanceTradingConfig = Field(default_factory=BinanceTradingConfig)
    risk: TradingRiskConfig = Field(default_factory=TradingRiskConfig)
    credentials: BinanceCredentials = Field(default_factory=BinanceCredentials)
    live_risk_acknowledged: bool = False


class StrategyConfigPayload(BaseModel):
    file_path: str = "resources/strategy"
    sandbox_mode: str = "subprocess"
    worker_pool_enabled: bool = True
    worker_pool_size: int = 4


class SiteConfigPayload(BaseModel):
    site_title: str = DEFAULT_SITE["site_title"]
    site_description: str = DEFAULT_SITE["site_description"]
    site_docs_url: str = ""
    site_github_url: str = ""
    site_twitter_url: str = ""
    site_email: str = ""
    site_stats_strategies: str = DEFAULT_SITE["site_stats_strategies"]
    site_stats_backtests: str = DEFAULT_SITE["site_stats_backtests"]
    site_stats_users: str = DEFAULT_SITE["site_stats_users"]


class ReportConfigPayload(BaseModel):
    enable_public_share: bool = False
    report_share_secret: str = ""
    report_max_age_days: int = 30
    output_directory: str = "data/reports"


class NetworkConfigPayload(BaseModel):
    http_proxy: str = ""
    https_proxy: str = ""
    cors_allow_origins: str = ""
    cors_allow_origin_regex: str = ""
    cors_allow_credentials: bool = False


class SetupWizardPayload(BaseModel):
    deployment_mode: str = "local"
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    database: DatabaseSelection
    auth: AuthConfig = Field(default_factory=AuthConfig)
    data_source: DataSourceConfig = Field(default_factory=DataSourceConfig)
    ai: AIConfig = Field(default_factory=AIConfig)
    trading: TradingConfig = Field(default_factory=TradingConfig)
    strategy: StrategyConfigPayload = Field(default_factory=StrategyConfigPayload)
    site: SiteConfigPayload = Field(default_factory=SiteConfigPayload)
    report: ReportConfigPayload = Field(default_factory=ReportConfigPayload)
    network: NetworkConfigPayload = Field(default_factory=NetworkConfigPayload)

    @model_validator(mode="after")
    def validate_cross_fields(self) -> "SetupWizardPayload":
        if self.deployment_mode not in {"local", "public"}:
            raise ValueError("Deployment mode must be local or public")

        login_enabled = _deployment_requires_login(self.deployment_mode)
        self.security.enable_login = login_enabled
        self.security.encryption_key = _clean_string(self.security.encryption_key) or generate_encryption_key()

        if self.database.mode not in {"sqlite", "postgresql"}:
            raise ValueError("Database mode must be sqlite or postgresql")

        if self.database.mode == "sqlite" and not _clean_string(self.database.sqlite_path):
            raise ValueError("SQLite path is required")

        if self.database.mode == "postgresql":
            pg = self.database.postgresql
            required_pg = {
                "host": pg.host,
                "database": pg.database,
                "username": pg.username,
            }
            missing_pg = [key for key, value in required_pg.items() if not _clean_string(value)]
            if missing_pg:
                raise ValueError(f"PostgreSQL fields required: {', '.join(missing_pg)}")

        if login_enabled:
            required_auth = {
                "LOGTO_ISSUER": self.auth.logto_issuer,
                "LOGTO_JWKS_URI": self.auth.logto_jwks_uri,
                "LOGTO_AUDIENCE": self.auth.logto_audience,
                "LOGTO_ENDPOINT": self.auth.logto_endpoint,
                "LOGTO_APP_ID": self.auth.logto_app_id,
                "LOGTO_REDIRECT_URI": self.auth.logto_redirect_uri,
                "LOGTO_POST_LOGOUT_REDIRECT_URI": self.auth.logto_post_logout_redirect_uri,
            }
            missing = [key for key, value in required_auth.items() if not _clean_string(value)]
            if missing:
                raise ValueError(f"Logto fields required when login is enabled: {', '.join(missing)}")

        if "eodhd" in self.data_source.priority and not _clean_string(self.data_source.eodhd_api_key):
            raise ValueError("EODHD_API_KEY is required when EODHD is enabled")

        provider_priority = _normalize_provider_priority(self.ai.provider_priority)
        if self.ai.enabled:
            if not provider_priority:
                raise ValueError("At least one AI provider must be enabled")
            missing_api_keys = [
                provider
                for provider in provider_priority
                if not _clean_string((self.ai.providers.get(provider) or AIProviderConfig()).api_key)
            ]
            if missing_api_keys:
                raise ValueError(
                    "API key is required for enabled AI providers: " + ", ".join(missing_api_keys)
                )
            missing_models = [
                provider
                for provider in provider_priority
                if not _clean_string((self.ai.providers.get(provider) or AIProviderConfig()).default_model)
            ]
            if missing_models:
                raise ValueError(
                    "Runtime model is required for enabled AI providers: " + ", ".join(missing_models)
                )

        paper_creds = self.trading.credentials.paper
        live_creds = self.trading.credentials.live
        paper_partial = any(_clean_string(value) for value in (paper_creds.api_key, paper_creds.secret))
        live_partial = any(_clean_string(value) for value in (live_creds.api_key, live_creds.secret))

        if paper_partial and (
            not _clean_string(paper_creds.api_key) or not _clean_string(paper_creds.secret)
        ):
            raise ValueError("Binance paper credentials require both API key and secret")

        if live_partial and (
            not _clean_string(live_creds.api_key) or not _clean_string(live_creds.secret)
        ):
            raise ValueError("Binance live credentials require both API key and secret")

        self.trading.default_trade_mode = "paper"
        self.trading.binance.default_market = "spot"
        self.trading.binance.markets = ["spot"]

        if self.trading.live_trading_enabled:
            if not _clean_string(live_creds.api_key) or not _clean_string(live_creds.secret):
                raise ValueError("Binance live credentials are required when live trading is enabled")
            if not self.trading.live_risk_acknowledged:
                raise ValueError("Live trading requires explicit risk acknowledgement")

        if self.report.enable_public_share and not _clean_string(self.report.report_share_secret):
            raise ValueError("REPORT_SHARE_SECRET is required when public report sharing is enabled")

        if self.network.cors_allow_credentials and "*" in {
            item.strip() for item in self.network.cors_allow_origins.split(",") if item.strip()
        }:
            raise ValueError("CORS_ALLOW_ORIGINS cannot contain '*' when credentials are enabled")

        return self


class SetupWizardService:
    """Read, validate, and persist first-run setup configuration."""

    def __init__(self) -> None:
        self.backend_env_path = PROJECT_ROOT / ".env"
        self.backend_env_template_path = PROJECT_ROOT / ".env.template"
        self.database_config_path = CONFIG_DIR / "database_config.json"
        self.strategy_config_path = CONFIG_DIR / "strategy_config.json"
        self.broker_config_path = CONFIG_DIR / "broker_config.json"
        self.report_config_path = CONFIG_DIR / "report_config.json"
        self.logger_config_path = CONFIG_DIR / "logger_config.json"

    def _backend_env(self) -> tuple[list[tuple[str, str | None]], dict[str, str]]:
        source = self.backend_env_path if self.backend_env_path.exists() else self.backend_env_template_path
        return _read_env_file(source, DEFAULT_BACKEND_ENV)

    def _build_ai_state(self, env_values: dict[str, str]) -> dict[str, Any]:
        provider_priority = _resolve_provider_priority(env_values)
        providers = _build_default_ai_providers()
        enabled = False

        for provider, defaults in AI_PROVIDER_DEFAULTS.items():
            api_key = env_values.get(defaults["api_key_env"], "")
            base_url = env_values.get(defaults["base_url_env"], "") or defaults["base_url"]
            default_model = env_values.get(defaults["model_env"], "") or defaults["default_model"]
            providers[provider] = {
                "api_key": _build_masked_secret(api_key),
                "base_url": base_url,
                "default_model": default_model,
                "configured": bool(_clean_string(api_key)),
            }
            if _clean_string(api_key):
                enabled = True

        return {
            "enabled": enabled,
            "provider_priority": provider_priority,
            "providers": providers,
        }

    def _build_trading_credentials(self, env_values: dict[str, str]) -> dict[str, Any]:
        paper_api_key = env_values.get("CCXT_BINANCE_PAPER_API_KEY", "")
        paper_secret = env_values.get("CCXT_BINANCE_PAPER_SECRET", "")
        live_api_key = env_values.get("CCXT_BINANCE_LIVE_API_KEY", "")
        live_secret = env_values.get("CCXT_BINANCE_LIVE_SECRET", "")
        return {
            "paper": {
                "api_key": _build_masked_secret(paper_api_key),
                "secret": _build_masked_secret(paper_secret),
                "configured": bool(_clean_string(paper_api_key) and _clean_string(paper_secret)),
            },
            "live": {
                "api_key": _build_masked_secret(live_api_key),
                "secret": _build_masked_secret(live_secret),
                "configured": bool(_clean_string(live_api_key) and _clean_string(live_secret)),
            },
        }

    def _build_summary(self, payload: SetupWizardPayload) -> list[dict[str, Any]]:
        warnings: list[str] = []
        login_enabled = _deployment_requires_login(payload.deployment_mode)
        if not payload.ai.enabled:
            warnings.append("AI analysis remains disabled until at least one provider key is configured.")
        if not login_enabled:
            warnings.append("Authentication remains disabled; the application will be publicly accessible.")
        if "eodhd" not in payload.data_source.priority:
            warnings.append("Only Yahoo Finance and cached database data sources are enabled.")
        if not _clean_string(payload.trading.credentials.paper.api_key):
            warnings.append("Binance paper credentials are not configured yet.")
        if not payload.trading.live_trading_enabled:
            warnings.append("Binance live trading remains disabled.")
        if not payload.report.enable_public_share:
            warnings.append("Public report sharing remains disabled.")

        return [
            {"target_file": "backend/.env", "purpose": "Runtime secrets and feature flags"},
            {"target_file": "backend/resources/config/database_config.json", "purpose": "Database backend selection"},
            {"target_file": "backend/resources/config/strategy_config.json", "purpose": "Strategy path and worker execution defaults"},
            {"target_file": "backend/resources/config/broker_config.json", "purpose": "Binance trading defaults and risk limits"},
            {"target_file": "backend/resources/config/report_config.json", "purpose": "Report output directory"},
            {"target_file": "backend/resources/config/logger_config.json", "purpose": "Current logger defaults retained"},
            {"warnings": warnings},
        ]

    def get_wizard_state(self) -> dict[str, Any]:
        _, backend_env = self._backend_env()
        database_config = _load_json(self.database_config_path, DEFAULT_DATABASE_CONFIG)
        strategy_config = _load_json(self.strategy_config_path, DEFAULT_STRATEGY_CONFIG)
        broker_config = _load_json(self.broker_config_path, DEFAULT_BROKER_CONFIG)
        report_config = _load_json(self.report_config_path, DEFAULT_REPORT_CONFIG)
        logger_config = _load_json(self.logger_config_path, DEFAULT_LOGGER_CONFIG)

        site_values = {
            key: backend_env.get(env_key, DEFAULT_SITE[key]) or DEFAULT_SITE[key]
            for key, env_key in SITE_ENV_MAPPING.items()
        }
        binance_config = broker_config.get("exchanges", {}).get(
            "binance",
            DEFAULT_BROKER_CONFIG["exchanges"]["binance"],
        )

        return {
            "status": {
                "is_ready": bool(_clean_string(backend_env.get("ENCRYPTION_KEY"))),
                "requires_login": _is_truthy(backend_env.get("ENABLE_LOGIN")),
                "has_encryption_key": bool(_clean_string(backend_env.get("ENCRYPTION_KEY"))),
            },
            "config": {
                "deployment_mode": "public" if _is_truthy(backend_env.get("ENABLE_LOGIN")) else "local",
                "security": {
                    "encryption_key": _build_masked_secret(backend_env.get("ENCRYPTION_KEY")),
                    "encryption_key_configured": bool(_clean_string(backend_env.get("ENCRYPTION_KEY"))),
                    "enable_login": _is_truthy(backend_env.get("ENABLE_LOGIN")),
                },
                "database": {
                    "mode": database_config.get("database", {}).get("type", "sqlite"),
                    "sqlite_path": database_config.get("database", {}).get("sqlite", {}).get("path", DEFAULT_DB_PATH.name),
                    "postgresql": {
                        "host": database_config.get("database", {}).get("postgresql", {}).get("host", "localhost"),
                        "port": database_config.get("database", {}).get("postgresql", {}).get("port", 5432),
                        "database": database_config.get("database", {}).get("postgresql", {}).get("database", "trading"),
                        "username": database_config.get("database", {}).get("postgresql", {}).get("username", "trading_user"),
                        "password": _build_masked_secret(
                            database_config.get("database", {}).get("postgresql", {}).get("password", "")
                        ),
                    },
                },
                "auth": {
                    "logto_issuer": backend_env.get("LOGTO_ISSUER", ""),
                    "logto_jwks_uri": backend_env.get("LOGTO_JWKS_URI", ""),
                    "logto_audience": backend_env.get("LOGTO_AUDIENCE", ""),
                    "logto_required_scopes": backend_env.get("LOGTO_REQUIRED_SCOPES", ""),
                    "logto_endpoint": backend_env.get("LOGTO_ENDPOINT", ""),
                    "logto_app_id": backend_env.get("LOGTO_APP_ID", ""),
                    "logto_redirect_uri": backend_env.get("LOGTO_REDIRECT_URI", ""),
                    "logto_post_logout_redirect_uri": backend_env.get("LOGTO_POST_LOGOUT_REDIRECT_URI", ""),
                },
                "data_source": {
                    "priority": ["eodhd", "yahoo", "database"]
                    if _clean_string(backend_env.get("EODHD_API_KEY"))
                    else ["yahoo", "database"],
                    "eodhd_api_key": _build_masked_secret(backend_env.get("EODHD_API_KEY", "")),
                    "eodhd_configured": bool(_clean_string(backend_env.get("EODHD_API_KEY"))),
                },
                "ai": self._build_ai_state(backend_env),
                "trading": {
                    "live_trading_enabled": _is_truthy(backend_env.get("LIVE_TRADING_ENABLED")),
                    "default_trade_mode": backend_env.get("DEFAULT_TRADE_MODE", "paper"),
                    "binance": {
                        "enabled": bool(binance_config.get("enabled", True)),
                        "markets": binance_config.get("markets", ["spot"]),
                        "default_market": binance_config.get("default_market", "spot"),
                        "paper_enabled": binance_config.get("paper_mode", {}).get("enabled", True),
                        "sandbox_url": binance_config.get("paper_mode", {}).get("sandbox_url", "https://testnet.binance.vision"),
                        "initial_balance_usdt": binance_config.get("paper_mode", {}).get("initial_balance_usdt", 10000),
                    },
                    "risk": {
                        "max_position_size_usd": broker_config.get("risk_management", {}).get("position_limits", {}).get("max_position_size_usd", 10000000),
                        "max_positions_count": broker_config.get("risk_management", {}).get("position_limits", {}).get("max_positions_count", 5),
                        "max_leverage": broker_config.get("risk_management", {}).get("position_limits", {}).get("max_leverage", 1),
                        "max_daily_loss_usd": broker_config.get("risk_management", {}).get("loss_limits", {}).get("max_daily_loss_usd", 500),
                        "max_daily_loss_percent": broker_config.get("risk_management", {}).get("loss_limits", {}).get("max_daily_loss_percent", 5),
                        "max_drawdown_percent": broker_config.get("risk_management", {}).get("loss_limits", {}).get("max_drawdown_percent", 10),
                        "min_order_size_usd": broker_config.get("risk_management", {}).get("order_limits", {}).get("min_order_size_usd", 10),
                        "max_order_size_usd": broker_config.get("risk_management", {}).get("order_limits", {}).get("max_order_size_usd", 10000000),
                        "max_slippage_percent": broker_config.get("risk_management", {}).get("order_limits", {}).get("max_slippage_percent", 1),
                    },
                    "credentials": self._build_trading_credentials(backend_env),
                    "live_risk_acknowledged": False,
                },
                "strategy": {
                    "file_path": strategy_config.get("strategy", {}).get("filePath", "resources/strategy"),
                    "sandbox_mode": strategy_config.get("sandbox", {}).get("mode", "subprocess"),
                    "worker_pool_enabled": strategy_config.get("workerPool", {}).get("enabled", True),
                    "worker_pool_size": strategy_config.get("workerPool", {}).get("poolSize", 4),
                },
                "site": site_values,
                "report": {
                    "enable_public_share": bool(_clean_string(backend_env.get("REPORT_SHARE_SECRET"))),
                    "report_share_secret": _build_masked_secret(backend_env.get("REPORT_SHARE_SECRET", "")),
                    "report_share_secret_configured": bool(_clean_string(backend_env.get("REPORT_SHARE_SECRET"))),
                    "report_max_age_days": int(backend_env.get("REPORT_MAX_AGE_DAYS", "30") or 30),
                    "output_directory": report_config.get("report", {}).get("output_directory", "data/reports"),
                },
                "network": {
                    "http_proxy": backend_env.get("HTTP_PROXY", ""),
                    "https_proxy": backend_env.get("HTTPS_PROXY", ""),
                    "cors_allow_origins": backend_env.get("CORS_ALLOW_ORIGINS", ""),
                    "cors_allow_origin_regex": backend_env.get("CORS_ALLOW_ORIGIN_REGEX", ""),
                    "cors_allow_credentials": _is_truthy(backend_env.get("CORS_ALLOW_CREDENTIALS")),
                },
            },
            "meta": {
                "generated_encryption_key": generate_encryption_key(),
                "files": [
                    "backend/.env",
                    "backend/resources/config/database_config.json",
                    "backend/resources/config/strategy_config.json",
                    "backend/resources/config/broker_config.json",
                    "backend/resources/config/report_config.json",
                    "backend/resources/config/logger_config.json",
                ],
                "logger_defaults": logger_config.get("logging", {}),
            },
        }

    def validate_payload(self, payload: dict[str, Any]) -> SetupWizardPayload:
        try:
            return SetupWizardPayload.model_validate(payload)
        except PydanticValidationError as exc:
            message = "; ".join(error["msg"] for error in exc.errors())
            raise ValueError(message) from exc

    def save(self, payload: dict[str, Any]) -> dict[str, Any]:
        validated = self.validate_payload(payload)
        login_enabled = _deployment_requires_login(validated.deployment_mode)
        backend_lines, backend_env = self._backend_env()

        database_config = _load_json(self.database_config_path, DEFAULT_DATABASE_CONFIG)
        strategy_config = _load_json(self.strategy_config_path, DEFAULT_STRATEGY_CONFIG)
        report_config = _load_json(self.report_config_path, DEFAULT_REPORT_CONFIG)
        logger_config = _load_json(self.logger_config_path, DEFAULT_LOGGER_CONFIG)

        backend_updates = dict(backend_env)
        backend_updates["ENCRYPTION_KEY"] = _resolve_secret(backend_env.get("ENCRYPTION_KEY"), validated.security.encryption_key)
        backend_updates["ENABLE_LOGIN"] = str(login_enabled).lower()
        if "DATABASE_URL" in backend_env:
            backend_updates["DATABASE_URL"] = ""

        backend_updates["LOGTO_ISSUER"] = validated.auth.logto_issuer if login_enabled else ""
        backend_updates["LOGTO_JWKS_URI"] = validated.auth.logto_jwks_uri if login_enabled else ""
        backend_updates["LOGTO_AUDIENCE"] = validated.auth.logto_audience if login_enabled else ""
        backend_updates["LOGTO_REQUIRED_SCOPES"] = validated.auth.logto_required_scopes if login_enabled else ""
        backend_updates["LOGTO_ENDPOINT"] = validated.auth.logto_endpoint if login_enabled else ""
        backend_updates["LOGTO_APP_ID"] = validated.auth.logto_app_id if login_enabled else ""
        backend_updates["LOGTO_REDIRECT_URI"] = validated.auth.logto_redirect_uri if login_enabled else ""
        backend_updates["LOGTO_POST_LOGOUT_REDIRECT_URI"] = (
            validated.auth.logto_post_logout_redirect_uri if login_enabled else ""
        )
        backend_updates["EODHD_API_KEY"] = _resolve_secret(backend_env.get("EODHD_API_KEY"), validated.data_source.eodhd_api_key)

        provider_priority = _normalize_provider_priority(validated.ai.provider_priority) if validated.ai.enabled else []
        backend_updates["AI_PROVIDER"] = provider_priority[0] if provider_priority else ""
        backend_updates["AI_PROVIDER_PRIORITY"] = ",".join(provider_priority)
        for provider, defaults in AI_PROVIDER_DEFAULTS.items():
            provider_config = validated.ai.providers.get(provider) or AIProviderConfig(base_url=defaults["base_url"])
            backend_updates[defaults["api_key_env"]] = (
                _resolve_secret(backend_env.get(defaults["api_key_env"]), provider_config.api_key)
                if validated.ai.enabled
                else ""
            )
            backend_updates[defaults["base_url_env"]] = _clean_string(provider_config.base_url) or defaults["base_url"]
            backend_updates[defaults["model_env"]] = _clean_string(provider_config.default_model) or defaults["default_model"]

        backend_updates["HTTP_PROXY"] = validated.network.http_proxy
        backend_updates["HTTPS_PROXY"] = validated.network.https_proxy
        backend_updates["CORS_ALLOW_ORIGINS"] = validated.network.cors_allow_origins
        backend_updates["CORS_ALLOW_ORIGIN_REGEX"] = validated.network.cors_allow_origin_regex
        backend_updates["CORS_ALLOW_CREDENTIALS"] = str(validated.network.cors_allow_credentials).lower()
        backend_updates["LIVE_TRADING_ENABLED"] = str(validated.trading.live_trading_enabled).lower()
        backend_updates["DEFAULT_EXCHANGE"] = "binance"
        backend_updates["DEFAULT_TRADE_MODE"] = validated.trading.default_trade_mode
        backend_updates["REPORT_SHARE_SECRET"] = (
            _resolve_secret(backend_env.get("REPORT_SHARE_SECRET"), validated.report.report_share_secret)
            if validated.report.enable_public_share
            else ""
        )
        backend_updates["REPORT_MAX_AGE_DAYS"] = str(validated.report.report_max_age_days)

        for site_key, env_key in SITE_ENV_MAPPING.items():
            backend_updates[env_key] = getattr(validated.site, site_key)

        backend_updates["CCXT_BINANCE_PAPER_API_KEY"] = _resolve_secret(
            backend_env.get("CCXT_BINANCE_PAPER_API_KEY"),
            validated.trading.credentials.paper.api_key,
        )
        backend_updates["CCXT_BINANCE_PAPER_SECRET"] = _resolve_secret(
            backend_env.get("CCXT_BINANCE_PAPER_SECRET"),
            validated.trading.credentials.paper.secret,
        )
        backend_updates["CCXT_BINANCE_LIVE_API_KEY"] = _resolve_secret(
            backend_env.get("CCXT_BINANCE_LIVE_API_KEY"),
            validated.trading.credentials.live.api_key,
        )
        backend_updates["CCXT_BINANCE_LIVE_SECRET"] = _resolve_secret(
            backend_env.get("CCXT_BINANCE_LIVE_SECRET"),
            validated.trading.credentials.live.secret,
        )

        for legacy_key in LEGACY_EXCHANGE_ENV_KEYS:
            if legacy_key in backend_env:
                backend_updates[legacy_key] = ""

        database_updates = {
            "database": {
                "type": validated.database.mode,
                "sqlite": {
                    **database_config.get("database", {}).get("sqlite", {}),
                    "path": validated.database.sqlite_path,
                },
                "postgresql": {
                    **database_config.get("database", {}).get("postgresql", {}),
                    "host": validated.database.postgresql.host,
                    "port": validated.database.postgresql.port,
                    "database": validated.database.postgresql.database,
                    "username": validated.database.postgresql.username,
                    "password": _resolve_secret(
                        database_config.get("database", {}).get("postgresql", {}).get("password", ""),
                        validated.database.postgresql.password,
                    ),
                },
            }
        }

        strategy_updates = {
            "strategy": {"filePath": validated.strategy.file_path},
            "sandbox": {
                **strategy_config.get("sandbox", {}),
                "mode": validated.strategy.sandbox_mode,
            },
            "workerPool": {
                **strategy_config.get("workerPool", {}),
                "enabled": validated.strategy.worker_pool_enabled,
                "poolSize": validated.strategy.worker_pool_size,
            },
        }

        broker_config = copy.deepcopy(DEFAULT_BROKER_CONFIG)
        broker_config["exchanges"]["binance"]["enabled"] = validated.trading.binance.enabled
        broker_config["exchanges"]["binance"]["markets"] = validated.trading.binance.markets
        broker_config["exchanges"]["binance"]["default_market"] = validated.trading.binance.default_market
        broker_config["exchanges"]["binance"]["paper_mode"]["enabled"] = validated.trading.binance.paper_enabled
        broker_config["exchanges"]["binance"]["paper_mode"]["sandbox_url"] = validated.trading.binance.sandbox_url
        broker_config["exchanges"]["binance"]["paper_mode"]["initial_balance_usdt"] = validated.trading.binance.initial_balance_usdt
        broker_config["risk_management"]["position_limits"]["max_position_size_usd"] = validated.trading.risk.max_position_size_usd
        broker_config["risk_management"]["position_limits"]["max_positions_count"] = validated.trading.risk.max_positions_count
        broker_config["risk_management"]["position_limits"]["max_leverage"] = validated.trading.risk.max_leverage
        broker_config["risk_management"]["loss_limits"]["max_daily_loss_usd"] = validated.trading.risk.max_daily_loss_usd
        broker_config["risk_management"]["loss_limits"]["max_daily_loss_percent"] = validated.trading.risk.max_daily_loss_percent
        broker_config["risk_management"]["loss_limits"]["max_drawdown_percent"] = validated.trading.risk.max_drawdown_percent
        broker_config["risk_management"]["order_limits"]["min_order_size_usd"] = validated.trading.risk.min_order_size_usd
        broker_config["risk_management"]["order_limits"]["max_order_size_usd"] = validated.trading.risk.max_order_size_usd
        broker_config["risk_management"]["order_limits"]["max_slippage_percent"] = validated.trading.risk.max_slippage_percent

        report_updates = {
            "report": {
                **report_config.get("report", {}),
                "output_directory": validated.report.output_directory,
            }
        }

        _write_env_file(self.backend_env_path, backend_lines, backend_updates)
        self.database_config_path.write_text(
            json.dumps(_deep_merge(database_config, database_updates), indent=4, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        self.strategy_config_path.write_text(
            json.dumps(_deep_merge(strategy_config, strategy_updates), indent=4, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        self.broker_config_path.write_text(json.dumps(broker_config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        self.report_config_path.write_text(
            json.dumps(_deep_merge(report_config, report_updates), indent=4, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        self.logger_config_path.write_text(json.dumps(logger_config, indent=4, ensure_ascii=False) + "\n", encoding="utf-8")

        return {
            "status": "ok",
            "saved_files": [
                "backend/.env",
                "backend/resources/config/database_config.json",
                "backend/resources/config/strategy_config.json",
                "backend/resources/config/broker_config.json",
                "backend/resources/config/report_config.json",
                "backend/resources/config/logger_config.json",
            ],
            "summary": self._build_summary(validated),
        }

    def test_endpoint(self, test_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        from src.utils.credential_validator import validate_credential

        normalized_type = test_type.lower()
        if normalized_type == "logto":
            valid, message = validate_credential(
                "logto",
                issuer=payload.get("issuer"),
                jwks_uri=payload.get("jwks_uri"),
            )
            return {"status": "ok", "valid": valid, "message": message}
        if normalized_type in {"openai", "ai_model"}:
            valid, message = validate_credential(
                "ai_model",
                provider=payload.get("provider", "openai"),
                api_key=payload.get("api_key"),
                base_url=payload.get("base_url"),
                model=payload.get("model"),
            )
            return {"status": "ok", "valid": valid, "message": message}
        if normalized_type == "ccxt":
            valid, message = validate_credential(
                "ccxt",
                exchange=payload.get("exchange", "binance"),
                mode=payload.get("mode"),
                api_key=payload.get("api_key"),
                secret=payload.get("secret"),
                use_testnet=payload.get("use_testnet"),
            )
            return {"status": "ok", "valid": valid, "message": message}
        if normalized_type == "proxy":
            valid, message = validate_credential("proxy", proxy_url=payload.get("proxy_url"))
            return {"status": "ok", "valid": valid, "message": message}
        raise ValueError(f"Unsupported setup test type: {test_type}")


__all__ = ["SetupWizardPayload", "SetupWizardService"]
