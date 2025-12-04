# FTPUploadNode

Upload a file to FTP server.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.ftp_nodes`
**File:** `src\casare_rpa\nodes\ftp_nodes.py:229`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `local_path` | INPUT | No | DataType.STRING |
| `remote_path` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `uploaded` | OUTPUT | DataType.BOOLEAN |
| `bytes_sent` | OUTPUT | DataType.INTEGER |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `binary_mode` | BOOLEAN | `True` | No | Transfer in binary mode (recommended for most files) |
| `create_dirs` | BOOLEAN | `False` | No | Create remote directories if they don't exist |
| `retry_count` | INTEGER | `0` | No | Number of upload retries on failure (min: 0) |
| `retry_interval` | INTEGER | `2000` | No | Delay between retries in milliseconds (min: 0) |

## Inheritance

Extends: `BaseNode`
