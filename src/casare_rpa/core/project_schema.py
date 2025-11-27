"""
CasareRPA - Project Schema (DEPRECATED)

DEPRECATED: This module is a compatibility layer.
All classes have been moved to domain.entities.project

For new code, import from:
- casare_rpa.domain.entities.project

This module will be removed in v3.0.
"""

import warnings

# Re-export everything from domain layer for backward compatibility
from ..domain.entities.project import (
    # Constants
    PROJECT_SCHEMA_VERSION,
    generate_project_id,
    generate_scenario_id,

    # Enums
    VariableScope,
    VariableType,

    # Variable classes
    ProjectVariable,
    VariablesFile,

    # Credential classes
    CredentialBinding,
    CredentialBindingsFile,

    # Settings classes
    ProjectSettings,
    ScenarioExecutionSettings,

    # Main entities
    Project,
    Scenario,

    # Index classes
    ProjectIndexEntry,
    ProjectsIndex,
)


# Emit deprecation warning when module is imported
warnings.warn(
    "casare_rpa.core.project_schema is deprecated. "
    "Use casare_rpa.domain.entities.project instead. "
    "This module will be removed in v3.0.",
    DeprecationWarning,
    stacklevel=2
)


__all__ = [
    # Constants
    "PROJECT_SCHEMA_VERSION",
    "generate_project_id",
    "generate_scenario_id",

    # Enums
    "VariableScope",
    "VariableType",

    # Variable classes
    "ProjectVariable",
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
