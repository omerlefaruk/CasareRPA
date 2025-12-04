# CaptureScreenshotNode

Node to capture a screenshot of the screen or a specific region.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.desktop_nodes.screenshot_ocr_nodes`
**File:** `src\casare_rpa\nodes\desktop_nodes\screenshot_ocr_nodes.py:20`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `file_path` | STRING | No | Save path (optional) |
| `region` | ANY | No | Region dict (optional) |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `image` | ANY | Captured image |
| `file_path` | STRING | Saved file path |
| `success` | BOOLEAN | Capture succeeded |

## Inheritance

Extends: `BaseNode`
