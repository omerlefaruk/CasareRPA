"""
Project controller for managing projects in the Canvas UI.

Coordinates between the ProjectManagerDialog and the application layer use cases.
"""

from pathlib import Path
from typing import TYPE_CHECKING, Optional

from loguru import logger
from PySide6.QtCore import Signal

from casare_rpa.presentation.canvas.controllers.base_controller import BaseController

if TYPE_CHECKING:
    from casare_rpa.domain.entities.project import Project, ProjectIndexEntry
    from casare_rpa.presentation.canvas.main_window import MainWindow


class ProjectController(BaseController):
    """
    Controller for project management operations.

    Responsibilities:
    - Show project manager dialog
    - Create new projects
    - Open existing projects
    - Track current project state
    - Coordinate with application layer use cases

    Signals:
        project_opened: Emitted when a project is opened (Project)
        project_closed: Emitted when project is closed
        project_created: Emitted when new project created (Project)
    """

    project_opened = Signal(object)  # Project
    project_closed = Signal()
    project_created = Signal(object)  # Project
    scenario_opened = Signal(str, str)  # project_path, scenario_path

    def __init__(self, main_window: "MainWindow") -> None:
        """
        Initialize project controller.

        Args:
            main_window: Reference to main window
        """
        super().__init__(main_window)
        self._current_project: Project | None = None
        self._repository = None
        self._dialog = None

    def initialize(self) -> None:
        """Initialize controller and setup repository."""
        super().initialize()
        self._setup_repository()

    def cleanup(self) -> None:
        """Clean up controller resources."""
        super().cleanup()
        self._current_project = None

    def _setup_repository(self) -> None:
        """Setup project repository instance."""
        try:
            from casare_rpa.infrastructure.persistence import (
                FileSystemProjectRepository,
            )

            self._repository = FileSystemProjectRepository()
            logger.debug("Project repository initialized")
        except Exception as e:
            logger.error(f"Failed to initialize project repository: {e}")

    @property
    def current_project(self) -> Optional["Project"]:
        """Get current project."""
        return self._current_project

    @property
    def has_project(self) -> bool:
        """Check if a project is currently open."""
        return self._current_project is not None

    async def get_recent_projects(self) -> list["ProjectIndexEntry"]:
        """
        Get list of recent projects.

        Returns:
            List of recent project index entries
        """
        if self._repository is None:
            return []

        try:
            index = await self._repository.get_projects_index()
            return index.get_recent_projects()
        except Exception as e:
            logger.error(f"Failed to get recent projects: {e}")
            return []

    def load_project(self, project_path: str) -> None:
        """
        Load a project from the given path.

        Public API for loading projects programmatically.

        Args:
            project_path: Path to the project directory
        """
        self._on_project_opened(project_path)

    def show_project_manager(self) -> None:
        """Show project manager dialog."""
        import asyncio

        # Get recent projects asynchronously
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Use Qt's event loop integration
                import qasync

                future = qasync.asyncio.ensure_future(self.get_recent_projects())
                future.add_done_callback(lambda f: self._show_dialog_with_projects(f.result()))
            else:
                recent = loop.run_until_complete(self.get_recent_projects())
                self._show_dialog_with_projects(recent)
        except RuntimeError:
            # No event loop, show dialog without recent projects
            self._show_dialog_with_projects([])

    def _show_dialog_with_projects(self, recent_projects: list["ProjectIndexEntry"]) -> None:
        """
        Show project manager dialog.

        Args:
            recent_projects: List of recent project entries
        """
        from ..ui.dialogs import ProjectManagerDialog

        dialog = ProjectManagerDialog(
            recent_projects=recent_projects,
            parent=self.main_window,
        )

        # Connect signals
        dialog.project_created.connect(self._on_project_created)
        dialog.project_opened.connect(self._on_project_opened)
        dialog.scenario_opened.connect(self._on_scenario_opened)

        self._dialog = dialog
        dialog.exec()
        self._dialog = None

    def _on_project_created(self, project_data: dict) -> None:
        """
        Handle project creation from dialog.

        Args:
            project_data: Dictionary with project info (name, path, description, author)
        """
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import qasync

                future = qasync.asyncio.ensure_future(self._create_project_async(project_data))
                future.add_done_callback(lambda f: self._handle_create_result(f))
            else:
                loop.run_until_complete(self._create_project_async(project_data))
        except RuntimeError as e:
            logger.error(f"Failed to create project: {e}")

    async def _create_project_async(self, project_data: dict) -> None:
        """
        Create project asynchronously.

        Args:
            project_data: Dictionary with project info
        """
        if self._repository is None:
            logger.error("Repository not initialized")
            return

        try:
            from casare_rpa.application.use_cases import CreateProjectUseCase

            use_case = CreateProjectUseCase(self._repository)
            result = await use_case.execute(
                name=project_data["name"],
                path=project_data["path"],
                description=project_data.get("description", ""),
                author=project_data.get("author", ""),
            )

            if result.success and result.project:
                self._current_project = result.project
                self.project_created.emit(result.project)
                self.project_opened.emit(result.project)
                logger.info(f"Created project: {result.project.name}")
            else:
                logger.error(f"Failed to create project: {result.error}")
                self._show_error("Project Creation Failed", result.error or "Unknown error")

        except Exception as e:
            logger.error(f"Failed to create project: {e}")
            self._show_error("Project Creation Failed", str(e))

    def _handle_create_result(self, future) -> None:
        """Handle async create result."""
        try:
            future.result()
        except Exception as e:
            logger.error(f"Project creation failed: {e}")

    def _on_project_opened(self, path: str) -> None:
        """
        Handle project open from dialog.

        Args:
            path: Path to project folder
        """
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import qasync

                future = qasync.asyncio.ensure_future(self._open_project_async(Path(path)))
                future.add_done_callback(lambda f: self._handle_open_result(f))
            else:
                loop.run_until_complete(self._open_project_async(Path(path)))
        except RuntimeError as e:
            logger.error(f"Failed to open project: {e}")

    async def _open_project_async(self, path: Path) -> None:
        """
        Open project asynchronously.

        Args:
            path: Path to project folder
        """
        if self._repository is None:
            logger.error("Repository not initialized")
            return

        try:
            from casare_rpa.application.use_cases import LoadProjectUseCase

            use_case = LoadProjectUseCase(self._repository)
            result = await use_case.execute(path=path)

            if result.success and result.project:
                self._current_project = result.project
                self.project_opened.emit(result.project)
                logger.info(f"Opened project: {result.project.name}")
            else:
                logger.error(f"Failed to open project: {result.error}")
                self._show_error("Project Open Failed", result.error or "Unknown error")

        except Exception as e:
            logger.error(f"Failed to open project: {e}")
            self._show_error("Project Open Failed", str(e))

    def _handle_open_result(self, future) -> None:
        """Handle async open result."""
        try:
            future.result()
        except Exception as e:
            logger.error(f"Project open failed: {e}")

    def _on_project_removed(self, project_id: str) -> None:
        """
        Handle project removal from recent list.

        Args:
            project_id: ID of project to remove
        """
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import qasync

                qasync.asyncio.ensure_future(self._remove_project_async(project_id))
            else:
                loop.run_until_complete(self._remove_project_async(project_id))
        except RuntimeError as e:
            logger.error(f"Failed to remove project from list: {e}")

    async def _remove_project_async(self, project_id: str) -> None:
        """
        Remove project from index asynchronously.

        Args:
            project_id: ID of project to remove
        """
        if self._repository is None:
            return

        try:
            index = await self._repository.get_projects_index()
            index.remove_project(project_id)
            await self._repository.save_projects_index(index)
            logger.info(f"Removed project {project_id} from index")
        except Exception as e:
            logger.error(f"Failed to remove project from index: {e}")

    def _on_scenario_opened(self, project_path: str, scenario_path: str) -> None:
        """
        Handle scenario open from dialog.

        Args:
            project_path: Path to project folder
            scenario_path: Path to scenario JSON file
        """
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import qasync

                future = qasync.asyncio.ensure_future(
                    self._open_scenario_async(Path(project_path), Path(scenario_path))
                )
                future.add_done_callback(lambda f: self._handle_scenario_open_result(f))
            else:
                loop.run_until_complete(
                    self._open_scenario_async(Path(project_path), Path(scenario_path))
                )
        except RuntimeError as e:
            logger.error(f"Failed to open scenario: {e}")

    async def _open_scenario_async(self, project_path: Path, scenario_path: Path) -> None:
        """
        Open scenario asynchronously.

        First opens the project, then emits scenario_opened signal.

        Args:
            project_path: Path to project folder
            scenario_path: Path to scenario JSON file
        """
        # First open the project if not already open
        if self._current_project is None or self._current_project.path != project_path:
            await self._open_project_async(project_path)

        # Emit scenario_opened signal for MainWindow to handle
        if self._current_project:
            self.scenario_opened.emit(str(project_path), str(scenario_path))
            logger.info(f"Opened scenario: {scenario_path.stem}")

    def _handle_scenario_open_result(self, future) -> None:
        """Handle async scenario open result."""
        try:
            future.result()
        except Exception as e:
            logger.error(f"Scenario open failed: {e}")

    def close_project(self) -> None:
        """Close the current project."""
        if self._current_project:
            logger.info(f"Closing project: {self._current_project.name}")
            self._current_project = None
            self.project_closed.emit()

    def _show_error(self, title: str, message: str) -> None:
        """
        Show error message to user.

        Args:
            title: Error title
            message: Error message
        """
        from PySide6.QtWidgets import QMessageBox

        QMessageBox.critical(self.main_window, title, message)
