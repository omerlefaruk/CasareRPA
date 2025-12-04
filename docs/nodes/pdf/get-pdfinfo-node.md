# GetPDFInfoNode

Get metadata and information from a PDF file.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.pdf_nodes`
**File:** `src\casare_rpa\nodes\pdf_nodes.py:180`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `file_path` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `page_count` | OUTPUT | DataType.INTEGER |
| `title` | OUTPUT | DataType.STRING |
| `author` | OUTPUT | DataType.STRING |
| `subject` | OUTPUT | DataType.STRING |
| `creator` | OUTPUT | DataType.STRING |
| `producer` | OUTPUT | DataType.STRING |
| `creation_date` | OUTPUT | DataType.STRING |
| `modification_date` | OUTPUT | DataType.STRING |
| `is_encrypted` | OUTPUT | DataType.BOOLEAN |
| `success` | OUTPUT | DataType.BOOLEAN |

## Inheritance

Extends: `BaseNode`
