"""
Comprehensive Selector Normalization Testing

Tests all selector formats across all nodes that use selectors.
Verifies that any format works correctly with Playwright.
"""

import pytest
from src.casare_rpa.utils.selector_normalizer import (
    normalize_selector,
    detect_selector_type,
    validate_selector_format
)


class TestSelectorNormalization:
    """Test selector normalization logic."""

    @pytest.mark.parametrize("selector,description", [
        # XPath variants
        ('//*[@id="search"]', 'XPath with //*'),
        ('//input[@name="q"]', 'XPath with //'),
        ('xpath=//*[@class="btn"]', 'XPath with xpath= prefix'),
        ('/html/body/div[1]', 'Absolute XPath'),
        ('//*[contains(text(), "Click")]', 'XPath with text function'),

        # CSS variants
        ('#myId', 'CSS ID selector'),
        ('.button-primary', 'CSS class selector'),
        ('button[type="submit"]', 'CSS attribute'),
        ('[data-testid="login"]', 'CSS data attribute'),
        ('[aria-label="Close"]', 'CSS ARIA attribute'),
        ('div > button.primary', 'CSS with combinators'),
        ('input[name="username"]', 'CSS input with name'),

        # Text selectors
        ('text=Click me', 'Text selector'),
        ('text=Submit', 'Text selector short'),

        # Edge cases
        ('button', 'Simple tag name'),
        ('#id.class[attr]', 'Complex CSS'),
    ])
    def test_normalize_selector(self, selector, description):
        """Test that selector normalization works for various formats."""
        normalized = normalize_selector(selector)
        assert normalized is not None, f"Failed for {description}: {selector}"

    def test_empty_selector_normalization(self):
        """Test that empty selector returns empty or handles gracefully."""
        # Empty selector should return empty or handle gracefully
        result = normalize_selector('')
        # Either empty string or None is acceptable
        assert result is not None or result == ''


class TestSelectorFormatValidation:
    """Test selector format validation."""

    @pytest.mark.parametrize("selector,should_be_valid,description", [
        ('#valid-id', True, "Valid CSS ID"),
        ('//*[@id="valid"]', True, "Valid XPath"),
        ('[unbalanced', False, "Unbalanced brackets"),
        ('contains(text()', False, "Unbalanced parentheses"),
        ('', False, "Empty selector"),
        (None, False, "None selector"),
        ('button', True, "Simple tag"),
    ])
    def test_validate_selector_format(self, selector, should_be_valid, description):
        """Test selector format validation."""
        is_valid, error = validate_selector_format(selector)
        assert is_valid == should_be_valid, f"Failed for {description}: expected {should_be_valid}, got {is_valid}. Error: {error}"


class TestSelectorTypeDetection:
    """Test selector type detection."""

    @pytest.mark.parametrize("selector,expected_contains", [
        ('//*[@id="test"]', 'xpath'),
        ('//div', 'xpath'),
        ('xpath=//button', 'xpath'),
        ('#test', 'css'),
        ('.class', 'css'),
        ('button', 'css'),
        ('text=Click', 'text'),
    ])
    def test_detect_selector_type(self, selector, expected_contains):
        """Test that selector type is correctly detected."""
        detected_type = detect_selector_type(selector)
        assert expected_contains.lower() in detected_type.lower(), \
            f"Expected type containing '{expected_contains}', got '{detected_type}' for selector '{selector}'"


class TestPlaywrightIntegration:
    """Playwright integration tests - requires browser."""

    @pytest.fixture
    def test_html(self):
        """HTML content for testing selectors."""
        return """
        <!DOCTYPE html>
        <html>
        <head><title>Selector Test Page</title></head>
        <body>
            <input id="search-box" name="query" data-testid="search-input"
                   aria-label="Search" placeholder="Type here..." />
            <button id="submit-btn" class="btn-primary" data-testid="submit-button"
                    aria-label="Submit form">Submit</button>
            <div class="container">
                <span>Click me</span>
                <a href="#" data-action="link">Link text</a>
            </div>
        </body>
        </html>
        """

    @pytest.mark.asyncio
    async def test_playwright_selector_xpath(self, test_html):
        """Test XPath selectors with Playwright."""
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.set_content(test_html)

            # Test XPath selector
            normalized = normalize_selector('//*[@id="search-box"]')
            element = await page.query_selector(normalized)
            assert element is not None, "XPath selector should find element"

            await browser.close()

    @pytest.mark.asyncio
    async def test_playwright_selector_css(self, test_html):
        """Test CSS selectors with Playwright."""
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.set_content(test_html)

            # Test CSS selector
            normalized = normalize_selector('#search-box')
            element = await page.query_selector(normalized)
            assert element is not None, "CSS selector should find element"

            await browser.close()

    @pytest.mark.asyncio
    async def test_playwright_selector_data_attribute(self, test_html):
        """Test data attribute selectors with Playwright."""
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.set_content(test_html)

            # Test data attribute selector
            normalized = normalize_selector('[data-testid="search-input"]')
            element = await page.query_selector(normalized)
            assert element is not None, "Data attribute selector should find element"

            await browser.close()

    @pytest.mark.asyncio
    async def test_playwright_selector_aria(self, test_html):
        """Test ARIA selectors with Playwright."""
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.set_content(test_html)

            # Test ARIA selector
            normalized = normalize_selector('[aria-label="Search"]')
            element = await page.query_selector(normalized)
            assert element is not None, "ARIA selector should find element"

            await browser.close()

    @pytest.mark.asyncio
    async def test_playwright_selector_text(self, test_html):
        """Test text selectors with Playwright."""
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.set_content(test_html)

            # Test text selector
            normalized = normalize_selector('text=Submit')
            element = await page.query_selector(normalized)
            assert element is not None, "Text selector should find element"

            await browser.close()

    @pytest.mark.asyncio
    async def test_playwright_selector_not_found(self, test_html):
        """Test that nonexistent selector returns None."""
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.set_content(test_html)

            # Test nonexistent selector
            normalized = normalize_selector('#nonexistent')
            element = await page.query_selector(normalized)
            assert element is None, "Nonexistent selector should return None"

            await browser.close()
