"""
CasareRPA - Browser Automation E2E Tests.

Comprehensive end-to-end tests for browser automation nodes using headless
Playwright and test HTML pages served via aiohttp test server.

Test Categories:
1. Browser Lifecycle (launch, close)
2. Navigation (go to URL, back, forward, refresh)
3. Element Interaction (click, type, select, checkbox)
4. Form Automation (fill forms, validation)
5. Data Extraction (text, attributes, screenshots)
6. Wait Operations (element, navigation, timeout)
7. Multi-Tab (new tab, switch tabs)
8. Complex Workflows (login, scraping, pagination)
"""

import os
from pathlib import Path
from typing import Any

import pytest
import pytest_asyncio

from tests.e2e.helpers.workflow_builder import WorkflowBuilder


# =============================================================================
# TEST MARKERS AND FIXTURES
# =============================================================================


pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.e2e,
    pytest.mark.browser,
]


@pytest_asyncio.fixture
async def test_url(test_server) -> str:
    """Get base URL for test server."""
    return str(test_server.make_url(""))


@pytest.fixture
def form_page_url(test_url: str) -> str:
    """Get URL for form.html test page."""
    return f"{test_url}/form.html"


@pytest.fixture
def table_page_url(test_url: str) -> str:
    """Get URL for table.html test page."""
    return f"{test_url}/table.html"


# =============================================================================
# BROWSER LIFECYCLE TESTS
# =============================================================================


class TestBrowserLifecycle:
    """Tests for browser launch and close operations."""

    async def test_launch_browser_headless(self, test_url: str) -> None:
        """Test launching browser in headless mode."""
        result = await (
            WorkflowBuilder("Launch Browser Headless")
            .add_start()
            .add_launch_browser(url=test_url, headless=True)
            .add_close_browser()
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["executed_nodes"] >= 3

    async def test_launch_browser_chromium(self, test_url: str) -> None:
        """Test launching Chromium browser specifically."""
        result = await (
            WorkflowBuilder("Launch Chromium")
            .add_start()
            .add_launch_browser(
                url=test_url,
                headless=True,
                browser_type="chromium",
            )
            .add_close_browser()
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"

    async def test_launch_and_close_browser(self, form_page_url: str) -> None:
        """Test full browser lifecycle with navigation."""
        result = await (
            WorkflowBuilder("Browser Lifecycle")
            .add_start()
            .add_launch_browser(headless=True)
            .add_navigate(form_page_url)
            .add_wait_for_element("#test-form")
            .add_close_browser()
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"


# =============================================================================
# NAVIGATION TESTS
# =============================================================================


class TestNavigation:
    """Tests for page navigation operations."""

    async def test_navigate_to_url(self, test_url: str) -> None:
        """Test basic URL navigation."""
        result = await (
            WorkflowBuilder("Navigate to URL")
            .add_start()
            .add_launch_browser(headless=True)
            .add_navigate(test_url + "/form.html")
            .add_wait_for_element("h1")
            .add_extract_text("h1", "page_title")
            .add_close_browser()
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"].get("page_title") == "E2E Test Form"

    async def test_navigate_to_local_page(self, form_page_url: str) -> None:
        """Test navigation to local test page."""
        result = await (
            WorkflowBuilder("Navigate Local Page")
            .add_start()
            .add_launch_browser(headless=True)
            .add_navigate(form_page_url)
            .add_wait_for_element("#name")
            .add_close_browser()
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"

    async def test_go_back(self, form_page_url: str, table_page_url: str) -> None:
        """Test back navigation."""
        result = await (
            WorkflowBuilder("Go Back Navigation")
            .add_start()
            .add_launch_browser(headless=True)
            .add_navigate(form_page_url)
            .add_wait_for_element("h1")
            .add_navigate(table_page_url)
            .add_wait_for_element("h1")
            .add_go_back()
            .add_wait_for_element("#test-form")
            .add_extract_text("h1", "title")
            .add_close_browser()
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"].get("title") == "E2E Test Form"

    async def test_go_forward(self, form_page_url: str, table_page_url: str) -> None:
        """Test forward navigation."""
        result = await (
            WorkflowBuilder("Go Forward Navigation")
            .add_start()
            .add_launch_browser(headless=True)
            .add_navigate(form_page_url)
            .add_wait_for_element("h1")
            .add_navigate(table_page_url)
            .add_wait_for_element("h1")
            .add_go_back()
            .add_wait_for_element("#test-form")
            .add_go_forward()
            .add_wait_for_element("#data-table")
            .add_extract_text("h1", "title")
            .add_close_browser()
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"].get("title") == "Product Catalog"

    async def test_refresh_page(self, form_page_url: str) -> None:
        """Test page refresh."""
        result = await (
            WorkflowBuilder("Refresh Page")
            .add_start()
            .add_launch_browser(headless=True)
            .add_navigate(form_page_url)
            .add_type_text("#name", "Before Refresh")
            .add_refresh()
            .add_wait_for_element("#name")
            .add_get_attribute("#name", "value", "input_value")
            .add_close_browser()
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        # After refresh, input should be empty
        assert result["variables"].get("input_value") == ""


# =============================================================================
# ELEMENT INTERACTION TESTS
# =============================================================================


class TestElementInteraction:
    """Tests for element interaction operations."""

    async def test_click_element(self, form_page_url: str) -> None:
        """Test clicking an element."""
        result = await (
            WorkflowBuilder("Click Element")
            .add_start()
            .add_launch_browser(headless=True)
            .add_navigate(form_page_url)
            .add_type_text("#name", "Test User")
            .add_type_text("#email", "test@example.com")
            .add_click("#terms")  # Click checkbox
            .add_click("#submit")
            .add_wait_for_element(".result.visible")
            .add_extract_text(".result h3", "result_text")
            .add_close_browser()
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert "Successfully" in result["variables"].get("result_text", "")

    async def test_type_text(self, form_page_url: str) -> None:
        """Test typing text into an input field."""
        result = await (
            WorkflowBuilder("Type Text")
            .add_start()
            .add_launch_browser(headless=True)
            .add_navigate(form_page_url)
            .add_type_text("#name", "John Doe")
            .add_get_attribute("#name", "value", "typed_value")
            .add_close_browser()
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"].get("typed_value") == "John Doe"

    async def test_clear_and_type(self, form_page_url: str) -> None:
        """Test clearing and typing new text."""
        result = await (
            WorkflowBuilder("Clear and Type")
            .add_start()
            .add_launch_browser(headless=True)
            .add_navigate(form_page_url)
            .add_type_text("#name", "Old Text")
            .add_clear_text("#name")
            .add_type_text("#name", "New Text", clear_first=False)
            .add_get_attribute("#name", "value", "final_value")
            .add_close_browser()
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"].get("final_value") == "New Text"

    async def test_select_dropdown(self, form_page_url: str) -> None:
        """Test selecting a dropdown option."""
        result = await (
            WorkflowBuilder("Select Dropdown")
            .add_start()
            .add_launch_browser(headless=True)
            .add_navigate(form_page_url)
            .add_select_dropdown("#country", "us")
            .add_get_attribute("#country", "value", "selected_value")
            .add_close_browser()
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"].get("selected_value") == "us"

    async def test_check_checkbox(self, form_page_url: str) -> None:
        """Test checking a checkbox."""
        result = await (
            WorkflowBuilder("Check Checkbox")
            .add_start()
            .add_launch_browser(headless=True)
            .add_navigate(form_page_url)
            .add_check_checkbox("#newsletter")
            .add_close_browser()
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"

    async def test_uncheck_checkbox(self, form_page_url: str) -> None:
        """Test unchecking a checkbox."""
        result = await (
            WorkflowBuilder("Uncheck Checkbox")
            .add_start()
            .add_launch_browser(headless=True)
            .add_navigate(form_page_url)
            # First check, then uncheck
            .add_click("#newsletter")  # Check
            .add_click("#newsletter")  # Uncheck
            .add_close_browser()
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"

    async def test_double_click(self, form_page_url: str) -> None:
        """Test double-clicking an element."""
        result = await (
            WorkflowBuilder("Double Click")
            .add_start()
            .add_launch_browser(headless=True)
            .add_navigate(form_page_url)
            .add_double_click("#name")
            .add_close_browser()
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"

    async def test_right_click(self, form_page_url: str) -> None:
        """Test right-clicking an element."""
        result = await (
            WorkflowBuilder("Right Click")
            .add_start()
            .add_launch_browser(headless=True)
            .add_navigate(form_page_url)
            .add_right_click("#name")
            .add_close_browser()
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"


# =============================================================================
# FORM AUTOMATION TESTS
# =============================================================================


class TestFormAutomation:
    """Tests for form automation scenarios."""

    async def test_fill_form_complete(self, form_page_url: str) -> None:
        """Test filling a complete form and submitting."""
        result = await (
            WorkflowBuilder("Fill Complete Form")
            .add_start()
            .add_launch_browser(headless=True)
            .add_navigate(form_page_url)
            # Fill form fields
            .add_type_text("#name", "John Doe")
            .add_type_text("#email", "john.doe@example.com")
            .add_type_text("#password", "SecurePass123")
            .add_select_dropdown("#country", "us")
            .add_type_text("#message", "This is a test message.")
            .add_click("#newsletter")  # Subscribe to newsletter
            .add_click("#terms")  # Accept terms
            # Submit form
            .add_click("#submit")
            .add_wait_for_element(".result.visible")
            # Verify result
            .add_extract_text(".result h3", "result_title")
            .add_close_browser()
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert "Successfully" in result["variables"].get("result_title", "")

    async def test_form_with_variable_values(self, form_page_url: str) -> None:
        """Test filling form with variable substitution."""
        result = await (
            WorkflowBuilder("Form with Variables")
            .add_start()
            .add_set_variable("user_name", "Variable User")
            .add_set_variable("user_email", "variable@test.com")
            .add_launch_browser(headless=True)
            .add_navigate(form_page_url)
            .add_type_text("#name", "{{user_name}}")
            .add_type_text("#email", "{{user_email}}")
            .add_click("#terms")
            .add_click("#submit")
            .add_wait_for_element(".result.visible")
            .add_close_browser()
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"


# =============================================================================
# DATA EXTRACTION TESTS
# =============================================================================


class TestDataExtraction:
    """Tests for data extraction operations."""

    async def test_extract_text(self, form_page_url: str) -> None:
        """Test extracting text content from an element."""
        result = await (
            WorkflowBuilder("Extract Text")
            .add_start()
            .add_launch_browser(headless=True)
            .add_navigate(form_page_url)
            .add_extract_text("h1", "header_text")
            .add_close_browser()
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"].get("header_text") == "E2E Test Form"

    async def test_extract_text_inner_text(self, form_page_url: str) -> None:
        """Test extracting inner text (visible text)."""
        result = await (
            WorkflowBuilder("Extract Inner Text")
            .add_start()
            .add_launch_browser(headless=True)
            .add_navigate(form_page_url)
            .add_extract_text("h1", "header_text", use_inner_text=True)
            .add_close_browser()
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"].get("header_text") == "E2E Test Form"

    async def test_get_attribute(self, form_page_url: str) -> None:
        """Test getting an attribute value."""
        result = await (
            WorkflowBuilder("Get Attribute")
            .add_start()
            .add_launch_browser(headless=True)
            .add_navigate(form_page_url)
            .add_get_attribute("#submit", "type", "button_type")
            .add_close_browser()
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"].get("button_type") == "submit"

    async def test_get_data_attribute(self, form_page_url: str) -> None:
        """Test getting a data-* attribute."""
        result = await (
            WorkflowBuilder("Get Data Attribute")
            .add_start()
            .add_launch_browser(headless=True)
            .add_navigate(form_page_url)
            .add_get_attribute("#name", "data-testid", "test_id")
            .add_close_browser()
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"].get("test_id") == "name-input"

    async def test_extract_multiple_elements(self, table_page_url: str) -> None:
        """Test extracting text from table elements."""
        result = await (
            WorkflowBuilder("Extract Multiple Elements")
            .add_start()
            .add_launch_browser(headless=True)
            .add_navigate(table_page_url)
            .add_wait_for_element("#data-table")
            # Extract first product name
            .add_extract_text(
                "#table-body tr:first-child td:nth-child(2)", "first_product"
            )
            .add_close_browser()
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"].get("first_product") is not None


# =============================================================================
# WAIT OPERATIONS TESTS
# =============================================================================


class TestWaitOperations:
    """Tests for wait and synchronization operations."""

    async def test_wait_for_element_visible(self, form_page_url: str) -> None:
        """Test waiting for an element to be visible."""
        result = await (
            WorkflowBuilder("Wait for Element Visible")
            .add_start()
            .add_launch_browser(headless=True)
            .add_navigate(form_page_url)
            .add_wait_for_element("#name", state="visible")
            .add_close_browser()
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"

    async def test_wait_for_element_timeout(self, form_page_url: str) -> None:
        """Test timeout when waiting for non-existent element."""
        result = await (
            WorkflowBuilder("Wait for Element Timeout")
            .add_start()
            .add_launch_browser(headless=True)
            .add_navigate(form_page_url)
            .add_wait_for_element("#nonexistent-element", timeout=2000)
            .add_close_browser()
            .add_end()
            .execute(timeout=60.0)
        )

        # This should fail because element doesn't exist
        assert not result["success"]
        assert result["error"] is not None

    async def test_wait_for_navigation(self, form_page_url: str) -> None:
        """Test waiting for navigation to complete."""
        result = await (
            WorkflowBuilder("Wait for Navigation")
            .add_start()
            .add_launch_browser(headless=True)
            .add_navigate(form_page_url)
            .add_wait_for_navigation()
            .add_extract_text("h1", "title")
            .add_close_browser()
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"

    async def test_simple_wait(self, form_page_url: str) -> None:
        """Test simple time-based wait."""
        result = await (
            WorkflowBuilder("Simple Wait")
            .add_start()
            .add_launch_browser(headless=True)
            .add_navigate(form_page_url)
            .add_wait(0.5)  # Wait 500ms
            .add_extract_text("h1", "title")
            .add_close_browser()
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"


# =============================================================================
# SCREENSHOT TESTS
# =============================================================================


class TestScreenshots:
    """Tests for screenshot operations."""

    async def test_take_screenshot_full_page(
        self, form_page_url: str, temp_workspace: Path
    ) -> None:
        """Test taking a full page screenshot."""
        screenshot_path = str(temp_workspace / "full_page.png")

        result = await (
            WorkflowBuilder("Full Page Screenshot")
            .add_start()
            .add_launch_browser(headless=True)
            .add_navigate(form_page_url)
            .add_wait_for_element("h1")
            .add_screenshot(screenshot_path, full_page=True)
            .add_close_browser()
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert Path(screenshot_path).exists()
        assert Path(screenshot_path).stat().st_size > 0

    async def test_take_screenshot_element(
        self, form_page_url: str, temp_workspace: Path
    ) -> None:
        """Test taking a screenshot of a specific element."""
        screenshot_path = str(temp_workspace / "element.png")

        result = await (
            WorkflowBuilder("Element Screenshot")
            .add_start()
            .add_launch_browser(headless=True)
            .add_navigate(form_page_url)
            .add_wait_for_element("#test-form")
            .add_screenshot(screenshot_path, selector="#test-form")
            .add_close_browser()
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert Path(screenshot_path).exists()


# =============================================================================
# MULTI-TAB TESTS
# =============================================================================


class TestMultiTab:
    """Tests for multi-tab operations."""

    async def test_new_tab(self, form_page_url: str) -> None:
        """Test creating a new tab."""
        result = await (
            WorkflowBuilder("New Tab")
            .add_start()
            .add_launch_browser(headless=True)
            .add_navigate(form_page_url)
            .add_new_tab("second_tab", form_page_url)
            .add_close_browser()
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"

    async def test_new_tab_with_url(
        self, form_page_url: str, table_page_url: str
    ) -> None:
        """Test creating a new tab with a URL."""
        result = await (
            WorkflowBuilder("New Tab with URL")
            .add_start()
            .add_launch_browser(headless=True)
            .add_navigate(form_page_url)
            .add_new_tab("table_tab", table_page_url)
            .add_wait_for_element("#data-table")
            .add_extract_text("h1", "table_title")
            .add_close_browser()
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"].get("table_title") == "Product Catalog"


# =============================================================================
# COMPLEX WORKFLOW TESTS
# =============================================================================


class TestComplexWorkflows:
    """Tests for complex multi-step workflows."""

    async def test_login_workflow(self, form_page_url: str) -> None:
        """Test a login-like workflow (using form page)."""
        result = await (
            WorkflowBuilder("Login Workflow")
            .add_start()
            .add_launch_browser(headless=True)
            .add_navigate(form_page_url)
            .add_wait_for_element("#name")
            # Simulate login form
            .add_type_text("#name", "admin")
            .add_type_text("#email", "admin@example.com")
            .add_type_text("#password", "password123")
            .add_click("#terms")
            .add_click("#submit")
            # Wait for result
            .add_wait_for_element(".result.visible", timeout=5000)
            .add_extract_text(".result h3", "result")
            .add_close_browser()
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert "Successfully" in result["variables"].get("result", "")

    async def test_search_and_extract(self, table_page_url: str) -> None:
        """Test searching and extracting results."""
        result = await (
            WorkflowBuilder("Search and Extract")
            .add_start()
            .add_launch_browser(headless=True)
            .add_navigate(table_page_url)
            .add_wait_for_element("#data-table")
            # Search for a product
            .add_type_text("#search", "Laptop")
            .add_wait(0.5)  # Wait for filter
            # Extract first result
            .add_extract_text(
                "#table-body tr:first-child td:nth-child(2)", "product_name"
            )
            .add_close_browser()
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert "Laptop" in result["variables"].get("product_name", "")

    async def test_filter_and_extract(self, table_page_url: str) -> None:
        """Test filtering data and extracting results."""
        result = await (
            WorkflowBuilder("Filter and Extract")
            .add_start()
            .add_launch_browser(headless=True)
            .add_navigate(table_page_url)
            .add_wait_for_element("#data-table")
            # Filter by category
            .add_select_dropdown("#category-filter", "electronics")
            .add_wait(0.5)  # Wait for filter
            # Extract summary
            .add_extract_text("#summary", "summary_text")
            .add_close_browser()
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        # Should show filtered results
        assert "products" in result["variables"].get("summary_text", "").lower()

    async def test_pagination_workflow(self, table_page_url: str) -> None:
        """Test paginating through table data."""
        result = await (
            WorkflowBuilder("Pagination Workflow")
            .add_start()
            .add_launch_browser(headless=True)
            .add_navigate(table_page_url)
            .add_wait_for_element("#data-table")
            # Extract first page data
            .add_extract_text("#summary", "page1_summary")
            # Go to page 2
            .add_click("#pagination button.page-btn[data-page='2']")
            .add_wait(0.5)  # Wait for update
            # Extract second page data
            .add_extract_text("#summary", "page2_summary")
            .add_close_browser()
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        # Both pages should have summary text
        assert result["variables"].get("page1_summary")
        assert result["variables"].get("page2_summary")

    async def test_multi_step_data_extraction(self, table_page_url: str) -> None:
        """Test extracting data in multiple steps."""
        result = await (
            WorkflowBuilder("Multi-step Extraction")
            .add_start()
            .add_launch_browser(headless=True)
            .add_navigate(table_page_url)
            .add_wait_for_element("#data-table")
            # Extract page title
            .add_extract_text("h1", "page_title")
            # Extract first row product
            .add_extract_text(
                "#table-body tr:first-child td:nth-child(2)", "first_product"
            )
            # Extract first row price
            .add_extract_text("#table-body tr:first-child td.price", "first_price")
            .add_close_browser()
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"].get("page_title") == "Product Catalog"
        assert result["variables"].get("first_product")
        assert "$" in result["variables"].get("first_price", "")

    async def test_conditional_element_check(self, form_page_url: str) -> None:
        """Test checking if element exists before interaction."""
        result = await (
            WorkflowBuilder("Conditional Check")
            .add_start()
            .add_launch_browser(headless=True)
            .add_navigate(form_page_url)
            # First check if form exists
            .add_wait_for_element("#test-form")
            .add_set_variable("form_found", True)
            # Then interact with it
            .add_type_text("#name", "Test")
            .add_close_browser()
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"].get("form_found") is True

    async def test_sort_table_and_extract(self, table_page_url: str) -> None:
        """Test sorting table and extracting sorted data."""
        result = await (
            WorkflowBuilder("Sort and Extract")
            .add_start()
            .add_launch_browser(headless=True)
            .add_navigate(table_page_url)
            .add_wait_for_element("#data-table")
            # Sort by price (high to low)
            .add_select_dropdown("#sort-by", "price-desc")
            .add_wait(0.5)  # Wait for sort
            # Extract first price (should be highest)
            .add_extract_text("#table-body tr:first-child td.price", "highest_price")
            .add_close_browser()
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        price_str = result["variables"].get("highest_price", "")
        assert "$" in price_str

    async def test_form_to_result_workflow(self, form_page_url: str) -> None:
        """Test complete form submission and result extraction."""
        result = await (
            WorkflowBuilder("Form to Result")
            .add_start()
            .add_set_variable("test_name", "Automated Test")
            .add_set_variable("test_email", "automated@test.com")
            .add_launch_browser(headless=True)
            .add_navigate(form_page_url)
            .add_wait_for_element("#test-form")
            # Fill form using variables
            .add_type_text("#name", "{{test_name}}")
            .add_type_text("#email", "{{test_email}}")
            .add_select_dropdown("#country", "uk")
            .add_click("#terms")
            # Submit
            .add_click("#submit")
            .add_wait_for_element(".result.visible")
            # Extract result
            .add_extract_text(".result-data", "result_json")
            .add_close_browser()
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        result_json = result["variables"].get("result_json", "")
        assert "Automated Test" in result_json
        assert "automated@test.com" in result_json

    async def test_retry_on_slow_element(self, form_page_url: str) -> None:
        """Test retry behavior when waiting for elements."""
        result = await (
            WorkflowBuilder("Retry on Slow Element")
            .add_start()
            .add_launch_browser(headless=True)
            .add_navigate(form_page_url)
            # Wait with generous timeout
            .add_wait_for_element("#test-form", timeout=10000)
            .add_extract_text("h1", "title")
            .add_close_browser()
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"].get("title") == "E2E Test Form"


# =============================================================================
# EDGE CASE TESTS
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    async def test_empty_selector_extraction(self, form_page_url: str) -> None:
        """Test extracting text from element that might be empty."""
        result = await (
            WorkflowBuilder("Empty Extraction")
            .add_start()
            .add_launch_browser(headless=True)
            .add_navigate(form_page_url)
            # Result div is hidden initially
            .add_extract_text(".result h3", "hidden_text")
            .add_close_browser()
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        # Should extract even if element is hidden
        assert "Successfully" in result["variables"].get("hidden_text", "")

    async def test_special_characters_in_text(self, form_page_url: str) -> None:
        """Test typing text with special characters."""
        special_text = "Test <>&\"'@#$%"
        result = await (
            WorkflowBuilder("Special Characters")
            .add_start()
            .add_launch_browser(headless=True)
            .add_navigate(form_page_url)
            .add_type_text("#message", special_text)
            .add_close_browser()
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"

    async def test_rapid_sequential_clicks(self, form_page_url: str) -> None:
        """Test multiple rapid sequential clicks."""
        result = await (
            WorkflowBuilder("Rapid Clicks")
            .add_start()
            .add_launch_browser(headless=True)
            .add_navigate(form_page_url)
            .add_click("#newsletter")
            .add_click("#newsletter")
            .add_click("#newsletter")
            .add_close_browser()
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"

    async def test_navigation_to_different_pages(
        self, form_page_url: str, table_page_url: str
    ) -> None:
        """Test navigating between different pages."""
        result = await (
            WorkflowBuilder("Multi-page Navigation")
            .add_start()
            .add_launch_browser(headless=True)
            .add_navigate(form_page_url)
            .add_extract_text("h1", "form_title")
            .add_navigate(table_page_url)
            .add_extract_text("h1", "table_title")
            .add_navigate(form_page_url)
            .add_extract_text("h1", "form_title_again")
            .add_close_browser()
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"].get("form_title") == "E2E Test Form"
        assert result["variables"].get("table_title") == "Product Catalog"
        assert result["variables"].get("form_title_again") == "E2E Test Form"

    async def test_long_text_input(self, form_page_url: str) -> None:
        """Test typing long text into textarea."""
        long_text = "This is a long message. " * 20
        result = await (
            WorkflowBuilder("Long Text Input")
            .add_start()
            .add_launch_browser(headless=True)
            .add_navigate(form_page_url)
            .add_type_text("#message", long_text)
            .add_close_browser()
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
