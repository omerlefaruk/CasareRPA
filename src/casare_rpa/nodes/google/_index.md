# Google Nodes Package Index

Google services integration nodes (Drive, Sheets, Docs, Gmail, Calendar).

## Directory Structure

| Directory/File | Purpose | Key Nodes |
|----------------|---------|-----------|
| `google_base.py` | Base classes | GoogleBaseNode, DriveBaseNode, SheetsBaseNode |
| `drive/` | Google Drive | DriveListFilesNode, DriveDownloadFileNode |
| `sheets/` | Google Sheets | SheetsGetCellNode, SheetsWriteCellNode |
| `docs/` | Google Docs | DocsGetTextNode, DocsInsertTextNode |
| `gmail/` | Gmail | GmailSendEmailNode, GmailListEmailsNode |
| `calendar/` | Calendar | CalendarListEventsNode, CalendarCreateEventNode |

## Drive Nodes

### DriveListFilesNode
List files in a Google Drive folder.

**Inputs:**
- `folder_id`: Folder to list (empty = all accessible files)
- `query`: Additional query filter (Drive API query syntax)
- `mime_type`: Filter by MIME type
- `max_results`: Maximum number of files to return
- `order_by`: Sort order
- `include_trashed`: Include trashed files

**Outputs:**
- `files`: Array of file objects with id, name, mimeType, size, etc.
- `file_count`: Number of files returned
- `has_more`: Whether there are more results available
- `folder_id`: The folder ID being listed (for downstream nodes)

---

### DriveDownloadFileNode
Download files from Google Drive. Supports single file and batch downloads.

**Input Modes:**
1. **Single file by ID**: Use `file_id` + `destination_path`
2. **Single file object**: Use `file` input (from ForEach loop) + `destination_folder`
3. **Batch download**: Use `files` input (list from DriveListFilesNode) + `destination_folder`

**Inputs:**
- `file_id`: Google Drive file ID (string)
- `file`: Single file object with 'id' and 'name' fields (from loop)
- `files`: List of file objects to download (for batch operations)
- `destination_path`: Local path for single file download
- `destination_folder`: Local folder for batch downloads

**Outputs:**
- `file_path`: Path to the downloaded file (single file mode)
- `file_paths`: List of downloaded file paths (batch mode)
- `downloaded_count`: Number of files successfully downloaded

---

## Entry Points

```python
# Import Drive nodes
from casare_rpa.nodes.google import (
    DriveListFilesNode,
    DriveDownloadFileNode,
    DriveUploadFileNode,
)

# Import Sheets nodes
from casare_rpa.nodes.google import (
    SheetsGetCellNode,
    SheetsWriteCellNode,
)
```

## Common Workflow Patterns

### Download all files from a folder
```
DriveListFiles → DriveDownloadFile
   (files) ────────→ (files)
   (folder_id) ────→ (logging)
```

### Process files one by one with ForEach
```
DriveListFiles → ForLoopStart → DriveDownloadFile
   (files) ─────→ (items)
                    (item) ────→ (file)
```
