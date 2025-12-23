"""
Toolbar builder for MainWindow toolbar.

Centralizes toolbar creation and styling.
"""

from typing import TYPE_CHECKING

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QToolBar

from casare_rpa.presentation.canvas.ui.icons import get_toolbar_icon
from casare_rpa.presentation.canvas.ui.theme import Theme

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
        c = Theme.get_colors()
        return f"""
            QToolBar {{
                background: {c.background_alt};
                border: none;
                spacing: 1px;
                padding: 2px 4px;
            }}
            QToolButton {{
                background: transparent;
                border: 1px solid transparent;
                border-radius: 3px;
                padding: 3px 6px;
                color: {c.text_secondary};
                font-size: 11px;
            }}
            QToolButton:hover {{
                background: {c.surface};
                border: 1px solid {c.border_light};
                color: {c.text_primary};
            }}
            QToolButton:pressed {{
                background: {c.secondary_hover};
            }}
            QToolButton:checked {{
                background: {c.selection};
                border: 1px solid {c.border_focus};
                color: #ffffff;
            }}
            QToolButton:disabled {{
                color: {c.text_disabled};
            }}
            QToolBar::separator {{
                background: {c.border_light};
                width: 1px;
                margin: 3px 5px;
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
        toolbar.setIconSize(QSize(16, 16))
        toolbar.setStyleSheet(self._get_toolbar_style())

        # Set icons with short labels (text beside icon)
        self._setup_toolbar_action(mw.action_run, "run", "Run", "Run Workflow (F5)")
        self._setup_toolbar_action(mw.action_pause, "pause", "Pause", "Pause (F6)")
        self._setup_toolbar_action(mw.action_stop, "stop", "Stop", "Stop (Shift+F5)")
        self._setup_toolbar_action(mw.action_restart, "restart", "Restart")
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
            mw.action_ai_assistant,
            "ai_assistant",
            "AI",
            "AI Workflow Assistant (Ctrl+Shift+G)",
        )
        self._setup_toolbar_action(
            mw.action_credential_manager,
            "credentials",
            "Keys",
            "Manage Credentials (Ctrl+Alt+C)",
        )

        # === Execution Controls ===
        toolbar.addAction(mw.action_run)
        toolbar.addAction(mw.action_pause)
        toolbar.addAction(mw.action_stop)
        toolbar.addAction(mw.action_restart)

        toolbar.addSeparator()

        # === Automation Tools ===
        toolbar.addAction(mw.action_record_workflow)
        toolbar.addAction(mw.action_pick_selector)

        toolbar.addSeparator()

        # === Project & Management ===
        toolbar.addAction(mw.action_project_manager)
        toolbar.addAction(mw.action_credential_manager)
        toolbar.addAction(mw.action_fleet_dashboard)
        toolbar.addAction(mw.action_save_layout)
        toolbar.addAction(mw.action_performance_dashboard)
        toolbar.addAction(mw.action_ai_assistant)

        mw.addToolBar(toolbar)
        mw._main_toolbar = toolbar

        return toolbar
