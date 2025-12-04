# CalendarGetEventNode

Get a single calendar event by ID.

`:material-play: Executable`


**Module:** `casare_rpa.nodes.google.calendar.calendar_events`
**File:** `src\casare_rpa\nodes\google\calendar\calendar_events.py:249`


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
| `event` | OUTPUT | DataType.DICT |
| `summary` | OUTPUT | DataType.STRING |
| `start` | OUTPUT | DataType.DICT |
| `end` | OUTPUT | DataType.DICT |

## Inheritance

Extends: `CalendarBaseNode`
