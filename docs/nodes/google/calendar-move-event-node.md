# CalendarMoveEventNode

Move an event to another calendar.

`:material-play: Executable`


**Module:** `casare_rpa.nodes.google.calendar.calendar_events`
**File:** `src\casare_rpa\nodes\google\calendar\calendar_events.py:974`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `calendar_id` | INPUT | No | DataType.STRING |
| `event_id` | INPUT | No | DataType.STRING |
| `destination_calendar_id` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `event_id` | OUTPUT | DataType.STRING |
| `new_calendar_id` | OUTPUT | DataType.STRING |
| `event` | OUTPUT | DataType.DICT |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `destination_calendar_id` | STRING | `` | Yes | Calendar ID to move the event to |
| `send_updates` | CHOICE | `all` | No | Who to notify about event move Choices: all, externalOnly, none |

## Inheritance

Extends: `CalendarBaseNode`
