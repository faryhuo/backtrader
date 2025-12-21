"""
Site Configuration Routes

Public API endpoints for site-level configuration.
These endpoints do not require authentication.
"""

import os
import logging
from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter(tags=["site"])


def get_env(key: str, default: str = "") -> str:
    """Get environment variable with default fallback."""
    return os.getenv(key, default)


def get_env_bool(key: str, default: bool = False) -> bool:
    """Get boolean environment variable."""
    value = os.getenv(key, "").lower()
    if value in ("true", "1", "yes", "on"):
        return True
    if value in ("false", "0", "no", "off"):
        return False
    return default


@router.get("/site/config")
def get_site_config() -> dict:
    """
    Get public site configuration.
    
    This endpoint returns configuration for the landing page including:
    - Site branding (title, description)
    - External links (docs, github, twitter)
    - Stats for display
    - Feature flags
    
    No authentication required.
    """
    return {
        "site": {
            "title": get_env("SITE_TITLE", "Backtrader Pro"),
            "description": get_env(
                "SITE_DESCRIPTION",
                "Professional quantitative trading platform"
            ),
        },
        "links": {
            "docs": get_env("SITE_DOCS_URL", ""),
            "github": get_env("SITE_GITHUB_URL", ""),
            "twitter": get_env("SITE_TWITTER_URL", ""),
            "email": get_env("SITE_EMAIL", ""),
        },
        "stats": {
            "strategies": get_env("SITE_STATS_STRATEGIES", "50+"),
            "backtests": get_env("SITE_STATS_BACKTESTS", "10K+"),
            "users": get_env("SITE_STATS_USERS", "1K+"),
        },
        "features": {
            "loginEnabled": get_env_bool("ENABLE_LOGIN", False),
            "liveTrading": get_env_bool("LIVE_TRADING_ENABLED", False),
        },
    }
