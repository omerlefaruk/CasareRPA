"""
Project Autosave Controller.

Automatically saves all project data:
- Workflow/scenario to project/scenarios/
- Variables to project/variables.json
- Credentials bindings to project/credentials.json
- Project settings to project/project.json
- Environment settings to project/environments/
"""

import re
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Optional

import orjson
from loguru import logger
from PySide6.QtCore import QObject, QTimer, Signal

from casare_rpa.presentation.canvas.events.event import Event
from casare_rpa.presentation.canvas.events.event_bus import EventBus
from casare_rpa.presentation.canvas.events.event_types import EventType

if TYPE_CHECKING:
    from casare_rpa.domain.entities.project import Project
    from casare_rpa.presentation.canvas.main_window import MainWindow

# Background thread pool for I/O
_project_save_executor: ThreadPoolExecutor | None = None
_project_save_lock = threading.Lock()


class ProjectAutosaveController(QObject):
    """
    Manages automatic saving of all project data.

    Saves on:
    - Timer interval (configurable, default 60s)
    - Variable changes
    - Credential changes
    - Environment changes
    - Node changes (debounced)

    Signals:
        project_saved: Emitted when project is saved
        save_failed: Emitted on save failure
    """

    project_saved = Signal(str)  # project_path
    save_failed = Signal(str)  # error_message

    def __init__(self, main_window: "MainWindow"):
        super().__init__(main_window)
        self._main_window = main_window
        self._current_project: Project | None = None
        self._current_project_path: Path | None = None

        # Timers
        self._autosave_timer: QTimer | None = None
        self._debounce_timer: QTimer | None = None

        # State
        self._dirty = False
        self._save_in_progress = False
        self._autosave_interval_ms = 60000  # 60 seconds default

        # EventBus
        self._event_bus = EventBus()

        # Initialize thread pool
        global _project_save_executor
        with _project_save_lock:
            if _project_save_executor is None:
                _project_save_executor = ThreadPoolExecutor(
                    max_workers=1, thread_name_prefix="project_save"
                )

    def initialize(self) -> None:
        """Initialize controller and timers."""
        # Autosave timer
        self._autosave_timer = QTimer(self)
        self._autosave_timer.timeout.connect(self._on_autosave_timer)
        self._autosave_timer.start(self._autosave_interval_ms)

        # Debounce timer for rapid changes
        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.timeout.connect(self._save_project)

        # Subscribe to events that should trigger save
        self._event_bus.subscribe(EventType.VARIABLE_SET, self._mark_dirty)
        self._event_bus.subscribe(EventType.VARIABLE_UPDATED, self._mark_dirty)
        self._event_bus.subscribe(EventType.VARIABLE_DELETED, self._mark_dirty)
        self._event_bus.subscribe(EventType.NODE_ADDED, self._mark_dirty_debounced)
        self._event_bus.subscribe(EventType.NODE_REMOVED, self._mark_dirty_debounced)
        self._event_bus.subscribe(EventType.NODE_POSITION_CHANGED, self._mark_dirty_debounced)
        self._event_bus.subscribe(EventType.CONNECTION_ADDED, self._mark_dirty_debounced)
        self._event_bus.subscribe(EventType.CONNECTION_REMOVED, self._mark_dirty_debounced)

        # Credential events
        if hasattr(EventType, "CREDENTIAL_ADDED"):
            self._event_bus.subscribe(EventType.CREDENTIAL_ADDED, self._mark_dirty)
            self._event_bus.subscribe(EventType.CREDENTIAL_UPDATED, self._mark_dirty)
            self._event_bus.subscribe(EventType.CREDENTIAL_DELETED, self._mark_dirty)

        logger.info("ProjectAutosaveController initialized")

    def cleanup(self) -> None:
        """Clean up resources."""
        if self._autosave_timer:
            self._autosave_timer.stop()
        if self._debounce_timer:
            self._debounce_timer.stop()

        # Final save if dirty
        if self._dirty and self._current_project_path:
            self._save_project_sync()

        logger.info("ProjectAutosaveController cleanup")

    # =========================================================================
    # Public API
    # =========================================================================

    def set_project(self, project: "Project", project_path: Path) -> None:
        """
        Set the current project to autosave.

        Args:
            project: Project entity
            project_path: Path to project directory
        """
        # Save current project first if dirty
        if self._dirty and self._current_project_path:
            self._save_project_sync()

        self._current_project = project
        self._current_project_path = project_path
        self._dirty = False

        logger.info(f"Project autosave active: {project_path}")

    def clear_project(self) -> None:
        """Clear current project (save first if dirty)."""
        if self._dirty and self._current_project_path:
            self._save_project_sync()

        self._current_project = None
        self._current_project_path = None
        self._dirty = False

    def save_now(self) -> None:
        """Force immediate save."""
        if self._debounce_timer:
            self._debounce_timer.stop()
        self._save_project()

    def set_autosave_interval(self, seconds: int) -> None:
        """Set autosave interval in seconds."""
        self._autosave_interval_ms = seconds * 1000
        if self._autosave_timer and self._autosave_timer.isActive():
            self._autosave_timer.setInterval(self._autosave_interval_ms)

    def is_dirty(self) -> bool:
        """Check if project has unsaved changes."""
        return self._dirty

    # =========================================================================
    # Private Methods
    # =========================================================================

    def _mark_dirty(self, event: Event | None = None) -> None:
        """Mark project as having unsaved changes."""
        self._dirty = True

    def _mark_dirty_debounced(self, event: Event | None = None) -> None:
        """Mark dirty and schedule debounced save."""
        self._dirty = True
        if self._debounce_timer:
            self._debounce_timer.start(2000)  # 2 second debounce

    def _on_autosave_timer(self) -> None:
        """Handle autosave timer - save if dirty."""
        if self._dirty and not self._save_in_progress:
            self._save_project()

    def _save_project(self) -> None:
        """Save project data asynchronously."""
        if not self._current_project_path or self._save_in_progress:
            return

        self._save_in_progress = True

        try:
            # Gather all data on main thread
            project_data = self._gather_project_data()

            if project_data and _project_save_executor:
                # Save in background
                future = _project_save_executor.submit(
                    self._save_project_files, project_data, self._current_project_path
                )
                future.add_done_callback(self._on_save_complete)
            else:
                # Fallback to sync save
                self._save_project_sync()

        except Exception as e:
            logger.error(f"Project save failed: {e}")
            self._save_in_progress = False
            self.save_failed.emit(str(e))

    def _save_project_sync(self) -> None:
        """Save project synchronously (for cleanup/shutdown)."""
        if not self._current_project_path:
            return

        try:
            project_data = self._gather_project_data()
            if project_data:
                self._save_project_files(project_data, self._current_project_path)
            self._dirty = False
            logger.info(f"Project saved: {self._current_project_path}")
        except Exception as e:
            logger.error(f"Sync project save failed: {e}")

    def _gather_project_data(self) -> dict[str, Any] | None:
        """
        Gather all project data from UI components.

        Returns:
            Dictionary with all project data or None
        """
        data = {
            "project": None,
            "workflow": None,
            "variables": None,
        }

        # Get workflow data
        if hasattr(self._main_window, "get_workflow_data"):
            data["workflow"] = self._main_window.get_workflow_data()

        # Get variables from panel
        if hasattr(self._main_window, "_bottom_panel") and self._main_window._bottom_panel:
            variables_tab = self._main_window._bottom_panel.get_variables_tab()
            if variables_tab and hasattr(variables_tab, "get_all_variables_flat"):
                data["variables"] = variables_tab.get_all_variables_flat()

        # Get project metadata
        if self._current_project:
            data["project"] = self._current_project.to_dict()

        return data

    def _save_project_files(self, data: dict[str, Any], project_path: Path) -> None:
        """
        Save all project files (runs in background thread).

        Args:
            data: Project data dictionary
            project_path: Project directory path
        """
        # Ensure directories exist
        project_path.mkdir(parents=True, exist_ok=True)
        (project_path / "scenarios").mkdir(exist_ok=True)
        (project_path / "environments").mkdir(exist_ok=True)

        # Save workflow as scenario
        if data.get("workflow"):
            workflow_name = data["workflow"].get("metadata", {}).get("name") or "main"
            safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", workflow_name).strip("_")
            scenario_id = safe_name or "main"
            scenario_path = project_path / "scenarios" / f"{scenario_id}.json"
            scenario_path.write_bytes(orjson.dumps(data["workflow"], option=orjson.OPT_INDENT_2))

        # Save variables
        if data.get("variables"):
            variables_path = project_path / "variables.json"
            variables_data = {"scope": "project", "variables": data["variables"]}
            variables_path.write_bytes(orjson.dumps(variables_data, option=orjson.OPT_INDENT_2))

        # Save project.json
        if data.get("project"):
            project_file = project_path / "project.json"
            project_file.write_bytes(orjson.dumps(data["project"], option=orjson.OPT_INDENT_2))

        # Create marker file
        marker = project_path / ".casare_project"
        if not marker.exists():
            marker.touch()

    def _on_save_complete(self, future) -> None:
        """Handle background save completion."""
        from PySide6.QtCore import QTimer

        self._save_in_progress = False

        try:
            future.result()  # Raise any exception
            self._dirty = False
            QTimer.singleShot(0, lambda: self._emit_saved())
        except Exception as e:
            logger.error(f"Background project save failed: {e}")
            QTimer.singleShot(0, lambda err=e: self.save_failed.emit(str(err)))

    def _emit_saved(self) -> None:
        """Emit saved signal on main thread."""
        if self._current_project_path:
            self.project_saved.emit(str(self._current_project_path))
            logger.debug(f"Project autosaved: {self._current_project_path}")
