"""
Authentication configuration for tests.

By default, tests use mock authentication which may not work with
backends that require real JWT tokens. 

To run tests with real authentication:
1. Configure a test user in Logto
2. Obtain a valid JWT token
3. Set TEST_AUTH_TOKEN environment variable or update this file
"""

import os

# Set to True to skip tests that require authentication
SKIP_AUTH_TESTS = os.getenv("SKIP_AUTH_TESTS", "true").lower() == "true"

# Real JWT token for testing (if available)
# You can set this via environment variable: TEST_AUTH_TOKEN
TEST_AUTH_TOKEN = os.getenv("TEST_AUTH_TOKEN", None)


def should_skip_auth_test():
    """Check if auth-required tests should be skipped."""
    return SKIP_AUTH_TESTS and TEST_AUTH_TOKEN is None


def get_auth_token():
    """Get authentication token for tests."""
    return TEST_AUTH_TOKEN
