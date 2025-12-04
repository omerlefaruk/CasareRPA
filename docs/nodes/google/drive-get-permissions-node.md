# DriveGetPermissionsNode

List all permissions on a Google Drive file or folder.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.google.drive.drive_share`
**File:** `src\casare_rpa\nodes\google\drive\drive_share.py:365`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `access_token` | INPUT | No | DataType.STRING |
| `file_id` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `permissions` | OUTPUT | DataType.ARRAY |
| `count` | OUTPUT | DataType.INTEGER |
| `success` | OUTPUT | DataType.BOOLEAN |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `include_permissions_for_view` | BOOLEAN | `False` | No | Include permissions for published files |

## Inheritance

Extends: `BaseNode`
