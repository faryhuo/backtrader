"""First-run setup wizard routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from src.service.setup_wizard_service import SetupWizardService
from src.utils.auth import get_optional_user

router = APIRouter(tags=["setup"])


def _require_setup_access(user: dict | None = Depends(get_optional_user)) -> dict | None:
    service = SetupWizardService()
    state = service.get_wizard_state()
    if state["status"]["requires_login"] and state["status"]["is_ready"] and user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


class SetupSaveRequest(BaseModel):
    config: dict[str, Any]


class SetupTestRequest(BaseModel):
    type: str = Field(..., min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)


@router.get("/setup/wizard")
def get_setup_wizard(_: dict | None = Depends(_require_setup_access)) -> dict[str, Any]:
    service = SetupWizardService()
    return service.get_wizard_state()


@router.put("/setup/wizard")
def save_setup_wizard(
    request: SetupSaveRequest,
    _: dict | None = Depends(_require_setup_access),
) -> dict[str, Any]:
    service = SetupWizardService()
    try:
        return service.save(request.config)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/setup/wizard/test")
def test_setup_wizard(
    request: SetupTestRequest,
    _: dict | None = Depends(_require_setup_access),
) -> dict[str, Any]:
    service = SetupWizardService()
    try:
        return service.test_endpoint(request.type, request.payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
