"""
Browser Automation Helpers using Playwright

Provides utilities for:
- Browser initialization
- Page navigation
- Element interactions
- Wait strategies
- Screenshot capture
- Session management
"""

import os
from typing import Optional, Dict, Any
from playwright.sync_api import Browser, Page, Playwright, sync_playwright, expect


class BrowserHelper:
    """Browser automation helper using Playwright."""

    def __init__(
        self,
        headless: bool = True,
        browser_type: str = "chromium",
        base_url: Optional[str] = None,
        slow_mo: int = 0,
    ):
        """
        Initialize browser helper.

        Args:
            headless: Run browser in headless mode
            browser_type: Browser type (chromium, firefox, webkit)
            base_url: Base URL for navigation (defaults to http://localhost:5173)
            slow_mo: Slow down operations by N milliseconds
        """
        self.headless = headless
        self.browser_type = browser_type
        self.base_url = base_url or os.getenv("FRONTEND_URL", "http://localhost:5173")
        self.slow_mo = slow_mo
        
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None

    def start(self):
        """Start browser instance."""
        if self.playwright is None:
            self.playwright = sync_playwright().start()
            
            browser_launcher = getattr(self.playwright, self.browser_type)
            self.browser = browser_launcher.launch(
                headless=self.headless,
                slow_mo=self.slow_mo,
            )
            
            context = self.browser.new_context(
                viewport={"width": 1920, "height": 1080},
                locale="en-US",
            )
            
            self.page = context.new_page()

    def stop(self):
        """Stop browser instance and cleanup."""
        if self.page:
            self.page.close()
            self.page = None
        
        if self.browser:
            self.browser.close()
            self.browser = None
        
        if self.playwright:
            self.playwright.stop()
            self.playwright = None

    def goto(self, path: str, wait_until: str = "networkidle"):
        """
        Navigate to a page.

        Args:
            path: Path relative to base_url (e.g., '/') or absolute URL
            wait_until: When to consider navigation succeeded
                       ('load', 'domcontentloaded', 'networkidle')
        """
        if not self.page:
            self.start()
        
        url = path if path.startswith("http") else f"{self.base_url}{path}"
        self.page.goto(url, wait_until=wait_until)

    def click(self, selector: str, timeout: int = 30000):
        """
        Click an element.

        Args:
            selector: CSS selector or text selector
            timeout: Timeout in milliseconds
        """
        self.page.click(selector, timeout=timeout)

    def fill(self, selector: str, value: str, timeout: int = 30000):
        """
        Fill input field.

        Args:
            selector: CSS selector
            value: Value to fill
            timeout: Timeout in milliseconds
        """
        self.page.fill(selector, value, timeout=timeout)

    def select_option(self, selector: str, value: str, timeout: int = 30000):
        """
        Select option from dropdown.

        Args:
            selector: CSS selector
            value: Option value to select
            timeout: Timeout in milliseconds
        """
        self.page.select_option(selector, value, timeout=timeout)

    def wait_for_selector(
        self,
        selector: str,
        state: str = "visible",
        timeout: int = 30000,
    ):
        """
        Wait for element to reach a specific state.

        Args:
            selector: CSS selector
            state: Element state ('attached', 'detached', 'visible', 'hidden')
            timeout: Timeout in milliseconds
        """
        self.page.wait_for_selector(selector, state=state, timeout=timeout)

    def wait_for_url(self, url: str, timeout: int = 30000):
        """
        Wait for URL to match pattern.

        Args:
            url: URL pattern (can use regex)
            timeout: Timeout in milliseconds
        """
        self.page.wait_for_url(url, timeout=timeout)

    def wait_for_network_idle(self, timeout: int = 30000):
        """
        Wait for network to be idle (no requests for 500ms).

        Args:
            timeout: Timeout in milliseconds
        """
        self.page.wait_for_load_state("networkidle", timeout=timeout)

    def screenshot(self, path: str, full_page: bool = False):
        """
        Take screenshot.

        Args:
            path: Path to save screenshot
            full_page: Capture full scrollable page
        """
        self.page.screenshot(path=path, full_page=full_page)

    def get_text(self, selector: str) -> str:
        """
        Get text content of element.

        Args:
            selector: CSS selector

        Returns:
            Text content
        """
        return self.page.text_content(selector)

    def is_visible(self, selector: str) -> bool:
        """
        Check if element is visible.

        Args:
            selector: CSS selector

        Returns:
            True if visible, False otherwise
        """
        return self.page.is_visible(selector)

    def set_local_storage(self, items: Dict[str, str]):
        """
        Set localStorage items.

        Args:
            items: Dictionary of key-value pairs
        """
        for key, value in items.items():
            self.page.evaluate(
                f"window.localStorage.setItem('{key}', '{value}')"
            )

    def get_local_storage(self, key: str) -> Optional[str]:
        """
        Get localStorage item.

        Args:
            key: Storage key

        Returns:
            Storage value or None
        """
        return self.page.evaluate(f"window.localStorage.getItem('{key}')")

    def clear_local_storage(self):
        """Clear all localStorage items."""
        self.page.evaluate("window.localStorage.clear()")

    def set_auth_token(self, token: str):
        """
        Set authentication token in localStorage.

        Args:
            token: JWT token
        """
        # This depends on how your frontend stores auth tokens
        # Adjust the key name as needed
        self.set_local_storage({"auth_token": token})

    def expect_visible(self, selector: str):
        """Assert element is visible."""
        expect(self.page.locator(selector)).to_be_visible()

    def expect_text(self, selector: str, text: str):
        """Assert element contains text."""
        expect(self.page.locator(selector)).to_contain_text(text)

    def expect_url(self, pattern: str):
        """Assert URL matches pattern."""
        expect(self.page).to_have_url(pattern)

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
