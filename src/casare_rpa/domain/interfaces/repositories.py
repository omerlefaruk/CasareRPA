"""
Domain Layer - Repository Interfaces.

This module defines Protocol interfaces for repository/storage classes
that allow the Application layer to depend on abstractions instead of
concrete Infrastructure implementations.

Design Pattern: Repository Pattern + Dependency Inversion
- Application depends on these abstractions (IFolderStorage, etc.)
- Infrastructure implements these abstractions (FolderStorage, etc.)

Usage:
    from casare_rpa.domain.interfaces import IFolderStorage

    class FolderManagementUseCase:
        def __init__(self, storage: IFolderStorage):
            self.storage = storage
"""

from pathlib import Path
from typing import Any, Protocol


class IFolderStorage(Protocol):
    """
    Protocol for folder storage operations.

    Infrastructure implementation: FolderStorage
    """

    @staticmethod
    def get_default_folders_file() -> Path:
        """Get default path for folders.json."""
        ...

    @staticmethod
    def save_folders(folders_file: Any, file_path: Path | None = None) -> None:
        """
        Save folders to file.

        Args:
            folders_file: FoldersFile container
            file_path: Optional path (uses default if not provided)
        """
        ...

    @staticmethod
    def load_folders(file_path: Path | None = None) -> Any:
        """
        Load folders from file.

        Args:
            file_path: Optional path (uses default if not provided)

        Returns:
            FoldersFile instance
        """
        ...

    @staticmethod
    def create_folder(
        name: str,
        parent_id: str | None = None,
        color: str = "blue",
        file_path: Path | None = None,
    ) -> Any:
        """
        Create a new folder.

        Args:
            name: Folder name
            parent_id: Parent folder ID (None for root)
            color: Folder color
            file_path: Optional path to folders.json

        Returns:
            Created ProjectFolder
        """
        ...

    @staticmethod
    def get_folder(folder_id: str, file_path: Path | None = None) -> Any | None:
        """
        Get a folder by ID.

        Args:
            folder_id: Folder ID
            file_path: Optional path to folders.json

        Returns:
            ProjectFolder or None if not found
        """
        ...

    @staticmethod
    def delete_folder(folder_id: str, file_path: Path | None = None) -> bool:
        """
        Delete a folder.

        Args:
            folder_id: Folder ID to delete
            file_path: Optional path to folders.json

        Returns:
            True if deleted, False if not found
        """
        ...

    @staticmethod
    def rename_folder(folder_id: str, new_name: str, file_path: Path | None = None) -> bool:
        """Rename a folder."""
        ...

    @staticmethod
    def move_project_to_folder(
        project_id: str, folder_id: str | None, file_path: Path | None = None
    ) -> bool:
        """Move a project to a folder (or root if folder_id is None)."""
        ...

    @staticmethod
    def set_folder_color(folder_id: str, color: str, file_path: Path | None = None) -> bool:
        """Update a folder color."""
        ...

    @staticmethod
    def reorder_folders(folder_ids: list[str], file_path: Path | None = None) -> bool:
        """Persist a new folder ordering."""
        ...

    @staticmethod
    def get_folder_tree(file_path: Path | None = None) -> list[dict]:
        """Return a hierarchical folder tree structure for UI consumption."""
        ...

    @staticmethod
    def get_folder_by_project(project_id: str, file_path: Path | None = None) -> Any | None:
        """Get the folder containing a given project, if any."""
        ...


class IEnvironmentStorage(Protocol):
    """
    Protocol for environment storage operations.

    Infrastructure implementation: EnvironmentStorage
    """

    @staticmethod
    def get_default_environments_file() -> Path:
        """Get default path for environments.json."""
        ...

    @staticmethod
    def save_environments(environments_file: Any, file_path: Path | None = None) -> None:
        """Save environments to file."""
        ...

    @staticmethod
    def load_environments(file_path: Path | None = None) -> Any:
        """Load environments from file."""
        ...

    @staticmethod
    def create_environment(
        name: str,
        description: str = "",
        variables: dict[str, str] | None = None,
        file_path: Path | None = None,
    ) -> Any:
        """Create a new environment."""
        ...

    @staticmethod
    def get_environment(environment_id: str, file_path: Path | None = None) -> Any | None:
        """Get an environment by ID."""
        ...

    @staticmethod
    def delete_environment(environment_id: str, file_path: Path | None = None) -> bool:
        """Delete an environment."""
        ...

    @staticmethod
    def load_environment(env_id: str, environments_dir: Path) -> Any | None:
        """Load a single environment by id."""
        ...

    @staticmethod
    def load_environment_by_type(env_type: Any, environments_dir: Path) -> Any | None:
        """Load a single environment by type."""
        ...

    @staticmethod
    def load_all_environments(environments_dir: Path) -> list[Any]:
        """Load all environments from a project directory."""
        ...

    @staticmethod
    def save_environment(environment: Any, environments_dir: Path) -> None:
        """Persist an environment to disk."""
        ...

    @staticmethod
    def create_default_environments(environments_dir: Path) -> list[Any]:
        """Create default environments (dev/staging/prod) and persist them."""
        ...

    @staticmethod
    def resolve_variables_with_inheritance(
        environment: Any,
        environments_dir: Path,
    ) -> dict[str, Any]:
        """Resolve environment variables including inherited values."""
        ...


class ITemplateStorage(Protocol):
    """
    Protocol for template storage operations.

    Infrastructure implementation: TemplateStorage
    """

    @staticmethod
    def get_templates_directory() -> Path:
        """Get default directory for templates."""
        ...

    @staticmethod
    def list_templates() -> list[Any]:
        """List all available templates."""
        ...

    @staticmethod
    def get_template(template_id: str) -> Any | None:
        """Get a template by ID."""
        ...

    @staticmethod
    def save_template(
        name: str,
        description: str,
        workflow_data: dict[str, Any],
        category: str = "general",
        tags: list[str] | None = None,
    ) -> Any:
        """Save a new template."""
        ...

    @staticmethod
    def delete_template(template_id: str) -> bool:
        """Delete a template."""
        ...

    @staticmethod
    def get_templates_by_category(category: Any) -> list[Any]:
        """List built-in templates in a category."""
        ...

    @staticmethod
    def get_all_templates(user_templates_dir: Path | None = None) -> list[Any]:
        """List all templates (built-in + user templates)."""
        ...

    @staticmethod
    def load_template(template_id: str) -> Any | None:
        """Load a template by id."""
        ...

    @staticmethod
    def save_user_template(template: Any, templates_dir: Path) -> None:
        """Save a user template."""
        ...

    @staticmethod
    def delete_user_template(template_id: str, templates_dir: Path) -> bool:
        """Delete a user template."""
        ...


__all__ = [
    "IFolderStorage",
    "IEnvironmentStorage",
    "ITemplateStorage",
]
