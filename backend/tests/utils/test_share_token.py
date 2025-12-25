"""
Unit tests for share token utilities.
"""
import time
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from src.utils.share_token import (
    generate_share_token,
    verify_share_token,
    parse_share_token,
    generate_random_token,
    create_share_link,
)


class TestGenerateShareToken:
    """Tests for generate_share_token function."""

    def test_generate_share_token_format(self):
        """Test that generated token has correct format."""
        report_id = "test-report-123"
        expires_at = datetime.utcnow() + timedelta(hours=24)

        token = generate_share_token(report_id, expires_at)

        # Token should have 3 parts separated by colons
        parts = token.split(":")
        assert len(parts) == 3
        assert parts[0] == report_id
        assert parts[1].isdigit()  # Timestamp
        assert len(parts[2]) == 16  # Signature (first 16 chars of HMAC)

    def test_generate_share_token_different_ids(self):
        """Test that different report IDs produce different tokens."""
        expires_at = datetime.utcnow() + timedelta(hours=24)

        token1 = generate_share_token("report-1", expires_at)
        token2 = generate_share_token("report-2", expires_at)

        assert token1 != token2

    def test_generate_share_token_different_expiry(self):
        """Test that different expiry times produce different tokens."""
        report_id = "test-report"
        expires_at_1 = datetime.utcnow() + timedelta(hours=24)
        expires_at_2 = datetime.utcnow() + timedelta(hours=48)

        token1 = generate_share_token(report_id, expires_at_1)
        token2 = generate_share_token(report_id, expires_at_2)

        assert token1 != token2


class TestVerifyShareToken:
    """Tests for verify_share_token function."""

    def test_verify_valid_token(self):
        """Test verification of a valid, non-expired token."""
        report_id = "test-report-123"
        expires_at = datetime.utcnow() + timedelta(hours=24)
        token = generate_share_token(report_id, expires_at)

        verified_id = verify_share_token(token)

        assert verified_id == report_id

    def test_verify_expired_token(self):
        """Test that expired tokens are rejected."""
        report_id = "test-report-123"
        expires_at = datetime.utcnow() - timedelta(hours=1)  # 1 hour ago
        token = generate_share_token(report_id, expires_at)

        verified_id = verify_share_token(token)

        assert verified_id is None

    def test_verify_tampered_signature(self):
        """Test that tokens with tampered signatures are rejected."""
        report_id = "test-report-123"
        expires_at = datetime.utcnow() + timedelta(hours=24)
        token = generate_share_token(report_id, expires_at)

        # Tamper with the signature
        parts = token.split(":")
        tampered_token = f"{parts[0]}:{parts[1]}:invalid_signature"

        verified_id = verify_share_token(tampered_token)

        assert verified_id is None

    def test_verify_tampered_report_id(self):
        """Test that tokens with tampered report IDs are rejected."""
        report_id = "test-report-123"
        expires_at = datetime.utcnow() + timedelta(hours=24)
        token = generate_share_token(report_id, expires_at)

        # Tamper with the report ID
        parts = token.split(":")
        tampered_token = f"different-id:{parts[1]}:{parts[2]}"

        verified_id = verify_share_token(tampered_token)

        assert verified_id is None

    def test_verify_invalid_format(self):
        """Test that malformed tokens are rejected."""
        invalid_tokens = [
            "invalid",
            "too:few",
            "too:many:parts:here",
            "",
            ":::",
        ]

        for token in invalid_tokens:
            verified_id = verify_share_token(token)
            assert verified_id is None

    def test_verify_invalid_timestamp(self):
        """Test that tokens with invalid timestamp are rejected."""
        token = "test-report:not_a_number:signature"

        verified_id = verify_share_token(token)

        assert verified_id is None

    def test_verify_token_exception_handling(self):
        """Test that exceptions during verification are handled gracefully."""
        # Token that will cause an exception during processing
        token = None

        with patch("src.utils.share_token.hmac.compare_digest", side_effect=Exception("Test error")):
            verified_id = verify_share_token("valid:123:sig")
            assert verified_id is None


class TestParseShareToken:
    """Tests for parse_share_token function."""

    def test_parse_valid_token(self):
        """Test parsing a valid token."""
        report_id = "test-report-123"
        expires_at = datetime.utcnow() + timedelta(hours=24)
        token = generate_share_token(report_id, expires_at)

        result = parse_share_token(token)

        assert result is not None
        parsed_id, parsed_expiry = result
        assert parsed_id == report_id
        # Allow 1 second tolerance for timestamp conversion
        assert abs((parsed_expiry - expires_at).total_seconds()) < 1

    def test_parse_invalid_format(self):
        """Test that malformed tokens return None."""
        invalid_tokens = [
            "invalid",
            "too:few",
            "",
        ]

        for token in invalid_tokens:
            result = parse_share_token(token)
            assert result is None

    def test_parse_invalid_timestamp(self):
        """Test that tokens with invalid timestamp return None."""
        token = "test-report:not_a_number:signature"

        result = parse_share_token(token)

        assert result is None

    def test_parse_does_not_verify_signature(self):
        """Test that parsing doesn't validate signature (by design)."""
        # Create token with tampered signature
        report_id = "test-report"
        expires_at = datetime.utcnow() + timedelta(hours=24)
        expiry_ts = int(expires_at.timestamp())
        tampered_token = f"{report_id}:{expiry_ts}:fake_signature"

        # Parse should still work (doesn't validate signature)
        result = parse_share_token(tampered_token)

        assert result is not None
        parsed_id, parsed_expiry = result
        assert parsed_id == report_id


class TestGenerateRandomToken:
    """Tests for generate_random_token function."""

    def test_generate_random_token_length(self):
        """Test that generated tokens have correct length."""
        token = generate_random_token(32)

        assert len(token) == 32
        assert all(c in "0123456789abcdef" for c in token)

    def test_generate_random_token_different_lengths(self):
        """Test generating tokens of different lengths."""
        for length in [16, 32, 64]:
            token = generate_random_token(length)
            assert len(token) == length

    def test_generate_random_token_uniqueness(self):
        """Test that consecutive tokens are different."""
        token1 = generate_random_token(32)
        token2 = generate_random_token(32)

        assert token1 != token2


class TestCreateShareLink:
    """Tests for create_share_link function."""

    def test_create_share_link_format(self):
        """Test that share link has correct format."""
        base_url = "https://example.com"
        report_id = "test-report-123"
        expires_in_hours = 24

        share_url, expires_at = create_share_link(base_url, report_id, expires_in_hours)

        assert share_url.startswith(f"{base_url}/report/shared/")
        assert report_id in share_url

        # Verify expiry time
        expected_expiry = datetime.utcnow() + timedelta(hours=expires_in_hours)
        # Allow 5 second tolerance
        assert abs((expires_at - expected_expiry).total_seconds()) < 5

    def test_create_share_link_with_trailing_slash(self):
        """Test that trailing slash in base_url is handled correctly."""
        base_url = "https://example.com/"
        report_id = "test-report-123"

        share_url, _ = create_share_link(base_url, report_id)

        # Should not have double slashes
        assert "//" not in share_url.replace("https://", "")

    def test_create_share_link_default_expiry(self):
        """Test that default expiry is 7 days (168 hours)."""
        base_url = "https://example.com"
        report_id = "test-report-123"

        share_url, expires_at = create_share_link(base_url, report_id)

        expected_expiry = datetime.utcnow() + timedelta(hours=168)
        assert abs((expires_at - expected_expiry).total_seconds()) < 5

    def test_create_share_link_custom_expiry(self):
        """Test creating link with custom expiry time."""
        base_url = "https://example.com"
        report_id = "test-report-123"
        expires_in_hours = 1

        share_url, expires_at = create_share_link(base_url, report_id, expires_in_hours)

        expected_expiry = datetime.utcnow() + timedelta(hours=1)
        assert abs((expires_at - expected_expiry).total_seconds()) < 5

    def test_create_share_link_token_is_verifiable(self):
        """Test that the token in the share link can be verified."""
        base_url = "https://example.com"
        report_id = "test-report-123"

        share_url, _ = create_share_link(base_url, report_id)

        # Extract token from URL
        token = share_url.split("/report/shared/")[1]

        # Verify token
        verified_id = verify_share_token(token)

        assert verified_id == report_id


class TestIntegrationScenarios:
    """Integration tests for complete workflows."""

    def test_generate_and_verify_workflow(self):
        """Test complete workflow of generating and verifying a token."""
        report_id = "test-report-456"
        expires_at = datetime.utcnow() + timedelta(hours=24)

        # Generate token
        token = generate_share_token(report_id, expires_at)

        # Verify token
        verified_id = verify_share_token(token)

        assert verified_id == report_id

    def test_create_link_and_verify_workflow(self):
        """Test complete workflow of creating a link and verifying its token."""
        base_url = "https://trading.example.com"
        report_id = "backtest-789"

        # Create share link
        share_url, expires_at = create_share_link(base_url, report_id, expires_in_hours=48)

        # Extract and verify token
        token = share_url.split("/report/shared/")[1]
        verified_id = verify_share_token(token)

        assert verified_id == report_id

    def test_expired_token_workflow(self):
        """Test that expired tokens are properly rejected."""
        report_id = "test-report"
        expires_at = datetime.utcnow() - timedelta(seconds=1)  # Expired 1 second ago

        # Generate expired token
        token = generate_share_token(report_id, expires_at)

        # Wait to ensure expiry
        time.sleep(1)

        # Verify token should fail
        verified_id = verify_share_token(token)

        assert verified_id is None
