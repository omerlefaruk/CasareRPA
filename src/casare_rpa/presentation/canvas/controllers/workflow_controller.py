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
from PySide6.QtWidgets import QFileDialog, QMessageBox
from loguru import logger
from pydantic import ValidationError

from casare_rpa.application.services import OrchestratorClient
from casare_rpa.config import WORKFLOWS_DIR
from casare_rpa.infrastructure.security.workflow_schema import validate_workflow_json
from casare_rpa.presentation.canvas.controllers.base_controller import BaseController

if TYPE_CHECKING:
    from casare_rpa.presentation.canvas.main_window import MainWindow
    from casare_rpa.domain.workflow.versioning import VersionHistory


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
        self._orchestrator_client: Optional[OrchestratorClient] = None

    def initialize(self) -> None:
        """Initialize controller."""
        super().initialize()
        # Setup drag-drop import handlers
        self.setup_drag_drop_import()

    def cleanup(self) -> None:
        """Clean up resources."""
        super().cleanup()
        # Close orchestrator client if exists
        if self._orchestrator_client:
            import asyncio

            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self._orchestrator_client.close())
                else:
                    loop.run_until_complete(self._orchestrator_client.close())
            except Exception as e:
                logger.warning("Failed to close orchestrator client cleanly: {}", e)
            self._orchestrator_client = None
        logger.info("WorkflowController cleanup")

    def _get_orchestrator_client(self) -> OrchestratorClient:
        """
        Get or create orchestrator client for API calls.

        Returns:
            OrchestratorClient instance with connection pooling
        """
        import os

        if self._orchestrator_client is None:
            orchestrator_url = os.getenv("ORCHESTRATOR_URL", "http://localhost:8000")
            self._orchestrator_client = OrchestratorClient(
                orchestrator_url=orchestrator_url
            )
            logger.debug("Created OrchestratorClient for API calls")
        return self._orchestrator_client

    def _extract_schedule_trigger_info(
        self, workflow_json: dict
    ) -> tuple[str | None, dict | None]:
        """
        Extract schedule trigger configuration from workflow JSON.

        Searches for ScheduleTriggerNode in the workflow and extracts its config.

        Args:
            workflow_json: Serialized workflow data

        Returns:
            Tuple of (trigger_type, schedule_config) where:
            - trigger_type: "scheduled" if Schedule Trigger found, None otherwise
            - schedule_config: Dict with 'cron_expression' and original config, or None
        """
        from typing import Any, Dict

        nodes = workflow_json.get("nodes", {})

        # LOG: Show the number of nodes and format
        logger.info(
            f"[SCHEDULE_DETECT] Searching {len(nodes) if nodes else 0} nodes "
            f"(format: {'list' if isinstance(nodes, list) else 'dict'})"
        )

        # Handle both dict format (Canvas) and list format
        if isinstance(nodes, list):
            nodes_iter = [(n.get("node_id", ""), n) for n in nodes]
        else:
            nodes_iter = nodes.items()

        for node_id, node_data in nodes_iter:
            # Check for ScheduleTriggerNode - try multiple key formats
            node_type = (
                node_data.get("node_type", "") or node_data.get("type_", "") or ""
            )

            # LOG: Show each node type for troubleshooting
            logger.info(f"[SCHEDULE_DETECT] Node {node_id}: type='{node_type}'")

            if "ScheduleTrigger" in node_type:
                # Extract config from 'config' (serialized) or 'custom' (Canvas raw)
                config = node_data.get("config", {}) or node_data.get("custom", {})

                # Convert to cron expression
                cron_expr = self._schedule_config_to_cron(config)

                logger.info(
                    f"Found ScheduleTriggerNode: {node_id}, "
                    f"frequency={config.get('frequency')}, cron={cron_expr}"
                )

                return "scheduled", {
                    "cron_expression": cron_expr,
                    "original_config": config,
                    "trigger_node_id": node_id,
                }

        logger.debug("[SCHEDULE_DETECT] No ScheduleTriggerNode found in workflow")
        return None, None

    def _schedule_config_to_cron(self, config: dict) -> str:
        """
        Convert ScheduleTriggerNode config to cron expression.

        Cron format: minute hour day month weekday

        Supports:
        - interval: Every N seconds (min 60s → */1 * * * *)
        - hourly: At minute M every hour
        - daily: At H:M every day
        - weekly: At H:M on specific weekday
        - monthly: At H:M on specific day of month
        - cron: Use provided cron expression directly

        Args:
            config: ScheduleTriggerNode configuration dict

        Returns:
            Cron expression string
        """
        frequency = config.get("frequency", "daily")

        # Parse time settings with defaults
        hour = int(config.get("time_hour", 9))
        minute = int(config.get("time_minute", 0))

        # Clamp to valid ranges
        hour = max(0, min(23, hour))
        minute = max(0, min(59, minute))

        if frequency == "cron":
            # Use provided cron expression directly
            return config.get("cron_expression", "0 9 * * *")

        elif frequency == "interval":
            # Convert interval to cron (minimum 1 minute)
            seconds = int(config.get("interval_seconds", 60))
            if seconds < 60:
                logger.warning(
                    f"Interval {seconds}s is less than 1 minute. "
                    f"Using minimum interval of 1 minute for cron scheduling."
                )
                seconds = 60

            minutes = seconds // 60
            if minutes >= 60:
                # Run every N hours
                hours = minutes // 60
                return f"0 */{hours} * * *"
            else:
                # Run every N minutes
                return f"*/{minutes} * * * *"

        elif frequency == "hourly":
            # At minute M every hour
            return f"{minute} * * * *"

        elif frequency == "daily":
            # At H:M every day
            return f"{minute} {hour} * * *"

        elif frequency == "weekly":
            # Convert day name to cron weekday number (0=Sun or mon,tue,wed...)
            day_map = {
                "sun": 0,
                "mon": 1,
                "tue": 2,
                "wed": 3,
                "thu": 4,
                "fri": 5,
                "sat": 6,
            }
            day = config.get("day_of_week", "mon").lower()
            weekday = day_map.get(day, 1)
            return f"{minute} {hour} * * {weekday}"

        elif frequency == "monthly":
            # At H:M on day D of month
            day = int(config.get("day_of_month", 1))
            day = max(1, min(31, day))
            return f"{minute} {hour} {day} * *"

        elif frequency == "once":
            # For 'once', we still create a schedule but it will be disabled after run
            # Default to daily at specified time
            return f"{minute} {hour} * * *"

        else:
            # Fallback: daily at 9:00
            logger.warning(f"Unknown frequency '{frequency}', defaulting to daily 9:00")
            return "0 9 * * *"

    def new_workflow(self) -> None:
        """Create a new empty workflow."""
        logger.info("Creating new workflow")

        if not self.check_unsaved_changes():
            return

        self.workflow_created.emit()
        self.set_current_file(None)
        self.set_modified(False)

        self.main_window.show_status("New workflow created", 3000)

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

            # Schedule validation after opening (delay to allow graph to fully load)
            from PySide6.QtCore import QTimer

            QTimer.singleShot(500, self._validate_after_open)

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
            self.main_window.add_to_recent_files(self._current_file)
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
            path = Path(file_path)
            self.workflow_saved.emit(file_path)
            self.set_current_file(path)
            self.set_modified(False)
            self.main_window.add_to_recent_files(path)
            self.main_window.show_status(f"Saved as: {path.name}", 3000)

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
            try:
                self.current_file_changed.emit(file_path)
            except RuntimeError as e:
                if "deleted" in str(e).lower():
                    # Signal source deleted during shutdown - safe to ignore
                    return
                raise
            self._update_window_title()

    def set_modified(self, modified: bool) -> None:
        """
        Set the modified state of the workflow.

        Args:
            modified: True if workflow has unsaved changes
        """
        if self._is_modified != modified:
            self._is_modified = modified
            try:
                self.modified_changed.emit(modified)
            except RuntimeError as e:
                if "deleted" in str(e).lower():
                    # Signal source deleted during shutdown - safe to ignore
                    return
                raise
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

        # Create styled message box
        msg_box = QMessageBox(self.main_window)
        msg_box.setWindowTitle("Unsaved Changes")
        msg_box.setText(f"The workflow '{file_name}' has unsaved changes.")
        msg_box.setInformativeText("Do you want to save before continuing?")
        msg_box.setStandardButtons(
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel
        )
        msg_box.setDefaultButton(QMessageBox.StandardButton.Save)

        # Style dialog to match UI Explorer
        msg_box.setStyleSheet("""
            QMessageBox {
                background: #252526;
            }
            QMessageBox QLabel {
                color: #D4D4D4;
                font-size: 12px;
            }
            QPushButton {
                background: #2D2D30;
                border: 1px solid #454545;
                border-radius: 4px;
                padding: 0 16px;
                color: #D4D4D4;
                font-size: 12px;
                font-weight: 500;
                min-height: 32px;
                min-width: 80px;
            }
            QPushButton:hover {
                background: #2A2D2E;
                border-color: #007ACC;
                color: white;
            }
            QPushButton:default {
                background: #007ACC;
                border-color: #007ACC;
                color: white;
            }
            QPushButton:default:hover {
                background: #1177BB;
            }
        """)

        reply = msg_box.exec()

        if reply == QMessageBox.StandardButton.Save:
            self.save_workflow()
            return not self._is_modified  # Only proceed if save succeeded
        elif reply == QMessageBox.StandardButton.Discard:
            return True
        else:  # Cancel
            return False

    def _get_message_box_style(self) -> str:
        """Get standard QMessageBox stylesheet matching UI Explorer."""
        return """
            QMessageBox { background: #252526; }
            QMessageBox QLabel { color: #D4D4D4; font-size: 12px; }
            QPushButton {
                background: #2D2D30;
                border: 1px solid #454545;
                border-radius: 4px;
                padding: 0 16px;
                color: #D4D4D4;
                font-size: 12px;
                font-weight: 500;
                min-height: 32px;
                min-width: 80px;
            }
            QPushButton:hover { background: #2A2D2E; border-color: #007ACC; color: white; }
            QPushButton:default { background: #007ACC; border-color: #007ACC; color: white; }
        """

    def _show_styled_message(
        self,
        title: str,
        text: str,
        info: str = "",
        icon: QMessageBox.Icon = QMessageBox.Icon.Warning,
    ) -> None:
        """Show a styled QMessageBox matching UI Explorer theme."""
        msg = QMessageBox(self.main_window)
        msg.setWindowTitle(title)
        msg.setText(text)
        if info:
            msg.setInformativeText(info)
        msg.setIcon(icon)
        msg.setStyleSheet(self._get_message_box_style())
        msg.exec()

    def _show_styled_question(
        self,
        title: str,
        text: str,
        buttons: QMessageBox.StandardButton = QMessageBox.StandardButton.Yes
        | QMessageBox.StandardButton.No,
        default: QMessageBox.StandardButton = QMessageBox.StandardButton.No,
    ) -> QMessageBox.StandardButton:
        """Show a styled QMessageBox question and return the reply."""
        msg = QMessageBox(self.main_window)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setStandardButtons(buttons)
        msg.setDefaultButton(default)
        msg.setStyleSheet(self._get_message_box_style())
        return msg.exec()

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
                reply = self._show_styled_question(
                    "Validation Errors",
                    f"The workflow has {len(validation_errors)} validation error(s).\n\n"
                    "Do you want to save anyway?",
                )
                return reply == QMessageBox.StandardButton.Yes

        return True

    def _validate_after_open(self) -> None:
        """Validate workflow after opening silently (no panel auto-open)."""
        # Directly call validation with show_panel=False to prevent auto-opening
        # Do NOT use validation_requested signal as it triggers show_panel=True
        self.main_window.validate_current_workflow(show_panel=False)

    def _update_window_title(self) -> None:
        """Update main window title with current file and modified state."""
        from casare_rpa.config import APP_NAME

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

        # Security: Limit clipboard size to prevent DoS (10MB)
        MAX_CLIPBOARD_SIZE = 10 * 1024 * 1024  # 10MB
        if len(text) > MAX_CLIPBOARD_SIZE:
            QMessageBox.warning(
                self.main_window,
                "Clipboard Too Large",
                f"Clipboard content is too large ({len(text) / (1024 * 1024):.1f} MB).\n"
                f"Maximum allowed size: 10 MB.\n\n"
                "This prevents memory exhaustion from malicious clipboard data.",
            )
            logger.warning(
                f"Rejected clipboard paste: size={len(text)} bytes (limit={MAX_CLIPBOARD_SIZE})"
            )
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

            # SECURITY: Full schema validation to prevent code injection
            # and resource exhaustion attacks from malicious clipboard data
            try:
                validate_workflow_json(data)
                logger.debug("Clipboard workflow schema validation passed")
            except ValidationError as e:
                logger.error(f"Clipboard workflow schema validation failed: {e}")
                QMessageBox.warning(
                    self.main_window,
                    "Invalid Workflow",
                    f"The clipboard content failed security validation:\n\n"
                    f"{str(e)[:500]}",
                )
                return
            except Exception as e:
                # Log but continue for backwards compatibility
                logger.warning(f"Schema validation skipped (non-standard format): {e}")

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

                # SECURITY: Validate dropped workflow against schema
                try:
                    validate_workflow_json(data)
                    logger.debug("Dropped workflow schema validation passed")
                except ValidationError as e:
                    logger.error(f"Dropped workflow schema validation failed: {e}")
                    QMessageBox.warning(
                        self.main_window,
                        "Invalid Workflow",
                        f"The dropped file failed security validation:\n\n"
                        f"{str(e)[:500]}",
                    )
                    return
                except Exception as e:
                    # Log but continue for backwards compatibility
                    logger.warning(
                        f"Schema validation skipped (non-standard format): {e}"
                    )

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

                # SECURITY: Validate dropped JSON data against schema
                try:
                    validate_workflow_json(data)
                    logger.debug("Dropped JSON data schema validation passed")
                except ValidationError as e:
                    logger.error(f"Dropped JSON data schema validation failed: {e}")
                    QMessageBox.warning(
                        self.main_window,
                        "Invalid Workflow",
                        f"The dropped data failed security validation:\n\n"
                        f"{str(e)[:500]}",
                    )
                    return
                except Exception as e:
                    # Log but continue for backwards compatibility
                    logger.warning(
                        f"Schema validation skipped (non-standard format): {e}"
                    )

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
        else:
            logger.debug("Graph does not support drag-drop import")

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

    # =========================
    # Remote Execution Methods
    # =========================

    async def run_local(self) -> None:
        """
        Execute workflow locally in Canvas (current behavior).

        This is the existing local execution - no changes needed.
        The execution controller handles this via execute_workflow().
        """
        logger.info("Run Local selected - delegating to execution controller")
        # Note: Main window's execution controller handles local execution
        # This method is here for API consistency with other execution modes

    async def run_on_robot(self) -> None:
        """
        Submit workflow to LAN robot via Orchestrator API.

        Flow:
        1. Serialize current workflow
        2. Submit via OrchestratorClient with execution_mode=lan
        3. Orchestrator queues job for LAN robots
        4. Show confirmation with job_id
        """
        logger.info("Run on Robot selected - submitting to Orchestrator")

        # Check if workflow has been saved
        if not self._current_file:
            reply = QMessageBox.question(
                self.main_window,
                "Save Workflow?",
                "Workflow must be saved before submitting to robot.\n\n" "Save now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.save_workflow()
                if not self._current_file:  # Save was cancelled
                    return
            else:
                return

        # Serialize workflow using the data provider
        workflow_json = self.main_window._get_workflow_data()
        if not workflow_json:
            self.main_window.show_status("No workflow to submit", 3000)
            return

        # Note: Keep nodes as dict - Robot's workflow_loader expects dict format
        # keyed by node_id. API accepts both dict and list formats.

        # Detect Schedule Trigger nodes and extract scheduling info
        trigger_type, schedule_config = self._extract_schedule_trigger_info(
            workflow_json
        )
        schedule_cron = None

        if trigger_type == "scheduled" and schedule_config:
            schedule_cron = schedule_config.get("cron_expression")
            self.main_window.show_status(
                f"Creating scheduled workflow (cron: {schedule_cron})...", 3000
            )
        else:
            trigger_type = "manual"
            self.main_window.show_status("Submitting workflow to robot...", 3000)

        # Submit via OrchestratorClient (Application layer)
        client = self._get_orchestrator_client()

        # Build metadata with workflow_json for scheduled execution
        metadata = {
            "submitted_from": "canvas",
            "canvas_file": str(self._current_file) if self._current_file else None,
        }
        if schedule_config:
            metadata["schedule_config"] = schedule_config
            # Include workflow_json in metadata for schedule execution
            metadata["workflow_json"] = workflow_json

        result = await client.submit_workflow(
            workflow_name=self._current_file.stem if self._current_file else "Untitled",
            workflow_json=workflow_json,
            execution_mode="lan",
            trigger_type=trigger_type,
            priority=10,
            metadata=metadata,
            schedule_cron=schedule_cron,
        )

        if result.success:
            job_id = result.job_id or "unknown"
            workflow_id = result.workflow_id or "unknown"

            self.main_window.show_status(
                f"Workflow submitted to robot! Job ID: {job_id[:8]}...",
                5000,
            )

            # Show success dialog with schedule info if applicable
            schedule_id = result.schedule_id
            if schedule_id:
                QMessageBox.information(
                    self.main_window,
                    "Workflow Scheduled",
                    f"Workflow scheduled on LAN robot successfully!\n\n"
                    f"Workflow ID: {workflow_id}\n"
                    f"Schedule ID: {schedule_id}\n"
                    f"Cron: {schedule_cron}\n\n"
                    f"View and manage in Fleet Dashboard → Schedules tab.",
                )
            else:
                QMessageBox.information(
                    self.main_window,
                    "Workflow Submitted",
                    f"Workflow submitted to LAN robot successfully!\n\n"
                    f"Workflow ID: {workflow_id}\n"
                    f"Job ID: {job_id}\n\n"
                    f"Monitor execution in the Monitoring Dashboard.",
                )
        else:
            self.main_window.show_status(f"Submission failed: {result.message}", 5000)

            # Distinguish connection errors from API errors
            if "connect" in (result.error or "").lower():
                QMessageBox.critical(
                    self.main_window,
                    "Connection Error",
                    f"Could not connect to Orchestrator.\n\n"
                    f"Error: {result.error}\n\n"
                    f"Ensure Orchestrator API is running:\n"
                    f"uvicorn casare_rpa.infrastructure.orchestrator.api.main:app",
                )
            else:
                QMessageBox.critical(
                    self.main_window,
                    "Submission Failed",
                    f"Failed to submit workflow to robot.\n\n"
                    f"{result.message}\n"
                    f"Error: {result.error[:200] if result.error else 'Unknown'}",
                )

    async def submit_for_internet_robots(self) -> None:
        """
        Submit workflow for internet robots (client PCs).

        Flow:
        1. Serialize current workflow
        2. Submit via OrchestratorClient with execution_mode=internet
        3. Orchestrator queues job for internet robots
        4. Show confirmation with workflow_id
        """
        logger.info(
            "Submit for Internet Robots selected - queuing for remote execution"
        )

        # Check if workflow has been saved
        if not self._current_file:
            reply = QMessageBox.question(
                self.main_window,
                "Save Workflow?",
                "Workflow must be saved before submitting.\n\n" "Save now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.save_workflow()
                if not self._current_file:  # Save was cancelled
                    return
            else:
                return

        # Serialize workflow using the data provider
        workflow_json = self.main_window._get_workflow_data()
        if not workflow_json:
            self.main_window.show_status("No workflow to submit", 3000)
            return

        # Note: Keep nodes as dict - Robot's workflow_loader expects dict format
        # keyed by node_id. API accepts both dict and list formats.

        # Detect Schedule Trigger nodes and extract scheduling info
        trigger_type, schedule_config = self._extract_schedule_trigger_info(
            workflow_json
        )
        schedule_cron = None

        if trigger_type == "scheduled" and schedule_config:
            schedule_cron = schedule_config.get("cron_expression")
            self.main_window.show_status(
                f"Creating scheduled workflow for internet robots (cron: {schedule_cron})...",
                3000,
            )
        else:
            trigger_type = "manual"
            self.main_window.show_status(
                "Submitting workflow for internet robots...", 3000
            )

        # Submit via OrchestratorClient (Application layer)
        client = self._get_orchestrator_client()

        # Build metadata with workflow_json for scheduled execution
        metadata = {
            "submitted_from": "canvas",
            "canvas_file": str(self._current_file) if self._current_file else None,
        }
        if schedule_config:
            metadata["schedule_config"] = schedule_config
            # Include workflow_json in metadata for schedule execution
            metadata["workflow_json"] = workflow_json

        result = await client.submit_workflow(
            workflow_name=self._current_file.stem if self._current_file else "Untitled",
            workflow_json=workflow_json,
            execution_mode="internet",
            trigger_type=trigger_type,
            priority=10,
            metadata=metadata,
            schedule_cron=schedule_cron,
        )

        if result.success:
            job_id = result.job_id or "unknown"
            workflow_id = result.workflow_id or "unknown"

            self.main_window.show_status(
                f"Workflow queued! Job ID: {job_id[:8]}...",
                5000,
            )

            # Show success dialog with schedule info if applicable
            schedule_id = result.schedule_id
            if schedule_id:
                QMessageBox.information(
                    self.main_window,
                    "Workflow Scheduled",
                    f"Workflow scheduled for internet robots successfully!\n\n"
                    f"Workflow ID: {workflow_id}\n"
                    f"Schedule ID: {schedule_id}\n"
                    f"Cron: {schedule_cron}\n\n"
                    f"View and manage in Fleet Dashboard → Schedules tab.",
                )
            else:
                QMessageBox.information(
                    self.main_window,
                    "Workflow Queued",
                    f"Workflow queued for internet robots successfully!\n\n"
                    f"Workflow ID: {workflow_id}\n"
                    f"Job ID: {job_id}\n\n"
                    f"The first available internet robot will claim and execute this job.\n\n"
                    f"Monitor execution in the Monitoring Dashboard.",
                )
        else:
            self.main_window.show_status(f"Submission failed: {result.message}", 5000)

            # Distinguish connection errors from API errors
            if "connect" in (result.error or "").lower():
                QMessageBox.critical(
                    self.main_window,
                    "Connection Error",
                    f"Could not connect to Orchestrator.\n\n"
                    f"Error: {result.error}\n\n"
                    f"Ensure Orchestrator API is running:\n"
                    f"uvicorn casare_rpa.infrastructure.orchestrator.api.main:app",
                )
            else:
                QMessageBox.critical(
                    self.main_window,
                    "Submission Failed",
                    f"Failed to queue workflow.\n\n"
                    f"{result.message}\n"
                    f"Error: {result.error[:200] if result.error else 'Unknown'}",
                )

    # =========================
    # Version History Methods
    # =========================

    def get_version_history(self) -> Optional["VersionHistory"]:
        """
        Get version history for the current workflow.

        Returns:
            VersionHistory if workflow has been saved and has history,
            None otherwise.

        Note:
            Version history is created when a workflow is first saved
            and updated on each subsequent save.
        """
        from casare_rpa.domain.workflow.versioning import VersionHistory

        if not self._current_file:
            logger.debug("No current file - no version history available")
            return None

        # Get workflow data from the graph
        graph = self.main_window.get_graph()
        if not graph:
            logger.debug("No graph available - no version history")
            return None

        # Try to load or create version history for this workflow
        workflow_id = str(self._current_file.stem)

        try:
            # Check for existing version history file
            history_file = self._current_file.parent / f".{workflow_id}_history.json"

            if history_file.exists():
                # Load existing history
                import orjson

                history_data = orjson.loads(history_file.read_bytes())
                history = VersionHistory.from_dict(history_data)
                logger.debug(f"Loaded version history for {workflow_id}")
                return history
            else:
                # Create new history with current workflow as v1.0.0
                workflow_data = self._serialize_workflow()
                if workflow_data:
                    history = VersionHistory(workflow_id=workflow_id)
                    history.create_new_version(
                        workflow_data=workflow_data,
                        change_summary="Initial version",
                    )
                    # Save history file
                    self._save_version_history(history, history_file)
                    logger.debug(f"Created new version history for {workflow_id}")
                    return history

        except Exception as e:
            logger.warning(f"Failed to get version history: {e}")

        return None

    def _serialize_workflow(self) -> Optional[dict]:
        """Serialize current workflow to dict."""
        graph = self.main_window.get_graph()
        if not graph:
            return None

        try:
            # Use existing serialization method if available
            if hasattr(graph, "serialize_session"):
                return graph.serialize_session()
            elif hasattr(graph, "to_dict"):
                return graph.to_dict()
            else:
                # Manual serialization
                return {
                    "nodes": [],
                    "connections": [],
                    "metadata": {
                        "name": self._current_file.stem
                        if self._current_file
                        else "Untitled"
                    },
                }
        except Exception as e:
            logger.warning(f"Failed to serialize workflow: {e}")
            return None

    def _save_version_history(self, history: "VersionHistory", path: Path) -> None:
        """Save version history to file."""
        try:
            import orjson

            path.write_bytes(
                orjson.dumps(history.to_dict(), option=orjson.OPT_INDENT_2)
            )
            logger.debug(f"Saved version history to {path}")
        except Exception as e:
            logger.warning(f"Failed to save version history: {e}")
