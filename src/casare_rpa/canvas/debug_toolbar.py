"""
Debug toolbar for workflow debugging.

Provides controls for debugging workflows including:
- Play/Pause execution
- Step execution
- Continue from breakpoint
- Stop execution
- Clear breakpoints
"""

from typing import Optional, Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import QToolBar, QWidget

from loguru import logger


class DebugToolbar(QToolBar):
    """
    Toolbar for workflow debugging controls.
    
    Provides actions for:
    - Enable/disable debug mode
    - Enable/disable step mode
    - Step to next node
    - Continue execution
    - Stop execution
    - Clear all breakpoints
    
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
        
        # Create actions
        self._create_actions()
        
        # Set initial state
        self._update_actions_state()
        
        logger.debug("Debug toolbar initialized")
    
    def _create_actions(self) -> None:
        """Create toolbar actions."""
        
        # Debug Mode toggle
        self.action_debug_mode = QAction("Debug Mode", self)
        self.action_debug_mode.setCheckable(True)
        self.action_debug_mode.setToolTip("Enable debug mode to track execution history and use breakpoints")
        self.action_debug_mode.setShortcut("F5")
        self.action_debug_mode.toggled.connect(self._on_debug_mode_toggled)
        self.addAction(self.action_debug_mode)
        
        self.addSeparator()
        
        # Step Mode toggle
        self.action_step_mode = QAction("Step Mode", self)
        self.action_step_mode.setCheckable(True)
        self.action_step_mode.setToolTip("Enable step mode to execute workflow one node at a time")
        self.action_step_mode.setShortcut("F6")
        self.action_step_mode.toggled.connect(self._on_step_mode_toggled)
        self.addAction(self.action_step_mode)
        
        # Step Next
        self.action_step = QAction("Step", self)
        self.action_step.setToolTip("Execute next node (F10)")
        self.action_step.setShortcut("F10")
        self.action_step.triggered.connect(self._on_step)
        self.addAction(self.action_step)
        
        # Continue
        self.action_continue = QAction("Continue", self)
        self.action_continue.setToolTip("Continue execution until next breakpoint (F8)")
        self.action_continue.setShortcut("F8")
        self.action_continue.triggered.connect(self._on_continue)
        self.addAction(self.action_continue)
        
        self.addSeparator()
        
        # Stop
        self.action_stop = QAction("Stop", self)
        self.action_stop.setToolTip("Stop workflow execution")
        self.action_stop.setShortcut("Shift+F5")
        self.action_stop.triggered.connect(self._on_stop)
        self.addAction(self.action_stop)
        
        self.addSeparator()
        
        # Clear Breakpoints
        self.action_clear_breakpoints = QAction("Clear Breakpoints", self)
        self.action_clear_breakpoints.setToolTip("Remove all breakpoints from workflow")
        self.action_clear_breakpoints.setShortcut("Ctrl+Shift+F9")
        self.action_clear_breakpoints.triggered.connect(self._on_clear_breakpoints)
        self.addAction(self.action_clear_breakpoints)
    
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
        """Handle debug mode toggle."""
        logger.debug(f"Debug mode {'enabled' if checked else 'disabled'}")
        self._update_actions_state()
        self.debug_mode_toggled.emit(checked)
    
    def _on_step_mode_toggled(self, checked: bool) -> None:
        """Handle step mode toggle."""
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
        self.action_step_mode.setEnabled(not is_running and self.action_debug_mode.isChecked())
        
        # Stop only available while running
        self.action_stop.setEnabled(is_running)
        
        # Step/continue only available in debug mode
        debug_on = self.action_debug_mode.isChecked()
        self.action_step.setEnabled(is_running and debug_on and self.action_step_mode.isChecked())
        self.action_continue.setEnabled(is_running and debug_on)
