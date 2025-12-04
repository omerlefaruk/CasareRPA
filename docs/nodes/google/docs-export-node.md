# DocsExportNode

Export a Google Doc to various formats.

`:material-play: Executable`


**Module:** `casare_rpa.nodes.google.docs.docs_read`
**File:** `src\casare_rpa\nodes\google\docs\docs_read.py:240`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `format` | INPUT | No | DataType.STRING |
| `output_path` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `content` | OUTPUT | DataType.OBJECT |
| `output_path` | OUTPUT | DataType.STRING |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `format` | CHOICE | `PDF` | No | Target format for export Choices: PDF, HTML, TXT, DOCX, ODT, ... (7 total) |
| `output_path` | STRING | `` | No | File path to save exported document (optional, returns bytes if empty) |

## Inheritance

Extends: `DocsBaseNode`
