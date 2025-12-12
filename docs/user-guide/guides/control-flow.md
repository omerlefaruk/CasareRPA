# Control Flow Patterns

Control flow nodes allow you to create dynamic workflows with branching logic, loops, and conditional execution. This guide covers all the control flow patterns available in CasareRPA.

## Table of Contents

- [If/Else Branching](#ifelse-branching)
- [Switch/Case Multi-Branching](#switchcase-multi-branching)
- [For Loop (Count-Based)](#for-loop-count-based)
- [ForEach Loop (Collection Iteration)](#foreach-loop-collection-iteration)
- [While Loop (Condition-Based)](#while-loop-condition-based)
- [Nested Loops](#nested-loops)
- [Break and Continue](#break-and-continue)
- [Combining Conditions](#combining-conditions)
- [Best Practices](#best-practices)

---

## If/Else Branching

The **If Node** evaluates a condition and routes execution to either the `true` or `false` output port.

### Basic Usage

```
[Start] --> [If] --true--> [Action A] --> [Merge] --> [End]
                  \--false--> [Action B] ---/
```

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `expression` | String | Boolean expression to evaluate (e.g., `{{count}} > 10`) |

### Expression Syntax

Use double curly braces to reference variables:

```
{{variable}} > 10           # Greater than comparison
{{status}} == "success"     # Equality check
{{items}} != null           # Null check
{{count}} >= 5 and {{count}} < 20   # Combined conditions
```

### Example: Check Login Status

```python
# If node expression:
{{login_success}} == True

# True branch: Navigate to dashboard
# False branch: Show error message
```

### Ports

| Port | Direction | Description |
|------|-----------|-------------|
| `exec_in` | Input | Execution input |
| `condition` | Input | Optional boolean input (overrides expression) |
| `true` | Output | Executes when condition is true |
| `false` | Output | Executes when condition is false |

> **Note:** The `condition` input port takes precedence over the `expression` property. This allows you to connect boolean outputs from other nodes directly.

---

## Switch/Case Multi-Branching

The **Switch Node** evaluates a value and routes to the matching case. Use this when you have multiple possible paths based on a single value.

### Basic Usage

```
                          /--> case_success --> [Handle Success]
[Get Status] --> [Switch] ---> case_error --> [Handle Error]
                          \--> case_pending --> [Handle Pending]
                           \--> default --> [Handle Unknown]
```

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `cases` | List | List of case values to match (e.g., `["success", "error", "pending"]`) |
| `expression` | String | Expression to evaluate for matching (e.g., `{{status}}`) |

### Example: Handle API Response Status

```python
# Switch node configuration:
# expression: {{response_status}}
# cases: ["200", "400", "404", "500"]

# Routes to:
# - case_200: Process successful response
# - case_400: Handle bad request
# - case_404: Handle not found
# - case_500: Handle server error
# - default: Handle unexpected status
```

### Ports

| Port | Direction | Description |
|------|-----------|-------------|
| `exec_in` | Input | Execution input |
| `value` | Input | Optional value input (overrides expression) |
| `case_{value}` | Output | Dynamic output for each case |
| `default` | Output | Fallback when no case matches |

---

## For Loop (Count-Based)

The **For Loop** iterates a specific number of times, controlled by start, end, and step values.

### Basic Usage

```
[For Loop Start] --body--> [Loop Body] --> [For Loop End]
        |
        +--completed--> [After Loop]
```

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `mode` | Choice | Set to `range` for count-based iteration |
| `start` | Integer | Starting value (default: 0) |
| `end` | Integer | End value (exclusive) |
| `step` | Integer | Increment per iteration (default: 1) |
| `item_var` | String | Variable name for current index (default: `item`) |

### Example: Process 10 Items

```python
# For Loop Start configuration:
# mode: range
# start: 0
# end: 10
# step: 1
# item_var: index

# Inside loop body, access:
# - {{index}}: Current iteration (0-9)
# - {{index_index}}: Same as {{index}}
```

### Output Ports

| Port | Type | Description |
|------|------|-------------|
| `body` | Exec | Loop body execution path |
| `completed` | Exec | Fires when all iterations complete |
| `current_item` | Data | Current iteration value |
| `current_index` | Data | Current index (0-based) |

---

## ForEach Loop (Collection Iteration)

The **For Loop** in `items` mode iterates over collections like lists, dictionaries, or strings.

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `mode` | Choice | Set to `items` for collection iteration |
| `list_var` | String | Variable name containing the list |
| `item_var` | String | Variable name for current item (default: `item`) |

### Example: Process List of URLs

```python
# Assume you have a list stored in "urls" variable:
# urls = ["https://example1.com", "https://example2.com", "https://example3.com"]

# For Loop Start configuration:
# mode: items
# list_var: urls
# item_var: current_url

# Inside loop body:
# - {{current_url}}: Current URL being processed
# - {{current_url_index}}: Index of current item (0, 1, 2)
```

### Iterating Over Dictionaries

When iterating over a dictionary, both keys and values are accessible:

```python
# Dictionary: {"name": "John", "age": 30, "city": "NYC"}

# For Loop Start configuration:
# mode: items
# item_var: entry

# Inside loop body:
# - {{entry}}: Current value ("John", 30, "NYC")
# - {{entry_key}}: Current key ("name", "age", "city")
# - {{entry_index}}: Index (0, 1, 2)
```

---

## While Loop (Condition-Based)

The **While Loop** continues iterating as long as a condition remains true. It includes a safety limit to prevent infinite loops.

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `expression` | String | Boolean expression evaluated each iteration |
| `max_iterations` | Integer | Safety limit (default: 1000) |

### Example: Wait for Element

```python
# While Loop Start configuration:
# expression: {{element_found}} == False
# max_iterations: 100

# Loop body:
# 1. Wait 1 second
# 2. Check if element exists
# 3. Set element_found variable
```

### Output Ports

| Port | Type | Description |
|------|------|-------------|
| `body` | Exec | Loop body execution path |
| `completed` | Exec | Fires when condition becomes false |
| `current_iteration` | Data | Current iteration number (0-based) |

> **Warning:** Always set a reasonable `max_iterations` value. Infinite loops will stop after reaching this limit with a warning in the logs.

---

## Nested Loops

You can nest loops inside each other for complex iteration patterns. Each loop maintains its own state.

### Example: Process Table Data

```python
# Outer loop: Iterate rows
# For Loop Start (outer):
#   mode: items
#   list_var: table_rows
#   item_var: row

    # Inner loop: Iterate cells in current row
    # For Loop Start (inner):
    #   mode: items
    #   list_var: row
    #   item_var: cell

        # Process each cell
        # {{cell}} contains current cell value
        # {{row}} contains current row

    # For Loop End (inner)

# For Loop End (outer)
```

### State Variables

Each loop creates unique state variables using its node ID, so nested loops don't interfere with each other.

---

## Break and Continue

Control loop execution flow with **Break** and **Continue** nodes.

### Break Node

Immediately exits the current loop and continues execution after the loop.

```
[For Loop Start] --body--> [If] --true--> [Break]
                               \--false--> [Continue Processing]
```

### Continue Node

Skips the remaining loop body and proceeds to the next iteration.

```
[For Loop Start] --body--> [If] --true--> [Continue] (skip to next)
                               \--false--> [Full Processing]
```

### Example: Find First Match

```python
# Search for a specific item in a list
# For Loop Start:
#   mode: items
#   list_var: search_results
#   item_var: result

    # Check if this is the item we want
    # If: {{result.id}} == {{target_id}}
    #   True: [Set Found Variable] --> [Break]
    #   False: (continue loop)

# For Loop End
```

### Properties

Both Break and Continue nodes have a `paired_loop_start_id` property that links them to their parent loop. This is set automatically when you add them inside a loop.

---

## Combining Conditions

Build complex conditions by combining multiple expressions.

### Logical Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `and` | Both conditions must be true | `{{a}} > 5 and {{b}} < 10` |
| `or` | Either condition must be true | `{{status}} == "active" or {{priority}} == "high"` |
| `not` | Negates the condition | `not {{is_disabled}}` |

### Comparison Operators

| Operator | Description |
|----------|-------------|
| `==` | Equal to |
| `!=` | Not equal to |
| `>` | Greater than |
| `<` | Less than |
| `>=` | Greater than or equal |
| `<=` | Less than or equal |

### Example: Complex Condition

```python
# If node expression:
({{user_role}} == "admin" or {{user_role}} == "moderator") and {{is_verified}} == True

# This evaluates to true only if:
# - User is admin OR moderator
# - AND user is verified
```

---

## Best Practices

### 1. Always Use Merge Nodes

After branching with If or Switch nodes, use a **Merge Node** to bring execution paths back together:

```
[If] --true--> [Action A] --+
     \--false--> [Action B] --+--> [Merge] --> [Continue]
```

### 2. Set Reasonable Loop Limits

Always configure `max_iterations` for While loops to prevent runaway execution:

```python
# Good: Reasonable limit
max_iterations: 100

# Bad: No limit (uses default 1000)
```

### 3. Use Descriptive Variable Names

Make your expressions readable:

```python
# Good: Clear intent
{{is_logged_in}} == True and {{has_permission}} == True

# Bad: Cryptic
{{a}} == 1 and {{b}} == 1
```

### 4. Handle All Cases in Switch

Always configure a meaningful `default` path for unexpected values:

```
[Switch] --case_a--> [Handle A]
         --case_b--> [Handle B]
         --default--> [Log Unknown Case] --> [Continue]
```

### 5. Avoid Deep Nesting

If you find yourself nesting more than 2-3 levels deep, consider:

- Extracting logic into a subflow
- Restructuring your workflow
- Using variables to track state instead of deep branching

### 6. Use Input Ports When Possible

Instead of complex expressions, compute values in preceding nodes and pass them via input ports:

```
[Compute Value] --output--> [If] (condition port)
```

This makes workflows more modular and easier to debug.

---

## Related Guides

- [Subflows Guide](./subflows.md) - Create reusable workflow components
- [Error Handling](./error-handling.md) - Handle errors in control flow
- [Debugging Guide](./debugging.md) - Debug control flow issues
