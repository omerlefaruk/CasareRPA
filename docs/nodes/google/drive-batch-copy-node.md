# DriveBatchCopyNode

Copy multiple Google Drive files to a folder in a batch operation.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.google.drive.drive_batch`
**File:** `src\casare_rpa\nodes\google\drive\drive_batch.py:564`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `access_token` | INPUT | No | DataType.STRING |
| `file_ids` | INPUT | No | DataType.ARRAY |
| `folder_id` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `copied_count` | OUTPUT | DataType.INTEGER |
| `failed_count` | OUTPUT | DataType.INTEGER |
| `new_file_ids` | OUTPUT | DataType.ARRAY |
| `results` | OUTPUT | DataType.ARRAY |
| `success` | OUTPUT | DataType.BOOLEAN |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `continue_on_error` | BOOLEAN | `True` | No | Continue copying remaining files if one fails |
| `preserve_name` | BOOLEAN | `True` | No | Keep original file names (otherwise appends ' - Copy') |

## Inheritance

Extends: `BaseNode`
