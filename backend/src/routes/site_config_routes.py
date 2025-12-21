"""
Site Configuration Routes

Public API endpoints for site-level configuration.
GET endpoint does not require authentication.
PUT endpoint requires authentication.
"""

import os
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from src.db.storage.settings import SettingsStorage
from src.utils.auth import get_current_user, get_optional_user

logger = logging.getLogger(__name__)

router = APIRouter(tags=["site"])

# Singleton storage instance
_settings_storage: Optional[SettingsStorage] = None


def get_settings_storage() -> SettingsStorage:
    """Get or create settings storage singleton."""
    global _settings_storage
    if _settings_storage is None:
        _settings_storage = SettingsStorage()
    return _settings_storage


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


class SiteConfigUpdate(BaseModel):
    """Request model for updating site configuration."""
    site_title: Optional[str] = None
    site_description: Optional[str] = None
    site_docs_url: Optional[str] = None
    site_github_url: Optional[str] = None
    site_twitter_url: Optional[str] = None
    site_email: Optional[str] = None
    site_stats_strategies: Optional[str] = None
    site_stats_backtests: Optional[str] = None
    site_stats_users: Optional[str] = None


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
    Configuration is read from database first, falling back to .env values.
    """
    storage = get_settings_storage()
    
    # Get site config from DB with env fallback (user_id=None for site-wide config)
    site_data = storage.get_site_config(user_id=None)
    config = site_data.get("config", {})
    
    return {
        "site": {
            "title": config.get("site_title", "Backtrader Pro"),
            "description": config.get("site_description", "Professional quantitative trading platform"),
        },
        "links": {
            "docs": config.get("site_docs_url", ""),
            "github": config.get("site_github_url", ""),
            "twitter": config.get("site_twitter_url", ""),
            "email": config.get("site_email", ""),
        },
        "stats": {
            "strategies": config.get("site_stats_strategies", "50+"),
            "backtests": config.get("site_stats_backtests", "10K+"),
            "users": config.get("site_stats_users", "1K+"),
        },
        "features": {
            "loginEnabled": get_env_bool("ENABLE_LOGIN", False),
            "liveTrading": get_env_bool("LIVE_TRADING_ENABLED", False),
        },
    }


@router.get("/site/config/admin")
def get_site_config_admin(user: dict = Depends(get_current_user)) -> dict:
    """
    Get site configuration with sources for admin editing.
    
    Returns config values and their sources (database/env/default).
    Requires authentication.
    """
    storage = get_settings_storage()
    site_data = storage.get_site_config(user_id=None)
    
    return {
        "status": "ok",
        "config": site_data.get("config", {}),
        "sources": site_data.get("sources", {})
    }


@router.put("/site/config")
def update_site_config(
    request: SiteConfigUpdate,
    user: dict = Depends(get_current_user)
) -> dict:
    """
    Update site configuration.
    
    Saves site configuration to database.
    Values saved here take precedence over .env file.
    Requires authentication.
    """
    storage = get_settings_storage()
    
    # Convert request to dict, excluding None values
    config_dict = {k: v for k, v in request.dict().items() if v is not None}
    
    if not config_dict:
        raise HTTPException(status_code=400, detail="No configuration values provided")
    
    success = storage.save_site_config(config=config_dict, user_id=None)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save site configuration")
    
    return {
        "status": "ok",
        "message": f"Updated {len(config_dict)} configuration values",
        "updated_fields": list(config_dict.keys())
    }


@router.post("/site/config/reset")
def reset_site_config(user: dict = Depends(get_current_user)) -> dict:
    """
    Reset site configuration to defaults.
    
    Removes database values, falling back to .env or defaults.
    Requires authentication.
    """
    storage = get_settings_storage()
    
    success = storage.reset_site_config(user_id=None)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to reset site configuration")
    
    return {
        "status": "ok",
        "message": "Site configuration reset to defaults"
    }

