# WriteCSVNode

Write data to a CSV file.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.file.structured_data`
**File:** `src\casare_rpa\nodes\file\structured_data.py:240`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `file_path` | INPUT | No | DataType.STRING |
| `data` | INPUT | No | DataType.LIST |
| `headers` | INPUT | No | DataType.LIST |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `file_path` | OUTPUT | DataType.STRING |
| `attachment_file` | OUTPUT | DataType.LIST |
| `row_count` | OUTPUT | DataType.INTEGER |
| `success` | OUTPUT | DataType.BOOLEAN |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `file_path` | STRING | `-` | Yes | File Path |
| `delimiter` | STRING | `,` | No | Delimiter |
| `write_header` | BOOLEAN | `True` | No | Write Header |
| `encoding` | STRING | `utf-8` | No | Encoding |

## Inheritance

Extends: `BaseNode`
