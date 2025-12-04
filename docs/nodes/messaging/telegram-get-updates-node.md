# TelegramGetUpdatesNode

Get updates via Telegram's getUpdates API.

`:material-play: Executable`


**Module:** `casare_rpa.nodes.messaging.telegram.telegram_actions`
**File:** `src\casare_rpa\nodes\messaging\telegram\telegram_actions.py:534`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `bot_token` | INPUT | No | DataType.STRING |
| `credential_name` | INPUT | No | DataType.STRING |
| `offset` | INPUT | No | DataType.INTEGER |
| `limit` | INPUT | No | DataType.INTEGER |
| `timeout` | INPUT | No | DataType.INTEGER |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `updates_json` | OUTPUT | DataType.STRING |
| `count` | OUTPUT | DataType.INTEGER |
| `last_update_id` | OUTPUT | DataType.INTEGER |
| `success` | OUTPUT | DataType.BOOLEAN |
| `error` | OUTPUT | DataType.STRING |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `offset` | INTEGER | `0` | No | Starting update ID (0 for first available) |
| `limit` | INTEGER | `100` | No | Max updates to retrieve (1-100) (min: 1, max: 100) |
| `timeout` | INTEGER | `30` | No | Long polling timeout in seconds (min: 0, max: 120) |

## Inheritance

Extends: `TelegramBaseNode`
