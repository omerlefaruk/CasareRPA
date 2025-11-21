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
]
