# File Watch Trigger

The **FileWatchTriggerNode** monitors directories for file system changes and triggers workflows when files are created, modified, deleted, or moved.

## Overview

| Property | Value |
|----------|-------|
| Node Type | `FileWatchTriggerNode` |
| Trigger Type | `FILE_WATCH` |
| Icon | folder |
| Category | triggers |

## Configuration Properties

### Basic Settings

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| watch_path | directory | **required** | Directory to watch for changes |
| patterns | string | `*` | Comma-separated glob patterns to match |
| events | string | `created,modified` | Comma-separated events to watch |
| recursive | boolean | `true` | Watch subdirectories |

### Filtering

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| ignore_patterns | string | `*.tmp,~*` | Patterns to ignore |
| include_hidden | boolean | `false` | Include hidden files and directories |

### Debouncing

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| debounce_ms | integer | `500` | Minimum time between events for same file (ms) |

## Output Ports (Payload)

| Port | Type | Description |
|------|------|-------------|
| file_path | string | Full path to the changed file |
| file_name | string | Name of the file (without directory) |
| event_type | string | Type of event: `created`, `modified`, `deleted`, `moved` |
| directory | string | Parent directory path |
| old_path | string | Previous path (for `moved` events only) |
| exec_out | exec | Execution flow continues |

## Event Types

| Event | Description | Example Use Case |
|-------|-------------|------------------|
| `created` | New file created | Process incoming invoices |
| `modified` | File content changed | Sync updated documents |
| `deleted` | File removed | Log deletions for audit |
| `moved` | File renamed or moved | Track file organization |

Configure which events to watch:

```json
{
  "events": "created,modified,deleted,moved"
}
```

## Watch Patterns (Glob)

Use glob patterns to filter which files trigger the workflow:

### Pattern Syntax

| Pattern | Matches | Example |
|---------|---------|---------|
| `*` | Any characters (not `/`) | `*.pdf` matches `invoice.pdf` |
| `**` | Any path segments | `**/*.pdf` matches all PDFs recursively |
| `?` | Single character | `file?.txt` matches `file1.txt` |
| `[abc]` | Character set | `file[123].txt` matches `file1.txt`, `file2.txt` |
| `[a-z]` | Character range | `[a-z]*.txt` matches `abc.txt` |

### Common Patterns

```json
// All PDF files
{"patterns": "*.pdf"}

// Excel files (multiple extensions)
{"patterns": "*.xlsx,*.xls,*.csv"}

// All files in specific subfolder
{"patterns": "invoices/*"}

// Images
{"patterns": "*.jpg,*.jpeg,*.png,*.gif"}

// Documents
{"patterns": "*.pdf,*.docx,*.doc,*.xlsx"}
```

## Ignore Patterns

Exclude files from triggering:

```json
{
  "ignore_patterns": "*.tmp,~*,*.swp,*.bak,Thumbs.db,.DS_Store"
}
```

Common patterns to ignore:
- `*.tmp` - Temporary files
- `~*` - Editor backup files
- `*.swp` - Vim swap files
- `.DS_Store` - macOS metadata
- `Thumbs.db` - Windows thumbnails
- `*.partial` - Incomplete downloads

## Recursive Watching

Control whether subdirectories are monitored:

```json
// Watch all subdirectories
{"recursive": true}

// Watch only the specified directory
{"recursive": false}
```

## Debouncing

When files are saved, many applications trigger multiple write events. Debouncing prevents duplicate triggers:

```json
{
  "debounce_ms": 1000
}
```

| debounce_ms | Behavior |
|-------------|----------|
| `0` | No debouncing (every event triggers) |
| `500` | Wait 500ms after last event |
| `1000` | Wait 1 second (recommended for large files) |
| `5000` | Wait 5 seconds (for very large files) |

> **Note:** Set higher debounce values for large files that take time to write.

## Examples

### Invoice Processing

Watch for new PDF invoices:

```json
{
  "watch_path": "C:\\Documents\\Invoices\\Inbox",
  "patterns": "*.pdf",
  "events": "created",
  "recursive": false,
  "debounce_ms": 1000
}
```

### Document Sync

Sync all document changes:

```json
{
  "watch_path": "C:\\Users\\Admin\\Documents",
  "patterns": "*.docx,*.xlsx,*.pdf",
  "events": "created,modified,deleted",
  "recursive": true,
  "ignore_patterns": "~*,*.tmp"
}
```

### Image Upload Processing

Process new images:

```json
{
  "watch_path": "C:\\Uploads\\Images",
  "patterns": "*.jpg,*.jpeg,*.png,*.gif,*.webp",
  "events": "created",
  "recursive": true,
  "include_hidden": false,
  "debounce_ms": 500
}
```

### Log File Monitoring

Monitor log file changes:

```json
{
  "watch_path": "C:\\Logs",
  "patterns": "*.log",
  "events": "modified",
  "recursive": true,
  "debounce_ms": 2000
}
```

### Folder Organization Tracking

Track file movements:

```json
{
  "watch_path": "C:\\SharedDrive",
  "patterns": "*",
  "events": "moved,deleted",
  "recursive": true,
  "ignore_patterns": "*.tmp,Thumbs.db,.DS_Store"
}
```

## Complete Workflow Example

```python
from casare_rpa.nodes.trigger_nodes import FileWatchTriggerNode
from casare_rpa.nodes.file import ReadFileNode, MoveFileNode
from casare_rpa.nodes import SendEmailNode

# Watch for new invoices
trigger = FileWatchTriggerNode(
    node_id="invoice_watcher",
    config={
        "watch_path": "C:\\Invoices\\Incoming",
        "patterns": "*.pdf",
        "events": "created",
        "recursive": False,
        "debounce_ms": 1000,
        "ignore_patterns": "*.tmp",
    }
)

# Workflow:
# [File Watch] -> [Read PDF] -> [Extract Data] -> [Send Email] -> [Move File]
#      |
#      +-- file_path   -> Full path to new file
#      +-- file_name   -> Just the filename
#      +-- event_type  -> "created"
```

## Workflow JSON Example

```json
{
  "nodes": [
    {
      "id": "file_watch_1",
      "type": "FileWatchTriggerNode",
      "config": {
        "watch_path": "C:\\Documents\\Inbox",
        "patterns": "*.pdf,*.docx",
        "events": "created,modified",
        "recursive": true,
        "debounce_ms": 500
      },
      "position": {"x": 100, "y": 200}
    },
    {
      "id": "log_1",
      "type": "LogNode",
      "config": {
        "message": "File {{event_type}}: {{file_name}} at {{file_path}}"
      },
      "position": {"x": 400, "y": 200}
    },
    {
      "id": "condition_1",
      "type": "IfNode",
      "config": {
        "condition": "event_type == 'created'"
      },
      "position": {"x": 700, "y": 200}
    }
  ],
  "connections": [
    {
      "source_node": "file_watch_1",
      "source_port": "exec_out",
      "target_node": "log_1",
      "target_port": "exec_in"
    }
  ]
}
```

## Using Payload Data

Access file information in subsequent nodes:

```python
# In a subsequent node's execute method
async def execute(self, context) -> ExecutionResult:
    file_path = context.inputs["file_path"]    # "C:\Invoices\invoice_001.pdf"
    file_name = context.inputs["file_name"]    # "invoice_001.pdf"
    event_type = context.inputs["event_type"]  # "created"
    directory = context.inputs["directory"]    # "C:\Invoices"

    # For moved events
    if event_type == "moved":
        old_path = context.inputs["old_path"]  # Previous location
```

## Common Use Cases

### Invoice Automation
1. Watch `Inbox` folder for new PDFs
2. Extract invoice data with OCR
3. Create record in accounting system
4. Move processed file to `Processed` folder

### Document Backup
1. Watch Documents folder for changes
2. Copy modified files to backup location
3. Log backup timestamp

### Data Pipeline
1. Watch for new CSV files
2. Parse and validate data
3. Import to database
4. Archive source file

### Media Processing
1. Watch Uploads folder for images
2. Resize and compress
3. Generate thumbnails
4. Upload to CDN

## Platform Considerations

### Windows
- Use backslash or forward slash in paths
- UNC paths supported: `\\\\server\\share\\folder`
- Case-insensitive file matching

### macOS/Linux
- Use forward slashes in paths
- Case-sensitive by default
- Symlinks followed by default

## Troubleshooting

### Events Not Firing

1. **Check permissions**: Ensure CasareRPA has read access to the watch directory
2. **Verify patterns**: Test glob patterns match your files
3. **Check debouncing**: Lower `debounce_ms` for quick tests
4. **Confirm events**: Ensure the event type is in your `events` list

### Too Many Events

1. **Add ignore patterns**: Filter out temp files and editor backups
2. **Increase debouncing**: Set higher `debounce_ms` value
3. **Limit events**: Watch only specific event types
4. **Disable recursive**: Set `recursive: false` if not needed

### Missed Events

1. **Check for rapid changes**: Debouncing may combine multiple events
2. **Verify buffer size**: Very high-activity directories may exceed OS limits
3. **Monitor for errors**: Check CasareRPA logs for watch errors

## Best Practices

1. **Use Specific Patterns**: Avoid watching `*` in busy directories
2. **Set Appropriate Debounce**: Higher values for large files, lower for quick processing
3. **Ignore Temp Files**: Always exclude common temp file patterns
4. **Test Thoroughly**: Verify trigger fires correctly before deployment
5. **Handle Errors**: Design workflow to handle file access errors
6. **Process and Move**: Move processed files to prevent re-triggering
7. **Log Events**: Track `file_path` and `event_type` for debugging

## Related

- [Schedule Trigger](schedule.md) - Time-based triggering
- [Webhook Trigger](webhook.md) - HTTP-based triggering
- [Trigger Overview](index.md) - All available triggers
