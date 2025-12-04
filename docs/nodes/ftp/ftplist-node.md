# FTPListNode

List contents of a directory on FTP server.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.ftp_nodes`
**File:** `src\casare_rpa\nodes\ftp_nodes.py:521`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `remote_path` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `items` | OUTPUT | DataType.LIST |
| `count` | OUTPUT | DataType.INTEGER |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `detailed` | BOOLEAN | `False` | No | Get detailed file information instead of just names |

## Inheritance

Extends: `BaseNode`
