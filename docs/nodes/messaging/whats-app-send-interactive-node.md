# WhatsAppSendInteractiveNode

Send an interactive message (buttons, lists) via WhatsApp.

`:material-play: Executable`


**Module:** `casare_rpa.nodes.messaging.whatsapp.whatsapp_send`
**File:** `src\casare_rpa\nodes\messaging\whatsapp\whatsapp_send.py:870`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `interactive_type` | INPUT | No | DataType.STRING |
| `body_text` | INPUT | No | DataType.STRING |
| `action_json` | INPUT | No | DataType.STRING |
| `header_json` | INPUT | No | DataType.STRING |
| `footer_text` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `interactive_type` | OUTPUT | DataType.STRING |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `interactive_type` | CHOICE | `button` | Yes | Type of interactive message (button or list) Choices: button, list |
| `body_text` | TEXT | `` | Yes | Main message body text |
| `action_json` | JSON | `{}` | Yes | JSON object defining buttons or list sections |
| `header_json` | JSON | `{}` | No | Optional JSON header object |
| `footer_text` | STRING | `` | No | Optional footer text |

## Inheritance

Extends: `WhatsAppBaseNode`
