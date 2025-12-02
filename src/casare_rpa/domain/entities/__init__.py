"""
CasareRPA - Domain Entities

Domain entities are objects with identity that persist over time.
"""

from .base_node import BaseNode
from .workflow_metadata import WorkflowMetadata
from .node_connection import NodeConnection
from .variable import Variable, VariableDefinition, ProjectVariable
from .workflow import WorkflowSchema
from .execution_state import ExecutionState, ExecutionContext
from .tenant import Tenant, TenantId, TenantSettings
from .project import (
    # Constants
    PROJECT_SCHEMA_VERSION,
    generate_project_id,
    generate_scenario_id,
    # Enums
    VariableScope,
    VariableType,
    # Variable classes
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

__all__ = [
    "BaseNode",
    "WorkflowMetadata",
    "NodeConnection",
    "WorkflowSchema",
    # Unified Variable class and backward compatibility aliases
    "Variable",
    "VariableDefinition",  # Alias for Variable (backwards compatibility)
    "ProjectVariable",  # Alias for Variable (backwards compatibility)
    "ExecutionState",
    "ExecutionContext",  # Alias for ExecutionState (backwards compatibility)
    # Project entities
    "Project",
    "Scenario",
    "VariablesFile",
    "CredentialBinding",
    "CredentialBindingsFile",
    "ProjectSettings",
    "ScenarioExecutionSettings",
    "ProjectIndexEntry",
    "ProjectsIndex",
    "VariableScope",
    "VariableType",
    "generate_project_id",
    "generate_scenario_id",
    "PROJECT_SCHEMA_VERSION",
    # Tenant entities
    "Tenant",
    "TenantId",
    "TenantSettings",
]
