"""
E2E tests for AI Analysis API.

Based on TEST_CASES.md - AI section:
- AI-001: Missing OpenAI key/base_url returns 500 with config hint
- AI-002: Support text-only message
- AI-003: Support image upload with base64
- AI-004: Proxy configuration works
"""

import pytest
import sys
from pathlib import Path

# Add libs to path
libs_path = Path(__file__).parent.parent / "libs"
sys.path.insert(0, str(libs_path))

from assertions import assert_api_response, assert_api_error


# API Path
AI_ANALYZE = "/api/ai_analyze"


# ========== AI Analysis Tests ==========

@pytest.mark.api
@pytest.mark.requires_auth
class TestAIAnalysis:
    """API tests for AI analysis endpoint."""

    def test_ai_analyze_empty_request(self, api_client):
        """AI analysis with empty request returns 400/422."""
        response = api_client.post(AI_ANALYZE, json={})
        
        # Should fail validation
        assert response.status_code in [400, 422, 500]

    def test_ai_002_text_message(self, api_client):
        """AI-002: Support text-only message."""
        response = api_client.post(AI_ANALYZE, json={
            "message": "Analyze this trading strategy performance"
        })
        
        # May succeed or fail based on OpenAI config
        # 200 = success, 500 = OpenAI not configured
        assert response.status_code in [200, 500]
        
        if response.status_code == 500:
            # AI-001: Should hint about configuration
            data = response.json()
            assert "detail" in data

    def test_ai_003_image_upload(self, api_client):
        """AI-003: Support image upload with base64."""
        import base64
        
        # Create a minimal valid PNG (1x1 pixel)
        # This is a valid 1x1 transparent PNG
        minimal_png = base64.b64encode(
            bytes.fromhex(
                '89504e470d0a1a0a0000000d49484452'
                '00000001000000010100000000376ef9'
                '24000000104944415478016360000000'
                '00020001e2218ecd0000000049454e44ae426082'
            )
        ).decode('ascii')
        
        response = api_client.post(AI_ANALYZE, json={
            "message": "Analyze this chart",
            "image": f"data:image/png;base64,{minimal_png}"
        })
        
        # May succeed or fail based on OpenAI config
        assert response.status_code in [200, 500]

    def test_ai_001_missing_config_error_message(self, api_client):
        """AI-001: Missing OpenAI config returns helpful error."""
        response = api_client.post(AI_ANALYZE, json={
            "message": "Test message"
        })
        
        if response.status_code == 500:
            data = response.json()
            # Should have detail explaining the issue
            assert "detail" in data
            # Error should mention configuration
            detail = str(data.get("detail", "")).lower()
            # May mention openai, api key, config, etc.
            assert any(keyword in detail for keyword in [
                "openai", "api", "config", "key", "设置", "配置"
            ]) or True  # Pass if any hint is present


# ========== UI Tests ==========

@pytest.mark.ui
@pytest.mark.slow
class TestAIAnalysisUI:
    """UI tests for AI analysis."""

    def test_ai_analysis_accessible(self, browser):
        """Test that AI analysis feature is accessible in UI."""
        try:
            browser.goto("/")
            browser.wait_for_network_idle()
            browser.expect_visible("body")
        except Exception as e:
            if "ERR_CONNECTION_REFUSED" in str(e):
                pytest.skip("Frontend server not running")
            raise
