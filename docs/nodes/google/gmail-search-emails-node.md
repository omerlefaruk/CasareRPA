# GmailSearchEmailsNode

Search for emails using Gmail query syntax.

`:material-play: Executable`


**Module:** `casare_rpa.nodes.google.gmail.gmail_read`
**File:** `src\casare_rpa\nodes\google\gmail\gmail_read.py:243`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `query` | INPUT | No | DataType.STRING |
| `max_results` | INPUT | No | DataType.INTEGER |
| `label_ids` | INPUT | No | DataType.STRING |
| `include_spam_trash` | INPUT | No | DataType.BOOLEAN |
| `page_token` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `messages` | OUTPUT | DataType.ARRAY |
| `message_count` | OUTPUT | DataType.INTEGER |
| `message_ids` | OUTPUT | DataType.ARRAY |
| `next_page_token` | OUTPUT | DataType.STRING |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `query` | STRING | `` | No | Gmail search query (same syntax as Gmail search box) |
| `max_results` | INTEGER | `10` | No | Maximum number of messages to return (1-500) (min: 1, max: 500) |
| `label_ids` | STRING | `` | No | Filter by label IDs (comma-separated) |
| `include_spam_trash` | BOOLEAN | `False` | No | Include messages from spam and trash folders |

## Inheritance

Extends: `GmailBaseNode`
