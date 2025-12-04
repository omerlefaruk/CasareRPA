# ForkNode

Fork node that splits execution into multiple parallel branches.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.parallel_nodes`
**File:** `src\casare_rpa\nodes\parallel_nodes.py:44`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC_INPUT | Yes |  |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `f'branch_{i}'` | EXEC_OUTPUT |  |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `branch_count` | INTEGER | `2` | No | Number of parallel branches (2-10) (min: 2, max: 10) |
| `fail_fast` | BOOLEAN | `False` | No | If True, stop all branches when one fails. If False, continue other branches. |

## Inheritance

Extends: `BaseNode`
