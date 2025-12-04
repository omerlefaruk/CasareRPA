# CaptureElementImageNode

Node to capture an image of a specific desktop element.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.desktop_nodes.screenshot_ocr_nodes`
**File:** `src\casare_rpa\nodes\desktop_nodes\screenshot_ocr_nodes.py:92`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `element` | ANY | No | Element to capture |
| `file_path` | STRING | No | Save path (optional) |
| `padding` | INTEGER | No | Padding pixels |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `image` | ANY | Captured image |
| `file_path` | STRING | Saved file path |
| `success` | BOOLEAN | Capture succeeded |

## Inheritance

Extends: `BaseNode`
