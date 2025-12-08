"""
Tests for ProjectFolder domain entity.

Tests cover:
- Folder creation and initialization
- Folder hierarchy operations (parent/child)
- Project management within folders
- Serialization/deserialization round-trip
"""

import pytest
from datetime import datetime

from casare_rpa.domain.entities.project.folder import (
    ProjectFolder,
    FoldersFile,
    FolderColor,
    generate_folder_id,
)


class TestProjectFolderCreation:
    """Tests for ProjectFolder entity creation."""

    def test_create_folder_with_required_fields(self):
        """Folder can be created with minimal required fields."""
        folder = ProjectFolder(id="fold_test1", name="Test Folder")

        assert folder.id == "fold_test1"
        assert folder.name == "Test Folder"
        assert folder.parent_id is None
        assert folder.description == ""
        assert folder.project_ids == []
        assert folder.is_expanded is True
        assert folder.is_archived is False

    def test_create_folder_with_all_fields(self):
        """Folder can be created with all fields."""
        folder = ProjectFolder(
            id="fold_sub",
            name="Subfolder",
            parent_id="fold_parent",
            description="A subfolder for organization",
            color="#4CAF50",
            icon="folder-open",
            project_ids=["proj_1", "proj_2"],
            is_expanded=False,
            is_archived=False,
            sort_order=5,
        )

        assert folder.id == "fold_sub"
        assert folder.name == "Subfolder"
        assert folder.parent_id == "fold_parent"
        assert folder.description == "A subfolder for organization"
        assert folder.color == "#4CAF50"
        assert folder.icon == "folder-open"
        assert folder.project_ids == ["proj_1", "proj_2"]
        assert folder.is_expanded is False
        assert folder.sort_order == 5

    def test_timestamps_auto_initialized(self):
        """Created and modified timestamps are auto-initialized."""
        before = datetime.now()
        folder = ProjectFolder(id="fold_test", name="Test")
        after = datetime.now()

        assert folder.created_at is not None
        assert folder.modified_at is not None
        assert before <= folder.created_at <= after

    def test_default_color_is_blue(self):
        """Default folder color is blue."""
        folder = ProjectFolder(id="fold_test", name="Test")

        assert folder.color == FolderColor.BLUE.value
        assert folder.color == "#2196F3"

    def test_generate_folder_id_format(self):
        """Generated ID has correct format."""
        folder_id = generate_folder_id()

        assert folder_id.startswith("fold_")
        assert len(folder_id) == 13  # fold_ + 8 hex chars

    def test_create_new_factory_method(self):
        """create_new() factory generates ID and sets fields."""
        folder = ProjectFolder.create_new(
            name="New Folder",
            parent_id="fold_parent",
            color=FolderColor.GREEN.value,
        )

        assert folder.id.startswith("fold_")
        assert folder.name == "New Folder"
        assert folder.parent_id == "fold_parent"
        assert folder.color == FolderColor.GREEN.value


class TestFolderHierarchy:
    """Tests for folder hierarchy operations."""

    def test_is_root_true_for_no_parent(self):
        """is_root is True when parent_id is None."""
        folder = ProjectFolder(id="fold_root", name="Root Folder")

        assert folder.is_root is True

    def test_is_root_false_with_parent(self):
        """is_root is False when parent_id is set."""
        folder = ProjectFolder(
            id="fold_child", name="Child Folder", parent_id="fold_parent"
        )

        assert folder.is_root is False


class TestFolderProjectManagement:
    """Tests for managing projects within folders."""

    def test_add_project_success(self):
        """add_project() adds project ID to list."""
        folder = ProjectFolder(id="fold_test", name="Test")

        result = folder.add_project("proj_001")

        assert result is True
        assert "proj_001" in folder.project_ids

    def test_add_project_duplicate_returns_false(self):
        """add_project() returns False for duplicate."""
        folder = ProjectFolder(id="fold_test", name="Test", project_ids=["proj_001"])

        result = folder.add_project("proj_001")

        assert result is False
        assert folder.project_ids.count("proj_001") == 1

    def test_remove_project_success(self):
        """remove_project() removes project ID from list."""
        folder = ProjectFolder(
            id="fold_test", name="Test", project_ids=["proj_001", "proj_002"]
        )

        result = folder.remove_project("proj_001")

        assert result is True
        assert "proj_001" not in folder.project_ids
        assert "proj_002" in folder.project_ids

    def test_remove_project_not_found_returns_false(self):
        """remove_project() returns False when not found."""
        folder = ProjectFolder(id="fold_test", name="Test", project_ids=["proj_001"])

        result = folder.remove_project("proj_999")

        assert result is False
        assert "proj_001" in folder.project_ids

    def test_has_project_returns_true(self):
        """has_project() returns True when project exists."""
        folder = ProjectFolder(id="fold_test", name="Test", project_ids=["proj_001"])

        assert folder.has_project("proj_001") is True

    def test_has_project_returns_false(self):
        """has_project() returns False when project not exists."""
        folder = ProjectFolder(id="fold_test", name="Test")

        assert folder.has_project("proj_001") is False

    def test_project_count_property(self):
        """project_count returns correct count."""
        folder = ProjectFolder(
            id="fold_test",
            name="Test",
            project_ids=["proj_1", "proj_2", "proj_3"],
        )

        assert folder.project_count == 3

    def test_add_project_updates_modified_timestamp(self):
        """add_project() updates modified_at."""
        folder = ProjectFolder(id="fold_test", name="Test")
        original_modified = folder.modified_at

        import time

        time.sleep(0.01)
        folder.add_project("proj_new")

        assert folder.modified_at > original_modified


class TestFolderSerialization:
    """Tests for ProjectFolder serialization/deserialization."""

    def test_to_dict_contains_all_fields(self):
        """to_dict() includes all folder fields."""
        folder = ProjectFolder(
            id="fold_test",
            name="Test Folder",
            parent_id="fold_parent",
            description="Test description",
            color="#FF9800",
            icon="folder-star",
            project_ids=["proj_1", "proj_2"],
            is_expanded=False,
            is_archived=True,
            sort_order=10,
        )

        data = folder.to_dict()

        assert data["id"] == "fold_test"
        assert data["name"] == "Test Folder"
        assert data["parent_id"] == "fold_parent"
        assert data["description"] == "Test description"
        assert data["color"] == "#FF9800"
        assert data["icon"] == "folder-star"
        assert data["project_ids"] == ["proj_1", "proj_2"]
        assert data["is_expanded"] is False
        assert data["is_archived"] is True
        assert data["sort_order"] == 10
        assert "created_at" in data
        assert "modified_at" in data

    def test_from_dict_restores_all_fields(self):
        """from_dict() restores all folder fields."""
        data = {
            "id": "fold_restored",
            "name": "Restored Folder",
            "parent_id": "fold_parent",
            "description": "Restored description",
            "color": "#E91E63",
            "icon": "folder-heart",
            "project_ids": ["proj_a", "proj_b"],
            "is_expanded": True,
            "is_archived": False,
            "sort_order": 5,
            "created_at": "2025-01-15T09:00:00",
            "modified_at": "2025-01-20T14:30:00",
        }

        folder = ProjectFolder.from_dict(data)

        assert folder.id == "fold_restored"
        assert folder.name == "Restored Folder"
        assert folder.parent_id == "fold_parent"
        assert folder.description == "Restored description"
        assert folder.color == "#E91E63"
        assert folder.project_ids == ["proj_a", "proj_b"]
        assert folder.created_at.day == 15

    def test_round_trip_serialization(self):
        """Serialization -> deserialization produces equivalent object."""
        original = ProjectFolder(
            id="fold_original",
            name="Original",
            parent_id="fold_parent",
            project_ids=["proj_1", "proj_2", "proj_3"],
            color=FolderColor.PURPLE.value,
            sort_order=7,
        )

        data = original.to_dict()
        restored = ProjectFolder.from_dict(data)

        assert restored.id == original.id
        assert restored.name == original.name
        assert restored.parent_id == original.parent_id
        assert restored.project_ids == original.project_ids
        assert restored.color == original.color
        assert restored.sort_order == original.sort_order


class TestFoldersFile:
    """Tests for FoldersFile container."""

    def test_empty_folders_file(self):
        """Empty FoldersFile has correct defaults."""
        folders_file = FoldersFile()

        assert folders_file.folders == {}
        assert folders_file.schema_version == "2.0.0"

    def test_add_folder(self):
        """add_folder() adds folder to collection."""
        folders_file = FoldersFile()
        folder = ProjectFolder(id="fold_001", name="Folder 1")

        folders_file.add_folder(folder)

        assert "fold_001" in folders_file.folders
        assert folders_file.folders["fold_001"].name == "Folder 1"

    def test_get_folder_found(self):
        """get_folder() returns folder when found."""
        folder = ProjectFolder(id="fold_001", name="Folder 1")
        folders_file = FoldersFile(folders={"fold_001": folder})

        result = folders_file.get_folder("fold_001")

        assert result is not None
        assert result.name == "Folder 1"

    def test_get_folder_not_found(self):
        """get_folder() returns None when not found."""
        folders_file = FoldersFile()

        result = folders_file.get_folder("fold_nonexistent")

        assert result is None

    def test_remove_folder(self):
        """remove_folder() removes and returns True."""
        folder = ProjectFolder(id="fold_001", name="Folder 1")
        folders_file = FoldersFile(folders={"fold_001": folder})

        result = folders_file.remove_folder("fold_001")

        assert result is True
        assert "fold_001" not in folders_file.folders

    def test_get_root_folders(self):
        """get_root_folders() returns folders without parents."""
        root1 = ProjectFolder(id="fold_root1", name="Root 1")
        root2 = ProjectFolder(id="fold_root2", name="Root 2")
        child = ProjectFolder(id="fold_child", name="Child", parent_id="fold_root1")
        archived = ProjectFolder(id="fold_arch", name="Archived", is_archived=True)

        folders_file = FoldersFile(
            folders={
                "fold_root1": root1,
                "fold_root2": root2,
                "fold_child": child,
                "fold_arch": archived,
            }
        )

        roots = folders_file.get_root_folders()

        assert len(roots) == 2
        root_ids = [f.id for f in roots]
        assert "fold_root1" in root_ids
        assert "fold_root2" in root_ids
        assert "fold_child" not in root_ids  # Has parent
        assert "fold_arch" not in root_ids  # Archived

    def test_get_children(self):
        """get_children() returns child folders of parent."""
        parent = ProjectFolder(id="fold_parent", name="Parent")
        child1 = ProjectFolder(id="fold_c1", name="Child 1", parent_id="fold_parent")
        child2 = ProjectFolder(id="fold_c2", name="Child 2", parent_id="fold_parent")
        other = ProjectFolder(
            id="fold_other", name="Other", parent_id="fold_other_parent"
        )

        folders_file = FoldersFile(
            folders={
                "fold_parent": parent,
                "fold_c1": child1,
                "fold_c2": child2,
                "fold_other": other,
            }
        )

        children = folders_file.get_children("fold_parent")

        assert len(children) == 2
        child_ids = [f.id for f in children]
        assert "fold_c1" in child_ids
        assert "fold_c2" in child_ids

    def test_get_folder_path(self):
        """get_folder_path() returns path from root to folder."""
        root = ProjectFolder(id="fold_root", name="Root")
        level1 = ProjectFolder(id="fold_l1", name="Level 1", parent_id="fold_root")
        level2 = ProjectFolder(id="fold_l2", name="Level 2", parent_id="fold_l1")

        folders_file = FoldersFile(
            folders={
                "fold_root": root,
                "fold_l1": level1,
                "fold_l2": level2,
            }
        )

        path = folders_file.get_folder_path("fold_l2")

        assert path == ["fold_root", "fold_l1", "fold_l2"]

    def test_move_project_between_folders(self):
        """move_project() moves project between folders."""
        from_folder = ProjectFolder(
            id="fold_from", name="From", project_ids=["proj_001"]
        )
        to_folder = ProjectFolder(id="fold_to", name="To", project_ids=[])

        folders_file = FoldersFile(
            folders={"fold_from": from_folder, "fold_to": to_folder}
        )

        result = folders_file.move_project("proj_001", "fold_from", "fold_to")

        assert result is True
        assert "proj_001" not in folders_file.folders["fold_from"].project_ids
        assert "proj_001" in folders_file.folders["fold_to"].project_ids

    def test_folders_file_serialization_round_trip(self):
        """FoldersFile serializes and deserializes correctly."""
        folder1 = ProjectFolder(id="fold_1", name="Folder 1")
        folder2 = ProjectFolder(id="fold_2", name="Folder 2", parent_id="fold_1")

        original = FoldersFile(
            folders={"fold_1": folder1, "fold_2": folder2},
            schema_version="2.0.0",
        )

        data = original.to_dict()
        restored = FoldersFile.from_dict(data)

        assert "fold_1" in restored.folders
        assert "fold_2" in restored.folders
        assert restored.folders["fold_2"].parent_id == "fold_1"
        assert restored.schema_version == "2.0.0"


class TestFolderColor:
    """Tests for FolderColor enum."""

    def test_all_colors_are_hex(self):
        """All FolderColor values are valid hex colors."""
        for color in FolderColor:
            assert color.value.startswith("#")
            assert len(color.value) == 7  # #RRGGBB format

    def test_expected_colors_exist(self):
        """Expected standard colors exist."""
        assert FolderColor.BLUE.value == "#2196F3"
        assert FolderColor.GREEN.value == "#4CAF50"
        assert FolderColor.ORANGE.value == "#FF9800"
        assert FolderColor.RED.value == "#F44336"
        assert FolderColor.PURPLE.value == "#9C27B0"
