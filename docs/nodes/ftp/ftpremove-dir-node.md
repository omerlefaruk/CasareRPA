# FTPRemoveDirNode

Remove a directory on FTP server.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.ftp_nodes`
**File:** `src\casare_rpa\nodes\ftp_nodes.py:723`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `remote_path` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `removed` | OUTPUT | DataType.BOOLEAN |

## Inheritance

Extends: `BaseNode`
