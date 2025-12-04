# ListFilesNode

List files in a directory.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.file.directory_nodes`
**File:** `src\casare_rpa\nodes\file\directory_nodes.py:168`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `directory_path` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `files` | OUTPUT | DataType.LIST |
| `count` | OUTPUT | DataType.INTEGER |
| `success` | OUTPUT | DataType.BOOLEAN |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `directory_path` | STRING | `` | No | Directory to list files from (required at runtime) |
| `pattern` | STRING | `*` | No | Glob pattern to filter files (e.g., *.txt, *.py) |
| `recursive` | BOOLEAN | `False` | No | Search subdirectories recursively |
| `allow_dangerous_paths` | BOOLEAN | `False` | No | Allow access to system directories |

## Inheritance

Extends: `BaseNode`
