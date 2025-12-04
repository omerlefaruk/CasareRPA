# DriveShareFileNode

Add a permission to a Google Drive file or folder.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.google.drive.drive_share`
**File:** `src\casare_rpa\nodes\google\drive\drive_share.py:117`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `access_token` | INPUT | No | DataType.STRING |
| `file_id` | INPUT | No | DataType.STRING |
| `email` | INPUT | No | DataType.STRING |
| `role` | INPUT | No | DataType.STRING |
| `type` | INPUT | No | DataType.STRING |
| `domain` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `permission_id` | OUTPUT | DataType.STRING |
| `permission` | OUTPUT | DataType.DICT |
| `success` | OUTPUT | DataType.BOOLEAN |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `send_notification` | BOOLEAN | `True` | No | Send email notification to the user being granted access |
| `email_message` | TEXT | `` | No | Custom message to include in the notification email |
| `move_to_new_owners_root` | BOOLEAN | `False` | No | For ownership transfers, move file to new owner's root folder |
| `transfer_ownership` | BOOLEAN | `False` | No | Transfer ownership to this user (requires role=owner) |

## Inheritance

Extends: `BaseNode`
