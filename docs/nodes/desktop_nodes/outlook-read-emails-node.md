# OutlookReadEmailsNode

Node to read emails from Outlook inbox.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.desktop_nodes.office_nodes`
**File:** `src\casare_rpa\nodes\desktop_nodes\office_nodes.py:840`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `emails` | ANY | List of emails |
| `count` | INTEGER | Number of emails |
| `success` | BOOLEAN | Operation succeeded |

## Inheritance

Extends: `BaseNode`
