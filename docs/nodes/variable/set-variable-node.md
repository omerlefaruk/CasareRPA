# SetVariableNode

Set variable node - stores a value in the execution context.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.variable_nodes`
**File:** `src\casare_rpa\nodes\variable_nodes.py:57`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `value` | INPUT | No | DataType.ANY |
| `variable_name` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `value` | OUTPUT | DataType.ANY |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `variable_name` | STRING | `-` | Yes | Name of the variable to set |
| `default_value` | ANY | `-` | No | Default value if no input provided |
| `variable_type` | CHOICE | `String` | No | Type to convert value to Choices: String, Boolean, Int32, Float, Object, ... (10 total) |

## Inheritance

Extends: `BaseNode`
