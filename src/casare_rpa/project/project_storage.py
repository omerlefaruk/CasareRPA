"""
CasareRPA - Project Storage
Handles file I/O operations for projects.
"""

from pathlib import Path
from typing import Optional, List
import orjson
from loguru import logger

from ..core.project_schema import (
    Project,
    VariablesFile,
    CredentialBindingsFile,
    ProjectsIndex,
    ProjectIndexEntry,
    VariableScope,
    PROJECT_SCHEMA_VERSION,
)
from ..utils.config import (
    PROJECTS_INDEX_FILE,
    GLOBAL_VARIABLES_FILE,
    GLOBAL_CREDENTIALS_FILE,
)


# Project marker file name
PROJECT_MARKER_FILE = ".casare_project"


class ProjectStorage:
    """
    Handles file I/O operations for projects.

    Provides methods to:
    - Create project folder structure
    - Save/load project metadata
    - Save/load project variables
    - Save/load project credentials
    - Manage global variables and credentials
    - Manage projects index
    """

    @staticmethod
    def is_project_folder(path: Path) -> bool:
        """Check if a folder is a valid CasareRPA project."""
        if not path.is_dir():
            return False
        # Check for marker file or project.json
        return (path / PROJECT_MARKER_FILE).exists() or (path / "project.json").exists()

    @staticmethod
    def create_project_structure(path: Path) -> None:
        """
        Create the folder structure for a new project.

        Creates:
        - project folder
        - .casare_project marker file
        - scenarios/ subfolder
        """
        path.mkdir(parents=True, exist_ok=True)
        (path / "scenarios").mkdir(exist_ok=True)
        (path / PROJECT_MARKER_FILE).touch()
        logger.info(f"Created project structure at {path}")

    # =========================================================================
    # Project Metadata
    # =========================================================================

    @staticmethod
    def save_project(project: Project) -> None:
        """
        Save project metadata to project.json.

        Args:
            project: Project to save (must have path set)

        Raises:
            ValueError: If project path is not set
        """
        if project.path is None:
            raise ValueError("Project path is not set")

        project.touch_modified()
        file_path = project.path / "project.json"

        json_data = orjson.dumps(
            project.to_dict(),
            option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS,
        )
        file_path.write_bytes(json_data)
        logger.debug(f"Saved project to {file_path}")

    @staticmethod
    def load_project(path: Path) -> Project:
        """
        Load project from a folder.

        Args:
            path: Path to project folder

        Returns:
            Project instance

        Raises:
            FileNotFoundError: If project.json doesn't exist
            ValueError: If project.json is invalid
        """
        file_path = path / "project.json"
        if not file_path.exists():
            raise FileNotFoundError(f"Project file not found: {file_path}")

        try:
            json_data = file_path.read_bytes()
            data = orjson.loads(json_data)
            project = Project.from_dict(data)
            project.path = path
            logger.debug(f"Loaded project from {file_path}")
            return project
        except Exception as e:
            logger.error(f"Failed to load project: {e}")
            raise ValueError(f"Invalid project file: {e}") from e

    # =========================================================================
    # Project Variables
    # =========================================================================

    @staticmethod
    def save_project_variables(project: Project, variables: VariablesFile) -> None:
        """Save project variables to variables.json."""
        if project.path is None:
            raise ValueError("Project path is not set")

        file_path = project.path / "variables.json"
        json_data = orjson.dumps(
            variables.to_dict(),
            option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS,
        )
        file_path.write_bytes(json_data)
        logger.debug(f"Saved project variables to {file_path}")

    @staticmethod
    def load_project_variables(project: Project) -> VariablesFile:
        """
        Load project variables from variables.json.

        Returns empty VariablesFile if file doesn't exist.
        """
        if project.path is None:
            return VariablesFile(scope=VariableScope.PROJECT)

        file_path = project.path / "variables.json"
        if not file_path.exists():
            return VariablesFile(scope=VariableScope.PROJECT)

        try:
            json_data = file_path.read_bytes()
            data = orjson.loads(json_data)
            return VariablesFile.from_dict(data)
        except Exception as e:
            logger.error(f"Failed to load project variables: {e}")
            return VariablesFile(scope=VariableScope.PROJECT)

    # =========================================================================
    # Project Credentials
    # =========================================================================

    @staticmethod
    def save_project_credentials(
        project: Project,
        credentials: CredentialBindingsFile
    ) -> None:
        """Save project credential bindings to credentials.json."""
        if project.path is None:
            raise ValueError("Project path is not set")

        file_path = project.path / "credentials.json"
        json_data = orjson.dumps(
            credentials.to_dict(),
            option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS,
        )
        file_path.write_bytes(json_data)
        logger.debug(f"Saved project credentials to {file_path}")

    @staticmethod
    def load_project_credentials(project: Project) -> CredentialBindingsFile:
        """
        Load project credential bindings from credentials.json.

        Returns empty CredentialBindingsFile if file doesn't exist.
        """
        if project.path is None:
            return CredentialBindingsFile(scope="project")

        file_path = project.path / "credentials.json"
        if not file_path.exists():
            return CredentialBindingsFile(scope="project")

        try:
            json_data = file_path.read_bytes()
            data = orjson.loads(json_data)
            return CredentialBindingsFile.from_dict(data)
        except Exception as e:
            logger.error(f"Failed to load project credentials: {e}")
            return CredentialBindingsFile(scope="project")

    # =========================================================================
    # Global Variables
    # =========================================================================

    @staticmethod
    def save_global_variables(variables: VariablesFile) -> None:
        """Save global variables to config directory."""
        json_data = orjson.dumps(
            variables.to_dict(),
            option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS,
        )
        GLOBAL_VARIABLES_FILE.write_bytes(json_data)
        logger.debug(f"Saved global variables to {GLOBAL_VARIABLES_FILE}")

    @staticmethod
    def load_global_variables() -> VariablesFile:
        """
        Load global variables from config directory.

        Returns empty VariablesFile if file doesn't exist.
        """
        if not GLOBAL_VARIABLES_FILE.exists():
            return VariablesFile(scope=VariableScope.GLOBAL)

        try:
            json_data = GLOBAL_VARIABLES_FILE.read_bytes()
            data = orjson.loads(json_data)
            return VariablesFile.from_dict(data)
        except Exception as e:
            logger.error(f"Failed to load global variables: {e}")
            return VariablesFile(scope=VariableScope.GLOBAL)

    # =========================================================================
    # Global Credentials
    # =========================================================================

    @staticmethod
    def save_global_credentials(credentials: CredentialBindingsFile) -> None:
        """Save global credential bindings to config directory."""
        json_data = orjson.dumps(
            credentials.to_dict(),
            option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS,
        )
        GLOBAL_CREDENTIALS_FILE.write_bytes(json_data)
        logger.debug(f"Saved global credentials to {GLOBAL_CREDENTIALS_FILE}")

    @staticmethod
    def load_global_credentials() -> CredentialBindingsFile:
        """
        Load global credential bindings from config directory.

        Returns empty CredentialBindingsFile if file doesn't exist.
        """
        if not GLOBAL_CREDENTIALS_FILE.exists():
            return CredentialBindingsFile(scope="global")

        try:
            json_data = GLOBAL_CREDENTIALS_FILE.read_bytes()
            data = orjson.loads(json_data)
            return CredentialBindingsFile.from_dict(data)
        except Exception as e:
            logger.error(f"Failed to load global credentials: {e}")
            return CredentialBindingsFile(scope="global")

    # =========================================================================
    # Projects Index
    # =========================================================================

    @staticmethod
    def save_projects_index(index: ProjectsIndex) -> None:
        """Save projects index to config directory."""
        PROJECTS_INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
        json_data = orjson.dumps(
            index.to_dict(),
            option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS,
        )
        PROJECTS_INDEX_FILE.write_bytes(json_data)
        logger.debug(f"Saved projects index to {PROJECTS_INDEX_FILE}")

    @staticmethod
    def load_projects_index() -> ProjectsIndex:
        """
        Load projects index from config directory.

        Returns empty ProjectsIndex if file doesn't exist.
        """
        if not PROJECTS_INDEX_FILE.exists():
            return ProjectsIndex()

        try:
            json_data = PROJECTS_INDEX_FILE.read_bytes()
            data = orjson.loads(json_data)
            return ProjectsIndex.from_dict(data)
        except Exception as e:
            logger.error(f"Failed to load projects index: {e}")
            return ProjectsIndex()

    # =========================================================================
    # Utility Methods
    # =========================================================================

    @staticmethod
    def list_scenario_files(project: Project) -> List[Path]:
        """List all scenario files in a project."""
        if project.path is None or project.scenarios_dir is None:
            return []

        if not project.scenarios_dir.exists():
            return []

        return sorted(project.scenarios_dir.glob("*.json"))

    @staticmethod
    def delete_project(project: Project, remove_files: bool = False) -> None:
        """
        Delete a project from the index and optionally remove files.

        Args:
            project: Project to delete
            remove_files: If True, also delete project folder
        """
        import shutil

        # Remove from index
        index = ProjectStorage.load_projects_index()
        index.remove_project(project.id)
        ProjectStorage.save_projects_index(index)

        # Optionally remove files
        if remove_files and project.path and project.path.exists():
            shutil.rmtree(project.path)
            logger.info(f"Deleted project folder: {project.path}")

        logger.info(f"Deleted project: {project.name}")
