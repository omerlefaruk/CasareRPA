# Phase 3: Durable Execution Implementation

## Overview
Transform workflow execution to use DBOS @workflow and @step decorators for automatic checkpointing, crash recovery, and exactly-once execution.

## Current Architecture Analysis

### ExecuteWorkflowUseCase (Application Layer)
- Main execution loop at `execute()` (line 374)
- Node execution at `_execute_node()` (line 219)
- Sequential execution via `_execute_from_node()` (line 490)
- Event emission via EventBus
- ExecutionContext for resources (Playwright, variables)

### DBOSWorkflowRunner (Infrastructure Layer)
- Currently wraps ExecuteWorkflowUseCase
- Placeholder for @workflow decorator
- No actual DBOS integration yet

### ExecutionOrchestrator (Domain Layer)
- Pure routing logic (no async, no side effects)
- Connection traversal
- Control flow decisions

## Implementation Plan

### 1. Create DBOS Step Functions Module
**File**: `src/casare_rpa/infrastructure/dbos/step_functions.py`

Convert node execution to @step functions:
- `@DBOS.step()` decorator for atomic node execution
- Pass node data + ExecutionContext as parameters
- Return ExecutionResult with state updates
- Enable automatic retry on transient failures

### 2. Modify DBOSWorkflowRunner
**File**: `src/casare_rpa/infrastructure/dbos/workflow_runner.py`

Add actual @workflow integration:
- Decorate `execute()` with `@DBOS.workflow()`
- Convert sequential execution to @step calls
- Pass ExecutionContext state through DBOS workflow context
- Remove manual checkpointing (DBOS auto-checkpoints after each @step)

### 3. Create ExecutionState Value Object
**File**: `src/casare_rpa/domain/value_objects/execution_state.py`

Serializable execution state:
- `executed_nodes: Set[NodeId]`
- `current_node_id: Optional[NodeId]`
- `variables: Dict[str, Any]`
- `status: WorkflowStatus`
- Pydantic model for JSON serialization

### 4. Integrate with ExecutionContext
**File**: `src/casare_rpa/infrastructure/execution/execution_context.py`

Add state serialization:
- `to_dict()` method for DBOS persistence
- `from_dict()` classmethod for restoration
- Handle Playwright resources (non-serializable)

### 5. Testing
**File**: `tests/infrastructure/test_dbos_durable_execution.py`

Crash recovery tests:
- Start workflow, kill process mid-execution
- Restart and verify resumption from checkpoint
- Validate exactly-once node execution
- Test state restoration

## Technical Details

### DBOS @workflow Pattern
```python
@DBOS.workflow()
async def execute_workflow_durable(
    workflow_id: str,
    workflow_data: Dict[str, Any]
) -> Dict[str, Any]:
    # DBOS auto-checkpoints after each @step
    state = await initialize_execution_state(workflow_data)

    for node_id in execution_order:
        result = await execute_node_step(node_id, state)
        state = await update_execution_state(state, result)

    return {"success": True, "state": state}
```

### DBOS @step Pattern
```python
@DBOS.step()
async def execute_node_step(
    node_id: str,
    node_config: Dict[str, Any],
    context_state: Dict[str, Any]
) -> Dict[str, Any]:
    # Atomic node execution
    # Auto-retry on transient failures
    # Checkpointed on completion
    context = ExecutionContext.from_dict(context_state)
    node = create_node_from_config(node_config)
    result = await node.execute(context)
    return {"success": True, "result": result, "context": context.to_dict()}
```

### State Serialization Strategy
- **Serializable**: Variables, node IDs, status, timestamps
- **Non-serializable**: Playwright contexts, browser instances
- **Solution**: Recreate resources on recovery using stored config

### Resource Recreation on Recovery
```python
async def recreate_resources(state: Dict[str, Any]) -> ExecutionContext:
    context = ExecutionContext(
        workflow_name=state["workflow_name"],
        initial_variables=state["variables"]
    )

    # Playwright resources recreated lazily on first use
    # No need to serialize browser state

    return context
```

## Migration Strategy

### Phase 3.1: Step Functions (Current)
- Create step_functions.py with @step decorators
- Test individual step execution
- Verify retry behavior

### Phase 3.2: Workflow Integration
- Add @workflow to DBOSWorkflowRunner
- Convert sequential execution to step calls
- Remove manual checkpointing

### Phase 3.3: State Management
- Add ExecutionState value object
- Implement serialization in ExecutionContext
- Test state restoration

### Phase 3.4: Crash Recovery
- Integration tests for crash scenarios
- Verify exactly-once execution
- Performance benchmarks

## Success Criteria

- [ ] All node executions wrapped in @step
- [ ] Workflow execution wrapped in @workflow
- [ ] State serialization complete
- [ ] Crash recovery tests pass (kill process, resume)
- [ ] Exactly-once guarantee verified
- [ ] No manual checkpointing code
- [ ] Performance acceptable (< 10% overhead)

## Files to Create/Modify

**Create**:
- `src/casare_rpa/infrastructure/dbos/step_functions.py`
- `src/casare_rpa/domain/value_objects/execution_state.py`
- `tests/infrastructure/test_dbos_durable_execution.py`
- `tests/infrastructure/test_crash_recovery.py`

**Modify**:
- `src/casare_rpa/infrastructure/dbos/workflow_runner.py`
- `src/casare_rpa/infrastructure/execution/execution_context.py`

## Next Steps

1. Create step_functions.py with @step decorators
2. Test step execution in isolation
3. Add @workflow to DBOSWorkflowRunner
4. Create ExecutionState value object
5. Add serialization to ExecutionContext
6. Write crash recovery tests
7. Remove manual checkpointing

---

**Phase**: 3
**Status**: Planning Complete → Implementation Starting
**Last Updated**: 2025-11-28
