# JoinNode

Join node that synchronizes parallel branches from a ForkNode.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.parallel_nodes`
**File:** `src\casare_rpa\nodes\parallel_nodes.py:138`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC_INPUT | Yes |  |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC_OUTPUT |  |
| `results` | OUTPUT | DataType.DICT |
| `branch_count` | OUTPUT | DataType.INTEGER |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `merge_strategy` | CHOICE | `all` | No | How to merge branch results: all (combine), first (first to complete), last (last to complete) Choices: all, first, last |

## Inheritance

Extends: `BaseNode`
