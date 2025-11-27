"""
Integration tests for system nodes.

Tests all 13 system nodes to ensure proper logic-to-visual layer connections
and basic functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from casare_rpa.core.execution_context import ExecutionContext


class TestSystemNodesIntegration:
    """Integration tests for system category nodes."""

    @pytest.fixture
    def execution_context(self):
        """Create a mock execution context."""
        context = Mock(spec=ExecutionContext)
        context.resolve_value = lambda x: x
        context.variables = {}
        return context

    # =============================================================================
    # Clipboard Nodes
    # =============================================================================

    def test_clipboard_copy_node_integration(self, execution_context):
        """Test ClipboardCopyNode logic-to-visual connection."""
        from casare_rpa.nodes.system_nodes import ClipboardCopyNode
        from casare_rpa.presentation.canvas.visual_nodes.system import VisualClipboardCopyNode

        # Test visual node returns correct logic class
        visual_node = VisualClipboardCopyNode()
        logic_class = visual_node.get_node_class()
        assert logic_class == ClipboardCopyNode

        # Test node instantiation
        node = ClipboardCopyNode(node_id="test_clipboard_copy")
        assert node.node_type == "ClipboardCopyNode"
        assert hasattr(node, "execute")

    def test_clipboard_paste_node_integration(self, execution_context):
        """Test ClipboardPasteNode logic-to-visual connection."""
        from casare_rpa.nodes.system_nodes import ClipboardPasteNode
        from casare_rpa.presentation.canvas.visual_nodes.system import VisualClipboardPasteNode

        visual_node = VisualClipboardPasteNode()
        logic_class = visual_node.get_node_class()
        assert logic_class == ClipboardPasteNode

        node = ClipboardPasteNode(node_id="test_clipboard_paste")
        assert node.node_type == "ClipboardPasteNode"

    def test_clipboard_clear_node_integration(self, execution_context):
        """Test ClipboardClearNode logic-to-visual connection."""
        from casare_rpa.nodes.system_nodes import ClipboardClearNode
        from casare_rpa.presentation.canvas.visual_nodes.system import VisualClipboardClearNode

        visual_node = VisualClipboardClearNode()
        logic_class = visual_node.get_node_class()
        assert logic_class == ClipboardClearNode

        node = ClipboardClearNode(node_id="test_clipboard_clear")
        assert node.node_type == "ClipboardClearNode"

    # =============================================================================
    # Dialog Nodes
    # =============================================================================

    def test_messagebox_node_integration(self, execution_context):
        """Test MessageBoxNode logic-to-visual connection."""
        from casare_rpa.nodes.system_nodes import MessageBoxNode
        from casare_rpa.presentation.canvas.visual_nodes.system import VisualMessageBoxNode

        visual_node = VisualMessageBoxNode()
        logic_class = visual_node.get_node_class()
        assert logic_class == MessageBoxNode

        node = MessageBoxNode(node_id="test_messagebox")
        assert node.node_type == "MessageBoxNode"
        assert hasattr(node, "execute")

    def test_input_dialog_node_integration(self, execution_context):
        """Test InputDialogNode logic-to-visual connection."""
        from casare_rpa.nodes.system_nodes import InputDialogNode
        from casare_rpa.presentation.canvas.visual_nodes.system import VisualInputDialogNode

        visual_node = VisualInputDialogNode()
        logic_class = visual_node.get_node_class()
        assert logic_class == InputDialogNode

        node = InputDialogNode(node_id="test_input_dialog")
        assert node.node_type == "InputDialogNode"

    def test_tooltip_node_integration(self, execution_context):
        """Test TooltipNode logic-to-visual connection."""
        from casare_rpa.nodes.system_nodes import TooltipNode
        from casare_rpa.presentation.canvas.visual_nodes.system import VisualTooltipNode

        visual_node = VisualTooltipNode()
        logic_class = visual_node.get_node_class()
        assert logic_class == TooltipNode

        node = TooltipNode(node_id="test_tooltip")
        assert node.node_type == "TooltipNode"

    # =============================================================================
    # Command Nodes
    # =============================================================================

    @pytest.mark.asyncio
    async def test_run_command_node_integration(self, execution_context):
        """Test RunCommandNode logic-to-visual connection and basic execution."""
        from casare_rpa.nodes.system_nodes import RunCommandNode
        from casare_rpa.presentation.canvas.visual_nodes.system import VisualRunCommandNode

        visual_node = VisualRunCommandNode()
        logic_class = visual_node.get_node_class()
        assert logic_class == RunCommandNode

        # Test basic echo command
        node = RunCommandNode(node_id="test_run_command", config={"shell": True, "timeout": 5})
        node.set_input_value("command", "echo test")

        result = await node.execute(execution_context)
        assert result["success"] is True
        assert "test" in node.get_output_value("stdout")

    @pytest.mark.asyncio
    async def test_run_powershell_node_integration(self, execution_context):
        """Test RunPowerShellNode logic-to-visual connection and basic execution."""
        from casare_rpa.nodes.system_nodes import RunPowerShellNode
        from casare_rpa.presentation.canvas.visual_nodes.system import VisualRunPowerShellNode

        visual_node = VisualRunPowerShellNode()
        logic_class = visual_node.get_node_class()
        assert logic_class == RunPowerShellNode

        # Test basic PowerShell command
        node = RunPowerShellNode(node_id="test_powershell", config={"timeout": 5})
        node.set_input_value("script", "Write-Output 'test'")

        result = await node.execute(execution_context)
        assert result["success"] is True
        assert "test" in node.get_output_value("output")

    # =============================================================================
    # Service Nodes
    # =============================================================================

    def test_get_service_status_node_integration(self, execution_context):
        """Test GetServiceStatusNode logic-to-visual connection."""
        from casare_rpa.nodes.system_nodes import GetServiceStatusNode
        from casare_rpa.presentation.canvas.visual_nodes.system import VisualGetServiceStatusNode

        visual_node = VisualGetServiceStatusNode()
        logic_class = visual_node.get_node_class()
        assert logic_class == GetServiceStatusNode

        node = GetServiceStatusNode(node_id="test_get_service_status")
        assert node.node_type == "GetServiceStatusNode"

    def test_start_service_node_integration(self, execution_context):
        """Test StartServiceNode logic-to-visual connection."""
        from casare_rpa.nodes.system_nodes import StartServiceNode
        from casare_rpa.presentation.canvas.visual_nodes.system import VisualStartServiceNode

        visual_node = VisualStartServiceNode()
        logic_class = visual_node.get_node_class()
        assert logic_class == StartServiceNode

        node = StartServiceNode(node_id="test_start_service", config={"timeout": 30})
        assert node.node_type == "StartServiceNode"

    def test_stop_service_node_integration(self, execution_context):
        """Test StopServiceNode logic-to-visual connection."""
        from casare_rpa.nodes.system_nodes import StopServiceNode
        from casare_rpa.presentation.canvas.visual_nodes.system import VisualStopServiceNode

        visual_node = VisualStopServiceNode()
        logic_class = visual_node.get_node_class()
        assert logic_class == StopServiceNode

        node = StopServiceNode(node_id="test_stop_service", config={"timeout": 30})
        assert node.node_type == "StopServiceNode"

    def test_restart_service_node_integration(self, execution_context):
        """Test RestartServiceNode logic-to-visual connection."""
        from casare_rpa.nodes.system_nodes import RestartServiceNode
        from casare_rpa.presentation.canvas.visual_nodes.system import VisualRestartServiceNode

        visual_node = VisualRestartServiceNode()
        logic_class = visual_node.get_node_class()
        assert logic_class == RestartServiceNode

        node = RestartServiceNode(node_id="test_restart_service", config={"timeout": 60})
        assert node.node_type == "RestartServiceNode"

    def test_list_services_node_integration(self, execution_context):
        """Test ListServicesNode logic-to-visual connection."""
        from casare_rpa.nodes.system_nodes import ListServicesNode
        from casare_rpa.presentation.canvas.visual_nodes.system import VisualListServicesNode

        visual_node = VisualListServicesNode()
        logic_class = visual_node.get_node_class()
        assert logic_class == ListServicesNode

        node = ListServicesNode(node_id="test_list_services", config={"filter_status": "all"})
        assert node.node_type == "ListServicesNode"

    # =============================================================================
    # Port Configuration Tests
    # =============================================================================

    def test_all_visual_nodes_have_proper_ports(self):
        """Test that all system visual nodes have setup_ports method."""
        from casare_rpa.presentation.canvas.visual_nodes.system import (
            VisualClipboardCopyNode,
            VisualClipboardPasteNode,
            VisualClipboardClearNode,
            VisualMessageBoxNode,
            VisualInputDialogNode,
            VisualTooltipNode,
            VisualRunCommandNode,
            VisualRunPowerShellNode,
            VisualGetServiceStatusNode,
            VisualStartServiceNode,
            VisualStopServiceNode,
            VisualRestartServiceNode,
            VisualListServicesNode,
        )

        visual_nodes = [
            VisualClipboardCopyNode(),
            VisualClipboardPasteNode(),
            VisualClipboardClearNode(),
            VisualMessageBoxNode(),
            VisualInputDialogNode(),
            VisualTooltipNode(),
            VisualRunCommandNode(),
            VisualRunPowerShellNode(),
            VisualGetServiceStatusNode(),
            VisualStartServiceNode(),
            VisualStopServiceNode(),
            VisualRestartServiceNode(),
            VisualListServicesNode(),
        ]

        for visual_node in visual_nodes:
            assert hasattr(visual_node, "setup_ports"), f"{visual_node.__class__.__name__} missing setup_ports method"
            assert hasattr(visual_node, "get_node_class"), f"{visual_node.__class__.__name__} missing get_node_class method"


class TestSystemNodesNodeRegistry:
    """Test that all system nodes are properly registered."""

    def test_all_system_nodes_in_registry(self):
        """Test that all 13 system nodes are in the node registry."""
        from casare_rpa.nodes import _NODE_REGISTRY

        system_nodes = [
            "ClipboardCopyNode",
            "ClipboardPasteNode",
            "ClipboardClearNode",
            "MessageBoxNode",
            "InputDialogNode",
            "TooltipNode",
            "RunCommandNode",
            "RunPowerShellNode",
            "GetServiceStatusNode",
            "StartServiceNode",
            "StopServiceNode",
            "RestartServiceNode",
            "ListServicesNode",
        ]

        for node_name in system_nodes:
            assert node_name in _NODE_REGISTRY, f"{node_name} not in node registry"
            assert _NODE_REGISTRY[node_name] == "system_nodes", f"{node_name} registered to wrong module"
