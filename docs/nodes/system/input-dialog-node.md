# InputDialogNode

Display an input dialog to get user input.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.system.dialog_nodes`
**File:** `src\casare_rpa\nodes\system\dialog_nodes.py:447`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `title` | INPUT | No | DataType.STRING |
| `prompt` | INPUT | No | DataType.STRING |
| `default_value` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `value` | OUTPUT | DataType.STRING |
| `confirmed` | OUTPUT | DataType.BOOLEAN |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `password_mode` | BOOLEAN | `False` | No | Hide input characters |

## Inheritance

Extends: `BaseNode`
