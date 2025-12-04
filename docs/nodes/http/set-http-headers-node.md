# SetHttpHeadersNode

Configure HTTP headers for subsequent requests.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.http.http_advanced`
**File:** `src\casare_rpa\nodes\http\http_advanced.py:60`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `base_headers` | INPUT | No | DataType.DICT |
| `header_name` | INPUT | No | DataType.STRING |
| `header_value` | INPUT | No | DataType.STRING |
| `headers_json` | INPUT | No | DataType.DICT |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `headers` | OUTPUT | DataType.DICT |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `header_name` | STRING | `` | No | Single header name to add |
| `header_value` | STRING | `` | No | Single header value to add |
| `headers_json` | JSON | `{}` | No | Multiple headers as JSON object |

## Inheritance

Extends: `BaseNode`
