"""
Tests for Project domain entity and related classes.
Covers Project, Scenario, VariablesFile, CredentialBindingsFile, ProjectsIndex.
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path

from casare_rpa.domain.entities.project import (
    Project,
    Scenario,
    ProjectVariable,
    VariablesFile,
    VariableScope,
    VariableType,
    CredentialBinding,
    CredentialBindingsFile,
    ProjectSettings,
    ScenarioExecutionSettings,
    ProjectIndexEntry,
    ProjectsIndex,
    generate_project_id,
    generate_scenario_id,
    PROJECT_SCHEMA_VERSION,
)


# ============================================================================
# ID Generation Tests
# ============================================================================


class TestIdGeneration:
    """Tests for ID generation functions."""

    def test_generate_project_id_format(self) -> None:
        """Project ID has correct format."""
        pid = generate_project_id()
        assert pid.startswith("proj_")
        assert len(pid) == 13  # proj_ + 8 hex chars

    def test_generate_project_id_unique(self) -> None:
        """Generated project IDs are unique."""
        ids = {generate_project_id() for _ in range(100)}
        assert len(ids) == 100

    def test_generate_scenario_id_format(self) -> None:
        """Scenario ID has correct format."""
        sid = generate_scenario_id()
        assert sid.startswith("scen_")
        assert len(sid) == 13

    def test_generate_scenario_id_unique(self) -> None:
        """Generated scenario IDs are unique."""
        ids = {generate_scenario_id() for _ in range(100)}
        assert len(ids) == 100


# ============================================================================
# ProjectVariable Tests
# ============================================================================


class TestProjectVariable:
    """Tests for ProjectVariable dataclass."""

    def test_create_default_variable(self) -> None:
        """Create variable with defaults."""
        var = ProjectVariable(name="test")
        assert var.name == "test"
        assert var.type == "String"
        assert var.default_value == ""
        assert var.sensitive is False
        assert var.readonly is False

    def test_create_sensitive_variable(self) -> None:
        """Create sensitive variable."""
        var = ProjectVariable(
            name="password",
            type="String",
            default_value="secret123",
            sensitive=True,
        )
        assert var.sensitive is True

    def test_create_readonly_variable(self) -> None:
        """Create readonly variable."""
        var = ProjectVariable(
            name="version",
            type="String",
            default_value="1.0.0",
            readonly=True,
        )
        assert var.readonly is True

    def test_variable_to_dict(self) -> None:
        """Serialize variable to dictionary."""
        var = ProjectVariable(
            name="count",
            type="Integer",
            default_value=42,
            description="Counter",
            sensitive=False,
            readonly=True,
        )
        data = var.to_dict()
        assert data["name"] == "count"
        assert data["type"] == "Integer"
        assert data["default_value"] == 42
        assert data["readonly"] is True

    def test_variable_from_dict(self) -> None:
        """Deserialize variable from dictionary."""
        data = {
            "name": "flag",
            "type": "Boolean",
            "default_value": True,
            "sensitive": True,
        }
        var = ProjectVariable.from_dict(data)
        assert var.name == "flag"
        assert var.type == "Boolean"
        assert var.sensitive is True


# ============================================================================
# VariablesFile Tests
# ============================================================================


class TestVariablesFile:
    """Tests for VariablesFile container."""

    def test_create_empty_file(self) -> None:
        """Create empty variables file."""
        vf = VariablesFile()
        assert vf.scope == VariableScope.PROJECT
        assert len(vf.variables) == 0

    def test_create_with_scope(self) -> None:
        """Create variables file with specific scope."""
        vf = VariablesFile(scope=VariableScope.GLOBAL)
        assert vf.scope == VariableScope.GLOBAL

    def test_set_variable(self) -> None:
        """Add variable to file."""
        vf = VariablesFile()
        var = ProjectVariable(name="x", default_value=10)
        vf.set_variable(var)
        assert "x" in vf.variables

    def test_get_variable_exists(self) -> None:
        """Get existing variable."""
        vf = VariablesFile()
        vf.set_variable(ProjectVariable(name="y", default_value=20))
        var = vf.get_variable("y")
        assert var is not None
        assert var.default_value == 20

    def test_get_variable_not_exists(self) -> None:
        """Get non-existing variable returns None."""
        vf = VariablesFile()
        assert vf.get_variable("missing") is None

    def test_remove_variable_exists(self) -> None:
        """Remove existing variable returns True."""
        vf = VariablesFile()
        vf.set_variable(ProjectVariable(name="z"))
        assert vf.remove_variable("z") is True
        assert "z" not in vf.variables

    def test_remove_variable_not_exists(self) -> None:
        """Remove non-existing variable returns False."""
        vf = VariablesFile()
        assert vf.remove_variable("missing") is False

    def test_get_default_values(self) -> None:
        """Get dictionary of default values."""
        vf = VariablesFile()
        vf.set_variable(ProjectVariable(name="a", default_value=1))
        vf.set_variable(ProjectVariable(name="b", default_value="two"))
        defaults = vf.get_default_values()
        assert defaults == {"a": 1, "b": "two"}

    def test_to_dict(self) -> None:
        """Serialize variables file."""
        vf = VariablesFile(scope=VariableScope.GLOBAL)
        vf.set_variable(ProjectVariable(name="test", default_value="value"))
        data = vf.to_dict()
        assert data["scope"] == "global"
        assert "test" in data["variables"]

    def test_from_dict(self) -> None:
        """Deserialize variables file."""
        data = {
            "scope": "project",
            "variables": {"x": {"name": "x", "type": "Integer", "default_value": 42}},
        }
        vf = VariablesFile.from_dict(data)
        assert vf.scope == VariableScope.PROJECT
        assert vf.get_variable("x").default_value == 42


# ============================================================================
# CredentialBinding Tests
# ============================================================================


class TestCredentialBinding:
    """Tests for CredentialBinding dataclass."""

    def test_create_binding(self) -> None:
        """Create credential binding."""
        binding = CredentialBinding(
            alias="db_creds",
            vault_path="projects/myproj/db",
        )
        assert binding.alias == "db_creds"
        assert binding.vault_path == "projects/myproj/db"
        assert binding.required is True

    def test_binding_to_dict(self) -> None:
        """Serialize binding."""
        binding = CredentialBinding(
            alias="api",
            vault_path="secrets/api",
            credential_type="api_key",
            required=False,
        )
        data = binding.to_dict()
        assert data["alias"] == "api"
        assert data["credential_type"] == "api_key"
        assert data["required"] is False

    def test_binding_from_dict(self) -> None:
        """Deserialize binding."""
        data = {
            "alias": "ssh",
            "vault_path": "secrets/ssh_key",
            "credential_type": "ssh_key",
        }
        binding = CredentialBinding.from_dict(data)
        assert binding.alias == "ssh"


# ============================================================================
# CredentialBindingsFile Tests
# ============================================================================


class TestCredentialBindingsFile:
    """Tests for CredentialBindingsFile container."""

    def test_create_empty_file(self) -> None:
        """Create empty bindings file."""
        cbf = CredentialBindingsFile()
        assert len(cbf.bindings) == 0

    def test_set_binding(self) -> None:
        """Add binding."""
        cbf = CredentialBindingsFile()
        binding = CredentialBinding(alias="test", vault_path="path/to/cred")
        cbf.set_binding(binding)
        assert "test" in cbf.bindings

    def test_get_binding(self) -> None:
        """Get binding by alias."""
        cbf = CredentialBindingsFile()
        cbf.set_binding(CredentialBinding(alias="x", vault_path="y"))
        assert cbf.get_binding("x") is not None

    def test_remove_binding(self) -> None:
        """Remove binding."""
        cbf = CredentialBindingsFile()
        cbf.set_binding(CredentialBinding(alias="rm", vault_path="path"))
        assert cbf.remove_binding("rm") is True
        assert cbf.remove_binding("rm") is False

    def test_resolve_vault_path(self) -> None:
        """Resolve alias to vault path."""
        cbf = CredentialBindingsFile()
        cbf.set_binding(CredentialBinding(alias="db", vault_path="secrets/db"))
        assert cbf.resolve_vault_path("db") == "secrets/db"
        assert cbf.resolve_vault_path("missing") is None

    def test_to_dict(self) -> None:
        """Serialize bindings file."""
        cbf = CredentialBindingsFile()
        cbf.set_binding(CredentialBinding(alias="a", vault_path="b"))
        data = cbf.to_dict()
        assert "a" in data["bindings"]

    def test_from_dict(self) -> None:
        """Deserialize bindings file."""
        data = {"bindings": {"cred": {"alias": "cred", "vault_path": "path"}}}
        cbf = CredentialBindingsFile.from_dict(data)
        assert cbf.get_binding("cred") is not None


# ============================================================================
# ProjectSettings Tests
# ============================================================================


class TestProjectSettings:
    """Tests for ProjectSettings value object."""

    def test_default_settings(self) -> None:
        """Default project settings."""
        settings = ProjectSettings()
        assert settings.default_browser == "chromium"
        assert settings.stop_on_error is True
        assert settings.timeout_seconds == 30
        assert settings.retry_count == 0

    def test_custom_settings(self) -> None:
        """Custom project settings."""
        settings = ProjectSettings(
            default_browser="firefox",
            stop_on_error=False,
            timeout_seconds=60,
            retry_count=3,
        )
        assert settings.default_browser == "firefox"
        assert settings.retry_count == 3

    def test_settings_serialization(self) -> None:
        """Settings roundtrip serialization."""
        original = ProjectSettings(timeout_seconds=120)
        data = original.to_dict()
        restored = ProjectSettings.from_dict(data)
        assert restored.timeout_seconds == 120


# ============================================================================
# Project Tests
# ============================================================================


class TestProject:
    """Tests for Project domain entity."""

    def test_create_project(self) -> None:
        """Create project with basic info."""
        proj = Project(id="proj_123", name="Test Project")
        assert proj.id == "proj_123"
        assert proj.name == "Test Project"
        assert proj.created_at is not None
        assert proj.modified_at is not None

    def test_create_project_new(self) -> None:
        """Create new project using factory method."""
        path = Path("/projects/new")
        proj = Project.create_new(name="New Project", path=path)
        assert proj.name == "New Project"
        assert proj.id.startswith("proj_")
        assert proj.path == path

    def test_project_path_properties(self) -> None:
        """Project path-related properties."""
        proj = Project(id="p1", name="P")
        proj.path = Path("/base")
        assert proj.scenarios_dir == Path("/base/scenarios")
        assert proj.project_file == Path("/base/project.json")
        assert proj.variables_file == Path("/base/variables.json")
        assert proj.credentials_file == Path("/base/credentials.json")

    def test_project_path_properties_no_path(self) -> None:
        """Path properties return None when no path set."""
        proj = Project(id="p1", name="P")
        assert proj.scenarios_dir is None
        assert proj.project_file is None

    def test_touch_modified(self) -> None:
        """Touch updates modified timestamp."""
        proj = Project(id="p1", name="P")
        old_modified = proj.modified_at
        # Ensure some time passes
        proj.touch_modified()
        assert proj.modified_at >= old_modified

    def test_project_to_dict(self) -> None:
        """Serialize project."""
        proj = Project(
            id="proj_abc",
            name="Serializable",
            description="A test project",
            tags=["test", "demo"],
        )
        data = proj.to_dict()
        assert data["id"] == "proj_abc"
        assert data["name"] == "Serializable"
        assert "test" in data["tags"]

    def test_project_from_dict(self) -> None:
        """Deserialize project."""
        data = {
            "id": "proj_xyz",
            "name": "Loaded",
            "created_at": "2024-01-01T10:00:00",
            "modified_at": "2024-01-02T10:00:00",
        }
        proj = Project.from_dict(data)
        assert proj.id == "proj_xyz"
        assert proj.created_at.year == 2024

    def test_project_repr(self) -> None:
        """String representation."""
        proj = Project(id="proj_test", name="Demo")
        rep = repr(proj)
        assert "proj_test" in rep
        assert "Demo" in rep


# ============================================================================
# ScenarioExecutionSettings Tests
# ============================================================================


class TestScenarioExecutionSettings:
    """Tests for ScenarioExecutionSettings."""

    def test_default_settings(self) -> None:
        """Default scenario execution settings."""
        settings = ScenarioExecutionSettings()
        assert settings.priority == "normal"
        assert settings.timeout_override is None

    def test_custom_settings(self) -> None:
        """Custom scenario execution settings."""
        settings = ScenarioExecutionSettings(
            priority="high",
            timeout_override=120,
            environment_override="production",
        )
        assert settings.priority == "high"
        assert settings.timeout_override == 120

    def test_settings_serialization(self) -> None:
        """Settings roundtrip."""
        original = ScenarioExecutionSettings(priority="critical")
        data = original.to_dict()
        restored = ScenarioExecutionSettings.from_dict(data)
        assert restored.priority == "critical"


# ============================================================================
# Scenario Tests
# ============================================================================


class TestScenario:
    """Tests for Scenario domain entity."""

    def test_create_scenario(self) -> None:
        """Create scenario with basic info."""
        scen = Scenario(
            id="scen_123",
            name="Login Test",
            project_id="proj_abc",
        )
        assert scen.id == "scen_123"
        assert scen.name == "Login Test"
        assert scen.project_id == "proj_abc"

    def test_create_scenario_new(self) -> None:
        """Create new scenario using factory method."""
        workflow = {"nodes": {}, "connections": []}
        scen = Scenario.create_new(
            name="New Scenario",
            project_id="proj_xyz",
            workflow=workflow,
        )
        assert scen.id.startswith("scen_")
        assert scen.workflow == workflow

    def test_scenario_variable_values(self) -> None:
        """Get and set variable values."""
        scen = Scenario(id="s1", name="S", project_id="p1")
        scen.set_variable_value("x", 42)
        assert scen.get_variable_value("x") == 42
        assert scen.get_variable_value("missing", "default") == "default"

    def test_touch_modified(self) -> None:
        """Touch updates modified timestamp."""
        scen = Scenario(id="s1", name="S", project_id="p1")
        old = scen.modified_at
        scen.touch_modified()
        assert scen.modified_at >= old

    def test_scenario_to_dict(self) -> None:
        """Serialize scenario."""
        scen = Scenario(
            id="scen_x",
            name="Test Scenario",
            project_id="proj_y",
            variable_values={"a": 1},
            triggers=[{"type": "manual"}],
        )
        data = scen.to_dict()
        assert data["id"] == "scen_x"
        assert data["variable_values"]["a"] == 1
        assert len(data["triggers"]) == 1

    def test_scenario_from_dict(self) -> None:
        """Deserialize scenario."""
        data = {
            "id": "scen_loaded",
            "name": "Loaded",
            "project_id": "proj_x",
            "workflow": {"nodes": {}},
            "created_at": "2024-06-01T12:00:00",
        }
        scen = Scenario.from_dict(data)
        assert scen.id == "scen_loaded"
        assert scen.workflow == {"nodes": {}}

    def test_scenario_repr(self) -> None:
        """String representation."""
        scen = Scenario(id="scen_abc", name="Demo", project_id="proj_xyz")
        rep = repr(scen)
        assert "scen_abc" in rep
        assert "Demo" in rep


# ============================================================================
# ProjectIndexEntry Tests
# ============================================================================


class TestProjectIndexEntry:
    """Tests for ProjectIndexEntry."""

    def test_create_entry(self) -> None:
        """Create index entry."""
        entry = ProjectIndexEntry(
            id="proj_1",
            name="Project One",
            path="/path/to/project",
        )
        assert entry.id == "proj_1"
        assert entry.last_opened is None

    def test_entry_serialization(self) -> None:
        """Entry roundtrip serialization."""
        original = ProjectIndexEntry(
            id="proj_2",
            name="Two",
            path="/two",
            last_opened=datetime(2024, 1, 1, 10, 0, 0),
        )
        data = original.to_dict()
        restored = ProjectIndexEntry.from_dict(data)
        assert restored.id == "proj_2"
        assert restored.last_opened.year == 2024


# ============================================================================
# ProjectsIndex Tests
# ============================================================================


class TestProjectsIndex:
    """Tests for ProjectsIndex."""

    def test_create_empty_index(self) -> None:
        """Create empty projects index."""
        idx = ProjectsIndex()
        assert len(idx.projects) == 0
        assert idx.recent_limit == 10

    def test_add_project(self) -> None:
        """Add project to index."""
        idx = ProjectsIndex()
        proj = Project(id="proj_new", name="New")
        proj.path = Path("/new")
        idx.add_project(proj)
        assert len(idx.projects) == 1
        assert idx.projects[0].id == "proj_new"

    def test_add_project_updates_existing(self) -> None:
        """Adding existing project updates and moves to front."""
        idx = ProjectsIndex()
        proj1 = Project(id="proj_1", name="First")
        proj1.path = Path("/first")
        proj2 = Project(id="proj_2", name="Second")
        proj2.path = Path("/second")

        idx.add_project(proj1)
        idx.add_project(proj2)
        idx.add_project(proj1)  # Re-add first

        assert len(idx.projects) == 2
        assert idx.projects[0].id == "proj_1"

    def test_add_project_trims_to_limit(self) -> None:
        """Index trims to recent_limit."""
        idx = ProjectsIndex(recent_limit=3)
        for i in range(5):
            proj = Project(id=f"proj_{i}", name=f"P{i}")
            proj.path = Path(f"/{i}")
            idx.add_project(proj)
        assert len(idx.projects) == 3

    def test_remove_project(self) -> None:
        """Remove project from index."""
        idx = ProjectsIndex()
        proj = Project(id="proj_rm", name="Remove")
        proj.path = Path("/rm")
        idx.add_project(proj)
        assert idx.remove_project("proj_rm") is True
        assert len(idx.projects) == 0

    def test_remove_project_not_exists(self) -> None:
        """Remove non-existent project returns False."""
        idx = ProjectsIndex()
        assert idx.remove_project("missing") is False

    def test_get_project(self) -> None:
        """Get project entry by ID."""
        idx = ProjectsIndex()
        proj = Project(id="proj_get", name="Get")
        proj.path = Path("/get")
        idx.add_project(proj)
        entry = idx.get_project("proj_get")
        assert entry is not None
        assert entry.name == "Get"

    def test_get_project_not_exists(self) -> None:
        """Get non-existent project returns None."""
        idx = ProjectsIndex()
        assert idx.get_project("missing") is None

    def test_get_recent_projects(self) -> None:
        """Get recent projects with limit."""
        idx = ProjectsIndex()
        for i in range(5):
            proj = Project(id=f"proj_{i}", name=f"P{i}")
            proj.path = Path(f"/{i}")
            idx.add_project(proj)

        recent = idx.get_recent_projects(limit=3)
        assert len(recent) == 3

    def test_update_last_opened(self) -> None:
        """Update last_opened moves project to front."""
        idx = ProjectsIndex()
        for i in range(3):
            proj = Project(id=f"proj_{i}", name=f"P{i}")
            proj.path = Path(f"/{i}")
            idx.add_project(proj)

        idx.update_last_opened("proj_0")  # Oldest, now becomes newest
        assert idx.projects[0].id == "proj_0"

    def test_index_serialization(self) -> None:
        """Index roundtrip serialization."""
        idx = ProjectsIndex()
        proj = Project(id="proj_ser", name="Serialize")
        proj.path = Path("/ser")
        idx.add_project(proj)

        data = idx.to_dict()
        restored = ProjectsIndex.from_dict(data)
        assert len(restored.projects) == 1
        assert restored.projects[0].id == "proj_ser"
