# DriveSearchFilesNode

Search for files in Google Drive using query syntax.

`:material-play: Executable`


**Module:** `casare_rpa.nodes.google.drive.drive_folders`
**File:** `src\casare_rpa\nodes\google\drive\drive_folders.py:421`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `query` | INPUT | No | DataType.STRING |
| `mime_type` | INPUT | No | DataType.STRING |
| `max_results` | INPUT | No | DataType.INTEGER |
| `include_trashed` | INPUT | No | DataType.BOOLEAN |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `files` | OUTPUT | DataType.LIST |
| `file_count` | OUTPUT | DataType.INTEGER |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `query` | TEXT | `` | Yes | Google Drive API query syntax |
| `mime_type` | CHOICE | `` | No | Additional MIME type filter (empty = all types) Choices: , application/vnd.google-apps.folder, application/vnd.google-apps.document, application/vnd.google-apps.spreadsheet, application/vnd.google-apps.presentation, ... (9 total) |
| `include_trashed` | BOOLEAN | `False` | No | Include files in trash |

## Inheritance

Extends: `DriveBaseNode`
