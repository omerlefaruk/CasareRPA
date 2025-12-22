---
skill: chain-tester
description: Node chain testing templates for quality agent. WorkflowBuilder patterns, tier-based testing (simple/complex/full), and assertion patterns.
---

Templates for testing node chains with REAL nodes. Mock ONLY external I/O.

## Testing Tiers

| Tier | Nodes | Complexity | Marker |
|------|-------|------------|--------|
| Simple | 2-3 | Linear flow | (none) |
| Complex | 5-10 | Branching, loops | (none) |
| Full | 10+ | Multi-branch workflows | `@pytest.mark.slow` |

## WorkflowBuilder API

```python
from tests.nodes.chain.conftest import WorkflowBuilder, chain_executor

# Fluent API for building test workflows
chain = WorkflowBuilder() \
    .add(StartNode(), id="start") \
    .add(SomeNode(param="value"), id="action") \
    .add(EndNode(), id="end") \
    .connect("start", "action") \
    .connect("action", "end") \
    .build()
```

## Simple Chain Templates

### Start → Action → End

```python
@pytest.mark.asyncio
async def test_basic_linear_chain(chain_executor):
    """2-3 nodes, linear flow."""
    chain = WorkflowBuilder() \
        .add(StartNode(), id="start") \
        .add(SetVariableNode(name="x", value=42), id="set") \
        .add(EndNode(), id="end") \
        .connect_sequential() \
        .build()

    result = await chain_executor.execute(chain)

    assert result.status == ExecutionStatus.COMPLETED
    assert result.context.variables["x"] == 42
```

### Variable Passing

```python
@pytest.mark.asyncio
async def test_variable_flows_through_chain(chain_executor):
    chain = WorkflowBuilder() \
        .add(StartNode(), id="start") \
        .add(SetVariableNode(name="input", value="hello"), id="set1") \
        .add(TransformNode(input_var="input", output_var="output", transform="upper"), id="transform") \
        .add(EndNode(), id="end") \
        .connect_sequential() \
        .build()

    result = await chain_executor.execute(chain)

    assert result.context.variables["output"] == "HELLO"
```

## Complex Chain Templates

### If Branching

```python
@pytest.mark.asyncio
async def test_if_true_branch(chain_executor):
    chain = WorkflowBuilder() \
        .add(StartNode(), id="start") \
        .add(IfNode(condition="x > 10"), id="if") \
        .add(SetVariableNode(name="result", value="big"), id="true_branch") \
        .add(SetVariableNode(name="result", value="small"), id="false_branch") \
        .add(EndNode(), id="end") \
        .connect("start", "if") \
        .connect("if.true", "true_branch") \
        .connect("if.false", "false_branch") \
        .connect(["true_branch", "false_branch"], "end") \
        .build()

    result = await chain_executor.execute(chain, variables={"x": 15})

    assert result.context.variables["result"] == "big"


@pytest.mark.asyncio
async def test_if_false_branch(chain_executor):
    # Same chain, different input
    result = await chain_executor.execute(chain, variables={"x": 5})

    assert result.context.variables["result"] == "small"
```

### For Loop

```python
@pytest.mark.asyncio
async def test_for_loop_iteration(chain_executor):
    chain = WorkflowBuilder() \
        .add(StartNode(), id="start") \
        .add(SetVariableNode(name="sum", value=0), id="init") \
        .add(ForEachNode(items=[1, 2, 3], item_var="i"), id="loop") \
        .add(IncrementNode(var="sum", by_var="i"), id="add") \
        .add(EndNode(), id="end") \
        .connect("start", "init") \
        .connect("init", "loop") \
        .connect("loop.body", "add") \
        .connect("add", "loop.next") \
        .connect("loop.done", "end") \
        .build()

    result = await chain_executor.execute(chain)

    assert result.context.variables["sum"] == 6  # 1+2+3
```

### Try-Catch

```python
@pytest.mark.asyncio
async def test_try_catch_handles_error(chain_executor, mock_page):
    mock_page.click.side_effect = Exception("Element not found")

    chain = WorkflowBuilder() \
        .add(StartNode(), id="start") \
        .add(TryCatchNode(), id="try") \
        .add(ClickNode(selector="#missing"), id="risky") \
        .add(SetVariableNode(name="status", value="success"), id="success") \
        .add(SetVariableNode(name="status", value="failed"), id="catch") \
        .add(EndNode(), id="end") \
        .connect("start", "try") \
        .connect("try.body", "risky") \
        .connect("risky", "success") \
        .connect("try.catch", "catch") \
        .connect(["success", "catch"], "end") \
        .build()

    result = await chain_executor.execute(chain)

    assert result.context.variables["status"] == "failed"
    assert result.status == ExecutionStatus.COMPLETED  # Not failed!
```

## Full Workflow Templates

### Browser Automation Chain

```python
@pytest.mark.slow
@pytest.mark.asyncio
async def test_browser_login_workflow(chain_executor, mock_page, mock_browser):
    """10+ nodes: navigate, fill form, click, wait, extract."""
    chain = WorkflowBuilder() \
        .add(StartNode(), id="start") \
        .add(OpenBrowserNode(), id="browser") \
        .add(NavigateNode(url="https://example.com/login"), id="nav") \
        .add(WaitForSelectorNode(selector="#username"), id="wait1") \
        .add(TypeNode(selector="#username", text="user@test.com"), id="type_user") \
        .add(TypeNode(selector="#password", text="password123"), id="type_pass") \
        .add(ClickNode(selector="#submit"), id="submit") \
        .add(WaitForNavigationNode(), id="wait_nav") \
        .add(ExtractTextNode(selector=".welcome", output_var="greeting"), id="extract") \
        .add(CloseBrowserNode(), id="close") \
        .add(EndNode(), id="end") \
        .connect_sequential() \
        .build()

    result = await chain_executor.execute(chain)

    assert result.status == ExecutionStatus.COMPLETED
    assert "Welcome" in result.context.variables["greeting"]
```

### Data Processing Chain

```python
@pytest.mark.slow
@pytest.mark.asyncio
async def test_data_pipeline(chain_executor):
    """Multi-step data transformation."""
    chain = WorkflowBuilder() \
        .add(StartNode(), id="start") \
        .add(ReadCSVNode(path="input.csv", output_var="data"), id="read") \
        .add(ForEachNode(items_var="data", item_var="row"), id="loop") \
        .add(TransformNode(input_var="row", transform="clean"), id="clean") \
        .add(ValidateNode(input_var="row", rules=["not_empty"]), id="validate") \
        .add(IfNode(condition="valid"), id="check") \
        .add(AppendToListNode(list_var="results", item_var="row"), id="append") \
        .add(LogNode(message="Invalid row skipped"), id="skip") \
        .add(WriteCSVNode(data_var="results", path="output.csv"), id="write") \
        .add(EndNode(), id="end") \
        .connect("start", "read") \
        .connect("read", "loop") \
        .connect("loop.body", "clean") \
        .connect("clean", "validate") \
        .connect("validate", "check") \
        .connect("check.true", "append") \
        .connect("check.false", "skip") \
        .connect(["append", "skip"], "loop.next") \
        .connect("loop.done", "write") \
        .connect("write", "end") \
        .build()

    result = await chain_executor.execute(chain)

    assert result.status == ExecutionStatus.COMPLETED
```

## Assertion Patterns

### Status Assertions

```python
# ChainExecutionResult from tests/nodes/chain/conftest.py

# Workflow completed successfully
assert result.success is True

# Workflow failed
assert result.success is False
```

### Variable Assertions

```python
# Check final variables after execution
assert result.final_variables["output"] == expected_value

# Check variable type
assert isinstance(result.final_variables["list"], list)

# Check variable not set (for error paths)
assert "output" not in result.final_variables
```

### Execution Assertions

```python
# Check node was executed (list of NodeId)
assert "node_id" in result.nodes_executed

# Check node count
assert len(result.nodes_executed) == 5

# Check specific node result
assert result.node_results["set_x"]["success"] is True
assert result.node_results["get_x"]["data"]["value"] == 42
```

### Error Assertions

```python
# Check errors list (tuples of node_id, error_message)
assert len(result.errors) > 0
assert any("timeout" in err[1].lower() for err in result.errors)

# Check which node failed
node_id, error_msg = result.errors[0]
assert node_id == "problematic_node"
```

## Mock Setup for Chains

```python
@pytest.fixture
def chain_with_browser_mocks(chain_executor, mock_page, mock_browser):
    """Pre-configured chain executor with browser mocks."""
    chain_executor.context.resources["browser"] = mock_browser
    chain_executor.context.resources["page"] = mock_page
    return chain_executor


@pytest.mark.asyncio
async def test_with_mocks(chain_with_browser_mocks):
    chain = WorkflowBuilder()...
    result = await chain_with_browser_mocks.execute(chain)
```

## File Structure

```
tests/nodes/chain/
├── conftest.py              # WorkflowBuilder, chain_executor fixtures
├── test_simple_chains.py    # 2-3 node linear chains
├── test_complex_chains.py   # 5-10 node branching chains
└── test_full_workflows.py   # 10+ node complete workflows (@pytest.mark.slow)
```
