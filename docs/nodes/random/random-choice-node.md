# RandomChoiceNode

Select a random item from a list.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.random_nodes`
**File:** `src\casare_rpa\nodes\random_nodes.py:118`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `items` | INPUT | No | DataType.LIST |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `result` | OUTPUT | DataType.ANY |
| `index` | OUTPUT | DataType.INTEGER |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `count` | INTEGER | `1` | No | Number of items to select (default: 1) (min: 1) |
| `allow_duplicates` | BOOLEAN | `False` | No | Allow same item multiple times (default: False) |

## Inheritance

Extends: `BaseNode`
