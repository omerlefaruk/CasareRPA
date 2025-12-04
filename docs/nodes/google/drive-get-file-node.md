# DriveGetFileNode

Get file metadata from Google Drive.

`:material-play: Executable`


**Module:** `casare_rpa.nodes.google.drive.drive_files`
**File:** `src\casare_rpa\nodes\google\drive\drive_files.py:725`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `file_id` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `file_id` | OUTPUT | DataType.STRING |
| `name` | OUTPUT | DataType.STRING |
| `mime_type` | OUTPUT | DataType.STRING |
| `size` | OUTPUT | DataType.INTEGER |
| `created_time` | OUTPUT | DataType.STRING |
| `modified_time` | OUTPUT | DataType.STRING |
| `web_view_link` | OUTPUT | DataType.STRING |
| `web_content_link` | OUTPUT | DataType.STRING |
| `parents` | OUTPUT | DataType.LIST |
| `description` | OUTPUT | DataType.STRING |
| `starred` | OUTPUT | DataType.BOOLEAN |
| `trashed` | OUTPUT | DataType.BOOLEAN |
| `shared` | OUTPUT | DataType.BOOLEAN |

## Inheritance

Extends: `DriveBaseNode`
