# ValidateNode

Validate node - validates data against rules.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.utility_nodes`
**File:** `src\casare_rpa\nodes\utility_nodes.py:290`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `value` | INPUT | No | DataType.ANY |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `valid` | EXEC_OUTPUT |  |
| `invalid` | EXEC_OUTPUT |  |
| `is_valid` | OUTPUT | DataType.BOOLEAN |
| `error_message` | OUTPUT | DataType.STRING |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `validation_type` | CHOICE | `not_empty` | No | Type of validation to perform Choices: not_empty, is_string, is_number, is_integer, is_boolean, ... (16 total) |
| `validation_param` | ANY | `-` | No | Parameter for validation (e.g., regex pattern, min value) |
| `error_message` | STRING | `Validation failed` | No | Custom error message on validation failure |

## Inheritance

Extends: `BaseNode`
