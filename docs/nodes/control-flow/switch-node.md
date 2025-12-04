# SwitchNode

Multi-way branching node based on value matching.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.control_flow_nodes`
**File:** `src\casare_rpa\nodes\control_flow_nodes.py:727`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC_INPUT | Yes |  |
| `value` | INPUT | No | DataType.ANY |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `f'case_{case}'` | EXEC_OUTPUT |  |
| `default` | EXEC_OUTPUT |  |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `cases` | LIST | `[]` | No | List of case values to match (e.g., ['success', 'error', 'pending']) |
| `expression` | STRING | `` | No | Expression to evaluate for value (optional if using input port) |

## Inheritance

Extends: `BaseNode`
