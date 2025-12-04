# ListFlattenNode

Node that flattens a nested list.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.list_nodes`
**File:** `src\casare_rpa\nodes\list_nodes.py:739`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `list` | INPUT | No | DataType.LIST |
| `depth` | INPUT | No | DataType.INTEGER |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `result` | OUTPUT | DataType.LIST |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `depth` | INTEGER | `1` | No | How many levels to flatten (min: 1) |

## Inheritance

Extends: `BaseNode`
