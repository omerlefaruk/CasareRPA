"""Project repository interface."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

from casare_rpa.domain.entities.project import (
    Project,
    Scenario,
    ProjectsIndex,
    VariablesFile,
    CredentialBindingsFile,
)


class ProjectRepository(ABC):
    """
    Repository interface for Project aggregate.

    Defines the contract for project persistence operations.
    Implementations can use file system, database, or cloud storage.
    """

    # =========================================================================
    # Project Operations
    # =========================================================================

    @abstractmethod
    async def get_by_id(self, project_id: str) -> Optional[Project]:
        """
        Get project by ID.

        Args:
            project_id: Project ID (e.g., 'proj_a1b2c3d4')

        Returns:
            Project if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_path(self, path: Path) -> Optional[Project]:
        """
        Get project by folder path.

        Args:
            path: Path to project folder

        Returns:
            Project if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_all(self) -> List[Project]:
        """
        Get all registered projects.

        Returns:
            List of all projects from the index
        """
        pass

    @abstractmethod
    async def save(self, project: Project) -> None:
        """
        Save or update project.

        Creates folder structure if new project.
        Updates modified timestamp automatically.

        Args:
            project: Project to save (must have path set)
        """
        pass

    @abstractmethod
    async def delete(self, project_id: str, remove_files: bool = False) -> None:
        """
        Delete project.

        Args:
            project_id: Project ID to delete
            remove_files: If True, also delete project folder from disk
        """
        pass

    @abstractmethod
    async def exists(self, project_id: str) -> bool:
        """
        Check if project exists.

        Args:
            project_id: Project ID to check

        Returns:
            True if project exists
        """
        pass

    # =========================================================================
    # Scenario Operations
    # =========================================================================

    @abstractmethod
    async def get_scenario(self, project_id: str, scenario_id: str) -> Optional[Scenario]:
        """
        Get scenario by ID.

        Args:
            project_id: Parent project ID
            scenario_id: Scenario ID

        Returns:
            Scenario if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_scenarios(self, project_id: str) -> List[Scenario]:
        """
        Get all scenarios for a project.

        Args:
            project_id: Project ID

        Returns:
            List of scenarios
        """
        pass

    @abstractmethod
    async def save_scenario(self, project_id: str, scenario: Scenario) -> None:
        """
        Save scenario to project.

        Args:
            project_id: Parent project ID
            scenario: Scenario to save
        """
        pass

    @abstractmethod
    async def delete_scenario(self, project_id: str, scenario_id: str) -> None:
        """
        Delete scenario from project.

        Args:
            project_id: Parent project ID
            scenario_id: Scenario ID to delete
        """
        pass

    # =========================================================================
    # Variables Operations
    # =========================================================================

    @abstractmethod
    async def get_project_variables(self, project_id: str) -> VariablesFile:
        """
        Get project-level variables.

        Args:
            project_id: Project ID

        Returns:
            VariablesFile (empty if not found)
        """
        pass

    @abstractmethod
    async def save_project_variables(self, project_id: str, variables: VariablesFile) -> None:
        """
        Save project-level variables.

        Args:
            project_id: Project ID
            variables: Variables to save
        """
        pass

    @abstractmethod
    async def get_global_variables(self) -> VariablesFile:
        """
        Get global variables.

        Returns:
            VariablesFile (empty if not found)
        """
        pass

    @abstractmethod
    async def save_global_variables(self, variables: VariablesFile) -> None:
        """
        Save global variables.

        Args:
            variables: Variables to save
        """
        pass

    # =========================================================================
    # Credentials Operations
    # =========================================================================

    @abstractmethod
    async def get_project_credentials(self, project_id: str) -> CredentialBindingsFile:
        """
        Get project-level credential bindings.

        Args:
            project_id: Project ID

        Returns:
            CredentialBindingsFile (empty if not found)
        """
        pass

    @abstractmethod
    async def save_project_credentials(
        self, project_id: str, credentials: CredentialBindingsFile
    ) -> None:
        """
        Save project-level credential bindings.

        Args:
            project_id: Project ID
            credentials: Credentials to save
        """
        pass

    @abstractmethod
    async def get_global_credentials(self) -> CredentialBindingsFile:
        """
        Get global credential bindings.

        Returns:
            CredentialBindingsFile (empty if not found)
        """
        pass

    @abstractmethod
    async def save_global_credentials(self, credentials: CredentialBindingsFile) -> None:
        """
        Save global credential bindings.

        Args:
            credentials: Credentials to save
        """
        pass

    # =========================================================================
    # Index Operations
    # =========================================================================

    @abstractmethod
    async def get_projects_index(self) -> ProjectsIndex:
        """
        Get the projects index (registry of all projects).

        Returns:
            ProjectsIndex
        """
        pass

    @abstractmethod
    async def save_projects_index(self, index: ProjectsIndex) -> None:
        """
        Save the projects index.

        Args:
            index: ProjectsIndex to save
        """
        pass

    @abstractmethod
    async def update_project_opened(self, project_id: str) -> None:
        """
        Update last_opened timestamp for a project in the index.

        Args:
            project_id: Project ID
        """
        pass
