"""
CasareRPA - FileSystemProjectRepository

Infrastructure implementation of ProjectRepository using the file system.
Wraps ProjectStorage for file I/O operations.
"""

from pathlib import Path
from typing import List, Optional

import orjson
from loguru import logger

from casare_rpa.domain.entities.project import (
    CredentialBindingsFile,
    Project,
    ProjectsIndex,
    Scenario,
    VariableScope,
    VariablesFile,
)
from casare_rpa.domain.repositories import ProjectRepository
from casare_rpa.infrastructure.persistence.project_storage import ProjectStorage


class FileSystemProjectRepository(ProjectRepository):
    """
    File system implementation of ProjectRepository.

    Uses ProjectStorage for file I/O operations.
    All methods are async for interface compliance but execute synchronously.
    """

    def __init__(self) -> None:
        """Initialize repository."""
        self._storage = ProjectStorage
        # Cache project index to avoid repeated file reads
        self._index_cache: ProjectsIndex | None = None

    def _invalidate_cache(self) -> None:
        """Invalidate the index cache."""
        self._index_cache = None

    # =========================================================================
    # Project Operations
    # =========================================================================

    async def get_by_id(self, project_id: str) -> Project | None:
        """Get project by ID."""
        try:
            index = await self.get_projects_index()
            entry = index.get_project(project_id)
            if entry is None:
                return None

            path = Path(entry.path)
            if not path.exists():
                logger.warning(f"Project path does not exist: {path}")
                return None

            return self._storage.load_project(path)
        except Exception as e:
            logger.error(f"Failed to get project by ID {project_id}: {e}")
            return None

    async def get_by_path(self, path: Path) -> Project | None:
        """Get project by folder path."""
        try:
            if not self._storage.is_project_folder(path):
                return None
            return self._storage.load_project(path)
        except Exception as e:
            logger.error(f"Failed to get project by path {path}: {e}")
            return None

    async def get_all(self) -> list[Project]:
        """Get all registered projects."""
        projects = []
        try:
            index = await self.get_projects_index()
            for entry in index.projects:
                path = Path(entry.path)
                if path.exists():
                    try:
                        project = self._storage.load_project(path)
                        projects.append(project)
                    except Exception as e:
                        logger.warning(f"Failed to load project {entry.name}: {e}")
        except Exception as e:
            logger.error(f"Failed to get all projects: {e}")
        return projects

    async def save(self, project: Project) -> None:
        """Save or update project."""
        try:
            if project.path is None:
                raise ValueError("Project path is not set")

            # Create folder structure if new project
            if not project.path.exists():
                self._storage.create_project_structure(project.path)

            # Save project metadata
            self._storage.save_project(project)

            # Update index
            index = await self.get_projects_index()
            index.add_project(project)
            await self.save_projects_index(index)

            logger.info(f"Saved project: {project.name}")
        except Exception as e:
            logger.error(f"Failed to save project {project.name}: {e}")
            raise

    async def delete(self, project_id: str, remove_files: bool = False) -> None:
        """Delete project."""
        try:
            project = await self.get_by_id(project_id)
            if project:
                self._storage.delete_project(project, remove_files=remove_files)
                self._invalidate_cache()
            else:
                # Just remove from index
                index = await self.get_projects_index()
                index.remove_project(project_id)
                await self.save_projects_index(index)
        except Exception as e:
            logger.error(f"Failed to delete project {project_id}: {e}")
            raise

    async def exists(self, project_id: str) -> bool:
        """Check if project exists."""
        index = await self.get_projects_index()
        entry = index.get_project(project_id)
        if entry is None:
            return False
        return Path(entry.path).exists()

    # =========================================================================
    # Scenario Operations
    # =========================================================================

    async def get_scenario(self, project_id: str, scenario_id: str) -> Scenario | None:
        """Get scenario by ID."""
        try:
            project = await self.get_by_id(project_id)
            if project is None or project.scenarios_dir is None:
                return None

            scenario_file = project.scenarios_dir / f"{scenario_id}.json"
            if not scenario_file.exists():
                return None

            data = orjson.loads(scenario_file.read_bytes())
            return Scenario.from_dict(data)
        except Exception as e:
            logger.error(f"Failed to get scenario {scenario_id}: {e}")
            return None

    async def get_scenarios(self, project_id: str) -> list[Scenario]:
        """Get all scenarios for a project."""
        scenarios = []
        try:
            project = await self.get_by_id(project_id)
            if project is None:
                return scenarios

            scenario_files = self._storage.list_scenario_files(project)
            for file_path in scenario_files:
                try:
                    data = orjson.loads(file_path.read_bytes())
                    scenario = Scenario.from_dict(data)
                    scenarios.append(scenario)
                except Exception as e:
                    logger.warning(f"Failed to load scenario {file_path}: {e}")
        except Exception as e:
            logger.error(f"Failed to get scenarios for project {project_id}: {e}")
        return scenarios

    async def save_scenario(self, project_id: str, scenario: Scenario) -> None:
        """Save scenario to project."""
        try:
            project = await self.get_by_id(project_id)
            if project is None:
                raise ValueError(f"Project not found: {project_id}")

            if project.scenarios_dir is None:
                raise ValueError("Project scenarios directory not set")

            # Ensure scenarios directory exists
            project.scenarios_dir.mkdir(parents=True, exist_ok=True)

            # Update timestamp
            scenario.touch_modified()

            # Save scenario
            scenario_file = project.scenarios_dir / f"{scenario.id}.json"
            json_data = orjson.dumps(
                scenario.to_dict(),
                option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS,
            )
            scenario_file.write_bytes(json_data)

            logger.debug(f"Saved scenario: {scenario.name}")
        except Exception as e:
            logger.error(f"Failed to save scenario: {e}")
            raise

    async def delete_scenario(self, project_id: str, scenario_id: str) -> None:
        """Delete scenario from project."""
        try:
            project = await self.get_by_id(project_id)
            if project is None or project.scenarios_dir is None:
                return

            scenario_file = project.scenarios_dir / f"{scenario_id}.json"
            if scenario_file.exists():
                scenario_file.unlink()
                logger.info(f"Deleted scenario: {scenario_id}")
        except Exception as e:
            logger.error(f"Failed to delete scenario {scenario_id}: {e}")
            raise

    # =========================================================================
    # Variables Operations
    # =========================================================================

    async def get_project_variables(self, project_id: str) -> VariablesFile:
        """Get project-level variables."""
        try:
            project = await self.get_by_id(project_id)
            if project is None:
                return VariablesFile(scope=VariableScope.PROJECT)
            return self._storage.load_project_variables(project)
        except Exception as e:
            logger.error(f"Failed to get project variables: {e}")
            return VariablesFile(scope=VariableScope.PROJECT)

    async def save_project_variables(self, project_id: str, variables: VariablesFile) -> None:
        """Save project-level variables."""
        try:
            project = await self.get_by_id(project_id)
            if project is None:
                raise ValueError(f"Project not found: {project_id}")
            self._storage.save_project_variables(project, variables)
        except Exception as e:
            logger.error(f"Failed to save project variables: {e}")
            raise

    async def get_global_variables(self) -> VariablesFile:
        """Get global variables."""
        return self._storage.load_global_variables()

    async def save_global_variables(self, variables: VariablesFile) -> None:
        """Save global variables."""
        self._storage.save_global_variables(variables)

    # =========================================================================
    # Credentials Operations
    # =========================================================================

    async def get_project_credentials(self, project_id: str) -> CredentialBindingsFile:
        """Get project-level credential bindings."""
        try:
            project = await self.get_by_id(project_id)
            if project is None:
                return CredentialBindingsFile(scope="project")
            return self._storage.load_project_credentials(project)
        except Exception as e:
            logger.error(f"Failed to get project credentials: {e}")
            return CredentialBindingsFile(scope="project")

    async def save_project_credentials(
        self, project_id: str, credentials: CredentialBindingsFile
    ) -> None:
        """Save project-level credential bindings."""
        try:
            project = await self.get_by_id(project_id)
            if project is None:
                raise ValueError(f"Project not found: {project_id}")
            self._storage.save_project_credentials(project, credentials)
        except Exception as e:
            logger.error(f"Failed to save project credentials: {e}")
            raise

    async def get_global_credentials(self) -> CredentialBindingsFile:
        """Get global credential bindings."""
        return self._storage.load_global_credentials()

    async def save_global_credentials(self, credentials: CredentialBindingsFile) -> None:
        """Save global credential bindings."""
        self._storage.save_global_credentials(credentials)

    # =========================================================================
    # Index Operations
    # =========================================================================

    async def get_projects_index(self) -> ProjectsIndex:
        """Get the projects index."""
        if self._index_cache is not None:
            return self._index_cache
        self._index_cache = self._storage.load_projects_index()
        return self._index_cache

    async def save_projects_index(self, index: ProjectsIndex) -> None:
        """Save the projects index."""
        self._storage.save_projects_index(index)
        self._index_cache = index

    async def update_project_opened(self, project_id: str) -> None:
        """Update last_opened timestamp for a project."""
        try:
            index = await self.get_projects_index()
            # update_last_opened is on ProjectsIndex, not ProjectIndexEntry
            index.update_last_opened(project_id)
            await self.save_projects_index(index)
        except Exception as e:
            logger.error(f"Failed to update project opened: {e}")
