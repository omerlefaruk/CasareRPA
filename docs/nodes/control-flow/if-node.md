# IfNode

Conditional node that executes different paths based on condition.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.control_flow_nodes`
**File:** `src\casare_rpa\nodes\control_flow_nodes.py:34`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC_INPUT | Yes |  |
| `condition` | INPUT | No | DataType.ANY |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `true` | EXEC_OUTPUT |  |
| `false` | EXEC_OUTPUT |  |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `expression` | STRING | `` | No | Boolean expression to evaluate (optional if using input port) |

## Inheritance

Extends: `BaseNode`
