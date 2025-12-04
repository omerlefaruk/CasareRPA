# RunJavaScriptNode

Execute JavaScript code using Node.js.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.script_nodes`
**File:** `src\casare_rpa\nodes\script_nodes.py:776`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `code` | INPUT | No | DataType.STRING |
| `input_data` | INPUT | No | DataType.ANY |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `result` | OUTPUT | DataType.STRING |
| `success` | OUTPUT | DataType.BOOLEAN |
| `error` | OUTPUT | DataType.STRING |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `timeout` | INTEGER | `60` | No | Execution timeout in seconds (default: 60) (min: 1) |
| `node_path` | STRING | `node` | No | Path to Node.js executable (default: 'node') |

## Inheritance

Extends: `BaseNode`
