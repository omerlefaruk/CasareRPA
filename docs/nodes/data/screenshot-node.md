# ScreenshotNode

Screenshot node - captures a screenshot of the page or element.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.data_nodes`
**File:** `src\casare_rpa\nodes\data_nodes.py:421`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `file_path` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `file_path` | OUTPUT | DataType.STRING |
| `attachment_file` | OUTPUT | DataType.LIST |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `file_path` | FILE_PATH | `` | No | Path where screenshot will be saved |
| `selector` | SELECTOR | `` | No | Optional selector for element screenshot |
| `full_page` | BOOLEAN | `False` | No | Whether to capture full scrollable page |
| `type` | CHOICE | `png` | No | Image format: png or jpeg Choices: png, jpeg |
| `quality` | INTEGER | `-` | No | JPEG quality 0-100 (ignored for PNG) (min: 0, max: 100) |
| `scale` | CHOICE | `device` | No | Image scale: css or device Choices: css, device |
| `animations` | CHOICE | `allow` | No | Allow or disable animations during capture Choices: allow, disabled |
| `omit_background` | BOOLEAN | `False` | No | Make background transparent (PNG only) |
| `caret` | CHOICE | `hide` | No | Whether to hide text caret Choices: hide, initial |

## Inheritance

Extends: `BrowserBaseNode`
