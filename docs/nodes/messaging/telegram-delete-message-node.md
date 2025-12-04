# TelegramDeleteMessageNode

Delete a message via Telegram.

`:material-play: Executable`


**Module:** `casare_rpa.nodes.messaging.telegram.telegram_actions`
**File:** `src\casare_rpa\nodes\messaging\telegram\telegram_actions.py:169`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `message_id` | INPUT | No | DataType.INTEGER |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `success` | OUTPUT | DataType.BOOLEAN |
| `error` | OUTPUT | DataType.STRING |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `message_id` | INTEGER | `0` | Yes | ID of the message to delete |

## Inheritance

Extends: `TelegramBaseNode`
