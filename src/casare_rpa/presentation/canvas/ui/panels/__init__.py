"""
UI Panels Module.

Reusable panel components for the CasareRPA Canvas application.
All panels are designed to be dockable and follow consistent UI patterns.
"""

from .properties_panel import PropertiesPanel, CollapsibleSection
from .debug_panel import DebugPanel
from .variables_panel import VariablesPanel, VARIABLE_TYPES, TYPE_DEFAULTS
from .minimap_panel import MinimapPanel, MinimapChangeTracker
from .bottom_panel_dock import BottomPanelDock
from .history_tab import HistoryTab
from .log_tab import LogTab
from .output_tab import OutputTab
from .log_viewer_panel import LogViewerPanel
from .process_mining_panel import ProcessMiningPanel
from .robot_picker_panel import RobotPickerPanel

# TriggersTab removed - triggers are now visual nodes
from .validation_tab import ValidationTab

__all__ = [
    # Panels
    "PropertiesPanel",
    "DebugPanel",
    "VariablesPanel",
    "MinimapPanel",
    "BottomPanelDock",
    "LogViewerPanel",
    "ProcessMiningPanel",
    "RobotPickerPanel",
    # Tabs
    "HistoryTab",
    "LogTab",
    "OutputTab",
    "ValidationTab",
    # Supporting Classes
    "CollapsibleSection",
    "MinimapChangeTracker",
    # Constants
    "VARIABLE_TYPES",
    "TYPE_DEFAULTS",
]
