"""
CasareRPA - Infrastructure: Project Storage
Handles file I/O operations for projects.

This is the infrastructure persistence adapter for project entities.
Manages all file system operations for projects, scenarios, variables, and credentials.
"""

from pathlib import Path
from typing import List, TYPE_CHECKING
import orjson
from loguru import logger

if TYPE_CHECKING:
    from casare_rpa.domain.entities.workflow import WorkflowSchema

from casare_rpa.domain.entities.project import (
    CredentialBindingsFile,
    Project,
    ProjectsIndex,
    VariableScope,
    VariablesFile,
)
from casare_rpa.config import (
    PROJECTS_INDEX_FILE,
    GLOBAL_VARIABLES_FILE,
    GLOBAL_CREDENTIALS_FILE,
)


# Project marker file name
PROJECT_MARKER_FILE = ".casare_project"


class ProjectStorage:
    """
    Infrastructure adapter for project persistence.

    Handles all file I/O operations for:
    - Project metadata (project.json)
    - Project variables (variables.json)
    - Project credentials (credentials.json)
    - Global variables and credentials
    - Projects index (registry of all projects)

    All methods are static as this is a stateless persistence adapter.
    """

    @staticmethod
    def is_project_folder(path: Path) -> bool:
        """
        Check if a folder is a valid CasareRPA project.

        Args:
            path: Path to check

        Returns:
            True if folder contains a CasareRPA project
        """
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

        Args:
            path: Path where project will be created
        """
        try:
            path.mkdir(parents=True, exist_ok=True)
            (path / "scenarios").mkdir(exist_ok=True)
            (path / PROJECT_MARKER_FILE).touch()
            logger.info(f"Created project structure at {path}")
        except Exception as e:
            logger.error(f"Failed to create project structure at {path}: {e}")
            raise

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
            OSError: If file cannot be written
        """
        if project.path is None:
            raise ValueError("Project path is not set")

        try:
            project.touch_modified()
            file_path = project.path / "project.json"

            json_data = orjson.dumps(
                project.to_dict(),
                option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS,
            )
            file_path.write_bytes(json_data)
            logger.debug(f"Saved project to {file_path}")
        except Exception as e:
            logger.error(f"Failed to save project {project.name}: {e}")
            raise

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
        except orjson.JSONDecodeError as e:
            logger.error(f"Invalid JSON in project file: {e}")
            raise ValueError(f"Invalid project file: {e}") from e
        except Exception as e:
            logger.error(f"Failed to load project: {e}")
            raise ValueError(f"Invalid project file: {e}") from e

    # =========================================================================
    # Project Variables
    # =========================================================================

    @staticmethod
    def save_project_variables(project: Project, variables: VariablesFile) -> None:
        """
        Save project variables to variables.json.

        Args:
            project: Project to save variables for
            variables: VariablesFile to save

        Raises:
            ValueError: If project path is not set
        """
        if project.path is None:
            raise ValueError("Project path is not set")

        try:
            file_path = project.path / "variables.json"
            json_data = orjson.dumps(
                variables.to_dict(),
                option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS,
            )
            file_path.write_bytes(json_data)
            logger.debug(f"Saved project variables to {file_path}")
        except Exception as e:
            logger.error(f"Failed to save project variables: {e}")
            raise

    @staticmethod
    def load_project_variables(project: Project) -> VariablesFile:
        """
        Load project variables from variables.json.

        Args:
            project: Project to load variables for

        Returns:
            VariablesFile (empty if file doesn't exist)
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
    def save_project_credentials(project: Project, credentials: CredentialBindingsFile) -> None:
        """
        Save project credential bindings to credentials.json.

        Args:
            project: Project to save credentials for
            credentials: CredentialBindingsFile to save

        Raises:
            ValueError: If project path is not set
        """
        if project.path is None:
            raise ValueError("Project path is not set")

        try:
            file_path = project.path / "credentials.json"
            json_data = orjson.dumps(
                credentials.to_dict(),
                option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS,
            )
            file_path.write_bytes(json_data)
            logger.debug(f"Saved project credentials to {file_path}")
        except Exception as e:
            logger.error(f"Failed to save project credentials: {e}")
            raise

    @staticmethod
    def load_project_credentials(project: Project) -> CredentialBindingsFile:
        """
        Load project credential bindings from credentials.json.

        Args:
            project: Project to load credentials for

        Returns:
            CredentialBindingsFile (empty if file doesn't exist)
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
        """
        Save global variables to config directory.

        Args:
            variables: VariablesFile to save
        """
        try:
            json_data = orjson.dumps(
                variables.to_dict(),
                option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS,
            )
            GLOBAL_VARIABLES_FILE.write_bytes(json_data)
            logger.debug(f"Saved global variables to {GLOBAL_VARIABLES_FILE}")
        except Exception as e:
            logger.error(f"Failed to save global variables: {e}")
            raise

    @staticmethod
    def load_global_variables() -> VariablesFile:
        """
        Load global variables from config directory.

        Returns:
            VariablesFile (empty if file doesn't exist)
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
        """
        Save global credential bindings to config directory.

        Args:
            credentials: CredentialBindingsFile to save
        """
        try:
            json_data = orjson.dumps(
                credentials.to_dict(),
                option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS,
            )
            GLOBAL_CREDENTIALS_FILE.write_bytes(json_data)
            logger.debug(f"Saved global credentials to {GLOBAL_CREDENTIALS_FILE}")
        except Exception as e:
            logger.error(f"Failed to save global credentials: {e}")
            raise

    @staticmethod
    def load_global_credentials() -> CredentialBindingsFile:
        """
        Load global credential bindings from config directory.

        Returns:
            CredentialBindingsFile (empty if file doesn't exist)
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
        """
        Save projects index to config directory.

        Args:
            index: ProjectsIndex to save
        """
        try:
            PROJECTS_INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
            json_data = orjson.dumps(
                index.to_dict(),
                option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS,
            )
            PROJECTS_INDEX_FILE.write_bytes(json_data)
            logger.debug(f"Saved projects index to {PROJECTS_INDEX_FILE}")
        except Exception as e:
            logger.error(f"Failed to save projects index: {e}")
            raise

    @staticmethod
    def load_projects_index() -> ProjectsIndex:
        """
        Load projects index from config directory.

        Returns:
            ProjectsIndex (empty if file doesn't exist)
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
        """
        List all scenario files in a project.

        Args:
            project: Project to list scenarios for

        Returns:
            List of paths to scenario JSON files
        """
        if project.path is None or project.scenarios_dir is None:
            return []

        if not project.scenarios_dir.exists():
            return []

        try:
            return sorted(project.scenarios_dir.glob("*.json"))
        except Exception as e:
            logger.error(f"Failed to list scenario files: {e}")
            return []

    @staticmethod
    def delete_project(project: Project, remove_files: bool = False) -> None:
        """
        Delete a project from the index and optionally remove files.

        Args:
            project: Project to delete
            remove_files: If True, also delete project folder from disk

        Raises:
            OSError: If file deletion fails
        """
        import shutil

        try:
            # Remove from index
            index = ProjectStorage.load_projects_index()
            index.remove_project(project.id)
            ProjectStorage.save_projects_index(index)

            # Optionally remove files
            if remove_files and project.path and project.path.exists():
                shutil.rmtree(project.path)
                logger.info(f"Deleted project folder: {project.path}")

            logger.info(f"Deleted project: {project.name}")
        except Exception as e:
            logger.error(f"Failed to delete project {project.name}: {e}")
            raise

    # =========================================================================
    # Workflow Storage (moved from domain layer)
    # =========================================================================

    @staticmethod
    def save_workflow(
        workflow: "WorkflowSchema",
        file_path: Path,
        validate_before_save: bool = False,
    ) -> None:
        """
        Save workflow to JSON file.

        Args:
            workflow: WorkflowSchema to save
            file_path: Path to save file
            validate_before_save: If True, validate workflow before saving

        Raises:
            ValueError: If validation fails and validate_before_save is True
        """

        try:
            if validate_before_save:
                result = workflow.validate_full()
                if not result.is_valid:
                    error_summary = result.format_summary()
                    logger.error(f"Validation failed before save:\n{error_summary}")
                    raise ValueError(f"Cannot save invalid workflow: {result.error_count} error(s)")

            # Update modified timestamp
            workflow.metadata.update_modified_timestamp()

            # Serialize to JSON using orjson
            json_data = orjson.dumps(
                workflow.to_dict(),
                option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS,
            )

            file_path.write_bytes(json_data)
            logger.info(f"Workflow saved to {file_path}")

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Failed to save workflow: {e}")
            raise

    @staticmethod
    def load_workflow(
        file_path: Path,
        validate_on_load: bool = False,
        strict: bool = False,
    ) -> "WorkflowSchema":
        """
        Load workflow from JSON file.

        Args:
            file_path: Path to workflow file
            validate_on_load: If True, validate workflow after loading
            strict: If True and validate_on_load is True, raise on validation errors

        Returns:
            WorkflowSchema instance

        Raises:
            ValueError: If strict validation fails
            FileNotFoundError: If file doesn't exist
        """
        from casare_rpa.domain.entities.workflow import WorkflowSchema

        try:
            json_data = file_path.read_bytes()
            data = orjson.loads(json_data)

            # Optionally validate
            if validate_on_load:
                from casare_rpa.domain.validation import validate_workflow

                result = validate_workflow(data)

                if not result.is_valid:
                    error_summary = result.format_summary()
                    logger.warning(f"Workflow validation issues:\n{error_summary}")

                    if strict:
                        raise ValueError(
                            f"Workflow validation failed: {result.error_count} error(s)"
                        )
                elif result.warnings:
                    logger.info(f"Workflow loaded with {result.warning_count} warning(s)")

            workflow = WorkflowSchema.from_dict(data)
            logger.info(f"Workflow loaded from {file_path}")

            return workflow

        except ValueError:
            raise
        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to load workflow: {e}")
            raise
