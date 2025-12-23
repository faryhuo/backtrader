"""
Unit tests for AI routes.
"""
import base64
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from fastapi import UploadFile
from httpx import AsyncClient

from src.routes.ai_routes import analyze_chart, encode_image


class TestEncodeImage:
    """Tests for encode_image helper function."""

    def test_encode_image(self):
        """Test that image is correctly base64 encoded."""
        test_data = b"fake_image_data"
        result = encode_image(test_data)
        expected = base64.b64encode(test_data).decode("utf-8")
        assert result == expected

    def test_encode_image_empty(self):
        """Test encoding empty image data."""
        result = encode_image(b"")
        assert result == ""


class TestAnalyzeChart:
    """Tests for analyze_chart endpoint."""

    @pytest.fixture
    def mock_config_manager(self):
        """Mock ConfigManager for testing."""
        with patch("src.routes.ai_routes.ConfigManager") as mock:
            instance = mock.return_value
            instance.get_openai_config.return_value = {
                "api_key": "test-api-key",
                "base_url": "https://api.openai.com/v1"
            }
            instance.get_proxy_config.return_value = {}
            yield mock

    @pytest.fixture
    def mock_openai(self):
        """Mock AsyncOpenAI client."""
        with patch("src.routes.ai_routes.AsyncOpenAI") as mock:
            # Create mock response
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "This is a test analysis"

            # Mock client methods
            client_instance = mock.return_value
            client_instance.chat.completions.create = AsyncMock(return_value=mock_response)

            yield mock

    @pytest.mark.asyncio
    async def test_analyze_chart_text_only(self, mock_config_manager, mock_openai):
        """Test analyzing chart with text message only."""
        user = {"sub": "test-user"}

        result = await analyze_chart(
            message="Analyze this strategy",
            model="gpt-4o",
            file=None,
            user=user
        )

        assert result == {"analysis": "This is a test analysis"}

        # Verify OpenAI client was called correctly
        mock_openai.return_value.chat.completions.create.assert_called_once()
        call_args = mock_openai.return_value.chat.completions.create.call_args
        assert call_args.kwargs["model"] == "gpt-4o"

        messages = call_args.kwargs["messages"]
        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        assert len(messages[0]["content"]) == 1
        assert messages[0]["content"][0]["type"] == "text"
        assert messages[0]["content"][0]["text"] == "Analyze this strategy"

    @pytest.mark.asyncio
    async def test_analyze_chart_with_image(self, mock_config_manager, mock_openai):
        """Test analyzing chart with image attachment."""
        user = {"sub": "test-user"}

        # Create mock upload file
        mock_file = AsyncMock(spec=UploadFile)
        mock_file.read = AsyncMock(return_value=b"fake_image_data")

        result = await analyze_chart(
            message="What do you see in this chart?",
            model="gpt-4o",
            file=mock_file,
            user=user
        )

        assert result == {"analysis": "This is a test analysis"}

        # Verify image was included in the request
        call_args = mock_openai.return_value.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]
        content = messages[0]["content"]

        assert len(content) == 2
        assert content[0]["type"] == "text"
        assert content[1]["type"] == "image_url"
        assert "data:image/png;base64," in content[1]["image_url"]["url"]

    @pytest.mark.asyncio
    async def test_analyze_chart_with_proxy(self, mock_config_manager, mock_openai):
        """Test analyzing chart with proxy configuration."""
        user = {"sub": "test-user"}

        # Configure proxy
        mock_config_manager.return_value.get_proxy_config.return_value = {
            "https_proxy": "http://proxy.example.com:8080"
        }

        with patch("src.routes.ai_routes.httpx.AsyncClient") as mock_httpx:
            mock_http_client = AsyncMock()
            mock_httpx.return_value.__aenter__ = AsyncMock(return_value=mock_http_client)
            mock_httpx.return_value.__aexit__ = AsyncMock()

            # Create new mock for OpenAI with http_client parameter
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Proxy test analysis"

            mock_openai.return_value.chat.completions.create = AsyncMock(
                return_value=mock_response
            )

            result = await analyze_chart(
                message="Test message",
                model="gpt-4o",
                file=None,
                user=user
            )

            assert result == {"analysis": "Proxy test analysis"}

            # Verify httpx client was created with proxy
            mock_httpx.assert_called_once()
            assert mock_httpx.call_args.kwargs["proxy"] == "http://proxy.example.com:8080"

    @pytest.mark.asyncio
    async def test_analyze_chart_missing_credentials(self, mock_config_manager):
        """Test error handling when OpenAI credentials are missing."""
        user = {"sub": "test-user"}

        # Configure missing credentials
        mock_config_manager.return_value.get_openai_config.return_value = {
            "api_key": None,
            "base_url": None
        }

        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await analyze_chart(
                message="Test message",
                model="gpt-4o",
                file=None,
                user=user
            )

        assert exc_info.value.status_code == 500
        assert "OpenAI API credentials not configured" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_analyze_chart_exception_handling(self, mock_config_manager, mock_openai):
        """Test error handling when OpenAI API fails."""
        user = {"sub": "test-user"}

        # Configure OpenAI to raise an exception
        mock_openai.return_value.chat.completions.create.side_effect = Exception(
            "API connection failed"
        )

        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await analyze_chart(
                message="Test message",
                model="gpt-4o",
                file=None,
                user=user
            )

        assert exc_info.value.status_code == 500
        assert "API connection failed" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_analyze_chart_no_user(self, mock_config_manager, mock_openai):
        """Test analyzing chart without authenticated user."""
        result = await analyze_chart(
            message="Test analysis",
            model="gpt-4o",
            file=None,
            user=None
        )

        assert result == {"analysis": "This is a test analysis"}

        # Verify ConfigManager was called without user_id
        mock_config_manager.assert_called_once_with(user_id=None)
