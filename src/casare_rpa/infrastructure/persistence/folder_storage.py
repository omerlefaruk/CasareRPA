"""
CasareRPA - Folder Storage

Infrastructure service for loading and managing project folders.
"""

import orjson
from loguru import logger
from pathlib import Path
from typing import Dict, List, Optional

from casare_rpa.domain.entities.project.folder import (
    FolderColor,
    FoldersFile,
    ProjectFolder,
)


class FolderStorage:
    """
    Static adapter for folder file operations.

    Folders are stored globally in ~/.casare_rpa/config/folders.json
    """

    @staticmethod
    def get_default_folders_file() -> Path:
        """Get default path for folders.json."""
        return Path.home() / ".casare_rpa" / "config" / "folders.json"

    @staticmethod
    def save_folders(
        folders_file: FoldersFile, file_path: Optional[Path] = None
    ) -> None:
        """
        Save folders to file.

        Args:
            folders_file: Folders container
            file_path: Optional path (uses default if not provided)
        """
        if file_path is None:
            file_path = FolderStorage.get_default_folders_file()

        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(
            orjson.dumps(folders_file.to_dict(), option=orjson.OPT_INDENT_2)
        )

    @staticmethod
    def load_folders(file_path: Optional[Path] = None) -> FoldersFile:
        """
        Load folders from file.

        Args:
            file_path: Optional path (uses default if not provided)

        Returns:
            FoldersFile instance
        """
        if file_path is None:
            file_path = FolderStorage.get_default_folders_file()

        if not file_path.exists():
            return FoldersFile()

        try:
            data = orjson.loads(file_path.read_bytes())
            return FoldersFile.from_dict(data)
        except Exception as e:
            logger.warning(f"Error loading folders: {e}")
            return FoldersFile()

    @staticmethod
    def create_folder(
        name: str,
        parent_id: Optional[str] = None,
        color: str = FolderColor.BLUE.value,
        file_path: Optional[Path] = None,
    ) -> ProjectFolder:
        """
        Create a new folder.

        Args:
            name: Folder name
            parent_id: Parent folder ID (None for root)
            color: Folder color
            file_path: Optional path to folders.json

        Returns:
            Created folder
        """
        folders_file = FolderStorage.load_folders(file_path)

        folder = ProjectFolder.create_new(
            name=name,
            parent_id=parent_id,
            color=color,
        )

        folders_file.add_folder(folder)
        FolderStorage.save_folders(folders_file, file_path)

        return folder

    @staticmethod
    def delete_folder(folder_id: str, file_path: Optional[Path] = None) -> bool:
        """
        Delete a folder and move its projects to parent (or root).

        Args:
            folder_id: Folder to delete
            file_path: Optional path to folders.json

        Returns:
            True if deleted
        """
        folders_file = FolderStorage.load_folders(file_path)

        folder = folders_file.get_folder(folder_id)
        if not folder:
            return False

        # Move projects to parent folder
        parent_id = folder.parent_id
        for project_id in folder.project_ids:
            if parent_id:
                parent = folders_file.get_folder(parent_id)
                if parent:
                    parent.add_project(project_id)

        # Move child folders to parent
        for child in folders_file.get_children(folder_id):
            child.parent_id = parent_id
            child.touch_modified()

        # Remove folder
        folders_file.remove_folder(folder_id)
        FolderStorage.save_folders(folders_file, file_path)

        return True

    @staticmethod
    def rename_folder(
        folder_id: str, new_name: str, file_path: Optional[Path] = None
    ) -> bool:
        """
        Rename a folder.

        Args:
            folder_id: Folder to rename
            new_name: New folder name
            file_path: Optional path to folders.json

        Returns:
            True if renamed
        """
        folders_file = FolderStorage.load_folders(file_path)

        folder = folders_file.get_folder(folder_id)
        if not folder:
            return False

        folder.name = new_name
        folder.touch_modified()

        FolderStorage.save_folders(folders_file, file_path)
        return True

    @staticmethod
    def move_project_to_folder(
        project_id: str,
        target_folder_id: Optional[str],
        file_path: Optional[Path] = None,
    ) -> bool:
        """
        Move a project to a folder.

        Args:
            project_id: Project to move
            target_folder_id: Destination folder (None for root)
            file_path: Optional path to folders.json

        Returns:
            True if moved
        """
        folders_file = FolderStorage.load_folders(file_path)

        # Find current folder containing project
        current_folder_id = None
        for folder in folders_file.folders.values():
            if project_id in folder.project_ids:
                current_folder_id = folder.id
                break

        # Move project
        folders_file.move_project(project_id, current_folder_id, target_folder_id)
        FolderStorage.save_folders(folders_file, file_path)

        return True

    @staticmethod
    def get_folder_tree(file_path: Optional[Path] = None) -> List[Dict]:
        """
        Get folder hierarchy as nested tree structure.

        Args:
            file_path: Optional path to folders.json

        Returns:
            List of root folders with nested children
        """
        folders_file = FolderStorage.load_folders(file_path)

        def build_tree(parent_id: Optional[str]) -> List[Dict]:
            children = []
            for folder in folders_file.folders.values():
                if folder.parent_id == parent_id and not folder.is_archived:
                    children.append(
                        {
                            "folder": folder,
                            "children": build_tree(folder.id),
                        }
                    )
            # Sort by sort_order, then name
            children.sort(key=lambda x: (x["folder"].sort_order, x["folder"].name))
            return children

        return build_tree(None)

    @staticmethod
    def get_folder_by_project(
        project_id: str, file_path: Optional[Path] = None
    ) -> Optional[ProjectFolder]:
        """
        Get the folder containing a project.

        Args:
            project_id: Project to find
            file_path: Optional path to folders.json

        Returns:
            Folder containing project, or None
        """
        folders_file = FolderStorage.load_folders(file_path)

        for folder in folders_file.folders.values():
            if project_id in folder.project_ids:
                return folder

        return None

    @staticmethod
    def set_folder_color(
        folder_id: str, color: str, file_path: Optional[Path] = None
    ) -> bool:
        """
        Set folder color.

        Args:
            folder_id: Folder to update
            color: New color (hex)
            file_path: Optional path to folders.json

        Returns:
            True if updated
        """
        folders_file = FolderStorage.load_folders(file_path)

        folder = folders_file.get_folder(folder_id)
        if not folder:
            return False

        folder.color = color
        folder.touch_modified()

        FolderStorage.save_folders(folders_file, file_path)
        return True

    @staticmethod
    def reorder_folders(
        folder_ids: List[str], file_path: Optional[Path] = None
    ) -> bool:
        """
        Reorder folders by setting sort_order.

        Args:
            folder_ids: List of folder IDs in desired order
            file_path: Optional path to folders.json

        Returns:
            True if reordered
        """
        folders_file = FolderStorage.load_folders(file_path)

        for index, folder_id in enumerate(folder_ids):
            folder = folders_file.get_folder(folder_id)
            if folder:
                folder.sort_order = index
                folder.touch_modified()

        FolderStorage.save_folders(folders_file, file_path)
        return True
