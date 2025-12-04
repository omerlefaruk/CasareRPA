# NewTabNode

New tab node - creates a new browser tab/page.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.browser_nodes`
**File:** `src\casare_rpa\nodes\browser_nodes.py:580`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `browser` | INPUT | No | DataType.BROWSER |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `page` | OUTPUT | DataType.PAGE |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `tab_name` | STRING | `main` | Yes | Name to identify this tab |
| `url` | STRING | `` | No | Optional URL to navigate to after creating tab |
| `timeout` | INTEGER | `30000` | No | Navigation timeout in milliseconds (min: 0) |
| `wait_until` | CHOICE | `load` | No | Navigation wait event Choices: load, domcontentloaded, networkidle, commit |
| `retry_count` | INTEGER | `0` | No | Number of retries on failure (min: 0) |
| `retry_interval` | INTEGER | `1000` | No | Delay between retries in milliseconds (min: 0) |
| `screenshot_on_fail` | BOOLEAN | `False` | No | Take screenshot when tab creation fails |
| `screenshot_path` | FILE_PATH | `` | No | Path for failure screenshot (auto-generated if empty) |

## Inheritance

Extends: `BaseNode`
