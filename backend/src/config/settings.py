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


def ensure_resource_dirs() -> None:
    """Ensure resource folders exist (images, strategy, frontend)."""
    RESOURCES_DIR.mkdir(parents=True, exist_ok=True)
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    STRATEGY_DIR.mkdir(parents=True, exist_ok=True)
    FRONTEND_DIR.mkdir(parents=True, exist_ok=True)


__all__ = [
    "ASSETS_DIR",
    "BASE_DIR",
    "DATABASE_URL",
    "ENABLE_LOGIN",
    "FRONTEND_DIR",
    "IMAGES_DIR",
    "LOGTO_AUDIENCE",
    "LOGTO_ISSUER",
    "LOGTO_JWKS_URI",
    "LOGTO_REQUIRED_SCOPES",
    "OPENAI_API_KEY",
    "OPENAI_BASE_URL",
    "PROJECT_ROOT",
    "RESOURCES_DIR",
    "STRATEGY_DIR",
    "ensure_resource_dirs",
]
