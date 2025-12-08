"""
Tests for Environment domain entity.

Tests cover:
- Environment creation and initialization
- Variable inheritance
- Serialization/deserialization round-trip
- Default environment creation
"""

import pytest
from datetime import datetime

from casare_rpa.domain.entities.project.environment import (
    Environment,
    EnvironmentSettings,
    EnvironmentType,
    ENVIRONMENT_INHERITANCE,
    generate_environment_id,
)


class TestEnvironmentCreation:
    """Tests for Environment entity creation."""

    def test_create_environment_with_required_fields(self):
        """Environment can be created with minimal required fields."""
        env = Environment(id="env_test1", name="Test Environment")

        assert env.id == "env_test1"
        assert env.name == "Test Environment"
        assert env.env_type == EnvironmentType.DEVELOPMENT
        assert env.description == ""
        assert env.variables == {}
        assert env.is_default is False

    def test_create_environment_with_all_fields(self):
        """Environment can be created with all fields."""
        env = Environment(
            id="env_staging",
            name="Staging",
            env_type=EnvironmentType.STAGING,
            description="Staging environment",
            variables={"API_URL": "https://staging.api.com"},
            credential_overrides={"db": "cred_staging_db"},
            settings=EnvironmentSettings(timeout_override=60000),
            is_default=False,
            color="#FF9800",
            icon="cloud",
        )

        assert env.id == "env_staging"
        assert env.env_type == EnvironmentType.STAGING
        assert env.variables["API_URL"] == "https://staging.api.com"
        assert env.credential_overrides["db"] == "cred_staging_db"
        assert env.settings.timeout_override == 60000
        assert env.color == "#FF9800"
        assert env.icon == "cloud"

    def test_timestamps_auto_initialized(self):
        """Created and modified timestamps are auto-initialized."""
        before = datetime.now()
        env = Environment(id="env_test", name="Test")
        after = datetime.now()

        assert env.created_at is not None
        assert env.modified_at is not None
        assert before <= env.created_at <= after
        assert before <= env.modified_at <= after

    def test_default_color_by_type(self):
        """Default color is set based on environment type."""
        dev = Environment(
            id="env_dev", name="Dev", env_type=EnvironmentType.DEVELOPMENT
        )
        staging = Environment(
            id="env_stg", name="Staging", env_type=EnvironmentType.STAGING
        )
        prod = Environment(
            id="env_prd", name="Prod", env_type=EnvironmentType.PRODUCTION
        )
        custom = Environment(
            id="env_cust", name="Custom", env_type=EnvironmentType.CUSTOM
        )

        assert dev.color == "#4CAF50"  # Green
        assert staging.color == "#FF9800"  # Orange
        assert prod.color == "#F44336"  # Red
        assert custom.color == "#9C27B0"  # Purple

    def test_generate_environment_id_format(self):
        """Generated ID has correct format."""
        env_id = generate_environment_id()

        assert env_id.startswith("env_")
        assert len(env_id) == 12  # env_ + 8 hex chars


class TestEnvironmentInheritance:
    """Tests for environment variable inheritance."""

    def test_inheritance_chain_defined(self):
        """Inheritance chain: staging -> dev, prod -> staging."""
        assert (
            ENVIRONMENT_INHERITANCE[EnvironmentType.STAGING]
            == EnvironmentType.DEVELOPMENT
        )
        assert (
            ENVIRONMENT_INHERITANCE[EnvironmentType.PRODUCTION]
            == EnvironmentType.STAGING
        )

    def test_get_parent_type_staging(self):
        """Staging environment's parent is development."""
        env = Environment(
            id="env_stg", name="Staging", env_type=EnvironmentType.STAGING
        )

        parent_type = env.get_parent_type()

        assert parent_type == EnvironmentType.DEVELOPMENT

    def test_get_parent_type_production(self):
        """Production environment's parent is staging."""
        env = Environment(
            id="env_prd", name="Prod", env_type=EnvironmentType.PRODUCTION
        )

        parent_type = env.get_parent_type()

        assert parent_type == EnvironmentType.STAGING

    def test_get_parent_type_development_has_no_parent(self):
        """Development environment has no parent."""
        env = Environment(
            id="env_dev", name="Dev", env_type=EnvironmentType.DEVELOPMENT
        )

        parent_type = env.get_parent_type()

        assert parent_type is None

    def test_resolve_variables_without_parent(self):
        """Variables resolve to own variables without parent."""
        env = Environment(
            id="env_dev",
            name="Dev",
            env_type=EnvironmentType.DEVELOPMENT,
            variables={"API_URL": "http://localhost:3000", "DEBUG": True},
        )

        resolved = env.resolve_variables()

        assert resolved == {"API_URL": "http://localhost:3000", "DEBUG": True}

    def test_resolve_variables_with_parent_inheritance(self):
        """Child variables override parent variables."""
        parent_vars = {"API_URL": "http://localhost:3000", "DEBUG": True, "TIMEOUT": 30}
        env = Environment(
            id="env_stg",
            name="Staging",
            env_type=EnvironmentType.STAGING,
            variables={"API_URL": "https://staging.api.com", "ENVIRONMENT": "staging"},
        )

        resolved = env.resolve_variables(parent_vars)

        # API_URL overridden, DEBUG and TIMEOUT inherited, ENVIRONMENT added
        assert resolved["API_URL"] == "https://staging.api.com"
        assert resolved["DEBUG"] is True
        assert resolved["TIMEOUT"] == 30
        assert resolved["ENVIRONMENT"] == "staging"


class TestEnvironmentSerialization:
    """Tests for Environment serialization/deserialization."""

    def test_to_dict_contains_all_fields(self):
        """to_dict() includes all environment fields."""
        env = Environment(
            id="env_test",
            name="Test",
            env_type=EnvironmentType.STAGING,
            description="Test env",
            variables={"KEY": "value"},
            credential_overrides={"alias": "cred_id"},
            settings=EnvironmentSettings(timeout_override=5000),
            is_default=True,
            color="#123456",
            icon="custom",
        )

        data = env.to_dict()

        assert data["id"] == "env_test"
        assert data["name"] == "Test"
        assert data["env_type"] == "staging"
        assert data["description"] == "Test env"
        assert data["variables"] == {"KEY": "value"}
        assert data["credential_overrides"] == {"alias": "cred_id"}
        assert data["settings"]["timeout_override"] == 5000
        assert data["is_default"] is True
        assert data["color"] == "#123456"
        assert data["icon"] == "custom"
        assert "created_at" in data
        assert "modified_at" in data

    def test_from_dict_restores_all_fields(self):
        """from_dict() restores all environment fields."""
        data = {
            "id": "env_prod",
            "name": "Production",
            "env_type": "production",
            "description": "Live environment",
            "variables": {"API_URL": "https://api.prod.com"},
            "credential_overrides": {"db": "cred_prod_db"},
            "settings": {
                "api_base_urls": {"api": "https://api.prod.com"},
                "timeout_override": 120000,
                "retry_count_override": 3,
            },
            "is_default": False,
            "color": "#F44336",
            "icon": "production",
            "created_at": "2025-01-01T10:00:00",
            "modified_at": "2025-01-02T15:30:00",
        }

        env = Environment.from_dict(data)

        assert env.id == "env_prod"
        assert env.name == "Production"
        assert env.env_type == EnvironmentType.PRODUCTION
        assert env.description == "Live environment"
        assert env.variables["API_URL"] == "https://api.prod.com"
        assert env.credential_overrides["db"] == "cred_prod_db"
        assert env.settings.timeout_override == 120000
        assert env.settings.retry_count_override == 3
        assert env.is_default is False
        assert env.created_at.year == 2025

    def test_round_trip_serialization(self):
        """Serialization -> deserialization produces equivalent object."""
        original = Environment(
            id="env_original",
            name="Original",
            env_type=EnvironmentType.STAGING,
            variables={"KEY1": "value1", "KEY2": 42},
            settings=EnvironmentSettings(
                feature_flags={"beta": True},
                headless_browser=True,
            ),
        )

        data = original.to_dict()
        restored = Environment.from_dict(data)

        assert restored.id == original.id
        assert restored.name == original.name
        assert restored.env_type == original.env_type
        assert restored.variables == original.variables
        assert restored.settings.feature_flags == original.settings.feature_flags
        assert restored.settings.headless_browser == original.settings.headless_browser

    def test_from_dict_handles_unknown_env_type(self):
        """Unknown env_type defaults to CUSTOM."""
        data = {
            "id": "env_unknown",
            "name": "Unknown",
            "env_type": "invalid_type",
        }

        env = Environment.from_dict(data)

        assert env.env_type == EnvironmentType.CUSTOM


class TestDefaultEnvironments:
    """Tests for default environment creation."""

    def test_create_default_environments_returns_three(self):
        """create_default_environments() returns dev, staging, prod."""
        environments = Environment.create_default_environments()

        assert len(environments) == 3

    def test_create_default_environments_types(self):
        """Default environments have correct types."""
        environments = Environment.create_default_environments()
        types = {env.env_type for env in environments}

        assert EnvironmentType.DEVELOPMENT in types
        assert EnvironmentType.STAGING in types
        assert EnvironmentType.PRODUCTION in types

    def test_create_default_environments_one_is_default(self):
        """Exactly one default environment is marked as default."""
        environments = Environment.create_default_environments()
        defaults = [env for env in environments if env.is_default]

        assert len(defaults) == 1
        assert defaults[0].env_type == EnvironmentType.DEVELOPMENT

    def test_create_default_environments_unique_ids(self):
        """Each default environment has unique ID."""
        environments = Environment.create_default_environments()
        ids = [env.id for env in environments]

        assert len(ids) == len(set(ids))


class TestEnvironmentSettings:
    """Tests for EnvironmentSettings value object."""

    def test_default_settings(self):
        """Default settings have expected values."""
        settings = EnvironmentSettings()

        assert settings.api_base_urls == {}
        assert settings.timeout_override is None
        assert settings.retry_count_override is None
        assert settings.feature_flags == {}
        assert settings.headless_browser is None

    def test_settings_serialization(self):
        """Settings serialize and deserialize correctly."""
        settings = EnvironmentSettings(
            api_base_urls={"main": "https://api.example.com"},
            timeout_override=30000,
            retry_count_override=5,
            feature_flags={"dark_mode": True, "beta": False},
            headless_browser=True,
        )

        data = settings.to_dict()
        restored = EnvironmentSettings.from_dict(data)

        assert restored.api_base_urls == settings.api_base_urls
        assert restored.timeout_override == settings.timeout_override
        assert restored.retry_count_override == settings.retry_count_override
        assert restored.feature_flags == settings.feature_flags
        assert restored.headless_browser == settings.headless_browser


class TestEnvironmentMethods:
    """Tests for Environment instance methods."""

    def test_touch_modified_updates_timestamp(self):
        """touch_modified() updates modified_at timestamp."""
        env = Environment(id="env_test", name="Test")
        original_modified = env.modified_at

        # Small delay to ensure different timestamp
        import time

        time.sleep(0.01)
        env.touch_modified()

        assert env.modified_at > original_modified

    def test_repr_format(self):
        """__repr__ returns readable string."""
        env = Environment(
            id="env_test",
            name="Test Env",
            env_type=EnvironmentType.STAGING,
        )

        repr_str = repr(env)

        assert "env_test" in repr_str
        assert "Test Env" in repr_str
        assert "staging" in repr_str
