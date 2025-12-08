"""
Tests for ProjectTemplate domain entity.

Tests cover:
- Template creation and initialization
- Template variables and credentials
- Serialization/deserialization round-trip
- Template file container
"""

import pytest
from datetime import datetime

from casare_rpa.domain.entities.project.template import (
    ProjectTemplate,
    TemplateVariable,
    TemplateCredential,
    TemplatesFile,
    TemplateCategory,
    TemplateDifficulty,
    generate_template_id,
)
from casare_rpa.domain.entities.project.settings import ProjectSettings


class TestTemplateCreation:
    """Tests for ProjectTemplate entity creation."""

    def test_create_template_with_required_fields(self):
        """Template can be created with minimal required fields."""
        template = ProjectTemplate(id="tmpl_test1", name="Test Template")

        assert template.id == "tmpl_test1"
        assert template.name == "Test Template"
        assert template.description == ""
        assert template.category == TemplateCategory.CUSTOM
        assert template.difficulty == TemplateDifficulty.BEGINNER
        assert template.default_variables == []
        assert template.default_credentials == []
        assert template.is_builtin is False
        assert template.is_public is True

    def test_create_template_with_all_fields(self):
        """Template can be created with all fields."""
        template = ProjectTemplate(
            id="tmpl_webscrape",
            name="Web Scraping Starter",
            description="Basic web scraping template",
            category=TemplateCategory.WEB_SCRAPING,
            icon="web",
            color="#2196F3",
            tags=["web", "scraping", "beginner"],
            base_workflow={"nodes": [], "connections": []},
            default_variables=[
                TemplateVariable(name="target_url", data_type="String", required=True)
            ],
            default_credentials=[
                TemplateCredential(alias="api_key", credential_type="api_key")
            ],
            default_settings=ProjectSettings(default_browser="chromium"),
            version="1.0.0",
            author="CasareRPA",
            difficulty=TemplateDifficulty.BEGINNER,
            estimated_nodes=8,
            is_builtin=True,
            is_public=True,
        )

        assert template.id == "tmpl_webscrape"
        assert template.category == TemplateCategory.WEB_SCRAPING
        assert template.difficulty == TemplateDifficulty.BEGINNER
        assert len(template.default_variables) == 1
        assert len(template.default_credentials) == 1
        assert template.is_builtin is True
        assert template.estimated_nodes == 8
        assert "web" in template.tags

    def test_timestamps_auto_initialized(self):
        """Created and modified timestamps are auto-initialized."""
        before = datetime.now()
        template = ProjectTemplate(id="tmpl_test", name="Test")
        after = datetime.now()

        assert template.created_at is not None
        assert template.modified_at is not None
        assert before <= template.created_at <= after

    def test_generate_template_id_format(self):
        """Generated ID has correct format."""
        tmpl_id = generate_template_id()

        assert tmpl_id.startswith("tmpl_")
        assert len(tmpl_id) == 13  # tmpl_ + 8 hex chars

    def test_create_new_factory_method(self):
        """create_new() factory generates ID and sets fields."""
        template = ProjectTemplate.create_new(
            name="New Template",
            category=TemplateCategory.DATA_ETL,
            author="Test Author",
        )

        assert template.id.startswith("tmpl_")
        assert template.name == "New Template"
        assert template.category == TemplateCategory.DATA_ETL
        assert template.author == "Test Author"


class TestTemplateCategory:
    """Tests for TemplateCategory enum."""

    def test_all_expected_categories_exist(self):
        """All expected template categories exist."""
        expected = [
            "Web Scraping",
            "Google Workspace",
            "Desktop Automation",
            "Data ETL",
            "Email & Documents",
            "API & Webhooks",
            "Notifications",
            "Office Automation",
            "Custom",
        ]

        category_values = [c.value for c in TemplateCategory]

        for expected_cat in expected:
            assert expected_cat in category_values, f"Missing category: {expected_cat}"


class TestTemplateDifficulty:
    """Tests for TemplateDifficulty enum."""

    def test_all_expected_difficulties_exist(self):
        """All expected difficulty levels exist."""
        assert TemplateDifficulty.BEGINNER.value == "beginner"
        assert TemplateDifficulty.INTERMEDIATE.value == "intermediate"
        assert TemplateDifficulty.ADVANCED.value == "advanced"


class TestTemplateVariable:
    """Tests for TemplateVariable value object."""

    def test_create_variable_with_defaults(self):
        """Variable can be created with defaults."""
        var = TemplateVariable(name="test_var")

        assert var.name == "test_var"
        assert var.data_type == "String"
        assert var.default_value == ""
        assert var.description == ""
        assert var.required is False

    def test_create_variable_with_all_fields(self):
        """Variable can be created with all fields."""
        var = TemplateVariable(
            name="api_url",
            data_type="String",
            default_value="https://api.example.com",
            description="API endpoint URL",
            required=True,
        )

        assert var.name == "api_url"
        assert var.data_type == "String"
        assert var.default_value == "https://api.example.com"
        assert var.description == "API endpoint URL"
        assert var.required is True

    def test_variable_serialization_round_trip(self):
        """Variable serializes and deserializes correctly."""
        original = TemplateVariable(
            name="count",
            data_type="Integer",
            default_value=10,
            description="Number of items",
            required=True,
        )

        data = original.to_dict()
        restored = TemplateVariable.from_dict(data)

        assert restored.name == original.name
        assert restored.data_type == original.data_type
        assert restored.default_value == original.default_value
        assert restored.required == original.required


class TestTemplateCredential:
    """Tests for TemplateCredential value object."""

    def test_create_credential_with_defaults(self):
        """Credential can be created with defaults."""
        cred = TemplateCredential(alias="my_cred")

        assert cred.alias == "my_cred"
        assert cred.credential_type == "username_password"
        assert cred.description == ""
        assert cred.required is False

    def test_create_credential_with_all_fields(self):
        """Credential can be created with all fields."""
        cred = TemplateCredential(
            alias="google_oauth",
            credential_type="google_oauth",
            description="Google Workspace OAuth credentials",
            required=True,
        )

        assert cred.alias == "google_oauth"
        assert cred.credential_type == "google_oauth"
        assert cred.required is True

    def test_credential_serialization_round_trip(self):
        """Credential serializes and deserializes correctly."""
        original = TemplateCredential(
            alias="api_key",
            credential_type="api_key",
            description="API authentication key",
            required=True,
        )

        data = original.to_dict()
        restored = TemplateCredential.from_dict(data)

        assert restored.alias == original.alias
        assert restored.credential_type == original.credential_type
        assert restored.required == original.required


class TestTemplateSerialization:
    """Tests for ProjectTemplate serialization/deserialization."""

    def test_to_dict_contains_all_fields(self):
        """to_dict() includes all template fields."""
        template = ProjectTemplate(
            id="tmpl_test",
            name="Test Template",
            description="Test description",
            category=TemplateCategory.DATA_ETL,
            icon="data",
            color="#FF5722",
            tags=["data", "etl"],
            base_workflow={"nodes": [{"id": "n1"}], "connections": []},
            default_variables=[TemplateVariable(name="var1")],
            default_credentials=[TemplateCredential(alias="cred1")],
            default_settings=ProjectSettings(timeout_seconds=60),
            version="2.0.0",
            author="Test Author",
            difficulty=TemplateDifficulty.INTERMEDIATE,
            estimated_nodes=15,
            is_builtin=False,
            is_public=True,
        )

        data = template.to_dict()

        assert data["id"] == "tmpl_test"
        assert data["name"] == "Test Template"
        assert data["category"] == "Data ETL"
        assert data["difficulty"] == "intermediate"
        assert data["version"] == "2.0.0"
        assert data["estimated_nodes"] == 15
        assert len(data["default_variables"]) == 1
        assert len(data["default_credentials"]) == 1
        assert data["default_settings"]["timeout_seconds"] == 60
        assert "created_at" in data
        assert "modified_at" in data

    def test_from_dict_restores_all_fields(self):
        """from_dict() restores all template fields."""
        data = {
            "id": "tmpl_restored",
            "name": "Restored Template",
            "description": "Restored description",
            "category": "Google Workspace",
            "icon": "google",
            "color": "#4285F4",
            "tags": ["google", "workspace"],
            "base_workflow": {"nodes": [], "connections": []},
            "default_variables": [
                {"name": "sheet_id", "data_type": "String", "required": True}
            ],
            "default_credentials": [
                {"alias": "google_oauth", "credential_type": "google_oauth"}
            ],
            "default_settings": {"default_browser": "chromium", "timeout_seconds": 45},
            "version": "1.5.0",
            "author": "Restored Author",
            "difficulty": "advanced",
            "estimated_nodes": 20,
            "is_builtin": True,
            "is_public": False,
            "created_at": "2025-02-01T10:00:00",
            "modified_at": "2025-02-15T16:00:00",
        }

        template = ProjectTemplate.from_dict(data)

        assert template.id == "tmpl_restored"
        assert template.name == "Restored Template"
        assert template.category == TemplateCategory.GOOGLE_WORKSPACE
        assert template.difficulty == TemplateDifficulty.ADVANCED
        assert template.is_builtin is True
        assert template.is_public is False
        assert len(template.default_variables) == 1
        assert template.default_variables[0].name == "sheet_id"
        assert template.default_settings.timeout_seconds == 45

    def test_round_trip_serialization(self):
        """Serialization -> deserialization produces equivalent object."""
        original = ProjectTemplate(
            id="tmpl_original",
            name="Original Template",
            category=TemplateCategory.API_WEBHOOKS,
            tags=["api", "webhook", "integration"],
            default_variables=[
                TemplateVariable(name="endpoint", data_type="String", required=True),
                TemplateVariable(name="timeout", data_type="Integer", default_value=30),
            ],
            default_credentials=[
                TemplateCredential(alias="api_auth", required=True),
            ],
            difficulty=TemplateDifficulty.INTERMEDIATE,
            estimated_nodes=12,
        )

        data = original.to_dict()
        restored = ProjectTemplate.from_dict(data)

        assert restored.id == original.id
        assert restored.name == original.name
        assert restored.category == original.category
        assert restored.difficulty == original.difficulty
        assert restored.tags == original.tags
        assert len(restored.default_variables) == 2
        assert len(restored.default_credentials) == 1

    def test_from_dict_handles_unknown_category(self):
        """Unknown category defaults to CUSTOM."""
        data = {
            "id": "tmpl_unknown",
            "name": "Unknown Category",
            "category": "Invalid Category",
        }

        template = ProjectTemplate.from_dict(data)

        assert template.category == TemplateCategory.CUSTOM

    def test_from_dict_handles_unknown_difficulty(self):
        """Unknown difficulty defaults to BEGINNER."""
        data = {
            "id": "tmpl_unknown",
            "name": "Unknown Difficulty",
            "difficulty": "expert",
        }

        template = ProjectTemplate.from_dict(data)

        assert template.difficulty == TemplateDifficulty.BEGINNER


class TestTemplatesFile:
    """Tests for TemplatesFile container."""

    def test_empty_templates_file(self):
        """Empty TemplatesFile has correct defaults."""
        templates_file = TemplatesFile()

        assert templates_file.templates == {}
        assert templates_file.schema_version == "2.0.0"

    def test_add_template(self):
        """add_template() adds template to collection."""
        templates_file = TemplatesFile()
        template = ProjectTemplate(id="tmpl_001", name="Template 1")

        templates_file.add_template(template)

        assert "tmpl_001" in templates_file.templates

    def test_get_template_found(self):
        """get_template() returns template when found."""
        template = ProjectTemplate(id="tmpl_001", name="Template 1")
        templates_file = TemplatesFile(templates={"tmpl_001": template})

        result = templates_file.get_template("tmpl_001")

        assert result is not None
        assert result.name == "Template 1"

    def test_get_template_not_found(self):
        """get_template() returns None when not found."""
        templates_file = TemplatesFile()

        result = templates_file.get_template("tmpl_nonexistent")

        assert result is None

    def test_remove_template(self):
        """remove_template() removes and returns True."""
        template = ProjectTemplate(id="tmpl_001", name="Template 1")
        templates_file = TemplatesFile(templates={"tmpl_001": template})

        result = templates_file.remove_template("tmpl_001")

        assert result is True
        assert "tmpl_001" not in templates_file.templates

    def test_get_by_category(self):
        """get_by_category() filters templates by category."""
        web1 = ProjectTemplate(
            id="tmpl_web1", name="Web 1", category=TemplateCategory.WEB_SCRAPING
        )
        web2 = ProjectTemplate(
            id="tmpl_web2", name="Web 2", category=TemplateCategory.WEB_SCRAPING
        )
        etl = ProjectTemplate(
            id="tmpl_etl", name="ETL", category=TemplateCategory.DATA_ETL
        )

        templates_file = TemplatesFile(
            templates={"tmpl_web1": web1, "tmpl_web2": web2, "tmpl_etl": etl}
        )

        web_templates = templates_file.get_by_category(TemplateCategory.WEB_SCRAPING)

        assert len(web_templates) == 2
        assert all(t.category == TemplateCategory.WEB_SCRAPING for t in web_templates)

    def test_get_builtin(self):
        """get_builtin() returns only built-in templates."""
        builtin = ProjectTemplate(id="tmpl_bi", name="Built-in", is_builtin=True)
        user = ProjectTemplate(id="tmpl_user", name="User", is_builtin=False)

        templates_file = TemplatesFile(
            templates={"tmpl_bi": builtin, "tmpl_user": user}
        )

        builtins = templates_file.get_builtin()

        assert len(builtins) == 1
        assert builtins[0].is_builtin is True

    def test_get_public(self):
        """get_public() returns only public templates."""
        public = ProjectTemplate(id="tmpl_pub", name="Public", is_public=True)
        private = ProjectTemplate(id="tmpl_priv", name="Private", is_public=False)

        templates_file = TemplatesFile(
            templates={"tmpl_pub": public, "tmpl_priv": private}
        )

        publics = templates_file.get_public()

        assert len(publics) == 1
        assert publics[0].is_public is True

    def test_templates_file_serialization_round_trip(self):
        """TemplatesFile serializes and deserializes correctly."""
        tmpl1 = ProjectTemplate(
            id="tmpl_1", name="Template 1", category=TemplateCategory.WEB_SCRAPING
        )
        tmpl2 = ProjectTemplate(
            id="tmpl_2", name="Template 2", category=TemplateCategory.DATA_ETL
        )

        original = TemplatesFile(
            templates={"tmpl_1": tmpl1, "tmpl_2": tmpl2},
            schema_version="2.0.0",
        )

        data = original.to_dict()
        restored = TemplatesFile.from_dict(data)

        assert "tmpl_1" in restored.templates
        assert "tmpl_2" in restored.templates
        assert restored.templates["tmpl_1"].category == TemplateCategory.WEB_SCRAPING
        assert restored.schema_version == "2.0.0"


class TestTemplateMethods:
    """Tests for ProjectTemplate instance methods."""

    def test_touch_modified_updates_timestamp(self):
        """touch_modified() updates modified_at timestamp."""
        template = ProjectTemplate(id="tmpl_test", name="Test")
        original_modified = template.modified_at

        import time

        time.sleep(0.01)
        template.touch_modified()

        assert template.modified_at > original_modified

    def test_repr_format(self):
        """__repr__ returns readable string."""
        template = ProjectTemplate(
            id="tmpl_test",
            name="Test Template",
            category=TemplateCategory.API_WEBHOOKS,
        )

        repr_str = repr(template)

        assert "tmpl_test" in repr_str
        assert "Test Template" in repr_str
        assert "API & Webhooks" in repr_str
