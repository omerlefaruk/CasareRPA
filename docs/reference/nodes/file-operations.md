# File Operations Nodes

File operations nodes provide comprehensive file system capabilities including reading, writing, copying, moving, and working with structured data formats (CSV, JSON, ZIP).

## Overview

| Category | Nodes |
|----------|-------|
| **Basic I/O** | ReadFileNode, WriteFileNode, AppendFileNode |
| **Structured Data** | ReadCSVNode, WriteCSVNode, ReadJSONFileNode, WriteJSONFileNode |
| **Archive** | ZipFilesNode, UnzipFilesNode |
| **File System** | CopyFileNode, MoveFileNode, DeleteFileNode, FileExistsNode |
| **Directory** | ListDirectoryNode, CreateDirectoryNode, DeleteDirectoryNode |
| **Path** | GetFileInfoNode, JoinPathNode, GetFilenameNode |

## Security

> **Important:** All file operations are subject to path sandboxing. By default, access to system directories (Windows, Program Files, etc.) is blocked. Use `allow_dangerous_paths: true` only when absolutely necessary.

---

## Basic File I/O

### ReadFileNode

Read text or binary content from a file.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `file_path` | STRING | (required) | Path to file to read |
| `encoding` | STRING | `utf-8` | Text encoding (utf-8, ascii, latin-1) |
| `binary_mode` | BOOLEAN | `false` | Read as binary data |
| `errors` | CHOICE | `strict` | Error handling: strict, ignore, replace |
| `max_size` | INTEGER | `0` | Max file size in bytes (0 = unlimited) |
| `allow_dangerous_paths` | BOOLEAN | `false` | Allow system directory access |

#### Ports

**Inputs:**
- `file_path` (STRING) - File path override

**Outputs:**
- `content` (STRING/BYTES) - File content
- `size` (INTEGER) - File size in bytes
- `success` (BOOLEAN) - Read success

#### Example

```python
# Read text file
read_file = ReadFileNode(
    node_id="read_config",
    config={
        "file_path": "C:\\config\\settings.txt",
        "encoding": "utf-8"
    }
)

# Read binary file
read_binary = ReadFileNode(
    node_id="read_image",
    config={
        "file_path": "{{image_path}}",
        "binary_mode": True
    }
)
```

---

### WriteFileNode

Write content to a file, creating or overwriting.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `file_path` | STRING | (required) | Path to write to |
| `content` | STRING | (required) | Content to write |
| `encoding` | STRING | `utf-8` | Text encoding |
| `binary_mode` | BOOLEAN | `false` | Write as binary |
| `create_dirs` | BOOLEAN | `true` | Create parent directories |
| `errors` | CHOICE | `strict` | Error handling mode |
| `append_mode` | BOOLEAN | `false` | Append instead of overwrite |
| `allow_dangerous_paths` | BOOLEAN | `false` | Allow system directories |

#### Ports

**Inputs:**
- `file_path` (STRING) - File path override
- `content` (STRING) - Content override

**Outputs:**
- `file_path` (STRING) - Written file path
- `attachment_file` (LIST) - File path as list (for email attachments)
- `bytes_written` (INTEGER) - Bytes written
- `success` (BOOLEAN) - Write success

#### Example

```python
# Write report to file
write_file = WriteFileNode(
    node_id="save_report",
    config={
        "file_path": "C:\\Reports\\daily_{{date}}.txt",
        "content": "{{report_content}}",
        "create_dirs": True
    }
)
```

---

### AppendFileNode

Append content to an existing file.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `file_path` | STRING | (required) | Path to append to |
| `content` | STRING | (required) | Content to append |
| `encoding` | STRING | `utf-8` | Text encoding |
| `create_if_missing` | BOOLEAN | `true` | Create file if it doesn't exist |
| `allow_dangerous_paths` | BOOLEAN | `false` | Allow system directories |

#### Ports

**Outputs:**
- `file_path` (STRING) - File path
- `bytes_written` (INTEGER) - Bytes appended
- `success` (BOOLEAN) - Append success

#### Example

```python
# Append log entry
append_log = AppendFileNode(
    node_id="log_entry",
    config={
        "file_path": "C:\\Logs\\activity.log",
        "content": "{{timestamp}} - {{event}}\n"
    }
)
```

---

## Structured Data Nodes

### ReadCSVNode

Read and parse a CSV file.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `file_path` | STRING | (required) | Path to CSV file |
| `delimiter` | STRING | `,` | Field delimiter |
| `has_header` | BOOLEAN | `true` | First row is header |
| `encoding` | STRING | `utf-8` | File encoding |
| `quotechar` | STRING | `"` | Quote character (Advanced tab) |
| `skip_rows` | INTEGER | `0` | Skip N rows at start (Advanced) |
| `max_rows` | INTEGER | `0` | Max rows to read (0 = all) (Advanced) |
| `strict` | BOOLEAN | `false` | Strict parsing mode (Advanced) |

#### Ports

**Inputs:**
- `file_path` (STRING) - File path override

**Outputs:**
- `data` (LIST) - Parsed rows (dicts if has_header, else lists)
- `headers` (LIST) - Column headers
- `row_count` (INTEGER) - Number of rows
- `success` (BOOLEAN) - Parse success

#### Example

```python
# Read CSV with headers
read_csv = ReadCSVNode(
    node_id="read_data",
    config={
        "file_path": "C:\\Data\\customers.csv",
        "delimiter": ",",
        "has_header": True
    }
)
# Output: [{"name": "John", "email": "john@example.com"}, ...]

# Read CSV without headers
read_csv_raw = ReadCSVNode(
    node_id="read_raw",
    config={
        "file_path": "C:\\Data\\values.csv",
        "has_header": False
    }
)
# Output: [["John", "john@example.com"], ...]
```

---

### WriteCSVNode

Write data to a CSV file.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `file_path` | STRING | (required) | Output path |
| `delimiter` | STRING | `,` | Field delimiter |
| `write_header` | BOOLEAN | `true` | Write header row |
| `encoding` | STRING | `utf-8` | File encoding |

#### Ports

**Inputs:**
- `file_path` (STRING) - File path override
- `data` (LIST) - Data rows (dicts or lists)
- `headers` (LIST) - Column headers (optional if data is dicts)

**Outputs:**
- `file_path` (STRING) - Written file path
- `attachment_file` (LIST) - File path list
- `row_count` (INTEGER) - Rows written
- `success` (BOOLEAN) - Write success

#### Example

```python
# Write data to CSV
write_csv = WriteCSVNode(
    node_id="export_data",
    config={
        "file_path": "C:\\Export\\results_{{date}}.csv",
        "write_header": True
    }
)
# Connect data input port with list of dicts
```

---

### ReadJSONFileNode

Read and parse a JSON file.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `file_path` | STRING | (required) | Path to JSON file |
| `encoding` | STRING | `utf-8` | File encoding |

#### Ports

**Inputs:**
- `file_path` (STRING) - File path override

**Outputs:**
- `data` (ANY) - Parsed JSON data
- `success` (BOOLEAN) - Parse success

#### Example

```python
# Read configuration JSON
read_json = ReadJSONFileNode(
    node_id="load_config",
    config={
        "file_path": "C:\\config\\settings.json"
    }
)
```

---

### WriteJSONFileNode

Write data to a JSON file.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `file_path` | STRING | (required) | Output path |
| `encoding` | STRING | `utf-8` | File encoding |
| `indent` | INTEGER | `2` | Indentation spaces |
| `ensure_ascii` | BOOLEAN | `false` | Escape non-ASCII characters |

#### Ports

**Inputs:**
- `file_path` (STRING) - File path override
- `data` (ANY) - Data to serialize

**Outputs:**
- `file_path` (STRING) - Written file path
- `attachment_file` (LIST) - File path list
- `success` (BOOLEAN) - Write success

#### Example

```python
# Save results as JSON
write_json = WriteJSONFileNode(
    node_id="save_results",
    config={
        "file_path": "C:\\Output\\results.json",
        "indent": 4
    }
)
```

---

## Archive Nodes

### ZipFilesNode

Create a ZIP archive from files.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `zip_path` | STRING | (required) | Output ZIP path |
| `source_path` | STRING | `""` | Folder path or glob pattern |
| `base_dir` | STRING | `""` | Base directory for relative paths |
| `compression` | CHOICE | `ZIP_DEFLATED` | Compression: ZIP_STORED, ZIP_DEFLATED |

#### Operation Modes

1. **Folder mode**: Set `source_path` to a folder path
   - Recursively zips all files
   - Preserves folder structure

2. **Glob mode**: Set `source_path` to a glob pattern
   - Example: `C:\folder\*.txt` or `C:\folder\**\*.pdf`

3. **File list mode**: Connect list to `files` input port

#### Ports

**Inputs:**
- `zip_path` (STRING) - Output ZIP path
- `source_path` (STRING) - Folder or glob pattern
- `files` (LIST) - Explicit file list
- `base_dir` (STRING) - Base directory

**Outputs:**
- `zip_path` (STRING) - Created ZIP path
- `attachment_file` (LIST) - ZIP path list
- `file_count` (INTEGER) - Files added
- `success` (BOOLEAN) - Creation success

#### Example

```python
# Zip entire folder
zip_folder = ZipFilesNode(
    node_id="backup",
    config={
        "zip_path": "C:\\Backups\\documents_{{date}}.zip",
        "source_path": "C:\\Documents\\Project"
    }
)

# Zip specific file types
zip_files = ZipFilesNode(
    node_id="archive_pdfs",
    config={
        "zip_path": "C:\\Archive\\pdfs.zip",
        "source_path": "C:\\Documents\\**\\*.pdf"
    }
)
```

---

### UnzipFilesNode

Extract files from a ZIP archive.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `zip_path` | STRING | (required) | Path to ZIP file |
| `extract_to` | STRING | (required) | Extraction directory |

> **Security:** This node validates each entry to prevent Zip Slip attacks. Malicious entries attempting to write outside the target directory will be rejected.

#### Ports

**Inputs:**
- `zip_path` (STRING) - ZIP file path
- `extract_to` (STRING) - Target directory

**Outputs:**
- `extract_to` (STRING) - Extraction directory
- `files` (LIST) - Extracted file paths
- `file_count` (INTEGER) - Files extracted
- `success` (BOOLEAN) - Extraction success

#### Example

```python
# Extract downloaded archive
unzip = UnzipFilesNode(
    node_id="extract",
    config={
        "zip_path": "{{downloaded_zip}}",
        "extract_to": "C:\\Temp\\extracted"
    }
)
```

---

## File System Nodes

### CopyFileNode

Copy a file to a new location.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `source` | STRING | (required) | Source file path |
| `destination` | STRING | (required) | Destination path |
| `overwrite` | BOOLEAN | `false` | Overwrite existing file |

#### Ports

**Outputs:**
- `destination` (STRING) - Copied file path
- `success` (BOOLEAN) - Copy success

---

### MoveFileNode

Move or rename a file.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `source` | STRING | (required) | Source file path |
| `destination` | STRING | (required) | Destination path |
| `overwrite` | BOOLEAN | `false` | Overwrite existing file |

---

### DeleteFileNode

Delete a file.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `file_path` | STRING | (required) | File to delete |
| `ignore_errors` | BOOLEAN | `false` | Ignore if file doesn't exist |

---

### FileExistsNode

Check if a file exists.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `file_path` | STRING | (required) | File path to check |

#### Ports

**Outputs:**
- `exists` (BOOLEAN) - File exists
- `is_file` (BOOLEAN) - Is a file (not directory)
- `is_directory` (BOOLEAN) - Is a directory

---

## Directory Nodes

### ListDirectoryNode

List files and directories.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `dir_path` | STRING | (required) | Directory to list |
| `pattern` | STRING | `*` | Glob pattern filter |
| `recursive` | BOOLEAN | `false` | Include subdirectories |
| `include_dirs` | BOOLEAN | `true` | Include directories in results |
| `include_files` | BOOLEAN | `true` | Include files in results |

#### Ports

**Outputs:**
- `files` (LIST) - List of file paths
- `directories` (LIST) - List of directory paths
- `count` (INTEGER) - Total items
- `success` (BOOLEAN) - List success

---

### CreateDirectoryNode

Create a new directory.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `dir_path` | STRING | (required) | Directory to create |
| `parents` | BOOLEAN | `true` | Create parent directories |
| `exist_ok` | BOOLEAN | `true` | No error if exists |

---

### DeleteDirectoryNode

Delete a directory.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `dir_path` | STRING | (required) | Directory to delete |
| `recursive` | BOOLEAN | `false` | Delete contents recursively |

---

## Path Utility Nodes

### GetFileInfoNode

Get file metadata.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `file_path` | STRING | (required) | File path |

#### Ports

**Outputs:**
- `size` (INTEGER) - File size in bytes
- `created` (STRING) - Creation timestamp
- `modified` (STRING) - Modification timestamp
- `extension` (STRING) - File extension
- `exists` (BOOLEAN) - File exists

---

### JoinPathNode

Join path components.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `base` | STRING | (required) | Base path |
| `parts` | LIST | `[]` | Path parts to join |

#### Ports

**Outputs:**
- `path` (STRING) - Joined path

---

### GetFilenameNode

Extract filename from path.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `file_path` | STRING | (required) | Full file path |

#### Ports

**Outputs:**
- `filename` (STRING) - Filename with extension
- `stem` (STRING) - Filename without extension
- `extension` (STRING) - File extension
- `directory` (STRING) - Parent directory

---

## Complete Example: Data Processing Workflow

```python
# 1. Read input CSV
read_input = ReadCSVNode(
    node_id="read_input",
    config={
        "file_path": "C:\\Input\\data.csv",
        "has_header": True
    }
)

# 2. Process data (via other nodes)
# ... data transformation nodes ...

# 3. Write results to JSON
write_results = WriteJSONFileNode(
    node_id="write_results",
    config={
        "file_path": "C:\\Output\\results.json",
        "indent": 2
    }
)

# 4. Export to CSV
export_csv = WriteCSVNode(
    node_id="export_csv",
    config={
        "file_path": "C:\\Output\\results.csv"
    }
)

# 5. Create backup archive
create_backup = ZipFilesNode(
    node_id="backup",
    config={
        "zip_path": "C:\\Backups\\output_{{date}}.zip",
        "source_path": "C:\\Output"
    }
)
```

---

## Best Practices

### Path Handling

- Use `{{variable}}` placeholders for dynamic paths
- Paths support environment variables (e.g., `%USERPROFILE%`)
- Always validate paths before operations

### Error Handling

```python
# All file nodes output success and handle errors
# Connect to error handling nodes for robust workflows
```

### Large Files

- Use `max_rows` in ReadCSVNode for large datasets
- Use `max_size` in ReadFileNode to prevent memory issues
- Consider streaming for very large files

### Security

> **Warning:** Never use `allow_dangerous_paths: true` in production without explicit security review. This setting disables sandboxing protections.

## Related Documentation

- [Data Operations](data-operations.md) - Process file data
- [Control Flow](control-flow.md) - Conditional file processing
- [PDF/XML Nodes](pdf-xml.md) - Document processing
