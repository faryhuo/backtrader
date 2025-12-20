"""
Authentication configuration for tests.

Auto-detects if backend requires authentication by making a test request.
If backend auth is disabled, all tests run without needing tokens.
"""

import os
import httpx

# Set to True to skip tests that require authentication
SKIP_AUTH_TESTS = os.getenv("SKIP_AUTH_TESTS", "true").lower() == "true"

# Real JWT token for testing (if available)
# You can set this via environment variable: TEST_AUTH_TOKEN
TEST_AUTH_TOKEN = os.getenv("TEST_AUTH_TOKEN", None)

# Cache for auth requirement detection
_auth_required = None


def is_auth_required():
    """
    Check if backend requires authentication.
    
    Makes a test request to backend. If it returns 200/401/403, auth is required.
    If it returns 503 (service unavailable), auth middleware is active.
    If auth is disabled, endpoints return 200 without token.
    
    Returns:
        bool: True if authentication is required, False otherwise
    """
    global _auth_required
    
    # Return cached result
    if _auth_required is not None:
        return _auth_required
    
    # If token is provided, assume auth is required and enabled
    if TEST_AUTH_TOKEN:
        _auth_required = True
        return True
    
    # Test if backend requires auth by making a request without token
    try:
        api_url = os.getenv("API_BASE_URL", "http://localhost:8000")
        
        # Make request WITHOUT any authorization header
        response = httpx.get(
            f"{api_url}/api/strategies",
            timeout=5,
            headers={}  # Explicitly no auth header
        )
        
        # If we get 200, auth is disabled - tests can run freely!
        if response.status_code == 200:
            _auth_required = False
            return False
        
        # 401/403 = auth required but not provided
        # 503 = service unavailable (auth middleware rejecting)
        # Either way, auth is required
        if response.status_code in [401, 403, 503]:
            _auth_required = True
            return True
        
        # Unknown status, assume auth required to be safe
        _auth_required = True
        return True
        
    except Exception as e:
        # Can't reach backend, assume auth required
        print(f"Warning: Cannot detect auth requirement: {e}")
        _auth_required = True
        return True


def should_skip_auth_test():
    """
    Check if auth-required tests should be skipped.
    
    Tests are skipped only if:
    1. SKIP_AUTH_TESTS is true, AND
    2. No TEST_AUTH_TOKEN is provided, AND  
    3. Backend actually requires authentication
    
    If backend auth is disabled, tests run regardless of token.
    """
    # If token provided, never skip
    if TEST_AUTH_TOKEN:
        return False
    
    # If backend doesn't require auth, don't skip!
    if not is_auth_required():
        return False
    
    # Backend requires auth but no token provided
    return SKIP_AUTH_TESTS


def get_auth_token():
    """Get authentication token for tests."""
    return TEST_AUTH_TOKEN
