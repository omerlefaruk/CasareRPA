# DriveDownloadFileNode

Download a file from Google Drive.

`:material-play: Executable`


**Module:** `casare_rpa.nodes.google.drive.drive_files`
**File:** `src\casare_rpa\nodes\google\drive\drive_files.py:245`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `file_id` | INPUT | No | DataType.STRING |
| `destination_path` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `file_path` | OUTPUT | DataType.STRING |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `destination_path` | STRING | `` | Yes | Local path to save the downloaded file |

## Inheritance

Extends: `DriveBaseNode`
