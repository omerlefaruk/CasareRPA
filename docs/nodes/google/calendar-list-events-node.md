# CalendarListEventsNode

List events from a Google Calendar.

`:material-play: Executable`


**Module:** `casare_rpa.nodes.google.calendar.calendar_events`
**File:** `src\casare_rpa\nodes\google\calendar\calendar_events.py:139`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `calendar_id` | INPUT | No | DataType.STRING |
| `time_min` | INPUT | No | DataType.STRING |
| `time_max` | INPUT | No | DataType.STRING |
| `query` | INPUT | No | DataType.STRING |
| `max_results` | INPUT | No | DataType.INTEGER |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `events` | OUTPUT | DataType.ARRAY |
| `event_count` | OUTPUT | DataType.INTEGER |
| `next_page_token` | OUTPUT | DataType.STRING |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `time_min` | STRING | `` | No | Filter events starting after this time (ISO 8601 format) |
| `time_max` | STRING | `` | No | Filter events ending before this time (ISO 8601 format) |
| `query` | STRING | `` | No | Free-text search within event fields |
| `max_results` | INTEGER | `100` | No | Maximum number of events to return (1-2500) |

## Inheritance

Extends: `CalendarBaseNode`
