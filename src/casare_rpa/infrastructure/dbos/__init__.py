"""
DBOS Durable Execution Infrastructure.

Provides durable workflow execution with automatic checkpointing and recovery
for the CasareRPA Project Aether platform.

Key Components:
- DBOSWorkflowRunner: Wraps ExecuteWorkflowUseCase with DBOS @workflow
- DBOSConfig: Configuration management for DBOS runtime
- Step functions: Atomic @step decorators for node execution

Phase 3 Status:
- [x] Step functions created (execute_node_step, initialize_context_step, cleanup_context_step)
- [x] ExecutionContext serialization added
- [x] DBOSWorkflowRunner updated to use step functions
- [ ] @workflow decorator application (Phase 3.2)
- [ ] Crash recovery tests (Phase 3.4)

References:
- https://docs.dbos.dev/python/tutorials/quickstart
- Plan: C:\\Users\\Rau\\.claude\\plans\\tender-puzzling-ullman.md
"""

from .config import DBOSConfig
from .workflow_runner import DBOSWorkflowRunner
from .step_functions import (
    ExecutionStepResult,
    execute_node_step,
    initialize_context_step,
    cleanup_context_step,
)

__all__ = [
    "DBOSConfig",
    "DBOSWorkflowRunner",
    "ExecutionStepResult",
    "execute_node_step",
    "initialize_context_step",
    "cleanup_context_step",
]
