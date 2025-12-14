"""
Visual Super Nodes for File Operations.

Consolidated visual nodes that replace multiple atomic nodes
with a single action-driven interface.
"""

from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode
from casare_rpa.presentation.canvas.visual_nodes.mixins.super_node_mixin import (
    SuperNodeMixin,
)
from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.nodes.file.super_node import (
    FileSystemSuperNode,
    FileSystemAction,
    FILE_SYSTEM_PORT_SCHEMA,
    StructuredDataSuperNode,
    StructuredDataAction,
    STRUCTURED_DATA_PORT_SCHEMA,
)


class VisualFileSystemSuperNode(SuperNodeMixin, VisualNode):
    """
    Visual representation of FileSystemSuperNode.

    Consolidates 12 file system operations into a single node:
    - Read File, Write File, Append File
    - Delete File, Copy File, Move File
    - File Exists, Get File Size, Get File Info
    - Create Directory, List Files, List Directory

    The action dropdown dynamically changes which properties and
    input/output ports are visible.
    """

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "File System"
    NODE_CATEGORY = "file_operations/super"
    CASARE_NODE_CLASS = "FileSystemSuperNode"

    # Dynamic port schema from domain layer
    DYNAMIC_PORT_SCHEMA = FILE_SYSTEM_PORT_SCHEMA

    def __init__(self) -> None:
        super().__init__()
        # Enable port deletion for dynamic port management
        self.set_port_deletion_allowed(True)

    def get_node_class(self) -> type:
        """Return the domain node class."""
        return FileSystemSuperNode

    def setup_ports(self) -> None:
        """
        Setup initial ports for the default action (Read File).

        Ports are dynamically updated when the action dropdown changes.
        """
        # Exec ports (always present)
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")

        # Default ports for Read File action
        self.add_typed_input("file_path", DataType.STRING)
        self.add_typed_output("content", DataType.STRING)
        self.add_typed_output("size", DataType.INTEGER)
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


class VisualStructuredDataSuperNode(SuperNodeMixin, VisualNode):
    """
    Visual representation of StructuredDataSuperNode.

    Consolidates 7 structured data operations into a single node:
    - Read CSV, Write CSV
    - Read JSON, Write JSON
    - Zip Files, Unzip Files
    - Image Convert

    The action dropdown dynamically changes which properties and
    input/output ports are visible.
    """

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "Structured Data"
    NODE_CATEGORY = "file_operations/super"
    CASARE_NODE_CLASS = "StructuredDataSuperNode"

    # Dynamic port schema from domain layer
    DYNAMIC_PORT_SCHEMA = STRUCTURED_DATA_PORT_SCHEMA

    def __init__(self) -> None:
        super().__init__()
        # Enable port deletion for dynamic port management
        self.set_port_deletion_allowed(True)

    def get_node_class(self) -> type:
        """Return the domain node class."""
        return StructuredDataSuperNode

    def setup_ports(self) -> None:
        """
        Setup initial ports for the default action (Read CSV).

        Ports are dynamically updated when the action dropdown changes.
        """
        # Exec ports (always present)
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")

        # Default ports for Read CSV action
        self.add_typed_input("file_path", DataType.STRING)
        self.add_typed_output("data", DataType.LIST)
        self.add_typed_output("headers", DataType.LIST)
        self.add_typed_output("row_count", DataType.INTEGER)
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
    "VisualFileSystemSuperNode",
    "VisualStructuredDataSuperNode",
]
