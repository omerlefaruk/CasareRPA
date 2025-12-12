# File Nodes Package Index

File system operations: read, write, copy, move, delete, and image processing.

## Directory Structure

| File | Purpose | Key Nodes |
|------|---------|-----------|
| `file_read_nodes.py` | Read file contents | ReadFileNode |
| `file_write_nodes.py` | Write/append files | WriteFileNode, AppendFileNode |
| `file_system_nodes.py` | File operations | CopyFileNode, MoveFileNode, DeleteFileNode |
| `directory_nodes.py` | Directory operations | CreateDirectoryNode, ListFilesNode |
| `path_nodes.py` | Path information | FileExistsNode, GetFileInfoNode |
| `structured_data.py` | CSV, JSON, ZIP | ReadCSVNode, WriteJSONFileNode, ZipFilesNode |
| `image_nodes.py` | Image processing | ImageConvertNode |

## Key Nodes

### ImageConvertNode
Convert images between formats (PNG, JPEG, BMP, GIF, WEBP, TIFF, ICO).

**Inputs:**
- `source_path`: Path to the image to convert (required)
- `output_path`: Destination path (auto-generated if empty)
- `output_format`: Target format - JPEG, PNG, BMP, GIF, WEBP, TIFF, ICO (default: JPEG)
- `quality`: Compression quality 1-100 for JPEG/WEBP (default: 85)
- `overwrite`: Overwrite existing file (default: false)

**Outputs:**
- `output_path`: Path to the converted image
- `success`: Boolean
- `error`: Error message if failed

**Example:**
```
Convert PNG → JPEG
  source_path: C:\images\photo.png
  output_format: JPEG
  quality: 90
```

---

### ReadFileNode
Read file contents as text or binary.

**Inputs:**
- `file_path`: Path to read
- `encoding`: Text encoding (default: utf-8)

**Outputs:**
- `content`: File contents
- `success`: Boolean

---

### WriteFileNode
Write content to a file.

**Inputs:**
- `file_path`: Destination path
- `content`: Content to write
- `encoding`: Text encoding
- `overwrite`: Overwrite if exists

**Outputs:**
- `file_path`: Written file path
- `success`: Boolean

---

### ListFilesNode
List files in a directory matching a pattern.

**Inputs:**
- `directory_path`: Directory to scan
- `pattern`: Glob pattern (default: *)
- `recursive`: Search subdirectories

**Outputs:**
- `files`: List of file paths
- `count`: Number of files found

---

## Entry Points

```python
# Import file nodes
from casare_rpa.nodes.file import (
    ReadFileNode,
    WriteFileNode,
    CopyFileNode,
    MoveFileNode,
    DeleteFileNode,
    ListFilesNode,
    ImageConvertNode,
)
```

## Security

All file nodes validate paths against security rules:
- System directories blocked by default
- Use `allow_dangerous_paths=True` to override (use with caution)
