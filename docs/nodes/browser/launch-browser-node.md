# LaunchBrowserNode

Launch browser node - creates a new browser instance.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.browser_nodes`
**File:** `src\casare_rpa\nodes\browser_nodes.py:154`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `url` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `browser` | OUTPUT | DataType.BROWSER |
| `page` | OUTPUT | DataType.PAGE |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `url` | STRING | `` | No | Initial URL to navigate to after launching browser |
| `browser_type` | CHOICE | `DEFAULT_BROWSER` | No | Browser to launch (chromium, firefox, or webkit) Choices: chromium, firefox, webkit |
| `headless` | BOOLEAN | `HEADLESS_MODE` | No | Run browser without visible window |
| `slow_mo` | INTEGER | `0` | No | Slow down operations by milliseconds (for debugging) (min: 0) |
| `channel` | STRING | `` | No | Browser channel (chrome, msedge, chrome-beta) - chromium only |
| `viewport_width` | INTEGER | `1280` | No | Browser viewport width in pixels (min: 1) |
| `viewport_height` | INTEGER | `720` | No | Browser viewport height in pixels (min: 1) |
| `user_agent` | STRING | `` | No | Custom user agent string |
| `locale` | STRING | `` | No | Browser locale (e.g., en-US, es-ES) |
| `timezone_id` | STRING | `` | No | Timezone identifier (e.g., America/New_York) |
| `color_scheme` | CHOICE | `light` | No | Preferred color scheme for the browser Choices: light, dark, no-preference |
| `ignore_https_errors` | BOOLEAN | `False` | No | Ignore HTTPS certificate errors |
| `proxy_server` | STRING | `` | No | Proxy server URL |
| `retry_count` | INTEGER | `0` | No | Number of retries on failure (min: 0) |
| `retry_interval` | INTEGER | `2000` | No | Delay between retries in milliseconds (min: 0) |
| `do_not_close` | BOOLEAN | `False` | No | Keep browser open after workflow execution completes |

## Inheritance

Extends: `BaseNode`
