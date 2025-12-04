# RunPythonScriptNode

Execute Python code inline.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.script_nodes`
**File:** `src\casare_rpa\nodes\script_nodes.py:51`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `code` | INPUT | No | DataType.STRING |
| `variables` | INPUT | No | DataType.DICT |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `result` | OUTPUT | DataType.ANY |
| `output` | OUTPUT | DataType.STRING |
| `success` | OUTPUT | DataType.BOOLEAN |
| `error` | OUTPUT | DataType.STRING |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `timeout` | INTEGER | `60` | No | Execution timeout in seconds (default: 60) (min: 1) |
| `isolated` | BOOLEAN | `False` | No | Run in isolated subprocess (default: False) |

## Inheritance

Extends: `BaseNode`
