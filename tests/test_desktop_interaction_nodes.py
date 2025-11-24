"""
Unit tests for Desktop Advanced Interaction Nodes

Tests SelectFromDropdownNode, CheckCheckboxNode, SelectRadioButtonNode,
SelectTabNode, ExpandTreeItemNode, ScrollElementNode
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from casare_rpa.nodes.desktop_nodes import (
    SelectFromDropdownNode,
    CheckCheckboxNode,
    SelectRadioButtonNode,
    SelectTabNode,
    ExpandTreeItemNode,
    ScrollElementNode,
)
from casare_rpa.desktop import DesktopContext, DesktopElement
from casare_rpa.core.execution_context import ExecutionContext
from casare_rpa.core.types import NodeStatus


class MockDesktopElement:
    """Mock DesktopElement for testing"""
    def __init__(self, name="MockElement"):
        self._control = Mock()
        self._control.Name = name
        self._control.ControlTypeName = "MockControl"

    def get_text(self):
        return self._control.Name

    def click(self, simulate=False, x_offset=0, y_offset=0):
        return True

    def exists(self):
        return True


class TestSelectFromDropdownNode:
    """Test suite for SelectFromDropdownNode"""

    def test_node_initialization(self):
        """Test that node initializes correctly"""
        node = SelectFromDropdownNode("dropdown_1", name="Select Dropdown")
        assert node.node_id == "dropdown_1"
        assert node.name == "Select Dropdown"
        assert node.node_type == "SelectFromDropdownNode"

    def test_default_config(self):
        """Test default configuration"""
        node = SelectFromDropdownNode("dropdown_2")
        assert node.config.get("by_text") is True

    @pytest.mark.asyncio
    async def test_missing_element_raises_error(self):
        """Test that missing element raises ValueError"""
        node = SelectFromDropdownNode("dropdown_3")
        context = ExecutionContext()

        node.set_input_value("value", "Option 1")

        with pytest.raises(ValueError, match="Dropdown element is required"):
            await node.execute(context)

    @pytest.mark.asyncio
    async def test_missing_value_raises_error(self):
        """Test that missing value raises ValueError"""
        node = SelectFromDropdownNode("dropdown_4")
        context = ExecutionContext()

        mock_element = MockDesktopElement()
        node.set_input_value("element", mock_element)

        with pytest.raises(ValueError, match="Value to select is required"):
            await node.execute(context)

    @pytest.mark.asyncio
    async def test_successful_selection_with_mock(self):
        """Test successful selection using mocked context"""
        node = SelectFromDropdownNode("dropdown_5", config={"by_text": True})
        context = ExecutionContext()

        mock_element = MockDesktopElement("Dropdown")
        node.set_input_value("element", mock_element)
        node.set_input_value("value", "Option 1")

        # Mock the desktop context
        mock_desktop_ctx = Mock(spec=DesktopContext)
        mock_desktop_ctx.select_from_dropdown.return_value = True
        context.desktop_context = mock_desktop_ctx

        result = await node.execute(context)

        assert result['success'] is True
        assert node.status == NodeStatus.SUCCESS
        mock_desktop_ctx.select_from_dropdown.assert_called_once()


class TestCheckCheckboxNode:
    """Test suite for CheckCheckboxNode"""

    def test_node_initialization(self):
        """Test that node initializes correctly"""
        node = CheckCheckboxNode("checkbox_1", name="Check Box")
        assert node.node_id == "checkbox_1"
        assert node.name == "Check Box"
        assert node.node_type == "CheckCheckboxNode"

    def test_default_config(self):
        """Test default configuration"""
        node = CheckCheckboxNode("checkbox_2")
        assert node.config.get("check") is True

    @pytest.mark.asyncio
    async def test_missing_element_raises_error(self):
        """Test that missing element raises ValueError"""
        node = CheckCheckboxNode("checkbox_3")
        context = ExecutionContext()

        with pytest.raises(ValueError, match="Checkbox element is required"):
            await node.execute(context)

    @pytest.mark.asyncio
    async def test_check_checkbox_with_mock(self):
        """Test checking checkbox using mocked context"""
        node = CheckCheckboxNode("checkbox_4", config={"check": True})
        context = ExecutionContext()

        mock_element = MockDesktopElement("Checkbox")
        node.set_input_value("element", mock_element)

        mock_desktop_ctx = Mock(spec=DesktopContext)
        mock_desktop_ctx.check_checkbox.return_value = True
        context.desktop_context = mock_desktop_ctx

        result = await node.execute(context)

        assert result['success'] is True
        assert node.status == NodeStatus.SUCCESS
        mock_desktop_ctx.check_checkbox.assert_called_once_with(mock_element, check=True)

    @pytest.mark.asyncio
    async def test_uncheck_checkbox_with_mock(self):
        """Test unchecking checkbox using mocked context"""
        node = CheckCheckboxNode("checkbox_5", config={"check": False})
        context = ExecutionContext()

        mock_element = MockDesktopElement("Checkbox")
        node.set_input_value("element", mock_element)

        mock_desktop_ctx = Mock(spec=DesktopContext)
        mock_desktop_ctx.check_checkbox.return_value = True
        context.desktop_context = mock_desktop_ctx

        result = await node.execute(context)

        assert result['success'] is True
        mock_desktop_ctx.check_checkbox.assert_called_once_with(mock_element, check=False)


class TestSelectRadioButtonNode:
    """Test suite for SelectRadioButtonNode"""

    def test_node_initialization(self):
        """Test that node initializes correctly"""
        node = SelectRadioButtonNode("radio_1", name="Select Radio")
        assert node.node_id == "radio_1"
        assert node.name == "Select Radio"
        assert node.node_type == "SelectRadioButtonNode"

    @pytest.mark.asyncio
    async def test_missing_element_raises_error(self):
        """Test that missing element raises ValueError"""
        node = SelectRadioButtonNode("radio_2")
        context = ExecutionContext()

        with pytest.raises(ValueError, match="Radio button element is required"):
            await node.execute(context)

    @pytest.mark.asyncio
    async def test_select_radio_with_mock(self):
        """Test selecting radio button using mocked context"""
        node = SelectRadioButtonNode("radio_3")
        context = ExecutionContext()

        mock_element = MockDesktopElement("RadioButton")
        node.set_input_value("element", mock_element)

        mock_desktop_ctx = Mock(spec=DesktopContext)
        mock_desktop_ctx.select_radio_button.return_value = True
        context.desktop_context = mock_desktop_ctx

        result = await node.execute(context)

        assert result['success'] is True
        assert node.status == NodeStatus.SUCCESS
        mock_desktop_ctx.select_radio_button.assert_called_once_with(mock_element)


class TestSelectTabNode:
    """Test suite for SelectTabNode"""

    def test_node_initialization(self):
        """Test that node initializes correctly"""
        node = SelectTabNode("tab_1", name="Select Tab")
        assert node.node_id == "tab_1"
        assert node.name == "Select Tab"
        assert node.node_type == "SelectTabNode"

    def test_default_config(self):
        """Test default configuration"""
        node = SelectTabNode("tab_2")
        assert node.config.get("tab_name") == ""
        assert node.config.get("tab_index") == -1

    @pytest.mark.asyncio
    async def test_missing_tab_control_raises_error(self):
        """Test that missing tab control raises ValueError"""
        node = SelectTabNode("tab_3")
        context = ExecutionContext()

        node.set_input_value("tab_name", "Tab 1")

        with pytest.raises(ValueError, match="Tab control element is required"):
            await node.execute(context)

    @pytest.mark.asyncio
    async def test_missing_tab_identifier_raises_error(self):
        """Test that missing tab name and index raises ValueError"""
        node = SelectTabNode("tab_4")
        context = ExecutionContext()

        mock_element = MockDesktopElement("TabControl")
        node.set_input_value("tab_control", mock_element)

        with pytest.raises(ValueError, match="Must provide either tab_name or tab_index"):
            await node.execute(context)

    @pytest.mark.asyncio
    async def test_select_tab_by_name_with_mock(self):
        """Test selecting tab by name using mocked context"""
        node = SelectTabNode("tab_5")
        context = ExecutionContext()

        mock_element = MockDesktopElement("TabControl")
        node.set_input_value("tab_control", mock_element)
        node.set_input_value("tab_name", "Settings")

        mock_desktop_ctx = Mock(spec=DesktopContext)
        mock_desktop_ctx.select_tab.return_value = True
        context.desktop_context = mock_desktop_ctx

        result = await node.execute(context)

        assert result['success'] is True
        assert node.status == NodeStatus.SUCCESS
        mock_desktop_ctx.select_tab.assert_called_once_with(mock_element, tab_name="Settings", tab_index=None)

    @pytest.mark.asyncio
    async def test_select_tab_by_index_with_mock(self):
        """Test selecting tab by index using mocked context"""
        node = SelectTabNode("tab_6", config={"tab_index": 2})
        context = ExecutionContext()

        mock_element = MockDesktopElement("TabControl")
        node.set_input_value("tab_control", mock_element)

        mock_desktop_ctx = Mock(spec=DesktopContext)
        mock_desktop_ctx.select_tab.return_value = True
        context.desktop_context = mock_desktop_ctx

        result = await node.execute(context)

        assert result['success'] is True
        mock_desktop_ctx.select_tab.assert_called_once_with(mock_element, tab_name=None, tab_index=2)


class TestExpandTreeItemNode:
    """Test suite for ExpandTreeItemNode"""

    def test_node_initialization(self):
        """Test that node initializes correctly"""
        node = ExpandTreeItemNode("tree_1", name="Expand Tree")
        assert node.node_id == "tree_1"
        assert node.name == "Expand Tree"
        assert node.node_type == "ExpandTreeItemNode"

    def test_default_config(self):
        """Test default configuration"""
        node = ExpandTreeItemNode("tree_2")
        assert node.config.get("expand") is True

    @pytest.mark.asyncio
    async def test_missing_element_raises_error(self):
        """Test that missing element raises ValueError"""
        node = ExpandTreeItemNode("tree_3")
        context = ExecutionContext()

        with pytest.raises(ValueError, match="Tree item element is required"):
            await node.execute(context)

    @pytest.mark.asyncio
    async def test_expand_tree_item_with_mock(self):
        """Test expanding tree item using mocked context"""
        node = ExpandTreeItemNode("tree_4", config={"expand": True})
        context = ExecutionContext()

        mock_element = MockDesktopElement("TreeItem")
        node.set_input_value("element", mock_element)

        mock_desktop_ctx = Mock(spec=DesktopContext)
        mock_desktop_ctx.expand_tree_item.return_value = True
        context.desktop_context = mock_desktop_ctx

        result = await node.execute(context)

        assert result['success'] is True
        assert node.status == NodeStatus.SUCCESS
        mock_desktop_ctx.expand_tree_item.assert_called_once_with(mock_element, expand=True)

    @pytest.mark.asyncio
    async def test_collapse_tree_item_with_mock(self):
        """Test collapsing tree item using mocked context"""
        node = ExpandTreeItemNode("tree_5", config={"expand": False})
        context = ExecutionContext()

        mock_element = MockDesktopElement("TreeItem")
        node.set_input_value("element", mock_element)

        mock_desktop_ctx = Mock(spec=DesktopContext)
        mock_desktop_ctx.expand_tree_item.return_value = True
        context.desktop_context = mock_desktop_ctx

        result = await node.execute(context)

        assert result['success'] is True
        mock_desktop_ctx.expand_tree_item.assert_called_once_with(mock_element, expand=False)


class TestScrollElementNode:
    """Test suite for ScrollElementNode"""

    def test_node_initialization(self):
        """Test that node initializes correctly"""
        node = ScrollElementNode("scroll_1", name="Scroll Element")
        assert node.node_id == "scroll_1"
        assert node.name == "Scroll Element"
        assert node.node_type == "ScrollElementNode"

    def test_default_config(self):
        """Test default configuration"""
        node = ScrollElementNode("scroll_2")
        assert node.config.get("direction") == "down"
        assert node.config.get("amount") == 0.5

    @pytest.mark.asyncio
    async def test_missing_element_raises_error(self):
        """Test that missing element raises ValueError"""
        node = ScrollElementNode("scroll_3")
        context = ExecutionContext()

        with pytest.raises(ValueError, match="Element to scroll is required"):
            await node.execute(context)

    @pytest.mark.asyncio
    async def test_scroll_down_with_mock(self):
        """Test scrolling down using mocked context"""
        node = ScrollElementNode("scroll_4", config={"direction": "down", "amount": 0.5})
        context = ExecutionContext()

        mock_element = MockDesktopElement("ScrollableList")
        node.set_input_value("element", mock_element)

        mock_desktop_ctx = Mock(spec=DesktopContext)
        mock_desktop_ctx.scroll_element.return_value = True
        context.desktop_context = mock_desktop_ctx

        result = await node.execute(context)

        assert result['success'] is True
        assert node.status == NodeStatus.SUCCESS
        mock_desktop_ctx.scroll_element.assert_called_once_with(mock_element, direction="down", amount=0.5)

    @pytest.mark.asyncio
    async def test_scroll_up_with_mock(self):
        """Test scrolling up using mocked context"""
        node = ScrollElementNode("scroll_5", config={"direction": "up", "amount": 0.3})
        context = ExecutionContext()

        mock_element = MockDesktopElement("ScrollableList")
        node.set_input_value("element", mock_element)

        mock_desktop_ctx = Mock(spec=DesktopContext)
        mock_desktop_ctx.scroll_element.return_value = True
        context.desktop_context = mock_desktop_ctx

        result = await node.execute(context)

        assert result['success'] is True
        mock_desktop_ctx.scroll_element.assert_called_once_with(mock_element, direction="up", amount=0.3)

    @pytest.mark.asyncio
    async def test_scroll_left_with_mock(self):
        """Test scrolling left using mocked context"""
        node = ScrollElementNode("scroll_6", config={"direction": "left", "amount": 0.2})
        context = ExecutionContext()

        mock_element = MockDesktopElement("ScrollableList")
        node.set_input_value("element", mock_element)

        mock_desktop_ctx = Mock(spec=DesktopContext)
        mock_desktop_ctx.scroll_element.return_value = True
        context.desktop_context = mock_desktop_ctx

        result = await node.execute(context)

        assert result['success'] is True
        mock_desktop_ctx.scroll_element.assert_called_once_with(mock_element, direction="left", amount=0.2)

    @pytest.mark.asyncio
    async def test_scroll_right_with_mock(self):
        """Test scrolling right using mocked context"""
        node = ScrollElementNode("scroll_7", config={"direction": "right", "amount": 0.8})
        context = ExecutionContext()

        mock_element = MockDesktopElement("ScrollableList")
        node.set_input_value("element", mock_element)

        mock_desktop_ctx = Mock(spec=DesktopContext)
        mock_desktop_ctx.scroll_element.return_value = True
        context.desktop_context = mock_desktop_ctx

        result = await node.execute(context)

        assert result['success'] is True
        mock_desktop_ctx.scroll_element.assert_called_once_with(mock_element, direction="right", amount=0.8)
