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


__all__ = [
    "IFolderStorage",
    "IEnvironmentStorage",
    "ITemplateStorage",
]
