# WhileLoopStartNode

Start node of a While Loop pair (WhileLoopStart + WhileLoopEnd).

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.control_flow_nodes`
**File:** `src\casare_rpa\nodes\control_flow_nodes.py:390`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC_INPUT | Yes |  |
| `condition` | INPUT | No | DataType.BOOLEAN |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `body` | EXEC_OUTPUT |  |
| `completed` | EXEC_OUTPUT |  |
| `current_iteration` | OUTPUT | DataType.INTEGER |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `expression` | STRING | `` | No | Boolean expression to evaluate each iteration (optional if using input port) |
| `max_iterations` | INTEGER | `1000` | No | Maximum iterations to prevent infinite loops (min: 1) |

## Inheritance

Extends: `BaseNode`
