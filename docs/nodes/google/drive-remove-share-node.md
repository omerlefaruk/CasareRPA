# DriveRemoveShareNode

Remove a permission from a Google Drive file or folder.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.google.drive.drive_share`
**File:** `src\casare_rpa\nodes\google\drive\drive_share.py:275`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `access_token` | INPUT | No | DataType.STRING |
| `file_id` | INPUT | No | DataType.STRING |
| `permission_id` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `success` | OUTPUT | DataType.BOOLEAN |

## Inheritance

Extends: `BaseNode`
