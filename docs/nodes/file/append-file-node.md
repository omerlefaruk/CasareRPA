# AppendFileNode

Append content to an existing file.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.file.file_write_nodes`
**File:** `src\casare_rpa\nodes\file\file_write_nodes.py:243`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `file_path` | INPUT | No | DataType.STRING |
| `content` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `file_path` | OUTPUT | DataType.STRING |
| `bytes_written` | OUTPUT | DataType.INTEGER |
| `success` | OUTPUT | DataType.BOOLEAN |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `file_path` | STRING | `-` | Yes | Path to append to |
| `content` | STRING | `-` | Yes | Content to append to file |
| `encoding` | STRING | `utf-8` | No | Text encoding |
| `create_if_missing` | BOOLEAN | `True` | No | Create file if it doesn't exist |
| `allow_dangerous_paths` | BOOLEAN | `False` | No | Allow access to system directories |

## Inheritance

Extends: `BaseNode`
