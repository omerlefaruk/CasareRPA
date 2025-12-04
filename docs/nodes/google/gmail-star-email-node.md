# GmailStarEmailNode

Star or unstar a Gmail message.

`:material-sync: Async`


**Module:** `casare_rpa.nodes.google.gmail_nodes`
**File:** `src\casare_rpa\nodes\google\gmail_nodes.py:804`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `message_id` | STRING | No | Message ID |
| `star` | BOOLEAN | No | Star (True) or Unstar (False) |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `success` | BOOLEAN | Success status |
| `error` | STRING | Error message |

## Inheritance

Extends: `BaseNode`
