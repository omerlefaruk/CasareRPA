"""
Tests for ProjectContext domain service.
Covers variable resolution, scope hierarchy, credential resolution.
"""

import pytest
from typing import Optional

from casare_rpa.domain.services.project_context import ProjectContext
from casare_rpa.domain.entities.project import (
    Project,
    Scenario,
    ProjectVariable,
    VariablesFile,
    VariableScope,
    CredentialBinding,
    CredentialBindingsFile,
    ProjectSettings,
    ScenarioExecutionSettings,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def project() -> Project:
    """Create test project."""
    return Project(
        id="proj_test",
        name="Test Project",
        settings=ProjectSettings(
            default_browser="chromium",
            stop_on_error=True,
            timeout_seconds=30,
            retry_count=2,
        ),
    )


@pytest.fixture
def scenario() -> Scenario:
    """Create test scenario."""
    return Scenario(
        id="scen_test",
        name="Test Scenario",
        project_id="proj_test",
        variable_values={
            "scenario_var": "scenario_value",
            "override_var": "from_scenario",
        },
        credential_bindings={"db_cred": "vault/scenario/db"},
        execution_settings=ScenarioExecutionSettings(
            priority="high",
            timeout_override=60,
        ),
    )


@pytest.fixture
def project_variables() -> VariablesFile:
    """Create project variables file."""
    vf = VariablesFile(scope=VariableScope.PROJECT)
    vf.set_variable(ProjectVariable(name="project_var", default_value="project_value"))
    vf.set_variable(ProjectVariable(name="override_var", default_value="from_project"))
    vf.set_variable(ProjectVariable(name="shared_var", default_value="project_shared"))
    return vf


@pytest.fixture
def global_variables() -> VariablesFile:
    """Create global variables file."""
    vf = VariablesFile(scope=VariableScope.GLOBAL)
    vf.set_variable(ProjectVariable(name="global_var", default_value="global_value"))
    vf.set_variable(ProjectVariable(name="shared_var", default_value="global_shared"))
    return vf


@pytest.fixture
def project_credentials() -> CredentialBindingsFile:
    """Create project credentials file."""
    cbf = CredentialBindingsFile(scope="project")
    cbf.set_binding(CredentialBinding(alias="api_key", vault_path="vault/project/api"))
    cbf.set_binding(CredentialBinding(alias="db_cred", vault_path="vault/project/db"))
    return cbf


@pytest.fixture
def global_credentials() -> CredentialBindingsFile:
    """Create global credentials file."""
    cbf = CredentialBindingsFile(scope="global")
    cbf.set_binding(
        CredentialBinding(alias="shared_cred", vault_path="vault/global/shared")
    )
    cbf.set_binding(CredentialBinding(alias="api_key", vault_path="vault/global/api"))
    return cbf


# ============================================================================
# Initialization Tests
# ============================================================================


class TestProjectContextInitialization:
    """Tests for ProjectContext initialization."""

    def test_create_with_project_only(self, project: Project) -> None:
        """Create context with just project."""
        ctx = ProjectContext(project=project)
        assert ctx.project == project
        assert ctx.project_id == "proj_test"
        assert ctx.project_name == "Test Project"
        assert ctx.scenario is None

    def test_create_with_scenario(self, project: Project, scenario: Scenario) -> None:
        """Create context with project and scenario."""
        ctx = ProjectContext(project=project, scenario=scenario)
        assert ctx.scenario == scenario
        assert ctx.scenario_id == "scen_test"
        assert ctx.scenario_name == "Test Scenario"

    def test_create_with_all_files(
        self,
        project: Project,
        scenario: Scenario,
        project_variables: VariablesFile,
        project_credentials: CredentialBindingsFile,
        global_variables: VariablesFile,
        global_credentials: CredentialBindingsFile,
    ) -> None:
        """Create context with all variable and credential files."""
        ctx = ProjectContext(
            project=project,
            scenario=scenario,
            project_variables=project_variables,
            project_credentials=project_credentials,
            global_variables=global_variables,
            global_credentials=global_credentials,
        )
        assert ctx.project == project
        assert ctx.scenario == scenario


# ============================================================================
# Property Tests
# ============================================================================


class TestProjectContextProperties:
    """Tests for context properties."""

    def test_project_id(self, project: Project) -> None:
        """Get project ID."""
        ctx = ProjectContext(project=project)
        assert ctx.project_id == "proj_test"

    def test_project_name(self, project: Project) -> None:
        """Get project name."""
        ctx = ProjectContext(project=project)
        assert ctx.project_name == "Test Project"

    def test_scenario_id_with_scenario(
        self, project: Project, scenario: Scenario
    ) -> None:
        """Get scenario ID when scenario exists."""
        ctx = ProjectContext(project=project, scenario=scenario)
        assert ctx.scenario_id == "scen_test"

    def test_scenario_id_without_scenario(self, project: Project) -> None:
        """Get scenario ID when no scenario returns None."""
        ctx = ProjectContext(project=project)
        assert ctx.scenario_id is None

    def test_scenario_name_with_scenario(
        self, project: Project, scenario: Scenario
    ) -> None:
        """Get scenario name when scenario exists."""
        ctx = ProjectContext(project=project, scenario=scenario)
        assert ctx.scenario_name == "Test Scenario"

    def test_scenario_name_without_scenario(self, project: Project) -> None:
        """Get scenario name when no scenario returns None."""
        ctx = ProjectContext(project=project)
        assert ctx.scenario_name is None


# ============================================================================
# Variable Access Tests - Individual Scopes
# ============================================================================


class TestVariableAccessScopes:
    """Tests for accessing variables from individual scopes."""

    def test_get_global_variables(
        self, project: Project, global_variables: VariablesFile
    ) -> None:
        """Get global variables."""
        ctx = ProjectContext(project=project, global_variables=global_variables)
        globals_dict = ctx.get_global_variables()
        assert globals_dict["global_var"] == "global_value"

    def test_get_global_variables_none(self, project: Project) -> None:
        """Get global variables when not set returns empty dict."""
        ctx = ProjectContext(project=project)
        assert ctx.get_global_variables() == {}

    def test_get_project_variables(
        self, project: Project, project_variables: VariablesFile
    ) -> None:
        """Get project variables."""
        ctx = ProjectContext(project=project, project_variables=project_variables)
        proj_dict = ctx.get_project_variables()
        assert proj_dict["project_var"] == "project_value"

    def test_get_project_variables_none(self, project: Project) -> None:
        """Get project variables when not set returns empty dict."""
        ctx = ProjectContext(project=project)
        assert ctx.get_project_variables() == {}

    def test_get_scenario_variables(self, project: Project, scenario: Scenario) -> None:
        """Get scenario variables."""
        ctx = ProjectContext(project=project, scenario=scenario)
        scen_dict = ctx.get_scenario_variables()
        assert scen_dict["scenario_var"] == "scenario_value"

    def test_get_scenario_variables_none(self, project: Project) -> None:
        """Get scenario variables when no scenario returns empty dict."""
        ctx = ProjectContext(project=project)
        assert ctx.get_scenario_variables() == {}


# ============================================================================
# Variable Merging Tests
# ============================================================================


class TestVariableMerging:
    """Tests for get_merged_variables with proper priority."""

    def test_merged_all_scopes(
        self,
        project: Project,
        scenario: Scenario,
        project_variables: VariablesFile,
        global_variables: VariablesFile,
    ) -> None:
        """Merge variables from all scopes."""
        ctx = ProjectContext(
            project=project,
            scenario=scenario,
            project_variables=project_variables,
            global_variables=global_variables,
        )
        merged = ctx.get_merged_variables()
        assert merged["global_var"] == "global_value"
        assert merged["project_var"] == "project_value"
        assert merged["scenario_var"] == "scenario_value"

    def test_project_overrides_global(
        self,
        project: Project,
        project_variables: VariablesFile,
        global_variables: VariablesFile,
    ) -> None:
        """Project variables override global."""
        ctx = ProjectContext(
            project=project,
            project_variables=project_variables,
            global_variables=global_variables,
        )
        merged = ctx.get_merged_variables()
        assert merged["shared_var"] == "project_shared"

    def test_scenario_overrides_project(
        self,
        project: Project,
        scenario: Scenario,
        project_variables: VariablesFile,
    ) -> None:
        """Scenario variables override project."""
        ctx = ProjectContext(
            project=project,
            scenario=scenario,
            project_variables=project_variables,
        )
        merged = ctx.get_merged_variables()
        assert merged["override_var"] == "from_scenario"


# ============================================================================
# Single Variable Lookup Tests
# ============================================================================


class TestGetVariable:
    """Tests for get_variable with scope fallback."""

    def test_get_from_scenario(self, project: Project, scenario: Scenario) -> None:
        """Get variable from scenario scope."""
        ctx = ProjectContext(project=project, scenario=scenario)
        assert ctx.get_variable("scenario_var") == "scenario_value"

    def test_get_from_project(
        self, project: Project, project_variables: VariablesFile
    ) -> None:
        """Get variable from project scope."""
        ctx = ProjectContext(project=project, project_variables=project_variables)
        assert ctx.get_variable("project_var") == "project_value"

    def test_get_from_global(
        self, project: Project, global_variables: VariablesFile
    ) -> None:
        """Get variable from global scope."""
        ctx = ProjectContext(project=project, global_variables=global_variables)
        assert ctx.get_variable("global_var") == "global_value"

    def test_get_with_fallback(
        self,
        project: Project,
        scenario: Scenario,
        project_variables: VariablesFile,
        global_variables: VariablesFile,
    ) -> None:
        """Variable lookup falls back through scopes."""
        ctx = ProjectContext(
            project=project,
            scenario=scenario,
            project_variables=project_variables,
            global_variables=global_variables,
        )
        # scenario > project > global
        assert ctx.get_variable("override_var") == "from_scenario"

    def test_get_not_found_returns_default(self, project: Project) -> None:
        """Get non-existent variable returns default."""
        ctx = ProjectContext(project=project)
        assert ctx.get_variable("missing") is None
        assert ctx.get_variable("missing", "default_val") == "default_val"


# ============================================================================
# Credential Resolution Tests
# ============================================================================


class TestCredentialResolution:
    """Tests for resolve_credential_path."""

    def test_resolve_from_scenario(self, project: Project, scenario: Scenario) -> None:
        """Resolve credential from scenario."""
        ctx = ProjectContext(project=project, scenario=scenario)
        path = ctx.resolve_credential_path("db_cred")
        assert path == "vault/scenario/db"

    def test_resolve_from_project(
        self, project: Project, project_credentials: CredentialBindingsFile
    ) -> None:
        """Resolve credential from project."""
        ctx = ProjectContext(project=project, project_credentials=project_credentials)
        path = ctx.resolve_credential_path("api_key")
        assert path == "vault/project/api"

    def test_resolve_from_global(
        self, project: Project, global_credentials: CredentialBindingsFile
    ) -> None:
        """Resolve credential from global."""
        ctx = ProjectContext(project=project, global_credentials=global_credentials)
        path = ctx.resolve_credential_path("shared_cred")
        assert path == "vault/global/shared"

    def test_resolve_with_priority(
        self,
        project: Project,
        scenario: Scenario,
        project_credentials: CredentialBindingsFile,
        global_credentials: CredentialBindingsFile,
    ) -> None:
        """Credential resolution follows priority: scenario > project > global."""
        ctx = ProjectContext(
            project=project,
            scenario=scenario,
            project_credentials=project_credentials,
            global_credentials=global_credentials,
        )
        # db_cred is in both scenario and project, scenario wins
        path = ctx.resolve_credential_path("db_cred")
        assert path == "vault/scenario/db"

    def test_resolve_not_found(self, project: Project) -> None:
        """Resolve non-existent credential returns None."""
        ctx = ProjectContext(project=project)
        path = ctx.resolve_credential_path("missing_cred")
        assert path is None


# ============================================================================
# Get All Credential Aliases Tests
# ============================================================================


class TestGetAllCredentialAliases:
    """Tests for get_all_credential_aliases."""

    def test_all_aliases_merged(
        self,
        project: Project,
        scenario: Scenario,
        project_credentials: CredentialBindingsFile,
        global_credentials: CredentialBindingsFile,
    ) -> None:
        """Get all credential aliases with proper merging."""
        ctx = ProjectContext(
            project=project,
            scenario=scenario,
            project_credentials=project_credentials,
            global_credentials=global_credentials,
        )
        aliases = ctx.get_all_credential_aliases()
        assert "db_cred" in aliases
        assert "api_key" in aliases
        assert "shared_cred" in aliases

    def test_scenario_overrides_project(
        self,
        project: Project,
        scenario: Scenario,
        project_credentials: CredentialBindingsFile,
    ) -> None:
        """Scenario credentials override project."""
        ctx = ProjectContext(
            project=project,
            scenario=scenario,
            project_credentials=project_credentials,
        )
        aliases = ctx.get_all_credential_aliases()
        assert aliases["db_cred"] == "vault/scenario/db"

    def test_project_overrides_global(
        self,
        project: Project,
        project_credentials: CredentialBindingsFile,
        global_credentials: CredentialBindingsFile,
    ) -> None:
        """Project credentials override global."""
        ctx = ProjectContext(
            project=project,
            project_credentials=project_credentials,
            global_credentials=global_credentials,
        )
        aliases = ctx.get_all_credential_aliases()
        assert aliases["api_key"] == "vault/project/api"


# ============================================================================
# Execution Settings Tests
# ============================================================================


class TestExecutionSettings:
    """Tests for execution settings access."""

    def test_get_timeout_default(self, project: Project) -> None:
        """Get timeout from project settings."""
        ctx = ProjectContext(project=project)
        assert ctx.get_timeout() == 30

    def test_get_timeout_scenario_override(
        self, project: Project, scenario: Scenario
    ) -> None:
        """Scenario timeout override takes precedence."""
        ctx = ProjectContext(project=project, scenario=scenario)
        assert ctx.get_timeout() == 60

    def test_get_timeout_no_override(self, project: Project) -> None:
        """No scenario override uses project timeout."""
        scen = Scenario(
            id="scen_x",
            name="X",
            project_id="proj_test",
            execution_settings=ScenarioExecutionSettings(),
        )
        ctx = ProjectContext(project=project, scenario=scen)
        assert ctx.get_timeout() == 30

    def test_get_stop_on_error(self, project: Project) -> None:
        """Get stop_on_error from project settings."""
        ctx = ProjectContext(project=project)
        assert ctx.get_stop_on_error() is True

    def test_get_retry_count(self, project: Project) -> None:
        """Get retry count from project settings."""
        ctx = ProjectContext(project=project)
        assert ctx.get_retry_count() == 2

    def test_get_default_browser(self, project: Project) -> None:
        """Get default browser from project settings."""
        ctx = ProjectContext(project=project)
        assert ctx.get_default_browser() == "chromium"


# ============================================================================
# String Representation Tests
# ============================================================================


class TestProjectContextRepr:
    """Tests for __repr__ method."""

    def test_repr_project_only(self, project: Project) -> None:
        """Repr shows project name only."""
        ctx = ProjectContext(project=project)
        rep = repr(ctx)
        assert "Test Project" in rep
        assert "scenario" not in rep.lower() or "None" in rep

    def test_repr_with_scenario(self, project: Project, scenario: Scenario) -> None:
        """Repr shows project and scenario."""
        ctx = ProjectContext(project=project, scenario=scenario)
        rep = repr(ctx)
        assert "Test Project" in rep
        assert "Test Scenario" in rep
