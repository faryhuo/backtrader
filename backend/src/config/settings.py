import os
import sys
from pathlib import Path
from urllib.parse import unquote

from dotenv import load_dotenv

def _resolve_project_root() -> Path:
    """Resolve the runtime backend root for source and frozen builds."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent.parent


# Resolve key paths for the backend.
PROJECT_ROOT = _resolve_project_root()
BASE_DIR = PROJECT_ROOT / "src"
RESOURCES_DIR = PROJECT_ROOT / "resources"
FRONTEND_DIR = RESOURCES_DIR / "frontend"
ASSETS_DIR = FRONTEND_DIR / "assets"
IMAGES_DIR = RESOURCES_DIR / "images"
STRATEGY_DIR = RESOURCES_DIR / "strategy"
CONFIG_DIR = RESOURCES_DIR / "config"
REPORTS_DIR = RESOURCES_DIR / "reports"
TEMPLATES_DIR = RESOURCES_DIR / "templates"

# Load environment variables from the backend .env if present.
load_dotenv(PROJECT_ROOT / ".env", override=False)

# Authentication / platform configuration.
LOGTO_ISSUER = os.getenv("LOGTO_ISSUER")
LOGTO_JWKS_URI = os.getenv("LOGTO_JWKS_URI")
LOGTO_AUDIENCE = os.getenv("LOGTO_AUDIENCE")
ENABLE_LOGIN = os.getenv("ENABLE_LOGIN", "true").lower() not in {"false", "0", "no", "off"}
AUTH_PROVIDER = os.getenv("AUTH_PROVIDER", "logto" if ENABLE_LOGIN else "none").strip().lower()
SYSTEM_AUTH_ALLOW_REGISTRATION = os.getenv("SYSTEM_AUTH_ALLOW_REGISTRATION", "false").lower() in {"true", "1", "yes", "on"}
SYSTEM_AUTH_SECRET = os.getenv("SYSTEM_AUTH_SECRET")
LOGTO_REQUIRED_SCOPES = [
    scope.strip()
    for scope in os.getenv("LOGTO_REQUIRED_SCOPES", "").split()
    if scope.strip()
]

# External services.
# Database configuration with centralized default path
DEFAULT_DB_PATH = PROJECT_ROOT / "trading_sessions.db"
DEFAULT_DB_URL = f"sqlite:///{DEFAULT_DB_PATH}"
DEFAULT_STRATEGY_PATH = STRATEGY_DIR


def load_database_config() -> dict:
    """
    Load database configuration from database_config.json.
    
    Returns:
        dict: Database configuration with all settings
    """
    import json
    config_file = CONFIG_DIR / "database_config.json"
    
    if config_file.exists():
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            import logging
            logging.getLogger(__name__).warning(f"Failed to load database_config.json: {e}")
    
    # Return default config if file doesn't exist or fails to load
    return {
        "database": {
            "type": "sqlite",
            "sqlite": {"path": str(DEFAULT_DB_PATH.name)}
        }
    }


def load_report_config() -> dict:
    """
    Load report generation configuration from report_config.json.
    
    Priority:
    1. report_config.json (user-customized)
    2. report_config.template.json (defaults)
    3. Hardcoded defaults (fallback)
    
    Returns:
        dict: Report configuration with all settings
    """
    import json
    import logging
    logger = logging.getLogger(__name__)
    
    # Try user config first
    config_file = CONFIG_DIR / "report_config.json"
    if config_file.exists():
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                logger.debug("Loaded report config from report_config.json")
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load report_config.json: {e}")
    
    # Fallback to template
    template_file = CONFIG_DIR / "report_config.template.json"
    if template_file.exists():
        try:
            with open(template_file, "r", encoding="utf-8") as f:
                logger.debug("Loaded report config from report_config.template.json")
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load report_config.template.json: {e}")
    
    # Return default config if all files fail
    return {
        "version": "1.0",
        "report": {
            "output_directory": "reports",
            "default_format": "html",
            "supported_formats": ["html", "pdf"]
        },
        "templates": {
            "backtest_report": {"template_file": "templates/backtest_report.html"},
            "portfolio_report": {"template_file": "templates/portfolio_report.html"},
            "walkforward_report": {"template_file": "templates/walkforward_report.html"}
        },
        "export": {
            "pdf": {
                "enabled": True,
                "page_size": "A4",
                "orientation": "portrait",
                "margin_mm": 15,
                "include_watermark": False
            }
        }
    }


def _build_postgresql_url(pg_config: dict) -> str:
    """
    Build PostgreSQL connection URL from configuration.
    
    Args:
        pg_config: PostgreSQL configuration dictionary with host, port, 
                   database, username, password keys
    
    Returns:
        str: PostgreSQL SQLAlchemy URL
    """
    host = pg_config.get("host", "localhost")
    port = pg_config.get("port", 5432)
    database = pg_config.get("database", "trading")
    username = pg_config.get("username", "")
    password = pg_config.get("password", "")
    
    if username and password:
        return f"postgresql://{username}:{password}@{host}:{port}/{database}"
    elif username:
        return f"postgresql://{username}@{host}:{port}/{database}"
    else:
        return f"postgresql://{host}:{port}/{database}"


def _build_sqlite_url(sqlite_config: dict) -> str:
    """
    Build SQLite connection URL from configuration.
    
    Note: This function does NOT create the database directory.
    Call ensure_database_dir() during application startup to create it.
    
    Args:
        sqlite_config: SQLite configuration dictionary with path key
    
    Returns:
        str: SQLite SQLAlchemy URL
    """
    db_path = sqlite_config.get("path", "trading_sessions.db")
    
    # Make path absolute if relative
    if not Path(db_path).is_absolute():
        db_path = PROJECT_ROOT / db_path
    
    return f"sqlite:///{Path(db_path)}"


def get_sqlite_db_path_from_url(database_url: str) -> Path | None:
    """
    Extract a SQLite database path from a SQLAlchemy database URL.

    Relative SQLite URLs are resolved against ``PROJECT_ROOT`` so startup
    directory creation matches the actual runtime database location.
    """
    if not database_url.lower().startswith("sqlite:///"):
        return None

    raw_path = unquote(database_url[len("sqlite:///"):]).split("?", 1)[0]
    if not raw_path:
        return None

    db_path = Path(raw_path)
    if not db_path.is_absolute():
        db_path = PROJECT_ROOT / db_path
    return db_path


def get_database_url_from_config() -> str:
    """
    Build database URL from configuration file.
    
    Priority:
    1. DATABASE_URL environment variable (if set)
    2. database_config.json settings
    3. Default SQLite path
    
    Returns:
        str: SQLAlchemy database URL
    """
    # Environment variable takes precedence
    env_url = os.getenv("DATABASE_URL")
    if env_url:
        return env_url
    
    config = load_database_config()
    db_config = config.get("database", {})
    db_type = db_config.get("type", "sqlite")
    
    if db_type == "postgresql":
        return _build_postgresql_url(db_config.get("postgresql", {}))
    
    # Default: SQLite
    return _build_sqlite_url(db_config.get("sqlite", {}))


# Load database URL from config (environment variable takes precedence)
DATABASE_URL = get_database_url_from_config()

AI_PROVIDER = os.getenv("AI_PROVIDER", "openai")
AI_PROVIDER_PRIORITY = os.getenv("AI_PROVIDER_PRIORITY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY")
MINIMAX_BASE_URL = os.getenv("MINIMAX_BASE_URL")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_BASE_URL = os.getenv("GEMINI_BASE_URL")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
CLAUDE_BASE_URL = os.getenv("CLAUDE_BASE_URL") or os.getenv("ANTHROPIC_BASE_URL")
# Optional outbound proxies for backend requests.
HTTP_PROXY = os.getenv("HTTP_PROXY") or os.getenv("http_proxy")
HTTPS_PROXY = os.getenv("HTTPS_PROXY") or os.getenv("https_proxy")

# Debug mode - when True, detailed error messages and stack traces are returned to clients
DEBUG = os.getenv("DEBUG", "false").lower() in {"true", "1", "yes", "on"}

# Report Center configuration
REPORT_SHARE_SECRET = os.getenv("REPORT_SHARE_SECRET", "default-secret-change-me-in-production")
REPORT_MAX_AGE_DAYS = int(os.getenv("REPORT_MAX_AGE_DAYS", "30"))

# Live Trading Configuration
LIVE_TRADING_ENABLED = os.getenv("LIVE_TRADING_ENABLED", "false").lower() in {"true", "1", "yes", "on"}
DEFAULT_EXCHANGE = os.getenv("DEFAULT_EXCHANGE", "binance")
DEFAULT_TRADE_MODE = os.getenv("DEFAULT_TRADE_MODE", "paper")

# CCXT API credentials are loaded directly by CCXTStore from environment variables
# Format: CCXT_{EXCHANGE}_{MODE}_API_KEY, CCXT_{EXCHANGE}_{MODE}_SECRET
# Example: CCXT_BINANCE_PAPER_API_KEY, CCXT_BINANCE_PAPER_SECRET


def _parse_list_env(name: str) -> list[str]:
    """
    Parse comma-separated env var into a list of non-empty strings.

    Example:
      CORS_ALLOW_ORIGINS="https://a.com, https://b.com"
    """
    raw = (os.getenv(name) or "").strip()
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


# CORS (Cross-Origin Resource Sharing)
# IMPORTANT: If you set allow_credentials=true, you must NOT use "*" as an allowed origin
# (browsers will reject it per Fetch/CORS rules).
CORS_ALLOW_ORIGINS = _parse_list_env("CORS_ALLOW_ORIGINS")
CORS_ALLOW_ORIGIN_REGEX = (os.getenv("CORS_ALLOW_ORIGIN_REGEX") or "").strip() or None
CORS_ALLOW_CREDENTIALS = (
    os.getenv("CORS_ALLOW_CREDENTIALS", "false").lower() in {"true", "1", "yes", "on"}
)


def ensure_resource_dirs() -> None:
    """Ensure resource folders exist (images, strategy, frontend, config, reports, templates)."""
    RESOURCES_DIR.mkdir(parents=True, exist_ok=True)
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    STRATEGY_DIR.mkdir(parents=True, exist_ok=True)
    FRONTEND_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)


def ensure_database_dir() -> None:
    """
    Ensure the database directory exists.
    
    This should be called during application startup (not import time)
    to avoid side effects during module imports.
    
    Raises:
        RuntimeError: If the directory cannot be created
    """
    import logging
    logger = logging.getLogger(__name__)
    
    db_path = get_sqlite_db_path_from_url(DATABASE_URL)
    if db_path is None:
        # Non-SQLite databases do not require local directory creation.
        return

    try:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Database directory ensured: {db_path.parent}")
    except (OSError, PermissionError) as e:
        raise RuntimeError(f"Cannot create database directory '{db_path.parent}': {e}") from e


__all__ = [
    "ASSETS_DIR",
    "AI_PROVIDER",
    "AI_PROVIDER_PRIORITY",
    "BASE_DIR",
    "CONFIG_DIR",
    "CORS_ALLOW_CREDENTIALS",
    "CORS_ALLOW_ORIGINS",
    "CORS_ALLOW_ORIGIN_REGEX",
    "CLAUDE_API_KEY",
    "CLAUDE_BASE_URL",
    "DATABASE_URL",
    "DEBUG",
    "DEFAULT_DB_PATH",
    "DEFAULT_DB_URL",
    "DEFAULT_STRATEGY_PATH",
    "DEFAULT_EXCHANGE",
    "DEFAULT_TRADE_MODE",
    "ENABLE_LOGIN",
    "AUTH_PROVIDER",
    "FRONTEND_DIR",
    "GEMINI_API_KEY",
    "GEMINI_BASE_URL",
    "IMAGES_DIR",
    "LIVE_TRADING_ENABLED",
    "LOGTO_AUDIENCE",
    "LOGTO_ISSUER",
    "LOGTO_JWKS_URI",
    "LOGTO_REQUIRED_SCOPES",
    "SYSTEM_AUTH_ALLOW_REGISTRATION",
    "SYSTEM_AUTH_SECRET",
    "MINIMAX_API_KEY",
    "MINIMAX_BASE_URL",
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "OPENAI_API_KEY",
    "OPENAI_BASE_URL",
    "PROJECT_ROOT",
    "REPORTS_DIR",
    "REPORT_MAX_AGE_DAYS",
    "REPORT_SHARE_SECRET",
    "RESOURCES_DIR",
    "STRATEGY_DIR",
    "TEMPLATES_DIR",
    "ensure_database_dir",
    "ensure_resource_dirs",
    "get_sqlite_db_path_from_url",
    "load_database_config",
    "load_report_config",
    "get_database_url_from_config",
]
