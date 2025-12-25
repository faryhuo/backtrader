"""
API Client for E2E Testing

Provides a reusable HTTP client wrapper with:
- Base URL configuration
- Authentication token management
- JSON request/response handling
- Retry logic for transient failures
"""

import os
import time
from typing import Any, Dict, Optional
import httpx

# Force disable proxy for localhost - Windows may use system proxy settings
os.environ.setdefault('NO_PROXY', 'localhost,127.0.0.1')


class APIClient:
    """HTTP client wrapper for testing backend API."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        token: Optional[str] = None,
        timeout: int = 30,
    ):
        """
        Initialize API client.

        Args:
            base_url: Base URL for API (defaults to env var API_BASE_URL or http://localhost:8000)
            token: JWT authentication token
            timeout: Request timeout in seconds
        """
        self.base_url = base_url or os.getenv("API_BASE_URL", "http://localhost:8000")
        self.token = token
        self.timeout = timeout
        # Disable proxy completely - trust_env=False ignores HTTP_PROXY/HTTPS_PROXY
        self.client = httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
            trust_env=False,  # Don't read proxy settings from environment
        )

    def set_token(self, token: str):
        """Set authentication token for subsequent requests."""
        self.token = token

    def _get_headers(self, extra_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Build request headers with authentication."""
        headers = {"Content-Type": "application/json"}
        
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        
        if extra_headers:
            headers.update(extra_headers)
        
        return headers

    def get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        retries: int = 0,
    ) -> httpx.Response:
        """
        Send GET request.

        Args:
            path: API path (e.g., '/api/strategies')
            params: Query parameters
            headers: Additional headers
            retries: Number of retries on failure

        Returns:
            httpx.Response object
        """
        return self._request("GET", path, params=params, headers=headers, retries=retries)

    def post(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        retries: int = 0,
    ) -> httpx.Response:
        """
        Send POST request.

        Args:
            path: API path
            json: JSON request body
            params: Query parameters
            headers: Additional headers
            retries: Number of retries on failure

        Returns:
            httpx.Response object
        """
        return self._request("POST", path, json=json, params=params, headers=headers, retries=retries)

    def delete(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        retries: int = 0,
    ) -> httpx.Response:
        """
        Send DELETE request.

        Args:
            path: API path
            params: Query parameters
            headers: Additional headers
            retries: Number of retries on failure

        Returns:
            httpx.Response object
        """
        return self._request("DELETE", path, params=params, headers=headers, retries=retries)

    def put(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        retries: int = 0,
    ) -> httpx.Response:
        """
        Send PUT request.

        Args:
            path: API path
            json: JSON request body
            params: Query parameters
            headers: Additional headers
            retries: Number of retries on failure

        Returns:
            httpx.Response object
        """
        return self._request("PUT", path, json=json, params=params, headers=headers, retries=retries)

    def _request(
        self,
        method: str,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        retries: int = 0,
    ) -> httpx.Response:
        """
        Internal method to send HTTP request with retry logic.

        Args:
            method: HTTP method
            path: API path
            json: JSON request body
            params: Query parameters
            headers: Additional headers
            retries: Number of retries on failure

        Returns:
            httpx.Response object
        """
        request_headers = self._get_headers(headers)
        
        for attempt in range(retries + 1):
            try:
                response = self.client.request(
                    method=method,
                    url=path,
                    json=json,
                    params=params,
                    headers=request_headers,
                )
                
                # Don't retry on success or client errors
                if response.status_code < 500:
                    return response
                
                # Retry on server errors
                if attempt < retries:
                    time.sleep(0.5 * (attempt + 1))  # Exponential backoff
                    continue
                
                return response
                
            except httpx.RequestError as e:
                if attempt < retries:
                    time.sleep(0.5 * (attempt + 1))
                    continue
                raise
        
        return response

    def wait_for_task(
        self,
        task_id: str,
        timeout: int = 120,
        poll_interval: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Poll task status until completion or timeout.

        Args:
            task_id: Task ID to poll
            timeout: Maximum time to wait in seconds
            poll_interval: Time between polls in seconds

        Returns:
            Task result dictionary

        Raises:
            TimeoutError: If task doesn't complete within timeout
            Exception: If task fails
        """
        from api_paths import task_detail
        
        start_time = time.time()
        
        while (time.time() - start_time) < timeout:
            response = self.get(task_detail(task_id))
            
            if response.status_code != 200:
                raise Exception(f"Failed to get task status: {response.text}")
            
            task = response.json()
            status = task.get("status", "unknown")
            
            if status == "completed":
                return task
            elif status == "failed":
                error = task.get("error", "Unknown error")
                raise Exception(f"Task failed: {error}")
            elif status == "cancelled":
                raise Exception("Task was cancelled")
            
            # Still running or pending, wait and poll again
            time.sleep(poll_interval)
        
        raise TimeoutError(f"Task {task_id} did not complete within {timeout} seconds")

    def close(self):
        """Close the HTTP client."""
        self.client.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def create_mock_token(user_id: str = "test_user", username: str = "testuser") -> str:
    """
    Create a mock JWT token for testing.
    
    Note: This is for testing only. In production tests with real auth,
    you would obtain real tokens from Logto.
    
    Args:
        user_id: User ID to include in token
        username: Username to include in token
    
    Returns:
        Mock token string (in real use, backend should accept this for test mode)
    """
    # For now, return a simple mock token
    # In a real scenario, you'd either:
    # 1. Generate a valid JWT with test signing key
    # 2. Use a test auth endpoint
    # 3. Configure backend to accept mock tokens in test mode
    return f"mock_token_{user_id}"
