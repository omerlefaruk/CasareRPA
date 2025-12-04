# FileWatchTriggerNode

File watch trigger node that fires when files change.

`:material-bell: Trigger`


**Module:** `casare_rpa.nodes.trigger_nodes.file_watch_trigger_node`
**File:** `src\casare_rpa\nodes\trigger_nodes\file_watch_trigger_node.py:75`


## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `file_path` | STRING | File Path |
| `file_name` | STRING | File Name |
| `event_type` | STRING | Event Type |
| `directory` | STRING | Directory |
| `old_path` | STRING | Old Path (moved) |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `watch_path` | DIRECTORY_PATH | `-` | Yes | Directory to watch for changes |
| `patterns` | STRING | `*` | No | Comma-separated glob patterns to match |
| `events` | STRING | `created,modified` | No | Comma-separated events to watch |
| `recursive` | BOOLEAN | `True` | No | Watch subdirectories |
| `ignore_patterns` | STRING | `*.tmp,~*` | No | Patterns to ignore |
| `debounce_ms` | INTEGER | `500` | No | Minimum time between events for same file |
| `include_hidden` | BOOLEAN | `False` | No | Include hidden files and directories |

## Inheritance

Extends: `BaseTriggerNode`
