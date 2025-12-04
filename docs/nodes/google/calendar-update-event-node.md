# CalendarUpdateEventNode

Update an existing calendar event.

`:material-play: Executable`


**Module:** `casare_rpa.nodes.google.calendar.calendar_events`
**File:** `src\casare_rpa\nodes\google\calendar\calendar_events.py:604`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `calendar_id` | INPUT | No | DataType.STRING |
| `event_id` | INPUT | No | DataType.STRING |
| `summary` | INPUT | No | DataType.STRING |
| `start_datetime` | INPUT | No | DataType.STRING |
| `end_datetime` | INPUT | No | DataType.STRING |
| `description` | INPUT | No | DataType.STRING |
| `location` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `event_id` | OUTPUT | DataType.STRING |
| `event` | OUTPUT | DataType.DICT |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `summary` | STRING | `` | No | New event title (leave empty to keep current) |
| `start_datetime` | STRING | `` | No | New start time (leave empty to keep current) |
| `end_datetime` | STRING | `` | No | New end time (leave empty to keep current) |
| `description` | TEXT | `` | No | New description (leave empty to keep current) |
| `location` | STRING | `` | No | New location (leave empty to keep current) |
| `send_updates` | CHOICE | `all` | No | Who to notify about event changes Choices: all, externalOnly, none |

## Inheritance

Extends: `CalendarBaseNode`
