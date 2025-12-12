# Variables

Variables allow you to store and reuse data throughout your workflow. They act as named containers that hold values which can be read, modified, and passed between nodes.

## Variable System Overview

CasareRPA's variable system provides:

- **Data storage**: Store values for use later in the workflow
- **Data passing**: Transfer data between nodes without direct port connections
- **Dynamic content**: Insert variable values into text, URLs, and configurations
- **Type flexibility**: Variables can hold strings, numbers, lists, objects, and more

Variables are stored in the **execution context** and persist for the duration of the workflow run.

## Variable Syntax

Variables use double curly brace syntax:

```
{{variable_name}}
```

When CasareRPA encounters this pattern, it replaces it with the variable's current value.

### Basic Examples

| Expression | Variable Value | Result |
|------------|----------------|--------|
| `Hello {{name}}!` | `name = "World"` | `Hello World!` |
| `https://{{domain}}/api` | `domain = "example.com"` | `https://example.com/api` |
| `Total: {{count}} items` | `count = 42` | `Total: 42 items` |

### Type Preservation

When a variable reference is the **entire value** (not embedded in text), the original type is preserved:

```python
# Variable: count = 42 (integer)
"{{count}}"         # Returns: 42 (integer preserved)
"Items: {{count}}"  # Returns: "Items: 42" (converted to string)

# Variable: data = {"name": "John"} (dict)
"{{data}}"          # Returns: {"name": "John"} (dict preserved)
```

## Setting Variables

### Using SetVariableNode

The primary way to create or update variables is the **Set Variable** node:

| Property | Type | Description |
|----------|------|-------------|
| `variable_name` | STRING | Name of the variable to set |
| `value` | ANY | Value to assign (can use `{{other_var}}`) |
| `default_value` | ANY | Value if no input provided |
| `variable_type` | CHOICE | Type conversion (String, Boolean, Int32, Float, Object, Array) |

**Example: Setting a simple variable**
1. Add a **Set Variable** node
2. Set `variable_name` to `username`
3. Set `value` to `john.doe`
4. Connect to your workflow

**Example: Setting from a node output**
1. Connect the output port of a previous node to the `value` input port
2. The output value is stored in the variable

### Variable Types

When setting variables, you can specify the type for automatic conversion:

| Type | Description | Conversion Example |
|------|-------------|-------------------|
| String | Text (default) | `42` becomes `"42"` |
| Boolean | True/False | `"true"`, `"1"`, `"yes"` become `true` |
| Int32 | Integer | `"42"` becomes `42` |
| Float | Decimal | `"3.14"` becomes `3.14` |
| Object | Dictionary | JSON string becomes dict |
| Array | List | JSON array or comma-separated becomes list |
| Dict | Same as Object | JSON string becomes dict |
| List | Same as Array | JSON array becomes list |

## Getting Variables

### Using GetVariableNode

The **Get Variable** node retrieves a stored variable value:

| Property | Type | Description |
|----------|------|-------------|
| `variable_name` | STRING | Name of the variable to retrieve |
| `default_value` | ANY | Value to return if variable not found |

The retrieved value is available on the `value` output port.

### Using Variable Syntax in Properties

You can reference variables directly in node properties without a Get Variable node:

```
# In a Navigate node's URL property:
https://app.example.com/users/{{user_id}}/profile

# In an HTTP Request body:
{"username": "{{username}}", "email": "{{email}}"}

# In a Type Text node:
Dear {{customer_name}}, your order {{order_id}} is confirmed.
```

## Variable Scopes

### Workflow-Level Scope

Variables are scoped to the current workflow execution:

- **Created**: When Set Variable node executes
- **Available**: From that point until workflow ends
- **Destroyed**: When workflow completes

Variables from one workflow run do not persist to the next run.

### Subflow Scope

When calling subflows:
- The parent workflow's variables are available in the subflow
- Variables set in the subflow are available in the parent after return
- Use naming conventions to avoid conflicts (e.g., `subflow_result`)

## Special Loop Variables

Loop nodes automatically create variables for the current iteration:

### For Loop Variables

When using **ForLoopStartNode** with `item_var = "item"`:

| Variable | Description | Example Value |
|----------|-------------|---------------|
| `item` | Current item being processed | `"apple"` |
| `item_index` | Zero-based index of current iteration | `0`, `1`, `2` |
| `item_key` | Key if iterating over a dictionary | `"fruit_name"` |

These variables update automatically on each iteration.

### Accessing Loop Variables

```
# In a Log node during loop:
Processing item {{item_index}}: {{item}}

# Accessing nested data:
Customer: {{item.name}}, Email: {{item.email}}
```

### Custom Loop Variable Names

Configure the `item_var` property to use a custom name:

| item_var Setting | Created Variables |
|------------------|-------------------|
| `item` (default) | `item`, `item_index`, `item_key` |
| `user` | `user`, `user_index`, `user_key` |
| `file` | `file`, `file_index`, `file_key` |

## System Variables

CasareRPA provides built-in system variables that are computed dynamically:

| Variable | Description | Example Value |
|----------|-------------|---------------|
| `{{$currentDate}}` | Today's date (YYYY-MM-DD) | `2024-01-15` |
| `{{$currentTime}}` | Current time (HH:MM:SS) | `14:30:45` |
| `{{$currentDateTime}}` | Full ISO timestamp | `2024-01-15T14:30:45` |
| `{{$timestamp}}` | Unix timestamp (seconds) | `1705329045` |

System variables start with `$` to distinguish them from user variables.

### Using System Variables

```
# In a filename:
report_{{$currentDate}}.csv

# In a log message:
Process started at {{$currentDateTime}}

# In unique identifiers:
order_{{$timestamp}}
```

## Nested Path Access

Variables can contain complex objects. Access nested values using dot notation:

```python
# Variable: user = {"name": "John", "address": {"city": "NYC"}}

{{user.name}}           # Returns: "John"
{{user.address.city}}   # Returns: "NYC"

# Variable: items = ["apple", "banana", "cherry"]

{{items[0]}}            # Returns: "apple"
{{items[2]}}            # Returns: "cherry"

# Combined:
# Variable: orders = [{"id": 1, "total": 100}, {"id": 2, "total": 200}]

{{orders[0].id}}        # Returns: 1
{{orders[1].total}}     # Returns: 200
```

## Using Variables in Node Properties

Most node properties support variable substitution:

### Text Properties
```
URL: https://api.example.com/users/{{user_id}}
Selector: #user-{{user_id}}-profile
Message: Hello {{name}}, welcome back!
```

### JSON Properties
```json
{
  "username": "{{username}}",
  "password": "{{password}}",
  "remember": {{remember_me}}
}
```

### File Paths
```
C:\Reports\{{$currentDate}}\{{report_name}}.xlsx
```

## Variables Panel in UI

The Canvas includes a **Variables Panel** (View > Variables) that shows:

- All defined workflow variables
- Current values during execution
- Variable types
- Quick add/edit functionality

### Managing Variables in the Panel

1. **View variables**: Open Variables Panel from the View menu
2. **Add variable**: Click the + button and enter name/value
3. **Edit variable**: Double-click on a variable row
4. **Delete variable**: Select and press Delete or use context menu
5. **Watch during execution**: Values update in real-time as workflow runs

### Initial Variables

You can define variables before the workflow runs:
1. Open the Variables Panel
2. Add variables with default values
3. These are available from the Start node onward

## Best Practices

### Naming Conventions

| Convention | Example | Use Case |
|------------|---------|----------|
| snake_case | `user_name`, `order_total` | General variables |
| camelCase | `userName`, `orderTotal` | Alternative style |
| UPPERCASE | `API_KEY`, `BASE_URL` | Constants/config |
| _prefix | `_loop_state`, `_internal` | Internal/temporary |

### Organization Tips

1. **Use descriptive names**: `customer_email` not `ce`
2. **Group related variables**: `order_id`, `order_total`, `order_date`
3. **Document complex variables**: Add Comment nodes explaining data structures
4. **Clean up temporary variables**: Delete variables that are no longer needed

### Common Patterns

**Configuration at workflow start:**
```
[Start] --> [Set Base URL] --> [Set API Key] --> [Main Logic]
```

**Accumulating results:**
```
[Initialize Results List] --> [Loop] --> [Add to Results] --> [Process All Results]
```

**Error context:**
```
[Set Current Step] --> [Do Work] --> [On Error: Log {{current_step}} failed]
```

## Troubleshooting

### Variable Not Found

If `{{variable_name}}` appears literally in output:
- Check the variable name spelling
- Verify the Set Variable node executed before the reference
- Look for typos in curly braces (must be double: `{{` not `{`)

### Type Errors

If operations fail due to type mismatch:
- Use the `variable_type` property in Set Variable to convert
- Use transformation nodes (ToInteger, ToString) before assignment

### Scope Issues

If a variable is not available:
- Ensure Set Variable executed in the current branch
- Check if the variable was set in a different conditional path
- Verify subflow variable passing settings

## Next Steps

- [Nodes and Ports](nodes-and-ports.md): Learn about data ports that pass values directly
- [Workflows](workflows.md): See how variables fit into complete automations
- [Execution Modes](execution-modes.md): Understand how variables persist during execution
