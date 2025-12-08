"""
Tests for Project entity v2.0.0 fields.

Tests cover:
- Project creation with v2.0.0 fields (folder_id, template_id, environments)
- Backward compatibility with v1.0.0 projects
- Serialization/deserialization of new fields
"""

import pytest
from datetime import datetime
from pathlib import Path

from casare_rpa.domain.entities.project.project import Project
from casare_rpa.domain.entities.project.settings import ProjectSettings
from casare_rpa.domain.entities.project.base import (
    PROJECT_SCHEMA_VERSION,
    generate_project_id,
)


class TestProjectV2Creation:
    """Tests for Project entity with v2.0.0 fields."""

    def test_create_project_with_v2_fields(self):
        """Project can be created with v2.0.0 fields."""
        project = Project(
            id="proj_test001",
            name="Test Project",
            description="Test description",
            author="Test Author",
            folder_id="fold_parent",
            template_id="tmpl_webscrape",
            environment_ids=["env_dev", "env_staging", "env_prod"],
            active_environment_id="env_dev",
        )

        assert project.id == "proj_test001"
        assert project.folder_id == "fold_parent"
        assert project.template_id == "tmpl_webscrape"
        assert project.environment_ids == ["env_dev", "env_staging", "env_prod"]
        assert project.active_environment_id == "env_dev"
        assert project.schema_version == PROJECT_SCHEMA_VERSION

    def test_v2_fields_default_to_none_or_empty(self):
        """v2.0.0 fields have appropriate defaults."""
        project = Project(id="proj_minimal", name="Minimal Project")

        assert project.folder_id is None
        assert project.template_id is None
        assert project.environment_ids == []
        assert project.active_environment_id is None

    def test_schema_version_is_2_0_0(self):
        """Project uses schema version 2.0.0."""
        assert PROJECT_SCHEMA_VERSION == "2.0.0"

        project = Project(id="proj_test", name="Test")

        assert project.schema_version == "2.0.0"


class TestProjectSerialization:
    """Tests for Project serialization with v2.0.0 fields."""

    def test_to_dict_includes_v2_fields(self):
        """to_dict() includes all v2.0.0 fields."""
        project = Project(
            id="proj_full",
            name="Full Project",
            description="Full description",
            author="Full Author",
            tags=["tag1", "tag2"],
            settings=ProjectSettings(default_browser="firefox"),
            folder_id="fold_main",
            template_id="tmpl_custom",
            environment_ids=["env_1", "env_2"],
            active_environment_id="env_1",
        )

        data = project.to_dict()

        # Check standard fields
        assert data["$schema_version"] == "2.0.0"
        assert data["id"] == "proj_full"
        assert data["name"] == "Full Project"
        assert data["description"] == "Full description"
        assert data["author"] == "Full Author"
        assert data["tags"] == ["tag1", "tag2"]
        assert data["settings"]["default_browser"] == "firefox"

        # Check v2.0.0 fields
        assert data["folder_id"] == "fold_main"
        assert data["template_id"] == "tmpl_custom"
        assert data["environment_ids"] == ["env_1", "env_2"]
        assert data["active_environment_id"] == "env_1"

    def test_from_dict_restores_v2_fields(self):
        """from_dict() restores v2.0.0 fields."""
        data = {
            "$schema_version": "2.0.0",
            "id": "proj_restored",
            "name": "Restored Project",
            "folder_id": "fold_restored",
            "template_id": "tmpl_restored",
            "environment_ids": ["env_a", "env_b", "env_c"],
            "active_environment_id": "env_b",
        }

        project = Project.from_dict(data)

        assert project.folder_id == "fold_restored"
        assert project.template_id == "tmpl_restored"
        assert project.environment_ids == ["env_a", "env_b", "env_c"]
        assert project.active_environment_id == "env_b"

    def test_round_trip_serialization_v2(self):
        """Serialization -> deserialization preserves v2.0.0 fields."""
        original = Project(
            id="proj_original",
            name="Original Project",
            folder_id="fold_org",
            template_id="tmpl_org",
            environment_ids=["env_x", "env_y"],
            active_environment_id="env_x",
        )

        data = original.to_dict()
        restored = Project.from_dict(data)

        assert restored.id == original.id
        assert restored.folder_id == original.folder_id
        assert restored.template_id == original.template_id
        assert restored.environment_ids == original.environment_ids
        assert restored.active_environment_id == original.active_environment_id


class TestV1ToV2Migration:
    """Tests for backward compatibility with v1.0.0 projects."""

    def test_from_dict_handles_missing_v2_fields(self):
        """from_dict() handles v1.0.0 projects without v2 fields."""
        v1_data = {
            "id": "proj_v1",
            "name": "V1 Project",
            "description": "Created with v1.0.0",
            "author": "V1 Author",
            "tags": ["legacy"],
            "settings": {
                "default_browser": "chromium",
                "stop_on_error": True,
            },
            # No folder_id, template_id, environment_ids, active_environment_id
        }

        project = Project.from_dict(v1_data)

        # Standard fields restored
        assert project.id == "proj_v1"
        assert project.name == "V1 Project"
        assert project.tags == ["legacy"]

        # v2.0.0 fields get defaults
        assert project.folder_id is None
        assert project.template_id is None
        assert project.environment_ids == []
        assert project.active_environment_id is None

    def test_from_dict_handles_v1_schema_version(self):
        """from_dict() handles v1.0.0 schema version."""
        v1_data = {
            "$schema_version": "1.0.0",
            "id": "proj_v1_explicit",
            "name": "Explicit V1 Project",
        }

        project = Project.from_dict(v1_data)

        # Schema version is preserved from data
        assert project.schema_version == "1.0.0"


class TestProjectPathProperties:
    """Tests for Project path-related properties."""

    def test_path_property(self):
        """path property can be get and set."""
        project = Project(id="proj_test", name="Test")
        test_path = Path("c:/test/project")

        project.path = test_path

        assert project.path == test_path

    def test_scenarios_dir_property(self):
        """scenarios_dir returns path to scenarios directory."""
        project = Project(id="proj_test", name="Test")
        project.path = Path("c:/test/project")

        assert project.scenarios_dir == Path("c:/test/project/scenarios")

    def test_project_file_property(self):
        """project_file returns path to project.json."""
        project = Project(id="proj_test", name="Test")
        project.path = Path("c:/test/project")

        assert project.project_file == Path("c:/test/project/project.json")

    def test_variables_file_property(self):
        """variables_file returns path to variables.json."""
        project = Project(id="proj_test", name="Test")
        project.path = Path("c:/test/project")

        assert project.variables_file == Path("c:/test/project/variables.json")

    def test_credentials_file_property(self):
        """credentials_file returns path to credentials.json."""
        project = Project(id="proj_test", name="Test")
        project.path = Path("c:/test/project")

        assert project.credentials_file == Path("c:/test/project/credentials.json")

    def test_environments_dir_property(self):
        """environments_dir returns path to environments directory (v2.0.0)."""
        project = Project(id="proj_test", name="Test")
        project.path = Path("c:/test/project")

        assert project.environments_dir == Path("c:/test/project/environments")

    def test_path_properties_none_when_path_not_set(self):
        """Path properties return None when path not set."""
        project = Project(id="proj_test", name="Test")

        assert project.path is None
        assert project.scenarios_dir is None
        assert project.project_file is None
        assert project.environments_dir is None


class TestProjectFactoryMethods:
    """Tests for Project factory methods."""

    def test_create_new_generates_id(self):
        """create_new() generates project ID and sets path."""
        path = Path("c:/test/new_project")

        project = Project.create_new(name="New Project", path=path)

        assert project.id.startswith("proj_")
        assert project.name == "New Project"
        assert project.path == path

    def test_create_new_with_additional_kwargs(self):
        """create_new() accepts additional kwargs."""
        path = Path("c:/test/project")

        project = Project.create_new(
            name="Kwarg Project",
            path=path,
            author="Kwarg Author",
            description="Created with kwargs",
            folder_id="fold_kwarg",
            template_id="tmpl_kwarg",
        )

        assert project.name == "Kwarg Project"
        assert project.author == "Kwarg Author"
        assert project.description == "Created with kwargs"
        assert project.folder_id == "fold_kwarg"
        assert project.template_id == "tmpl_kwarg"


class TestProjectMethods:
    """Tests for Project instance methods."""

    def test_touch_modified_updates_timestamp(self):
        """touch_modified() updates modified_at timestamp."""
        project = Project(id="proj_test", name="Test")
        original_modified = project.modified_at

        import time

        time.sleep(0.01)
        project.touch_modified()

        assert project.modified_at > original_modified

    def test_repr_format(self):
        """__repr__ returns readable string."""
        project = Project(id="proj_test", name="Test Project")

        repr_str = repr(project)

        assert "proj_test" in repr_str
        assert "Test Project" in repr_str


class TestProjectIdGeneration:
    """Tests for project ID generation."""

    def test_generate_project_id_format(self):
        """Generated ID has correct format."""
        proj_id = generate_project_id()

        assert proj_id.startswith("proj_")
        assert len(proj_id) == 13  # proj_ + 8 hex chars

    def test_generate_project_id_unique(self):
        """Generated IDs are unique."""
        ids = [generate_project_id() for _ in range(100)]

        assert len(ids) == len(set(ids))
