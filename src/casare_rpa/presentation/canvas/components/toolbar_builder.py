"""
Toolbar builder for MainWindow toolbar.

Centralizes toolbar creation and styling.
"""

from typing import TYPE_CHECKING

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QToolBar

from casare_rpa.presentation.canvas.theme import THEME
from casare_rpa.presentation.canvas.theme_system import TOKENS
from casare_rpa.presentation.canvas.theme_system.helpers import set_margins, set_spacing
from casare_rpa.presentation.canvas.ui.icons import get_toolbar_icon

if TYPE_CHECKING:
    from casare_rpa.presentation.canvas.main_window import MainWindow


class ToolbarBuilder:
    """
    Builds the main toolbar for MainWindow.

    Responsibilities:
    - Create compact unified toolbar
    - Apply modern dark theme styling
    - Organize execution and automation controls
    """

    @staticmethod
    def _get_toolbar_style() -> str:
        """Generate theme-aware toolbar stylesheet."""
        return f"""
            QToolBar {{
                background: {THEME.bg_dark};
                border: none;
                spacing: {TOKENS.spacing.xs}px;
                padding: {TOKENS.spacing.xs}px {TOKENS.spacing.sm}px;
            }}
            QToolButton {{
                background: transparent;
                border: 1px solid transparent;
                border-radius: {TOKENS.radii.sm}px;
                padding: {TOKENS.spacing.xs}px {TOKENS.spacing.sm}px;
                color: {THEME.text_secondary};
                font-size: {TOKENS.fonts.sm}px;
            }}
            QToolButton:hover {{
                background: {THEME.bg_medium};
                border: 1px solid {THEME.border_light};
                color: {THEME.text_primary};
            }}
            QToolButton:pressed {{
                background: {THEME.accent_secondary};
            }}
            QToolButton:checked {{
                background: {THEME.selection};
                border: 1px solid {THEME.border_focus};
                color: {THEME.text_primary};
            }}
            QToolButton:disabled {{
                color: {THEME.text_disabled};
            }}
            QToolBar::separator {{
                background: {THEME.border_light};
                width: 1px;
                margin: {TOKENS.spacing.xs}px {TOKENS.spacing.sm}px;
            }}
        """

    def __init__(self, main_window: "MainWindow") -> None:
        """
        Initialize toolbar builder.

        Args:
            main_window: Parent MainWindow instance
        """
        self._main_window = main_window

    def _setup_toolbar_action(self, action, icon_name: str, text: str, tooltip: str = "") -> None:
        """Set icon, short text label, and tooltip for an action."""
        action.setIcon(get_toolbar_icon(icon_name))
        action.setIconText(text)
        if tooltip:
            action.setToolTip(tooltip)

    def create_toolbar(self) -> QToolBar:
        """
        Create unified compact toolbar with execution and debug controls.

        Returns:
            Created QToolBar instance
        """
        mw = self._main_window

        toolbar = QToolBar("Main Toolbar")
        toolbar.setObjectName("MainToolbar")
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        toolbar.setIconSize(QSize(TOKENS.sizes.icon_sm, TOKENS.sizes.icon_sm))
        toolbar.setStyleSheet(self._get_toolbar_style())

        # Set icons with short labels (text beside icon)
        self._setup_toolbar_action(mw.action_run, "run", "Run", "Run Workflow (F5)")
        self._setup_toolbar_action(mw.action_pause, "pause", "Pause", "Pause (F6)")
        self._setup_toolbar_action(mw.action_stop, "stop", "Stop", "Stop (Shift+F5)")
        self._setup_toolbar_action(mw.action_restart, "restart", "Restart")
        self._setup_toolbar_action(
            mw.action_reload, "reload", "Reload", "Reload Workflow (Ctrl+Shift+R)"
        )
        self._setup_toolbar_action(
            mw.action_record_workflow, "record", "Record", "Record Browser Actions"
        )
        self._setup_toolbar_action(
            mw.action_pick_selector, "pick_selector", "Pick", "Pick Element Selector"
        )
        self._setup_toolbar_action(
            mw.action_project_manager, "project", "Project", "Project Manager"
        )
        self._setup_toolbar_action(mw.action_fleet_dashboard, "fleet", "Fleet", "Fleet Dashboard")
        self._setup_toolbar_action(mw.action_save_layout, "layout", "Layout", "Save Layout")
        self._setup_toolbar_action(
            mw.action_performance_dashboard,
            "performance",
            "Perf",
            "Performance Dashboard",
        )
        self._setup_toolbar_action(
            mw.action_toggle_panel, "layout", "Bottom", "Toggle Bottom Panel (6)"
        )
        self._setup_toolbar_action(
            mw.action_toggle_side_panel, "layout", "Side", "Toggle Side Panel (7)"
        )

        # === Execution Controls ===
        toolbar.addAction(mw.action_run)
        toolbar.addAction(mw.action_pause)
        toolbar.addAction(mw.action_stop)
        toolbar.addAction(mw.action_restart)
        toolbar.addAction(mw.action_reload)

        toolbar.addSeparator()

        # === Automation Tools ===
        toolbar.addAction(mw.action_record_workflow)
        toolbar.addAction(mw.action_pick_selector)

        toolbar.addSeparator()

        # === Project & Management ===
        toolbar.addAction(mw.action_project_manager)
        toolbar.addAction(mw.action_credential_manager)
        toolbar.addSeparator()
        toolbar.addAction(mw.action_toggle_panel)
        toolbar.addAction(mw.action_toggle_side_panel)
        toolbar.addSeparator()
        toolbar.addAction(mw.action_fleet_dashboard)
        toolbar.addAction(mw.action_save_layout)
        toolbar.addAction(mw.action_performance_dashboard)
        toolbar.addAction(mw.action_ai_assistant)

        mw.addToolBar(toolbar)
        mw._main_toolbar = toolbar

        return toolbar
