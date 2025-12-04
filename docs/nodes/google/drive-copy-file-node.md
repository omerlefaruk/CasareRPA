# DriveCopyFileNode

Create a copy of a file in Google Drive.

`:material-play: Executable`


**Module:** `casare_rpa.nodes.google.drive.drive_files`
**File:** `src\casare_rpa\nodes\google\drive\drive_files.py:348`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `file_id` | INPUT | No | DataType.STRING |
| `new_name` | INPUT | No | DataType.STRING |
| `folder_id` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `new_file_id` | OUTPUT | DataType.STRING |
| `name` | OUTPUT | DataType.STRING |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `new_name` | STRING | `` | No | Name for the copy (default: 'Copy of {original}') |

## Inheritance

Extends: `DriveBaseNode`
