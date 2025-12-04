# WhatsAppSendDocumentNode

Send a document via WhatsApp.

`:material-play: Executable`


**Module:** `casare_rpa.nodes.messaging.whatsapp.whatsapp_send`
**File:** `src\casare_rpa\nodes\messaging\whatsapp\whatsapp_send.py:462`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `document` | INPUT | No | DataType.STRING |
| `filename` | INPUT | No | DataType.STRING |
| `caption` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `document_path` | OUTPUT | DataType.STRING |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `document` | STRING | `` | Yes | URL of the document to send |
| `filename` | STRING | `` | No | Display filename for the document |
| `caption` | TEXT | `` | No | Optional caption for the document |

## Inheritance

Extends: `WhatsAppBaseNode`
