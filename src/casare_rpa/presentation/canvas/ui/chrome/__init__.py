"""
Chrome v2 Package - ActionManager, Toolbar, Menu Bar, and Status Bar for NewMainWindow.

Epic 1.2: ActionManagerV2 - Centralized Action/Shortcut Management
- ActionManagerV2: 64+ actions with persistent shortcuts
- ActionCategory: Batch enable/disable by category

Epic 2.1: Menu Bar Integration
- MenuBarV2: standard menu structure (File, Edit, View, Run, Tools, Help)

Epic 4.2: Chrome - Top Toolbar + Status Bar v2
- ToolbarV2: Primary actions (New, Open, Save, Undo/Redo, Run/Stop)
- StatusBarV2: Execution status, zoom display

All components use THEME_V2 styling and IconProviderV2 icons.

Usage:
    from casare_rpa.presentation.canvas.ui.chrome import (
        ActionManagerV2, ActionCategory,
        MenuBarV2, ToolbarV2, StatusBarV2
    )

    # Action manager
    action_manager = ActionManagerV2(main_window)
    action_manager.register_all_actions()

    # UI components
    toolbar = ToolbarV2(parent=self)
    status_bar = StatusBarV2(parent=self)

See: docs/UX_REDESIGN_PLAN.md Phase 4 Epic 1.2, Epic 2.1, Epic 4.2
"""

from casare_rpa.presentation.canvas.ui.chrome.action_manager_v2 import (
    ActionCategory,
    ActionManagerV2,
    get_action,
)
from casare_rpa.presentation.canvas.ui.chrome.menubar_v2 import MenuBarV2
from casare_rpa.presentation.canvas.ui.chrome.statusbar_v2 import StatusBarV2
from casare_rpa.presentation.canvas.ui.chrome.toolbar_v2 import ToolbarV2

__all__ = [
    "ActionCategory",
    "ActionManagerV2",
    "MenuBarV2",
    "StatusBarV2",
    "ToolbarV2",
    "get_action",
]
