# WebhookNotifyNode

Send error notifications via webhook.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.error_handling_nodes`
**File:** `src\casare_rpa\nodes\error_handling_nodes.py:456`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `webhook_url` | INPUT | No | DataType.STRING |
| `message` | INPUT | No | DataType.STRING |
| `error_details` | INPUT | No | DataType.DICT |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `success` | OUTPUT | DataType.BOOLEAN |
| `response` | OUTPUT | DataType.STRING |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `webhook_url` | STRING | `-` | Yes | URL to send webhook notification to |
| `message` | STRING | `Error notificatio...` | No | Notification message |
| `format` | CHOICE | `generic` | No | Webhook payload format Choices: generic, slack, discord, teams |
| `timeout` | INTEGER | `30` | No | Request timeout in seconds (min: 1) |
| `retry_count` | INTEGER | `0` | No | Number of retry attempts (min: 0) |
| `retry_delay` | FLOAT | `2.0` | No | Delay between retries (min: 0.0) |

## Inheritance

Extends: `BaseNode`
