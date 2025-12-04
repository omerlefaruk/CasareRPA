# GetFileInfoNode

Get detailed information about a file.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.file.path_nodes`
**File:** `src\casare_rpa\nodes\file\path_nodes.py:232`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `file_path` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `size` | OUTPUT | DataType.INTEGER |
| `created` | OUTPUT | DataType.STRING |
| `modified` | OUTPUT | DataType.STRING |
| `extension` | OUTPUT | DataType.STRING |
| `name` | OUTPUT | DataType.STRING |
| `parent` | OUTPUT | DataType.STRING |
| `success` | OUTPUT | DataType.BOOLEAN |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `file_path` | STRING | `-` | Yes | Path to the file to get information about |
| `allow_dangerous_paths` | BOOLEAN | `False` | No | Allow access to system directories (use with caution) |

## Inheritance

Extends: `BaseNode`
