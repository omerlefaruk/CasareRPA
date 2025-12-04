# HttpUploadFileNode

Upload a file via HTTP POST multipart/form-data.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.http.http_advanced`
**File:** `src\casare_rpa\nodes\http\http_advanced.py:557`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `url` | INPUT | No | DataType.STRING |
| `file_path` | INPUT | No | DataType.STRING |
| `field_name` | INPUT | No | DataType.STRING |
| `headers` | INPUT | No | DataType.DICT |
| `extra_fields` | INPUT | No | DataType.DICT |
| `timeout` | INPUT | No | DataType.FLOAT |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `response_body` | OUTPUT | DataType.STRING |
| `response_json` | OUTPUT | DataType.ANY |
| `status_code` | OUTPUT | DataType.INTEGER |
| `success` | OUTPUT | DataType.BOOLEAN |
| `error` | OUTPUT | DataType.STRING |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `url` | STRING | `-` | Yes | Upload URL |
| `file_path` | FILE_PATH | `-` | Yes | Path to file to upload |
| `field_name` | STRING | `file` | No | Form field name for the file |
| `headers` | JSON | `{}` | No | Additional headers as JSON object |
| `extra_fields` | JSON | `{}` | No | Extra form fields as JSON object |
| `timeout` | FLOAT | `300.0` | No | Upload timeout in seconds (min: 0.1) |
| `verify_ssl` | BOOLEAN | `True` | No | Verify SSL certificates |
| `retry_count` | INTEGER | `0` | No | Number of retry attempts on failure (min: 0) |
| `retry_delay` | FLOAT | `2.0` | No | Delay between retry attempts (min: 0.0) |

## Inheritance

Extends: `BaseNode`
