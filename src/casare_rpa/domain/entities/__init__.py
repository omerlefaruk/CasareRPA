"""
CasareRPA - Domain Entities

Domain entities are objects with identity that persist over time.
"""

from .base_node import BaseNode
from .workflow_metadata import WorkflowMetadata
from .node_connection import NodeConnection
from .workflow import WorkflowSchema, VariableDefinition
from .execution_state import ExecutionState, ExecutionContext
from .project import (
    Project,
    Scenario,
    ProjectVariable,
    VariablesFile,
    CredentialBinding,
    CredentialBindingsFile,
    ProjectSettings,
    ScenarioExecutionSettings,
    ProjectIndexEntry,
    ProjectsIndex,
    VariableScope,
    VariableType,
    generate_project_id,
    generate_scenario_id,
    PROJECT_SCHEMA_VERSION,
)

__all__ = [
    "BaseNode",
    "WorkflowMetadata",
    "NodeConnection",
    "WorkflowSchema",
    "VariableDefinition",
    "ExecutionState",
    "ExecutionContext",  # Alias for ExecutionState (backwards compatibility)
    # Project entities
    "Project",
    "Scenario",
    "ProjectVariable",
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
]
