# CalendarTriggerNode

Google Calendar trigger node that listens for calendar events.

`:material-bell: Trigger`


**Module:** `casare_rpa.nodes.trigger_nodes.calendar_trigger_node`
**File:** `src\casare_rpa\nodes\trigger_nodes\calendar_trigger_node.py:90`


## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `event_id` | STRING | Event ID |
| `calendar_id` | STRING | Calendar ID |
| `summary` | STRING | Summary |
| `description` | STRING | Description |
| `start` | STRING | Start Time |
| `end` | STRING | End Time |
| `location` | STRING | Location |
| `attendees` | LIST | Attendees |
| `event_type` | STRING | Event Type |
| `minutes_until_start` | INTEGER | Minutes Until Start |
| `organizer` | STRING | Organizer |
| `html_link` | STRING | HTML Link |
| `status` | STRING | Status |
| `created` | STRING | Created |
| `updated` | STRING | Updated |

## Configuration Properties

### Advanced Tab

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `polling_interval` | INTEGER | `60` | No | Seconds between checks (min 30) |

### Connection Tab

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `credential_name` | STRING | `google` | No | Name of stored Google OAuth credential |

### Properties Tab

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `calendar_id` | STRING | `primary` | No | Calendar ID to watch (primary = main calendar) |
| `trigger_on` | CHOICE | `upcoming` | No | When to trigger: upcoming events, newly created, updated, or cancelled Choices: upcoming, created, updated, cancelled |
| `minutes_before` | INTEGER | `15` | No | For upcoming: minutes before event to trigger |
| `filter_summary` | STRING | `` | No | Comma-separated keywords in event summary (empty = all) |
| `filter_attendees` | STRING | `` | No | Only trigger if these attendees present (empty = all) |
| `include_all_day` | BOOLEAN | `True` | No | Also trigger on all-day events |

## Inheritance

Extends: `BaseTriggerNode`
