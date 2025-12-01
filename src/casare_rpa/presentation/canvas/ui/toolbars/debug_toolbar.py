"""
Debug Toolbar UI Component.

Provides debug controls for workflow execution.
Extracted from canvas/panels/debug_toolbar.py for reusability.
"""

from typing import Optional

from PySide6.QtCore import Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QToolBar, QWidget

from loguru import logger

from casare_rpa.presentation.canvas.ui.icons import get_toolbar_icon


class DebugToolbar(QToolBar):
    """
    Toolbar for workflow debugging controls.

    Features:
    - Debug mode toggle
    - Step mode toggle
    - Step execution
    - Continue execution
    - Stop execution
    - Clear breakpoints

    Signals:
        debug_mode_toggled: Emitted when debug mode is toggled (bool: enabled)
        step_mode_toggled: Emitted when step mode is toggled (bool: enabled)
        step_requested: Emitted when user requests to step to next node
        continue_requested: Emitted when user requests to continue execution
        stop_requested: Emitted when user requests to stop execution
        clear_breakpoints_requested: Emitted when user requests to clear all breakpoints
    """

    debug_mode_toggled = Signal(bool)
    step_mode_toggled = Signal(bool)
    step_requested = Signal()
    continue_requested = Signal()
    stop_requested = Signal()
    toggle_breakpoint_requested = Signal()
    clear_breakpoints_requested = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the debug toolbar.

        Args:
            parent: Optional parent widget
        """
        super().__init__("Debug", parent)

        self.setObjectName("DebugToolbar")
        self.setMovable(True)
        self.setFloatable(False)

        self._create_actions()
        self._update_actions_state()
        self._apply_styles()

        logger.debug("DebugToolbar initialized")

    def _create_actions(self) -> None:
        """Create toolbar actions.

        Standardized shortcuts (VS Code-like):
        - F5: Run/Continue execution
        - F6: Pause execution (main toolbar)
        - F7: Stop execution (main toolbar)
        - F9: Toggle breakpoint
        - F10: Step over
        - F11: Step into (future)
        - Shift+F5: Stop execution
        - Ctrl+F5: Debug mode toggle
        - Ctrl+Shift+F5: Restart debug
        """
        # Debug Mode toggle
        self.action_debug_mode = QAction(get_toolbar_icon("debug"), "Debug Mode", self)
        self.action_debug_mode.setCheckable(True)
        self.action_debug_mode.setToolTip(
            "Enable debug mode to track execution history and use breakpoints (Ctrl+F5)"
        )
        self.action_debug_mode.setShortcut("Ctrl+F5")
        self.action_debug_mode.toggled.connect(self._on_debug_mode_toggled)
        self.addAction(self.action_debug_mode)

        self.addSeparator()

        # Step Mode toggle - no shortcut to avoid conflict with Pause (F6)
        self.action_step_mode = QAction(get_toolbar_icon("step"), "Step Mode", self)
        self.action_step_mode.setCheckable(True)
        self.action_step_mode.setToolTip(
            "Enable step mode to execute workflow one node at a time"
        )
        # Removed F6 shortcut - conflicts with Pause
        self.action_step_mode.toggled.connect(self._on_step_mode_toggled)
        self.addAction(self.action_step_mode)

        # Step Next (F10 - VS Code standard)
        self.action_step = QAction(get_toolbar_icon("step"), "Step Over", self)
        self.action_step.setToolTip("Execute next node (F10)")
        self.action_step.setShortcut("F10")
        self.action_step.triggered.connect(self._on_step)
        self.addAction(self.action_step)

        # Continue (F5 when paused - VS Code standard)
        self.action_continue = QAction(get_toolbar_icon("continue"), "Continue", self)
        self.action_continue.setToolTip("Continue execution until next breakpoint (F5)")
        self.action_continue.setShortcut("F5")
        self.action_continue.triggered.connect(self._on_continue)
        self.addAction(self.action_continue)

        self.addSeparator()

        # Stop (Shift+F5 - VS Code standard)
        self.action_stop = QAction(get_toolbar_icon("stop"), "Stop", self)
        self.action_stop.setToolTip("Stop workflow execution (Shift+F5)")
        self.action_stop.setShortcut("Shift+F5")
        self.action_stop.triggered.connect(self._on_stop)
        self.addAction(self.action_stop)

        self.addSeparator()

        # Toggle Breakpoint (F9 - VS Code standard)
        self.action_toggle_breakpoint = QAction(
            get_toolbar_icon("breakpoint"), "Toggle Breakpoint", self
        )
        self.action_toggle_breakpoint.setToolTip(
            "Toggle breakpoint on selected node (F9)"
        )
        self.action_toggle_breakpoint.setShortcut("F9")
        self.action_toggle_breakpoint.triggered.connect(self._on_toggle_breakpoint)
        self.addAction(self.action_toggle_breakpoint)

        # Clear Breakpoints
        self.action_clear_breakpoints = QAction(
            get_toolbar_icon("clear_breakpoints"), "Clear Breakpoints", self
        )
        self.action_clear_breakpoints.setToolTip(
            "Remove all breakpoints from workflow (Ctrl+Shift+F9)"
        )
        self.action_clear_breakpoints.setShortcut("Ctrl+Shift+F9")
        self.action_clear_breakpoints.triggered.connect(self._on_clear_breakpoints)
        self.addAction(self.action_clear_breakpoints)

    def _apply_styles(self) -> None:
        """Apply toolbar styling."""
        self.setStyleSheet("""
            QToolBar {
                background: #2d2d2d;
                border: 1px solid #3d3d3d;
                spacing: 3px;
                padding: 2px;
            }
            QToolBar::separator {
                background: #4a4a4a;
                width: 1px;
                margin: 4px 2px;
            }
            QToolButton {
                background: transparent;
                color: #e0e0e0;
                border: none;
                border-radius: 2px;
                padding: 4px 8px;
            }
            QToolButton:hover {
                background: #3d3d3d;
            }
            QToolButton:pressed {
                background: #252525;
            }
            QToolButton:checked {
                background: #5a8a9a;
                color: #ffffff;
            }
            QToolButton:disabled {
                color: #666666;
            }
        """)

    def _update_actions_state(self) -> None:
        """Update the enabled state of actions based on current mode."""
        debug_enabled = self.action_debug_mode.isChecked()
        step_enabled = self.action_step_mode.isChecked()

        # Step mode controls only available when debug mode is on
        self.action_step_mode.setEnabled(debug_enabled)
        self.action_step.setEnabled(debug_enabled and step_enabled)
        self.action_continue.setEnabled(debug_enabled)
        self.action_clear_breakpoints.setEnabled(debug_enabled)

    def _on_debug_mode_toggled(self, checked: bool) -> None:
        """
        Handle debug mode toggle.

        Args:
            checked: New checked state
        """
        logger.debug(f"Debug mode {'enabled' if checked else 'disabled'}")
        self._update_actions_state()
        self.debug_mode_toggled.emit(checked)

    def _on_step_mode_toggled(self, checked: bool) -> None:
        """
        Handle step mode toggle.

        Args:
            checked: New checked state
        """
        logger.debug(f"Step mode {'enabled' if checked else 'disabled'}")
        self._update_actions_state()
        self.step_mode_toggled.emit(checked)

    def _on_step(self) -> None:
        """Handle step action."""
        logger.debug("Step requested")
        self.step_requested.emit()

    def _on_continue(self) -> None:
        """Handle continue action."""
        logger.debug("Continue requested")
        self.continue_requested.emit()

    def _on_stop(self) -> None:
        """Handle stop action."""
        logger.debug("Stop requested")
        self.stop_requested.emit()

    def _on_toggle_breakpoint(self) -> None:
        """Handle toggle breakpoint action."""
        logger.debug("Toggle breakpoint requested")
        self.toggle_breakpoint_requested.emit()

    def _on_clear_breakpoints(self) -> None:
        """Handle clear breakpoints action."""
        logger.debug("Clear breakpoints requested")
        self.clear_breakpoints_requested.emit()

    def set_debug_mode(self, enabled: bool) -> None:
        """
        Programmatically set debug mode state.

        Args:
            enabled: Whether debug mode should be enabled
        """
        self.action_debug_mode.setChecked(enabled)

    def set_step_mode(self, enabled: bool) -> None:
        """
        Programmatically set step mode state.

        Args:
            enabled: Whether step mode should be enabled
        """
        self.action_step_mode.setChecked(enabled)

    def set_execution_state(self, is_running: bool) -> None:
        """
        Update toolbar based on execution state.

        Args:
            is_running: Whether workflow is currently executing
        """
        # Can't change modes while running
        self.action_debug_mode.setEnabled(not is_running)
        self.action_step_mode.setEnabled(
            not is_running and self.action_debug_mode.isChecked()
        )

        # Stop only available while running
        self.action_stop.setEnabled(is_running)

        # Step/continue only available in debug mode
        debug_on = self.action_debug_mode.isChecked()
        self.action_step.setEnabled(
            is_running and debug_on and self.action_step_mode.isChecked()
        )
        self.action_continue.setEnabled(is_running and debug_on)
