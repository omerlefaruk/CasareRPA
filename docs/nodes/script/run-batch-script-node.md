# RunBatchScriptNode

Execute a batch script (Windows) or shell script (Unix).

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.script_nodes`
**File:** `src\casare_rpa\nodes\script_nodes.py:575`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `script` | INPUT | No | DataType.STRING |
| `working_dir` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `stdout` | OUTPUT | DataType.STRING |
| `stderr` | OUTPUT | DataType.STRING |
| `return_code` | OUTPUT | DataType.INTEGER |
| `success` | OUTPUT | DataType.BOOLEAN |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `timeout` | INTEGER | `60` | No | Execution timeout in seconds (default: 60) (min: 1) |
| `retry_count` | INTEGER | `0` | No | Number of retries on failure (default: 0) (min: 0) |
| `retry_interval` | INTEGER | `1000` | No | Delay between retries in ms (default: 1000) (min: 0) |
| `retry_on_nonzero` | BOOLEAN | `False` | No | Retry if return code is non-zero (default: False) |

## Inheritance

Extends: `BaseNode`
