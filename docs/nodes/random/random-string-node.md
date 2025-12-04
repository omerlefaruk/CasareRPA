# RandomStringNode

Generate a random string.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.random_nodes`
**File:** `src\casare_rpa\nodes\random_nodes.py:229`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `length` | INPUT | No | DataType.INTEGER |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `result` | OUTPUT | DataType.STRING |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `include_uppercase` | BOOLEAN | `True` | No | Include A-Z (default: True) |
| `include_lowercase` | BOOLEAN | `True` | No | Include a-z (default: True) |
| `include_digits` | BOOLEAN | `True` | No | Include 0-9 (default: True) |
| `include_special` | BOOLEAN | `False` | No | Include special characters (default: False) |
| `custom_chars` | STRING | `` | No | Custom character set to use (overrides above) |

## Inheritance

Extends: `BaseNode`
