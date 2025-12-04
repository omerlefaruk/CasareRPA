# ReadCSVNode

Read and parse a CSV file.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.file.structured_data`
**File:** `src\casare_rpa\nodes\file\structured_data.py:101`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `file_path` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `data` | OUTPUT | DataType.LIST |
| `headers` | OUTPUT | DataType.LIST |
| `row_count` | OUTPUT | DataType.INTEGER |
| `success` | OUTPUT | DataType.BOOLEAN |

## Configuration Properties

### Advanced Tab

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `quotechar` | STRING | `"` | No | Quote Char |
| `skip_rows` | INTEGER | `0` | No | Skip Rows |
| `max_rows` | INTEGER | `0` | No | Max Rows (0=unlimited) |
| `strict` | BOOLEAN | `False` | No | Strict Mode |

### Properties Tab

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `file_path` | STRING | `-` | Yes | File Path |
| `delimiter` | STRING | `,` | No | Delimiter |
| `has_header` | BOOLEAN | `True` | No | Has Header |
| `encoding` | STRING | `utf-8` | No | Encoding |

## Inheritance

Extends: `BaseNode`
