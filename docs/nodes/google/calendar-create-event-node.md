# CalendarCreateEventNode

Create a new calendar event.

`:material-play: Executable`


**Module:** `casare_rpa.nodes.google.calendar.calendar_events`
**File:** `src\casare_rpa\nodes\google\calendar\calendar_events.py:404`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `calendar_id` | INPUT | No | DataType.STRING |
| `summary` | INPUT | No | DataType.STRING |
| `start_datetime` | INPUT | No | DataType.STRING |
| `end_datetime` | INPUT | No | DataType.STRING |
| `timezone` | INPUT | No | DataType.STRING |
| `description` | INPUT | No | DataType.STRING |
| `location` | INPUT | No | DataType.STRING |
| `attendees` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `event_id` | OUTPUT | DataType.STRING |
| `html_link` | OUTPUT | DataType.STRING |
| `event` | OUTPUT | DataType.DICT |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `summary` | STRING | `` | Yes | The title/summary of the event |
| `start_datetime` | STRING | `` | Yes | Start date/time in ISO 8601 format |
| `end_datetime` | STRING | `` | Yes | End date/time in ISO 8601 format |
| `timezone` | STRING | `` | No | Timezone for the event (e.g., America/New_York) |
| `description` | TEXT | `` | No | Detailed description of the event |
| `location` | STRING | `` | No | Event location or meeting room |
| `attendees` | STRING | `` | No | Comma-separated email addresses of attendees |
| `send_updates` | CHOICE | `all` | No | Who to notify about event changes Choices: all, externalOnly, none |

## Inheritance

Extends: `CalendarBaseNode`
