# OutlookSendEmailNode

Node to send an email via Outlook.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.desktop_nodes.office_nodes`
**File:** `src\casare_rpa\nodes\desktop_nodes\office_nodes.py:728`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `to` | STRING | No | Recipient(s) |
| `subject` | STRING | No | Subject |
| `body` | STRING | No | Body |
| `cc` | STRING | No | CC recipients |
| `bcc` | STRING | No | BCC recipients |
| `attachments` | ANY | No | Attachment paths |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `success` | BOOLEAN | Email sent |

## Inheritance

Extends: `BaseNode`
