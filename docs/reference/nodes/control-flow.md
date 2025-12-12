# Control Flow Nodes

Control flow nodes manage execution logic: conditional branching, loops, and error handling. They determine which nodes execute and in what order.

## Overview

| Category | Nodes |
|----------|-------|
| **Conditionals** | IfNode, SwitchNode, MergeNode |
| **Loops** | ForLoopStartNode, ForLoopEndNode, WhileLoopStartNode, WhileLoopEndNode |
| **Loop Control** | BreakNode, ContinueNode |
| **Error Handling** | TryNode, CatchNode, FinallyNode |
| **Retries** | RetryNode, ThrowErrorNode |

---

## Conditional Nodes

### IfNode

Binary condition branching - routes execution based on a boolean condition.

#### Description

Evaluates a condition and routes execution to either the `true` or `false` output port. Conditions can come from an input port connection or from an expression in the properties.

#### Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `expression` | STRING | No | `""` | Boolean expression to evaluate |

#### Ports

| Port | Type | Direction | Description |
|------|------|-----------|-------------|
| `exec_in` | EXEC | Input | Execution flow |
| `condition` | ANY | Input | Condition value (optional) |
| `true` | EXEC | Output | Execute if condition is true |
| `false` | EXEC | Output | Execute if condition is false |

#### Expression Syntax

Expressions support variable references with double curly braces:

```
{{count}} > 10
{{status}} == "success"
{{items}} != []
{{is_enabled}} and {{has_permission}}
```

Variables are resolved from the execution context.

#### Example: Simple Condition

```
[If]
    expression: "{{user_age}} >= 18"
        |
   +----+----+
   |         |
 true      false
   |         |
[Adult]  [Minor]
```

#### Example: Input Port Condition

```
[CompareValues]     [If]
    |                 |
    +--> condition -->+
                      |
                 +----+----+
                 |         |
               true      false
```

#### Code Example

```python
from casare_rpa.nodes import IfNode

# Using expression
if_node = IfNode(
    node_id="if_1",
    config={"expression": "{{count}} > 0"}
)

# Execute with context
context.variables["count"] = 5
result = await if_node.execute(context)
# result["next_nodes"] = ["true"]
```

---

### SwitchNode

Multi-way branching based on value matching.

#### Description

Evaluates an input value against a list of cases and routes to the matching case output. If no case matches, routes to the `default` output.

#### Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `cases` | LIST | Yes | `[]` | List of case values to match |
| `expression` | STRING | No | `""` | Expression to evaluate for value |

#### Ports

| Port | Type | Direction | Description |
|------|------|-----------|-------------|
| `exec_in` | EXEC | Input | Execution flow |
| `value` | ANY | Input | Value to match (optional) |
| `case_{value}` | EXEC | Output | One per case in the list |
| `default` | EXEC | Output | No match fallback |

#### Example

```python
[Switch]
    cases: ["success", "error", "pending"]
    expression: "{{status}}"
        |
   +----+----+----+----+
   |    |    |    |    |
case_  case_  case_  default
success error pending
   |    |    |    |
[Ok] [Err] [Wait] [Unknown]
```

#### Code Example

```python
from casare_rpa.nodes import SwitchNode

switch = SwitchNode(
    node_id="switch_1",
    config={
        "cases": ["red", "green", "blue"],
        "expression": "{{color}}"
    }
)

context.variables["color"] = "green"
result = await switch.execute(context)
# result["next_nodes"] = ["case_green"]
```

---

### MergeNode

Convergence point for multiple execution paths.

#### Description

A pass-through node that accepts multiple incoming execution connections and continues to a single output. Use after If/Switch nodes to rejoin branches.

#### Properties

*No configurable properties*

#### Ports

| Port | Type | Direction | Description |
|------|------|-----------|-------------|
| `exec_in` | EXEC | Input | Multiple connections allowed |
| `exec_out` | EXEC | Output | Single output |

#### Example

```
[If]
   |
+--+--+
|     |
true  false
|     |
[A]   [B]
|     |
+--+--+
   |
[Merge]
   |
[Continue]
```

---

## Loop Nodes

### ForLoopStartNode / ForLoopEndNode

Counter-based or collection iteration loop.

#### Description

ForLoopStart and ForLoopEnd work together to create loops. Connect nodes between them for the loop body. Supports two modes:
- **items**: Iterate over a collection (list, dict, string)
- **range**: Iterate over a numeric range

#### ForLoopStartNode Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `mode` | CHOICE | No | `"items"` | Iteration mode: items, range |
| `list_var` | STRING | No | `""` | Variable name containing list (items mode) |
| `item_var` | STRING | No | `"item"` | Variable name for current item |
| `start` | INTEGER | No | `0` | Range start value |
| `end` | INTEGER | No | `10` | Range end value |
| `step` | INTEGER | No | `1` | Range step value |

#### ForLoopStartNode Ports

| Port | Type | Direction | Description |
|------|------|-----------|-------------|
| `exec_in` | EXEC | Input | Start iteration |
| `items` | ANY | Input | Collection to iterate (items mode) |
| `end` | INTEGER | Input | End value override (range mode) |
| `body` | EXEC | Output | Loop body execution |
| `completed` | EXEC | Output | After all iterations |
| `current_item` | ANY | Output | Current item value |
| `current_index` | INTEGER | Output | Current index (0-based) |
| `current_key` | ANY | Output | Current key (dict iteration) |

#### ForLoopEndNode Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `paired_start_id` | STRING | Auto | `""` | Paired ForLoopStartNode ID |

#### Example: Range Loop

```
[ForLoopStart]
    mode: "range"
    start: 0
    end: 10
    step: 1
    item_var: "i"
        |
   +----+----+
   |         |
 body    completed
   |         |
[Action]   [Done]
   |
[ForLoopEnd]
   |
   +---> (loops back to ForLoopStart)
```

#### Example: Collection Loop

```python
# Loop over items from ReadCSV
[ReadCSV] --data--> [ForLoopStart]
                        mode: "items"
                        item_var: "row"
                            |
                          body
                            |
                       [ProcessRow]
                       # Access {{row}} variable
                            |
                       [ForLoopEnd]
```

#### Code Example

```python
from casare_rpa.nodes import ForLoopStartNode, ForLoopEndNode

# Range mode
loop_start = ForLoopStartNode(
    node_id="loop_start_1",
    config={
        "mode": "range",
        "start": 1,
        "end": 5,
        "item_var": "counter"
    }
)

loop_end = ForLoopEndNode(node_id="loop_end_1")
loop_end.set_paired_start("loop_start_1")

# Each iteration: counter = 1, 2, 3, 4
```

---

### WhileLoopStartNode / WhileLoopEndNode

Condition-based loop that continues while condition is true.

#### Description

WhileLoopStart evaluates a condition on each iteration and continues until the condition becomes false. Includes a safety limit to prevent infinite loops.

#### WhileLoopStartNode Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `expression` | STRING | No | `""` | Boolean condition expression |
| `max_iterations` | INTEGER | No | `1000` | Safety limit |

#### WhileLoopStartNode Ports

| Port | Type | Direction | Description |
|------|------|-----------|-------------|
| `exec_in` | EXEC | Input | Start loop |
| `condition` | BOOLEAN | Input | Condition value (optional) |
| `body` | EXEC | Output | Loop body |
| `completed` | EXEC | Output | After condition false |
| `current_iteration` | INTEGER | Output | Iteration number |

#### Example

```
[WhileLoopStart]
    expression: "{{retry_count}} < 3"
    max_iterations: 100
        |
   +----+----+
   |         |
 body    completed
   |         |
[Attempt]  [Done]
   |
[IncrementVariable]
    variable: "retry_count"
   |
[WhileLoopEnd]
```

---

### BreakNode

Exits from the current loop immediately.

#### Description

Signals the parent loop (For/While) to terminate and proceed to the `completed` output. Must be placed inside a loop body.

#### Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `paired_loop_start_id` | STRING | Auto | `""` | Parent loop ID |

#### Example

```
[ForLoopStart]
        |
      body
        |
[If: "{{item}} == 'stop'"]
        |
   +----+----+
   |         |
 true      false
   |         |
[Break]  [Continue processing]
```

---

### ContinueNode

Skips to the next loop iteration.

#### Description

Signals the parent loop to skip the remaining loop body and proceed to the next iteration.

#### Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `paired_loop_start_id` | STRING | Auto | `""` | Parent loop ID |

#### Example

```
[ForLoopStart]
        |
      body
        |
[If: "{{item}} is None"]
        |
   +----+----+
   |         |
 true      false
   |         |
[Continue] [ProcessItem]
```

---

## Error Handling Nodes

### TryNode / CatchNode / FinallyNode

Structured error handling similar to try/catch/finally in programming languages.

#### Description

- **TryNode**: Begins an error-protected block
- **CatchNode**: Handles errors from the Try block
- **FinallyNode**: Cleanup code that always executes

#### TryNode Ports

| Port | Type | Direction | Description |
|------|------|-----------|-------------|
| `exec_in` | EXEC | Input | Start try block |
| `try_body` | EXEC | Output | Protected code |
| `exec_out` | EXEC | Output | Continue after try (no error) |

#### CatchNode Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `paired_try_id` | STRING | Auto | `""` | Paired TryNode ID |
| `error_types` | STRING | No | `""` | Comma-separated error types to catch |

#### CatchNode Ports

| Port | Type | Direction | Description |
|------|------|-----------|-------------|
| `exec_in` | EXEC | Input | Error occurred |
| `catch_body` | EXEC | Output | Error handling code |
| `error_message` | STRING | Output | Error message |
| `error_type` | STRING | Output | Error type name |
| `stack_trace` | STRING | Output | Full stack trace |

#### FinallyNode Ports

| Port | Type | Direction | Description |
|------|------|-----------|-------------|
| `exec_in` | EXEC | Input | Cleanup |
| `finally_body` | EXEC | Output | Cleanup code |
| `had_error` | BOOLEAN | Output | True if error occurred |

#### Example

```
[Try]
   |
try_body
   |
[RiskyOperation]  --error--> [Catch]
   |                            |
   |                       catch_body
   |                            |
   |                       [LogError]
   |                            |
   +------------+---------------+
                |
            [Finally]
                |
           finally_body
                |
            [Cleanup]
                |
            [Continue]
```

#### Code Example

```python
# The workflow executor handles routing errors to Catch
# Try/Catch/Finally nodes manage state via context variables

[Try]
    |
    try_body --> [ClickElement] --> [TypeText]
                        |
                    (if error)
                        |
                    [Catch]
                        |
                        +--> error_message --> [Log]
```

---

## Retry Nodes

### RetryNode

Retries a block of nodes with configurable backoff.

#### Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `max_attempts` | INTEGER | No | `3` | Maximum retry attempts |
| `delay_ms` | INTEGER | No | `1000` | Initial delay (ms) |
| `backoff_multiplier` | FLOAT | No | `2.0` | Delay multiplier |
| `max_delay_ms` | INTEGER | No | `30000` | Maximum delay cap |

#### Ports

| Port | Type | Direction | Description |
|------|------|-----------|-------------|
| `exec_in` | EXEC | Input | Start retry block |
| `retry_body` | EXEC | Output | Code to retry |
| `success` | EXEC | Output | Succeeded within attempts |
| `failure` | EXEC | Output | All attempts failed |
| `attempt_number` | INTEGER | Output | Current attempt (1-based) |

#### Example

```
[Retry]
    max_attempts: 3
    delay_ms: 1000
    backoff_multiplier: 2.0
        |
   +----+----+----+
   |    |    |    |
retry success failure
 body    |    |
   |    [Ok] [Error]
[FlakyAPI]
```

---

### ThrowErrorNode

Raises an error to stop execution or trigger error handling.

#### Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `error_type` | STRING | No | `"Error"` | Error type/class name |
| `message` | STRING | Yes | `""` | Error message |

#### Example

```python
[If: "{{data}} is None"]
        |
      true
        |
[ThrowError]
    error_type: "ValidationError"
    message: "Data cannot be empty"
```

---

## Complete Examples

### Example 1: Conditional Processing

```
[Start]
    |
[ReadCSV]
    |
    +---> data
    |
[If]
    expression: "len({{data}}) > 0"
        |
   +----+----+
   |         |
 true      false
   |         |
[Process]  [Log: "No data"]
   |         |
   +----+----+
        |
    [Merge]
        |
    [End]
```

### Example 2: Loop with Retry

```
[Start]
    |
[ReadCSV] --data--> [ForLoopStart]
                        item_var: "row"
                            |
                          body
                            |
                       [Retry]
                       max_attempts: 3
                            |
                       retry_body
                            |
                       [APICall]
                       url: "{{api_url}}/{{row.id}}"
                            |
                       [RetryEnd]
                            |
                       [ForLoopEnd]
                            |
                       completed
                            |
                       [End]
```

### Example 3: Error Handling

```
[Start]
    |
[Try]
    |
try_body
    |
[LaunchBrowser]
    |
[GoToURL]
    |
[ClickElement]
    |
    +---(error)--> [Catch]
    |                  |
    |             catch_body
    |                  |
    |             [Screenshot]
    |                  |
    |             [Log: "Error: {{error_message}}"]
    |                  |
    +--------+---------+
             |
         [Finally]
             |
        finally_body
             |
        [CloseBrowser]
             |
         [End]
```

## Best Practices

1. **Always pair Start/End nodes**: Every ForLoopStart needs ForLoopEnd, every Try needs matching Catch/Finally
2. **Set max_iterations on While loops**: Prevent infinite loops
3. **Use Merge after If/Switch**: Rejoin branches before continuing
4. **Add Try/Catch around browser operations**: Handle network failures gracefully
5. **Use meaningful variable names**: `item_var: "customer"` not `item_var: "i"`
6. **Log inside Catch blocks**: Record errors for debugging
7. **Clean up in Finally**: Close browsers, files, database connections
