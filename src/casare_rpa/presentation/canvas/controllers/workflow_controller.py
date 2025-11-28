"""
Workflow lifecycle controller.

Handles all workflow-related operations:
- New/Open/Save/Save As/Close
- Import/Export
- Validation
- File management
"""

from pathlib import Path
from typing import Optional, TYPE_CHECKING
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFileDialog, QMessageBox, QDialog
from loguru import logger

from .base_controller import BaseController
from ....utils.config import WORKFLOWS_DIR

if TYPE_CHECKING:
    from ....canvas.main_window import MainWindow


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
    workflow_imported_json = Signal(str)  # json_string for paste workflow
    workflow_exported = Signal(str)  # file_path
    workflow_closed = Signal()
    current_file_changed = Signal(object)  # Optional[Path]
    modified_changed = Signal(bool)

    def __init__(self, main_window: "MainWindow"):
        """Initialize workflow controller."""
        super().__init__(main_window)
        self._current_file: Optional[Path] = None
        self._is_modified = False

    def initialize(self) -> None:
        """Initialize controller."""
        super().initialize()
        # Setup drag-drop import handlers
        self.setup_drag_drop_import()
        logger.info("WorkflowController initialized")

    def cleanup(self) -> None:
        """Clean up resources."""
        super().cleanup()
        logger.info("WorkflowController cleanup")

    def new_workflow(self) -> None:
        """Create a new empty workflow."""
        logger.info("Creating new workflow")

        if not self.check_unsaved_changes():
            return

        self.workflow_created.emit()
        self.set_current_file(None)
        self.set_modified(False)

        self.main_window.show_status("New workflow created", 3000)

    def new_from_template(self) -> None:
        """Create a new workflow from a template."""
        logger.info("Creating workflow from template")

        if not self.check_unsaved_changes():
            return

        from ....canvas.dialogs.template_browser import show_template_browser

        template = show_template_browser(self.main_window)
        if template:
            # MainWindow will handle the actual template loading via signal
            self.main_window.show_status(f"Loading template: {template.name}...", 3000)
            # Emit through main window signal
            self.main_window.workflow_new_from_template.emit(template)

    def open_workflow(self) -> None:
        """Open an existing workflow file."""
        logger.info("Opening workflow")

        if not self.check_unsaved_changes():
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

            self.main_window.show_status(f"Opened: {Path(file_path).name}", 3000)

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
            self.main_window.show_status(f"Importing: {Path(file_path).name}...", 3000)

    def export_selected_nodes(self) -> None:
        """Export selected nodes to a workflow file."""
        logger.info("Exporting selected nodes")

        # Check if graph is available
        graph = self.main_window.get_graph()
        if not graph:
            self.main_window.show_status("No graph available", 3000)
            return

        graph = graph
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
            self.main_window.show_status(
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
            self.main_window.show_status(f"Saved: {self._current_file.name}", 3000)
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
            self.main_window.show_status(f"Saved as: {Path(file_path).name}", 3000)

    def close_workflow(self) -> bool:
        """
        Close the current workflow.

        Returns:
            True if workflow was closed, False if cancelled
        """
        logger.info("Closing workflow")

        if not self.check_unsaved_changes():
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

    def check_unsaved_changes(self) -> bool:
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
        bottom_panel = self.main_window.get_bottom_panel()
        if bottom_panel:
            validation_errors = bottom_panel.get_validation_errors_blocking()
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
        bottom_panel = self.main_window.get_bottom_panel()
        if bottom_panel:
            bottom_panel.trigger_validation()

            # Show validation tab if there are errors
            validation_errors = bottom_panel.get_validation_errors_blocking()
            if validation_errors:
                bottom_panel.show_validation_tab()

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

    def paste_workflow(self) -> None:
        """
        Paste workflow JSON from clipboard and import nodes.

        Validates the clipboard content as valid workflow JSON and
        emits workflow_imported_json signal for the app to handle.
        """
        logger.info("Pasting workflow from clipboard")

        from PySide6.QtWidgets import QApplication
        import orjson

        clipboard = QApplication.clipboard()
        text = clipboard.text()

        if not text:
            self.main_window.show_status("Clipboard is empty", 3000)
            return

        # Try to parse as JSON
        try:
            data = orjson.loads(text)

            # Basic validation - should have nodes key
            if "nodes" not in data:
                QMessageBox.warning(
                    self.main_window,
                    "Invalid Workflow JSON",
                    "The clipboard content does not appear to be a valid workflow.\n"
                    "Expected a JSON object with a 'nodes' key.",
                )
                return

            # Emit signal with the JSON string for app to handle
            self.workflow_imported_json.emit(text)
            self.main_window.show_status(
                f"Importing {len(data.get('nodes', []))} nodes from clipboard...", 3000
            )

        except Exception as e:
            logger.warning(f"Failed to parse clipboard as workflow JSON: {e}")
            QMessageBox.warning(
                self.main_window,
                "Invalid JSON",
                f"The clipboard content is not valid JSON.\n\nError: {str(e)}",
            )

    def setup_drag_drop_import(self) -> None:
        """
        Setup drag-and-drop support for importing workflow JSON files.

        Allows users to drag .json workflow files directly onto the canvas
        to import nodes at the drop position.

        Extracted from: canvas/components/dragdrop_component.py
        """
        logger.info("Setting up drag-drop import handlers")

        def on_import_file(file_path: str, position: tuple) -> None:
            """Handle file drop on canvas."""
            try:
                import orjson
                from pathlib import Path

                logger.info(
                    f"Importing dropped file: {file_path} at position {position}"
                )

                # Load workflow data
                data = orjson.loads(Path(file_path).read_bytes())

                # Signal workflow import with file path
                self.workflow_imported.emit(file_path)
                self.main_window.set_modified(True)

                self.main_window.show_status(
                    f"Imported {len(data.get('nodes', {}))} nodes from {Path(file_path).name}",
                    5000,
                )
            except Exception as e:
                logger.error(f"Failed to import dropped file: {e}")
                self.main_window.show_status(f"Error importing file: {str(e)}", 5000)

        def on_import_data(data: dict, position: tuple) -> None:
            """Handle JSON data drop on canvas."""
            try:
                import orjson

                logger.info(f"Importing dropped JSON data at position {position}")

                # Convert to JSON string and signal
                json_str = orjson.dumps(data).decode("utf-8")
                self.workflow_imported_json.emit(json_str)
                self.main_window.set_modified(True)

                self.main_window.show_status(
                    f"Imported {len(data.get('nodes', {}))} nodes", 5000
                )
            except Exception as e:
                logger.error(f"Failed to import dropped JSON: {e}")
                self.main_window.show_status(f"Error importing JSON: {str(e)}", 5000)

        # Get node graph and set callbacks
        graph = self.main_window.get_graph()
        if graph and hasattr(graph, "set_import_file_callback"):
            graph.set_import_file_callback(on_import_file)
            graph.set_import_callback(on_import_data)
            if hasattr(graph, "setup_drag_drop"):
                graph.setup_drag_drop()
            logger.info("Drag-drop import handlers configured")
        else:
            logger.warning("Graph does not support drag-drop import")

    def check_validation_before_run(self) -> bool:
        """
        Check validation before running workflow.

        Returns:
            True if workflow is valid or user wants to run anyway,
            False if validation errors exist and user cancels
        """
        logger.debug("Checking validation before run")

        # Get validation errors from bottom panel if available
        bottom_panel = self.main_window.get_bottom_panel()
        if bottom_panel:
            validation_errors = bottom_panel.get_validation_errors_blocking()
            if validation_errors:
                # Count errors vs warnings
                error_count = sum(
                    1
                    for e in validation_errors
                    if getattr(e, "severity", "error") == "error"
                )
                warning_count = len(validation_errors) - error_count

                if error_count > 0:
                    reply = QMessageBox.warning(
                        self.main_window,
                        "Validation Errors",
                        f"The workflow has {error_count} error(s) and {warning_count} warning(s).\n\n"
                        "Running a workflow with errors may cause unexpected behavior.\n\n"
                        "Do you want to run anyway?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.No,
                    )
                    return reply == QMessageBox.StandardButton.Yes

        return True
