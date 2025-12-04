# DeleteFileNode

Delete a file.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.file.file_system_nodes`
**File:** `src\casare_rpa\nodes\file\file_system_nodes.py:57`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `file_path` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `deleted_path` | OUTPUT | DataType.STRING |
| `success` | OUTPUT | DataType.BOOLEAN |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `file_path` | STRING | `-` | Yes | Path to delete |
| `ignore_missing` | BOOLEAN | `False` | No | Don't error if file doesn't exist |
| `allow_dangerous_paths` | BOOLEAN | `False` | No | Allow access to system directories |

## Inheritance

Extends: `BaseNode`
