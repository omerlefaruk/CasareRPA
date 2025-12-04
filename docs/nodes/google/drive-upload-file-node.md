# DriveUploadFileNode

Upload a file to Google Drive.

`:material-play: Executable`


**Module:** `casare_rpa.nodes.google.drive.drive_files`
**File:** `src\casare_rpa\nodes\google\drive\drive_files.py:117`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `file_path` | INPUT | No | DataType.STRING |
| `folder_id` | INPUT | No | DataType.STRING |
| `file_name` | INPUT | No | DataType.STRING |
| `mime_type` | INPUT | No | DataType.STRING |
| `description` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `file_id` | OUTPUT | DataType.STRING |
| `name` | OUTPUT | DataType.STRING |
| `web_view_link` | OUTPUT | DataType.STRING |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `file_path` | STRING | `` | Yes | Local path to the file to upload |
| `file_name` | STRING | `` | No | Name in Drive (default: local filename) |
| `mime_type` | STRING | `` | No | File MIME type (auto-detected if empty) |
| `description` | TEXT | `` | No | File description in Drive |

## Inheritance

Extends: `DriveBaseNode`
