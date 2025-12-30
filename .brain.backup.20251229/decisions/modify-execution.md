# Decision Tree: Modifying Execution Flow

## Quick Decision

```
What aspect of execution?
├─ NODE EXECUTION ORDER → Step 1: Execution Engine
├─ ERROR HANDLING/RETRY → Step 2: Error Handling
├─ PARALLEL EXECUTION → Step 3: Parallel Nodes
├─ CONDITIONAL BRANCHING → Step 4: Control Flow
└─ EVENT FLOW → Step 5: Event System
```

---

## Step 1: Execution Engine

### Key Files

| File | Purpose |
|------|---------|
| `domain/services/execution_orchestrator.py` | Main execution coordinator |
| `application/execution/workflow_executor.py` | Workflow execution logic |
| `domain/entities/execution_state.py` | Execution state tracking |
| `domain/entities/base_node.py` | Node execution interface |

### Execution Flow

```
WorkflowExecutor.execute(workflow)
    │
    ├─ 1. Initialize ExecutionContext
    │
    ├─ 2. Find Start Node
    │
    ├─ 3. Execute Node
    │   ├─ Resolve input values
    │   ├─ Call node.execute(context)
    │   ├─ Store output values
    │   └─ Publish NodeCompleted event
    │
    ├─ 4. Follow Execution Port
    │   └─ Get next node via exec_out connection
    │
    └─ 5. Repeat until End Node or Error
```

### Modifying Execution Order

```python
# To change how next node is determined:
# File: application/execution/workflow_executor.py

def _get_next_node(self, current_node, context):
    """
    AI-HINT: Modify this to change execution order.
    AI-WARNING: Changes here affect ALL workflows.
    """
    # Current: Follow exec_out connection
    exec_out_port = current_node.get_port("exec_out")
    connection = self._get_connection_from_port(exec_out_port)

    if connection:
        return self._get_node_by_id(connection.target_node_id)
    return None
```

---

## Step 2: Error Handling {#error-handling}

### Key Files

| File | Purpose |
|------|---------|
| `domain/errors/handlers/` | Error handler implementations |
| `nodes/error_handling/try_catch_node.py` | TryCatch node |
| `nodes/error_handling/retry_node.py` | Retry node |

### Adding Custom Error Handler

```python
# domain/errors/handlers/my_handler.py
from casare_rpa.domain.errors import ErrorHandler, ErrorContext

class MyErrorHandler(ErrorHandler):
    """
    AI-HINT: Custom error handler for specific error type.
    AI-CONTEXT: Registered in error_handler_registry.py
    """

    def can_handle(self, error: Exception, context: ErrorContext) -> bool:
        return isinstance(error, MySpecificError)

    async def handle(self, error: Exception, context: ErrorContext) -> bool:
        """
        Returns True if error was handled and execution should continue.
        Returns False if error should propagate.
        """
        # Log error
        logger.warning(f"Handled error: {error}")

        # Optionally set fallback value
        context.set_output("result", "fallback_value")

        return True  # Continue execution
```

### Retry Logic

```python
# In node execute() method
from casare_rpa.utils.resilience import retry_with_backoff

async def execute(self, context):
    @retry_with_backoff(max_retries=3, base_delay=1.0)
    async def do_operation():
        return await self._perform_action()

    try:
        result = await do_operation()
        return {"success": True, "data": result}
    except MaxRetriesExceeded as e:
        return {"success": False, "error": str(e.last_error)}
```

---

## Step 3: Parallel Execution

### Key Files

| File | Purpose |
|------|---------|
| `nodes/control_flow/parallel_node.py` | Parallel execution node |
| `domain/entities/execution_state.py` | Track parallel branches |

### Parallel Execution Pattern

```python
# In ParallelNode or custom parallel logic
import asyncio

async def execute_parallel_branches(self, branches, context):
    """
    AI-HINT: Execute multiple branches in parallel.
    AI-WARNING: Each branch needs isolated context.
    """
    tasks = []
    for branch in branches:
        # Create isolated context for each branch
        branch_context = context.create_branch_context()
        task = asyncio.create_task(
            self._execute_branch(branch, branch_context)
        )
        tasks.append(task)

    # Wait for all branches
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Merge results back to main context
    for result in results:
        if isinstance(result, Exception):
            # Handle branch failure
            pass
        else:
            context.merge_branch_results(result)

    return {"success": True, "branches_completed": len(results)}
```

---

## Step 4: Control Flow {#control-flow}

### Key Files

| File | Purpose |
|------|---------|
| `nodes/control_flow/if_node.py` | Conditional branching |
| `nodes/control_flow/switch_node.py` | Multi-way branching |
| `nodes/control_flow/for_loop_node.py` | Loop iteration |

### Adding New Control Flow

```python
# nodes/control_flow/my_control_node.py
from casare_rpa.domain import node, properties
from casare_rpa.domain.entities import BaseNode
from casare_rpa.domain.value_objects import DataType

@properties(
    PropertyDef("condition", PropertyType.EXPRESSION, essential=True),
)
@node(category="control_flow")
class MyControlNode(BaseNode):
    """
    AI-HINT: Custom control flow node.
    AI-CONTEXT: Must handle multiple exec outputs for branching.
    """

    def _define_ports(self):
        self.add_exec_input()
        # Multiple execution outputs for different paths
        self.add_exec_output("path_a")
        self.add_exec_output("path_b")
        self.add_exec_output("path_default")

        self.add_input_port("value", DataType.ANY, "Value to evaluate")

    async def execute(self, context):
        value = self.get_input_value("value")
        condition = self.get_parameter("condition")

        # Evaluate condition and set active output
        if self._evaluate_path_a(value, condition):
            context.set_next_exec_port("path_a")
        elif self._evaluate_path_b(value, condition):
            context.set_next_exec_port("path_b")
        else:
            context.set_next_exec_port("path_default")

        return {"success": True, "selected_path": context.next_exec_port}
```

---

## Step 5: Event System {#events}

### Key Files

| File | Purpose |
|------|---------|
| `domain/events.py` | Domain event bus |
| `domain/events/__init__.py` | Event class definitions |
| `presentation/canvas/events/` | Presentation event bus |
| `presentation/canvas/coordinators/event_bridge.py` | Domain→Qt bridge |

### Event Flow

```
Node Execution
    │
    ├─ Domain Event Published
    │   └─ domain/events.py: get_event_bus().publish(NodeCompleted(...))
    │
    ├─ Event Bridge Receives
    │   └─ presentation/canvas/coordinators/event_bridge.py
    │
    └─ Qt Signal Emitted
        └─ UI components update via signal/slot
```

### Adding New Event

```python
# 1. Define event in domain/events/__init__.py
@dataclass(frozen=True)
class MyCustomEvent(DomainEvent):
    """Raised when X happens."""
    entity_id: str
    action: str
    metadata: dict = field(default_factory=dict)

# 2. Publish event where appropriate
from casare_rpa.domain.events import get_event_bus, MyCustomEvent

bus = get_event_bus()
bus.publish(MyCustomEvent(
    entity_id="xyz",
    action="created",
    metadata={"key": "value"}
))

# 3. Subscribe to event
def handle_my_event(event: MyCustomEvent):
    logger.info(f"Received: {event.entity_id} - {event.action}")

bus.subscribe(MyCustomEvent, handle_my_event)
```

### Bridge to UI

```python
# presentation/canvas/coordinators/event_bridge.py

class DomainEventBridge:
    """
    AI-HINT: Bridges domain events to Qt signals.
    AI-CONTEXT: Ensures thread-safe UI updates.
    """

    def __init__(self):
        self._domain_bus = get_event_bus()
        self._qt_signals = QtEventSignals()

    def start(self):
        # Subscribe to domain events
        self._domain_bus.subscribe(NodeCompleted, self._on_node_completed)
        self._domain_bus.subscribe(MyCustomEvent, self._on_my_event)

    def _on_my_event(self, event: MyCustomEvent):
        # Emit Qt signal (thread-safe)
        self._qt_signals.my_event_signal.emit(event.entity_id, event.action)
```

---

## Common Modifications

### Change Node Timeout

```python
# In node class
@properties(
    PropertyDef("timeout", PropertyType.INTEGER, default=30000),
)
class MyNode(BaseNode):
    async def execute(self, context):
        timeout = self.get_parameter("timeout") / 1000  # Convert to seconds
        async with asyncio.timeout(timeout):
            result = await self._do_work()
```

### Add Execution Hook

```python
# In workflow executor
class WorkflowExecutor:
    def __init__(self):
        self._pre_execute_hooks = []
        self._post_execute_hooks = []

    def add_pre_execute_hook(self, hook):
        """Called before each node executes."""
        self._pre_execute_hooks.append(hook)

    async def _execute_node(self, node, context):
        # Run pre-hooks
        for hook in self._pre_execute_hooks:
            await hook(node, context)

        result = await node.execute(context)

        # Run post-hooks
        for hook in self._post_execute_hooks:
            await hook(node, context, result)

        return result
```

### Skip Node Conditionally

```python
# In node execute()
async def execute(self, context):
    # Check skip condition
    if self._should_skip(context):
        return {
            "success": True,
            "skipped": True,
            "reason": "Condition not met"
        }

    # Normal execution
    ...
```

---

## Testing Execution Changes

```python
# tests/application/test_workflow_executor.py

@pytest.mark.asyncio
async def test_custom_execution_order(chain_executor):
    """Test modified execution order."""
    workflow = WorkflowBuilder() \
        .add(StartNode(), id="start") \
        .add(MyControlNode(), id="control") \
        .add(NodeA(), id="path_a") \
        .add(NodeB(), id="path_b") \
        .connect("start", "control") \
        .connect("control.path_a", "path_a") \
        .connect("control.path_b", "path_b") \
        .build()

    result = await chain_executor.execute(
        workflow,
        variables={"condition": "a"}
    )

    assert result.executed_nodes == ["start", "control", "path_a"]
```

---

*See also: `.brain/systemPatterns.md` Section 11 (Event Bus)*
