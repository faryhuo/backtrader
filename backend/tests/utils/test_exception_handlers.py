"""
Tests for exception_handlers module.
"""

import pytest
from unittest.mock import MagicMock
from fastapi import Request, HTTPException
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.utils.exception_handlers import (
    ErrorCode,
    AppError,
    ValidationError,
    NotFoundError,
    ExternalServiceError,
    build_error_response,
    app_error_handler,
    http_exception_handler,
    unhandled_exception_handler,
    create_exception_handlers,
)


def _create_mock_request(path: str = "/test", method: str = "GET") -> MagicMock:
    """Create a mock request for testing."""
    request = MagicMock(spec=Request)
    request.url = MagicMock()
    request.url.path = path
    request.method = method
    return request


class TestErrorCode:
    """Tests for ErrorCode constants."""
    
    def test_error_codes_exist(self):
        assert ErrorCode.INTERNAL_ERROR == "INTERNAL_ERROR"
        assert ErrorCode.VALIDATION_ERROR == "VALIDATION_ERROR"
        assert ErrorCode.NOT_FOUND == "NOT_FOUND"
        assert ErrorCode.BAD_REQUEST == "BAD_REQUEST"
        assert ErrorCode.EXTERNAL_SERVICE_ERROR == "EXTERNAL_SERVICE_ERROR"


class TestAppError:
    """Tests for AppError and subclasses."""
    
    def test_app_error_default_values(self):
        err = AppError("Test error")
        assert err.message == "Test error"
        assert err.error_code == ErrorCode.INTERNAL_ERROR
        assert err.status_code == 500
        assert err.details is None
    
    def test_app_error_custom_values(self):
        err = AppError(
            message="Custom error",
            error_code=ErrorCode.BAD_REQUEST,
            status_code=400,
            details={"field": "name"}
        )
        assert err.message == "Custom error"
        assert err.error_code == ErrorCode.BAD_REQUEST
        assert err.status_code == 400
        assert err.details == {"field": "name"}
    
    def test_validation_error(self):
        err = ValidationError("Invalid input", details={"field": "email"})
        assert err.status_code == 400
        assert err.error_code == ErrorCode.VALIDATION_ERROR
    
    def test_not_found_error(self):
        err = NotFoundError("User not found")
        assert err.status_code == 404
        assert err.error_code == ErrorCode.NOT_FOUND
    
    def test_external_service_error(self):
        err = ExternalServiceError("API timeout")
        assert err.status_code == 502
        assert err.error_code == ErrorCode.EXTERNAL_SERVICE_ERROR


class TestBuildErrorResponse:
    """Tests for build_error_response function."""
    
    def test_basic_response(self):
        response = build_error_response(
            message="Something went wrong",
            error_code=ErrorCode.INTERNAL_ERROR,
            status_code=500
        )
        assert response.status_code == 500
        # Check body content
        import json
        body = json.loads(response.body)
        assert body["detail"] == "Something went wrong"
        assert body["error_code"] == "INTERNAL_ERROR"
    
    def test_response_with_details(self):
        response = build_error_response(
            message="Validation failed",
            error_code=ErrorCode.VALIDATION_ERROR,
            status_code=400,
            details={"field": "email"}
        )
        import json
        body = json.loads(response.body)
        assert body["details"] == {"field": "email"}
    
    def test_response_with_trace_in_debug(self):
        response = build_error_response(
            message="Error",
            error_code=ErrorCode.INTERNAL_ERROR,
            status_code=500,
            include_trace=True,
            trace="Traceback..."
        )
        import json
        body = json.loads(response.body)
        assert body["trace"] == "Traceback..."


class TestExceptionHandlers:
    """Tests for exception handler functions."""
    
    def test_app_error_handler(self):
        request = _create_mock_request()
        exc = AppError("Test error", error_code=ErrorCode.BAD_REQUEST, status_code=400)
        
        response = app_error_handler(request, exc)
        assert response.status_code == 400
    
    def test_http_exception_handler_non_debug(self):
        request = _create_mock_request()
        exc = HTTPException(status_code=500, detail="Secret implementation detail")
        
        response = http_exception_handler(request, exc, debug=False)
        assert response.status_code == 500
        
        import json
        body = json.loads(response.body)
        # In production mode, should not expose raw exception detail for 5xx
        assert body["detail"] == "Internal server error"
    
    def test_http_exception_handler_debug(self):
        request = _create_mock_request()
        exc = HTTPException(status_code=500, detail="Secret implementation detail")
        
        response = http_exception_handler(request, exc, debug=True)
        
        import json
        body = json.loads(response.body)
        # In debug mode, should expose detail
        assert body["detail"] == "Secret implementation detail"
    
    def test_http_exception_4xx_always_shows_detail(self):
        request = _create_mock_request()
        exc = HTTPException(status_code=404, detail="Resource not found")
        
        response = http_exception_handler(request, exc, debug=False)
        
        import json
        body = json.loads(response.body)
        # 4xx errors always show detail even in production
        assert body["detail"] == "Resource not found"
    
    def test_unhandled_exception_handler_non_debug(self):
        request = _create_mock_request()
        exc = ValueError("Some internal error with stack trace")
        
        response = unhandled_exception_handler(request, exc, debug=False)
        assert response.status_code == 500
        
        import json
        body = json.loads(response.body)
        # In production, should return generic message
        assert body["detail"] == "Internal server error"
        assert "trace" not in body
    
    def test_unhandled_exception_handler_debug(self):
        request = _create_mock_request()
        exc = ValueError("Some internal error with stack trace")
        
        response = unhandled_exception_handler(request, exc, debug=True)
        
        import json
        body = json.loads(response.body)
        # In debug mode, should expose error and trace
        assert "internal error" in body["detail"]
        assert "trace" in body


class TestCreateExceptionHandlers:
    """Tests for create_exception_handlers factory."""
    
    def test_creates_all_handlers(self):
        handlers = create_exception_handlers(debug=False)
        
        assert AppError in handlers
        assert HTTPException in handlers
        assert StarletteHTTPException in handlers
        assert Exception in handlers
    
    def test_handlers_are_callable(self):
        handlers = create_exception_handlers(debug=False)
        
        for exc_class, handler in handlers.items():
            assert callable(handler)
