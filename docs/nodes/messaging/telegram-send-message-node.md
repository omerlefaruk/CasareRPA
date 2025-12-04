# TelegramSendMessageNode

Send a text message via Telegram.

`:material-play: Executable`


**Module:** `casare_rpa.nodes.messaging.telegram.telegram_send`
**File:** `src\casare_rpa\nodes\messaging\telegram\telegram_send.py:102`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `text` | INPUT | No | DataType.STRING |
| `parse_mode` | INPUT | No | DataType.STRING |
| `disable_notification` | INPUT | No | DataType.BOOLEAN |
| `reply_to_message_id` | INPUT | No | DataType.INTEGER |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `text` | OUTPUT | DataType.STRING |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `text` | TEXT | `` | Yes | Message content (1-4096 characters) |
| `reply_to_message_id` | INTEGER | `0` | No | Message ID to reply to (0 for no reply) |

## Inheritance

Extends: `TelegramBaseNode`
