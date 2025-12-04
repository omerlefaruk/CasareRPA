# CompareImagesNode

Node to compare two images and return similarity metrics.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.desktop_nodes.screenshot_ocr_nodes`
**File:** `src\casare_rpa\nodes\desktop_nodes\screenshot_ocr_nodes.py:264`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `image1` | ANY | No | First image |
| `image2` | ANY | No | Second image |
| `image1_path` | STRING | No | First image path |
| `image2_path` | STRING | No | Second image path |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `similarity` | FLOAT | Similarity score |
| `is_match` | BOOLEAN | Images match |
| `method` | STRING | Comparison method |

## Inheritance

Extends: `BaseNode`
