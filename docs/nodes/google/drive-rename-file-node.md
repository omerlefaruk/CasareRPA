# DriveRenameFileNode

Rename a file or folder in Google Drive.

`:material-play: Executable`


**Module:** `casare_rpa.nodes.google.drive.drive_files`
**File:** `src\casare_rpa\nodes\google\drive\drive_files.py:638`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `file_id` | INPUT | No | DataType.STRING |
| `new_name` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `file_id` | OUTPUT | DataType.STRING |
| `name` | OUTPUT | DataType.STRING |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `new_name` | STRING | `` | Yes | New name for the file |

## Inheritance

Extends: `DriveBaseNode`
