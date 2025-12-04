# WhatsAppSendTemplateNode

Send a template message via WhatsApp.

`:material-play: Executable`


**Module:** `casare_rpa.nodes.messaging.whatsapp.whatsapp_send`
**File:** `src\casare_rpa\nodes\messaging\whatsapp\whatsapp_send.py:213`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `template_name` | INPUT | No | DataType.STRING |
| `language_code` | INPUT | No | DataType.STRING |
| `components` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `template_name` | OUTPUT | DataType.STRING |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `template_name` | STRING | `` | Yes | Name of the pre-approved WhatsApp template |
| `language_code` | STRING | `en_US` | No | Template language code (e.g., en_US, es_ES) |
| `components` | JSON | `{}` | No | JSON array of template component parameters |

## Inheritance

Extends: `WhatsAppBaseNode`
