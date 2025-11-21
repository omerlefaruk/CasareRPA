"""
CasareRPA - GUI Package
Contains PySide6 UI components and windows.
"""

__version__ = "0.1.0"

from .app import CasareRPAApp, main
from .main_window import MainWindow
from .node_graph_widget import NodeGraphWidget

__all__ = [
    "CasareRPAApp",
    "main",
    "MainWindow",
    "NodeGraphWidget",
]
# from .properties_panel import PropertiesPanel
# from .log_viewer import LogViewer

__all__ = [
    "__version__",
    # GUI classes will be added here in Phase 3
]
