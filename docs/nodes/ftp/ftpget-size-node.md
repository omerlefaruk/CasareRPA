# FTPGetSizeNode

Get the size of a file on FTP server.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.ftp_nodes`
**File:** `src\casare_rpa\nodes\ftp_nodes.py:884`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `remote_path` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `size` | OUTPUT | DataType.INTEGER |
| `found` | OUTPUT | DataType.BOOLEAN |

## Inheritance

Extends: `BaseNode`
