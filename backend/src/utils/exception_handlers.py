"""
Unified Exception Handlers for FastAPI.

Provides centralized exception handling with:
- Standardized error response format
- DEBUG mode for detailed errors in development
- Proper logging of stack traces without exposing to clients
"""

import logging
import traceback
from typing import Any, Optional

from src.utils.error_payloads import build_error_payload, is_error_payload
from src.utils.request_context import get_request_id

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


# ========== Error Codes ==========

class ErrorCode:
    """Standardized error codes for API responses."""
    INTERNAL_ERROR = "INTERNAL_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    BAD_REQUEST = "BAD_REQUEST"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"


# ========== Custom Exceptions ==========

class AppError(Exception):
    """
    Base application error with standardized error code.
    
    Use this for business logic errors that should return specific messages.
    """
    def __init__(
        self,
        message: str,
        error_code: str = ErrorCode.INTERNAL_ERROR,
        status_code: int = 500,
        details: Optional[dict] = None,
        retryable: bool = False,
        safe_to_expose: Optional[bool] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details
        self.retryable = retryable
        self.safe_to_expose = status_code < 500 if safe_to_expose is None else safe_to_expose


class ValidationError(AppError):
    """Validation error for request data."""
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.VALIDATION_ERROR,
            status_code=400,
            details=details
        )


class NotFoundError(AppError):
    """Resource not found error."""
    def __init__(self, message: str = "Resource not found"):
        super().__init__(
            message=message,
            error_code=ErrorCode.NOT_FOUND,
            status_code=404
        )


class ExternalServiceError(AppError):
    """Error from external service (e.g., exchange API, OpenAI)."""
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.EXTERNAL_SERVICE_ERROR,
            status_code=502,
            details=details,
            retryable=True,
            safe_to_expose=True,
        )


class DataNotFoundError(NotFoundError):
    """No data found for specified ticker/date range."""
    pass


class TickerValidationError(ValidationError):
    """Ticker symbol validation failed."""
    pass


class CredentialError(AppError):
    """Credential validation or storage failed."""
    def __init__(self, message: str):
        super().__init__(
            message=message,
            error_code=ErrorCode.BAD_REQUEST,
            status_code=400
        )


class SessionNotFoundError(NotFoundError):
    """Trading session not found."""
    pass


class SessionAlreadyStoppedError(ValidationError):
    """Trading session already stopped."""
    pass


class TaskNotFoundError(NotFoundError):
    """Task not found."""
    pass


class StrategyNotFoundError(NotFoundError):
    """Strategy not found."""
    pass


# ========== Response Builders ==========

def build_error_response(
    message: str,
    error_code: str,
    status_code: int,
    details: Optional[dict] = None,
    retryable: bool = False,
    include_trace: bool = False,
    trace: Optional[str] = None
) -> JSONResponse:
    """Build a standardized error response."""
    content = build_error_payload(
        message,
        error_code=error_code,
        details=details,
        retryable=retryable,
    )

    if include_trace and trace:
        content["trace"] = trace

    return JSONResponse(status_code=status_code, content=content)


SAFE_5XX_ERROR_CODES = {
    ErrorCode.EXTERNAL_SERVICE_ERROR,
    ErrorCode.SERVICE_UNAVAILABLE,
}


def _normalize_http_exception_payload(exc: HTTPException, fallback_error_code: str) -> tuple[dict[str, Any], bool]:
    detail = exc.detail
    if is_error_payload(detail):
        payload = dict(detail)
    elif isinstance(detail, dict):
        payload = build_error_payload(
            str(detail.get("detail") or "Request failed"),
            error_code=str(detail.get("error_code") or fallback_error_code),
            details=detail.get("details"),
            retryable=bool(detail.get("retryable", False)),
        )
    else:
        payload = build_error_payload(
            str(detail),
            error_code=fallback_error_code,
        )

    safe_to_expose = bool(
        getattr(exc, "safe_to_expose", False)
        or (isinstance(detail, dict) and detail.get("safe_to_expose"))
        or payload.get("error_code") in SAFE_5XX_ERROR_CODES
    )
    return payload, safe_to_expose


# ========== Exception Handlers ==========

def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Handle custom AppError exceptions."""
    request_id = get_request_id()
    logger.warning(
        f"[{request_id}] AppError: {exc.error_code} - {exc.message}",
        extra={"path": request.url.path, "error_code": exc.error_code, "request_id": request_id}
    )
    
    return build_error_response(
        message=exc.message,
        error_code=exc.error_code,
        status_code=exc.status_code,
        details=exc.details,
        retryable=exc.retryable,
    )


def http_exception_handler(
    request: Request,
    exc: HTTPException,
    debug: bool = False
) -> JSONResponse:
    """
    Handle HTTPException with standardized format.
    
    Maps HTTP status codes to appropriate error codes.
    """
    status_to_code = {
        400: ErrorCode.BAD_REQUEST,
        401: ErrorCode.UNAUTHORIZED,
        403: ErrorCode.FORBIDDEN,
        404: ErrorCode.NOT_FOUND,
        502: ErrorCode.EXTERNAL_SERVICE_ERROR,
        503: ErrorCode.SERVICE_UNAVAILABLE,
    }
    
    error_code = status_to_code.get(exc.status_code, ErrorCode.INTERNAL_ERROR)
    
    # For 5xx errors, log the details
    if exc.status_code >= 500:
        logger.error(
            f"HTTPException {exc.status_code}: {exc.detail}",
            extra={"path": request.url.path}
        )
    
    payload, safe_to_expose = _normalize_http_exception_payload(exc, error_code)
    expose_detail = debug or exc.status_code < 500 or safe_to_expose
    return build_error_response(
        message=str(payload.get("detail") if expose_detail else "Internal server error"),
        error_code=str(payload.get("error_code") or error_code),
        status_code=exc.status_code,
        details=payload.get("details"),
        retryable=bool(payload.get("retryable", False)),
    )


def unhandled_exception_handler(
    request: Request,
    exc: Exception,
    debug: bool = False
) -> JSONResponse:
    """
    Handle all unhandled exceptions.
    
    - Logs full stack trace to logger
    - Returns sanitized message to client (unless DEBUG mode)
    """
    # Get full traceback for logging
    tb_str = traceback.format_exception(type(exc), exc, exc.__traceback__)
    full_trace = "".join(tb_str)
    
    # Always log the full error with request context
    request_id = get_request_id()
    logger.error(
        f"[{request_id}] Unhandled exception on {request.method} {request.url.path}: {exc}",
        exc_info=True,
        extra={"path": request.url.path, "traceback": full_trace, "request_id": request_id}
    )
    
    if debug:
        # In debug mode, return detailed error info
        return build_error_response(
            message=str(exc),
            error_code=ErrorCode.INTERNAL_ERROR,
            status_code=500,
            retryable=False,
            include_trace=True,
            trace=full_trace
        )
    else:
        # In production, return generic message
        return build_error_response(
            message="Internal server error",
            error_code=ErrorCode.INTERNAL_ERROR,
            status_code=500,
            retryable=False,
        )


def create_exception_handlers(debug: bool = False) -> dict:
    """
    Create exception handler mappings for FastAPI app.
    
    Usage:
        handlers = create_exception_handlers(debug=DEBUG)
        for exc_class, handler in handlers.items():
            app.add_exception_handler(exc_class, handler)
    """
    def http_handler(request: Request, exc: HTTPException):
        return http_exception_handler(request, exc, debug=debug)
    
    def starlette_http_handler(request: Request, exc: StarletteHTTPException):
        # Convert Starlette exception to FastAPI HTTPException format
        return http_exception_handler(
            request, 
            HTTPException(status_code=exc.status_code, detail=exc.detail),
            debug=debug
        )
    
    def global_handler(request: Request, exc: Exception):
        return unhandled_exception_handler(request, exc, debug=debug)
    
    return {
        AppError: app_error_handler,
        HTTPException: http_handler,
        StarletteHTTPException: starlette_http_handler,
        Exception: global_handler,
    }


__all__ = [
    "ErrorCode",
    "AppError",
    "ValidationError",
    "NotFoundError",
    "ExternalServiceError",
    "DataNotFoundError",
    "TickerValidationError",
    "CredentialError",
    "SessionNotFoundError",
    "SessionAlreadyStoppedError",
    "TaskNotFoundError",
    "StrategyNotFoundError",
    "create_exception_handlers",
    "build_error_response",
]
