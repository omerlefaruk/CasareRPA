# FilterEmailsNode

Filter a list of emails based on criteria.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.email.receive_nodes`
**File:** `src\casare_rpa\nodes\email\receive_nodes.py:360`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `emails` | INPUT | No | DataType.LIST |
| `subject_contains` | INPUT | No | DataType.STRING |
| `from_contains` | INPUT | No | DataType.STRING |
| `has_attachments` | INPUT | No | DataType.BOOLEAN |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `filtered` | OUTPUT | DataType.LIST |
| `count` | OUTPUT | DataType.INTEGER |

## Inheritance

Extends: `BaseNode`
