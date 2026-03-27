"""
Unit tests for AI routes.
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import UploadFile

from src.routes.ai_routes import analyze_chart


class TestAnalyzeChart:
    """Tests for analyze_chart endpoint."""

    @pytest.fixture
    def mock_call_ai(self):
        """Mock call_ai from ai_service."""
        with patch("src.routes.ai_routes.call_ai") as mock:
            mock.return_value = {"analysis": "This is a test analysis"}
            yield mock

    @pytest.mark.asyncio
    async def test_analyze_chart_text_only(self, mock_call_ai):
        """Test analyzing chart with text message only."""
        result = await analyze_chart(
            message="Analyze this strategy",
            model="gpt-4o",
            file=None,
            user_id="test-user"
        )

        assert result == {"analysis": "This is a test analysis"}

        mock_call_ai.assert_called_once()
        call_kwargs = mock_call_ai.call_args.kwargs
        assert call_kwargs["message"] == "Analyze this strategy"
        assert call_kwargs["model"] == "gpt-4o"
        assert call_kwargs["user_id"] == "test-user"
        assert call_kwargs["image_bytes"] is None

    @pytest.mark.asyncio
    async def test_analyze_chart_with_image(self, mock_call_ai):
        """Test analyzing chart with image attachment."""
        mock_file = AsyncMock(spec=UploadFile)
        mock_file.read = AsyncMock(return_value=b"fake_image_data")

        result = await analyze_chart(
            message="What do you see in this chart?",
            model="gpt-4o",
            file=mock_file,
            user_id="test-user"
        )

        assert result == {"analysis": "This is a test analysis"}

        call_kwargs = mock_call_ai.call_args.kwargs
        assert call_kwargs["image_bytes"] == b"fake_image_data"
        await mock_file.read.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_analyze_chart_exception_propagation(self, mock_call_ai):
        """Test that exceptions from call_ai are raised as HTTPException 500."""

        mock_call_ai.side_effect = RuntimeError("All AI providers failed")

        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await analyze_chart(
                message="Test message",
                model="gpt-4o",
                file=None,
                user_id="test-user"
            )

        assert exc_info.value.status_code == 500
        assert "All AI providers failed" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_analyze_chart_no_user(self, mock_call_ai):
        """Test analyzing chart without authenticated user."""
        result = await analyze_chart(
            message="Test analysis",
            model="gpt-4o",
            file=None,
            user_id=None
        )

        assert result == {"analysis": "This is a test analysis"}

        call_kwargs = mock_call_ai.call_args.kwargs
        assert call_kwargs["user_id"] is None

    @pytest.mark.asyncio
    async def test_analyze_chart_no_model(self, mock_call_ai):
        """Test analyzing chart without explicit model (uses provider default)."""
        result = await analyze_chart(
            message="Test analysis",
            model=None,
            file=None,
            user_id="test-user"
        )

        assert result == {"analysis": "This is a test analysis"}

        call_kwargs = mock_call_ai.call_args.kwargs
        assert call_kwargs["model"] is None

    @pytest.mark.asyncio
    async def test_analyze_chart_call_ai_returns_full_response(self, mock_call_ai):
        """Test that full call_ai response (with provider/model fields) is returned."""
        mock_call_ai.return_value = {
            "analysis": "Deep analysis",
            "provider": "openai",
            "model": "gpt-4o",
            "provider_priority": ["openai", "claude"],
        }

        result = await analyze_chart(
            message="Analyze",
            model=None,
            file=None,
            user_id="user-1"
        )

        assert result == {
            "analysis": "Deep analysis",
            "provider": "openai",
            "model": "gpt-4o",
            "provider_priority": ["openai", "claude"],
        }
