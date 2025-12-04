# HttpRequestNode

Generic HTTP request node supporting all HTTP methods.

`:material-play: Executable`


**Module:** `casare_rpa.nodes.http.http_basic`
**File:** `src\casare_rpa\nodes\http\http_basic.py:146`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `url` | INPUT | No | DataType.STRING |
| `method` | INPUT | No | DataType.STRING |
| `headers` | INPUT | No | DataType.DICT |
| `body` | INPUT | No | DataType.ANY |
| `params` | INPUT | No | DataType.DICT |
| `timeout` | INPUT | No | DataType.FLOAT |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `method` | CHOICE | `GET` | No | HTTP request method Choices: GET, POST, PUT, PATCH, DELETE, ... (7 total) |
| `follow_redirects` | BOOLEAN | `True` | No | Automatically follow HTTP redirects |
| `max_redirects` | INTEGER | `10` | No | Maximum number of redirects to follow (min: 0) |
| `proxy` | STRING | `` | No | HTTP proxy URL (optional) |
| `response_encoding` | STRING | `` | No | Force specific response encoding (optional) |

## Inheritance

Extends: `HttpBaseNode`
