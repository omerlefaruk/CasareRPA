# PDFToImagesNode

Convert PDF pages to images.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.pdf_nodes`
**File:** `src\casare_rpa\nodes\pdf_nodes.py:573`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `input_file` | INPUT | No | DataType.STRING |
| `output_dir` | INPUT | No | DataType.STRING |
| `start_page` | INPUT | No | DataType.INTEGER |
| `end_page` | INPUT | No | DataType.INTEGER |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `output_files` | OUTPUT | DataType.LIST |
| `page_count` | OUTPUT | DataType.INTEGER |
| `success` | OUTPUT | DataType.BOOLEAN |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `dpi` | INTEGER | `200` | No | Resolution in dots per inch (min: 72, max: 600) |
| `format` | CHOICE | `png` | No | Output image format Choices: png, jpg, jpeg, bmp, tiff |

## Inheritance

Extends: `BaseNode`
