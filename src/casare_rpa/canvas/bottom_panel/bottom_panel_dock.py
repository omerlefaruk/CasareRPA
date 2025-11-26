"""
Bottom Panel Dock for CasareRPA.

Main dockable container with tabs for Variables, Output, Log, Validation, History, and Triggers.
Provides Power Automate/UiPath-style bottom panel functionality.
"""

from typing import Optional, Dict, Any, List, TYPE_CHECKING

from PySide6.QtWidgets import (
    QDockWidget,
    QWidget,
    QVBoxLayout,
    QTabWidget,
    QSizePolicy,
)
from PySide6.QtCore import Qt, Signal
from loguru import logger

if TYPE_CHECKING:
    from ...core.validation import ValidationResult
    from ...core.events import Event
    from .triggers_tab import TriggersTab


class BottomPanelDock(QDockWidget):
    """
    Dockable bottom panel with tabs for Variables, Output, Log, Validation, History, and Triggers.

    This panel provides a Power Automate/UiPath-style interface for:
    - Variables: Global workflow variables with design/runtime modes
    - Output: Workflow outputs and return values
    - Log: Real-time execution logs
    - Validation: Workflow validation issues
    - History: Execution history with timing and status
    - Triggers: Workflow trigger configuration

    Signals:
        variables_changed: Emitted when variables are modified
        validation_requested: Emitted when user requests manual validation
        issue_clicked: Emitted when a validation issue is clicked (location: str)
        navigate_to_node: Emitted when user wants to navigate to a node (node_id: str)
        history_clear_requested: Emitted when user requests to clear history
        trigger_add_requested: Emitted when user wants to add a trigger
        trigger_edit_requested: Emitted when user wants to edit a trigger (trigger_config: dict)
        trigger_delete_requested: Emitted when user wants to delete a trigger (trigger_id: str)
        trigger_toggle_requested: Emitted when user toggles trigger state (trigger_id: str, enabled: bool)
        trigger_run_requested: Emitted when user wants to run a trigger (trigger_id: str)
    """

    variables_changed = Signal(dict)  # {name: VariableDefinition}
    validation_requested = Signal()
    issue_clicked = Signal(str)  # location string
    navigate_to_node = Signal(str)  # node_id
    history_clear_requested = Signal()

    # Trigger signals
    trigger_add_requested = Signal()
    trigger_edit_requested = Signal(dict)  # trigger config
    trigger_delete_requested = Signal(str)  # trigger_id
    trigger_toggle_requested = Signal(str, bool)  # trigger_id, enabled
    trigger_run_requested = Signal(str)  # trigger_id
    triggers_start_requested = Signal()  # Start all triggers
    triggers_stop_requested = Signal()  # Stop all triggers

    # Tab indices
    TAB_VARIABLES = 0
    TAB_OUTPUT = 1
    TAB_LOG = 2
    TAB_VALIDATION = 3
    TAB_HISTORY = 4
    TAB_TRIGGERS = 5

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the bottom panel dock.

        Args:
            parent: Optional parent widget
        """
        super().__init__("Panel", parent)
        self.setObjectName("BottomPanelDock")

        self._is_runtime_mode = False

        self._setup_dock()
        self._setup_ui()
        self._apply_styles()

        logger.debug("BottomPanelDock initialized")

    def _setup_dock(self) -> None:
        """Configure dock widget properties."""
        # Allow only bottom area
        self.setAllowedAreas(Qt.DockWidgetArea.BottomDockWidgetArea)

        # Set features (movable but not floatable)
        self.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable |
            QDockWidget.DockWidgetFeature.DockWidgetClosable
        )

        # Set minimum height
        self.setMinimumHeight(150)

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        # Main container widget
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create tab widget
        self._tab_widget = QTabWidget()
        self._tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        self._tab_widget.setDocumentMode(True)

        # Create tabs
        self._create_tabs()

        layout.addWidget(self._tab_widget)
        self.setWidget(container)

    def _create_tabs(self) -> None:
        """Create all tab widgets."""
        from .variables_tab import VariablesTab
        from .output_tab import OutputTab
        from .log_tab import LogTab
        from .validation_tab import ValidationTab
        from .history_tab import HistoryTab
        from .triggers_tab import TriggersTab

        # Variables tab
        self._variables_tab = VariablesTab()
        self._variables_tab.variables_changed.connect(self._on_variables_changed)
        self._variables_tab.variables_changed.connect(self._update_tab_badges)
        self._tab_widget.addTab(self._variables_tab, "Variables")

        # Output tab
        self._output_tab = OutputTab()
        self._tab_widget.addTab(self._output_tab, "Output")

        # Log tab
        self._log_tab = LogTab()
        self._log_tab.navigate_to_node.connect(self.navigate_to_node.emit)
        self._tab_widget.addTab(self._log_tab, "Log")

        # Validation tab
        self._validation_tab = ValidationTab()
        self._validation_tab.validation_requested.connect(self.validation_requested.emit)
        self._validation_tab.issue_clicked.connect(self.issue_clicked.emit)
        self._tab_widget.addTab(self._validation_tab, "Validation")

        # History tab
        self._history_tab = HistoryTab()
        self._history_tab.node_selected.connect(self.navigate_to_node.emit)
        self._history_tab.clear_requested.connect(self._on_history_clear_requested)
        self._tab_widget.addTab(self._history_tab, "History")

        # Triggers tab
        self._triggers_tab = TriggersTab()
        self._triggers_tab.add_trigger_requested.connect(self.trigger_add_requested.emit)
        self._triggers_tab.trigger_updated.connect(self.trigger_edit_requested.emit)
        self._triggers_tab.trigger_deleted.connect(self.trigger_delete_requested.emit)
        self._triggers_tab.trigger_toggled.connect(self.trigger_toggle_requested.emit)
        self._triggers_tab.trigger_run_requested.connect(self.trigger_run_requested.emit)
        self._triggers_tab.triggers_start_requested.connect(self.triggers_start_requested.emit)
        self._triggers_tab.triggers_stop_requested.connect(self.triggers_stop_requested.emit)
        self._tab_widget.addTab(self._triggers_tab, "Triggers")

    def _update_tab_badges(self) -> None:
        """Update tab titles with badge counts."""
        # Variables tab - show count if > 0
        var_count = len(self._variables_tab.get_variables())
        var_title = f"Variables ({var_count})" if var_count > 0 else "Variables"
        self._tab_widget.setTabText(self.TAB_VARIABLES, var_title)

        # Output tab - show count if > 0
        output_count = self._output_tab.get_output_count() if hasattr(self._output_tab, 'get_output_count') else 0
        output_title = f"Output ({output_count})" if output_count > 0 else "Output"
        self._tab_widget.setTabText(self.TAB_OUTPUT, output_title)

        # Log tab - show count if > 0
        log_count = self._log_tab.get_entry_count() if hasattr(self._log_tab, 'get_entry_count') else 0
        log_title = f"Log ({log_count})" if log_count > 0 else "Log"
        self._tab_widget.setTabText(self.TAB_LOG, log_title)

        # Validation tab - show error/warning count
        if hasattr(self._validation_tab, 'get_issue_count'):
            error_count, warning_count = self._validation_tab.get_issue_count()
            if error_count > 0:
                val_title = f"Validation ({error_count})"
            elif warning_count > 0:
                val_title = f"Validation ({warning_count})"
            else:
                val_title = "Validation"
        else:
            val_title = "Validation"
        self._tab_widget.setTabText(self.TAB_VALIDATION, val_title)

        # History tab - show count if > 0
        history_count = self._history_tab.get_entry_count() if hasattr(self._history_tab, 'get_entry_count') else 0
        history_title = f"History ({history_count})" if history_count > 0 else "History"
        self._tab_widget.setTabText(self.TAB_HISTORY, history_title)

        # Triggers tab - show count if > 0
        trigger_count = self._triggers_tab.get_trigger_count() if hasattr(self._triggers_tab, 'get_trigger_count') else 0
        trigger_title = f"Triggers ({trigger_count})" if trigger_count > 0 else "Triggers"
        self._tab_widget.setTabText(self.TAB_TRIGGERS, trigger_title)

    def _apply_styles(self) -> None:
        """Apply VSCode Dark+ theme styling."""
        from ..theme import THEME

        self.setStyleSheet(f"""
            QDockWidget {{
                background-color: {THEME.bg_panel};
                color: {THEME.text_secondary};
            }}
            QDockWidget::title {{
                background-color: {THEME.dock_title_bg};
                padding: 6px;
                text-align: left;
            }}
            QTabWidget::pane {{
                border: 1px solid {THEME.border_dark};
                background: {THEME.bg_panel};
                border-top: none;
            }}
            QTabBar::tab {{
                background: {THEME.bg_medium};
                color: {THEME.text_secondary};
                padding: 8px 16px;
                border: 1px solid {THEME.border_dark};
                border-bottom: none;
                margin-right: 2px;
                font-weight: 500;
            }}
            QTabBar::tab:selected {{
                background: {THEME.bg_panel};
                color: {THEME.text_primary};
                border-bottom: 2px solid {THEME.accent_primary};
            }}
            QTabBar::tab:hover:!selected {{
                background: {THEME.bg_hover};
                color: {THEME.text_primary};
            }}
        """)

    def _on_variables_changed(self, variables: Dict[str, Any]) -> None:
        """Handle variables changed from Variables tab."""
        self.variables_changed.emit(variables)

    def _on_history_clear_requested(self) -> None:
        """Handle history clear request from History tab."""
        self._history_tab.clear()
        self._update_tab_badges()
        self.history_clear_requested.emit()

    # ==================== Public API ====================

    def get_variables_tab(self) -> 'VariablesTab':
        """Get the Variables tab widget."""
        return self._variables_tab

    def get_output_tab(self) -> 'OutputTab':
        """Get the Output tab widget."""
        return self._output_tab

    def get_log_tab(self) -> 'LogTab':
        """Get the Log tab widget."""
        return self._log_tab

    def get_validation_tab(self) -> 'ValidationTab':
        """Get the Validation tab widget."""
        return self._validation_tab

    def show_variables_tab(self) -> None:
        """Show and focus the Variables tab."""
        self.show()
        self._tab_widget.setCurrentIndex(self.TAB_VARIABLES)

    def show_output_tab(self) -> None:
        """Show and focus the Output tab."""
        self.show()
        self._tab_widget.setCurrentIndex(self.TAB_OUTPUT)

    def show_log_tab(self) -> None:
        """Show and focus the Log tab."""
        self.show()
        self._tab_widget.setCurrentIndex(self.TAB_LOG)

    def show_validation_tab(self) -> None:
        """Show and focus the Validation tab."""
        self.show()
        self._tab_widget.setCurrentIndex(self.TAB_VALIDATION)

    def get_history_tab(self) -> 'HistoryTab':
        """Get the History tab widget."""
        return self._history_tab

    def show_history_tab(self) -> None:
        """Show and focus the History tab."""
        self.show()
        self._tab_widget.setCurrentIndex(self.TAB_HISTORY)

    # ==================== Variables API ====================

    def set_variables(self, variables: Dict[str, Any]) -> None:
        """
        Set workflow variables (design mode).

        Args:
            variables: Dict of variable definitions
        """
        self._variables_tab.set_variables(variables)

    def get_variables(self) -> Dict[str, Any]:
        """
        Get current workflow variables.

        Returns:
            Dict of variable definitions
        """
        return self._variables_tab.get_variables()

    def update_runtime_values(self, values: Dict[str, Any]) -> None:
        """
        Update variable values during runtime.

        Args:
            values: Dict of {variable_name: current_value}
        """
        self._variables_tab.update_runtime_values(values)

    def set_runtime_mode(self, enabled: bool) -> None:
        """
        Switch between design mode and runtime mode.

        Args:
            enabled: True for runtime mode, False for design mode
        """
        self._is_runtime_mode = enabled
        self._variables_tab.set_runtime_mode(enabled)

    # ==================== Output API ====================

    def add_output(self, name: str, value: Any, timestamp: Optional[str] = None) -> None:
        """
        Add an output to the Output tab.

        Args:
            name: Output name/key
            value: Output value
            timestamp: Optional timestamp string
        """
        self._output_tab.add_output(name, value, timestamp)
        self._update_tab_badges()

    def clear_outputs(self) -> None:
        """Clear all outputs."""
        self._output_tab.clear()
        self._update_tab_badges()

    def set_workflow_result(self, success: bool, message: str) -> None:
        """
        Set the final workflow result.

        Args:
            success: Whether workflow completed successfully
            message: Result message
        """
        self._output_tab.set_workflow_result(success, message)

    # ==================== Log API ====================

    def log_event(self, event: 'Event') -> None:
        """
        Log an execution event.

        Args:
            event: Event to log
        """
        self._log_tab.log_event(event)
        self._update_tab_badges()

    def log_message(self, message: str, level: str = "info", node_id: Optional[str] = None) -> None:
        """
        Log a custom message.

        Args:
            message: Message text
            level: Log level (info, warning, error, success)
            node_id: Optional associated node ID
        """
        self._log_tab.log_message(message, level, node_id)
        self._update_tab_badges()

    def clear_log(self) -> None:
        """Clear the execution log."""
        self._log_tab.clear()
        self._update_tab_badges()

    # ==================== Validation API ====================

    def set_validation_result(self, result: 'ValidationResult') -> None:
        """
        Set validation results.

        Args:
            result: ValidationResult to display
        """
        self._validation_tab.set_result(result)
        self._update_tab_badges()

    def clear_validation(self) -> None:
        """Clear validation results."""
        self._validation_tab.clear()
        self._update_tab_badges()

    def has_validation_errors(self) -> bool:
        """Check if there are validation errors."""
        return self._validation_tab.has_errors()

    # ==================== History API ====================

    def update_history(self, history: List[Dict[str, Any]]) -> None:
        """
        Update the execution history display.

        Args:
            history: List of execution history entries
        """
        self._history_tab.update_history(history)
        self._update_tab_badges()

    def append_history_entry(self, entry: Dict[str, Any]) -> None:
        """
        Append a single entry to the execution history.

        Args:
            entry: Execution history entry with keys:
                   - timestamp: ISO timestamp string
                   - node_id: Node identifier
                   - node_type: Type of the node
                   - execution_time: Time in seconds
                   - status: 'success' or 'failed'
        """
        self._history_tab.append_entry(entry)
        self._update_tab_badges()

    def clear_history(self) -> None:
        """Clear execution history."""
        self._history_tab.clear()
        self._update_tab_badges()

    # ==================== Triggers API ====================

    def get_triggers_tab(self) -> 'TriggersTab':
        """Get the Triggers tab widget."""
        return self._triggers_tab

    def show_triggers_tab(self) -> None:
        """Show and focus the Triggers tab."""
        self.show()
        self._tab_widget.setCurrentIndex(self.TAB_TRIGGERS)

    def set_triggers(self, triggers: List[Dict[str, Any]]) -> None:
        """
        Set the list of triggers to display.

        Args:
            triggers: List of trigger configurations as dictionaries
        """
        self._triggers_tab.set_triggers(triggers)
        self._update_tab_badges()

    def get_triggers(self) -> List[Dict[str, Any]]:
        """
        Get the current list of triggers.

        Returns:
            List of trigger configurations
        """
        return self._triggers_tab.get_triggers()

    def add_trigger(self, trigger: Dict[str, Any]) -> None:
        """
        Add a trigger to the list.

        Args:
            trigger: Trigger configuration dictionary
        """
        self._triggers_tab.add_trigger(trigger)
        self._update_tab_badges()

    def update_trigger(self, trigger: Dict[str, Any]) -> None:
        """
        Update an existing trigger.

        Args:
            trigger: Updated trigger configuration
        """
        self._triggers_tab.update_trigger(trigger)
        self._update_tab_badges()

    def remove_trigger(self, trigger_id: str) -> None:
        """
        Remove a trigger from the list.

        Args:
            trigger_id: ID of the trigger to remove
        """
        self._triggers_tab.remove_trigger(trigger_id)
        self._update_tab_badges()

    def clear_triggers(self) -> None:
        """Clear all triggers."""
        self._triggers_tab.clear()
        self._update_tab_badges()

    def set_triggers_running(self, running: bool) -> None:
        """
        Update the UI to reflect trigger running status.

        Args:
            running: True if triggers are running, False otherwise
        """
        self._triggers_tab.set_triggers_running(running)

    # ==================== State Management ====================

    def prepare_for_execution(self) -> None:
        """Prepare panel for workflow execution (preserves panel visibility)."""
        self.set_runtime_mode(True)
        self.clear_log()
        self.clear_outputs()
        self.clear_history()
        # Don't change panel visibility or current tab

    def execution_finished(self) -> None:
        """Handle workflow execution completion."""
        self.set_runtime_mode(False)

    def reset(self) -> None:
        """Reset all tabs to initial state."""
        self._variables_tab.clear()
        self._output_tab.clear()
        self._log_tab.clear()
        self._validation_tab.clear()
        self._history_tab.clear()
        self._triggers_tab.clear()
        self.set_runtime_mode(False)
        self._update_tab_badges()
