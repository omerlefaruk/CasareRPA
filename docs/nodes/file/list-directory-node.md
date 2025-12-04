# ListDirectoryNode

List files and directories in a folder.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.file.directory_nodes`
**File:** `src\casare_rpa\nodes\file\directory_nodes.py:302`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `dir_path` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `items` | OUTPUT | DataType.LIST |
| `count` | OUTPUT | DataType.INTEGER |
| `success` | OUTPUT | DataType.BOOLEAN |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `dir_path` | STRING | `-` | Yes | Path to the directory to list |
| `pattern` | STRING | `*` | No | Glob pattern to filter results (e.g., *.txt, *.pdf) |
| `recursive` | BOOLEAN | `False` | No | Search subdirectories recursively |
| `files_only` | BOOLEAN | `False` | No | Only return files (exclude directories) |
| `dirs_only` | BOOLEAN | `False` | No | Only return directories (exclude files) |
| `allow_dangerous_paths` | BOOLEAN | `False` | No | Allow access to system directories |

## Inheritance

Extends: `BaseNode`
