"""
Toolbar builder for MainWindow toolbar.

Centralizes toolbar creation and styling.
"""

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QToolBar

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

    # Toolbar stylesheet for modern dark theme with text under icons
    TOOLBAR_STYLE = """
        QToolBar {
            background: #2b2b2b;
            border: none;
            spacing: 2px;
            padding: 4px 6px;
        }
        QToolButton {
            background: transparent;
            border: 1px solid transparent;
            border-radius: 4px;
            padding: 6px 8px 4px 8px;
            color: #b0b0b0;
            font-size: 10px;
        }
        QToolButton:hover {
            background: #3d3d3d;
            border: 1px solid #4a4a4a;
            color: #e0e0e0;
        }
        QToolButton:pressed {
            background: #4a4a4a;
        }
        QToolButton:checked {
            background: #4a6a8a;
            border: 1px solid #5a7a9a;
            color: #ffffff;
        }
        QToolButton:disabled {
            color: #555555;
        }
        QToolBar::separator {
            background: #4a4a4a;
            width: 1px;
            margin: 6px 8px;
        }
    """

    def __init__(self, main_window: "MainWindow") -> None:
        """
        Initialize toolbar builder.

        Args:
            main_window: Parent MainWindow instance
        """
        self._main_window = main_window

    def _setup_toolbar_action(self, action, icon_name: str, toolbar_text: str) -> None:
        """Set icon and short toolbar text for an action."""
        action.setIcon(get_toolbar_icon(icon_name))
        action.setIconText(toolbar_text)

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
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        toolbar.setStyleSheet(self.TOOLBAR_STYLE)

        # Set icons and short text labels for toolbar display
        self._setup_toolbar_action(mw.action_run, "run", "Run")
        self._setup_toolbar_action(mw.action_pause, "pause", "Pause")
        self._setup_toolbar_action(mw.action_stop, "stop", "Stop")
        self._setup_toolbar_action(
            mw.action_record_workflow, "record", "Record Browser"
        )
        self._setup_toolbar_action(
            mw.action_pick_selector, "pick_selector", "Pick Element"
        )
        self._setup_toolbar_action(
            mw.action_project_manager, "project", "Project Manager"
        )
        self._setup_toolbar_action(
            mw.action_credential_manager, "credentials", "Credential Manager"
        )
        self._setup_toolbar_action(
            mw.action_performance_dashboard, "performance", "Performance Monitor"
        )

        # === Execution Controls ===
        toolbar.addAction(mw.action_run)
        toolbar.addAction(mw.action_pause)
        toolbar.addAction(mw.action_stop)

        toolbar.addSeparator()

        # === Automation Tools ===
        toolbar.addAction(mw.action_record_workflow)
        toolbar.addAction(mw.action_pick_selector)

        toolbar.addSeparator()

        # === Project & Settings ===
        toolbar.addAction(mw.action_project_manager)
        toolbar.addAction(mw.action_credential_manager)

        toolbar.addSeparator()

        # === Performance ===
        toolbar.addAction(mw.action_performance_dashboard)

        mw.addToolBar(toolbar)
        mw._main_toolbar = toolbar

        return toolbar
