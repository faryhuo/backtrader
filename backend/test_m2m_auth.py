#!/usr/bin/env python3
"""
Test script for Logto M2M authentication

This script tests the M2M token acquisition flow to verify
that the credentials are configured correctly.

Usage:
    python test_m2m_auth.py
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path to import auth module
sys.path.insert(0, os.path.dirname(__file__))

from auth import get_logto_config, obtain_m2m_token, clear_token_cache


def test_config():
    """Test that configuration is loaded correctly"""
    print("=" * 60)
    print("Testing Logto M2M Configuration")
    print("=" * 60)

    try:
        config = get_logto_config()
        print("✓ Configuration loaded successfully")
        print(f"  Endpoint: {config.endpoint}")
        print(f"  App ID: {config.app_id}")
        print(f"  App Secret: {'*' * len(config.app_secret) if config.app_secret else 'NOT SET'}")
        print(f"  API Resource: {config.resource}")
        print(f"  Token Endpoint: {config.token_endpoint}")
        print(f"  JWKS URI: {config.jwks_uri}")
        print()
        return config
    except ValueError as e:
        print(f"✗ Configuration error: {e}")
        print()
        return None


def test_token_acquisition(config):
    """Test M2M token acquisition"""
    print("=" * 60)
    print("Testing M2M Token Acquisition")
    print("=" * 60)

    try:
        # Clear any cached token
        clear_token_cache()
        print("Cleared token cache")

        # Obtain new token
        print("Requesting M2M access token...")
        token = obtain_m2m_token(config)

        print("✓ Token acquired successfully")
        print(f"  Token length: {len(token)} characters")
        print(f"  Token preview: {token[:50]}...")
        print()

        # Decode token (without verification) to inspect claims
        try:
            import json
            import base64
            from jose import jwt

            # Get unverified claims
            claims = jwt.get_unverified_claims(token)

            print("Token Claims:")
            print(f"  Issuer: {claims.get('iss', 'N/A')}")
            print(f"  Audience: {claims.get('aud', 'N/A')}")
            print(f"  Subject: {claims.get('sub', 'N/A')}")
            print(f"  Issued At: {claims.get('iat', 'N/A')}")
            print(f"  Expires At: {claims.get('exp', 'N/A')}")
            print(f"  Scope: {claims.get('scope', 'N/A')}")
            print()

        except Exception as e:
            print(f"  (Could not decode token claims: {e})")
            print()

        return True

    except Exception as e:
        print(f"✗ Token acquisition failed: {e}")
        print()
        return False


def test_token_caching(config):
    """Test that token caching works"""
    print("=" * 60)
    print("Testing Token Caching")
    print("=" * 60)

    try:
        # Clear cache
        clear_token_cache()

        # First acquisition
        print("First token acquisition...")
        token1 = obtain_m2m_token(config)

        # Second acquisition (should use cache)
        print("Second token acquisition (should be cached)...")
        token2 = obtain_m2m_token(config)

        if token1 == token2:
            print("✓ Token caching works correctly")
            print("  Same token returned from cache")
            print()
            return True
        else:
            print("✗ Token caching not working")
            print("  Different tokens returned")
            print()
            return False

    except Exception as e:
        print(f"✗ Caching test failed: {e}")
        print()
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("Logto M2M Authentication Test Suite")
    print("=" * 60 + "\n")

    # Test configuration
    config = test_config()
    if not config:
        print("❌ Configuration test failed. Please check your .env file.")
        print("\nRequired environment variables:")
        print("  - LOGTO_ENDPOINT")
        print("  - LOGTO_M2M_APP_ID")
        print("  - LOGTO_M2M_APP_SECRET")
        print("  - LOGTO_API_RESOURCE (optional)")
        return False

    # Test token acquisition
    if not test_token_acquisition(config):
        print("❌ Token acquisition test failed.")
        print("\nPossible issues:")
        print("  1. Invalid App ID or App Secret")
        print("  2. M2M app not linked to API resource in Logto Console")
        print("  3. Network connectivity issues")
        print("  4. Incorrect API resource identifier")
        return False

    # Test token caching
    if not test_token_caching(config):
        print("⚠️  Token caching test failed (non-critical)")

    # All tests passed
    print("=" * 60)
    print("✓ All Critical Tests Passed!")
    print("=" * 60)
    print("\nYour Logto M2M authentication is configured correctly.")
    print("You can now start the backend server with: python main.py")
    print()

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
