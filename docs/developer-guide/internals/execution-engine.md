# Execution Engine Internals

This document describes the internal architecture of CasareRPA's workflow execution engine.

## Overview

The execution engine is responsible for orchestrating workflow execution, managing node lifecycle, resolving variables, and handling errors. It follows a layered architecture with clear separation between domain logic, application use cases, and infrastructure concerns.

## Core Components

### ExecuteWorkflowUseCase

**Location:** `src/casare_rpa/application/use_cases/execute_workflow.py`

The main orchestrator for workflow execution. Coordinates all execution components.

```python
from casare_rpa.application.use_cases import ExecuteWorkflowUseCase
from casare_rpa.domain.entities.workflow import WorkflowSchema

# Create executor with workflow
executor = ExecuteWorkflowUseCase(
    workflow=workflow_schema,
    settings=ExecutionSettings(node_timeout=120.0),
    initial_variables={"api_key": "xxx"},
)

# Execute workflow
success = await executor.execute(run_all=False)
```

**Responsibilities:**

| Component | Purpose |
|-----------|---------|
| StateManager | Tracks execution progress, pause/resume, stop signals |
| NodeExecutor | Executes individual nodes with timeout |
| VariableResolver | Resolves `{{variable}}` patterns in node properties |
| ParallelStrategy | Handles Fork/Join and concurrent execution |
| ResultHandler | Routes execution flow based on node results |

### Execution Flow

```
1. execute() called
   |
   +-> Create ExecutionContext
   +-> Initialize delegates (NodeExecutor, VariableResolver, etc.)
   +-> Publish WorkflowStarted event
   |
2. Find start node(s)
   |
   +-> Single start: _execute_from_node()
   +-> Multiple starts (run_all): _parallel_strategy.execute_parallel_workflows()
   |
3. Main execution loop (_execute_from_node)
   |
   for each node in queue:
       +-> Check stop/pause signals
       +-> Skip if already executed (except loops)
       +-> Transfer inputs via VariableResolver
       +-> Execute node via NodeExecutor
       +-> Handle result (success/failure/special routing)
       +-> Store outputs in context
       +-> Get next nodes from ExecutionOrchestrator
   |
4. Finalize
   |
   +-> Publish WorkflowCompleted/WorkflowFailed/WorkflowStopped
   +-> Cleanup ExecutionContext
```

### NodeExecutor

**Location:** `src/casare_rpa/application/use_cases/node_executor.py`

Handles individual node execution with lifecycle management.

```python
from casare_rpa.application.use_cases import NodeExecutor, NodeExecutionResult

executor = NodeExecutor(
    context=execution_context,
    event_bus=event_bus,
    node_timeout=120.0,  # seconds
    progress_calculator=lambda: 50.0,
)

result: NodeExecutionResult = await executor.execute(node_instance)
```

**Node Execution Lifecycle:**

```
1. IDLE -> RUNNING
   +-> Check if disabled (bypass mode)
   +-> Set context.current_node_id
   +-> Publish NodeStarted event
   +-> Record metrics start

2. Validate node
   +-> Check required input ports
   +-> Run node._validate_config()

3. Execute with timeout
   +-> asyncio.wait_for(node.execute(context), timeout)
   +-> Handle asyncio.TimeoutError

4. Process result
   +-> SUCCESS: Update status, collect outputs, publish NodeCompleted
   +-> ERROR: Update status, publish NodeFailed

5. Record metrics
```

**Bypass Pattern:**

When a node has `config["_disabled"] = True`, it enters bypass mode:

```python
# Bypass logic in _handle_bypassed_node()
# 1. Mark node as SUCCESS (doesn't block workflow)
# 2. Pass-through inputs to matching outputs:
#    - Direct match: page -> page
#    - Suffix pattern: fields_in -> fields_out
```

### NodeExecutorWithTryCatch

Extended executor with try-catch block error capture support:

```python
from casare_rpa.application.use_cases import NodeExecutorWithTryCatch

executor = NodeExecutorWithTryCatch(
    context=context,
    event_bus=event_bus,
    error_capturer=error_handler.capture_error,  # Returns True if captured
)
```

When a node inside a TryNode block fails:
1. Error is captured by `error_capturer` callback
2. Error stored in `try_state` variable
3. Execution routes to CatchNode
4. Result returns `success=True, error_captured=True`

---

## Port Resolution

### Data Flow Between Nodes

Data flows through connected ports. The VariableResolver handles data transfer:

```python
# In VariableResolver.transfer_inputs_to_node()
for connection in workflow.connections:
    if connection.target_node == node_id:
        source_node = get_node_instance(connection.source_node)
        source_port = source_node.output_ports[connection.source_port]
        target_port = node.input_ports[connection.target_port]

        # Transfer value
        value = source_port.get_value()
        target_port.set_value(value)
```

### Port Value Sources (Dual-Source Pattern)

Node properties can come from two sources:
1. **Connected ports** - Data from upstream nodes
2. **Config values** - Static values from properties panel

```python
# In BaseNode.get_input_value()
def get_input_value(self, port_name: str, default=None):
    # 1. Check port connection first
    if port_name in self.input_ports:
        port = self.input_ports[port_name]
        if port.value is not None:
            return port.value

    # 2. Fall back to config
    return self.config.get(port_name, default)
```

---

## Variable Resolution

### Pattern Syntax

Variables use double-brace syntax: `{{variable_name}}`

```python
# Simple variable
"{{api_key}}"  # Resolves to context.get_variable("api_key")

# Node output reference
"{{node_id.output_port}}"  # Resolves to node's output port value

# Nested access
"{{data.items[0].name}}"  # JSON path-style access
```

### Resolution Process

**Location:** `src/casare_rpa/application/use_cases/variable_resolver.py`

```python
class VariableResolver:
    def resolve_value(self, value: Any) -> Any:
        if not isinstance(value, str) or "{{" not in value:
            return value

        # Find all {{...}} patterns
        pattern = r"\{\{([^}]+)\}\}"
        matches = re.findall(pattern, value)

        for var_name in matches:
            resolved = self._resolve_variable(var_name)
            if resolved is not None:
                value = value.replace(f"{{{{{var_name}}}}}", str(resolved))

        return value
```

### Variable Cache

ExecutionContext uses a resolution cache for performance:

```python
# In ExecutionContext.resolve_value()
# 1. Check cache
found, cached_result = self._var_cache.get_cached(value, self._state.variables)
if found:
    return cached_result

# 2. Cache miss - resolve
result = self._state.resolve_value(value)

# 3. Store in cache
self._var_cache.cache_result(value, self._state.variables, result)
```

---

## Error Propagation

### Error Flow

```
Node execution fails
    |
    +-> NodeExecutor._handle_exception()
        |
        +-> Check if inside TryNode block (via error_capturer)
            |
            +-> YES: Capture error, route to CatchNode
            |       Return success=True, error_captured=True
            |
            +-> NO: Publish NodeFailed event
                    Return success=False with error details
    |
ExecuteWorkflowUseCase._execute_from_node()
    |
    +-> result_handler.handle_execution_failure()
        |
        +-> Check for TryCatch recovery path
        +-> If recoverable: add CatchNode to queue
        +-> If not: mark workflow failed
```

### Error Result Structure

```python
# Node error result
{
    "success": False,
    "error": "Element not found: #submit-btn",
    "error_code": "ELEMENT_NOT_FOUND",  # Optional ErrorCode
}

# Captured error (TryCatch)
{
    "success": True,
    "error_captured": True,
}
```

---

## Parallel Execution

### Fork/Join Pattern

**Location:** `src/casare_rpa/application/use_cases/execution_strategies_parallel.py`

```python
# ForkNode result triggers parallel execution
result = {
    "success": True,
    "parallel_branches": ["branch_1", "branch_2", "branch_3"],
    "paired_join_id": "join_node_123",
}

# ParallelExecutionStrategy handles branches
await parallel_strategy.execute_parallel_branches(result)
```

**Execution Flow:**

```
ForkNode executes
    |
    +-> Returns parallel_branches list
    +-> ParallelStrategy creates branch contexts (cloned from main)
    +-> Each branch executed concurrently (asyncio.gather)
    +-> Results merged back to main context
    +-> JoinNode added to queue
```

### Multiple Workflows (Run All)

When canvas has multiple StartNodes:

```python
# In execute() with run_all=True
start_nodes = orchestrator.find_all_start_nodes()
if len(start_nodes) > 1:
    await parallel_strategy.execute_parallel_workflows(start_nodes)
```

Each workflow gets:
- **Shared variables** - Same dict reference for coordination
- **Separate browser** - Independent BrowserResourceManager

---

## Subflow Execution

**Location:** `src/casare_rpa/application/use_cases/subflow_executor.py`

Subflows are reusable workflow components executed as atomic units.

```python
from casare_rpa.application.use_cases import SubflowExecutor, Subflow

executor = SubflowExecutor(event_bus=event_bus, node_timeout=120.0)

result = await executor.execute(
    subflow=subflow_definition,
    inputs={"url": "https://example.com"},
    context=parent_context,
    param_values={"timeout": 30000},  # Promoted parameters
)

if result.success:
    outputs = result.outputs  # {"scraped_data": [...]}
```

### Subflow Context Isolation

```python
# Internal context creation
internal_context = parent_context.clone_for_branch(f"subflow_{name}")

# Input injection
for input_def in subflow.inputs:
    internal_context.set_variable(input_def.name, inputs[input_def.name])

# Browser resources shared (read-only)
internal_context._resources = parent_context._resources
```

### Promoted Parameters

Allow configuring internal node properties from subflow level:

```python
@dataclass
class PromotedParameter:
    name: str
    display_name: str
    internal_node_id: str
    internal_property_name: str
    default_value: Any = None

# During execution, values injected into internal nodes
node.config[internal_property_name] = param_value
```

---

## ExecutionContext

**Location:** `src/casare_rpa/infrastructure/execution/execution_context.py`

Facade composing domain state and infrastructure resources.

### Architecture

```
ExecutionContext
    |
    +-> ExecutionState (domain)
    |   +-> Variables
    |   +-> Execution tracking
    |   +-> Stop/pause state
    |
    +-> BrowserResourceManager (infrastructure)
    |   +-> Browser instances
    |   +-> Page management
    |   +-> Cleanup
    |
    +-> VariableResolutionCache
    |   +-> LRU cache for resolved values
    |
    +-> Resources registry
        +-> Telegram client
        +-> Credential provider
        +-> Custom resources
```

### Key Methods

```python
# Variable management
context.set_variable("name", value)
context.get_variable("name", default=None)
context.resolve_value("Hello {{name}}!")

# Browser management
context.set_active_page(page, name="default")
page = context.get_active_page()

# Execution control
context.stop_execution()
context.is_stopped()
await context.pause_checkpoint()

# Cleanup
await context.cleanup()  # Releases all resources
```

### Branch Context

For parallel execution:

```python
# Clone for parallel branch (isolated variables, shared browser)
branch_ctx = context.clone_for_branch("branch_1")

# Create for parallel workflow (shared variables, separate browser)
workflow_ctx = context.create_workflow_context("workflow_2")
```

---

## Event System Integration

The execution engine publishes typed domain events:

```python
from casare_rpa.domain.events import (
    WorkflowStarted,
    WorkflowCompleted,
    WorkflowFailed,
    NodeStarted,
    NodeCompleted,
    NodeFailed,
    get_event_bus,
)

# Published during execution
event_bus.publish(WorkflowStarted(
    workflow_id="wf_123",
    workflow_name="My Workflow",
    execution_mode=ExecutionMode.NORMAL,
    total_nodes=15,
))

event_bus.publish(NodeCompleted(
    node_id="node_456",
    node_type="ClickElementNode",
    workflow_id="wf_123",
    execution_time_ms=150.5,
    output_data={"clicked": True},
))
```

---

## Performance Considerations

### Node Instance Caching

```python
# In ExecuteWorkflowUseCase
def _get_node_instance(self, node_id: str) -> Any:
    if node_id in self._node_instances:
        return self._node_instances[node_id]

    node = _create_node_from_dict(node_data)
    self._node_instances[node_id] = node
    return node
```

### Metrics Recording

```python
# Execution metrics via performance_metrics
metrics = get_metrics()
metrics.record_workflow_start(workflow_name)
metrics.record_node_start(node_type, node_id)
metrics.record_node_complete(node_type, node_id, time_ms, success)
metrics.record_workflow_complete(workflow_name, time_ms, success)
```

---

## Related Documentation

- [Browser Integration](browser-integration.md) - Playwright lifecycle
- [Desktop Integration](desktop-integration.md) - UIAutomation integration
- [Error Codes Reference](../../reference/error-codes.md) - Error code catalog
- [Data Types Reference](../../reference/data-types.md) - Port data types
