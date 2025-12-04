# CalendarListCalendarsNode

List all calendars accessible to the user.

`:material-play: Executable`


**Module:** `casare_rpa.nodes.google.calendar.calendar_manage`
**File:** `src\casare_rpa\nodes\google\calendar\calendar_manage.py:94`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `show_hidden` | INPUT | No | DataType.BOOLEAN |
| `show_deleted` | INPUT | No | DataType.BOOLEAN |
| `min_access_role` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `calendars` | OUTPUT | DataType.ARRAY |
| `calendar_count` | OUTPUT | DataType.INTEGER |
| `primary_calendar` | OUTPUT | DataType.DICT |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `show_hidden` | BOOLEAN | `False` | No | Include hidden calendars in the list |
| `show_deleted` | BOOLEAN | `False` | No | Include deleted calendars in the list |
| `min_access_role` | CHOICE | `` | No | Filter calendars by minimum access level Choices: , freeBusyReader, reader, writer, owner |

## Inheritance

Extends: `CalendarBaseNode`
