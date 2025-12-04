# FTPConnectNode

Connect to an FTP server.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.ftp_nodes`
**File:** `src\casare_rpa\nodes\ftp_nodes.py:77`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `host` | INPUT | No | DataType.STRING |
| `port` | INPUT | No | DataType.INTEGER |
| `username` | INPUT | No | DataType.STRING |
| `password` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `connected` | OUTPUT | DataType.BOOLEAN |
| `server_message` | OUTPUT | DataType.STRING |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `passive` | BOOLEAN | `True` | No | Use passive mode for FTP connection |
| `timeout` | INTEGER | `30` | No | Connection timeout in seconds (min: 1) |
| `use_tls` | BOOLEAN | `False` | No | Use FTPS (FTP over TLS) |
| `retry_count` | INTEGER | `0` | No | Number of connection retries on failure (min: 0) |
| `retry_interval` | INTEGER | `2000` | No | Delay between retries in milliseconds (min: 0) |

## Inheritance

Extends: `BaseNode`
