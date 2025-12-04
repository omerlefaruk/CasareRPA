# DriveCreateFolderNode

Create a new folder in Google Drive.

`:material-play: Executable`


**Module:** `casare_rpa.nodes.google.drive.drive_folders`
**File:** `src\casare_rpa\nodes\google\drive\drive_folders.py:114`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `name` | INPUT | No | DataType.STRING |
| `parent_id` | INPUT | No | DataType.STRING |
| `description` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `folder_id` | OUTPUT | DataType.STRING |
| `name` | OUTPUT | DataType.STRING |
| `web_view_link` | OUTPUT | DataType.STRING |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `name` | STRING | `` | Yes | Name for the new folder |
| `parent_id` | STRING | `` | No | Parent folder ID (empty = root) |
| `description` | TEXT | `` | No | Folder description |

## Inheritance

Extends: `DriveBaseNode`
