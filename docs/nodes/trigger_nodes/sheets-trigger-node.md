# SheetsTriggerNode

Google Sheets trigger node that monitors for spreadsheet changes.

`:material-bell: Trigger`


**Module:** `casare_rpa.nodes.trigger_nodes.sheets_trigger_node`
**File:** `src\casare_rpa\nodes\trigger_nodes\sheets_trigger_node.py:107`


## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `spreadsheet_id` | STRING | Spreadsheet ID |
| `sheet_name` | STRING | Sheet Name |
| `event_type` | STRING | Event Type |
| `row_number` | INTEGER | Row Number |
| `column` | STRING | Column |
| `old_value` | ANY | Old Value |
| `new_value` | ANY | New Value |
| `row_data` | LIST | Row Data (List) |
| `row_dict` | DICT | Row Data (Dict) |
| `changed_cells` | LIST | Changed Cells |
| `timestamp` | STRING | Timestamp |
| `raw_data` | DICT | Raw Data |

## Configuration Properties

### Advanced Tab

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `trigger_on_delete` | BOOLEAN | `False` | No | Trigger when rows are deleted |
| `ignore_empty_rows` | BOOLEAN | `True` | No | Don't trigger on completely empty rows |

### Connection Tab

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `credential_name` | STRING | `google` | No | Name of stored Google OAuth credential |

### Properties Tab

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `spreadsheet_id` | STRING | `` | Yes | Google Sheets spreadsheet ID to monitor |
| `sheet_name` | STRING | `Sheet1` | No | Name of the sheet to monitor |
| `range` | STRING | `` | No | Cell range to monitor (empty = entire sheet) |
| `polling_interval` | INTEGER | `30` | No | Seconds between checks for changes |
| `trigger_on_new_row` | BOOLEAN | `True` | No | Trigger when a new row is added |
| `trigger_on_cell_change` | BOOLEAN | `True` | No | Trigger when cell values change |
| `watch_columns` | STRING | `` | No | Comma-separated columns to watch (empty = all) |

## Inheritance

Extends: `BaseTriggerNode`
