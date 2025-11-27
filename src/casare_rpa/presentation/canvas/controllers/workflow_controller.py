"""
Workflow lifecycle controller.

Handles all workflow-related operations:
- New/Open/Save/Save As/Close
- Import/Export
- Validation
- File management
"""

from pathlib import Path
from typing import Optional
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFileDialog, QMessageBox, QDialog
from loguru import logger

from .base_controller import BaseController
from ....utils.config import WORKFLOWS_DIR


class WorkflowController(BaseController):
    """
    Manages workflow lifecycle operations.

    Single Responsibility: Workflow file management and validation.

    Signals:
        workflow_created: Emitted when new workflow is created
        workflow_loaded: Emitted when workflow is opened (str: file_path)
        workflow_saved: Emitted when workflow is saved (str: file_path)
        workflow_imported: Emitted when workflow is imported (str: file_path)
        workflow_exported: Emitted when nodes are exported (str: file_path)
        workflow_closed: Emitted when workflow is closed
        current_file_changed: Emitted when current file changes (Optional[Path])
        modified_changed: Emitted when modified state changes (bool)
    """

    # Signals
    workflow_created = Signal()
    workflow_loaded = Signal(str)  # file_path
    workflow_saved = Signal(str)  # file_path
    workflow_imported = Signal(str)  # file_path
    workflow_exported = Signal(str)  # file_path
    workflow_closed = Signal()
    current_file_changed = Signal(object)  # Optional[Path]
    modified_changed = Signal(bool)

    def __init__(self, main_window):
        """Initialize workflow controller."""
        super().__init__(main_window)
        self._current_file: Optional[Path] = None
        self._is_modified = False

    def initialize(self) -> None:
        """Initialize controller."""
        super().initialize()
        logger.info("WorkflowController initialized")

    def cleanup(self) -> None:
        """Clean up resources."""
        super().cleanup()
        logger.info("WorkflowController cleanup")

    def new_workflow(self) -> None:
        """Create a new empty workflow."""
        logger.info("Creating new workflow")

        if not self._check_unsaved_changes():
            return

        self.workflow_created.emit()
        self.set_current_file(None)
        self.set_modified(False)

        if self.main_window.statusBar():
            self.main_window.statusBar().showMessage("New workflow created", 3000)

    def new_from_template(self) -> None:
        """Create a new workflow from a template."""
        logger.info("Creating workflow from template")

        if not self._check_unsaved_changes():
            return

        from ....canvas.dialogs.template_browser import show_template_browser

        template = show_template_browser(self.main_window)
        if template:
            # MainWindow will handle the actual template loading via signal
            if self.main_window.statusBar():
                self.main_window.statusBar().showMessage(
                    f"Loading template: {template.name}...", 3000
                )
            # Emit through main window signal
            self.main_window.workflow_new_from_template.emit(template)

    def open_workflow(self) -> None:
        """Open an existing workflow file."""
        logger.info("Opening workflow")

        if not self._check_unsaved_changes():
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self.main_window,
            "Open Workflow",
            str(WORKFLOWS_DIR),
            "Workflow Files (*.json);;All Files (*.*)",
        )

        if file_path:
            self.workflow_loaded.emit(file_path)
            self.set_current_file(Path(file_path))
            self.set_modified(False)

            if self.main_window.statusBar():
                self.main_window.statusBar().showMessage(
                    f"Opened: {Path(file_path).name}", 3000
                )

            # Schedule validation after opening
            from PySide6.QtCore import QTimer

            QTimer.singleShot(100, self._validate_after_open)

    def import_workflow(self) -> None:
        """Import nodes from another workflow."""
        logger.info("Importing workflow")

        file_path, _ = QFileDialog.getOpenFileName(
            self.main_window,
            "Import Workflow",
            str(WORKFLOWS_DIR),
            "Workflow Files (*.json);;All Files (*.*)",
        )

        if file_path:
            self.workflow_imported.emit(file_path)
            if self.main_window.statusBar():
                self.main_window.statusBar().showMessage(
                    f"Importing: {Path(file_path).name}...", 3000
                )

    def export_selected_nodes(self) -> None:
        """Export selected nodes to a workflow file."""
        logger.info("Exporting selected nodes")

        # Check if graph is available
        central_widget = self.main_window._central_widget
        if not central_widget or not hasattr(central_widget, "graph"):
            if self.main_window.statusBar():
                self.main_window.statusBar().showMessage("No graph available", 3000)
            return

        graph = central_widget.graph
        selected_nodes = graph.selected_nodes()

        if not selected_nodes:
            QMessageBox.information(
                self.main_window,
                "Export Selected Nodes",
                "Please select one or more nodes to export.",
            )
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self.main_window,
            "Export Selected Nodes",
            str(WORKFLOWS_DIR / "exported_nodes.json"),
            "Workflow Files (*.json);;All Files (*.*)",
        )

        if file_path:
            self.workflow_exported.emit(file_path)
            if self.main_window.statusBar():
                self.main_window.statusBar().showMessage(
                    f"Exporting {len(selected_nodes)} nodes...", 3000
                )

    def save_workflow(self) -> None:
        """Save the current workflow."""
        logger.info("Saving workflow")

        # Validate before saving
        if not self._check_validation_before_save():
            return

        if self._current_file:
            self.workflow_saved.emit(str(self._current_file))
            self.set_modified(False)
            if self.main_window.statusBar():
                self.main_window.statusBar().showMessage(
                    f"Saved: {self._current_file.name}", 3000
                )
        else:
            self.save_workflow_as()

    def save_workflow_as(self) -> None:
        """Save the workflow with a new name."""
        logger.info("Saving workflow as")

        # Validate before saving
        if not self._check_validation_before_save():
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self.main_window,
            "Save Workflow As",
            str(WORKFLOWS_DIR),
            "Workflow Files (*.json);;All Files (*.*)",
        )

        if file_path:
            self.workflow_saved.emit(file_path)
            self.set_current_file(Path(file_path))
            self.set_modified(False)
            if self.main_window.statusBar():
                self.main_window.statusBar().showMessage(
                    f"Saved as: {Path(file_path).name}", 3000
                )

    def close_workflow(self) -> bool:
        """
        Close the current workflow.

        Returns:
            True if workflow was closed, False if cancelled
        """
        logger.info("Closing workflow")

        if not self._check_unsaved_changes():
            return False

        self.workflow_closed.emit()
        self.set_current_file(None)
        self.set_modified(False)
        return True

    def set_current_file(self, file_path: Optional[Path]) -> None:
        """
        Set the current workflow file path.

        Args:
            file_path: Path to workflow file, or None for new workflow
        """
        if self._current_file != file_path:
            self._current_file = file_path
            self.current_file_changed.emit(file_path)
            self._update_window_title()

    def set_modified(self, modified: bool) -> None:
        """
        Set the modified state of the workflow.

        Args:
            modified: True if workflow has unsaved changes
        """
        if self._is_modified != modified:
            self._is_modified = modified
            self.modified_changed.emit(modified)
            self._update_window_title()
            self._update_save_action()

    @property
    def current_file(self) -> Optional[Path]:
        """Get the current workflow file path."""
        return self._current_file

    @property
    def is_modified(self) -> bool:
        """Check if workflow has unsaved changes."""
        return self._is_modified

    def _check_unsaved_changes(self) -> bool:
        """
        Check for unsaved changes and prompt user.

        Returns:
            True if safe to proceed, False if cancelled
        """
        if not self._is_modified:
            return True

        file_name = self._current_file.name if self._current_file else "Untitled"
        reply = QMessageBox.question(
            self.main_window,
            "Unsaved Changes",
            f"The workflow '{file_name}' has unsaved changes.\n\n"
            "Do you want to save before continuing?",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save,
        )

        if reply == QMessageBox.StandardButton.Save:
            self.save_workflow()
            return not self._is_modified  # Only proceed if save succeeded
        elif reply == QMessageBox.StandardButton.Discard:
            return True
        else:  # Cancel
            return False

    def _check_validation_before_save(self) -> bool:
        """
        Check validation before saving.

        Returns:
            True if safe to save, False if validation errors exist
        """
        # Get validation errors from bottom panel if available
        if hasattr(self.main_window, "_bottom_panel") and self.main_window._bottom_panel:
            validation_errors = (
                self.main_window._bottom_panel.get_validation_errors_blocking()
            )
            if validation_errors:
                reply = QMessageBox.warning(
                    self.main_window,
                    "Validation Errors",
                    f"The workflow has {len(validation_errors)} validation error(s).\n\n"
                    "Do you want to save anyway?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )
                return reply == QMessageBox.StandardButton.Yes

        return True

    def _validate_after_open(self) -> None:
        """Validate workflow after opening and show panel if issues found."""
        if hasattr(self.main_window, "_bottom_panel") and self.main_window._bottom_panel:
            self.main_window._bottom_panel.trigger_validation()

            # Show validation tab if there are errors
            validation_errors = (
                self.main_window._bottom_panel.get_validation_errors_blocking()
            )
            if validation_errors:
                self.main_window._bottom_panel.show_validation_tab()

    def _update_window_title(self) -> None:
        """Update main window title with current file and modified state."""
        from ....utils.config import APP_NAME

        if self._current_file:
            title = f"{self._current_file.name} - {APP_NAME}"
        else:
            title = f"Untitled - {APP_NAME}"

        if self._is_modified:
            title += " *"

        self.main_window.setWindowTitle(title)

    def _update_save_action(self) -> None:
        """Update save action enabled state."""
        if hasattr(self.main_window, "action_save"):
            self.main_window.action_save.setEnabled(self._is_modified)
