# TelegramAnswerCallbackNode

Answer a callback query from an inline keyboard.

`:material-play: Executable`


**Module:** `casare_rpa.nodes.messaging.telegram.telegram_actions`
**File:** `src\casare_rpa\nodes\messaging\telegram\telegram_actions.py:405`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `bot_token` | INPUT | No | DataType.STRING |
| `credential_name` | INPUT | No | DataType.STRING |
| `callback_query_id` | INPUT | No | DataType.STRING |
| `text` | INPUT | No | DataType.STRING |
| `show_alert` | INPUT | No | DataType.BOOLEAN |
| `url` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `success` | OUTPUT | DataType.BOOLEAN |
| `error` | OUTPUT | DataType.STRING |

## Configuration Properties

### Advanced Tab

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `url` | STRING | `` | No | URL to open (for game bots) |

### Properties Tab

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `callback_query_id` | STRING | `` | Yes | ID of the callback query to answer |
| `text` | STRING | `` | No | Optional notification text to show user |
| `show_alert` | BOOLEAN | `False` | No | Show as alert popup instead of toast notification |

## Inheritance

Extends: `TelegramBaseNode`
