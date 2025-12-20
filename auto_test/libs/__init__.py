"""
Reusable test utilities and helpers.

This package contains shared libraries for e2e and smoke tests:
- api_client: HTTP client wrapper with authentication
- browser_helper: Playwright browser automation utilities
- data_fixtures: Test data generators and factories
- db_helper: Database utilities for test setup/teardown
- assertions: Custom assertion helpers
"""

__all__ = [
    "APIClient",
    "BrowserHelper",
    "DataFixtures",
    "DBHelper",
    "assert_api_response",
    "assert_api_error",
]
