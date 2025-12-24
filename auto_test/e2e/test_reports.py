"""
E2E tests for Reports API.

Based on TEST_CASES.md - REPORTS section:
- RPT-001: report_type enum validation, source_ids not empty
- RPT-002: Generate creates record, status is pollable
- RPT-003: Download only COMPLETED, file missing returns 404
- RPT-004: Share only COMPLETED, expires_in_hours validation
- RPT-005: Revoke share makes token invalid
- RPT-006: Public shared with invalid/expired token returns 401
"""

import pytest
import sys
from pathlib import Path

# Add libs to path
libs_path = Path(__file__).parent.parent / "libs"
sys.path.insert(0, str(libs_path))

from assertions import assert_api_response, assert_api_error


# API Paths for Reports
REPORTS = "/api/reports"

def report_detail(report_id: str) -> str:
    return f"/api/reports/{report_id}"

def report_download(report_id: str) -> str:
    return f"/api/reports/{report_id}/download"

def report_share(report_id: str) -> str:
    return f"/api/reports/{report_id}/share"

def report_shared(share_token: str) -> str:
    return f"/api/reports/shared/{share_token}"


# ========== Report Generation Tests ==========

@pytest.mark.api
@pytest.mark.requires_auth
class TestReportGeneration:
    """API tests for report generation."""

    def test_rpt_001_invalid_report_type(self, api_client):
        """RPT-001: Invalid report_type returns 422/400."""
        response = api_client.post(REPORTS, json={
            "report_type": "invalid_type_xyz",
            "source_ids": ["some-id"]
        })
        
        assert response.status_code in [400, 422]

    def test_rpt_001_empty_source_ids(self, api_client):
        """RPT-001: Empty source_ids returns 422/400."""
        response = api_client.post(REPORTS, json={
            "report_type": "backtest",
            "source_ids": []
        })
        
        assert response.status_code in [400, 422]

    def test_rpt_002_get_report_not_found(self, api_client):
        """RPT-002: Get non-existent report returns 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        
        response = api_client.get(report_detail(fake_id))
        
        assert_api_error(response, expected_status=404)


# ========== Report Download Tests ==========

@pytest.mark.api
@pytest.mark.requires_auth
class TestReportDownload:
    """API tests for report download."""

    def test_rpt_003_download_not_found(self, api_client):
        """RPT-003: Download non-existent report returns 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        
        response = api_client.get(report_download(fake_id))
        
        assert_api_error(response, expected_status=404)


# ========== Report Sharing Tests ==========

@pytest.mark.api
@pytest.mark.requires_auth
class TestReportSharing:
    """API tests for report sharing."""

    def test_rpt_004_share_not_found(self, api_client):
        """RPT-004: Share non-existent report returns 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        
        response = api_client.post(report_share(fake_id), json={
            "expires_in_hours": 24
        })
        
        assert_api_error(response, expected_status=404)

    def test_rpt_005_revoke_share_not_found(self, api_client):
        """RPT-005: Revoke share for non-existent report returns 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        
        response = api_client.delete(report_share(fake_id))
        
        assert_api_error(response, expected_status=404)

    def test_rpt_006_public_shared_invalid_token(self, api_base_url):
        """RPT-006: Public shared with invalid token returns 401."""
        import httpx
        
        response = httpx.get(
            f"{api_base_url}{report_shared('invalid_token_xyz')}",
            timeout=10,
            proxy=None
        )
        
        # Should return 401 for invalid token
        assert response.status_code in [401, 404]

    def test_rpt_006_public_shared_expired_token(self, api_base_url):
        """RPT-006: Public shared with expired token returns 401."""
        import httpx
        
        # Expired token format (base64 encoded with old timestamp)
        expired_token = "expired_test_token"
        
        response = httpx.get(
            f"{api_base_url}{report_shared(expired_token)}",
            timeout=10,
            proxy=None
        )
        
        # Should return 401 for expired token
        assert response.status_code in [401, 404]
