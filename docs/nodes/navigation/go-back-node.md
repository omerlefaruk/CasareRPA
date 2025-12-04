# GoBackNode

Go back node - navigates back in browser history.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.navigation_nodes`
**File:** `src\casare_rpa\nodes\navigation_nodes.py:321`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `page` | INPUT | No | DataType.PAGE |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `page` | OUTPUT | DataType.PAGE |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `timeout` | INTEGER | `DEFAULT_PAGE_LOAD...` | No | Page load timeout in milliseconds (min: 0) |
| `wait_until` | CHOICE | `load` | No | Navigation event to wait for Choices: load, domcontentloaded, networkidle, commit |
| `retry_count` | INTEGER | `0` | No | Number of retries on failure (min: 0) |
| `retry_interval` | INTEGER | `1000` | No | Delay between retries in milliseconds (min: 0) |

## Inheritance

Extends: `BaseNode`
