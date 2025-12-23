"""
Domain Project Schema Re-export Module.

Re-exports project schema components from domain.entities.project for convenience.
This allows imports like `from casare_rpa.domain.project_schema import Project`.

All implementations are in domain.entities.project - this is just a convenience alias.
"""

from casare_rpa.domain.entities.project import (
    # Constants
    PROJECT_SCHEMA_VERSION,
    # Credential classes
    CredentialBinding,
    CredentialBindingsFile,
    # Main entities
    Project,
    # Index classes
    ProjectIndexEntry,
    # Settings classes
    ProjectSettings,
    ProjectsIndex,
    Scenario,
    ScenarioExecutionSettings,
    # Enums
    VariableScope,
    # Variable classes
    VariablesFile,
    VariableType,
    generate_project_id,
    generate_scenario_id,
)
from casare_rpa.domain.entities.variable import ProjectVariable, Variable

__all__ = [
    # Constants
    "PROJECT_SCHEMA_VERSION",
    "generate_project_id",
    "generate_scenario_id",
    # Enums
    "VariableScope",
    "VariableType",
    # Variable classes
    "Variable",
    "ProjectVariable",  # Alias for Variable (backwards compatibility)
    "VariablesFile",
    # Credential classes
    "CredentialBinding",
    "CredentialBindingsFile",
    # Settings classes
    "ProjectSettings",
    "ScenarioExecutionSettings",
    # Main entities
    "Project",
    "Scenario",
    # Index classes
    "ProjectIndexEntry",
    "ProjectsIndex",
]
