# HttpDownloadFileNode

Download a file from a URL and save to disk.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.http.http_advanced`
**File:** `src\casare_rpa\nodes\http\http_advanced.py:345`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `url` | INPUT | No | DataType.STRING |
| `save_path` | INPUT | No | DataType.STRING |
| `headers` | INPUT | No | DataType.DICT |
| `timeout` | INPUT | No | DataType.FLOAT |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `file_path` | OUTPUT | DataType.STRING |
| `file_size` | OUTPUT | DataType.INTEGER |
| `success` | OUTPUT | DataType.BOOLEAN |
| `error` | OUTPUT | DataType.STRING |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `url` | STRING | `-` | Yes | URL to download from |
| `save_path` | FILE_PATH | `-` | Yes | Path to save downloaded file |
| `headers` | JSON | `{}` | No | Request headers as JSON object |
| `timeout` | FLOAT | `300.0` | No | Download timeout in seconds (min: 0.1) |
| `overwrite` | BOOLEAN | `True` | No | Overwrite file if it already exists |
| `verify_ssl` | BOOLEAN | `True` | No | Verify SSL certificates |
| `proxy` | STRING | `` | No | HTTP proxy URL (optional) |
| `retry_count` | INTEGER | `0` | No | Number of retry attempts on failure (min: 0) |
| `retry_delay` | FLOAT | `2.0` | No | Delay between retry attempts (min: 0.0) |
| `chunk_size` | INTEGER | `8192` | No | Download chunk size in bytes (min: 512) |

## Inheritance

Extends: `BaseNode`
