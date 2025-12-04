# TelegramEditMessageNode

Edit a sent text message via Telegram.

`:material-play: Executable`


**Module:** `casare_rpa.nodes.messaging.telegram.telegram_actions`
**File:** `src\casare_rpa\nodes\messaging\telegram\telegram_actions.py:60`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `message_id` | INPUT | No | DataType.INTEGER |
| `text` | INPUT | No | DataType.STRING |
| `parse_mode` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `message_id` | INTEGER | `0` | Yes | ID of the message to edit |
| `text` | TEXT | `` | Yes | New message text content |

## Inheritance

Extends: `TelegramBaseNode`
