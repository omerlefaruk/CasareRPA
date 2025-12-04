# ForLoopStartNode

Start node of a For Loop pair (ForLoopStart + ForLoopEnd).

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.control_flow_nodes`
**File:** `src\casare_rpa\nodes\control_flow_nodes.py:144`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC_INPUT | Yes |  |
| `items` | INPUT | No | DataType.ANY |
| `end` | INPUT | No | DataType.INTEGER |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `body` | EXEC_OUTPUT |  |
| `completed` | EXEC_OUTPUT |  |
| `current_item` | OUTPUT | DataType.ANY |
| `current_index` | OUTPUT | DataType.INTEGER |
| `current_key` | OUTPUT | DataType.ANY |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `mode` | CHOICE | `items` | No | Iteration mode: 'items' for collection iteration (ForEach), 'range' for counter-based iteration Choices: items, range |
| `start` | INTEGER | `0` | No | Start value for range iteration (when mode='range') |
| `end` | INTEGER | `10` | No | End value for range iteration (when mode='range') |
| `step` | INTEGER | `1` | No | Step value for range iteration (when mode='range') (min: 1) |

## Inheritance

Extends: `BaseNode`
