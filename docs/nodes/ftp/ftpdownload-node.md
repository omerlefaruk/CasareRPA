# FTPDownloadNode

Download a file from FTP server.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.ftp_nodes`
**File:** `src\casare_rpa\nodes\ftp_nodes.py:383`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `remote_path` | INPUT | No | DataType.STRING |
| `local_path` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `downloaded` | OUTPUT | DataType.BOOLEAN |
| `bytes_received` | OUTPUT | DataType.INTEGER |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `binary_mode` | BOOLEAN | `True` | No | Transfer in binary mode (recommended for most files) |
| `overwrite` | BOOLEAN | `False` | No | Overwrite local file if it already exists |
| `retry_count` | INTEGER | `0` | No | Number of download retries on failure (min: 0) |
| `retry_interval` | INTEGER | `2000` | No | Delay between retries in milliseconds (min: 0) |

## Inheritance

Extends: `BaseNode`
