# GoToURLNode

Go to URL node - navigates to a specified URL.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.navigation_nodes`
**File:** `src\casare_rpa\nodes\navigation_nodes.py:100`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `page` | INPUT | No | DataType.PAGE |
| `url` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `page` | OUTPUT | DataType.PAGE |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `url` | STRING | `` | No | URL to navigate to |
| `timeout` | INTEGER | `DEFAULT_PAGE_LOAD...` | No | Page load timeout in milliseconds (min: 0) |
| `wait_until` | CHOICE | `load` | No | Navigation event to wait for Choices: load, domcontentloaded, networkidle, commit |
| `referer` | STRING | `` | No | Optional HTTP referer header |
| `retry_count` | INTEGER | `0` | No | Number of retries on navigation failure (min: 0) |
| `retry_interval` | INTEGER | `1000` | No | Delay between retries in milliseconds (min: 0) |
| `screenshot_on_fail` | BOOLEAN | `False` | No | Take screenshot on navigation failure |
| `screenshot_path` | FILE_PATH | `` | No | Path to save failure screenshot |
| `ignore_https_errors` | BOOLEAN | `False` | No | Ignore HTTPS certificate errors |

## Inheritance

Extends: `BaseNode`
