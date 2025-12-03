"""
UI Panels Module.

Reusable panel components for the CasareRPA Canvas application.
All panels are designed to be dockable and follow consistent UI patterns.
"""

from casare_rpa.presentation.canvas.ui.panels.properties_panel import (
    PropertiesPanel,
    CollapsibleSection,
)
from casare_rpa.presentation.canvas.ui.panels.variables_panel import (
    VariablesPanel,
    VARIABLE_TYPES,
    TYPE_DEFAULTS,
)
from casare_rpa.presentation.canvas.ui.panels.minimap_panel import (
    MinimapPanel,
    MinimapChangeTracker,
)
from casare_rpa.presentation.canvas.ui.panels.bottom_panel_dock import BottomPanelDock
from casare_rpa.presentation.canvas.ui.panels.history_tab import HistoryTab
from casare_rpa.presentation.canvas.ui.panels.log_tab import LogTab
from casare_rpa.presentation.canvas.ui.panels.output_tab import OutputTab
from casare_rpa.presentation.canvas.ui.panels.log_viewer_panel import LogViewerPanel
from casare_rpa.presentation.canvas.ui.panels.process_mining_panel import (
    ProcessMiningPanel,
)
from casare_rpa.presentation.canvas.ui.panels.analytics_panel import AnalyticsPanel
from casare_rpa.presentation.canvas.ui.panels.robot_picker_panel import RobotPickerPanel

# TriggersTab removed - triggers are now visual nodes
from casare_rpa.presentation.canvas.ui.panels.validation_tab import ValidationTab

__all__ = [
    # Panels
    "PropertiesPanel",
    "VariablesPanel",
    "MinimapPanel",
    "BottomPanelDock",
    "LogViewerPanel",
    "ProcessMiningPanel",
    "AnalyticsPanel",
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
