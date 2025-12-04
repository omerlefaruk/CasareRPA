# ConcatenateNode

Node that concatenates multiple strings.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.string_nodes`
**File:** `src\casare_rpa\nodes\string_nodes.py:30`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `string_1` | INPUT | No | DataType.STRING |
| `string_2` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `result` | OUTPUT | DataType.STRING |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `separator` | STRING | `` | No | Separator to insert between strings |

## Inheritance

Extends: `BaseNode`
