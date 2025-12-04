# CloseBrowserNode

Close browser node - closes the browser instance.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.browser_nodes`
**File:** `src\casare_rpa\nodes\browser_nodes.py:429`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `browser` | INPUT | No | DataType.BROWSER |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `timeout` | INTEGER | `30000` | No | Timeout for close operation in milliseconds (min: 0) |
| `force_close` | BOOLEAN | `False` | No | Force close even if pages have unsaved changes |
| `retry_count` | INTEGER | `0` | No | Number of retries on failure (min: 0) |
| `retry_interval` | INTEGER | `1000` | No | Delay between retries in milliseconds (min: 0) |

## Inheritance

Extends: `BaseNode`
