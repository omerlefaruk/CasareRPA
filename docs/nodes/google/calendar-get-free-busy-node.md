# CalendarGetFreeBusyNode

Query free/busy information for calendars.

`:material-play: Executable`


**Module:** `casare_rpa.nodes.google.calendar.calendar_events`
**File:** `src\casare_rpa\nodes\google\calendar\calendar_events.py:1107`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `calendar_ids` | INPUT | No | DataType.STRING |
| `time_min` | INPUT | No | DataType.STRING |
| `time_max` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `free_busy` | OUTPUT | DataType.DICT |
| `is_busy` | OUTPUT | DataType.BOOLEAN |
| `busy_count` | OUTPUT | DataType.INTEGER |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `calendar_ids` | STRING | `primary` | Yes | Comma-separated calendar IDs to check availability |
| `time_min` | STRING | `` | Yes | Start of time range to check (ISO 8601) |
| `time_max` | STRING | `` | Yes | End of time range to check (ISO 8601) |

## Inheritance

Extends: `CalendarBaseNode`
