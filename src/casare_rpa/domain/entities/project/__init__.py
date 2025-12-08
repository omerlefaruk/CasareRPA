"""
CasareRPA - Domain Entities: Project Package

Project hierarchy and organization domain entities.
Split from monolithic project.py for maintainability.

v2.0.0: Added Environment, Folder, and Template entities.
"""

# Base constants and utilities
from casare_rpa.domain.entities.project.base import (
    PROJECT_SCHEMA_VERSION,
    generate_environment_id,
    generate_folder_id,
    generate_project_id,
    generate_scenario_id,
    generate_template_id,
)

# Credential classes
from casare_rpa.domain.entities.project.credentials import (
    CredentialBinding,
    CredentialBindingsFile,
)

# Environment classes (v2.0.0)
from casare_rpa.domain.entities.project.environment import (
    ENVIRONMENT_INHERITANCE,
    Environment,
    EnvironmentSettings,
    EnvironmentType,
)

# Folder classes (v2.0.0)
from casare_rpa.domain.entities.project.folder import (
    FolderColor,
    FoldersFile,
    ProjectFolder,
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

# Template classes (v2.0.0)
from casare_rpa.domain.entities.project.template import (
    ProjectTemplate,
    TemplateCategory,
    TemplateCredential,
    TemplateDifficulty,
    TemplatesFile,
    TemplateVariable,
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
    "generate_environment_id",
    "generate_folder_id",
    "generate_template_id",
    # Enums
    "VariableScope",
    "VariableType",
    "EnvironmentType",
    "FolderColor",
    "TemplateCategory",
    "TemplateDifficulty",
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
    # Environment classes (v2.0.0)
    "Environment",
    "EnvironmentSettings",
    "ENVIRONMENT_INHERITANCE",
    # Folder classes (v2.0.0)
    "ProjectFolder",
    "FoldersFile",
    # Template classes (v2.0.0)
    "ProjectTemplate",
    "TemplateVariable",
    "TemplateCredential",
    "TemplatesFile",
]
