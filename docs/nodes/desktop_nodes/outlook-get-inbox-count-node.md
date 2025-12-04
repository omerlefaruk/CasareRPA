# OutlookGetInboxCountNode

Node to get the count of emails in Outlook inbox.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.desktop_nodes.office_nodes`
**File:** `src\casare_rpa\nodes\desktop_nodes\office_nodes.py:938`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `total_count` | INTEGER | Total emails |
| `unread_count` | INTEGER | Unread emails |
| `success` | BOOLEAN | Operation succeeded |

## Inheritance

Extends: `BaseNode`
