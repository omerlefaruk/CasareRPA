"""
Dockable Panel Components for CasareRPA Canvas.
"""

from .bottom_panel_dock import BottomPanelDock
from .properties_panel import PropertiesPanel
from .debug_toolbar import DebugToolbar
from .variable_inspector_dock import VariableInspectorDock

__all__ = [
    "BottomPanelDock",
    "PropertiesPanel",
    "DebugToolbar",
    "VariableInspectorDock",
]
