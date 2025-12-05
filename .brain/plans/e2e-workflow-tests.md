# E2E Workflow Tests - Real Node Execution Without Mocks

## Overview

Create comprehensive end-to-end tests that execute **real workflows** with **real nodes**, **real connections**, and **real data** - NO MOCKS. Tests verify actual node behavior, data flow between connected nodes, and complete workflow execution.

## Scope

### What We're Testing
- **Real workflow creation** - Programmatic WorkflowSchema with nodes and connections
- **Real node execution** - Actual node.execute() with real ExecutionContext
- **Real data flow** - Variables passed between connected nodes
- **Real use cases** - Practical automation scenarios

### What We're NOT Mocking
- ExecutionContext (real)
- Node instances (real)
- Variable storage (real)
- Port connections (real)
- Execution orchestration (real)

### External Resources (Minimal Mocking)
For external I/O that can't run in CI:
- Browser/Playwright → Use headless mode or mock page responses
- Desktop/UIAutomation → Skip on non-Windows or use mock controls
- HTTP → Use httpbin.org or local mock server
- File I/O → Use temp directories with real files
- Database → Use SQLite in-memory

---

## Test Categories & Node Coverage

### 1. Core Logic Nodes (Pure - No External Deps)
**Priority: HIGH** - Can run anywhere, no external deps

| Node | Test Scenario |
|------|---------------|
| StartNode | Workflow entry point, triggers first connection |
| EndNode | Workflow termination, captures final state |
| SetVariableNode | Set string/int/list/dict variables |
| GetVariableNode | Retrieve variables, default values |
| IncrementVariableNode | Counter workflows |
| IfNode | Branching based on conditions |
| ForLoopStartNode/EndNode | Iterate over lists |
| WhileLoopStartNode/EndNode | Conditional loops |
| SwitchNode | Multi-branch routing |
| MergeNode | Merge parallel branches |
| TryNode/OnErrorNode | Error handling flows |
| RetryNode | Retry logic with limits |
| AssertNode | Validation assertions |
| BreakNode/ContinueNode | Loop control |

**E2E Workflow Tests:**
1. `test_variable_workflow` - Set, get, increment variables through 5 nodes
2. `test_conditional_branching` - If/Else with true/false paths
3. `test_for_loop_iteration` - Loop through list, accumulate results
4. `test_while_loop_counter` - While condition with break
5. `test_switch_routing` - Multi-case routing
6. `test_error_handling_flow` - Try, catch, recover
7. `test_nested_loops` - For loop inside for loop
8. `test_parallel_merge` - Fork, parallel execution, merge

### 2. Data Operation Nodes (Pure - No External Deps)
**Priority: HIGH**

| Node | Test Scenario |
|------|---------------|
| ConcatenateNode | String joining |
| FormatStringNode | Template formatting with variables |
| RegexMatchNode | Pattern matching |
| MathOperationNode | Add, subtract, multiply, divide |
| ComparisonNode | Compare values (==, !=, <, >, etc.) |
| CreateListNode | Build lists dynamically |
| JsonParseNode | Parse JSON strings |
| DictGetNode | Access dict keys |
| DictSetNode | Modify dict values |
| TypeConversionNode | Convert between types |

**E2E Workflow Tests:**
1. `test_string_processing_pipeline` - Concat → Format → Regex → Output
2. `test_math_calculation_chain` - Multiple math operations chained
3. `test_json_data_manipulation` - Parse → Get → Set → Serialize
4. `test_list_operations` - Create → Append → Filter → Map
5. `test_data_transformation_etl` - Extract → Transform → Load pattern

### 3. DateTime Nodes (Pure - Uses System Time)
**Priority: MEDIUM**

| Node | Test Scenario |
|------|---------------|
| GetCurrentDateTimeNode | Get current time |
| FormatDateTimeNode | Format datetime strings |
| ParseDateTimeNode | Parse date strings |
| DateTimeDifferenceNode | Calculate time deltas |
| AddToDateTimeNode | Add/subtract time |

**E2E Workflow Tests:**
1. `test_datetime_formatting_pipeline` - Get → Format → Store → Verify
2. `test_datetime_calculations` - Parse → Difference → Add → Compare

### 4. File Operation Nodes (Uses Temp Files)
**Priority: MEDIUM**

| Node | Test Scenario |
|------|---------------|
| ReadFileNode | Read text files |
| WriteFileNode | Write text files |
| ReadCSVNode | Parse CSV data |
| WriteCSVNode | Generate CSV files |
| ReadJSONNode | Load JSON files |
| WriteJSONNode | Save JSON files |
| FileExistsNode | Check file existence |
| CopyFileNode | Copy files |
| MoveFileNode | Move files |
| DeleteFileNode | Delete files |
| CreateDirectoryNode | Create folders |
| ListDirectoryNode | List folder contents |

**E2E Workflow Tests:**
1. `test_csv_etl_pipeline` - Read CSV → Transform → Write CSV
2. `test_json_config_workflow` - Read JSON → Modify → Save JSON
3. `test_file_management` - Create dir → Write → Copy → Move → Delete
4. `test_batch_file_processing` - List files → Loop → Process each

### 5. HTTP Nodes (Uses Real HTTP - httpbin.org)
**Priority: MEDIUM**

| Node | Test Scenario |
|------|---------------|
| HttpGetNode | GET request |
| HttpPostNode | POST with body |
| HttpPutNode | PUT request |
| HttpDeleteNode | DELETE request |

**E2E Workflow Tests:**
1. `test_rest_api_crud` - GET → POST → PUT → DELETE sequence
2. `test_http_error_handling` - Request → Check status → Retry if failed
3. `test_api_data_extraction` - GET → Parse JSON → Extract fields

### 6. Browser Nodes (Headless Playwright)
**Priority: HIGH** - Core RPA functionality

| Node | Test Scenario |
|------|---------------|
| LaunchBrowserNode | Start headless browser |
| GoToURLNode | Navigate to URL |
| ClickElementNode | Click elements |
| TypeTextNode | Enter text |
| ExtractTextNode | Get element text |
| GetAttributeNode | Get element attributes |
| WaitForElementNode | Wait for elements |
| ScreenshotNode | Take screenshots |
| CloseBrowserNode | Clean up browser |

**E2E Workflow Tests (using test HTML pages):**
1. `test_browser_navigation_flow` - Launch → Navigate → Screenshot → Close
2. `test_form_fill_submit` - Navigate → Type → Click → Verify
3. `test_data_scraping` - Navigate → Extract multiple elements → Store results
4. `test_multi_page_workflow` - Tab1 actions → Tab2 actions → Merge data

### 7. Desktop Nodes (Windows Only - Skip on CI)
**Priority: LOW** - Platform-specific

| Node | Test Scenario |
|------|---------------|
| LaunchApplicationNode | Start notepad/calc |
| MouseClickNode | Click coordinates |
| SendKeysNode | Send keystrokes |
| CloseApplicationNode | Close app |

**E2E Workflow Tests (Windows only):**
1. `test_notepad_automation` - Launch → Type → Save → Close
2. `test_calculator_automation` - Launch → Click buttons → Read result

---

## Implementation Plan

### Phase 1: Test Infrastructure (Day 1)
1. Create `tests/e2e/` directory structure
2. Create `tests/e2e/conftest.py` with real fixtures
3. Create `tests/e2e/helpers/workflow_builder.py` helper class
4. Create `tests/e2e/fixtures/` for test data files

### Phase 2: Core Logic E2E Tests (Day 1-2)
1. `tests/e2e/test_variable_workflows.py`
2. `tests/e2e/test_control_flow_workflows.py`
3. `tests/e2e/test_loop_workflows.py`
4. `tests/e2e/test_error_handling_workflows.py`

### Phase 3: Data Operation E2E Tests (Day 2)
1. `tests/e2e/test_string_workflows.py`
2. `tests/e2e/test_math_workflows.py`
3. `tests/e2e/test_json_workflows.py`
4. `tests/e2e/test_list_workflows.py`

### Phase 4: File Operation E2E Tests (Day 2-3)
1. `tests/e2e/test_file_workflows.py`
2. `tests/e2e/test_csv_workflows.py`
3. `tests/e2e/test_json_file_workflows.py`

### Phase 5: HTTP E2E Tests (Day 3)
1. `tests/e2e/test_http_workflows.py`

### Phase 6: Browser E2E Tests (Day 3-4)
1. `tests/e2e/test_browser_workflows.py`
2. `tests/e2e/fixtures/test_pages/` - HTML test pages

### Phase 7: Integration & Cleanup (Day 4)
1. Add markers for platform-specific tests
2. Add CI configuration
3. Documentation

---

## Test File Structure

```
tests/e2e/
├── conftest.py                    # Real fixtures (no mocks)
├── helpers/
│   ├── __init__.py
│   └── workflow_builder.py        # Fluent workflow builder
├── fixtures/
│   ├── __init__.py
│   ├── test_data.csv
│   ├── test_config.json
│   └── test_pages/
│       ├── form.html
│       ├── table.html
│       └── dynamic.html
├── test_variable_workflows.py     # SetVar, GetVar, Increment
├── test_control_flow_workflows.py # If, Switch, Merge
├── test_loop_workflows.py         # For, While, Break, Continue
├── test_error_handling_workflows.py # Try, Catch, Retry
├── test_string_workflows.py       # Concat, Format, Regex
├── test_math_workflows.py         # Math operations
├── test_json_workflows.py         # JSON parse, dict operations
├── test_list_workflows.py         # List operations
├── test_datetime_workflows.py     # DateTime operations
├── test_file_workflows.py         # File R/W operations
├── test_csv_workflows.py          # CSV processing
├── test_http_workflows.py         # HTTP requests
├── test_browser_workflows.py      # Browser automation
└── test_desktop_workflows.py      # Desktop automation (Windows)
```

---

## Helper Class Design

```python
# tests/e2e/helpers/workflow_builder.py

class WorkflowBuilder:
    """Fluent builder for creating test workflows."""

    def __init__(self, name: str):
        self.workflow = WorkflowSchema(
            metadata=WorkflowMetadata(name=name, description="E2E Test")
        )
        self._node_counter = 0
        self._last_node_id: str | None = None

    def add_start(self) -> "WorkflowBuilder":
        """Add StartNode as entry point."""
        node_id = self._gen_id("start")
        self.workflow.add_node({
            "node_id": node_id,
            "node_type": "StartNode",
            "config": {}
        })
        self._last_node_id = node_id
        return self

    def add_set_variable(self, name: str, value: Any) -> "WorkflowBuilder":
        """Add SetVariableNode."""
        node_id = self._gen_id("set_var")
        self.workflow.add_node({
            "node_id": node_id,
            "node_type": "SetVariableNode",
            "config": {
                "variable_name": name,
                "variable_type": self._infer_type(value)
            }
        })
        self._auto_connect(node_id)
        return self

    def add_if(self, condition: str) -> "WorkflowBuilder":
        """Add IfNode with condition."""
        ...

    def add_for_loop(self, variable: str, list_variable: str) -> "WorkflowBuilder":
        """Add ForLoopStartNode."""
        ...

    def add_end(self) -> "WorkflowBuilder":
        """Add EndNode."""
        ...

    def connect(self, from_id: str, from_port: str, to_id: str, to_port: str) -> "WorkflowBuilder":
        """Manually add connection."""
        self.workflow.add_connection(NodeConnection(from_id, from_port, to_id, to_port))
        return self

    def build(self) -> WorkflowSchema:
        """Return completed workflow."""
        return self.workflow

    async def execute(self, initial_vars: dict = None) -> dict:
        """Build and execute workflow, return results."""
        workflow = self.build()
        use_case = ExecuteWorkflowUseCase(workflow, initial_vars or {})
        try:
            return await use_case.execute()
        finally:
            await use_case.context.cleanup()
```

---

## Example Test Cases

### 1. Variable Workflow

```python
# tests/e2e/test_variable_workflows.py

@pytest.mark.asyncio
async def test_set_get_increment_variable_chain():
    """
    Workflow:
    Start → SetVar(counter=0) → Increment(counter) → Increment(counter) → End

    Expected: counter = 2
    """
    builder = WorkflowBuilder("Variable Chain")

    result = await (
        builder
        .add_start()
        .add_set_variable("counter", 0)
        .add_increment_variable("counter")
        .add_increment_variable("counter")
        .add_end()
        .execute()
    )

    assert result["success"] is True
    assert result["variables"]["counter"] == 2
```

### 2. Conditional Branching

```python
@pytest.mark.asyncio
async def test_if_else_branching_true_path():
    """
    Workflow:
                    ┌─ (true) → SetVar(path="true") ─┐
    Start → If(x>5) ┤                                 ├→ Merge → End
                    └─ (false) → SetVar(path="false")─┘

    Input: x=10
    Expected: path = "true"
    """
    builder = WorkflowBuilder("Conditional Branch")

    result = await (
        builder
        .add_start()
        .add_if("{{x}} > 5")
        .on_true().add_set_variable("path", "true").end_branch()
        .on_false().add_set_variable("path", "false").end_branch()
        .add_merge()
        .add_end()
        .execute(initial_vars={"x": 10})
    )

    assert result["variables"]["path"] == "true"
```

### 3. For Loop with Accumulator

```python
@pytest.mark.asyncio
async def test_for_loop_sum_numbers():
    """
    Workflow:
    Start → SetVar(sum=0) → ForLoop(items=[1,2,3,4,5]) →
        Math(sum = sum + item) → EndLoop → End

    Expected: sum = 15
    """
    result = await (
        WorkflowBuilder("Sum Numbers")
        .add_start()
        .add_set_variable("sum", 0)
        .add_set_variable("items", [1, 2, 3, 4, 5])
        .add_for_loop("item", "items")
        .add_math_operation("sum", "{{sum}} + {{item}}")
        .add_for_loop_end()
        .add_end()
        .execute()
    )

    assert result["variables"]["sum"] == 15
```

### 4. File CSV ETL Pipeline

```python
@pytest.mark.asyncio
async def test_csv_etl_pipeline(tmp_path):
    """
    Workflow:
    Start → ReadCSV(input.csv) → ForLoop(rows) →
        Transform(uppercase name) → WriteCSV(output.csv) → End
    """
    # Create input CSV
    input_csv = tmp_path / "input.csv"
    input_csv.write_text("name,age\njohn,25\njane,30\n")

    result = await (
        WorkflowBuilder("CSV ETL")
        .add_start()
        .add_read_csv(str(input_csv), "data")
        .add_for_loop("row", "data")
        .add_string_operation("row.name", "upper")
        .add_for_loop_end()
        .add_write_csv(str(tmp_path / "output.csv"), "data")
        .add_end()
        .execute()
    )

    output_csv = tmp_path / "output.csv"
    assert output_csv.exists()
    content = output_csv.read_text()
    assert "JOHN" in content
    assert "JANE" in content
```

### 5. Browser Form Automation

```python
@pytest.mark.asyncio
async def test_browser_form_fill_and_submit(test_server):
    """
    Workflow:
    Start → LaunchBrowser(headless) → Navigate(form.html) →
        TypeText(#name, "John") → TypeText(#email, "john@test.com") →
        Click(#submit) → ExtractText(.result) → CloseBrowser → End
    """
    result = await (
        WorkflowBuilder("Form Automation")
        .add_start()
        .add_launch_browser(headless=True)
        .add_navigate(f"{test_server.url}/form.html")
        .add_type_text("#name", "John Doe")
        .add_type_text("#email", "john@test.com")
        .add_click("#submit")
        .add_wait_for_element(".result")
        .add_extract_text(".result", "confirmation")
        .add_close_browser()
        .add_end()
        .execute()
    )

    assert result["success"] is True
    assert "John Doe" in result["variables"]["confirmation"]
```

---

## Markers & CI Integration

```python
# pytest.ini or pyproject.toml
[tool.pytest.ini_options]
markers = [
    "e2e: End-to-end workflow tests",
    "slow: Slow-running tests",
    "browser: Browser automation tests (requires Playwright)",
    "desktop: Desktop automation tests (Windows only)",
    "http: HTTP tests (requires network)",
]
```

```yaml
# .github/workflows/e2e-tests.yml
name: E2E Tests
on: [push, pull_request]
jobs:
  e2e:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -e ".[dev]"
      - run: playwright install chromium
      - run: pytest tests/e2e/ -v -m "e2e and not desktop"
```

---

## Unresolved Questions

1. **Browser test infrastructure**: Use built-in test server (aiohttp) or pytest-aiohttp?
2. **HTTP tests**: Use httpbin.org (external) or local mock server?
3. **Desktop tests**: How to run on CI? Use GitHub Actions Windows runner?
4. **Execution timeout**: What default timeout for E2E workflows? 30s? 60s?
5. **Parallel execution**: Should tests run in parallel or sequential?
6. **Resource cleanup**: How to ensure browser/file cleanup on test failure?

---

## Success Criteria

- [ ] 50+ E2E tests covering all major node categories
- [ ] All tests pass on Windows with Python 3.12
- [ ] Browser tests run headless in CI
- [ ] No flaky tests (3 consecutive green runs)
- [ ] Test execution time < 5 minutes total
- [ ] Clear failure messages with workflow context
