# CalendarGetCalendarNode

Get calendar information by ID.

`:material-play: Executable`


**Module:** `casare_rpa.nodes.google.calendar.calendar_manage`
**File:** `src\casare_rpa\nodes\google\calendar\calendar_manage.py:196`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `calendar_id` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `calendar` | OUTPUT | DataType.DICT |
| `summary` | OUTPUT | DataType.STRING |
| `timezone` | OUTPUT | DataType.STRING |
| `access_role` | OUTPUT | DataType.STRING |

## Inheritance

Extends: `CalendarBaseNode`
