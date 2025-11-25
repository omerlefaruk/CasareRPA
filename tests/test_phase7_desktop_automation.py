"""
Phase 7: Windows Desktop Automation Tests

Tests for:
1. Desktop Context (Bite 1) - Foundation
2. Application Management Nodes (Bite 2) - Launch, Close, Activate, GetWindowList
3. Element Interaction Nodes (Bite 3) - Find, Click, Type, GetText, GetProperty
4. Desktop Selector (Bite 4) - Selector parsing and validation
5. Window Management (Bite 5) - Resize, Move, Maximize, Minimize, GetProperties
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path


class TestDesktopContext:
    """Tests for DesktopContext foundation (Bite 1)."""

    def test_desktop_context_creation(self):
        """Test DesktopContext instantiation."""
        from casare_rpa.desktop.context import DesktopContext

        ctx = DesktopContext()

        assert ctx is not None

    def test_desktop_context_has_launch_application(self):
        """Test DesktopContext has launch_application method."""
        from casare_rpa.desktop.context import DesktopContext

        ctx = DesktopContext()

        assert hasattr(ctx, "launch_application")
        assert callable(ctx.launch_application)

    def test_desktop_context_has_find_window(self):
        """Test DesktopContext has find_window method."""
        from casare_rpa.desktop.context import DesktopContext

        ctx = DesktopContext()

        assert hasattr(ctx, "find_window")
        assert callable(ctx.find_window)

    def test_desktop_context_has_close_application(self):
        """Test DesktopContext has close_application method."""
        from casare_rpa.desktop.context import DesktopContext

        ctx = DesktopContext()

        assert hasattr(ctx, "close_application")
        assert callable(ctx.close_application)

    def test_desktop_context_has_get_all_windows(self):
        """Test DesktopContext has get_all_windows method."""
        from casare_rpa.desktop.context import DesktopContext

        ctx = DesktopContext()

        assert hasattr(ctx, "get_all_windows")
        assert callable(ctx.get_all_windows)


class TestDesktopElement:
    """Tests for DesktopElement wrapper (Bite 1)."""

    def test_desktop_element_module_exists(self):
        """Test DesktopElement module exists."""
        from casare_rpa.desktop import element

        assert element is not None

    def test_desktop_element_class_exists(self):
        """Test DesktopElement class exists."""
        from casare_rpa.desktop.element import DesktopElement

        assert DesktopElement is not None


class TestDesktopSelector:
    """Tests for Desktop Selector system (Bite 4)."""

    def test_desktop_selector_module_exists(self):
        """Test desktop selector module exists."""
        from casare_rpa.desktop import selector

        assert selector is not None

    def test_selector_has_parse_function(self):
        """Test selector module has parse_selector function."""
        from casare_rpa.desktop.selector import parse_selector

        assert parse_selector is not None
        assert callable(parse_selector)

    def test_selector_has_find_element_function(self):
        """Test selector module has find_element function."""
        from casare_rpa.desktop.selector import find_element

        assert find_element is not None
        assert callable(find_element)

    def test_selector_has_find_elements_function(self):
        """Test selector module has find_elements function."""
        from casare_rpa.desktop.selector import find_elements

        assert find_elements is not None
        assert callable(find_elements)


class TestApplicationManagementNodes:
    """Tests for Application Management Nodes (Bite 2)."""

    def test_launch_application_node_exists(self):
        """Test LaunchApplicationNode exists."""
        from casare_rpa.nodes.desktop_nodes import LaunchApplicationNode

        node = LaunchApplicationNode("launch_1")

        assert node.node_id == "launch_1"
        assert node.node_type == "LaunchApplicationNode"

    def test_launch_application_node_ports(self):
        """Test LaunchApplicationNode has correct ports."""
        from casare_rpa.nodes.desktop_nodes import LaunchApplicationNode

        node = LaunchApplicationNode("launch_1")

        assert "application_path" in node.input_ports
        assert "arguments" in node.input_ports
        assert "window" in node.output_ports
        assert "process_id" in node.output_ports

    def test_close_application_node_exists(self):
        """Test CloseApplicationNode exists."""
        from casare_rpa.nodes.desktop_nodes import CloseApplicationNode

        node = CloseApplicationNode("close_1")

        assert node.node_id == "close_1"
        assert node.node_type == "CloseApplicationNode"

    def test_close_application_node_ports(self):
        """Test CloseApplicationNode has correct ports."""
        from casare_rpa.nodes.desktop_nodes import CloseApplicationNode

        node = CloseApplicationNode("close_1")

        assert "window" in node.input_ports
        assert "process_id" in node.input_ports
        assert "success" in node.output_ports

    def test_activate_window_node_exists(self):
        """Test ActivateWindowNode exists."""
        from casare_rpa.nodes.desktop_nodes import ActivateWindowNode

        node = ActivateWindowNode("activate_1")

        assert node.node_id == "activate_1"
        assert node.node_type == "ActivateWindowNode"

    def test_activate_window_node_ports(self):
        """Test ActivateWindowNode has correct ports."""
        from casare_rpa.nodes.desktop_nodes import ActivateWindowNode

        node = ActivateWindowNode("activate_1")

        assert "window" in node.input_ports
        assert "window_title" in node.input_ports
        assert "success" in node.output_ports

    def test_get_window_list_node_exists(self):
        """Test GetWindowListNode exists."""
        from casare_rpa.nodes.desktop_nodes import GetWindowListNode

        node = GetWindowListNode("list_1")

        assert node.node_id == "list_1"
        assert node.node_type == "GetWindowListNode"

    def test_get_window_list_node_ports(self):
        """Test GetWindowListNode has correct ports."""
        from casare_rpa.nodes.desktop_nodes import GetWindowListNode

        node = GetWindowListNode("list_1")

        assert "window_list" in node.output_ports
        assert "window_count" in node.output_ports


class TestElementInteractionNodes:
    """Tests for Element Interaction Nodes (Bite 3)."""

    def test_find_element_node_exists(self):
        """Test FindElementNode exists."""
        from casare_rpa.nodes.desktop_nodes import FindElementNode

        node = FindElementNode("find_1")

        assert node.node_id == "find_1"

    def test_click_element_node_exists(self):
        """Test ClickElementNode exists."""
        from casare_rpa.nodes.desktop_nodes import ClickElementNode

        node = ClickElementNode("click_1")

        assert node.node_id == "click_1"

    def test_type_text_node_exists(self):
        """Test TypeTextNode exists."""
        from casare_rpa.nodes.desktop_nodes import TypeTextNode

        node = TypeTextNode("type_1")

        assert node.node_id == "type_1"

    def test_get_element_text_node_exists(self):
        """Test GetElementTextNode exists."""
        from casare_rpa.nodes.desktop_nodes import GetElementTextNode

        node = GetElementTextNode("text_1")

        assert node.node_id == "text_1"

    def test_get_element_property_node_exists(self):
        """Test GetElementPropertyNode exists."""
        from casare_rpa.nodes.desktop_nodes import GetElementPropertyNode

        node = GetElementPropertyNode("prop_1")

        assert node.node_id == "prop_1"


class TestNodeConfiguration:
    """Tests for node configuration options."""

    def test_launch_app_default_config(self):
        """Test LaunchApplicationNode has default config."""
        from casare_rpa.nodes.desktop_nodes import LaunchApplicationNode

        node = LaunchApplicationNode("launch_1")

        assert "timeout" in node.config
        assert node.config["timeout"] == 10.0

    def test_close_app_force_config(self):
        """Test CloseApplicationNode force close config."""
        from casare_rpa.nodes.desktop_nodes import CloseApplicationNode

        node = CloseApplicationNode("close_1", config={"force_close": True})

        assert node.config["force_close"] is True

    def test_activate_window_partial_match_config(self):
        """Test ActivateWindowNode partial match config."""
        from casare_rpa.nodes.desktop_nodes import ActivateWindowNode

        node = ActivateWindowNode("activate_1")

        assert "match_partial" in node.config
        assert node.config["match_partial"] is True

    def test_get_window_list_filter_config(self):
        """Test GetWindowListNode filter config."""
        from casare_rpa.nodes.desktop_nodes import GetWindowListNode

        node = GetWindowListNode("list_1", config={"filter_title": "Notepad"})

        assert node.config["filter_title"] == "Notepad"


class TestNodeExecution:
    """Tests for node execution (with mocked desktop context)."""

    @pytest.mark.asyncio
    async def test_launch_app_requires_path(self):
        """Test LaunchApplicationNode requires application_path."""
        from casare_rpa.nodes.desktop_nodes import LaunchApplicationNode
        from casare_rpa.core.execution_context import ExecutionContext

        context = ExecutionContext(workflow_name="test")
        node = LaunchApplicationNode("launch_1")

        # Should raise because no path provided
        with pytest.raises(ValueError, match="path is required"):
            await node.execute(context)

    @pytest.mark.asyncio
    async def test_close_app_requires_target(self):
        """Test CloseApplicationNode requires target."""
        from casare_rpa.nodes.desktop_nodes import CloseApplicationNode
        from casare_rpa.core.execution_context import ExecutionContext

        context = ExecutionContext(workflow_name="test")
        node = CloseApplicationNode("close_1")

        # Should raise because no window/pid/title provided
        with pytest.raises(ValueError, match="Must provide"):
            await node.execute(context)

    @pytest.mark.asyncio
    async def test_activate_window_requires_target(self):
        """Test ActivateWindowNode requires target."""
        from casare_rpa.nodes.desktop_nodes import ActivateWindowNode
        from casare_rpa.core.execution_context import ExecutionContext

        context = ExecutionContext(workflow_name="test")
        node = ActivateWindowNode("activate_1")

        # Should raise because no window/title provided
        with pytest.raises(ValueError, match="Must provide"):
            await node.execute(context)


class TestDesktopNodesExports:
    """Tests for desktop_nodes module exports."""

    def test_all_nodes_exported(self):
        """Test all desktop nodes are exported from module."""
        from casare_rpa.nodes import desktop_nodes

        expected_nodes = [
            "LaunchApplicationNode",
            "CloseApplicationNode",
            "ActivateWindowNode",
            "GetWindowListNode",
            "FindElementNode",
            "ClickElementNode",
            "TypeTextNode",
            "GetElementTextNode",
            "GetElementPropertyNode",
        ]

        for node_name in expected_nodes:
            assert hasattr(desktop_nodes, node_name), f"Missing: {node_name}"

    def test_desktop_nodes_in_all(self):
        """Test desktop nodes are in __all__."""
        from casare_rpa.nodes import desktop_nodes

        assert hasattr(desktop_nodes, "__all__")
        assert len(desktop_nodes.__all__) >= 9


class TestWindowManagementNodes:
    """Tests for Window Management Nodes (Bite 5 - To Be Implemented)."""

    @pytest.mark.skip(reason="Bite 5 not yet implemented")
    def test_resize_window_node_exists(self):
        """Test ResizeWindowNode exists."""
        from casare_rpa.nodes.desktop_nodes import ResizeWindowNode

        node = ResizeWindowNode("resize_1")
        assert node.node_id == "resize_1"

    @pytest.mark.skip(reason="Bite 5 not yet implemented")
    def test_move_window_node_exists(self):
        """Test MoveWindowNode exists."""
        from casare_rpa.nodes.desktop_nodes import MoveWindowNode

        node = MoveWindowNode("move_1")
        assert node.node_id == "move_1"

    @pytest.mark.skip(reason="Bite 5 not yet implemented")
    def test_maximize_window_node_exists(self):
        """Test MaximizeWindowNode exists."""
        from casare_rpa.nodes.desktop_nodes import MaximizeWindowNode

        node = MaximizeWindowNode("max_1")
        assert node.node_id == "max_1"

    @pytest.mark.skip(reason="Bite 5 not yet implemented")
    def test_minimize_window_node_exists(self):
        """Test MinimizeWindowNode exists."""
        from casare_rpa.nodes.desktop_nodes import MinimizeWindowNode

        node = MinimizeWindowNode("min_1")
        assert node.node_id == "min_1"

    @pytest.mark.skip(reason="Bite 5 not yet implemented")
    def test_restore_window_node_exists(self):
        """Test RestoreWindowNode exists."""
        from casare_rpa.nodes.desktop_nodes import RestoreWindowNode

        node = RestoreWindowNode("restore_1")
        assert node.node_id == "restore_1"

    @pytest.mark.skip(reason="Bite 5 not yet implemented")
    def test_get_window_properties_node_exists(self):
        """Test GetWindowPropertiesNode exists."""
        from casare_rpa.nodes.desktop_nodes import GetWindowPropertiesNode

        node = GetWindowPropertiesNode("props_1")
        assert node.node_id == "props_1"


class TestDesktopContextIntegration:
    """Tests for ExecutionContext integration with desktop."""

    def test_context_can_hold_desktop_context(self):
        """Test ExecutionContext can store desktop_context."""
        from casare_rpa.core.execution_context import ExecutionContext
        from casare_rpa.desktop.context import DesktopContext

        context = ExecutionContext(workflow_name="test")
        desktop_ctx = DesktopContext()

        context.desktop_context = desktop_ctx

        assert hasattr(context, "desktop_context")
        assert context.desktop_context is desktop_ctx
