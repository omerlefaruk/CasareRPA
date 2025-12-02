# Parallel Execution Nodes Implementation Plan

## Overview
Implement true parallel execution with ForkNode, JoinNode, and ParallelForEachNode.

## Architecture Decision

**Approach**: Executor-level parallelism with `asyncio.gather`

The executor (`execute_workflow.py`) will be modified to:
1. Detect `parallel_branches` key in ExecutionResult
2. Clone ExecutionContext for each branch (variable isolation)
3. Execute branches concurrently with `asyncio.gather`
4. Merge results at JoinNode

## New Nodes

### 1. ForkNode
```
Inputs:  exec_in
Outputs: branch_1, branch_2, branch_3, ..., branch_N (configurable)

Returns: {
    "parallel_branches": ["branch_1", "branch_2", ...],
    "fork_id": node_id,  # For JoinNode pairing
}
```

### 2. JoinNode
```
Inputs:  exec_in (multiple connections allowed)
Outputs: exec_out, results (Dict of branch results)

Behavior:
- Tracks which branches have arrived via state key
- Waits until ALL expected branches complete
- Merges branch variables back to main context
- Continues to exec_out
```

### 3. ParallelForEachNode
```
Inputs:  exec_in, items (List), batch_size (Int, default=5)
Outputs: body (per-item execution), completed, current_item, current_index

Behavior:
- Takes list of items
- Processes batch_size items concurrently
- Each item triggers body branch execution
- Continues to completed when done
```

## Executor Modifications (execute_workflow.py)

### Current Flow (Sequential)
```python
while nodes_to_execute:
    current = nodes_to_execute.pop(0)
    result = await self._execute_node(current)
    next_nodes = orchestrator.get_next_nodes(current, result)
    nodes_to_execute.extend(next_nodes)  # Sequential queue
```

### New Flow (Parallel-aware)
```python
while nodes_to_execute:
    current = nodes_to_execute.pop(0)
    result = await self._execute_node(current)

    # Check for parallel execution
    if result and "parallel_branches" in result:
        branch_results = await self._execute_parallel_branches(
            current, result["parallel_branches"], result.get("fork_id")
        )
        # Store results for JoinNode
        self.context.variables[f"{result['fork_id']}_branch_results"] = branch_results
        # Find JoinNode and continue there
        join_node = self._find_paired_join(result["fork_id"])
        if join_node:
            nodes_to_execute.insert(0, join_node)
    else:
        next_nodes = orchestrator.get_next_nodes(current, result)
        nodes_to_execute.extend(next_nodes)
```

### Branch Execution Method
```python
async def _execute_parallel_branches(
    self, fork_node_id: NodeId, branch_ports: List[str], fork_id: str
) -> Dict[str, Any]:
    """Execute branches in parallel with isolated contexts."""

    async def execute_branch(branch_port: str) -> Tuple[str, Any]:
        # Clone context for isolation
        branch_context = self.context.clone_for_branch(branch_port)

        # Get target node for this branch
        target_node = self.orchestrator.get_connection_target(fork_node_id, branch_port)

        # Execute branch until JoinNode or terminal
        await self._execute_branch_to_join(target_node, branch_context, fork_id)

        return branch_port, branch_context.variables

    # Execute all branches concurrently
    tasks = [execute_branch(port) for port in branch_ports]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Collect results
    branch_results = {}
    for result in results:
        if isinstance(result, Exception):
            # Handle branch failure
            branch_results[f"error_{id(result)}"] = str(result)
        else:
            port, variables = result
            branch_results[port] = variables

    return branch_results
```

## Variable Isolation Strategy

### Context Cloning
```python
# ExecutionContext
def clone_for_branch(self, branch_name: str) -> "ExecutionContext":
    """Create isolated context for parallel branch."""
    return ExecutionContext(
        workflow_name=self.workflow_name,
        mode=self._state.mode,
        initial_variables=self.variables.copy(),  # Snapshot
        project_context=self.project_context,
        # Shared resources (browser) - read-only during parallel
        resources=self._resources,
    )
```

### Result Merging at JoinNode
```python
# JoinNode.execute()
branch_results = context.variables.get(f"{fork_id}_branch_results", {})

# Merge strategy: Namespace by branch
for branch_port, branch_vars in branch_results.items():
    for key, value in branch_vars.items():
        # Prefix with branch name to avoid conflicts
        context.variables[f"{branch_port}_{key}"] = value

# Also provide combined dict
self.set_output_value("results", branch_results)
```

## ParallelForEach Implementation

Different from Fork/Join - handles batched iteration:

```python
async def execute(self, context: ExecutionContext) -> ExecutionResult:
    state_key = f"{self.node_id}_parallel_foreach"

    if state_key not in context.variables:
        # Initialize
        items = self.get_input_value("items") or []
        batch_size = self.get_parameter("batch_size", 5)
        context.variables[state_key] = {
            "items": items,
            "index": 0,
            "batch_size": batch_size,
            "results": [],
        }

    state = context.variables[state_key]
    items = state["items"]
    index = state["index"]
    batch_size = state["batch_size"]

    if index >= len(items):
        # All done
        del context.variables[state_key]
        return {
            "success": True,
            "data": {"results": state["results"]},
            "next_nodes": ["completed"],
        }

    # Get current batch
    batch_end = min(index + batch_size, len(items))
    current_batch = items[index:batch_end]
    state["index"] = batch_end

    # Signal parallel execution of batch
    return {
        "success": True,
        "parallel_foreach_batch": {
            "items": current_batch,
            "batch_indices": list(range(index, batch_end)),
            "body_port": "body",
        },
        "next_nodes": [],  # Executor handles this
    }
```

## File Structure

```
src/casare_rpa/nodes/
└── parallel_nodes.py          # ForkNode, JoinNode, ParallelForEachNode

src/casare_rpa/presentation/canvas/visual_nodes/control_flow/
└── nodes.py                   # Add visual nodes (existing file)

src/casare_rpa/application/use_cases/
└── execute_workflow.py        # Modify for parallel support

src/casare_rpa/infrastructure/execution/
└── execution_context.py       # Add clone_for_branch()

tests/nodes/
└── test_parallel_nodes.py     # Unit tests
```

## Implementation Order

1. [ ] Add `clone_for_branch()` to ExecutionContext
2. [ ] Create parallel_nodes.py with ForkNode, JoinNode, ParallelForEachNode
3. [ ] Modify execute_workflow.py for parallel branch handling
4. [ ] Add visual nodes to control_flow/nodes.py
5. [ ] Register nodes in __init__.py
6. [ ] Write unit tests
7. [ ] Integration test with sample parallel workflow

## Edge Cases

1. **Branch Failure**: If one branch fails, what happens?
   - Option A: Fail entire fork (strict)
   - Option B: Continue other branches, report failure (lenient)
   - **Decision**: Option B with `fail_fast` parameter (default: False)

2. **Nested Parallelism**: Fork inside Fork
   - Each level gets its own fork_id
   - Context cloning handles isolation

3. **Shared Resources**: Browser pages during parallel execution
   - Read-only access to shared browser
   - Each branch can create new pages
   - Cleanup responsibility on JoinNode

4. **Pause/Resume**: Pausing during parallel execution
   - Pause propagates to all branches
   - Resume continues all branches

## Questions Resolved

- ✅ Variable isolation: Context cloning with snapshot
- ✅ Result merging: Namespace by branch name + combined dict
- ✅ Error handling: Configurable fail_fast behavior
- ✅ Synchronization: JoinNode tracks completed branches
