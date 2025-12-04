# BuildUrlNode

Build a URL with query parameters.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.http.http_advanced`
**File:** `src\casare_rpa\nodes\http\http_advanced.py:741`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `base_url` | INPUT | No | DataType.STRING |
| `path` | INPUT | No | DataType.STRING |
| `params` | INPUT | No | DataType.DICT |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `url` | OUTPUT | DataType.STRING |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `base_url` | STRING | `-` | Yes | Base URL (e.g., https://api.example.com) |
| `path` | STRING | `` | No | Path to append to base URL |
| `params` | JSON | `{}` | No | Query parameters as JSON object |

## Inheritance

Extends: `BaseNode`
