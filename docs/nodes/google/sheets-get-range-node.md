# SheetsGetRangeNode

Read a range of values from Google Sheets.

`:material-play: Executable`


**Module:** `casare_rpa.nodes.google.sheets.sheets_read`
**File:** `src\casare_rpa\nodes\google\sheets\sheets_read.py:223`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `range` | INPUT | No | DataType.STRING |
| `value_render_option` | INPUT | No | DataType.STRING |
| `major_dimension` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `values` | OUTPUT | DataType.ARRAY |
| `row_count` | OUTPUT | DataType.INTEGER |
| `column_count` | OUTPUT | DataType.INTEGER |

## Configuration Properties

### Advanced Tab

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `major_dimension` | CHOICE | `ROWS` | No | Whether to return rows or columns as the major dimension Choices: ROWS, COLUMNS |

### Properties Tab

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `range` | STRING | `Sheet1!A1:B10` | Yes | Range in A1 notation (e.g., 'Sheet1!A1:B10') |

## Inheritance

Extends: `SheetsBaseNode`
