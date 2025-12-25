"""
Authentication dependencies for route handlers.

Provides FastAPI dependencies for extracting user_id from authentication context.
Use these dependencies instead of manually extracting user_id in each endpoint.
"""

from typing import Optional
from fastapi import Depends

from src.utils.auth import get_current_user, get_optional_user


def get_user_id(user: dict = Depends(get_current_user)) -> str:
    """
    Extract user ID from authenticated user context.

    This is a FastAPI dependency that requires authentication.
    Use this when the endpoint requires a valid user.

    Args:
        user: User dictionary from authentication dependency (injected by FastAPI)

    Returns:
        User ID string from the 'sub' claim

    Raises:
        HTTPException: 401 if user is not authenticated (handled by get_current_user)

    Example:
        @router.get("/protected")
        def protected_endpoint(user_id: str = Depends(get_user_id)):
            # user_id is guaranteed to be a valid string
            return {"user_id": user_id}
    """
    return user.get("sub")


def get_optional_user_id(user: Optional[dict] = Depends(get_optional_user)) -> Optional[str]:
    """
    Extract user ID from authentication context if present.

    This is a FastAPI dependency that allows optional authentication.
    Use this when the endpoint can work with or without authentication.

    Args:
        user: Optional user dictionary from authentication dependency (injected by FastAPI)

    Returns:
        User ID string from the 'sub' claim, or None if not authenticated

    Example:
        @router.get("/public")
        def public_endpoint(user_id: Optional[str] = Depends(get_optional_user_id)):
            # user_id may be None for anonymous users
            if user_id:
                # Return user-specific data
                pass
            else:
                # Return public data
                pass
    """
    return user.get("sub") if user else None


__all__ = ["get_user_id", "get_optional_user_id"]
