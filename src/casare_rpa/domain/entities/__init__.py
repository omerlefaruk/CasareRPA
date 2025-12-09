"""
CasareRPA - Domain Entities

Domain entities are objects with identity that persist over time.
"""

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.entities.workflow_metadata import WorkflowMetadata
from casare_rpa.domain.entities.node_connection import NodeConnection
from casare_rpa.domain.entities.variable import (
    Variable,
    VariableDefinition,
    ProjectVariable,
)
from casare_rpa.domain.entities.workflow import WorkflowSchema
from casare_rpa.domain.entities.execution_state import ExecutionState, ExecutionContext
from casare_rpa.domain.entities.tenant import Tenant, TenantId, TenantSettings
from casare_rpa.domain.entities.subflow import (
    Subflow,
    SubflowPort,
    SubflowParameter,
    SubflowMetadata,
    SUBFLOW_SCHEMA_VERSION,
    MAX_NESTING_DEPTH,
    SUBFLOWS_DIRECTORY,
    generate_subflow_id,
)
from casare_rpa.domain.entities.trigger_config import (
    TriggerConfig,
    TriggerConfigProtocol,
)

# WorkflowSchedule removed - use Schedule Trigger node instead
from casare_rpa.domain.entities.project import (
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
    # Subflow entities
    "Subflow",
    "SubflowPort",
    "SubflowParameter",
    "SubflowMetadata",
    "SUBFLOW_SCHEMA_VERSION",
    "MAX_NESTING_DEPTH",
    "SUBFLOWS_DIRECTORY",
    "generate_subflow_id",
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
    # Trigger entities
    "TriggerConfig",
    "TriggerConfigProtocol",
]
