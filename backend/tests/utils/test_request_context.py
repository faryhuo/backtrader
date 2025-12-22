"""
Tests for request_context module.

Tests the request context functionality including:
- Request ID generation and retrieval
- Trace ID setting and retrieval
- Context isolation between requests
- Middleware integration
"""

import pytest
import uuid
from unittest.mock import MagicMock, AsyncMock
from contextvars import copy_context

from src.utils.request_context import (
    get_request_id,
    get_trace_id,
    set_trace_id,
    RequestContextMiddleware,
    REQUEST_ID_HEADER,
    format_log_prefix,
    _request_id_var,
    _trace_id_var,
)


class TestRequestId:
    """Tests for request_id functionality."""
    
    def test_get_request_id_returns_none_by_default(self):
        """Request ID should be None when not set."""
        # Reset context
        _request_id_var.set(None)
        assert get_request_id() is None
    
    def test_get_request_id_returns_set_value(self):
        """Request ID should return the set value."""
        test_id = "test-request-123"
        _request_id_var.set(test_id)
        assert get_request_id() == test_id
        # Cleanup
        _request_id_var.set(None)


class TestTraceId:
    """Tests for trace_id functionality."""
    
    def test_get_trace_id_returns_none_by_default(self):
        """Trace ID should be None when not set."""
        _trace_id_var.set(None)
        assert get_trace_id() is None
    
    def test_set_and_get_trace_id(self):
        """Should be able to set and retrieve trace ID."""
        test_trace_id = "backtest-uuid-123"
        set_trace_id(test_trace_id)
        assert get_trace_id() == test_trace_id
        # Cleanup
        _trace_id_var.set(None)
    
    def test_trace_id_overwrites_previous(self):
        """Setting trace ID should overwrite previous value."""
        set_trace_id("first-trace")
        set_trace_id("second-trace")
        assert get_trace_id() == "second-trace"
        # Cleanup
        _trace_id_var.set(None)


class TestFormatLogPrefix:
    """Tests for format_log_prefix helper."""
    
    def test_empty_prefix_when_no_context(self):
        """Should return empty string when no context set."""
        _request_id_var.set(None)
        _trace_id_var.set(None)
        assert format_log_prefix() == ""
    
    def test_prefix_with_request_id_only(self):
        """Should include shortened request ID."""
        _request_id_var.set("12345678-1234-1234-1234-123456789abc")
        _trace_id_var.set(None)
        prefix = format_log_prefix()
        assert "[12345678]" in prefix
        assert "trace" not in prefix
        # Cleanup
        _request_id_var.set(None)
    
    def test_prefix_with_both_ids(self):
        """Should include both request and trace IDs."""
        _request_id_var.set("request-id-123")
        _trace_id_var.set("trace-id-456")
        prefix = format_log_prefix()
        assert "[request-" in prefix
        assert "[trace:trace-id" in prefix
        # Cleanup
        _request_id_var.set(None)
        _trace_id_var.set(None)


class TestRequestContextMiddleware:
    """Tests for RequestContextMiddleware."""
    
    @pytest.fixture
    def middleware(self):
        """Create middleware instance."""
        return RequestContextMiddleware(app=MagicMock())
    
    @pytest.fixture
    def mock_request(self):
        """Create mock request."""
        request = MagicMock()
        request.headers = {}
        request.method = "GET"
        request.url = MagicMock()
        request.url.path = "/api/test"
        return request
    
    @pytest.mark.asyncio
    async def test_middleware_generates_request_id(self, middleware, mock_request):
        """Middleware should generate request ID when not provided."""
        async def call_next(request):
            # Verify request ID is set during processing
            req_id = get_request_id()
            assert req_id is not None
            # Verify it looks like a UUID
            uuid.UUID(req_id)  # Will raise if not valid UUID
            
            response = MagicMock()
            response.headers = {}
            return response
        
        response = await middleware.dispatch(mock_request, call_next)
        
        # Response should have X-Request-ID header
        assert REQUEST_ID_HEADER in response.headers
    
    @pytest.mark.asyncio
    async def test_middleware_uses_provided_request_id(self, middleware, mock_request):
        """Middleware should use X-Request-ID from request headers."""
        custom_id = "custom-request-id-from-client"
        mock_request.headers = {REQUEST_ID_HEADER: custom_id}
        
        async def call_next(request):
            assert get_request_id() == custom_id
            response = MagicMock()
            response.headers = {}
            return response
        
        response = await middleware.dispatch(mock_request, call_next)
        assert response.headers[REQUEST_ID_HEADER] == custom_id
    
    @pytest.mark.asyncio
    async def test_middleware_resets_trace_id(self, middleware, mock_request):
        """Middleware should reset trace ID for new requests."""
        # Set trace ID before request
        set_trace_id("old-trace-id")
        
        async def call_next(request):
            # Trace ID should be reset to None
            assert get_trace_id() is None
            response = MagicMock()
            response.headers = {}
            return response
        
        await middleware.dispatch(mock_request, call_next)


class TestContextIsolation:
    """Tests for context isolation between concurrent contexts."""
    
    def test_context_isolation(self):
        """Different contexts should have isolated values."""
        results = []
        
        def task1():
            _request_id_var.set("task1-id")
            set_trace_id("task1-trace")
            results.append(("task1", get_request_id(), get_trace_id()))
        
        def task2():
            _request_id_var.set("task2-id")
            set_trace_id("task2-trace")
            results.append(("task2", get_request_id(), get_trace_id()))
        
        # Run in separate contexts
        ctx1 = copy_context()
        ctx2 = copy_context()
        
        ctx1.run(task1)
        ctx2.run(task2)
        
        # Verify each context had its own values
        assert ("task1", "task1-id", "task1-trace") in results
        assert ("task2", "task2-id", "task2-trace") in results
