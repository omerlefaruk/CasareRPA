# CalendarCreateCalendarNode

Create a new Google Calendar.

`:material-play: Executable`


**Module:** `casare_rpa.nodes.google.calendar.calendar_manage`
**File:** `src\casare_rpa\nodes\google\calendar\calendar_manage.py:318`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `summary` | INPUT | No | DataType.STRING |
| `description` | INPUT | No | DataType.STRING |
| `location` | INPUT | No | DataType.STRING |
| `timezone` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `calendar_id` | OUTPUT | DataType.STRING |
| `calendar` | OUTPUT | DataType.DICT |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `summary` | STRING | `` | Yes | The name of the new calendar |
| `description` | TEXT | `` | No | Description of the calendar |
| `location` | STRING | `` | No | Geographic location associated with the calendar |
| `timezone` | STRING | `` | No | Timezone for the calendar (e.g., America/New_York) |

## Inheritance

Extends: `CalendarBaseNode`
