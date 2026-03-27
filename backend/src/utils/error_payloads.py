"""
Structured error payload helpers.

Provides a single error payload contract used by HTTP responses, task storage,
and long-running background workflows.
"""

from __future__ import annotations

import json
from typing import Any, Optional

from src.utils.request_context import get_request_id


ERROR_PAYLOAD_KEYS = {"detail", "error_code", "request_id", "details", "retryable"}


def build_error_payload(
    detail: str,
    *,
    error_code: str,
    request_id: Optional[str] = None,
    details: Optional[dict[str, Any]] = None,
    retryable: bool = False,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "detail": str(detail),
        "error_code": error_code,
        "retryable": bool(retryable),
    }
    effective_request_id = request_id or get_request_id()
    if effective_request_id:
        payload["request_id"] = effective_request_id
    if details:
        payload["details"] = details
    return payload


def is_error_payload(value: Any) -> bool:
    return isinstance(value, dict) and "detail" in value and "error_code" in value


def serialize_error_payload(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if is_error_payload(value):
        return json.dumps(value)
    return str(value)


def deserialize_error_payload(value: Any) -> Optional[dict[str, Any]]:
    if value is None:
        return None
    if is_error_payload(value):
        return dict(value)
    if not isinstance(value, str):
        return None

    raw = value.strip()
    if not raw.startswith("{"):
        return None

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return None

    if is_error_payload(parsed):
        return parsed
    return None


def get_error_detail(value: Any) -> Optional[str]:
    payload = deserialize_error_payload(value)
    if payload:
        return payload.get("detail")
    if value is None:
        return None
    return str(value)

