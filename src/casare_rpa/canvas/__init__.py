"""
CasareRPA - GUI Package
Contains PySide6 UI components and windows.
"""

__version__ = "0.1.0"

from .app import CasareRPAApp, main
from .main_window import MainWindow
from .node_graph_widget import NodeGraphWidget
from .node_registry import (
    NodeRegistry,
    NodeFactory,
    get_node_registry,
    get_node_factory
)
from .visual_nodes import (
    VisualNode,
    VISUAL_NODE_CLASSES,
    NODE_COLORS
)
from .debug_toolbar import DebugToolbar
from .auto_connect import AutoConnectManager
from .connection_cutter import ConnectionCutter
from .minimap import Minimap
from .variable_inspector_dock import VariableInspectorDock

__all__ = [
    "__version__",
    "CasareRPAApp",
    "main",
    "MainWindow",
    "NodeGraphWidget",
    "NodeRegistry",
    "NodeFactory",
    "get_node_registry",
    "get_node_factory",
    "VisualNode",
    "VISUAL_NODE_CLASSES",
    "NODE_COLORS",
    "DebugToolbar",
    "AutoConnectManager",
    "ConnectionCutter",
    "Minimap",
    "VariableInspectorDock",
]
