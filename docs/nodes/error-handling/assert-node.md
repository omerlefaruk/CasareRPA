# AssertNode

Assert a condition and throw error if false.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.error_handling_nodes`
**File:** `src\casare_rpa\nodes\error_handling_nodes.py:964`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `condition` | INPUT | No | DataType.BOOLEAN |
| `message` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `passed` | OUTPUT | DataType.BOOLEAN |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `condition` | BOOLEAN | `True` | No | Condition to assert (can be overridden by input port) |
| `message` | STRING | `Assertion failed` | No | Error message if assertion fails |

## Inheritance

Extends: `BaseNode`
