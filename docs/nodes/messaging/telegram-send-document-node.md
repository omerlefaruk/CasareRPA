# TelegramSendDocumentNode

Send a document/file via Telegram.

`:material-play: Executable`


**Module:** `casare_rpa.nodes.messaging.telegram.telegram_send`
**File:** `src\casare_rpa\nodes\messaging\telegram\telegram_send.py:356`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `document` | INPUT | No | DataType.STRING |
| `filename` | INPUT | No | DataType.STRING |
| `caption` | INPUT | No | DataType.STRING |
| `parse_mode` | INPUT | No | DataType.STRING |
| `disable_notification` | INPUT | No | DataType.BOOLEAN |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `document_path` | OUTPUT | DataType.STRING |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `document` | STRING | `` | Yes | Document URL, file path, or Telegram file_id |
| `filename` | STRING | `` | No | Custom display filename |
| `caption` | TEXT | `` | No | Optional document caption |

## Inheritance

Extends: `TelegramBaseNode`
