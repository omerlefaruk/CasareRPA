# GetAllImagesNode

Get all images from the current page.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.browser_nodes`
**File:** `src\casare_rpa\nodes\browser_nodes.py:774`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `images` | OUTPUT | DataType.LIST |
| `count` | OUTPUT | DataType.INTEGER |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `min_width` | INTEGER | `0` | No | Minimum image width in pixels (0 = no filter) (min: 0) |
| `min_height` | INTEGER | `0` | No | Minimum image height in pixels (0 = no filter) (min: 0) |
| `include_backgrounds` | BOOLEAN | `True` | No | Include CSS background images |
| `file_types` | STRING | `` | No | Comma-separated file extensions to include (empty = all) |

## Inheritance

Extends: `BaseNode`
