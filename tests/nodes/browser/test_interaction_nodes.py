"""
Tests for interaction nodes.

Tests ClickElementNode, TypeTextNode, SelectDropdownNode.
Validates element interaction, selector handling, and error handling.
"""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock


class TestClickElementNode:
    """Tests for ClickElementNode - element click interactions."""

    @pytest.mark.asyncio
    async def test_click_success(self, execution_context, mock_page):
        """Test successful element click."""
        from casare_rpa.nodes.interaction_nodes import ClickElementNode

        mock_page.click = AsyncMock()
        execution_context.get_active_page = MagicMock(return_value=mock_page)

        node = ClickElementNode(
            node_id="test_click", selector="#submit-button", timeout=5000
        )
        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["selector"] == "#submit-button"
        assert "exec_out" in result["next_nodes"]
        mock_page.click.assert_called_once()

    @pytest.mark.asyncio
    async def test_click_css_selector(self, execution_context, mock_page):
        """Test click with CSS selector."""
        from casare_rpa.nodes.interaction_nodes import ClickElementNode

        mock_page.click = AsyncMock()
        execution_context.get_active_page = MagicMock(return_value=mock_page)

        node = ClickElementNode(node_id="test_css", selector=".btn-primary")
        result = await node.execute(execution_context)

        assert result["success"] is True
        call_args = mock_page.click.call_args[0]
        assert ".btn-primary" in call_args[0]

    @pytest.mark.asyncio
    async def test_click_xpath_selector(self, execution_context, mock_page):
        """Test click with XPath selector."""
        from casare_rpa.nodes.interaction_nodes import ClickElementNode

        mock_page.click = AsyncMock()
        execution_context.get_active_page = MagicMock(return_value=mock_page)

        node = ClickElementNode(
            node_id="test_xpath", selector="//button[@type='submit']"
        )
        result = await node.execute(execution_context)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_click_double_click(self, execution_context, mock_page):
        """Test double click with click_count=2."""
        from casare_rpa.nodes.interaction_nodes import ClickElementNode

        mock_page.click = AsyncMock()
        execution_context.get_active_page = MagicMock(return_value=mock_page)

        node = ClickElementNode(
            node_id="test_double",
            config={"selector": "#item", "click_count": 2, "timeout": 5000},
        )
        result = await node.execute(execution_context)

        assert result["success"] is True
        call_kwargs = mock_page.click.call_args[1]
        assert call_kwargs.get("click_count") == 2

    @pytest.mark.asyncio
    async def test_click_right_button(self, execution_context, mock_page):
        """Test right-click with button='right'."""
        from casare_rpa.nodes.interaction_nodes import ClickElementNode

        mock_page.click = AsyncMock()
        execution_context.get_active_page = MagicMock(return_value=mock_page)

        node = ClickElementNode(
            node_id="test_right",
            config={"selector": "#context-menu", "button": "right", "timeout": 5000},
        )
        result = await node.execute(execution_context)

        assert result["success"] is True
        call_kwargs = mock_page.click.call_args[1]
        assert call_kwargs.get("button") == "right"

    @pytest.mark.asyncio
    async def test_click_no_page(self, execution_context_no_page):
        """Test click fails without active page."""
        from casare_rpa.nodes.interaction_nodes import ClickElementNode

        node = ClickElementNode(node_id="test_no_page", selector="#button")
        result = await node.execute(execution_context_no_page)

        assert result["success"] is False
        assert "page" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_click_no_selector(self, execution_context, mock_page):
        """Test click fails without selector."""
        from casare_rpa.nodes.interaction_nodes import ClickElementNode

        execution_context.get_active_page = MagicMock(return_value=mock_page)

        node = ClickElementNode(node_id="test_no_selector", selector="")
        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "selector" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_click_element_not_found(self, execution_context, mock_page):
        """Test click fails when element not found."""
        from casare_rpa.nodes.interaction_nodes import ClickElementNode

        mock_page.click = AsyncMock(side_effect=Exception("Element not found"))
        execution_context.get_active_page = MagicMock(return_value=mock_page)

        node = ClickElementNode(node_id="test_not_found", selector="#nonexistent")
        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_click_with_force(self, execution_context, mock_page):
        """Test force click bypasses actionability checks."""
        from casare_rpa.nodes.interaction_nodes import ClickElementNode

        mock_page.click = AsyncMock()
        execution_context.get_active_page = MagicMock(return_value=mock_page)

        node = ClickElementNode(
            node_id="test_force",
            config={"selector": "#hidden-button", "force": True, "timeout": 5000},
        )
        result = await node.execute(execution_context)

        assert result["success"] is True
        call_kwargs = mock_page.click.call_args[1]
        assert call_kwargs.get("force") is True


class TestTypeTextNode:
    """Tests for TypeTextNode - text input interactions."""

    @pytest.mark.asyncio
    async def test_type_text_success(self, execution_context, mock_page):
        """Test successful text typing."""
        from casare_rpa.nodes.interaction_nodes import TypeTextNode

        mock_page.fill = AsyncMock()
        execution_context.get_active_page = MagicMock(return_value=mock_page)

        node = TypeTextNode(node_id="test_type", selector="#username", text="testuser")
        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["text_length"] == 8
        assert "exec_out" in result["next_nodes"]

    @pytest.mark.asyncio
    async def test_type_text_with_delay(self, execution_context, mock_page):
        """Test typing with keystroke delay."""
        from casare_rpa.nodes.interaction_nodes import TypeTextNode

        mock_page.fill = AsyncMock()
        mock_page.type = AsyncMock()
        execution_context.get_active_page = MagicMock(return_value=mock_page)

        node = TypeTextNode(
            node_id="test_delay",
            config={
                "selector": "#input",
                "text": "slow",
                "delay": 100,
                "timeout": 5000,
            },
        )
        result = await node.execute(execution_context)

        assert result["success"] is True
        mock_page.type.assert_called()

    @pytest.mark.asyncio
    async def test_type_text_press_enter(self, execution_context, mock_page):
        """Test typing with Enter key press after."""
        from casare_rpa.nodes.interaction_nodes import TypeTextNode

        mock_page.fill = AsyncMock()
        mock_page.keyboard = MagicMock()
        mock_page.keyboard.press = AsyncMock()
        execution_context.get_active_page = MagicMock(return_value=mock_page)

        node = TypeTextNode(
            node_id="test_enter",
            config={
                "selector": "#search",
                "text": "query",
                "press_enter_after": True,
                "timeout": 5000,
            },
        )
        result = await node.execute(execution_context)

        assert result["success"] is True
        mock_page.keyboard.press.assert_called_with("Enter")

    @pytest.mark.asyncio
    async def test_type_text_press_tab(self, execution_context, mock_page):
        """Test typing with Tab key press after."""
        from casare_rpa.nodes.interaction_nodes import TypeTextNode

        mock_page.fill = AsyncMock()
        mock_page.keyboard = MagicMock()
        mock_page.keyboard.press = AsyncMock()
        execution_context.get_active_page = MagicMock(return_value=mock_page)

        node = TypeTextNode(
            node_id="test_tab",
            config={
                "selector": "#field1",
                "text": "value",
                "press_tab_after": True,
                "timeout": 5000,
            },
        )
        result = await node.execute(execution_context)

        assert result["success"] is True
        mock_page.keyboard.press.assert_called_with("Tab")

    @pytest.mark.asyncio
    async def test_type_text_no_page(self, execution_context_no_page):
        """Test typing fails without active page."""
        from casare_rpa.nodes.interaction_nodes import TypeTextNode

        node = TypeTextNode(node_id="test_no_page", selector="#input", text="test")
        result = await node.execute(execution_context_no_page)

        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_type_text_no_selector(self, execution_context, mock_page):
        """Test typing fails without selector."""
        from casare_rpa.nodes.interaction_nodes import TypeTextNode

        execution_context.get_active_page = MagicMock(return_value=mock_page)

        node = TypeTextNode(node_id="test_no_selector", selector="", text="test")
        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "selector" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_type_text_empty_string(self, execution_context, mock_page):
        """Test typing empty string (clears field)."""
        from casare_rpa.nodes.interaction_nodes import TypeTextNode

        mock_page.fill = AsyncMock()
        execution_context.get_active_page = MagicMock(return_value=mock_page)

        node = TypeTextNode(node_id="test_empty", selector="#input", text="")
        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["text_length"] == 0


class TestSelectDropdownNode:
    """Tests for SelectDropdownNode - dropdown selection."""

    @pytest.mark.asyncio
    async def test_select_by_value(self, execution_context, mock_page):
        """Test select option by value."""
        from casare_rpa.nodes.interaction_nodes import SelectDropdownNode

        mock_page.select_option = AsyncMock()
        execution_context.get_active_page = MagicMock(return_value=mock_page)

        node = SelectDropdownNode(node_id="test_value", selector="#country", value="US")
        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["value"] == "US"
        assert result["data"]["select_by"] == "value"
        mock_page.select_option.assert_called()

    @pytest.mark.asyncio
    async def test_select_by_label(self, execution_context, mock_page):
        """Test select option by label."""
        from casare_rpa.nodes.interaction_nodes import SelectDropdownNode

        mock_page.select_option = AsyncMock()
        execution_context.get_active_page = MagicMock(return_value=mock_page)

        node = SelectDropdownNode(
            node_id="test_label",
            config={
                "selector": "#country",
                "value": "United States",
                "select_by": "label",
                "timeout": 5000,
            },
        )
        result = await node.execute(execution_context)

        assert result["success"] is True
        call_kwargs = mock_page.select_option.call_args[1]
        assert "label" in call_kwargs

    @pytest.mark.asyncio
    async def test_select_by_index(self, execution_context, mock_page):
        """Test select option by index."""
        from casare_rpa.nodes.interaction_nodes import SelectDropdownNode

        mock_page.select_option = AsyncMock()
        execution_context.get_active_page = MagicMock(return_value=mock_page)

        node = SelectDropdownNode(
            node_id="test_index",
            config={
                "selector": "#options",
                "value": "2",
                "select_by": "index",
                "timeout": 5000,
            },
        )
        result = await node.execute(execution_context)

        assert result["success"] is True
        call_kwargs = mock_page.select_option.call_args[1]
        assert "index" in call_kwargs

    @pytest.mark.asyncio
    async def test_select_no_page(self, execution_context_no_page):
        """Test select fails without active page."""
        from casare_rpa.nodes.interaction_nodes import SelectDropdownNode

        node = SelectDropdownNode(
            node_id="test_no_page", selector="#select", value="opt1"
        )
        result = await node.execute(execution_context_no_page)

        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_select_no_selector(self, execution_context, mock_page):
        """Test select fails without selector."""
        from casare_rpa.nodes.interaction_nodes import SelectDropdownNode

        execution_context.get_active_page = MagicMock(return_value=mock_page)

        node = SelectDropdownNode(node_id="test_no_selector", selector="", value="opt1")
        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "selector" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_select_no_value(self, execution_context, mock_page):
        """Test select fails without value."""
        from casare_rpa.nodes.interaction_nodes import SelectDropdownNode

        execution_context.get_active_page = MagicMock(return_value=mock_page)

        node = SelectDropdownNode(node_id="test_no_value", selector="#select", value="")
        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "value" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_select_element_not_found(self, execution_context, mock_page):
        """Test select fails when element not found."""
        from casare_rpa.nodes.interaction_nodes import SelectDropdownNode

        mock_page.select_option = AsyncMock(side_effect=Exception("Element not found"))
        execution_context.get_active_page = MagicMock(return_value=mock_page)

        node = SelectDropdownNode(
            node_id="test_not_found", selector="#nonexistent", value="opt1"
        )
        result = await node.execute(execution_context)

        assert result["success"] is False
