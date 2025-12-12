"""
CasareRPA - Folder Management Use Cases

Application layer use cases for project folder organization.
Handles hierarchical folder structure with drag-drop support.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional

from loguru import logger

from casare_rpa.domain.entities.project import (
    FolderColor,
    ProjectFolder,
)
from casare_rpa.infrastructure.persistence.folder_storage import FolderStorage


# =============================================================================
# Result Types
# =============================================================================


@dataclass
class FolderResult:
    """Result of a folder operation."""

    success: bool
    folder: Optional[ProjectFolder] = None
    error: Optional[str] = None


@dataclass
class FolderListResult:
    """Result of listing folders."""

    success: bool
    folders: List[ProjectFolder] = None
    error: Optional[str] = None

    def __post_init__(self):
        if self.folders is None:
            self.folders = []


@dataclass
class FolderTreeResult:
    """Result of getting folder tree."""

    success: bool
    tree: List[Dict] = None
    error: Optional[str] = None

    def __post_init__(self):
        if self.tree is None:
            self.tree = []


# =============================================================================
# Create Folder Use Case
# =============================================================================


class CreateFolderUseCase:
    """Create a new folder for organizing projects."""

    async def execute(
        self,
        name: str,
        parent_id: Optional[str] = None,
        color: str = FolderColor.BLUE.value,
        description: str = "",
    ) -> FolderResult:
        """
        Create a new folder.

        Args:
            name: Folder name
            parent_id: Parent folder ID (None for root)
            color: Folder color (hex)
            description: Folder description

        Returns:
            FolderResult with created folder or error
        """
        try:
            # Validate parent exists if specified
            if parent_id:
                folders_file = FolderStorage.load_folders()
                parent = folders_file.get_folder(parent_id)
                if not parent:
                    return FolderResult(
                        success=False,
                        error=f"Parent folder not found: {parent_id}",
                    )

            folder = FolderStorage.create_folder(
                name=name,
                parent_id=parent_id,
                color=color,
            )

            if description:
                folder.description = description
                # Reload and save the updated folders file
                folders_file = FolderStorage.load_folders()
                if folders_file.get_folder(folder.id):
                    folders_file.get_folder(folder.id).description = description
                    FolderStorage.save_folders(folders_file)

            logger.info(f"Created folder: {name}")
            return FolderResult(success=True, folder=folder)

        except Exception as e:
            logger.error(f"Failed to create folder: {e}")
            return FolderResult(success=False, error=str(e))


# =============================================================================
# Rename Folder Use Case
# =============================================================================


class RenameFolderUseCase:
    """Rename an existing folder."""

    async def execute(
        self,
        folder_id: str,
        new_name: str,
    ) -> FolderResult:
        """
        Rename a folder.

        Args:
            folder_id: Folder to rename
            new_name: New folder name

        Returns:
            FolderResult with renamed folder
        """
        try:
            success = FolderStorage.rename_folder(folder_id, new_name)

            if not success:
                return FolderResult(
                    success=False,
                    error=f"Folder not found: {folder_id}",
                )

            # Get updated folder
            folders_file = FolderStorage.load_folders()
            folder = folders_file.get_folder(folder_id)

            logger.info(f"Renamed folder to: {new_name}")
            return FolderResult(success=True, folder=folder)

        except Exception as e:
            logger.error(f"Failed to rename folder: {e}")
            return FolderResult(success=False, error=str(e))


# =============================================================================
# Delete Folder Use Case
# =============================================================================


class DeleteFolderUseCase:
    """Delete a folder and move contents to parent."""

    async def execute(self, folder_id: str) -> FolderResult:
        """
        Delete a folder.

        Projects and child folders are moved to parent (or root).

        Args:
            folder_id: Folder to delete

        Returns:
            FolderResult indicating success
        """
        try:
            success = FolderStorage.delete_folder(folder_id)

            if not success:
                return FolderResult(
                    success=False,
                    error=f"Folder not found: {folder_id}",
                )

            logger.info(f"Deleted folder: {folder_id}")
            return FolderResult(success=True)

        except Exception as e:
            logger.error(f"Failed to delete folder: {e}")
            return FolderResult(success=False, error=str(e))


# =============================================================================
# Move Project Use Case
# =============================================================================


class MoveProjectToFolderUseCase:
    """Move a project to a folder."""

    async def execute(
        self,
        project_id: str,
        target_folder_id: Optional[str] = None,
    ) -> FolderResult:
        """
        Move a project to a folder.

        Args:
            project_id: Project to move
            target_folder_id: Destination folder (None for root)

        Returns:
            FolderResult indicating success
        """
        try:
            # Validate target folder exists if specified
            if target_folder_id:
                folders_file = FolderStorage.load_folders()
                target = folders_file.get_folder(target_folder_id)
                if not target:
                    return FolderResult(
                        success=False,
                        error=f"Target folder not found: {target_folder_id}",
                    )

            success = FolderStorage.move_project_to_folder(project_id, target_folder_id)

            if not success:
                return FolderResult(
                    success=False,
                    error="Failed to move project",
                )

            logger.info(f"Moved project {project_id} to folder {target_folder_id}")
            return FolderResult(success=True)

        except Exception as e:
            logger.error(f"Failed to move project: {e}")
            return FolderResult(success=False, error=str(e))


# =============================================================================
# Set Folder Color Use Case
# =============================================================================


class SetFolderColorUseCase:
    """Change folder color."""

    async def execute(
        self,
        folder_id: str,
        color: str,
    ) -> FolderResult:
        """
        Set folder color.

        Args:
            folder_id: Folder to update
            color: New color (hex)

        Returns:
            FolderResult with updated folder
        """
        try:
            success = FolderStorage.set_folder_color(folder_id, color)

            if not success:
                return FolderResult(
                    success=False,
                    error=f"Folder not found: {folder_id}",
                )

            folders_file = FolderStorage.load_folders()
            folder = folders_file.get_folder(folder_id)

            logger.info(f"Set folder {folder_id} color to {color}")
            return FolderResult(success=True, folder=folder)

        except Exception as e:
            logger.error(f"Failed to set folder color: {e}")
            return FolderResult(success=False, error=str(e))


# =============================================================================
# Reorder Folders Use Case
# =============================================================================


class ReorderFoldersUseCase:
    """Reorder folders (for drag-drop)."""

    async def execute(self, folder_ids: List[str]) -> FolderListResult:
        """
        Reorder folders.

        Args:
            folder_ids: List of folder IDs in desired order

        Returns:
            FolderListResult with reordered folders
        """
        try:
            success = FolderStorage.reorder_folders(folder_ids)

            if not success:
                return FolderListResult(
                    success=False,
                    error="Failed to reorder folders",
                )

            folders_file = FolderStorage.load_folders()
            folders = [
                folder for fid in folder_ids if (folder := folders_file.get_folder(fid))
            ]

            logger.info(f"Reordered {len(folders)} folders")
            return FolderListResult(success=True, folders=folders)

        except Exception as e:
            logger.error(f"Failed to reorder folders: {e}")
            return FolderListResult(success=False, error=str(e))


# =============================================================================
# Get Folder Tree Use Case
# =============================================================================


class GetFolderTreeUseCase:
    """Get folder hierarchy as tree structure."""

    async def execute(self) -> FolderTreeResult:
        """
        Get folder tree.

        Returns:
            FolderTreeResult with nested tree structure
        """
        try:
            tree = FolderStorage.get_folder_tree()
            return FolderTreeResult(success=True, tree=tree)

        except Exception as e:
            logger.error(f"Failed to get folder tree: {e}")
            return FolderTreeResult(success=False, error=str(e))


# =============================================================================
# Get Folder By Project Use Case
# =============================================================================


class GetFolderByProjectUseCase:
    """Get the folder containing a project."""

    async def execute(self, project_id: str) -> FolderResult:
        """
        Get folder containing project.

        Args:
            project_id: Project ID

        Returns:
            FolderResult with folder (or None if not in any folder)
        """
        try:
            folder = FolderStorage.get_folder_by_project(project_id)
            return FolderResult(success=True, folder=folder)

        except Exception as e:
            logger.error(f"Failed to get folder by project: {e}")
            return FolderResult(success=False, error=str(e))


# =============================================================================
# List Root Folders Use Case
# =============================================================================


class ListRootFoldersUseCase:
    """List all root-level folders."""

    async def execute(self) -> FolderListResult:
        """
        List root folders.

        Returns:
            FolderListResult with root folders
        """
        try:
            folders_file = FolderStorage.load_folders()
            folders = folders_file.get_root_folders()
            return FolderListResult(success=True, folders=folders)

        except Exception as e:
            logger.error(f"Failed to list root folders: {e}")
            return FolderListResult(success=False, error=str(e))
