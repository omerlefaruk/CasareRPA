# WriteFileNode

Write content to a file, creating or overwriting.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.file.file_write_nodes`
**File:** `src\casare_rpa\nodes\file\file_write_nodes.py:96`


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
| `attachment_file` | OUTPUT | DataType.LIST |
| `bytes_written` | OUTPUT | DataType.INTEGER |
| `success` | OUTPUT | DataType.BOOLEAN |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `file_path` | STRING | `-` | Yes | Path to write to |
| `content` | STRING | `-` | Yes | Content to write to file |
| `encoding` | STRING | `utf-8` | No | Text encoding |
| `binary_mode` | BOOLEAN | `False` | No | Write as binary data |
| `create_dirs` | BOOLEAN | `True` | No | Create parent directories if needed |
| `errors` | CHOICE | `strict` | No | How to handle encoding errors Choices: strict, ignore, replace, backslashreplace, xmlcharrefreplace |
| `append_mode` | BOOLEAN | `False` | No | Append to file instead of overwrite |
| `allow_dangerous_paths` | BOOLEAN | `False` | No | Allow access to system directories |

## Inheritance

Extends: `BaseNode`
