"""
Toolbar builder for MainWindow toolbar.

Centralizes toolbar creation and styling.
"""

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QToolBar

if TYPE_CHECKING:
    from ..main_window import MainWindow


class ToolbarBuilder:
    """
    Builds the main toolbar for MainWindow.

    Responsibilities:
    - Create compact unified toolbar
    - Apply modern dark theme styling
    - Organize execution and automation controls
    """

    # Toolbar stylesheet for modern dark theme
    TOOLBAR_STYLE = """
        QToolBar {
            background: #2b2b2b;
            border: none;
            spacing: 2px;
            padding: 2px 4px;
        }
        QToolButton {
            background: transparent;
            border: 1px solid transparent;
            border-radius: 4px;
            padding: 4px 8px;
            color: #e0e0e0;
            font-size: 12px;
        }
        QToolButton:hover {
            background: #3d3d3d;
            border: 1px solid #4a4a4a;
        }
        QToolButton:pressed {
            background: #4a4a4a;
        }
        QToolButton:checked {
            background: #4a6a8a;
            border: 1px solid #5a7a9a;
        }
        QToolButton:disabled {
            color: #666666;
        }
        QToolBar::separator {
            background: #4a4a4a;
            width: 1px;
            margin: 4px 6px;
        }
    """

    def __init__(self, main_window: "MainWindow") -> None:
        """
        Initialize toolbar builder.

        Args:
            main_window: Parent MainWindow instance
        """
        self._main_window = main_window

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
        toolbar.setStyleSheet(self.TOOLBAR_STYLE)

        # === Execution Controls ===
        toolbar.addAction(mw.action_run)
        toolbar.addAction(mw.action_pause)
        toolbar.addAction(mw.action_stop)

        toolbar.addSeparator()

        # === Trigger Controls ===
        toolbar.addAction(mw.action_start_listening)
        toolbar.addAction(mw.action_stop_listening)

        toolbar.addSeparator()

        # === Automation Tools ===
        toolbar.addAction(mw.action_record_workflow)
        toolbar.addAction(mw.action_pick_selector)

        toolbar.addSeparator()

        # === Project Management ===
        toolbar.addAction(mw.action_project_manager)

        mw.addToolBar(toolbar)
        mw._main_toolbar = toolbar

        return toolbar
