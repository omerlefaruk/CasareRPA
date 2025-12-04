# TelegramSendPhotoNode

Send a photo via Telegram.

`:material-play: Executable`


**Module:** `casare_rpa.nodes.messaging.telegram.telegram_send`
**File:** `src\casare_rpa\nodes\messaging\telegram\telegram_send.py:227`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `photo` | INPUT | No | DataType.STRING |
| `caption` | INPUT | No | DataType.STRING |
| `parse_mode` | INPUT | No | DataType.STRING |
| `disable_notification` | INPUT | No | DataType.BOOLEAN |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `photo_path` | OUTPUT | DataType.STRING |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `photo` | STRING | `` | Yes | Photo URL, file path, or Telegram file_id |
| `caption` | TEXT | `` | No | Optional photo caption (0-1024 characters) |

## Inheritance

Extends: `TelegramBaseNode`
