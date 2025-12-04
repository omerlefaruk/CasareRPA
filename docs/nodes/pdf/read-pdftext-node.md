# ReadPDFTextNode

Extract text from a PDF file.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.pdf_nodes`
**File:** `src\casare_rpa\nodes\pdf_nodes.py:60`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `file_path` | INPUT | No | DataType.STRING |
| `start_page` | INPUT | No | DataType.INTEGER |
| `end_page` | INPUT | No | DataType.INTEGER |
| `password` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `text` | OUTPUT | DataType.STRING |
| `page_count` | OUTPUT | DataType.INTEGER |
| `pages` | OUTPUT | DataType.LIST |
| `is_encrypted` | OUTPUT | DataType.BOOLEAN |
| `success` | OUTPUT | DataType.BOOLEAN |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `page_separator` | STRING | `

` | No | Separator string between pages in extracted text |
| `password` | STRING | `` | No | Password for encrypted PDFs (optional) |
| `extract_tables` | BOOLEAN | `False` | No | Attempt to extract tables (experimental) |
| `preserve_layout` | BOOLEAN | `False` | No | Try to preserve text layout (experimental) |

## Inheritance

Extends: `BaseNode`
