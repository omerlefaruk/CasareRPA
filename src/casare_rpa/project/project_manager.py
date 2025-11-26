"""
CasareRPA - Project Manager
High-level project management operations.
"""

from pathlib import Path
from typing import List, Optional, Dict, Any
from loguru import logger

from ..core.project_schema import (
    Project,
    Scenario,
    VariablesFile,
    CredentialBindingsFile,
    ProjectVariable,
    CredentialBinding,
    VariableScope,
    ProjectsIndex,
)
from .project_storage import ProjectStorage
from .scenario_storage import ScenarioStorage


class ProjectManager:
    """
    High-level project management API.

    Provides unified interface for:
    - Creating, opening, and saving projects
    - Managing scenarios within projects
    - Managing project and global variables
    - Managing credential bindings
    - Tracking recent projects
    """

    def __init__(self):
        """Initialize project manager."""
        self._current_project: Optional[Project] = None
        self._current_scenario: Optional[Scenario] = None
        self._project_variables: Optional[VariablesFile] = None
        self._project_credentials: Optional[CredentialBindingsFile] = None
        self._global_variables: Optional[VariablesFile] = None
        self._global_credentials: Optional[CredentialBindingsFile] = None

        # Load global resources on init
        self._load_global_resources()

    def _load_global_resources(self) -> None:
        """Load global variables and credentials."""
        self._global_variables = ProjectStorage.load_global_variables()
        self._global_credentials = ProjectStorage.load_global_credentials()

    # =========================================================================
    # Current State Properties
    # =========================================================================

    @property
    def current_project(self) -> Optional[Project]:
        """Get currently open project."""
        return self._current_project

    @property
    def current_scenario(self) -> Optional[Scenario]:
        """Get currently open scenario."""
        return self._current_scenario

    @property
    def has_project(self) -> bool:
        """Check if a project is currently open."""
        return self._current_project is not None

    @property
    def has_scenario(self) -> bool:
        """Check if a scenario is currently open."""
        return self._current_scenario is not None

    # =========================================================================
    # Project Operations
    # =========================================================================

    def create_project(
        self,
        name: str,
        path: Path,
        description: str = "",
        author: str = "",
    ) -> Project:
        """
        Create a new project.

        Args:
            name: Project name
            path: Path where project folder will be created
            description: Project description
            author: Project author

        Returns:
            Created Project instance
        """
        # Create project folder structure
        ProjectStorage.create_project_structure(path)

        # Create project
        project = Project.create_new(
            name=name,
            path=path,
            description=description,
            author=author,
        )

        # Save project metadata
        ProjectStorage.save_project(project)

        # Initialize empty variables and credentials files
        variables = VariablesFile(scope=VariableScope.PROJECT)
        credentials = CredentialBindingsFile(scope="project")
        ProjectStorage.save_project_variables(project, variables)
        ProjectStorage.save_project_credentials(project, credentials)

        # Add to projects index
        index = ProjectStorage.load_projects_index()
        index.add_project(project)
        ProjectStorage.save_projects_index(index)

        # Set as current project
        self._current_project = project
        self._project_variables = variables
        self._project_credentials = credentials
        self._current_scenario = None

        logger.info(f"Created project: {name} at {path}")
        return project

    def open_project(self, path: Path) -> Project:
        """
        Open an existing project.

        Args:
            path: Path to project folder

        Returns:
            Loaded Project instance

        Raises:
            FileNotFoundError: If project doesn't exist
        """
        # Validate project folder
        if not ProjectStorage.is_project_folder(path):
            raise FileNotFoundError(f"Not a valid project folder: {path}")

        # Load project
        project = ProjectStorage.load_project(path)
        self._current_project = project

        # Load project resources
        self._project_variables = ProjectStorage.load_project_variables(project)
        self._project_credentials = ProjectStorage.load_project_credentials(project)

        # Clear current scenario
        self._current_scenario = None

        # Update projects index
        index = ProjectStorage.load_projects_index()
        index.add_project(project)
        ProjectStorage.save_projects_index(index)

        logger.info(f"Opened project: {project.name}")
        return project

    def save_project(self) -> None:
        """Save current project and its resources."""
        if self._current_project is None:
            raise ValueError("No project is currently open")

        ProjectStorage.save_project(self._current_project)

        if self._project_variables:
            ProjectStorage.save_project_variables(
                self._current_project,
                self._project_variables
            )

        if self._project_credentials:
            ProjectStorage.save_project_credentials(
                self._current_project,
                self._project_credentials
            )

        logger.debug(f"Saved project: {self._current_project.name}")

    def close_project(self) -> None:
        """Close current project."""
        if self._current_project is None:
            return

        logger.info(f"Closed project: {self._current_project.name}")

        self._current_project = None
        self._current_scenario = None
        self._project_variables = None
        self._project_credentials = None

    def delete_project(self, remove_files: bool = False) -> None:
        """
        Delete current project.

        Args:
            remove_files: If True, also delete project files
        """
        if self._current_project is None:
            raise ValueError("No project is currently open")

        project = self._current_project
        self.close_project()
        ProjectStorage.delete_project(project, remove_files=remove_files)

    # =========================================================================
    # Scenario Operations
    # =========================================================================

    def create_scenario(
        self,
        name: str,
        workflow: Optional[Dict[str, Any]] = None,
        description: str = "",
    ) -> Scenario:
        """
        Create a new scenario in the current project.

        Args:
            name: Scenario name
            workflow: Optional workflow data to embed
            description: Scenario description

        Returns:
            Created Scenario instance
        """
        if self._current_project is None:
            raise ValueError("No project is currently open")

        scenario = Scenario.create_new(
            name=name,
            project_id=self._current_project.id,
            workflow=workflow,
            description=description,
        )

        ScenarioStorage.save_scenario(scenario, self._current_project)

        # Set as current scenario
        self._current_scenario = scenario

        logger.info(f"Created scenario: {name}")
        return scenario

    def open_scenario(self, scenario: Scenario) -> Scenario:
        """
        Open a scenario.

        Args:
            scenario: Scenario to open

        Returns:
            Opened Scenario instance
        """
        self._current_scenario = scenario
        logger.info(f"Opened scenario: {scenario.name}")
        return scenario

    def open_scenario_by_path(self, file_path: Path) -> Scenario:
        """
        Open a scenario by file path.

        Args:
            file_path: Path to scenario file

        Returns:
            Loaded Scenario instance
        """
        scenario = ScenarioStorage.load_scenario(file_path)
        self._current_scenario = scenario
        logger.info(f"Opened scenario: {scenario.name}")
        return scenario

    def save_scenario(self, workflow: Optional[Dict[str, Any]] = None) -> None:
        """
        Save current scenario.

        Args:
            workflow: Optional updated workflow data
        """
        if self._current_project is None:
            raise ValueError("No project is currently open")
        if self._current_scenario is None:
            raise ValueError("No scenario is currently open")

        if workflow is not None:
            self._current_scenario.workflow = workflow

        ScenarioStorage.save_scenario(self._current_scenario, self._current_project)
        logger.debug(f"Saved scenario: {self._current_scenario.name}")

    def close_scenario(self) -> None:
        """Close current scenario."""
        if self._current_scenario:
            logger.info(f"Closed scenario: {self._current_scenario.name}")
        self._current_scenario = None

    def delete_scenario(self, scenario: Optional[Scenario] = None) -> None:
        """
        Delete a scenario.

        Args:
            scenario: Scenario to delete (defaults to current)
        """
        target = scenario or self._current_scenario
        if target is None:
            raise ValueError("No scenario specified")

        ScenarioStorage.delete_scenario(target)

        if target == self._current_scenario:
            self._current_scenario = None

    def get_scenarios(self) -> List[Scenario]:
        """Get all scenarios in current project."""
        if self._current_project is None:
            return []
        return ScenarioStorage.load_all_scenarios(self._current_project)

    def duplicate_scenario(self, new_name: str) -> Scenario:
        """
        Duplicate current scenario.

        Args:
            new_name: Name for the duplicate

        Returns:
            New Scenario instance
        """
        if self._current_project is None:
            raise ValueError("No project is currently open")
        if self._current_scenario is None:
            raise ValueError("No scenario is currently open")

        return ScenarioStorage.duplicate_scenario(
            self._current_scenario,
            new_name,
            self._current_project
        )

    # =========================================================================
    # Variable Operations
    # =========================================================================

    def get_project_variables(self) -> Dict[str, ProjectVariable]:
        """Get all project variables."""
        if self._project_variables is None:
            return {}
        return self._project_variables.variables

    def get_project_variable(self, name: str) -> Optional[ProjectVariable]:
        """Get a specific project variable."""
        if self._project_variables is None:
            return None
        return self._project_variables.get_variable(name)

    def set_project_variable(self, variable: ProjectVariable) -> None:
        """Set a project variable."""
        if self._project_variables is None:
            raise ValueError("No project is currently open")
        self._project_variables.set_variable(variable)

    def remove_project_variable(self, name: str) -> bool:
        """Remove a project variable."""
        if self._project_variables is None:
            return False
        return self._project_variables.remove_variable(name)

    def get_global_variables(self) -> Dict[str, ProjectVariable]:
        """Get all global variables."""
        if self._global_variables is None:
            return {}
        return self._global_variables.variables

    def get_global_variable(self, name: str) -> Optional[ProjectVariable]:
        """Get a specific global variable."""
        if self._global_variables is None:
            return None
        return self._global_variables.get_variable(name)

    def set_global_variable(self, variable: ProjectVariable) -> None:
        """Set a global variable."""
        if self._global_variables is None:
            self._global_variables = VariablesFile(scope=VariableScope.GLOBAL)
        self._global_variables.set_variable(variable)
        ProjectStorage.save_global_variables(self._global_variables)

    def remove_global_variable(self, name: str) -> bool:
        """Remove a global variable."""
        if self._global_variables is None:
            return False
        result = self._global_variables.remove_variable(name)
        if result:
            ProjectStorage.save_global_variables(self._global_variables)
        return result

    def get_merged_variables(self) -> Dict[str, Any]:
        """
        Get merged variables from all scopes.

        Priority (highest to lowest):
        - Scenario variable values
        - Project variable defaults
        - Global variable defaults

        Returns:
            Dictionary of variable name -> value
        """
        merged = {}

        # Start with global defaults
        if self._global_variables:
            merged.update(self._global_variables.get_default_values())

        # Override with project defaults
        if self._project_variables:
            merged.update(self._project_variables.get_default_values())

        # Override with scenario values
        if self._current_scenario:
            merged.update(self._current_scenario.variable_values)

        return merged

    # =========================================================================
    # Credential Operations
    # =========================================================================

    def get_project_credentials(self) -> Dict[str, CredentialBinding]:
        """Get all project credential bindings."""
        if self._project_credentials is None:
            return {}
        return self._project_credentials.bindings

    def set_project_credential(self, binding: CredentialBinding) -> None:
        """Set a project credential binding."""
        if self._project_credentials is None:
            raise ValueError("No project is currently open")
        self._project_credentials.set_binding(binding)

    def remove_project_credential(self, alias: str) -> bool:
        """Remove a project credential binding."""
        if self._project_credentials is None:
            return False
        return self._project_credentials.remove_binding(alias)

    def get_global_credentials(self) -> Dict[str, CredentialBinding]:
        """Get all global credential bindings."""
        if self._global_credentials is None:
            return {}
        return self._global_credentials.bindings

    def set_global_credential(self, binding: CredentialBinding) -> None:
        """Set a global credential binding."""
        if self._global_credentials is None:
            self._global_credentials = CredentialBindingsFile(scope="global")
        self._global_credentials.set_binding(binding)
        ProjectStorage.save_global_credentials(self._global_credentials)

    def remove_global_credential(self, alias: str) -> bool:
        """Remove a global credential binding."""
        if self._global_credentials is None:
            return False
        result = self._global_credentials.remove_binding(alias)
        if result:
            ProjectStorage.save_global_credentials(self._global_credentials)
        return result

    def resolve_credential_path(self, alias: str) -> Optional[str]:
        """
        Resolve a credential alias to its Vault path.

        Checks scenario, project, then global bindings.

        Args:
            alias: Credential alias to resolve

        Returns:
            Vault path if found, None otherwise
        """
        # Check scenario-level bindings first
        if self._current_scenario:
            path = self._current_scenario.credential_bindings.get(alias)
            if path:
                return path

        # Check project bindings
        if self._project_credentials:
            path = self._project_credentials.resolve_vault_path(alias)
            if path:
                return path

        # Check global bindings
        if self._global_credentials:
            path = self._global_credentials.resolve_vault_path(alias)
            if path:
                return path

        return None

    # =========================================================================
    # Recent Projects
    # =========================================================================

    def get_recent_projects(self, limit: int = 10) -> List[dict]:
        """
        Get list of recently opened projects.

        Returns:
            List of project info dicts with id, name, path, last_opened
        """
        index = ProjectStorage.load_projects_index()
        return [
            {
                "id": p.id,
                "name": p.name,
                "path": p.path,
                "last_opened": p.last_opened.isoformat() if p.last_opened else None,
            }
            for p in index.get_recent_projects(limit)
        ]

    def clear_recent_projects(self) -> None:
        """Clear the recent projects list."""
        index = ProjectsIndex()
        ProjectStorage.save_projects_index(index)
        logger.info("Cleared recent projects list")

    def remove_from_recent(self, project_id: str) -> None:
        """
        Remove a project from the recent projects list.

        Args:
            project_id: ID of the project to remove
        """
        index = ProjectStorage.load_projects_index()
        original_count = len(index.projects)

        # Filter out the project with matching ID
        index.projects = [p for p in index.projects if p.id != project_id]

        if len(index.projects) < original_count:
            ProjectStorage.save_projects_index(index)
            logger.info(f"Removed project {project_id} from recent projects")
        else:
            logger.debug(f"Project {project_id} not found in recent projects")


# Singleton instance
_project_manager: Optional[ProjectManager] = None


def get_project_manager() -> ProjectManager:
    """Get or create the singleton ProjectManager instance."""
    global _project_manager
    if _project_manager is None:
        _project_manager = ProjectManager()
    return _project_manager
