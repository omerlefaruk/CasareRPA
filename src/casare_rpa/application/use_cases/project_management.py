"""
CasareRPA - Project Management Use Cases

Application layer use cases for project CRUD operations.
Orchestrates domain entities and infrastructure persistence.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from loguru import logger

from casare_rpa.domain.entities.project import (
    Project,
    Scenario,
)
from casare_rpa.domain.repositories import ProjectRepository


# =============================================================================
# Result Types
# =============================================================================


@dataclass
class ProjectResult:
    """Result of a project operation."""

    success: bool
    project: Optional[Project] = None
    error: Optional[str] = None


@dataclass
class ScenarioResult:
    """Result of a scenario operation."""

    success: bool
    scenario: Optional[Scenario] = None
    error: Optional[str] = None


@dataclass
class ProjectListResult:
    """Result of listing projects."""

    success: bool
    projects: List[Project] = None
    error: Optional[str] = None

    def __post_init__(self):
        if self.projects is None:
            self.projects = []


# =============================================================================
# Create Project Use Case
# =============================================================================


class CreateProjectUseCase:
    """
    Create a new project.

    Creates folder structure, initializes project metadata,
    and registers project in the index.
    """

    def __init__(self, repository: ProjectRepository) -> None:
        """
        Initialize use case.

        Args:
            repository: Project repository for persistence
        """
        self._repository = repository

    async def execute(
        self,
        name: str,
        path: Path,
        description: str = "",
        author: str = "",
        tags: Optional[List[str]] = None,
    ) -> ProjectResult:
        """
        Create a new project.

        Args:
            name: Project name
            path: Path to project folder
            description: Project description
            author: Project author
            tags: List of tags

        Returns:
            ProjectResult with created project or error
        """
        try:
            # Validate path
            if path.exists() and any(path.iterdir()):
                # Check if it's already a project
                existing = await self._repository.get_by_path(path)
                if existing:
                    return ProjectResult(
                        success=False,
                        error=f"Project already exists at {path}",
                    )
                return ProjectResult(
                    success=False,
                    error=f"Directory not empty: {path}",
                )

            # Create project
            project = Project.create_new(
                name=name,
                path=path,
                description=description,
                author=author,
                tags=tags or [],
            )

            # Save project
            await self._repository.save(project)

            logger.info(f"Created project: {name} at {path}")
            return ProjectResult(success=True, project=project)

        except Exception as e:
            logger.error(f"Failed to create project: {e}")
            return ProjectResult(success=False, error=str(e))


# =============================================================================
# Load Project Use Case
# =============================================================================


class LoadProjectUseCase:
    """
    Load an existing project.

    Loads project metadata and updates last_opened timestamp.
    """

    def __init__(self, repository: ProjectRepository) -> None:
        """Initialize use case."""
        self._repository = repository

    async def execute(
        self,
        project_id: Optional[str] = None,
        path: Optional[Path] = None,
    ) -> ProjectResult:
        """
        Load a project by ID or path.

        Args:
            project_id: Project ID (preferred)
            path: Path to project folder (fallback)

        Returns:
            ProjectResult with loaded project or error
        """
        try:
            if project_id:
                project = await self._repository.get_by_id(project_id)
            elif path:
                project = await self._repository.get_by_path(path)
            else:
                return ProjectResult(
                    success=False,
                    error="Either project_id or path must be provided",
                )

            if project is None:
                return ProjectResult(
                    success=False,
                    error="Project not found",
                )

            # Update last_opened timestamp
            await self._repository.update_project_opened(project.id)

            logger.info(f"Loaded project: {project.name}")
            return ProjectResult(success=True, project=project)

        except Exception as e:
            logger.error(f"Failed to load project: {e}")
            return ProjectResult(success=False, error=str(e))


# =============================================================================
# Save Project Use Case
# =============================================================================


class SaveProjectUseCase:
    """
    Save project changes.

    Updates project metadata and modified timestamp.
    """

    def __init__(self, repository: ProjectRepository) -> None:
        """Initialize use case."""
        self._repository = repository

    async def execute(self, project: Project) -> ProjectResult:
        """
        Save project.

        Args:
            project: Project to save

        Returns:
            ProjectResult with saved project or error
        """
        try:
            await self._repository.save(project)
            logger.info(f"Saved project: {project.name}")
            return ProjectResult(success=True, project=project)
        except Exception as e:
            logger.error(f"Failed to save project: {e}")
            return ProjectResult(success=False, error=str(e))


# =============================================================================
# List Projects Use Case
# =============================================================================


class ListProjectsUseCase:
    """
    List all registered projects.

    Returns projects sorted by last_opened timestamp.
    """

    def __init__(self, repository: ProjectRepository) -> None:
        """Initialize use case."""
        self._repository = repository

    async def execute(self, limit: Optional[int] = None) -> ProjectListResult:
        """
        List projects.

        Args:
            limit: Maximum number of projects to return

        Returns:
            ProjectListResult with list of projects
        """
        try:
            projects = await self._repository.get_all()

            # Sort by last opened (most recent first)
            # Note: This requires getting index entries for sorting
            index = await self._repository.get_projects_index()
            project_order = {entry.id: entry.last_opened for entry in index.projects}
            projects.sort(
                key=lambda p: project_order.get(p.id, ""),
                reverse=True,
            )

            if limit:
                projects = projects[:limit]

            return ProjectListResult(success=True, projects=projects)

        except Exception as e:
            logger.error(f"Failed to list projects: {e}")
            return ProjectListResult(success=False, error=str(e))


# =============================================================================
# Delete Project Use Case
# =============================================================================


class DeleteProjectUseCase:
    """
    Delete a project.

    Removes from index and optionally deletes files.
    """

    def __init__(self, repository: ProjectRepository) -> None:
        """Initialize use case."""
        self._repository = repository

    async def execute(
        self,
        project_id: str,
        remove_files: bool = False,
    ) -> ProjectResult:
        """
        Delete a project.

        Args:
            project_id: Project ID to delete
            remove_files: If True, also delete project folder from disk

        Returns:
            ProjectResult indicating success or error
        """
        try:
            # Get project first for logging
            project = await self._repository.get_by_id(project_id)
            name = project.name if project else project_id

            await self._repository.delete(project_id, remove_files=remove_files)

            logger.info(f"Deleted project: {name} (files removed: {remove_files})")
            return ProjectResult(success=True)

        except Exception as e:
            logger.error(f"Failed to delete project: {e}")
            return ProjectResult(success=False, error=str(e))


# =============================================================================
# Scenario Use Cases
# =============================================================================


class CreateScenarioUseCase:
    """Create a new scenario in a project."""

    def __init__(self, repository: ProjectRepository) -> None:
        """Initialize use case."""
        self._repository = repository

    async def execute(
        self,
        project_id: str,
        name: str,
        workflow: Optional[dict] = None,
        tags: Optional[List[str]] = None,
    ) -> ScenarioResult:
        """
        Create a new scenario.

        Args:
            project_id: Parent project ID
            name: Scenario name
            workflow: Optional workflow dict to include
            tags: Optional tags

        Returns:
            ScenarioResult with created scenario or error
        """
        try:
            # Verify project exists
            project = await self._repository.get_by_id(project_id)
            if project is None:
                return ScenarioResult(
                    success=False,
                    error=f"Project not found: {project_id}",
                )

            # Create scenario
            scenario = Scenario.create_new(
                name=name,
                project_id=project_id,
                workflow=workflow,
                tags=tags or [],
            )

            # Save scenario
            await self._repository.save_scenario(project_id, scenario)

            logger.info(f"Created scenario: {name} in project {project.name}")
            return ScenarioResult(success=True, scenario=scenario)

        except Exception as e:
            logger.error(f"Failed to create scenario: {e}")
            return ScenarioResult(success=False, error=str(e))


class LoadScenarioUseCase:
    """Load a scenario from a project."""

    def __init__(self, repository: ProjectRepository) -> None:
        """Initialize use case."""
        self._repository = repository

    async def execute(
        self,
        project_id: str,
        scenario_id: str,
    ) -> ScenarioResult:
        """
        Load a scenario.

        Args:
            project_id: Parent project ID
            scenario_id: Scenario ID

        Returns:
            ScenarioResult with loaded scenario or error
        """
        try:
            scenario = await self._repository.get_scenario(project_id, scenario_id)
            if scenario is None:
                return ScenarioResult(
                    success=False,
                    error=f"Scenario not found: {scenario_id}",
                )

            return ScenarioResult(success=True, scenario=scenario)

        except Exception as e:
            logger.error(f"Failed to load scenario: {e}")
            return ScenarioResult(success=False, error=str(e))


class SaveScenarioUseCase:
    """Save scenario changes."""

    def __init__(self, repository: ProjectRepository) -> None:
        """Initialize use case."""
        self._repository = repository

    async def execute(
        self,
        project_id: str,
        scenario: Scenario,
    ) -> ScenarioResult:
        """
        Save scenario.

        Args:
            project_id: Parent project ID
            scenario: Scenario to save

        Returns:
            ScenarioResult with saved scenario or error
        """
        try:
            await self._repository.save_scenario(project_id, scenario)
            logger.info(f"Saved scenario: {scenario.name}")
            return ScenarioResult(success=True, scenario=scenario)

        except Exception as e:
            logger.error(f"Failed to save scenario: {e}")
            return ScenarioResult(success=False, error=str(e))


class DeleteScenarioUseCase:
    """Delete a scenario from a project."""

    def __init__(self, repository: ProjectRepository) -> None:
        """Initialize use case."""
        self._repository = repository

    async def execute(
        self,
        project_id: str,
        scenario_id: str,
    ) -> ScenarioResult:
        """
        Delete a scenario.

        Args:
            project_id: Parent project ID
            scenario_id: Scenario ID to delete

        Returns:
            ScenarioResult indicating success or error
        """
        try:
            await self._repository.delete_scenario(project_id, scenario_id)
            logger.info(f"Deleted scenario: {scenario_id}")
            return ScenarioResult(success=True)

        except Exception as e:
            logger.error(f"Failed to delete scenario: {e}")
            return ScenarioResult(success=False, error=str(e))


class ListScenariosUseCase:
    """List all scenarios in a project."""

    def __init__(self, repository: ProjectRepository) -> None:
        """Initialize use case."""
        self._repository = repository

    async def execute(self, project_id: str) -> List[Scenario]:
        """
        List scenarios in a project.

        Args:
            project_id: Project ID

        Returns:
            List of scenarios
        """
        try:
            return await self._repository.get_scenarios(project_id)
        except Exception as e:
            logger.error(f"Failed to list scenarios: {e}")
            return []
