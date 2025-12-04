# OCRExtractTextNode

Node to extract text from an image using OCR.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.desktop_nodes.screenshot_ocr_nodes`
**File:** `src\casare_rpa\nodes\desktop_nodes\screenshot_ocr_nodes.py:176`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `image` | ANY | No | Image object (optional) |
| `image_path` | STRING | No | Image file path (optional) |
| `region` | ANY | No | Region dict (optional) |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `text` | STRING | Extracted text |
| `engine_used` | STRING | OCR engine used |
| `success` | BOOLEAN | Extraction succeeded |

## Inheritance

Extends: `BaseNode`
