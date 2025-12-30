"""
UI Panels Module.

Reusable panel components for the CasareRPA Canvas application.
All panels are designed to be dockable and follow consistent UI patterns.

UX Helpers (panel_ux_helpers.py) provide shared components:
- EmptyStateWidget: Guidance when panels have no data
- StatusBadge: Color-coded status indicators
- ToolbarButton: Consistent toolbar buttons
- SectionHeader: Visual section separators
- Stylesheet helpers for tables and toolbars
"""

from casare_rpa.presentation.canvas.ui.panels.analytics_panel import AnalyticsPanel
from casare_rpa.presentation.canvas.ui.panels.audit_panel import AuditPanel
from casare_rpa.presentation.canvas.ui.panels.bottom_panel_dock import BottomPanelDock
from casare_rpa.presentation.canvas.ui.panels.breakpoints_panel import BreakpointsPanel
from casare_rpa.presentation.canvas.ui.panels.browser_recording_panel import (
    BrowserRecordingPanel,
)
from casare_rpa.presentation.canvas.ui.panels.credentials_panel import CredentialsPanel
from casare_rpa.presentation.canvas.ui.panels.history_tab import HistoryTab
from casare_rpa.presentation.canvas.ui.panels.log_tab import LogTab
from casare_rpa.presentation.canvas.ui.panels.log_viewer_panel import LogViewerPanel
from casare_rpa.presentation.canvas.ui.panels.minimap_panel import (
    MinimapChangeTracker,
    MinimapPanel,
)
from casare_rpa.presentation.canvas.ui.panels.output_tab import OutputTab
from casare_rpa.presentation.canvas.ui.panels.properties_panel import PropertiesPanel

# UX Helper components for consistent panel styling
from casare_rpa.presentation.canvas.ui.panels.panel_ux_helpers import (
    EmptyStateWidget,
    SectionHeader,
    StatusBadge,
    ToolbarButton,
    create_context_menu,
    get_panel_table_stylesheet,
    get_panel_toolbar_stylesheet,
)
from casare_rpa.presentation.canvas.ui.panels.port_legend_panel import PortLegendPanel
from casare_rpa.presentation.canvas.ui.panels.process_mining_panel import (
    ProcessMiningPanel,
)
from casare_rpa.presentation.canvas.ui.panels.project_explorer_panel import (
    ProjectExplorerPanel,
)
from casare_rpa.presentation.canvas.ui.panels.recorded_actions_panel import (
    RecordedActionsPanel,
)
from casare_rpa.presentation.canvas.ui.panels.robot_picker_panel import RobotPickerPanel
from casare_rpa.presentation.canvas.ui.panels.side_panel_dock import SidePanelDock
from casare_rpa.presentation.canvas.ui.panels.terminal_tab import TerminalTab

# TriggersTab removed - triggers are now visual nodes
from casare_rpa.presentation.canvas.ui.panels.validation_tab import ValidationTab
from casare_rpa.presentation.canvas.ui.panels.variables_panel import (
    TYPE_DEFAULTS,
    VARIABLE_TYPES,
    VariablesPanel,
)

__all__ = [
    # Panels
    "VariablesPanel",
    "MinimapPanel",
    "BottomPanelDock",
    "SidePanelDock",
    "LogViewerPanel",
    "ProcessMiningPanel",
    "AnalyticsPanel",
    "RobotPickerPanel",
    "BrowserRecordingPanel",
    "PortLegendPanel",
    "CredentialsPanel",
    "ProjectExplorerPanel",
    "BreakpointsPanel",
    "AuditPanel",
    "RecordedActionsPanel",
    "PropertiesPanel",
    # Tabs
    "HistoryTab",
    "LogTab",
    "OutputTab",
    "TerminalTab",
    "ValidationTab",
    # UX Helpers
    "EmptyStateWidget",
    "StatusBadge",
    "ToolbarButton",
    "SectionHeader",
    "get_panel_table_stylesheet",
    "get_panel_toolbar_stylesheet",
    "create_context_menu",
    # Supporting Classes
    "MinimapChangeTracker",
    # Constants
    "VARIABLE_TYPES",
    "TYPE_DEFAULTS",
]
