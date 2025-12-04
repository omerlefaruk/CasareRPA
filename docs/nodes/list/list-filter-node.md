# ListFilterNode

Node that filters a list based on a condition.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.list_nodes`
**File:** `src\casare_rpa\nodes\list_nodes.py:447`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `list` | INPUT | No | DataType.LIST |
| `condition` | INPUT | No | DataType.STRING |
| `value` | INPUT | No | DataType.ANY |
| `key_path` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `result` | OUTPUT | DataType.LIST |
| `removed` | OUTPUT | DataType.LIST |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `condition` | CHOICE | `is_not_none` | No | Condition to filter by Choices: equals, not_equals, contains, starts_with, ends_with, ... (11 total) |
| `key_path` | STRING | `` | No | Dot-separated path to compare (for dict items) |

## Inheritance

Extends: `BaseNode`
