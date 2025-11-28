"""
CasareRPA - Domain Entities: Project Package

Project hierarchy and organization domain entities.
Split from monolithic project.py for maintainability.
"""

# Base constants and utilities
from .base import (
    PROJECT_SCHEMA_VERSION,
    generate_project_id,
    generate_scenario_id,
)

# Variable classes (uses unified Variable from domain.entities.variable)
from .variables import (
    VariableScope,
    VariableType,
    ProjectVariable,  # Alias for Variable
    VariablesFile,
)

# Credential classes
from .credentials import (
    CredentialBinding,
    CredentialBindingsFile,
)

# Settings classes
from .settings import (
    ProjectSettings,
    ScenarioExecutionSettings,
)

# Main entities
from .project import Project
from .scenario import Scenario

# Index classes
from .index import (
    ProjectIndexEntry,
    ProjectsIndex,
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
