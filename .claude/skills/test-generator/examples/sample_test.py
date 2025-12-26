"""
Example test file for CasareRPA node.

This demonstrates a complete test suite for a browser automation node.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from casare_rpa.domain.value_objects import DataType, ExecutionResult
from casare_rpa.nodes.browser.click_node import ClickNode


@pytest.fixture
def node():
    """Create ClickNode instance."""
    return ClickNode()


@pytest.fixture
def mock_context():
    """Create mock execution context with test data."""
    context = MagicMock()
    context.get_variable = MagicMock(
        side_effect=lambda x: {
            "selector": "#submit-button",
            "timeout": 30000,
        }.get(x)
    )
    context.set_variable = MagicMock()
    return context


@pytest.fixture
def mock_page():
    """Create mock Playwright page."""
    page = AsyncMock()
    page.click = AsyncMock()
    page.wait_for_selector = AsyncMock()
    page.wait_for_load_state = AsyncMock()
    return page


class TestClickNode:
    """Comprehensive test suite for ClickNode."""

    # Initialization Tests

    def test_initialization(self, node):
        """Test node initializes with correct properties."""
        assert node.id == "click"
        assert node.name == "Click"
        assert node.category == "browser"

    def test_has_correct_input_ports(self, node):
        """Test node has all required input ports with correct types."""
        assert "selector" in node.inputs
        assert node.inputs["selector"].data_type == DataType.STRING
        assert "timeout" in node.inputs
        assert node.inputs["timeout"].data_type == DataType.INTEGER

    def test_has_correct_output_ports(self, node):
        """Test node has all required output ports."""
        assert "success" in node.outputs
        assert node.outputs["success"].data_type == DataType.BOOLEAN

    # Execution Tests - Success Cases

    @pytest.mark.asyncio
    async def test_execute_success(self, node, mock_context, mock_page):
        """Test successful execution returns ExecutionResult."""
        with patch("casare_rpa.nodes.browser.browser_base.BrowserResourceManager") as mock_mgr:
            mock_mgr.get_page.return_value = mock_page
            mock_context.resources = {"browser": mock_mgr}

            result = await node.execute(mock_context)

            assert isinstance(result, ExecutionResult)
            assert result.success is True
            assert "success" in result.output

    @pytest.mark.asyncio
    async def test_execute_with_valid_input(self, node, mock_context, mock_page):
        """Test execution with valid input produces expected output."""
        with patch("casare_rpa.nodes.browser.browser_base.BrowserResourceManager") as mock_mgr:
            mock_mgr.get_page.return_value = mock_page
            mock_context.resources = {"browser": mock_mgr}

            result = await node.execute(mock_context)

            mock_page.click.assert_called_once_with("#submit-button")
            assert result.success is True

    # Execution Tests - Error Cases

    @pytest.mark.asyncio
    async def test_execute_with_missing_input(self, node, mock_context):
        """Test execution fails gracefully when input is missing."""
        mock_context.get_variable.return_value = None

        result = await node.execute(mock_context)

        assert result.success is False
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_execute_with_invalid_input_type(self, node, mock_context):
        """Test execution fails with appropriate error for invalid input type."""
        mock_context.get_variable.return_value = 12345

        result = await node.execute(mock_context)

        assert result.success is False
        assert "type" in result.error.lower() or "invalid" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_handles_exception(self, node, mock_context, mock_page):
        """Test execution catches and handles exceptions properly."""
        mock_page.click.side_effect = RuntimeError("Element not found")
        with patch("casare_rpa.nodes.browser.browser_base.BrowserResourceManager") as mock_mgr:
            mock_mgr.get_page.return_value = mock_page
            mock_context.resources = {"browser": mock_mgr}

            result = await node.execute(mock_context)

            assert result.success is False
            assert "Element not found" in result.error

    # Edge Cases

    @pytest.mark.asyncio
    async def test_execute_with_empty_string(self, node, mock_context):
        """Test execution handles empty string input."""
        mock_context.get_variable.return_value = ""

        result = await node.execute(mock_context)

        assert isinstance(result, ExecutionResult)

    @pytest.mark.asyncio
    async def test_execute_with_special_characters(self, node, mock_context, mock_page):
        """Test execution handles special characters in selector."""
        mock_context.get_variable.return_value = "button[data-test-id='submit-btn']"
        with patch("casare_rpa.nodes.browser.browser_base.BrowserResourceManager") as mock_mgr:
            mock_mgr.get_page.return_value = mock_page
            mock_context.resources = {"browser": mock_mgr}

            result = await node.execute(mock_context)

            assert result.success is True
            mock_page.click.assert_called_once()

    # Logging Tests

    @pytest.mark.asyncio
    async def test_execute_logs_info_on_success(self, node, mock_context, mock_page, caplog):
        """Test successful execution logs info message."""
        with patch("casare_rpa.nodes.browser.browser_base.BrowserResourceManager") as mock_mgr:
            mock_mgr.get_page.return_value = mock_page
            mock_context.resources = {"browser": mock_mgr}

            result = await node.execute(mock_context)

            assert result.success is True
            assert any("completed" in record.message.lower() for record in caplog.records)

    @pytest.mark.asyncio
    async def test_execute_logs_error_on_failure(self, node, mock_context, mock_page, caplog):
        """Test failed execution logs error message."""
        mock_page.click.side_effect = ValueError("Test error")
        with patch("casare_rpa.nodes.browser.browser_base.BrowserResourceManager") as mock_mgr:
            mock_mgr.get_page.return_value = mock_page
            mock_context.resources = {"browser": mock_mgr}

            result = await node.execute(mock_context)

            assert result.success is False
            assert any(record.levelname == "ERROR" for record in caplog.records)
