# GmailListEmailsNode

List emails from Gmail inbox.

`:material-sync: Async`


**Module:** `casare_rpa.nodes.google.gmail_nodes`
**File:** `src\casare_rpa\nodes\google\gmail_nodes.py:453`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `max_results` | INTEGER | No | Maximum results |
| `label_ids` | ARRAY | No | Label IDs to filter |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `messages` | ARRAY | List of message objects |
| `count` | INTEGER | Number of messages |
| `next_page_token` | STRING | Next page token |
| `success` | BOOLEAN | Success status |
| `error` | STRING | Error message |

## Inheritance

Extends: `BaseNode`
