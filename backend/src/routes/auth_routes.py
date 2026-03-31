"""Authentication routes for built-in system login."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from src.service.auth_service import (
    AuthService,
    InvalidCredentialsError,
    RegistrationDisabledError,
    UnsupportedAuthProviderError,
    UserAlreadyExistsError,
)
from src.utils.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(tags=["auth"])


def _serialize_auth_tokens(tokens) -> dict:
    return {
        "status": "ok",
        "access_token": tokens.access_token,
        "token_type": tokens.token_type,
        "expires_in": tokens.expires_in,
        "user": tokens.user,
    }


class SystemLoginRequest(BaseModel):
    email: str = Field(..., min_length=3)
    password: str = Field(..., min_length=8)


class SystemRegisterRequest(SystemLoginRequest):
    display_name: str | None = Field(default=None, max_length=255)


@router.get("/auth/config")
def get_auth_public_config() -> dict:
    service = AuthService()
    config = service.get_auth_config()
    return {"status": "ok", "config": config}


@router.post("/auth/login")
def login_system_user(request: SystemLoginRequest) -> dict:
    service = AuthService()
    try:
        tokens = service.login_user(request.email, request.password)
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except UnsupportedAuthProviderError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return _serialize_auth_tokens(tokens)


@router.post("/auth/register")
def register_system_user(request: SystemRegisterRequest) -> dict:
    service = AuthService()
    try:
        tokens = service.register_user(
            email=request.email,
            password=request.password,
            display_name=request.display_name,
        )
    except UserAlreadyExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except RegistrationDisabledError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except (InvalidCredentialsError, UnsupportedAuthProviderError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return _serialize_auth_tokens(tokens)


@router.get("/auth/me")
def get_current_authenticated_user(user: dict = Depends(get_current_user)) -> dict:
    return {"status": "ok", "user": user}


class SystemUserCreateRequest(SystemRegisterRequest):
    is_superuser: bool = False


class SystemUserPasswordResetRequest(BaseModel):
    password: str = Field(..., min_length=8)


def _require_system_admin(user: dict = Depends(get_current_user)) -> dict:
    if user.get("auth_provider") != "system":
        raise HTTPException(status_code=403, detail="System authentication required")
    if not user.get("is_superuser"):
        raise HTTPException(status_code=403, detail="Administrator privileges required")
    return user


@router.get("/auth/system-users")
def list_system_users(_: dict = Depends(_require_system_admin)) -> dict:
    service = AuthService()
    return {"status": "ok", "users": service.list_users()}


@router.post("/auth/system-users")
def create_system_user(request: SystemUserCreateRequest, _: dict = Depends(_require_system_admin)) -> dict:
    service = AuthService()
    try:
        user = service.create_user(
            email=request.email,
            password=request.password,
            display_name=request.display_name,
            is_superuser=request.is_superuser,
        )
    except UserAlreadyExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"status": "ok", "user": user}


@router.post("/auth/system-users/{user_id}/activate")
def set_system_user_active(
    user_id: int,
    is_active: bool,
    admin_user: dict = Depends(_require_system_admin),
) -> dict:
    if admin_user.get("id") == user_id and not is_active:
        raise HTTPException(status_code=400, detail="You cannot deactivate your own account")
    service = AuthService()
    user = service.set_user_active(user_id, is_active)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {"status": "ok", "user": user}


@router.post("/auth/system-users/{user_id}/password")
def reset_system_user_password(
    user_id: int,
    request: SystemUserPasswordResetRequest,
    _: dict = Depends(_require_system_admin),
) -> dict:
    service = AuthService()
    user = service.reset_password(user_id, request.password)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {"status": "ok", "user": user}
