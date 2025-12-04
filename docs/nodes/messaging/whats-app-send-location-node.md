# WhatsAppSendLocationNode

Send a location via WhatsApp.

`:material-play: Executable`


**Module:** `casare_rpa.nodes.messaging.whatsapp.whatsapp_send`
**File:** `src\casare_rpa\nodes\messaging\whatsapp\whatsapp_send.py:700`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `latitude` | INPUT | No | DataType.FLOAT |
| `longitude` | INPUT | No | DataType.FLOAT |
| `name` | INPUT | No | DataType.STRING |
| `address` | INPUT | No | DataType.STRING |

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
| `name` | STRING | `` | No | Display name for the location |
| `address` | STRING | `` | No | Address text for the location |

## Inheritance

Extends: `WhatsAppBaseNode`
