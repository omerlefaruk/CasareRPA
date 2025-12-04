# DriveBatchDeleteNode

Delete multiple Google Drive files in a batch operation.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.google.drive.drive_batch`
**File:** `src\casare_rpa\nodes\google\drive\drive_batch.py:207`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `access_token` | INPUT | No | DataType.STRING |
| `file_ids` | INPUT | No | DataType.ARRAY |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `deleted_count` | OUTPUT | DataType.INTEGER |
| `failed_count` | OUTPUT | DataType.INTEGER |
| `results` | OUTPUT | DataType.ARRAY |
| `success` | OUTPUT | DataType.BOOLEAN |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `continue_on_error` | BOOLEAN | `True` | No | Continue deleting remaining files if one fails |

## Inheritance

Extends: `BaseNode`
