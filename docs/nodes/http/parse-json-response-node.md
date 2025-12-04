# ParseJsonResponseNode

Parse JSON response and extract data using JSONPath-like expressions.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.http.http_advanced`
**File:** `src\casare_rpa\nodes\http\http_advanced.py:156`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `json_data` | INPUT | No | DataType.ANY |
| `path` | INPUT | No | DataType.STRING |
| `default` | INPUT | No | DataType.ANY |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `value` | OUTPUT | DataType.ANY |
| `success` | OUTPUT | DataType.BOOLEAN |
| `error` | OUTPUT | DataType.STRING |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `path` | STRING | `` | No | Path to extract (e.g., 'data.users[0].name') |
| `default` | STRING | `` | No | Default value if path not found |

## Inheritance

Extends: `BaseNode`
