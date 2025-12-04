# CalendarDeleteCalendarNode

Delete a Google Calendar.

`:material-play: Executable`


**Module:** `casare_rpa.nodes.google.calendar.calendar_manage`
**File:** `src\casare_rpa\nodes\google\calendar\calendar_manage.py:425`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `calendar_id` | INPUT | No | DataType.STRING |
| `confirm_delete` | INPUT | No | DataType.BOOLEAN |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `deleted_id` | OUTPUT | DataType.STRING |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `confirm_delete` | BOOLEAN | `False` | Yes | Must be true to confirm calendar deletion (prevents accidental deletion) |

## Inheritance

Extends: `CalendarBaseNode`
