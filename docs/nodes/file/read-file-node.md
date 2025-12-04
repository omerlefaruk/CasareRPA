# ReadFileNode

Read content from a text or binary file.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.file.file_read_nodes`
**File:** `src\casare_rpa\nodes\file\file_read_nodes.py:82`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `file_path` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `content` | OUTPUT | DataType.STRING |
| `size` | OUTPUT | DataType.INTEGER |
| `success` | OUTPUT | DataType.BOOLEAN |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `file_path` | STRING | `-` | Yes | Path to the file to read |
| `encoding` | STRING | `utf-8` | No | Text encoding (utf-8, ascii, latin-1, etc.) |
| `binary_mode` | BOOLEAN | `False` | No | Read as binary data (returns bytes instead of string) |
| `errors` | CHOICE | `strict` | No | How to handle encoding errors Choices: strict, ignore, replace, backslashreplace, xmlcharrefreplace |
| `max_size` | INTEGER | `0` | No | Maximum file size to read (0 = unlimited) (min: 0) |
| `allow_dangerous_paths` | BOOLEAN | `False` | No | Allow access to system directories |

## Inheritance

Extends: `BaseNode`
