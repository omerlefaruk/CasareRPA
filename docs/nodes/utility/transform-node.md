# TransformNode

Transform node - transforms data from one format to another.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.utility_nodes`
**File:** `src\casare_rpa\nodes\utility_nodes.py:548`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `value` | INPUT | No | DataType.ANY |
| `param` | INPUT | No | DataType.ANY |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `result` | OUTPUT | DataType.ANY |
| `success` | OUTPUT | DataType.BOOLEAN |
| `error` | OUTPUT | DataType.STRING |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `transform_type` | CHOICE | `to_string` | No | Type of transformation to perform Choices: to_string, to_integer, to_float, to_boolean, to_list, ... (18 total) |
| `transform_param` | ANY | `-` | No | Parameter for transformation |
| `variable_name` | STRING | `transformed` | No | Name of variable to store result |

## Inheritance

Extends: `BaseNode`
