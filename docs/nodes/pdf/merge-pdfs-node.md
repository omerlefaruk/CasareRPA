# MergePDFsNode

Merge multiple PDF files into one.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.pdf_nodes`
**File:** `src\casare_rpa\nodes\pdf_nodes.py:272`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `input_files` | INPUT | No | DataType.LIST |
| `output_path` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `output_path` | OUTPUT | DataType.STRING |
| `attachment_file` | OUTPUT | DataType.LIST |
| `page_count` | OUTPUT | DataType.INTEGER |
| `success` | OUTPUT | DataType.BOOLEAN |

## Inheritance

Extends: `BaseNode`
