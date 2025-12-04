# GetEmailContentNode

Extract content from an email object.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.email.receive_nodes`
**File:** `src\casare_rpa\nodes\email\receive_nodes.py:300`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `email` | INPUT | No | DataType.DICT |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `subject` | OUTPUT | DataType.STRING |
| `from` | OUTPUT | DataType.STRING |
| `to` | OUTPUT | DataType.STRING |
| `date` | OUTPUT | DataType.STRING |
| `body_text` | OUTPUT | DataType.STRING |
| `body_html` | OUTPUT | DataType.STRING |
| `attachments` | OUTPUT | DataType.LIST |

## Inheritance

Extends: `BaseNode`
