"""
Bottom Panel Dock for CasareRPA.

Main dockable container with tabs for Variables, Output, Log, Validation, History,
and Terminal.

Epic 6.1: Migrated to v2 design system (THEME_V2, TOKENS_V2).

Note: Styling is handled by the application-level v2 stylesheet
(`get_canvas_stylesheet_v2()` in NewMainWindow). Avoid per-dock overrides to keep
tabs/buttons unified across the UI.
"""

from typing import TYPE_CHECKING, Any

from loguru import logger
from PySide6.QtCore import QSize, Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QDockWidget,
    QSizePolicy,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.theme import TOKENS_V2

if TYPE_CHECKING:
    from casare_rpa.domain.events import DomainEvent
    from casare_rpa.domain.validation import ValidationResult

    from .history_tab import HistoryTab
    from .log_tab import LogTab
    from .output_tab import OutputTab
    from .terminal_tab import TerminalTab
    from .validation_tab import ValidationTab
    from .variables_tab import VariablesTab


class BottomPanelDock(QDockWidget):
    """
    Dockable bottom panel with tabs for Variables, Output, Log, Validation, History, and Terminal.

    This panel provides a Power Automate/UiPath-style interface for:
    - Variables: Global workflow variables with design/runtime modes
    - Output: Workflow outputs and return values
    - Log: Real-time execution logs
    - Validation: Workflow validation issues
    - History: Execution history with timing and status
    - Terminal: Raw stdout/stderr output

    Note: Triggers are now visual nodes on the canvas.

    Signals:
        variables_changed: Emitted when variables are modified
        validation_requested: Emitted when user requests manual validation
        repair_requested: Emitted when user requests to repair workflow issues
        issue_clicked: Emitted when a validation issue is clicked (location: str)
        navigate_to_node: Emitted when user wants to navigate to a node (node_id: str)
        history_clear_requested: Emitted when user requests to clear history
    """

    variables_changed = Signal(dict)  # {name: VariableDefinition}
    validation_requested = Signal()
    repair_requested = Signal()  # repair workflow issues (duplicate IDs, etc.)
    issue_clicked = Signal(str)  # location string
    navigate_to_node = Signal(str)  # node_id
    history_clear_requested = Signal()

    # Tab indices
    TAB_VARIABLES = 0
    TAB_OUTPUT = 1
    TAB_LOG = 2
    TAB_VALIDATION = 3
    TAB_HISTORY = 4
    TAB_TERMINAL = 5

    def __init__(self, parent: QWidget | None = None) -> None:
        """
        Initialize the bottom panel dock.

        Args:
            parent: Optional parent widget
        """
        super().__init__("Output", parent)
        self.setObjectName("BottomPanelDock")

        self._is_runtime_mode = False
        self._preserved_dock_height: int | None = None

        self._setup_dock()
        self._setup_ui()

        logger.debug("BottomPanelDock initialized")

    def _setup_dock(self) -> None:
        """Configure dock widget properties."""
        # Allow bottom and top areas for flexibility
        self.setAllowedAreas(
            Qt.DockWidgetArea.BottomDockWidgetArea | Qt.DockWidgetArea.TopDockWidgetArea
        )

        # Set features - dock-only: NO DockWidgetFloatable (v2 requirement)
        self.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QDockWidget.DockWidgetFeature.DockWidgetClosable
            # NO DockWidgetFloatable - dock-only enforcement
        )

        # Set minimum height - allow shrinking but not too small
        self.setMinimumHeight(
            max(120, TOKENS_V2.sizes.tab_height + TOKENS_V2.sizes.row_height * 3)
        )

        # Allow vertical resizing - can expand but starts preferred size  
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def sizeHint(self) -> QSize:
        """Return preferred size for dock widget."""
        return QSize(
            800,
            max(250, TOKENS_V2.sizes.tab_height + TOKENS_V2.sizes.row_height * 6),
        )

    def showEvent(self, event) -> None:
        """Handle show event - ensure minimum visible size."""
        super().showEvent(event)
        # Ensure dock has usable size when shown without overriding a user-chosen size.
        if self.height() < self.minimumHeight():
            target_height = self._preserved_dock_height or self.sizeHint().height()
            QTimer.singleShot(0, lambda: self._resize_dock_height(target_height))

    def resizeEvent(self, event) -> None:
        """Track user-adjusted dock height so tab switches don't reflow the dock."""
        super().resizeEvent(event)
        if self.isVisible() and self.height() >= self.minimumHeight():
            self._preserved_dock_height = self.height()

    def _resize_dock_height(self, height: int) -> None:
        """Resize the dock in its area without fighting QMainWindow layout."""
        if height <= 0:
            return
        main_window = self.parent()
        if main_window is not None and hasattr(main_window, "resizeDocks"):
            try:
                main_window.resizeDocks([self], [height], Qt.Orientation.Vertical)
                return
            except Exception:
                # Fall back to direct resize if QMainWindow refuses
                pass
        self.resize(self.width(), height)

    def _on_tab_changed(self, _index: int) -> None:
        """
        Prevent tab switches (especially Output) from changing the dock height.

        Some tab content can trigger a transient sizeHint/layoutRequest that causes
        QMainWindow to reflow dock sizes. Re-apply the last known height after the
        event loop settles.
        """
        if not self.isVisible():
            return
        target_height = self._preserved_dock_height or self.height()
        QTimer.singleShot(0, lambda: self._resize_dock_height(target_height))

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        # Main container widget with expanding size policy
        container = QWidget()
        container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create tab widget with expanding size policy
        self._tab_widget = QTabWidget()
        self._tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        self._tab_widget.setDocumentMode(True)
        self._tab_widget.setUsesScrollButtons(True)
        self._tab_widget.setMovable(False)  # Fixed tab order for consistency
        self._tab_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._tab_widget.currentChanged.connect(self._on_tab_changed)

        # Create tabs
        self._create_tabs()

        layout.addWidget(self._tab_widget, stretch=1)
        self.setWidget(container)

    def _create_tabs(self) -> None:
        """Create all tab widgets."""
        from .history_tab import HistoryTab
        from .log_tab import LogTab
        from .output_tab import OutputTab
        from .terminal_tab import TerminalTab
        from .validation_tab import ValidationTab
        from .variables_tab import VariablesTab

        # Variables tab
        self._variables_tab = VariablesTab()
        self._variables_tab.variables_changed.connect(self._on_variables_changed)
        self._variables_tab.variables_changed.connect(self._update_tab_badges)
        self._tab_widget.addTab(self._variables_tab, "Variables")
        self._tab_widget.setTabToolTip(self.TAB_VARIABLES, "Workflow variables (Ctrl+Shift+V)")

        # Output tab
        self._output_tab = OutputTab()
        self._tab_widget.addTab(self._output_tab, "Output")
        self._tab_widget.setTabToolTip(self.TAB_OUTPUT, "Workflow outputs and return values")

        # Log tab
        self._log_tab = LogTab()
        self._log_tab.navigate_to_node.connect(self.navigate_to_node.emit)
        self._tab_widget.addTab(self._log_tab, "Log")
        self._tab_widget.setTabToolTip(self.TAB_LOG, "Execution log messages")

        # Validation tab
        self._validation_tab = ValidationTab()
        self._validation_tab.validation_requested.connect(self.validation_requested.emit)
        self._validation_tab.repair_requested.connect(self.repair_requested.emit)
        self._validation_tab.issue_clicked.connect(self.issue_clicked.emit)
        self._tab_widget.addTab(self._validation_tab, "Validation")
        self._tab_widget.setTabToolTip(
            self.TAB_VALIDATION, "Workflow validation issues (Ctrl+Shift+V)"
        )

        # History tab
        self._history_tab = HistoryTab()
        self._history_tab.node_selected.connect(self.navigate_to_node.emit)
        self._history_tab.clear_requested.connect(self._on_history_clear_requested)
        self._tab_widget.addTab(self._history_tab, "History")
        self._tab_widget.setTabToolTip(self.TAB_HISTORY, "Execution history with timing")

        # Terminal tab (raw stdout/stderr output)
        self._terminal_tab = TerminalTab()
        self._tab_widget.addTab(self._terminal_tab, "Terminal")
        self._tab_widget.setTabToolTip(self.TAB_TERMINAL, "Raw console output")

        # Note: Triggers are now visual nodes on the canvas (not a tab)

    def _update_tab_badges(self) -> None:
        """Update tab titles with badge counts."""
        # Variables tab - show count if > 0
        var_count = len(self._variables_tab.get_variables())
        var_title = f"Variables ({var_count})" if var_count > 0 else "Variables"
        self._tab_widget.setTabText(self.TAB_VARIABLES, var_title)

        # Output tab - show count if > 0
        output_count = (
            self._output_tab.get_output_count()
            if hasattr(self._output_tab, "get_output_count")
            else 0
        )
        output_title = f"Output ({output_count})" if output_count > 0 else "Output"
        self._tab_widget.setTabText(self.TAB_OUTPUT, output_title)

        # Log tab - show count if > 0
        log_count = (
            self._log_tab.get_entry_count() if hasattr(self._log_tab, "get_entry_count") else 0
        )
        log_title = f"Log ({log_count})" if log_count > 0 else "Log"
        self._tab_widget.setTabText(self.TAB_LOG, log_title)

        # Validation tab - show error/warning count with color hint
        if hasattr(self._validation_tab, "get_issue_count"):
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
        history_count = (
            self._history_tab.get_entry_count()
            if hasattr(self._history_tab, "get_entry_count")
            else 0
        )
        history_title = f"History ({history_count})" if history_count > 0 else "History"
        self._tab_widget.setTabText(self.TAB_HISTORY, history_title)

    def _on_variables_changed(self, variables: dict[str, Any]) -> None:
        """Handle variables changed from Variables tab."""
        self.variables_changed.emit(variables)

    def _on_history_clear_requested(self) -> None:
        """Handle history clear request from History tab."""
        self._history_tab.clear()
        self._update_tab_badges()
        self.history_clear_requested.emit()

    # ==================== Public API ====================

    def get_variables_tab(self) -> "VariablesTab":
        """Get the Variables tab widget."""
        return self._variables_tab

    def get_output_tab(self) -> "OutputTab":
        """Get the Output tab widget."""
        return self._output_tab

    def get_log_tab(self) -> "LogTab":
        """Get the Log tab widget."""
        return self._log_tab

    def get_validation_tab(self) -> "ValidationTab":
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

    def get_history_tab(self) -> "HistoryTab":
        """Get the History tab widget."""
        return self._history_tab

    def show_history_tab(self) -> None:
        """Show and focus the History tab."""
        self.show()
        self._tab_widget.setCurrentIndex(self.TAB_HISTORY)

    def get_terminal_tab(self) -> "TerminalTab":
        """Get the Terminal tab widget."""
        return self._terminal_tab

    def show_terminal_tab(self) -> None:
        """Show and focus the Terminal tab."""
        self.show()
        self._tab_widget.setCurrentIndex(self.TAB_TERMINAL)

    # ==================== Variables API ====================

    def set_variables(self, variables: dict[str, Any]) -> None:
        """
        Set workflow variables (design mode).

        Args:
            variables: Dict of variable definitions
        """
        self._variables_tab.set_variables(variables)

    def get_variables(self) -> dict[str, Any]:
        """
        Get current workflow variables.

        Returns:
            Dict of variable definitions
        """
        return self._variables_tab.get_variables()

    def update_runtime_values(self, values: dict[str, Any]) -> None:
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

    def add_output(self, name: str, value: Any, timestamp: str | None = None) -> None:
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

    def log_event(self, event: "DomainEvent") -> None:
        """
        Log an execution event.

        Args:
            event: Typed domain event to log
        """
        self._log_tab.log_event(event)
        self._update_tab_badges()

    def log_message(self, message: str, level: str = "info", node_id: str | None = None) -> None:
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

    def set_validation_result(self, result: "ValidationResult") -> None:
        """
        Set validation results.

        Updates the validation tab badge but does NOT auto-open the panel.
        User can manually check validation via View menu or the tab badge.

        Args:
            result: ValidationResult to display
        """
        self._validation_tab.set_result(result)
        self._update_tab_badges()

        # Validation runs silently - panel does NOT auto-open
        # The tab badge will indicate errors if any

    def clear_validation(self) -> None:
        """Clear validation results."""
        self._validation_tab.clear()
        self._update_tab_badges()

    def has_validation_errors(self) -> bool:
        """Check if there are validation errors."""
        return self._validation_tab.has_errors()

    def get_validation_errors_blocking(self) -> list[dict]:
        """Get current validation errors synchronously.

        Returns:
            List of validation error dictionaries
        """
        if hasattr(self, "_validation_tab"):
            return self._validation_tab.get_all_errors()
        return []

    # ==================== History API ====================

    def update_history(self, history: list[dict[str, Any]]) -> None:
        """
        Update the execution history display.

        Args:
            history: List of execution history entries
        """
        self._history_tab.update_history(history)
        self._update_tab_badges()

    def append_history_entry(self, entry: dict[str, Any]) -> None:
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

    # ==================== Terminal API ====================

    def terminal_write(self, text: str, level: str = "info") -> None:
        """
        Write text to the Terminal tab.

        Args:
            text: Text to write
            level: Output level (info, warning, error, success, debug)
        """
        self._terminal_tab.write(text, level)

    def terminal_write_stdout(self, text: str) -> None:
        """Write stdout text to the Terminal tab."""
        self._terminal_tab.write_stdout(text)

    def terminal_write_stderr(self, text: str) -> None:
        """Write stderr text to the Terminal tab."""
        self._terminal_tab.write_stderr(text)

    def clear_terminal(self) -> None:
        """Clear the Terminal tab."""
        self._terminal_tab.clear()

    # ==================== State Management ====================

    def prepare_for_execution(self) -> None:
        """Prepare panel for workflow execution (preserves panel visibility)."""
        self.set_runtime_mode(True)
        self.clear_log()
        self.clear_outputs()
        self.clear_history()
        self.clear_terminal()
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
        self._terminal_tab.clear()
        self.set_runtime_mode(False)
        self._update_tab_badges()

