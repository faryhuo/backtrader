import os
from pathlib import Path

from dotenv import load_dotenv

# Resolve key paths for the backend.
BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent
RESOURCES_DIR = PROJECT_ROOT / "resources"
FRONTEND_DIR = RESOURCES_DIR / "frontend"
ASSETS_DIR = FRONTEND_DIR / "assets"
IMAGES_DIR = RESOURCES_DIR / "images"
STRATEGY_DIR = RESOURCES_DIR / "strategy"
CONFIG_DIR = RESOURCES_DIR / "config"

# Load environment variables from the backend .env if present.
load_dotenv(PROJECT_ROOT / ".env", override=False)

# Authentication / platform configuration.
LOGTO_ISSUER = os.getenv("LOGTO_ISSUER")
LOGTO_JWKS_URI = os.getenv("LOGTO_JWKS_URI")
LOGTO_AUDIENCE = os.getenv("LOGTO_AUDIENCE")
ENABLE_LOGIN = os.getenv("ENABLE_LOGIN", "true").lower() not in {"false", "0", "no", "off"}
LOGTO_REQUIRED_SCOPES = [
    scope.strip()
    for scope in os.getenv("LOGTO_REQUIRED_SCOPES", "").split()
    if scope.strip()
]

# External services.
DATABASE_URL = os.getenv("DATABASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
# Optional outbound proxies for backend requests.
HTTP_PROXY = os.getenv("HTTP_PROXY") or os.getenv("http_proxy")
HTTPS_PROXY = os.getenv("HTTPS_PROXY") or os.getenv("https_proxy")

# Live Trading Configuration
LIVE_TRADING_ENABLED = os.getenv("LIVE_TRADING_ENABLED", "false").lower() in {"true", "1", "yes", "on"}
DEFAULT_EXCHANGE = os.getenv("DEFAULT_EXCHANGE", "binance")
DEFAULT_TRADE_MODE = os.getenv("DEFAULT_TRADE_MODE", "paper")

# CCXT API credentials are loaded directly by CCXTStore from environment variables
# Format: CCXT_{EXCHANGE}_{MODE}_API_KEY, CCXT_{EXCHANGE}_{MODE}_SECRET
# Example: CCXT_BINANCE_PAPER_API_KEY, CCXT_BINANCE_PAPER_SECRET


def ensure_resource_dirs() -> None:
    """Ensure resource folders exist (images, strategy, frontend, config)."""
    RESOURCES_DIR.mkdir(parents=True, exist_ok=True)
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    STRATEGY_DIR.mkdir(parents=True, exist_ok=True)
    FRONTEND_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


__all__ = [
    "ASSETS_DIR",
    "BASE_DIR",
    "CONFIG_DIR",
    "DATABASE_URL",
    "DEFAULT_EXCHANGE",
    "DEFAULT_TRADE_MODE",
    "ENABLE_LOGIN",
    "FRONTEND_DIR",
    "IMAGES_DIR",
    "LIVE_TRADING_ENABLED",
    "LOGTO_AUDIENCE",
    "LOGTO_ISSUER",
    "LOGTO_JWKS_URI",
    "LOGTO_REQUIRED_SCOPES",
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "OPENAI_API_KEY",
    "OPENAI_BASE_URL",
    "PROJECT_ROOT",
    "RESOURCES_DIR",
    "STRATEGY_DIR",
    "ensure_resource_dirs",
]
