"""
MainWindow component extractors.

This package contains extracted components from MainWindow to reduce
its size and improve maintainability:

- ActionManager: QAction creation and hotkey management (~250 lines)
- MenuBuilder: Menu bar construction (~70 lines)
- ToolbarBuilder: Toolbar construction (~60 lines)
- StatusBarManager: Status bar updates (~100 lines)
- DockCreator: Dock widget creation (~100 lines)
"""

from .action_manager import ActionManager
from .menu_builder import MenuBuilder
from .toolbar_builder import ToolbarBuilder
from .status_bar_manager import StatusBarManager
from .dock_creator import DockCreator

__all__ = [
    "ActionManager",
    "MenuBuilder",
    "ToolbarBuilder",
    "StatusBarManager",
    "DockCreator",
]
