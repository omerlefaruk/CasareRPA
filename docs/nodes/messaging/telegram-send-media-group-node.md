# TelegramSendMediaGroupNode

Send a media group (album) via Telegram.

`:material-play: Executable`


**Module:** `casare_rpa.nodes.messaging.telegram.telegram_actions`
**File:** `src\casare_rpa\nodes\messaging\telegram\telegram_actions.py:256`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `media_json` | INPUT | No | DataType.STRING |
| `disable_notification` | INPUT | No | DataType.BOOLEAN |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `message_ids` | OUTPUT | DataType.STRING |
| `count` | OUTPUT | DataType.INTEGER |
| `success` | OUTPUT | DataType.BOOLEAN |
| `error` | OUTPUT | DataType.STRING |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `media_json` | JSON | `[]` | Yes | JSON array of InputMediaPhoto/InputMediaVideo objects (2-10 items) |

## Inheritance

Extends: `TelegramBaseNode`
