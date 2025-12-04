# FileExistsNode

Check if a file or directory exists.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.file.path_nodes`
**File:** `src\casare_rpa\nodes\file\path_nodes.py:53`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `path` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `exists` | OUTPUT | DataType.BOOLEAN |
| `is_file` | OUTPUT | DataType.BOOLEAN |
| `is_dir` | OUTPUT | DataType.BOOLEAN |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `path` | STRING | `-` | Yes | File or directory path to check |
| `check_type` | CHOICE | `any` | No | Type of path to check: file only, directory only, or any Choices: file, directory, any |
| `allow_dangerous_paths` | BOOLEAN | `False` | No | Allow access to system directories (use with caution) |

## Inheritance

Extends: `BaseNode`
