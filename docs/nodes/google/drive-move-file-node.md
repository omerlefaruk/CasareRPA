# DriveMoveFileNode

Move a file to a different folder in Google Drive.

`:material-play: Executable`


**Module:** `casare_rpa.nodes.google.drive.drive_files`
**File:** `src\casare_rpa\nodes\google\drive\drive_files.py:446`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `file_id` | INPUT | No | DataType.STRING |
| `folder_id` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `file_id` | OUTPUT | DataType.STRING |
| `new_parents` | OUTPUT | DataType.LIST |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `folder_id` | STRING | `` | Yes | ID of the destination folder |

## Inheritance

Extends: `DriveBaseNode`
