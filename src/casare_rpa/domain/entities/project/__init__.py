"""
CasareRPA - Domain Entities: Project Package

Project hierarchy and organization domain entities.
Split from monolithic project.py for maintainability.
"""

# Base constants and utilities
from casare_rpa.domain.entities.project.base import (
    PROJECT_SCHEMA_VERSION,
    generate_project_id,
    generate_scenario_id,
)

# Credential classes
from casare_rpa.domain.entities.project.credentials import (
    CredentialBinding,
    CredentialBindingsFile,
)

# Index classes
from casare_rpa.domain.entities.project.index import (
    ProjectIndexEntry,
    ProjectsIndex,
)

# Main entities
from casare_rpa.domain.entities.project.project import Project
from casare_rpa.domain.entities.project.scenario import Scenario

# Settings classes
from casare_rpa.domain.entities.project.settings import (
    ProjectSettings,
    ScenarioExecutionSettings,
)

# Variable classes (uses unified Variable from domain.entities.variable)
from casare_rpa.domain.entities.project.variables import (
    ProjectVariable,  # Alias for Variable
    VariableScope,
    VariablesFile,
    VariableType,
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
