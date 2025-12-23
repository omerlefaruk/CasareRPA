"""
Visual Super Nodes for Desktop Automation Operations.

Consolidated visual nodes that replace multiple atomic nodes
with a single action-driven interface.
"""

from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.nodes.desktop_nodes.window_super_node import (
    WINDOW_PORT_SCHEMA,
    WindowManagementSuperNode,
)
from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode
from casare_rpa.presentation.canvas.visual_nodes.mixins.super_node_mixin import (
    SuperNodeMixin,
)


class VisualWindowManagementSuperNode(SuperNodeMixin, VisualNode):
    """
    Visual representation of WindowManagementSuperNode.

    Consolidates 7 window management operations into a single node:
    - Resize: Resize window to specified dimensions
    - Move: Move window to specified position
    - Maximize: Maximize window to fill screen
    - Minimize: Minimize window to taskbar
    - Restore: Restore window to normal state
    - Get Properties: Get window title, size, position, state
    - Set State: Set window state (normal/maximized/minimized)

    The action dropdown dynamically changes which properties and
    input/output ports are visible.
    """

    __identifier__ = "casare_rpa.desktop_automation"
    NODE_NAME = "Window Management"
    NODE_CATEGORY = "desktop/super"
    CASARE_NODE_CLASS = "WindowManagementSuperNode"

    # Dynamic port schema from domain layer
    DYNAMIC_PORT_SCHEMA = WINDOW_PORT_SCHEMA

    def __init__(self) -> None:
        super().__init__()
        # Enable port deletion for dynamic port management
        self.set_port_deletion_allowed(True)

    def get_node_class(self) -> type:
        """Return the domain node class."""
        return WindowManagementSuperNode

    def setup_ports(self) -> None:
        """
        Setup initial ports for the default action (Resize).

        Ports are dynamically updated when the action dropdown changes.
        """
        # Exec ports (always present)
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")

        # Default ports for Resize action
        self.add_typed_input("window", DataType.ANY)
        self.add_typed_input("width", DataType.INTEGER)
        self.add_typed_input("height", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)

    def setup_widgets(self) -> None:
        """
        Setup widgets and connect action listener.

        The action listener triggers port refresh when the
        action dropdown selection changes.
        """
        super().setup_widgets()
        # Connect action dropdown to port refresh (from SuperNodeMixin)
        self._setup_action_listener()


__all__ = [
    "VisualWindowManagementSuperNode",
]
