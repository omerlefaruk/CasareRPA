# ListSortNode

Node that sorts a list.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.list_nodes`
**File:** `src\casare_rpa\nodes\list_nodes.py:293`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `list` | INPUT | No | DataType.LIST |
| `reverse` | INPUT | No | DataType.BOOLEAN |
| `key_path` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `result` | OUTPUT | DataType.LIST |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `reverse` | BOOLEAN | `False` | No | Sort in descending order |
| `key_path` | STRING | `` | No | Dot-separated path to sort by (for dict items) |

## Inheritance

Extends: `BaseNode`
