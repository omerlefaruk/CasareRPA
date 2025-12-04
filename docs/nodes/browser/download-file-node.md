# DownloadFileNode

Download a file from URL to local path.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.browser_nodes`
**File:** `src\casare_rpa\nodes\browser_nodes.py:970`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `url` | INPUT | No | DataType.STRING |
| `filename` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `path` | OUTPUT | DataType.STRING |
| `attachment_file` | OUTPUT | DataType.LIST |
| `size` | OUTPUT | DataType.INTEGER |
| `success` | OUTPUT | DataType.BOOLEAN |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `save_path` | FILE_PATH | `` | No | Local file path to save to (supports {{variables}}) |
| `use_browser` | BOOLEAN | `False` | No | Use browser context for download (for authenticated sites) |
| `timeout` | INTEGER | `30000` | No | Download timeout in milliseconds (min: 0) |
| `overwrite` | BOOLEAN | `True` | No | Overwrite existing file if it exists |
| `verify_ssl` | BOOLEAN | `True` | No | Verify SSL certificate when downloading. Disable only for trusted internal sites with self-signed certificates. |

## Inheritance

Extends: `BaseNode`
