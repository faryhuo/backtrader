"""
Settings Routes - API endpoints for user settings management.
"""

import logging
from typing import List

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from src.db.settings_storage import SettingsStorage
from src.utils.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

# Module-level singleton
_settings_storage = None


def get_settings_storage():
    """Get or create settings storage singleton."""
    global _settings_storage
    if _settings_storage is None:
        _settings_storage = SettingsStorage()
    return _settings_storage


class UserSettingsRequest(BaseModel):
    """Request model for updating user settings."""
    selected_models: List[str] = Field(..., min_length=1, description="List of AI model names")
    code_analysis_prompt: str = Field(..., min_length=1)
    code_rewrite_prompt: str = Field(..., min_length=1)
    full_strategy_analysis_prompt: str = Field(..., min_length=1)


@router.get("/settings")
def get_user_settings(user: dict = Depends(get_current_user)) -> dict:
    """
    Get user settings.

    Returns settings from database if found, otherwise returns defaults.
    Frontend will migrate from localStorage on first save.
    """
    try:
        storage = get_settings_storage()
        user_id = user.get("sub") if user else None

        settings = storage.get_settings(user_id=user_id)

        return {
            "status": "ok",
            "settings": settings
        }

    except Exception as e:
        logger.error(f"Failed to get settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/settings")
def update_user_settings(
    request: UserSettingsRequest,
    user: dict = Depends(get_current_user)
) -> dict:
    """
    Update user settings.

    Creates new settings if none exist, updates existing settings otherwise.
    Frontend should migrate localStorage data on first save.
    """
    try:
        storage = get_settings_storage()
        user_id = user.get("sub") if user else None

        # Validate at least one model selected
        if not request.selected_models or len(request.selected_models) == 0:
            raise HTTPException(
                status_code=400,
                detail="At least one AI model must be selected"
            )

        settings = storage.save_settings(
            selected_models=request.selected_models,
            code_analysis_prompt=request.code_analysis_prompt,
            code_rewrite_prompt=request.code_rewrite_prompt,
            full_strategy_analysis_prompt=request.full_strategy_analysis_prompt,
            user_id=user_id
        )

        return {
            "status": "ok",
            "message": "Settings saved successfully",
            "settings": settings
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"Failed to update settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/settings/reset")
def reset_user_settings(user: dict = Depends(get_current_user)) -> dict:
    """
    Reset user settings to defaults.

    Deletes user settings from database and returns default values.
    """
    try:
        storage = get_settings_storage()
        user_id = user.get("sub") if user else None

        defaults = storage.reset_settings(user_id=user_id)

        return {
            "status": "ok",
            "message": "Settings reset to defaults",
            "settings": defaults
        }

    except Exception as e:
        logger.error(f"Failed to reset settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))
