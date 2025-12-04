# CreateDirectoryNode

Create a directory.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.file.directory_nodes`
**File:** `src\casare_rpa\nodes\file\directory_nodes.py:63`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `directory_path` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `dir_path` | OUTPUT | DataType.STRING |
| `success` | OUTPUT | DataType.BOOLEAN |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `directory_path` | STRING | `-` | Yes | Path to create |
| `parents` | BOOLEAN | `True` | No | Create parent directories as needed |
| `exist_ok` | BOOLEAN | `True` | No | Don't error if directory already exists |
| `allow_dangerous_paths` | BOOLEAN | `False` | No | Allow access to system directories |

## Inheritance

Extends: `BaseNode`
