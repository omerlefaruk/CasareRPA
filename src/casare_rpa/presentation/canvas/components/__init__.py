"""
MainWindow component extractors.

This package contains extracted components from MainWindow to reduce
its size and improve maintainability:

- ActionManager: QAction creation and hotkey management (~250 lines)
- MenuBuilder: Menu bar construction (~70 lines)
- ToolbarBuilder: Toolbar construction (~60 lines)
- StatusBarManager: Status bar updates (~100 lines)
- DockCreator: Dock widget creation (~100 lines)
- FleetDashboardManager: Fleet dashboard dialog operations (~500 lines)
"""

from casare_rpa.presentation.canvas.components.action_manager import ActionManager
from casare_rpa.presentation.canvas.components.menu_builder import MenuBuilder
from casare_rpa.presentation.canvas.components.toolbar_builder import ToolbarBuilder
from casare_rpa.presentation.canvas.components.status_bar_manager import (
    StatusBarManager,
)
from casare_rpa.presentation.canvas.components.dock_creator import DockCreator
from casare_rpa.presentation.canvas.components.fleet_dashboard_manager import (
    FleetDashboardManager,
)

__all__ = [
    "ActionManager",
    "MenuBuilder",
    "ToolbarBuilder",
    "StatusBarManager",
    "DockCreator",
    "FleetDashboardManager",
]
