# CasareRPA AI Assistant - Workflow Standards

> **Purpose:** This document provides the CasareRPA Genius AI Assistant with comprehensive knowledge of node types, workflow schemas, robustness patterns, and topology rules for generating valid, production-ready workflows.

---

## Table of Contents

1. [Workflow JSON Schema](#1-workflow-json-schema)
2. [Node Registry Reference](#2-node-registry-reference)
3. [Common Node Signatures](#3-common-node-signatures)
4. [Robustness Protocol](#4-robustness-protocol)
5. [Topology Rules](#5-topology-rules)
6. [Connection Patterns](#6-connection-patterns)
7. [Best Practices](#7-best-practices)
8. [Missing Node Protocol](#8-missing-node-protocol) *(NEW)*

---

## 1. Workflow JSON Schema

### Complete Schema Structure

```json
{
  "metadata": {
    "name": "string (1-256 chars, required)",
    "description": "string (optional, max 10000 chars)",
    "version": "string (semver format: 1.0.0)",
    "author": "string (optional)",
    "tags": ["string"]
  },
  "nodes": {
    "<node_id>": {
      "node_id": "string (must match dict key, alphanumeric with _ or -)",
      "node_type": "string (PascalCase ending with 'Node')",
      "config": {},
      "position": [x, y]
    }
  },
  "connections": [
    {
      "source_node": "string (node_id)",
      "source_port": "string (snake_case port name)",
      "target_node": "string (node_id)",
      "target_port": "string (snake_case port name)"
    }
  ],
  "variables": {
    "<variable_name>": "any"
  },
  "settings": {
    "stop_on_error": true,
    "timeout": 30,
    "retry_count": 0
  }
}
```

### Security Constraints

| Constraint | Limit | Reason |
|------------|-------|--------|
| Maximum nodes | 1000 | Prevent resource exhaustion |
| Maximum connections | 5000 | Prevent graph explosion |
| Max node_id length | 256 chars | Storage efficiency |
| Max string length | 10000 chars | Memory protection |
| Max config depth | 10 levels | Prevent deep nesting attacks |

### Validation Rules

1. **node_id format**: Must match regex `^[a-zA-Z0-9_-]+$`
2. **node_type format**: Must match regex `^[A-Z][a-zA-Z0-9]*Node$`
3. **port names**: Must be snake_case matching `^[a-z][a-z0-9_]*$`
4. **node_id consistency**: Dict key must equal `node.node_id`
5. **connection validity**: All referenced node IDs must exist in `nodes`

### Dangerous Patterns (Blocked)

The following patterns are blocked in all string fields:
- `__import__`, `eval(`, `exec(`, `compile(`
- `os.system`, `subprocess.`, `open(`, `pickle.`
- `marshal.`, `__builtins__`, `__globals__`

---

## 2. Node Registry Reference

### Node Categories

| Category | Description | Example Nodes |
|----------|-------------|---------------|
| `control_flow` | Workflow control | StartNode, EndNode, IfNode, ForLoopStartNode |
| `browser` | Web automation | LaunchBrowserNode, ClickElementNode, TypeTextNode |
| `file` | File operations | ReadFileNode, WriteFileNode, ReadCSVNode |
| `data` | Variables | SetVariableNode, GetVariableNode |
| `data_operation` | String/List/Dict | ConcatenateNode, JsonParseNode, DictGetNode |
| `http` | REST API | HttpRequestNode, HttpDownloadFileNode |
| `database` | SQL operations | DatabaseConnectNode, ExecuteQueryNode |
| `system` | OS operations | ClipboardCopyNode, RunCommandNode |
| `google` | Google services | GmailSendEmailNode, SheetsGetRangeNode |
| `messaging` | Chat platforms | TelegramSendMessageNode, WhatsAppSendMessageNode |
| `desktop` | Desktop automation | LaunchApplicationNode, FindElementNode |
| `ai_ml` | AI integration | LLMCompletionNode, LLMExtractDataNode |
| `triggers` | Event triggers | WebhookTriggerNode, ScheduleTriggerNode |

### Port Types

| Port Type | Purpose | Data Flow |
|-----------|---------|-----------|
| `EXEC_INPUT` | Execution flow in | `exec_in` |
| `EXEC_OUTPUT` | Execution flow out | `exec_out`, `true`, `false`, `body`, `completed` |
| `INPUT` | Data input | Any data port |
| `OUTPUT` | Data output | Any data port |

### Data Types

| Type | Description | Example Values |
|------|-------------|----------------|
| `STRING` | Text data | `"hello"` |
| `INTEGER` | Whole numbers | `42` |
| `FLOAT` | Decimal numbers | `3.14` |
| `BOOLEAN` | True/False | `true` |
| `LIST` | Arrays | `[1, 2, 3]` |
| `DICT` | Objects | `{"key": "value"}` |
| `ANY` | Any type | Variable content |
| `BROWSER` | Browser instance | Playwright Browser |
| `PAGE` | Page instance | Playwright Page |

---

## 3. Common Node Signatures

### Control Flow Nodes

#### StartNode
Entry point for workflow execution. Every workflow must have exactly one.

```json
{
  "node_id": "start",
  "node_type": "StartNode",
  "config": {},
  "position": [0, 0]
}
```

| Port | Type | Direction | Description |
|------|------|-----------|-------------|
| `exec_out` | EXEC_OUTPUT | out | Workflow execution begins |

#### EndNode
Exit point for workflow execution. Can have multiple.

```json
{
  "node_id": "end",
  "node_type": "EndNode",
  "config": {},
  "position": [0, 600]
}
```

| Port | Type | Direction | Description |
|------|------|-----------|-------------|
| `exec_in` | EXEC_INPUT | in | Workflow execution ends |

#### IfNode
Conditional branching based on expression evaluation.

```json
{
  "node_id": "check_condition",
  "node_type": "IfNode",
  "config": {
    "expression": "{{counter}} > 10"
  },
  "position": [0, 150]
}
```

| Port | Type | Direction | Description |
|------|------|-----------|-------------|
| `exec_in` | EXEC_INPUT | in | Execution input |
| `condition` | INPUT (ANY) | in | Boolean condition (optional) |
| `true` | EXEC_OUTPUT | out | Condition is true |
| `false` | EXEC_OUTPUT | out | Condition is false |

#### ForLoopStartNode
Iterates over collections or ranges. Must pair with ForLoopEndNode.

```json
{
  "node_id": "loop_start",
  "node_type": "ForLoopStartNode",
  "config": {
    "mode": "items",
    "item_var": "item"
  },
  "position": [0, 150]
}
```

| Port | Type | Direction | Description |
|------|------|-----------|-------------|
| `exec_in` | EXEC_INPUT | in | Start loop |
| `items` | INPUT (ANY) | in | Collection to iterate |
| `end` | INPUT (INTEGER) | in | End value for range mode |
| `body` | EXEC_OUTPUT | out | Loop body execution |
| `completed` | EXEC_OUTPUT | out | Loop finished |
| `current_item` | OUTPUT (ANY) | out | Current iteration item |
| `current_index` | OUTPUT (INTEGER) | out | Current iteration index |

**Config Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `mode` | choice | `"items"` | `"items"` or `"range"` |
| `list_var` | string | `""` | Variable name for list (items mode) |
| `item_var` | string | `"item"` | Variable to store current item |
| `start` | integer | `0` | Start value (range mode) |
| `end` | integer | `10` | End value (range mode) |
| `step` | integer | `1` | Step value (range mode) |

#### ForLoopEndNode
Marks end of loop body. Automatically loops back to paired ForLoopStartNode.

```json
{
  "node_id": "loop_end",
  "node_type": "ForLoopEndNode",
  "config": {
    "paired_start_id": "loop_start"
  },
  "position": [0, 450]
}
```

#### WhileLoopStartNode
Condition-based loop with safety limit.

```json
{
  "node_id": "while_loop",
  "node_type": "WhileLoopStartNode",
  "config": {
    "expression": "{{counter}} < 100",
    "max_iterations": 1000
  },
  "position": [0, 150]
}
```

#### TryNode
Error handling - wraps risky operations.

```json
{
  "node_id": "try_block",
  "node_type": "TryNode",
  "config": {},
  "position": [0, 150]
}
```

| Port | Type | Direction | Description |
|------|------|-----------|-------------|
| `exec_in` | EXEC_INPUT | in | Start try block |
| `try_body` | EXEC_OUTPUT | out | Protected code path |
| `exec_out` | EXEC_OUTPUT | out | Normal completion |

#### CatchNode
Handles errors from paired TryNode.

```json
{
  "node_id": "catch_block",
  "node_type": "CatchNode",
  "config": {
    "error_types": ""
  },
  "position": [400, 150]
}
```

| Port | Type | Direction | Description |
|------|------|-----------|-------------|
| `exec_in` | EXEC_INPUT | in | Error received |
| `catch_body` | EXEC_OUTPUT | out | Error handling code |
| `error_message` | OUTPUT (STRING) | out | Error message |
| `error_type` | OUTPUT (STRING) | out | Error type name |
| `stack_trace` | OUTPUT (STRING) | out | Full stack trace |

#### FinallyNode
Always executes after Try/Catch regardless of errors.

```json
{
  "node_id": "finally_block",
  "node_type": "FinallyNode",
  "config": {},
  "position": [800, 150]
}
```

| Port | Type | Direction | Description |
|------|------|-----------|-------------|
| `exec_in` | EXEC_INPUT | in | Execute cleanup |
| `finally_body` | EXEC_OUTPUT | out | Cleanup code path |
| `had_error` | OUTPUT (BOOLEAN) | out | Whether error occurred |

### Variable Nodes

#### SetVariableNode
Stores a value in workflow context.

```json
{
  "node_id": "set_counter",
  "node_type": "SetVariableNode",
  "config": {
    "variable_name": "counter",
    "default_value": 0,
    "variable_type": "Int32"
  },
  "position": [0, 150]
}
```

| Port | Type | Direction | Description |
|------|------|-----------|-------------|
| `exec_in` | EXEC_INPUT | in | Execution input |
| `value` | INPUT (ANY) | in | Value to store (optional) |
| `exec_out` | EXEC_OUTPUT | out | Execution continues |
| `value` | OUTPUT (ANY) | out | Stored value |

**Variable Types:** `String`, `Boolean`, `Int32`, `Float`, `Object`, `Array`, `List`, `Dict`, `FilePath`, `DataTable`

#### GetVariableNode
Retrieves a value from workflow context.

```json
{
  "node_id": "get_counter",
  "node_type": "GetVariableNode",
  "config": {
    "variable_name": "counter",
    "default_value": 0
  },
  "position": [0, 150]
}
```

### Browser Nodes

#### LaunchBrowserNode
Opens a browser instance.

```json
{
  "node_id": "launch_browser",
  "node_type": "LaunchBrowserNode",
  "config": {
    "url": "https://example.com",
    "browser_type": "chromium",
    "headless": false,
    "window_state": "maximized"
  },
  "position": [0, 150]
}
```

| Port | Type | Direction | Description |
|------|------|-----------|-------------|
| `exec_in` | EXEC_INPUT | in | Execution input |
| `url` | INPUT (STRING) | in | Initial URL (optional) |
| `exec_out` | EXEC_OUTPUT | out | Browser launched |
| `browser` | OUTPUT (BROWSER) | out | Browser instance |
| `page` | OUTPUT (PAGE) | out | Initial page |
| `window` | OUTPUT (ANY) | out | Desktop window handle |

**Key Config Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | string | `""` | Initial URL to navigate |
| `browser_type` | choice | `"chromium"` | `chromium`, `firefox`, `webkit` |
| `headless` | boolean | `false` | Run without UI |
| `window_state` | choice | `"normal"` | `normal`, `maximized`, `minimized` |
| `viewport_width` | integer | `1280` | Browser width |
| `viewport_height` | integer | `720` | Browser height |
| `timeout` | integer | `30000` | Default timeout (ms) |

#### GoToURLNode
Navigates to a URL.

```json
{
  "node_id": "navigate",
  "node_type": "GoToURLNode",
  "config": {
    "url": "https://example.com/login"
  },
  "position": [0, 300]
}
```

| Port | Type | Direction | Description |
|------|------|-----------|-------------|
| `exec_in` | EXEC_INPUT | in | Execution input |
| `url` | INPUT (STRING) | in | Target URL |
| `page` | INPUT (PAGE) | in | Page to navigate (optional) |
| `exec_out` | EXEC_OUTPUT | out | Navigation complete |
| `page` | OUTPUT (PAGE) | out | Navigated page |

#### ClickElementNode
Clicks an element on the page.

```json
{
  "node_id": "click_login",
  "node_type": "ClickElementNode",
  "config": {
    "selector": "#login-button",
    "timeout": 5000,
    "force": false
  },
  "position": [0, 450]
}
```

| Port | Type | Direction | Description |
|------|------|-----------|-------------|
| `exec_in` | EXEC_INPUT | in | Execution input |
| `selector` | INPUT (STRING) | in | CSS/XPath selector |
| `page` | INPUT (PAGE) | in | Page context (optional) |
| `exec_out` | EXEC_OUTPUT | out | Click complete |

**Key Config Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `selector` | string | required | CSS or XPath selector |
| `timeout` | integer | `30000` | Wait timeout (ms) |
| `force` | boolean | `false` | Force click even if not visible |
| `click_count` | integer | `1` | Number of clicks |
| `button` | choice | `"left"` | `left`, `right`, `middle` |

#### TypeTextNode
Types text into an input element.

```json
{
  "node_id": "type_username",
  "node_type": "TypeTextNode",
  "config": {
    "selector": "#username",
    "text": "{{username}}",
    "clear_first": true
  },
  "position": [0, 600]
}
```

| Port | Type | Direction | Description |
|------|------|-----------|-------------|
| `exec_in` | EXEC_INPUT | in | Execution input |
| `selector` | INPUT (STRING) | in | Element selector |
| `text` | INPUT (STRING) | in | Text to type |
| `page` | INPUT (PAGE) | in | Page context (optional) |
| `exec_out` | EXEC_OUTPUT | out | Typing complete |

**Key Config Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `selector` | string | required | CSS or XPath selector |
| `text` | string | required | Text to type (supports `{{variables}}`) |
| `clear_first` | boolean | `true` | Clear existing text first |
| `delay` | integer | `0` | Delay between keystrokes (ms) |

#### WaitForElementNode
Waits for an element to appear.

```json
{
  "node_id": "wait_for_result",
  "node_type": "WaitForElementNode",
  "config": {
    "selector": ".success-message",
    "timeout": 10000,
    "state": "visible"
  },
  "position": [0, 750]
}
```

**State Options:** `attached`, `detached`, `visible`, `hidden`

#### ExtractTextNode
Extracts text content from an element.

```json
{
  "node_id": "extract_result",
  "node_type": "ExtractTextNode",
  "config": {
    "selector": ".result-value"
  },
  "position": [0, 300]
}
```

| Port | Type | Direction | Description |
|------|------|-----------|-------------|
| `exec_in` | EXEC_INPUT | in | Execution input |
| `selector` | INPUT (STRING) | in | Element selector |
| `exec_out` | EXEC_OUTPUT | out | Extraction complete |
| `text` | OUTPUT (STRING) | out | Extracted text |

### File Nodes

#### ReadFileNode
Reads file contents.

```json
{
  "node_id": "read_config",
  "node_type": "ReadFileNode",
  "config": {
    "file_path": "C:/config/settings.txt",
    "encoding": "utf-8"
  },
  "position": [0, 150]
}
```

| Port | Type | Direction | Description |
|------|------|-----------|-------------|
| `exec_in` | EXEC_INPUT | in | Execution input |
| `file_path` | INPUT (STRING) | in | File path |
| `exec_out` | EXEC_OUTPUT | out | Read complete |
| `content` | OUTPUT (STRING) | out | File contents |
| `success` | OUTPUT (BOOLEAN) | out | Operation result |

#### WriteFileNode
Writes content to a file.

```json
{
  "node_id": "write_output",
  "node_type": "WriteFileNode",
  "config": {
    "file_path": "C:/output/result.txt",
    "content": "{{result_data}}",
    "create_directory": true
  },
  "position": [0, 300]
}
```

#### ReadCSVNode
Reads and parses CSV files.

```json
{
  "node_id": "read_data",
  "node_type": "ReadCSVNode",
  "config": {
    "file_path": "C:/data/input.csv",
    "has_header": true,
    "delimiter": ","
  },
  "position": [0, 150]
}
```

| Port | Type | Direction | Description |
|------|------|-----------|-------------|
| `exec_in` | EXEC_INPUT | in | Execution input |
| `file_path` | INPUT (STRING) | in | CSV file path |
| `exec_out` | EXEC_OUTPUT | out | Read complete |
| `data` | OUTPUT (LIST) | out | Parsed rows |
| `headers` | OUTPUT (LIST) | out | Column headers |
| `row_count` | OUTPUT (INTEGER) | out | Number of rows |

#### WriteCSVNode
Writes data to CSV format.

```json
{
  "node_id": "write_results",
  "node_type": "WriteCSVNode",
  "config": {
    "file_path": "C:/output/results.csv",
    "include_header": true
  },
  "position": [0, 450]
}
```

### Data Operation Nodes

#### RegexMatchNode
Extracts text using regular expressions.

```json
{
  "node_id": "extract_email",
  "node_type": "RegexMatchNode",
  "config": {
    "pattern": "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}",
    "find_all": true
  },
  "position": [0, 300]
}
```

| Port | Type | Direction | Description |
|------|------|-----------|-------------|
| `exec_in` | EXEC_INPUT | in | Execution input |
| `text` | INPUT (STRING) | in | Text to search |
| `pattern` | INPUT (STRING) | in | Regex pattern |
| `exec_out` | EXEC_OUTPUT | out | Match complete |
| `matches` | OUTPUT (LIST) | out | All matches |
| `match` | OUTPUT (STRING) | out | First match |
| `groups` | OUTPUT (LIST) | out | Capture groups |

#### JsonParseNode
Parses JSON string to object.

```json
{
  "node_id": "parse_response",
  "node_type": "JsonParseNode",
  "config": {},
  "position": [0, 300]
}
```

| Port | Type | Direction | Description |
|------|------|-----------|-------------|
| `exec_in` | EXEC_INPUT | in | Execution input |
| `json_string` | INPUT (STRING) | in | JSON string |
| `exec_out` | EXEC_OUTPUT | out | Parse complete |
| `result` | OUTPUT (ANY) | out | Parsed object |

#### DictGetNode
Gets a value from a dictionary by key.

```json
{
  "node_id": "get_user_name",
  "node_type": "DictGetNode",
  "config": {
    "key": "name",
    "default_value": "Unknown"
  },
  "position": [0, 450]
}
```

| Port | Type | Direction | Description |
|------|------|-----------|-------------|
| `exec_in` | EXEC_INPUT | in | Execution input |
| `dict` | INPUT (DICT) | in | Dictionary object |
| `key` | INPUT (STRING) | in | Key to retrieve |
| `exec_out` | EXEC_OUTPUT | out | Get complete |
| `value` | OUTPUT (ANY) | out | Retrieved value |

### Error Handling Nodes

#### LogNode
Logs a message for debugging.

```json
{
  "node_id": "log_status",
  "node_type": "LogNode",
  "config": {
    "message": "Processing item: {{current_item}}",
    "level": "INFO"
  },
  "position": [0, 300]
}
```

**Log Levels:** `DEBUG`, `INFO`, `WARNING`, `ERROR`

#### AssertNode
Validates conditions during execution.

```json
{
  "node_id": "validate_data",
  "node_type": "AssertNode",
  "config": {
    "expression": "{{row_count}} > 0",
    "message": "No data found in CSV"
  },
  "position": [0, 300]
}
```

---

## 4. Robustness Protocol

### Mandatory Pattern: TryCatchNode Wrapper

All logic clusters that interact with external systems (browser, files, APIs, databases) MUST be wrapped in Try/Catch blocks.

```
[Pattern: Protected Cluster]

StartNode
    |
    v
TryNode ----try_body----> [Critical Operations] -----> FinallyNode
    |                                                      |
    v                                                      v
CatchNode ----catch_body----> [Error Handler] ---------> EndNode
```

**Example: Browser Automation with Error Handling**

```json
{
  "nodes": {
    "start": {"node_id": "start", "node_type": "StartNode", "config": {}, "position": [0, 0]},
    "try_block": {"node_id": "try_block", "node_type": "TryNode", "config": {}, "position": [0, 150]},
    "launch": {"node_id": "launch", "node_type": "LaunchBrowserNode", "config": {"url": "https://example.com"}, "position": [0, 300]},
    "click": {"node_id": "click", "node_type": "ClickElementNode", "config": {"selector": "#submit"}, "position": [0, 450]},
    "catch_block": {"node_id": "catch_block", "node_type": "CatchNode", "config": {}, "position": [400, 150]},
    "log_error": {"node_id": "log_error", "node_type": "LogNode", "config": {"message": "Error: {{error_message}}", "level": "ERROR"}, "position": [400, 300]},
    "finally_block": {"node_id": "finally_block", "node_type": "FinallyNode", "config": {}, "position": [800, 150]},
    "close": {"node_id": "close", "node_type": "CloseBrowserNode", "config": {}, "position": [800, 300]},
    "end": {"node_id": "end", "node_type": "EndNode", "config": {}, "position": [0, 600]}
  },
  "connections": [
    {"source_node": "start", "source_port": "exec_out", "target_node": "try_block", "target_port": "exec_in"},
    {"source_node": "try_block", "source_port": "try_body", "target_node": "launch", "target_port": "exec_in"},
    {"source_node": "launch", "source_port": "exec_out", "target_node": "click", "target_port": "exec_in"},
    {"source_node": "catch_block", "source_port": "catch_body", "target_node": "log_error", "target_port": "exec_in"},
    {"source_node": "catch_block", "source_port": "error_message", "target_node": "log_error", "target_port": "message"},
    {"source_node": "finally_block", "source_port": "finally_body", "target_node": "close", "target_port": "exec_in"},
    {"source_node": "close", "source_port": "exec_out", "target_node": "end", "target_port": "exec_in"}
  ]
}
```

### Mandatory Pattern: IfElseNode Sanity Checks

Critical variables MUST be validated before use.

```json
{
  "node_id": "validate_input",
  "node_type": "IfNode",
  "config": {
    "expression": "{{input_data}} != None and {{input_data}} != ''"
  }
}
```

**Common Validation Patterns:**

| Check | Expression |
|-------|------------|
| Not null/empty | `{{var}} != None and {{var}} != ''` |
| Is positive | `{{count}} > 0` |
| In range | `{{value}} >= 0 and {{value}} <= 100` |
| Type check | `type({{var}}) == str` |
| List has items | `len({{items}}) > 0` |

### Mandatory Pattern: DebugNode Logging

Entry and exit points of critical sections MUST have logging.

```
[Pattern: Logged Section]

LogNode("Entering: Process Orders")
    |
    v
[Critical Processing]
    |
    v
LogNode("Exiting: Process Orders - processed {{count}} items")
```

### Error Recovery Patterns

#### Pattern 1: Retry with Backoff

```json
{
  "nodes": {
    "retry_start": {"node_id": "retry_start", "node_type": "ForLoopStartNode", "config": {"mode": "range", "start": 0, "end": 3}},
    "try_operation": {"node_id": "try_operation", "node_type": "TryNode", "config": {}},
    "operation": {"node_id": "operation", "node_type": "HttpRequestNode", "config": {"url": "https://api.example.com"}},
    "catch_retry": {"node_id": "catch_retry", "node_type": "CatchNode", "config": {}},
    "wait": {"node_id": "wait", "node_type": "WaitNode", "config": {"duration": 2000}},
    "break_on_success": {"node_id": "break_on_success", "node_type": "BreakNode", "config": {}}
  }
}
```

#### Pattern 2: Fallback Value

```json
{
  "node_id": "get_with_default",
  "node_type": "GetVariableNode",
  "config": {
    "variable_name": "user_preference",
    "default_value": "en-US"
  }
}
```

#### Pattern 3: Graceful Degradation

```json
{
  "nodes": {
    "try_primary": {"node_id": "try_primary", "node_type": "TryNode"},
    "primary_api": {"node_id": "primary_api", "node_type": "HttpRequestNode", "config": {"url": "https://primary.api.com"}},
    "catch_primary": {"node_id": "catch_primary", "node_type": "CatchNode"},
    "fallback_api": {"node_id": "fallback_api", "node_type": "HttpRequestNode", "config": {"url": "https://fallback.api.com"}}
  }
}
```

---

## 5. Topology Rules

### Node Positioning Standards

| Constant | Value | Description |
|----------|-------|-------------|
| X_SPACING | 400px | Horizontal gap between sequential nodes |
| Y_SPACING | 150px | Vertical gap between nodes |
| BRANCH_OFFSET | 400px | Horizontal offset for parallel branches |
| APPEND_MARGIN | 200px | Margin from existing content for new nodes |

### Append Area Calculation

When adding nodes to an existing workflow:

```python
# Calculate append position
max_x = max(node["position"][0] for node in existing_nodes.values())
max_y = max(node["position"][1] for node in existing_nodes.values())

append_x = max_x + 400  # X_SPACING
append_y = 0  # Start new column at top
```

### Standard Layouts

#### Linear Flow
```
Start (0, 0)
  |
Node1 (0, 150)
  |
Node2 (0, 300)
  |
End (0, 450)
```

#### Branching (If/Else)
```
Start (0, 0)
  |
If (0, 150)
  |\
  | \
  |  TrueNode (400, 300)
  |  |
  v  v
FalseNode (0, 300)
  |  |
  v  v
Merge (0, 450)
  |
End (0, 600)
```

#### Loop
```
Start (0, 0)
  |
ForLoopStart (0, 150)
  |
  +-body-> LoopBody1 (0, 300)
  |            |
  |        LoopBody2 (0, 450)
  |            |
  |        ForLoopEnd (0, 600)
  |            |
  |<-----------+
  |
  +-completed-> End (400, 750)
```

#### Try/Catch/Finally
```
Start (0, 0)
  |
Try (0, 150) ----try_body----> TryBody (0, 300)
  |                                |
  v                                v
Catch (400, 150) --catch_body-> ErrorHandler (400, 300)
  |                                |
  v                                v
Finally (800, 150) -finally_body-> Cleanup (800, 300)
                                   |
                                   v
                                 End (800, 450)
```

---

## 6. Connection Patterns

### Execution Flow Connections

Always connect `exec_out` to `exec_in` for sequential flow:

```json
{
  "source_node": "node_a",
  "source_port": "exec_out",
  "target_node": "node_b",
  "target_port": "exec_in"
}
```

### Data Port Connections

Data flows from OUTPUT ports to INPUT ports of compatible types:

```json
{
  "source_node": "extract_text",
  "source_port": "text",
  "target_node": "set_variable",
  "target_port": "value"
}
```

### Type Compatibility Matrix

| Source Type | Compatible Targets |
|-------------|-------------------|
| STRING | STRING, ANY |
| INTEGER | INTEGER, FLOAT, ANY |
| FLOAT | FLOAT, ANY |
| BOOLEAN | BOOLEAN, ANY |
| LIST | LIST, ANY |
| DICT | DICT, ANY |
| ANY | ANY |
| BROWSER | BROWSER |
| PAGE | PAGE |

### Invalid Connection Examples

```json
// INVALID: Cannot connect exec port to data port
{
  "source_port": "exec_out",
  "target_port": "value"
}

// INVALID: Cannot connect data port to exec port
{
  "source_port": "result",
  "target_port": "exec_in"
}

// INVALID: Type mismatch without ANY
{
  "source_port": "count",  // INTEGER
  "target_port": "text"    // STRING (strict)
}
```

---

## 7. Best Practices

### Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| node_id | snake_case, descriptive | `validate_user_input` |
| variables | snake_case | `user_email`, `row_count` |
| Loop items | singular noun | `item`, `row`, `user` |

### Variable Pattern: {{variable}}

Use double braces for variable interpolation in string config values:

```json
{
  "config": {
    "url": "https://api.example.com/users/{{user_id}}",
    "message": "Processing {{item_count}} items for {{customer_name}}"
  }
}
```

### Workflow Organization

1. **Single Responsibility**: Each workflow should do ONE thing well
2. **Modular Sections**: Group related nodes with Comment nodes
3. **Clear Flow**: Minimize crossing connections
4. **Error Handling**: Every external operation should have error handling
5. **Logging**: Log entry/exit of major sections
6. **Cleanup**: Always clean up resources (close browsers, connections)

### Performance Considerations

1. **Batch Operations**: Use ForLoop with batch size for large datasets
2. **Selective Waits**: Use explicit waits instead of fixed delays
3. **Resource Cleanup**: Close browser/DB connections when done
4. **Pagination**: Process large API responses in pages

### Complete Workflow Example

```json
{
  "metadata": {
    "name": "Web Scraping with Error Handling",
    "description": "Scrapes product data with retry logic and CSV export",
    "version": "1.0.0"
  },
  "nodes": {
    "start": {
      "node_id": "start",
      "node_type": "StartNode",
      "config": {},
      "position": [0, 0]
    },
    "init_results": {
      "node_id": "init_results",
      "node_type": "SetVariableNode",
      "config": {"variable_name": "results", "default_value": [], "variable_type": "Array"},
      "position": [0, 150]
    },
    "try_scrape": {
      "node_id": "try_scrape",
      "node_type": "TryNode",
      "config": {},
      "position": [0, 300]
    },
    "launch": {
      "node_id": "launch",
      "node_type": "LaunchBrowserNode",
      "config": {"url": "https://example.com/products", "headless": true},
      "position": [0, 450]
    },
    "extract_products": {
      "node_id": "extract_products",
      "node_type": "ExtractTextNode",
      "config": {"selector": ".product-name"},
      "position": [0, 600]
    },
    "catch_scrape": {
      "node_id": "catch_scrape",
      "node_type": "CatchNode",
      "config": {},
      "position": [400, 300]
    },
    "log_error": {
      "node_id": "log_error",
      "node_type": "LogNode",
      "config": {"message": "Scraping failed: {{error_message}}", "level": "ERROR"},
      "position": [400, 450]
    },
    "finally_cleanup": {
      "node_id": "finally_cleanup",
      "node_type": "FinallyNode",
      "config": {},
      "position": [800, 300]
    },
    "close_browser": {
      "node_id": "close_browser",
      "node_type": "CloseBrowserNode",
      "config": {},
      "position": [800, 450]
    },
    "check_results": {
      "node_id": "check_results",
      "node_type": "IfNode",
      "config": {"expression": "len({{results}}) > 0"},
      "position": [800, 600]
    },
    "write_csv": {
      "node_id": "write_csv",
      "node_type": "WriteCSVNode",
      "config": {"file_path": "output/products.csv"},
      "position": [800, 750]
    },
    "end": {
      "node_id": "end",
      "node_type": "EndNode",
      "config": {},
      "position": [800, 900]
    }
  },
  "connections": [
    {"source_node": "start", "source_port": "exec_out", "target_node": "init_results", "target_port": "exec_in"},
    {"source_node": "init_results", "source_port": "exec_out", "target_node": "try_scrape", "target_port": "exec_in"},
    {"source_node": "try_scrape", "source_port": "try_body", "target_node": "launch", "target_port": "exec_in"},
    {"source_node": "launch", "source_port": "exec_out", "target_node": "extract_products", "target_port": "exec_in"},
    {"source_node": "catch_scrape", "source_port": "catch_body", "target_node": "log_error", "target_port": "exec_in"},
    {"source_node": "finally_cleanup", "source_port": "finally_body", "target_node": "close_browser", "target_port": "exec_in"},
    {"source_node": "close_browser", "source_port": "exec_out", "target_node": "check_results", "target_port": "exec_in"},
    {"source_node": "check_results", "source_port": "true", "target_node": "write_csv", "target_port": "exec_in"},
    {"source_node": "check_results", "source_port": "false", "target_node": "end", "target_port": "exec_in"},
    {"source_node": "write_csv", "source_port": "exec_out", "target_node": "end", "target_port": "exec_in"}
  ],
  "variables": {},
  "settings": {
    "stop_on_error": false,
    "timeout": 60,
    "retry_count": 0
  }
}
```

---

## 8. Missing Node Protocol

When a workflow requires functionality that **no existing node provides**, you have the authority to request node creation or modification.

### 8.1 Identify the Gap

Before requesting a new node:
1. Check if an existing node can be configured differently
2. Check if combining existing nodes achieves the goal
3. If neither works, a NEW NODE is needed

### 8.2 Request Node Creation

Output a special JSON response:

```json
{
  "action": "create_node",
  "reason": "No existing node supports [specific capability]",
  "node_spec": {
    "name": "MyNewNode",
    "category": "browser|file|data|http|system|desktop|llm",
    "description": "What this node does",
    "inputs": [
      {"name": "exec_in", "type": "EXEC"},
      {"name": "input_value", "type": "STRING", "required": true}
    ],
    "outputs": [
      {"name": "exec_out", "type": "EXEC"},
      {"name": "result", "type": "STRING"}
    ],
    "config": {
      "param_name": {"type": "string", "default": "", "description": "Parameter description"}
    },
    "execute_logic": "Description of what the execute() method should do"
  }
}
```

### 8.3 Request Node Modification

If an existing node is close but needs enhancement:

```json
{
  "action": "modify_node",
  "existing_node": "ExistingNodeName",
  "reason": "Need additional [capability]",
  "modifications": {
    "new_input": {"name": "new_param", "type": "STRING"},
    "new_output": {"name": "new_result", "type": "LIST"},
    "new_config": {"option_name": {"type": "boolean", "default": false}}
  }
}
```

### 8.4 Node Creation Rules

| Rule | Description |
|------|-------------|
| **Naming** | PascalCase ending with `Node` (e.g., `ScrapeTableNode`) |
| **Category** | Match closest existing category |
| **Ports** | Always include `exec_in`/`exec_out` for flow control |
| **Config** | Define all configurable parameters with types and defaults |
| **Focus** | One node = one responsibility (Single Responsibility Principle) |

### 8.5 Node Registration (For Implementation)

After node creation approval, follow 5-step registration:

1. **Logic Node Export**: `nodes/{category}/__init__.py` - Export node class
2. **Node Registry**: `nodes/__init__.py` - Add to `_NODE_REGISTRY`
3. **Workflow Loader**: `workflow_loader.py` - Add to `NODE_TYPE_MAP`
4. **Visual Node**: `visual_nodes/{category}/nodes.py` - Create visual class
5. **Visual Registry**: `visual_nodes/__init__.py` - Add to `_VISUAL_NODE_REGISTRY`

### 8.6 Common Missing Node Patterns

| Pattern | Example Use Case |
|---------|------------------|
| Data transformation | Custom JSON restructuring, XML to JSON |
| API integrations | Stripe payments, Twilio SMS, custom APIs |
| Custom parsing | Specific PDF extraction, email parsing |
| File formats | Excel formulas, Word document generation |
| Platform-specific | SAP integration, Salesforce automation |

---

## Quick Reference Card

### Most-Used Nodes

| Node | Purpose | Key Config |
|------|---------|------------|
| `StartNode` | Begin workflow | (none) |
| `EndNode` | End workflow | (none) |
| `SetVariableNode` | Store value | `variable_name`, `default_value` |
| `GetVariableNode` | Retrieve value | `variable_name` |
| `IfNode` | Branch logic | `expression` |
| `ForLoopStartNode` | Iterate collection | `mode`, `item_var` |
| `TryNode` | Error handling | (none) |
| `CatchNode` | Handle errors | `error_types` |
| `LaunchBrowserNode` | Open browser | `url`, `headless` |
| `ClickElementNode` | Click element | `selector`, `timeout` |
| `TypeTextNode` | Type text | `selector`, `text` |
| `ExtractTextNode` | Get text | `selector` |
| `WaitForElementNode` | Wait for element | `selector`, `state` |
| `ReadCSVNode` | Read CSV | `file_path`, `has_header` |
| `WriteCSVNode` | Write CSV | `file_path`, `data` |
| `HttpRequestNode` | API call | `url`, `method` |
| `LogNode` | Debug log | `message`, `level` |

### Execution Port Reference

| Node Type | Input | Output(s) |
|-----------|-------|-----------|
| StartNode | (none) | `exec_out` |
| EndNode | `exec_in` | (none) |
| IfNode | `exec_in` | `true`, `false` |
| ForLoopStartNode | `exec_in` | `body`, `completed` |
| ForLoopEndNode | `exec_in` | `exec_out` |
| TryNode | `exec_in` | `try_body`, `exec_out` |
| CatchNode | `exec_in` | `catch_body` |
| FinallyNode | `exec_in` | `finally_body` |
| (Most others) | `exec_in` | `exec_out` |

---

*Document Version: 1.0.0*
*Generated for: CasareRPA Genius AI Assistant*
*Based on: registry_dumper.py, workflow_ai.py, control_flow_nodes.py*
