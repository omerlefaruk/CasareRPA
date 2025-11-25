"""
Chaos tests for browser automation nodes.

Tests failure scenarios, resilience, and recovery mechanisms:
- Browser process crashes
- Network failures
- Selector failures
- Timeout scenarios
- Stale element handling
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
import pytest
from playwright.async_api import Error as PlaywrightError, TimeoutError as PlaywrightTimeout


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def execution_context():
    """Create execution context for testing."""
    from casare_rpa.core.execution_context import ExecutionContext
    from casare_rpa.core.types import ExecutionMode
    return ExecutionContext(workflow_name="ChaosTest", mode=ExecutionMode.NORMAL)


@pytest.fixture
def mock_browser_manager():
    """Create a mock browser manager."""
    manager = MagicMock()
    manager.get_browser = AsyncMock()
    manager.get_page = AsyncMock()
    manager.close_browser = AsyncMock()
    return manager


@pytest.fixture
def mock_page_with_failures():
    """Create a mock page that can simulate various failures."""
    page = MagicMock()
    page.goto = AsyncMock()
    page.click = AsyncMock()
    page.fill = AsyncMock()
    page.type = AsyncMock()
    page.wait_for_selector = AsyncMock()
    page.query_selector = AsyncMock()
    page.evaluate = AsyncMock()
    page.screenshot = AsyncMock()
    page.close = AsyncMock()
    page.wait_for_load_state = AsyncMock()
    page.url = "https://example.com"
    page.title = AsyncMock(return_value="Test Page")
    return page


# ============================================================================
# Browser Crash Tests
# ============================================================================

class TestBrowserCrash:
    """Test browser crash scenarios."""

    @pytest.mark.asyncio
    async def test_browser_disconnect_during_navigation(self, execution_context, mock_page_with_failures):
        """Test handling when browser disconnects during page navigation."""
        from casare_rpa.nodes.browser_nodes import GoToURLNode

        # Simulate browser disconnect
        mock_page_with_failures.goto.side_effect = PlaywrightError("Browser closed")

        node = GoToURLNode("test_goto")
        node.config["url"] = "https://example.com"
        execution_context.set_variable("__browser_page__", mock_page_with_failures)

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "error" in result
        assert "Browser" in result["error"] or "closed" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_browser_crash_during_click(self, execution_context, mock_page_with_failures):
        """Test handling when browser crashes during element click."""
        from casare_rpa.nodes.browser_nodes import ClickElementNode

        # Simulate browser crash
        mock_page_with_failures.click.side_effect = PlaywrightError("Target page, context or browser has been closed")

        node = ClickElementNode("test_click")
        node.config["selector"] = "#submit-button"
        execution_context.set_variable("__browser_page__", mock_page_with_failures)

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_browser_not_launched(self, execution_context):
        """Test error when trying to use browser that wasn't launched."""
        from casare_rpa.nodes.browser_nodes import GoToURLNode

        node = GoToURLNode("test_goto")
        node.config["url"] = "https://example.com"
        # No browser page set in context

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "error" in result


# ============================================================================
# Network Failure Tests
# ============================================================================

class TestNetworkFailures:
    """Test network failure scenarios."""

    @pytest.mark.asyncio
    async def test_network_timeout_on_navigation(self, execution_context, mock_page_with_failures):
        """Test handling of network timeout during navigation."""
        from casare_rpa.nodes.browser_nodes import GoToURLNode

        # Simulate timeout
        mock_page_with_failures.goto.side_effect = PlaywrightTimeout("Timeout 30000ms exceeded")

        node = GoToURLNode("test_goto")
        node.config["url"] = "https://slow-site.example.com"
        node.config["timeout"] = 30000
        execution_context.set_variable("__browser_page__", mock_page_with_failures)

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "error" in result
        assert "timeout" in result["error"].lower() or "Timeout" in result["error"]

    @pytest.mark.asyncio
    async def test_dns_resolution_failure(self, execution_context, mock_page_with_failures):
        """Test handling of DNS resolution failure."""
        from casare_rpa.nodes.browser_nodes import GoToURLNode

        # Simulate DNS failure
        mock_page_with_failures.goto.side_effect = PlaywrightError("net::ERR_NAME_NOT_RESOLVED")

        node = GoToURLNode("test_goto")
        node.config["url"] = "https://nonexistent.invalid"
        execution_context.set_variable("__browser_page__", mock_page_with_failures)

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_connection_refused(self, execution_context, mock_page_with_failures):
        """Test handling of connection refused errors."""
        from casare_rpa.nodes.browser_nodes import GoToURLNode

        # Simulate connection refused
        mock_page_with_failures.goto.side_effect = PlaywrightError("net::ERR_CONNECTION_REFUSED")

        node = GoToURLNode("test_goto")
        node.config["url"] = "https://localhost:9999"
        execution_context.set_variable("__browser_page__", mock_page_with_failures)

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "error" in result


# ============================================================================
# Selector Failure Tests
# ============================================================================

class TestSelectorFailures:
    """Test selector failure scenarios."""

    @pytest.mark.asyncio
    async def test_selector_not_found(self, execution_context, mock_page_with_failures):
        """Test handling when selector doesn't match any element."""
        from casare_rpa.nodes.browser_nodes import ClickElementNode

        # Simulate element not found
        mock_page_with_failures.click.side_effect = PlaywrightError(
            "Error: strict mode violation: locator('#nonexistent') resolved to 0 elements"
        )

        node = ClickElementNode("test_click")
        node.config["selector"] = "#nonexistent"
        execution_context.set_variable("__browser_page__", mock_page_with_failures)

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_selector_timeout(self, execution_context, mock_page_with_failures):
        """Test handling when waiting for selector times out."""
        from casare_rpa.nodes.browser_nodes import WaitForElementNode

        # Simulate wait timeout
        mock_page_with_failures.wait_for_selector.side_effect = PlaywrightTimeout(
            "Timeout 30000ms exceeded while waiting for selector '#loading-element'"
        )

        node = WaitForElementNode("test_wait")
        node.config["selector"] = "#loading-element"
        node.config["timeout"] = 30000
        execution_context.set_variable("__browser_page__", mock_page_with_failures)

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_multiple_elements_matched(self, execution_context, mock_page_with_failures):
        """Test handling when selector matches multiple elements in strict mode."""
        from casare_rpa.nodes.browser_nodes import ClickElementNode

        # Simulate multiple elements matched
        mock_page_with_failures.click.side_effect = PlaywrightError(
            "Error: strict mode violation: locator('.button') resolved to 5 elements"
        )

        node = ClickElementNode("test_click")
        node.config["selector"] = ".button"
        execution_context.set_variable("__browser_page__", mock_page_with_failures)

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "error" in result


# ============================================================================
# Stale Element Tests
# ============================================================================

class TestStaleElementHandling:
    """Test stale element reference handling."""

    @pytest.mark.asyncio
    async def test_stale_element_after_navigation(self, execution_context, mock_page_with_failures):
        """Test handling when element becomes stale after page navigation."""
        from casare_rpa.nodes.browser_nodes import ClickElementNode

        # Simulate stale element
        mock_page_with_failures.click.side_effect = PlaywrightError(
            "Element is not attached to the DOM"
        )

        node = ClickElementNode("test_click")
        node.config["selector"] = "#dynamic-element"
        execution_context.set_variable("__browser_page__", mock_page_with_failures)

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_element_removed_before_interaction(self, execution_context, mock_page_with_failures):
        """Test handling when element is removed before interaction completes."""
        from casare_rpa.nodes.browser_nodes import TypeTextNode

        # Simulate element removal
        mock_page_with_failures.fill.side_effect = PlaywrightError(
            "Element is detached from document"
        )

        node = TypeTextNode("test_type")
        node.config["selector"] = "#disappearing-input"
        node.set_input_value("text", "Test text")
        execution_context.set_variable("__browser_page__", mock_page_with_failures)

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "error" in result


# ============================================================================
# Page State Tests
# ============================================================================

class TestPageStateErrors:
    """Test page state error scenarios."""

    @pytest.mark.asyncio
    async def test_page_closed_unexpectedly(self, execution_context, mock_page_with_failures):
        """Test handling when page is closed unexpectedly."""
        from casare_rpa.nodes.browser_nodes import ExtractTextNode

        # Simulate page closed
        mock_page_with_failures.evaluate.side_effect = PlaywrightError(
            "Execution context was destroyed, most likely because of a navigation"
        )

        node = ExtractTextNode("test_extract")
        node.config["selector"] = "#content"
        execution_context.set_variable("__browser_page__", mock_page_with_failures)

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_navigation_during_operation(self, execution_context, mock_page_with_failures):
        """Test handling when navigation occurs during an operation."""
        from casare_rpa.nodes.browser_nodes import ClickElementNode

        # Simulate navigation during click
        mock_page_with_failures.click.side_effect = PlaywrightError(
            "Navigation interrupted"
        )

        node = ClickElementNode("test_click")
        node.config["selector"] = "#link"
        execution_context.set_variable("__browser_page__", mock_page_with_failures)

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "error" in result


# ============================================================================
# Screenshot/Resource Tests
# ============================================================================

class TestResourceErrors:
    """Test resource-related error scenarios."""

    @pytest.mark.asyncio
    async def test_screenshot_permission_denied(self, execution_context, mock_page_with_failures):
        """Test handling when screenshot save fails due to permissions."""
        from casare_rpa.nodes.browser_nodes import ScreenshotNode

        # Simulate permission error
        mock_page_with_failures.screenshot.side_effect = PermissionError(
            "[Errno 13] Permission denied: '/protected/screenshot.png'"
        )

        node = ScreenshotNode("test_screenshot")
        node.config["path"] = "/protected/screenshot.png"
        execution_context.set_variable("__browser_page__", mock_page_with_failures)

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_screenshot_disk_full(self, execution_context, mock_page_with_failures):
        """Test handling when disk is full during screenshot."""
        from casare_rpa.nodes.browser_nodes import ScreenshotNode

        # Simulate disk full
        mock_page_with_failures.screenshot.side_effect = OSError(
            "[Errno 28] No space left on device"
        )

        node = ScreenshotNode("test_screenshot")
        node.config["path"] = "/tmp/screenshot.png"
        execution_context.set_variable("__browser_page__", mock_page_with_failures)

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "error" in result


# ============================================================================
# Concurrent Operation Tests
# ============================================================================

class TestConcurrentOperations:
    """Test concurrent operation scenarios."""

    @pytest.mark.asyncio
    async def test_rapid_navigation_sequence(self, execution_context, mock_page_with_failures):
        """Test handling rapid sequential navigations."""
        from casare_rpa.nodes.browser_nodes import GoToURLNode

        call_count = 0
        async def navigation_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise PlaywrightError("Navigation interrupted by another navigation")
            return None

        mock_page_with_failures.goto.side_effect = navigation_side_effect
        execution_context.set_variable("__browser_page__", mock_page_with_failures)

        node1 = GoToURLNode("test_goto1")
        node1.config["url"] = "https://page1.example.com"

        # First navigation should fail
        result = await node1.execute(execution_context)
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_element_becomes_hidden_during_click(self, execution_context, mock_page_with_failures):
        """Test handling when element becomes hidden during click attempt."""
        from casare_rpa.nodes.browser_nodes import ClickElementNode

        mock_page_with_failures.click.side_effect = PlaywrightError(
            "Element is not visible"
        )

        node = ClickElementNode("test_click")
        node.config["selector"] = "#hidden-button"
        execution_context.set_variable("__browser_page__", mock_page_with_failures)

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "error" in result


# ============================================================================
# Recovery Tests
# ============================================================================

class TestErrorRecovery:
    """Test error recovery scenarios."""

    @pytest.mark.asyncio
    async def test_node_returns_proper_error_structure(self, execution_context, mock_page_with_failures):
        """Test that nodes return proper error structure for retry logic."""
        from casare_rpa.nodes.browser_nodes import ClickElementNode

        mock_page_with_failures.click.side_effect = PlaywrightTimeout("Timeout")

        node = ClickElementNode("test_click")
        node.config["selector"] = "#button"
        execution_context.set_variable("__browser_page__", mock_page_with_failures)

        result = await node.execute(execution_context)

        # Verify error structure
        assert "success" in result
        assert result["success"] is False
        assert "error" in result
        assert isinstance(result["error"], str)
        # Should have next_nodes even on failure (empty list)
        assert "next_nodes" in result

    @pytest.mark.asyncio
    async def test_context_state_after_failure(self, execution_context, mock_page_with_failures):
        """Test that context state is preserved after node failure."""
        from casare_rpa.nodes.browser_nodes import ClickElementNode
        from casare_rpa.core.types import NodeStatus

        mock_page_with_failures.click.side_effect = PlaywrightError("Click failed")

        execution_context.set_variable("preserved_var", "should_remain")
        execution_context.set_variable("__browser_page__", mock_page_with_failures)

        node = ClickElementNode("test_click")
        node.config["selector"] = "#button"

        await node.execute(execution_context)

        # Verify context state preserved
        assert execution_context.get_variable("preserved_var") == "should_remain"
        # Verify node status updated
        assert node.status == NodeStatus.ERROR


# ============================================================================
# Edge Case Tests
# ============================================================================

class TestEdgeCases:
    """Test edge case scenarios."""

    @pytest.mark.asyncio
    async def test_empty_selector(self, execution_context, mock_page_with_failures):
        """Test handling of empty selector."""
        from casare_rpa.nodes.browser_nodes import ClickElementNode

        node = ClickElementNode("test_click")
        node.config["selector"] = ""
        execution_context.set_variable("__browser_page__", mock_page_with_failures)

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_invalid_url_format(self, execution_context, mock_page_with_failures):
        """Test handling of invalid URL format."""
        from casare_rpa.nodes.browser_nodes import GoToURLNode

        mock_page_with_failures.goto.side_effect = PlaywrightError("Invalid URL")

        node = GoToURLNode("test_goto")
        node.config["url"] = "not-a-valid-url"
        execution_context.set_variable("__browser_page__", mock_page_with_failures)

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_very_long_selector(self, execution_context, mock_page_with_failures):
        """Test handling of very long selector string."""
        from casare_rpa.nodes.browser_nodes import ClickElementNode

        long_selector = "#element" + " > div" * 100

        node = ClickElementNode("test_click")
        node.config["selector"] = long_selector
        execution_context.set_variable("__browser_page__", mock_page_with_failures)

        # Should not crash, should handle gracefully
        result = await node.execute(execution_context)

        # Either succeeds or fails gracefully
        assert "success" in result
