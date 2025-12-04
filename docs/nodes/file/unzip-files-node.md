# UnzipFilesNode

Extract files from a ZIP archive.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.file.structured_data`
**File:** `src\casare_rpa\nodes\file\structured_data.py:712`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `zip_path` | INPUT | No | DataType.STRING |
| `extract_to` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `extract_to` | OUTPUT | DataType.STRING |
| `files` | OUTPUT | DataType.LIST |
| `file_count` | OUTPUT | DataType.INTEGER |
| `success` | OUTPUT | DataType.BOOLEAN |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `zip_path` | STRING | `-` | Yes | ZIP Path |
| `extract_to` | STRING | `-` | Yes | Extract To |

## Inheritance

Extends: `BaseNode`
