# CalendarDeleteEventNode

Delete a calendar event.

`:material-play: Executable`


**Module:** `casare_rpa.nodes.google.calendar.calendar_events`
**File:** `src\casare_rpa\nodes\google\calendar\calendar_events.py:749`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `calendar_id` | INPUT | No | DataType.STRING |
| `event_id` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `deleted_id` | OUTPUT | DataType.STRING |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `send_updates` | CHOICE | `all` | No | Who to notify about event deletion Choices: all, externalOnly, none |

## Inheritance

Extends: `CalendarBaseNode`
