"""
Visual Super Nodes for Text Operations.

Consolidated visual node that replaces 14 atomic text nodes
with a single action-driven interface.
"""

from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.nodes.text.super_node import (
    TEXT_PORT_SCHEMA,
    TextSuperNode,
)
from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode
from casare_rpa.presentation.canvas.visual_nodes.mixins.super_node_mixin import (
    SuperNodeMixin,
)


class VisualTextSuperNode(SuperNodeMixin, VisualNode):
    """
    Visual representation of TextSuperNode.

    Consolidates 14 text operations into a single node:

    Search:
        - Substring: Extract substring by index
        - Contains: Check if text contains substring
        - Starts With: Check if text starts with prefix
        - Ends With: Check if text ends with suffix
        - Extract (Regex): Extract text using regex pattern

    Transform:
        - Split: Split text into list
        - Replace: Replace occurrences in text
        - Trim: Trim whitespace or specified characters
        - Case: Change case (upper/lower/title/etc.)
        - Pad: Pad text to target length
        - Reverse: Reverse text
        - Lines: Split text into lines or join lines

    Analyze:
        - Count: Count characters, words, or lines
        - Join: Join list of items with separator

    The action dropdown dynamically changes which properties and
    input/output ports are visible.
    """

    __identifier__ = "casare_rpa.text_operations"
    NODE_NAME = "Text"
    NODE_CATEGORY = "text/super"
    CASARE_NODE_CLASS = "TextSuperNode"

    # Dynamic port schema from domain layer
    DYNAMIC_PORT_SCHEMA = TEXT_PORT_SCHEMA

    def __init__(self) -> None:
        super().__init__()
        # Enable port deletion for dynamic port management
        self.set_port_deletion_allowed(True)

    def get_node_class(self) -> type:
        """Return the domain node class."""
        return TextSuperNode

    def setup_ports(self) -> None:
        """
        Setup initial ports for the default action (Contains).

        Ports are dynamically updated when the action dropdown changes.
        """
        # Exec ports (always present)
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")

        # Default ports for Contains action
        self.add_typed_input("text", DataType.STRING)
        self.add_typed_input("search", DataType.STRING)
        self.add_typed_output("contains", DataType.BOOLEAN)
        self.add_typed_output("position", DataType.INTEGER)
        self.add_typed_output("count", DataType.INTEGER)

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
    "VisualTextSuperNode",
]
