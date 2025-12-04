# WhatsAppSendVideoNode

Send a video via WhatsApp.

`:material-play: Executable`


**Module:** `casare_rpa.nodes.messaging.whatsapp.whatsapp_send`
**File:** `src\casare_rpa\nodes\messaging\whatsapp\whatsapp_send.py:574`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `video` | INPUT | No | DataType.STRING |
| `caption` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `video_path` | OUTPUT | DataType.STRING |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `video` | STRING | `` | Yes | URL of the video to send (MP4, 3GP supported) |
| `caption` | TEXT | `` | No | Optional caption for the video |

## Inheritance

Extends: `WhatsAppBaseNode`
