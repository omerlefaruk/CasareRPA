# CopyFileNode

Copy a file to a new location.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.file.file_system_nodes`
**File:** `src\casare_rpa\nodes\file\file_system_nodes.py:187`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `source_path` | INPUT | No | DataType.STRING |
| `dest_path` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `dest_path` | OUTPUT | DataType.STRING |
| `bytes_copied` | OUTPUT | DataType.INTEGER |
| `success` | OUTPUT | DataType.BOOLEAN |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `source_path` | STRING | `-` | Yes | Path to the file to copy |
| `dest_path` | STRING | `-` | Yes | Path to copy the file to |
| `overwrite` | BOOLEAN | `False` | No | Overwrite if destination exists |
| `create_dirs` | BOOLEAN | `True` | No | Create destination directories if needed |
| `allow_dangerous_paths` | BOOLEAN | `False` | No | Allow access to system directories |

## Inheritance

Extends: `BaseNode`
