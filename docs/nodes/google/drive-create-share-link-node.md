# DriveCreateShareLinkNode

Create a shareable link for a Google Drive file or folder.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.google.drive.drive_share`
**File:** `src\casare_rpa\nodes\google\drive\drive_share.py:500`


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
| `share_link` | OUTPUT | DataType.STRING |
| `permission_id` | OUTPUT | DataType.STRING |
| `success` | OUTPUT | DataType.BOOLEAN |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `access_type` | CHOICE | `anyone` | No | Who can access via the link Choices: anyone, anyoneWithLink |
| `link_role` | CHOICE | `reader` | No | Role granted to anyone accessing via link Choices: reader, writer, commenter |
| `allow_file_discovery` | BOOLEAN | `False` | No | Allow file to appear in search results |

## Inheritance

Extends: `BaseNode`
