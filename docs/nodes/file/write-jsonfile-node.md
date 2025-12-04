# WriteJSONFileNode

Write data to a JSON file.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.file.structured_data`
**File:** `src\casare_rpa\nodes\file\structured_data.py:427`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `file_path` | INPUT | No | DataType.STRING |
| `data` | INPUT | No | DataType.ANY |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `file_path` | OUTPUT | DataType.STRING |
| `attachment_file` | OUTPUT | DataType.LIST |
| `success` | OUTPUT | DataType.BOOLEAN |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `file_path` | STRING | `-` | Yes | File Path |
| `encoding` | STRING | `utf-8` | No | Encoding |
| `indent` | INTEGER | `2` | No | Indent |
| `ensure_ascii` | BOOLEAN | `False` | No | Ensure ASCII |

## Inheritance

Extends: `BaseNode`
