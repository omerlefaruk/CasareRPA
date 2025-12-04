# WhatsAppSendImageNode

Send an image via WhatsApp.

`:material-play: Executable`


**Module:** `casare_rpa.nodes.messaging.whatsapp.whatsapp_send`
**File:** `src\casare_rpa\nodes\messaging\whatsapp\whatsapp_send.py:349`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `image` | INPUT | No | DataType.STRING |
| `caption` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `image_path` | OUTPUT | DataType.STRING |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `image` | STRING | `` | Yes | URL of the image to send (JPEG, PNG supported) |
| `caption` | TEXT | `` | No | Optional caption for the image |

## Inheritance

Extends: `WhatsAppBaseNode`
