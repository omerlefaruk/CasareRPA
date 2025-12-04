# GmailBatchSendNode

Send multiple emails in batch.

`:material-sync: Async`


**Module:** `casare_rpa.nodes.google.gmail_nodes`
**File:** `src\casare_rpa\nodes\google\gmail_nodes.py:939`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `emails` | ARRAY | No | Array of email objects |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `results` | ARRAY | Send results |
| `sent_count` | INTEGER | Number sent |
| `failed_count` | INTEGER | Number failed |
| `success` | BOOLEAN | Overall success |
| `error` | STRING | Error message |

## Inheritance

Extends: `BaseNode`
