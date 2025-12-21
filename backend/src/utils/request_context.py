"""
Request Context Module for Observability.

Provides request-scoped context using Python's contextvars for:
- request_id: Unique identifier for each HTTP request
- trace_id: Business operation trace ID (backtest/live/optimization)

Usage:
    # Get current request ID
    from src.utils.request_context import get_request_id
    request_id = get_request_id()
    
    # Set trace ID for business operation
    from src.utils.request_context import set_trace_id
    set_trace_id(backtest_id)
"""

import uuid
import logging
from contextvars import ContextVar
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

# Context variables for request-scoped data
_request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
_trace_id_var: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)

# Header name for external request ID
REQUEST_ID_HEADER = "X-Request-ID"


def get_request_id() -> Optional[str]:
    """Get the current request ID from context."""
    return _request_id_var.get()


def get_trace_id() -> Optional[str]:
    """Get the current trace ID from context."""
    return _trace_id_var.get()


def set_trace_id(trace_id: str) -> None:
    """
    Set the trace ID for the current context.
    
    Use this to associate a business operation ID (backtest_id, optimization_id,
    session_id) with the current request for tracing purposes.
    """
    _trace_id_var.set(trace_id)


def _generate_request_id() -> str:
    """Generate a new unique request ID."""
    return str(uuid.uuid4())


class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware to set up request context for each HTTP request.
    
    - Extracts X-Request-ID from headers or generates a new one
    - Sets the request_id in context for logging and error responses
    - Adds X-Request-ID to response headers
    """
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Get request ID from header or generate new one
        request_id = request.headers.get(REQUEST_ID_HEADER)
        if not request_id:
            request_id = _generate_request_id()
        
        # Set context variables
        _request_id_var.set(request_id)
        _trace_id_var.set(None)  # Reset trace ID for new request
        
        # Log request start
        logger.debug(
            f"[{request_id}] {request.method} {request.url.path}",
            extra={"request_id": request_id}
        )
        
        # Process request
        response = await call_next(request)
        
        # Add request ID to response headers
        response.headers[REQUEST_ID_HEADER] = request_id
        
        return response


def format_log_prefix() -> str:
    """
    Format a log prefix with request and trace context.
    
    Returns a string like "[req-abc123] [trace-xyz789]" or "[req-abc123]"
    for use in log messages.
    """
    request_id = get_request_id()
    trace_id = get_trace_id()
    
    parts = []
    if request_id:
        parts.append(f"[{request_id[:8]}]")  # Shortened for readability
    if trace_id:
        parts.append(f"[trace:{trace_id[:8]}]")
    
    return " ".join(parts) if parts else ""


__all__ = [
    "get_request_id",
    "get_trace_id",
    "set_trace_id",
    "RequestContextMiddleware",
    "REQUEST_ID_HEADER",
    "format_log_prefix",
]
