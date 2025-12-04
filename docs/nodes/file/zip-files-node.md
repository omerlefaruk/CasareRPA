# ZipFilesNode

Create a ZIP archive from files.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.file.structured_data`
**File:** `src\casare_rpa\nodes\file\structured_data.py:530`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `zip_path` | INPUT | No | DataType.STRING |
| `source_path` | INPUT | No | DataType.STRING |
| `files` | INPUT | No | DataType.LIST |
| `base_dir` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `zip_path` | OUTPUT | DataType.STRING |
| `attachment_file` | OUTPUT | DataType.LIST |
| `file_count` | OUTPUT | DataType.INTEGER |
| `success` | OUTPUT | DataType.BOOLEAN |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `zip_path` | STRING | `-` | Yes | ZIP Path |
| `source_path` | STRING | `` | No | Folder path (zips entire folder) or glob pattern (e.g., *.txt) |
| `base_dir` | STRING | `` | No | Base directory for relative paths in archive (auto-set if source_path is folder) |
| `compression` | CHOICE | `ZIP_DEFLATED` | No | Compression Choices: ZIP_STORED, ZIP_DEFLATED |

## Inheritance

Extends: `BaseNode`
