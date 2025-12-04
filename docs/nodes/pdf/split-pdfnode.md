# SplitPDFNode

Split a PDF into separate files, one per page.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.pdf_nodes`
**File:** `src\casare_rpa\nodes\pdf_nodes.py:368`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `input_file` | INPUT | No | DataType.STRING |
| `output_dir` | INPUT | No | DataType.STRING |

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
| `filename_pattern` | STRING | `page_{n}.pdf` | No | Pattern for output files (use {n} for page number) |

## Inheritance

Extends: `BaseNode`
