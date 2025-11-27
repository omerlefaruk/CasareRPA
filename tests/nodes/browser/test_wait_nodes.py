"""
Tests for wait/synchronization nodes.

Tests WaitNode, WaitForElementNode, WaitForNavigationNode.
Validates timing, element state detection, and navigation wait conditions.
"""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock
import asyncio


class TestWaitNode:
    """Tests for WaitNode - fixed time delay."""

    @pytest.mark.asyncio
    async def test_wait_success(self, execution_context):
        """Test successful wait with default duration."""
        from casare_rpa.nodes.wait_nodes import WaitNode

        node = WaitNode(node_id="test_wait", duration=0.01)
        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["duration"] == 0.01
        assert "exec_out" in result["next_nodes"]

    @pytest.mark.asyncio
    async def test_wait_from_input(self, execution_context):
        """Test wait with duration from input port."""
        from casare_rpa.nodes.wait_nodes import WaitNode

        # Test wait with a short duration using config
        node = WaitNode(node_id="test_input", config={"duration": 0.02})
        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["duration"] == 0.02

    @pytest.mark.asyncio
    async def test_wait_string_duration(self, execution_context):
        """Test wait with string duration (auto-converted)."""
        from casare_rpa.nodes.wait_nodes import WaitNode

        node = WaitNode(node_id="test_string", config={"duration": "0.01"})
        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["duration"] == 0.01

    @pytest.mark.asyncio
    async def test_wait_zero_duration(self, execution_context):
        """Test wait with zero duration (instant)."""
        from casare_rpa.nodes.wait_nodes import WaitNode

        node = WaitNode(node_id="test_zero", duration=0)
        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["duration"] == 0

    @pytest.mark.asyncio
    async def test_wait_negative_duration_fails(self, execution_context):
        """Test wait with negative duration fails."""
        from casare_rpa.nodes.wait_nodes import WaitNode

        node = WaitNode(node_id="test_negative", duration=-1)
        result = await node.execute(execution_context)

        assert result["success"] is False
        assert (
            "negative" in result["error"].lower()
            or "non-negative" in result["error"].lower()
        )

    def test_validate_config_negative(self):
        """Test config validation rejects negative duration."""
        from casare_rpa.nodes.wait_nodes import WaitNode

        node = WaitNode(node_id="test_validate", duration=-5)
        is_valid, error = node._validate_config()

        assert is_valid is False
        assert "negative" in error.lower() or "non-negative" in error.lower()

    def test_validate_config_valid(self):
        """Test config validation accepts valid duration."""
        from casare_rpa.nodes.wait_nodes import WaitNode

        node = WaitNode(node_id="test_valid", duration=5)
        is_valid, error = node._validate_config()

        assert is_valid is True


class TestWaitForElementNode:
    """Tests for WaitForElementNode - element appearance wait."""

    @pytest.mark.asyncio
    async def test_wait_element_visible(self, execution_context, mock_page):
        """Test wait for visible element."""
        from casare_rpa.nodes.wait_nodes import WaitForElementNode

        mock_element = MagicMock()
        mock_page.wait_for_selector = AsyncMock(return_value=mock_element)
        execution_context.get_active_page = MagicMock(return_value=mock_page)

        node = WaitForElementNode(
            node_id="test_visible", selector="#loading-done", state="visible"
        )
        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["found"] is True
        assert result["data"]["state"] == "visible"
        assert "exec_out" in result["next_nodes"]

    @pytest.mark.asyncio
    async def test_wait_element_hidden(self, execution_context, mock_page):
        """Test wait for element to become hidden."""
        from casare_rpa.nodes.wait_nodes import WaitForElementNode

        mock_page.wait_for_selector = AsyncMock(return_value=None)
        execution_context.get_active_page = MagicMock(return_value=mock_page)

        node = WaitForElementNode(
            node_id="test_hidden", selector="#spinner", state="hidden"
        )
        result = await node.execute(execution_context)

        assert result["success"] is True
        call_kwargs = mock_page.wait_for_selector.call_args[1]
        assert call_kwargs["state"] == "hidden"

    @pytest.mark.asyncio
    async def test_wait_element_attached(self, execution_context, mock_page):
        """Test wait for element to be attached to DOM."""
        from casare_rpa.nodes.wait_nodes import WaitForElementNode

        mock_page.wait_for_selector = AsyncMock(return_value=MagicMock())
        execution_context.get_active_page = MagicMock(return_value=mock_page)

        node = WaitForElementNode(
            node_id="test_attached", selector="#dynamic-content", state="attached"
        )
        result = await node.execute(execution_context)

        assert result["success"] is True
        call_kwargs = mock_page.wait_for_selector.call_args[1]
        assert call_kwargs["state"] == "attached"

    @pytest.mark.asyncio
    async def test_wait_element_detached(self, execution_context, mock_page):
        """Test wait for element to be removed from DOM."""
        from casare_rpa.nodes.wait_nodes import WaitForElementNode

        mock_page.wait_for_selector = AsyncMock(return_value=None)
        execution_context.get_active_page = MagicMock(return_value=mock_page)

        node = WaitForElementNode(
            node_id="test_detached", selector="#removed-item", state="detached"
        )
        result = await node.execute(execution_context)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_wait_element_timeout(self, execution_context, mock_page):
        """Test wait times out when element not found."""
        from casare_rpa.nodes.wait_nodes import WaitForElementNode

        mock_page.wait_for_selector = AsyncMock(side_effect=Exception("Timeout"))
        execution_context.get_active_page = MagicMock(return_value=mock_page)

        node = WaitForElementNode(
            node_id="test_timeout", selector="#never-appears", timeout=100
        )
        result = await node.execute(execution_context)

        assert result["success"] is False
        assert result["data"]["found"] is False

    @pytest.mark.asyncio
    async def test_wait_element_xpath(self, execution_context, mock_page):
        """Test wait with XPath selector."""
        from casare_rpa.nodes.wait_nodes import WaitForElementNode

        mock_page.wait_for_selector = AsyncMock(return_value=MagicMock())
        execution_context.get_active_page = MagicMock(return_value=mock_page)

        node = WaitForElementNode(
            node_id="test_xpath", selector="//div[@class='result']"
        )
        result = await node.execute(execution_context)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_wait_element_no_page(self, execution_context_no_page):
        """Test wait fails without active page."""
        from casare_rpa.nodes.wait_nodes import WaitForElementNode

        node = WaitForElementNode(node_id="test_no_page", selector="#element")
        result = await node.execute(execution_context_no_page)

        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_wait_element_no_selector(self, execution_context, mock_page):
        """Test wait fails without selector."""
        from casare_rpa.nodes.wait_nodes import WaitForElementNode

        execution_context.get_active_page = MagicMock(return_value=mock_page)

        node = WaitForElementNode(node_id="test_no_selector", selector="")
        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "selector" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_wait_element_outputs_found(self, execution_context, mock_page):
        """Test that found output is set correctly."""
        from casare_rpa.nodes.wait_nodes import WaitForElementNode

        mock_page.wait_for_selector = AsyncMock(return_value=MagicMock())
        execution_context.get_active_page = MagicMock(return_value=mock_page)

        node = WaitForElementNode(node_id="test_found", selector="#exists")
        result = await node.execute(execution_context)

        assert result["success"] is True
        # Check output port
        found_output = node.output_ports.get("found")
        if found_output:
            assert found_output.value is True

    def test_validate_config_invalid_state(self):
        """Test config validation rejects invalid state."""
        from casare_rpa.nodes.wait_nodes import WaitForElementNode

        node = WaitForElementNode(node_id="test_invalid", selector="#elem")
        node.config["state"] = "invalid_state"
        is_valid, error = node._validate_config()

        assert is_valid is False
        assert "invalid_state" in error.lower() or "state" in error.lower()


class TestWaitForNavigationNode:
    """Tests for WaitForNavigationNode - page load wait."""

    @pytest.mark.asyncio
    async def test_wait_navigation_load(self, execution_context, mock_page):
        """Test wait for load event."""
        from casare_rpa.nodes.wait_nodes import WaitForNavigationNode

        mock_page.wait_for_load_state = AsyncMock()
        mock_page.url = "https://example.com/loaded"
        execution_context.get_active_page = MagicMock(return_value=mock_page)

        node = WaitForNavigationNode(node_id="test_load", wait_until="load")
        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["url"] == "https://example.com/loaded"
        assert result["data"]["wait_until"] == "load"
        assert "exec_out" in result["next_nodes"]

    @pytest.mark.asyncio
    async def test_wait_navigation_domcontentloaded(self, execution_context, mock_page):
        """Test wait for DOMContentLoaded event."""
        from casare_rpa.nodes.wait_nodes import WaitForNavigationNode

        mock_page.wait_for_load_state = AsyncMock()
        mock_page.url = "https://example.com"
        execution_context.get_active_page = MagicMock(return_value=mock_page)

        node = WaitForNavigationNode(node_id="test_dom", wait_until="domcontentloaded")
        result = await node.execute(execution_context)

        assert result["success"] is True
        mock_page.wait_for_load_state.assert_called_with(
            "domcontentloaded", timeout=30000
        )

    @pytest.mark.asyncio
    async def test_wait_navigation_networkidle(self, execution_context, mock_page):
        """Test wait for networkidle state."""
        from casare_rpa.nodes.wait_nodes import WaitForNavigationNode

        mock_page.wait_for_load_state = AsyncMock()
        mock_page.url = "https://example.com"
        execution_context.get_active_page = MagicMock(return_value=mock_page)

        node = WaitForNavigationNode(node_id="test_network", wait_until="networkidle")
        result = await node.execute(execution_context)

        assert result["success"] is True
        mock_page.wait_for_load_state.assert_called_with("networkidle", timeout=30000)

    @pytest.mark.asyncio
    async def test_wait_navigation_with_timeout(self, execution_context, mock_page):
        """Test wait navigation with custom timeout."""
        from casare_rpa.nodes.wait_nodes import WaitForNavigationNode

        mock_page.wait_for_load_state = AsyncMock()
        mock_page.url = "https://example.com"
        execution_context.get_active_page = MagicMock(return_value=mock_page)

        node = WaitForNavigationNode(
            node_id="test_timeout", timeout=60000, wait_until="load"
        )
        result = await node.execute(execution_context)

        assert result["success"] is True
        mock_page.wait_for_load_state.assert_called_with("load", timeout=60000)

    @pytest.mark.asyncio
    async def test_wait_navigation_timeout_error(self, execution_context, mock_page):
        """Test wait navigation timeout handling."""
        from casare_rpa.nodes.wait_nodes import WaitForNavigationNode

        mock_page.wait_for_load_state = AsyncMock(
            side_effect=Exception("Navigation timeout")
        )
        execution_context.get_active_page = MagicMock(return_value=mock_page)

        node = WaitForNavigationNode(node_id="test_fail", timeout=100)
        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_wait_navigation_no_page(self, execution_context_no_page):
        """Test wait navigation fails without active page."""
        from casare_rpa.nodes.wait_nodes import WaitForNavigationNode

        node = WaitForNavigationNode(node_id="test_no_page")
        result = await node.execute(execution_context_no_page)

        assert result["success"] is False

    def test_validate_config_valid_wait_until(self):
        """Test config validation accepts valid wait_until values."""
        from casare_rpa.nodes.wait_nodes import WaitForNavigationNode

        for wait_until in ["load", "domcontentloaded", "networkidle"]:
            node = WaitForNavigationNode(node_id="test", wait_until=wait_until)
            is_valid, error = node._validate_config()
            assert is_valid is True, f"Failed for wait_until={wait_until}"

    def test_validate_config_invalid_wait_until(self):
        """Test config validation rejects invalid wait_until."""
        from casare_rpa.nodes.wait_nodes import WaitForNavigationNode

        node = WaitForNavigationNode(node_id="test")
        node.config["wait_until"] = "invalid"
        is_valid, error = node._validate_config()

        assert is_valid is False
        assert "invalid" in error.lower()
