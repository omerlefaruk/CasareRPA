# CalendarQuickAddNode

Create an event using natural language.

`:material-play: Executable`


**Module:** `casare_rpa.nodes.google.calendar.calendar_events`
**File:** `src\casare_rpa\nodes\google\calendar\calendar_events.py:851`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `calendar_id` | INPUT | No | DataType.STRING |
| `text` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `event_id` | OUTPUT | DataType.STRING |
| `summary` | OUTPUT | DataType.STRING |
| `start` | OUTPUT | DataType.DICT |
| `end` | OUTPUT | DataType.DICT |
| `event` | OUTPUT | DataType.DICT |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `text` | STRING | `` | Yes | Natural language description of the event |
| `send_updates` | CHOICE | `all` | No | Who to notify about event creation Choices: all, externalOnly, none |

## Inheritance

Extends: `CalendarBaseNode`
