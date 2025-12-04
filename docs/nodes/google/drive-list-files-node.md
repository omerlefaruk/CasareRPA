# DriveListFilesNode

List files in a Google Drive folder.

`:material-play: Executable`


**Module:** `casare_rpa.nodes.google.drive.drive_folders`
**File:** `src\casare_rpa\nodes\google\drive\drive_folders.py:255`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `folder_id` | INPUT | No | DataType.STRING |
| `query` | INPUT | No | DataType.STRING |
| `mime_type` | INPUT | No | DataType.STRING |
| `max_results` | INPUT | No | DataType.INTEGER |
| `order_by` | INPUT | No | DataType.STRING |
| `include_trashed` | INPUT | No | DataType.BOOLEAN |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `files` | OUTPUT | DataType.LIST |
| `file_count` | OUTPUT | DataType.INTEGER |
| `has_more` | OUTPUT | DataType.BOOLEAN |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `mime_type` | CHOICE | `` | No | Filter by MIME type (empty = all types) Choices: , application/vnd.google-apps.folder, application/vnd.google-apps.document, application/vnd.google-apps.spreadsheet, application/vnd.google-apps.presentation, ... (9 total) |
| `order_by` | CHOICE | `name` | No | Sort order for results Choices: name, name desc, modifiedTime, modifiedTime desc, createdTime, ... (6 total) |
| `include_trashed` | BOOLEAN | `False` | No | Include files in trash |

## Inheritance

Extends: `DriveBaseNode`
