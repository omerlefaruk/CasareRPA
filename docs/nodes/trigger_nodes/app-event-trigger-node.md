# AppEventTriggerNode

App event trigger node that fires on system/application events.

`:material-bell: Trigger`


**Module:** `casare_rpa.nodes.trigger_nodes.app_event_trigger_node`
**File:** `src\casare_rpa\nodes\trigger_nodes\app_event_trigger_node.py:89`


## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `event_data` | DICT | Event Data |
| `event_type` | STRING | Event Type |
| `window_title` | STRING | Window Title |
| `process_name` | STRING | Process Name |
| `url` | STRING | URL |
| `timestamp` | STRING | Timestamp |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `event_source` | CHOICE | `windows` | No | Source of events to monitor Choices: windows, browser, rpa |
| `window_event` | CHOICE | `focus` | No | Type of window event Choices: focus, open, close, minimize, maximize |
| `window_title_pattern` | STRING | `` | No | Regex pattern for window title |
| `process_name` | STRING | `` | No | Process name to match |
| `browser_event` | CHOICE | `tab_open` | No | Type of browser event Choices: tab_open, tab_close, url_change, page_load |
| `url_pattern` | STRING | `` | No | Regex pattern for URL |
| `rpa_event` | CHOICE | `workflow_complete` | No | Type of RPA event Choices: workflow_complete, workflow_error, node_error, custom |
| `custom_event_name` | STRING | `` | No | Name of custom RPA event |

## Inheritance

Extends: `BaseTriggerNode`
