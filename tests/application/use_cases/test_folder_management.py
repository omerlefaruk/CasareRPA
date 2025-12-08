"""Tests for folder management use cases."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock

from casare_rpa.domain.entities.project import (
    FolderColor,
    FoldersFile,
    ProjectFolder,
)
from casare_rpa.domain.entities.project.folder import generate_folder_id
from casare_rpa.application.use_cases.folder_management import (
    CreateFolderUseCase,
    RenameFolderUseCase,
    DeleteFolderUseCase,
    MoveProjectToFolderUseCase,
    SetFolderColorUseCase,
    ReorderFoldersUseCase,
    GetFolderTreeUseCase,
    GetFolderByProjectUseCase,
    ListRootFoldersUseCase,
    FolderResult,
    FolderListResult,
    FolderTreeResult,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_folder():
    """Create a sample folder."""
    return ProjectFolder.create_new(
        name="Test Folder",
        color=FolderColor.BLUE.value,
    )


@pytest.fixture
def sample_folders_file():
    """Create a sample folders file with multiple folders."""
    folders_file = FoldersFile()

    parent_folder = ProjectFolder.create_new(name="Parent Folder")
    child_folder = ProjectFolder.create_new(
        name="Child Folder",
        parent_id=parent_folder.id,
    )

    folders_file.add_folder(parent_folder)
    folders_file.add_folder(child_folder)

    return folders_file


# =============================================================================
# CreateFolderUseCase Tests
# =============================================================================


class TestCreateFolderUseCase:
    """Tests for CreateFolderUseCase."""

    @pytest.mark.asyncio
    async def test_create_folder_success(self):
        """Test successful folder creation."""
        mock_folder = ProjectFolder.create_new(name="New Folder")

        with patch(
            "casare_rpa.application.use_cases.folder_management.FolderStorage"
        ) as mock_storage:
            mock_storage.load_folders.return_value = FoldersFile()
            mock_storage.create_folder.return_value = mock_folder
            mock_storage.save_folders.return_value = None

            use_case = CreateFolderUseCase()
            result = await use_case.execute(
                name="New Folder",
                color=FolderColor.GREEN.value,
                description="Test description",
            )

            assert result.success is True
            assert result.folder is not None
            assert result.error is None
            mock_storage.create_folder.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_folder_with_parent(self, sample_folder):
        """Test creating folder with parent."""
        folders_file = FoldersFile()
        folders_file.add_folder(sample_folder)

        with patch(
            "casare_rpa.application.use_cases.folder_management.FolderStorage"
        ) as mock_storage:
            mock_storage.load_folders.return_value = folders_file
            mock_storage.create_folder.return_value = ProjectFolder.create_new(
                name="Child", parent_id=sample_folder.id
            )

            use_case = CreateFolderUseCase()
            result = await use_case.execute(
                name="Child",
                parent_id=sample_folder.id,
            )

            assert result.success is True
            assert result.folder is not None

    @pytest.mark.asyncio
    async def test_create_folder_parent_not_found(self):
        """Test creating folder with non-existent parent."""
        with patch(
            "casare_rpa.application.use_cases.folder_management.FolderStorage"
        ) as mock_storage:
            folders_file = FoldersFile()
            mock_storage.load_folders.return_value = folders_file

            use_case = CreateFolderUseCase()
            result = await use_case.execute(
                name="Child",
                parent_id="fold_nonexistent",
            )

            assert result.success is False
            assert "not found" in result.error

    @pytest.mark.asyncio
    async def test_create_folder_exception_handling(self):
        """Test error handling when storage fails."""
        with patch(
            "casare_rpa.application.use_cases.folder_management.FolderStorage"
        ) as mock_storage:
            # First call succeeds (no parent validation needed)
            # But create_folder fails
            mock_storage.create_folder.side_effect = Exception("Storage error")

            use_case = CreateFolderUseCase()
            result = await use_case.execute(name="Failing Folder")

            assert result.success is False
            assert "Storage error" in result.error


# =============================================================================
# RenameFolderUseCase Tests
# =============================================================================


class TestRenameFolderUseCase:
    """Tests for RenameFolderUseCase."""

    @pytest.mark.asyncio
    async def test_rename_folder_success(self, sample_folder):
        """Test successful folder rename."""
        folders_file = FoldersFile()
        sample_folder.name = "Renamed Folder"
        folders_file.add_folder(sample_folder)

        with patch(
            "casare_rpa.application.use_cases.folder_management.FolderStorage"
        ) as mock_storage:
            mock_storage.rename_folder.return_value = True
            mock_storage.load_folders.return_value = folders_file

            use_case = RenameFolderUseCase()
            result = await use_case.execute(
                folder_id=sample_folder.id,
                new_name="Renamed Folder",
            )

            assert result.success is True
            assert result.folder.name == "Renamed Folder"
            mock_storage.rename_folder.assert_called_once()

    @pytest.mark.asyncio
    async def test_rename_folder_not_found(self):
        """Test renaming non-existent folder."""
        with patch(
            "casare_rpa.application.use_cases.folder_management.FolderStorage"
        ) as mock_storage:
            mock_storage.rename_folder.return_value = False

            use_case = RenameFolderUseCase()
            result = await use_case.execute(
                folder_id="fold_nonexistent",
                new_name="New Name",
            )

            assert result.success is False
            assert "not found" in result.error


# =============================================================================
# DeleteFolderUseCase Tests
# =============================================================================


class TestDeleteFolderUseCase:
    """Tests for DeleteFolderUseCase."""

    @pytest.mark.asyncio
    async def test_delete_folder_success(self, sample_folder):
        """Test successful folder deletion."""
        with patch(
            "casare_rpa.application.use_cases.folder_management.FolderStorage"
        ) as mock_storage:
            mock_storage.delete_folder.return_value = True

            use_case = DeleteFolderUseCase()
            result = await use_case.execute(folder_id=sample_folder.id)

            assert result.success is True
            mock_storage.delete_folder.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_folder_not_found(self):
        """Test deleting non-existent folder."""
        with patch(
            "casare_rpa.application.use_cases.folder_management.FolderStorage"
        ) as mock_storage:
            mock_storage.delete_folder.return_value = False

            use_case = DeleteFolderUseCase()
            result = await use_case.execute(folder_id="fold_nonexistent")

            assert result.success is False
            assert "not found" in result.error

    @pytest.mark.asyncio
    async def test_delete_folder_exception_handling(self):
        """Test error handling when delete fails."""
        with patch(
            "casare_rpa.application.use_cases.folder_management.FolderStorage"
        ) as mock_storage:
            mock_storage.delete_folder.side_effect = Exception("Delete error")

            use_case = DeleteFolderUseCase()
            result = await use_case.execute(folder_id="fold_test")

            assert result.success is False
            assert "Delete error" in result.error


# =============================================================================
# MoveProjectToFolderUseCase Tests
# =============================================================================


class TestMoveProjectToFolderUseCase:
    """Tests for MoveProjectToFolderUseCase."""

    @pytest.mark.asyncio
    async def test_move_project_to_folder_success(self, sample_folder):
        """Test successfully moving a project to a folder."""
        folders_file = FoldersFile()
        folders_file.add_folder(sample_folder)

        with patch(
            "casare_rpa.application.use_cases.folder_management.FolderStorage"
        ) as mock_storage:
            mock_storage.load_folders.return_value = folders_file
            mock_storage.move_project_to_folder.return_value = True

            use_case = MoveProjectToFolderUseCase()
            result = await use_case.execute(
                project_id="proj_12345",
                target_folder_id=sample_folder.id,
            )

            assert result.success is True
            mock_storage.move_project_to_folder.assert_called_once()

    @pytest.mark.asyncio
    async def test_move_project_to_root(self):
        """Test moving project to root (no folder)."""
        with patch(
            "casare_rpa.application.use_cases.folder_management.FolderStorage"
        ) as mock_storage:
            mock_storage.move_project_to_folder.return_value = True

            use_case = MoveProjectToFolderUseCase()
            result = await use_case.execute(
                project_id="proj_12345",
                target_folder_id=None,
            )

            assert result.success is True

    @pytest.mark.asyncio
    async def test_move_project_target_not_found(self):
        """Test moving project to non-existent folder."""
        with patch(
            "casare_rpa.application.use_cases.folder_management.FolderStorage"
        ) as mock_storage:
            mock_storage.load_folders.return_value = FoldersFile()

            use_case = MoveProjectToFolderUseCase()
            result = await use_case.execute(
                project_id="proj_12345",
                target_folder_id="fold_nonexistent",
            )

            assert result.success is False
            assert "not found" in result.error


# =============================================================================
# SetFolderColorUseCase Tests
# =============================================================================


class TestSetFolderColorUseCase:
    """Tests for SetFolderColorUseCase."""

    @pytest.mark.asyncio
    async def test_set_folder_color_success(self, sample_folder):
        """Test successfully setting folder color."""
        folders_file = FoldersFile()
        sample_folder.color = FolderColor.RED.value
        folders_file.add_folder(sample_folder)

        with patch(
            "casare_rpa.application.use_cases.folder_management.FolderStorage"
        ) as mock_storage:
            mock_storage.set_folder_color.return_value = True
            mock_storage.load_folders.return_value = folders_file

            use_case = SetFolderColorUseCase()
            result = await use_case.execute(
                folder_id=sample_folder.id,
                color=FolderColor.RED.value,
            )

            assert result.success is True
            assert result.folder.color == FolderColor.RED.value

    @pytest.mark.asyncio
    async def test_set_folder_color_not_found(self):
        """Test setting color on non-existent folder."""
        with patch(
            "casare_rpa.application.use_cases.folder_management.FolderStorage"
        ) as mock_storage:
            mock_storage.set_folder_color.return_value = False

            use_case = SetFolderColorUseCase()
            result = await use_case.execute(
                folder_id="fold_nonexistent",
                color=FolderColor.GREEN.value,
            )

            assert result.success is False
            assert "not found" in result.error


# =============================================================================
# ReorderFoldersUseCase Tests
# =============================================================================


class TestReorderFoldersUseCase:
    """Tests for ReorderFoldersUseCase."""

    @pytest.mark.asyncio
    async def test_reorder_folders_success(self):
        """Test successfully reordering folders."""
        folders_file = FoldersFile()
        folder1 = ProjectFolder.create_new(name="Folder 1")
        folder2 = ProjectFolder.create_new(name="Folder 2")
        folders_file.add_folder(folder1)
        folders_file.add_folder(folder2)

        with patch(
            "casare_rpa.application.use_cases.folder_management.FolderStorage"
        ) as mock_storage:
            mock_storage.reorder_folders.return_value = True
            mock_storage.load_folders.return_value = folders_file

            use_case = ReorderFoldersUseCase()
            result = await use_case.execute(
                folder_ids=[folder2.id, folder1.id],  # Reversed order
            )

            assert result.success is True
            mock_storage.reorder_folders.assert_called_once()

    @pytest.mark.asyncio
    async def test_reorder_folders_failure(self):
        """Test reordering folders failure."""
        with patch(
            "casare_rpa.application.use_cases.folder_management.FolderStorage"
        ) as mock_storage:
            mock_storage.reorder_folders.return_value = False

            use_case = ReorderFoldersUseCase()
            result = await use_case.execute(folder_ids=["fold_1", "fold_2"])

            assert result.success is False
            assert "Failed to reorder" in result.error


# =============================================================================
# GetFolderTreeUseCase Tests
# =============================================================================


class TestGetFolderTreeUseCase:
    """Tests for GetFolderTreeUseCase."""

    @pytest.mark.asyncio
    async def test_get_folder_tree_success(self, sample_folders_file):
        """Test successfully getting folder tree."""
        mock_tree = [
            {
                "folder": sample_folders_file.get_root_folders()[0],
                "children": [],
            }
        ]

        with patch(
            "casare_rpa.application.use_cases.folder_management.FolderStorage"
        ) as mock_storage:
            mock_storage.get_folder_tree.return_value = mock_tree

            use_case = GetFolderTreeUseCase()
            result = await use_case.execute()

            assert result.success is True
            assert len(result.tree) == 1
            mock_storage.get_folder_tree.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_folder_tree_empty(self):
        """Test getting empty folder tree."""
        with patch(
            "casare_rpa.application.use_cases.folder_management.FolderStorage"
        ) as mock_storage:
            mock_storage.get_folder_tree.return_value = []

            use_case = GetFolderTreeUseCase()
            result = await use_case.execute()

            assert result.success is True
            assert result.tree == []

    @pytest.mark.asyncio
    async def test_get_folder_tree_exception(self):
        """Test error handling when getting tree fails."""
        with patch(
            "casare_rpa.application.use_cases.folder_management.FolderStorage"
        ) as mock_storage:
            mock_storage.get_folder_tree.side_effect = Exception("Tree error")

            use_case = GetFolderTreeUseCase()
            result = await use_case.execute()

            assert result.success is False
            assert "Tree error" in result.error


# =============================================================================
# GetFolderByProjectUseCase Tests
# =============================================================================


class TestGetFolderByProjectUseCase:
    """Tests for GetFolderByProjectUseCase."""

    @pytest.mark.asyncio
    async def test_get_folder_by_project_success(self, sample_folder):
        """Test successfully getting folder containing a project."""
        sample_folder.add_project("proj_12345")

        with patch(
            "casare_rpa.application.use_cases.folder_management.FolderStorage"
        ) as mock_storage:
            mock_storage.get_folder_by_project.return_value = sample_folder

            use_case = GetFolderByProjectUseCase()
            result = await use_case.execute(project_id="proj_12345")

            assert result.success is True
            assert result.folder is not None
            assert result.folder.has_project("proj_12345")

    @pytest.mark.asyncio
    async def test_get_folder_by_project_not_in_folder(self):
        """Test getting folder for project not in any folder."""
        with patch(
            "casare_rpa.application.use_cases.folder_management.FolderStorage"
        ) as mock_storage:
            mock_storage.get_folder_by_project.return_value = None

            use_case = GetFolderByProjectUseCase()
            result = await use_case.execute(project_id="proj_no_folder")

            assert result.success is True
            assert result.folder is None


# =============================================================================
# ListRootFoldersUseCase Tests
# =============================================================================


class TestListRootFoldersUseCase:
    """Tests for ListRootFoldersUseCase."""

    @pytest.mark.asyncio
    async def test_list_root_folders_success(self):
        """Test successfully listing root folders."""
        folders_file = FoldersFile()
        folder1 = ProjectFolder.create_new(name="Root 1")
        folder2 = ProjectFolder.create_new(name="Root 2")
        folders_file.add_folder(folder1)
        folders_file.add_folder(folder2)

        with patch(
            "casare_rpa.application.use_cases.folder_management.FolderStorage"
        ) as mock_storage:
            mock_storage.load_folders.return_value = folders_file

            use_case = ListRootFoldersUseCase()
            result = await use_case.execute()

            assert result.success is True
            assert len(result.folders) == 2

    @pytest.mark.asyncio
    async def test_list_root_folders_empty(self):
        """Test listing when no root folders exist."""
        with patch(
            "casare_rpa.application.use_cases.folder_management.FolderStorage"
        ) as mock_storage:
            mock_storage.load_folders.return_value = FoldersFile()

            use_case = ListRootFoldersUseCase()
            result = await use_case.execute()

            assert result.success is True
            assert result.folders == []

    @pytest.mark.asyncio
    async def test_list_root_folders_exception(self):
        """Test error handling when listing fails."""
        with patch(
            "casare_rpa.application.use_cases.folder_management.FolderStorage"
        ) as mock_storage:
            mock_storage.load_folders.side_effect = Exception("Load error")

            use_case = ListRootFoldersUseCase()
            result = await use_case.execute()

            assert result.success is False
            assert "Load error" in result.error
