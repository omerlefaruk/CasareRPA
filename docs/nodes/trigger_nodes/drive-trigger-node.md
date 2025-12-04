# DriveTriggerNode

Google Drive trigger node that monitors for file changes.

`:material-bell: Trigger`


**Module:** `casare_rpa.nodes.trigger_nodes.drive_trigger_node`
**File:** `src\casare_rpa\nodes\trigger_nodes\drive_trigger_node.py:99`


## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `file_id` | STRING | File ID |
| `file_name` | STRING | File Name |
| `mime_type` | STRING | MIME Type |
| `event_type` | STRING | Event Type |
| `modified_time` | STRING | Modified Time |
| `size` | INTEGER | Size (bytes) |
| `parent_id` | STRING | Parent Folder ID |
| `parent_name` | STRING | Parent Folder Name |
| `web_view_link` | STRING | Web View Link |
| `download_url` | STRING | Download URL |
| `changed_by` | STRING | Changed By |
| `raw_change` | DICT | Raw Change |

## Configuration Properties

### Advanced Tab

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `mime_types` | STRING | `` | No | Comma-separated MIME types to filter (empty = all) |
| `ignore_own_changes` | BOOLEAN | `True` | No | Don't trigger on changes made by this automation |

### Connection Tab

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `credential_name` | STRING | `google` | No | Name of stored Google OAuth credential |

### Properties Tab

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `polling_interval` | INTEGER | `60` | No | Seconds between checks for changes |
| `folder_id` | STRING | `` | No | Google Drive folder ID to monitor (empty = entire drive) |
| `include_subfolders` | BOOLEAN | `True` | No | Monitor subfolders recursively |
| `event_types` | STRING | `created,modified` | No | Comma-separated events to trigger on |
| `file_types` | STRING | `` | No | Comma-separated file extensions to filter (empty = all) |
| `name_pattern` | STRING | `` | No | Glob pattern for file names (empty = all) |

## Inheritance

Extends: `BaseTriggerNode`
