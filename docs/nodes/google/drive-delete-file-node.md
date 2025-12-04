# DriveDeleteFileNode

Delete or trash a file in Google Drive.

`:material-play: Executable`


**Module:** `casare_rpa.nodes.google.drive.drive_files`
**File:** `src\casare_rpa\nodes\google\drive\drive_files.py:544`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `file_id` | INPUT | No | DataType.STRING |
| `permanent` | INPUT | No | DataType.BOOLEAN |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `file_id` | OUTPUT | DataType.STRING |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `permanent` | BOOLEAN | `False` | No | If True, permanently delete. If False, move to trash. |

## Inheritance

Extends: `DriveBaseNode`
