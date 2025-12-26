"""
CasareRPA - Domain Entities

AI-HINT: Core domain entities with identity that persist over time.
AI-CONTEXT: All nodes inherit from BaseNode. Projects contain Scenarios.

Domain entities are objects with identity that persist over time.

PUBLIC API - Safe to import:
    BaseNode, WorkflowSchema, Variable, Project, Scenario, Subflow

INTERNAL - Avoid direct import:
    ExecutionState (use IExecutionContext interface)
"""

# Parallel agent framework entities
from casare_rpa.domain.entities.agent_coordination import (
    ConditionEvent,
    ResourceAllocation,
    SharedState,
    StateSubscription,
)
from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.entities.execution_state import ExecutionContext, ExecutionState
from casare_rpa.domain.entities.node_connection import NodeConnection

# WorkflowSchedule removed - use Schedule Trigger node instead
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
from casare_rpa.domain.entities.resource_node import ResourceNode
from casare_rpa.domain.entities.subflow import (
    MAX_NESTING_DEPTH,
    SUBFLOW_SCHEMA_VERSION,
    SUBFLOWS_DIRECTORY,
    Subflow,
    SubflowMetadata,
    SubflowParameter,
    SubflowPort,
    generate_subflow_id,
)
from casare_rpa.domain.entities.task_decomposition import (
    DecompositionExecutionResult,
    DecompositionResult,
    ParallelGroup,
    ResourceRequest,
    Subtask,
    SubtaskPriority,
    SubtaskResult,
    SubtaskStatus,
)
from casare_rpa.domain.entities.tenant import Tenant, TenantId, TenantSettings
from casare_rpa.domain.entities.trigger_config import (
    TriggerConfig,
    TriggerConfigProtocol,
)
from casare_rpa.domain.entities.user import User, UserStatus
from casare_rpa.domain.entities.variable import (
    ProjectVariable,
    Variable,
    VariableDefinition,
)
from casare_rpa.domain.entities.workflow import WorkflowSchema
from casare_rpa.domain.entities.workflow_metadata import WorkflowMetadata

__all__ = [
    "BaseNode",
    "ResourceNode",
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
    # User entities
    "User",
    "UserStatus",
    # Parallel agent framework
    "SharedState",
    "StateSubscription",
    "ConditionEvent",
    "ResourceAllocation",
    "DecompositionResult",
    "DecompositionExecutionResult",
    "ParallelGroup",
    "ResourceRequest",
    "Subtask",
    "SubtaskPriority",
    "SubtaskResult",
    "SubtaskStatus",
]
