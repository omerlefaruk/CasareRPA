"""
Real-World Workflow Test
Demonstrates selector normalization with browser automation
"""

import pytest
from src.casare_rpa.utils.selector_normalizer import normalize_selector


class TestRealWorldSelectors:
    """Test selector normalization with real-world selectors."""

    @pytest.mark.parametrize("selector,description", [
        ('textarea[name="q"]', 'CSS from DevTools'),
        ('//*[@name="q"]', 'XPath from picker'),
        ('[name="q"]', 'Simple CSS attribute'),
        ('textarea#APjFqb', 'CSS with tag and ID'),
    ])
    def test_search_box_selectors(self, selector, description):
        """Test search box selectors normalize correctly."""
        normalized = normalize_selector(selector)
        assert normalized is not None, f"Failed for {description}: {selector}"

    @pytest.mark.parametrize("selector,description", [
        ('input[name="btnK"]', 'CSS name attribute'),
        ('[name="btnK"]', 'CSS attribute only'),
        ('//*[@name="btnK"]', 'XPath name attribute'),
        ('input[value="Google Search"]', 'CSS value attribute'),
    ])
    def test_button_selectors(self, selector, description):
        """Test button selectors normalize correctly."""
        normalized = normalize_selector(selector)
        assert normalized is not None, f"Failed for {description}: {selector}"

    @pytest.mark.parametrize("selector,description", [
        ('[data-testid="my-button"]', 'CSS data-testid'),
        ('//*[@data-testid="my-button"]', 'XPath data-testid'),
        ('[data-cy="username"]', 'CSS data-cy'),
        ('[data-analytics="track-click"]', 'CSS data-analytics'),
    ])
    def test_data_attribute_selectors(self, selector, description):
        """Test data attribute selectors normalize correctly."""
        normalized = normalize_selector(selector)
        assert normalized is not None, f"Failed for {description}: {selector}"

    @pytest.mark.parametrize("selector,description", [
        ('[aria-label="Close dialog"]', 'CSS aria-label'),
        ('//*[@aria-label="Search"]', 'XPath aria-label'),
        ('[role="alert"]', 'CSS role attribute'),
        ('[aria-describedby="help-text"]', 'CSS aria-describedby'),
    ])
    def test_aria_selectors(self, selector, description):
        """Test ARIA selectors normalize correctly."""
        normalized = normalize_selector(selector)
        assert normalized is not None, f"Failed for {description}: {selector}"


class TestPlaywrightRealWorkflow:
    """Playwright integration tests for real workflow scenarios."""

    @pytest.fixture
    def test_html(self):
        """HTML content for testing selectors."""
        return """
        <html>
        <body>
            <button data-testid="my-button" data-action="submit">Click</button>
            <input data-cy="username" id="user" />
            <div data-analytics="track-click">Analytics</div>
            <button aria-label="Close dialog">X</button>
            <input aria-label="Search" type="search" />
            <div role="alert" aria-live="polite">Alert</div>
            <button aria-describedby="help-text">Help</button>
        </body>
        </html>
        """

    @pytest.mark.asyncio
    async def test_data_attribute_selectors_with_playwright(self, test_html):
        """Test data attribute selectors with Playwright."""
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.set_content(test_html)

            # Test data-testid selector
            normalized = normalize_selector('[data-testid="my-button"]')
            element = await page.query_selector(normalized)
            assert element is not None

            await browser.close()

    @pytest.mark.asyncio
    async def test_aria_selectors_with_playwright(self, test_html):
        """Test ARIA selectors with Playwright."""
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.set_content(test_html)

            # Test aria-label selector
            normalized = normalize_selector('[aria-label="Close dialog"]')
            element = await page.query_selector(normalized)
            assert element is not None

            await browser.close()

    @pytest.mark.asyncio
    async def test_role_selector_with_playwright(self, test_html):
        """Test role selector with Playwright."""
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.set_content(test_html)

            # Test role selector
            normalized = normalize_selector('[role="alert"]')
            element = await page.query_selector(normalized)
            assert element is not None

            await browser.close()

    @pytest.mark.asyncio
    async def test_xpath_data_attribute_with_playwright(self, test_html):
        """Test XPath data attribute selector with Playwright."""
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.set_content(test_html)

            # Test XPath selector
            normalized = normalize_selector('//*[@data-testid="my-button"]')
            element = await page.query_selector(normalized)
            assert element is not None

            await browser.close()
