# TelegramSendLocationNode

Send a location via Telegram.

`:material-play: Executable`


**Module:** `casare_rpa.nodes.messaging.telegram.telegram_send`
**File:** `src\casare_rpa\nodes\messaging\telegram\telegram_send.py:487`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `latitude` | INPUT | No | DataType.FLOAT |
| `longitude` | INPUT | No | DataType.FLOAT |
| `disable_notification` | INPUT | No | DataType.BOOLEAN |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `latitude` | OUTPUT | DataType.FLOAT |
| `longitude` | OUTPUT | DataType.FLOAT |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `latitude` | FLOAT | `0.0` | Yes | Location latitude (-90 to 90) (min: -90.0, max: 90.0) |
| `longitude` | FLOAT | `0.0` | Yes | Location longitude (-180 to 180) (min: -180.0, max: 180.0) |

## Inheritance

Extends: `TelegramBaseNode`
