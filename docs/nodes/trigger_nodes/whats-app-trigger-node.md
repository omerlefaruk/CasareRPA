# WhatsAppTriggerNode

WhatsApp trigger node that listens for incoming messages.

`:material-bell: Trigger`


**Module:** `casare_rpa.nodes.trigger_nodes.whatsapp_trigger_node`
**File:** `src\casare_rpa\nodes\trigger_nodes\whatsapp_trigger_node.py:93`


## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `message_id` | STRING | Message ID |
| `from_number` | STRING | From Number |
| `to_number` | STRING | To Number |
| `timestamp` | STRING | Timestamp |
| `text` | STRING | Message Text |
| `message_type` | STRING | Message Type |
| `media_id` | STRING | Media ID |
| `media_url` | STRING | Media URL |
| `caption` | STRING | Caption |
| `contact_name` | STRING | Contact Name |
| `raw_message` | DICT | Raw Message |

## Configuration Properties

### Advanced Tab

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `include_status_updates` | BOOLEAN | `False` | No | Also trigger on message status updates (sent, delivered, read) |

### Connection Tab

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `access_token` | STRING | `` | No | WhatsApp Business API access token |
| `phone_number_id` | STRING | `` | No | WhatsApp Business phone number ID |
| `credential_name` | STRING | `` | No | Name of stored credential (alternative to access token) |

### Properties Tab

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `verify_token` | STRING | `` | No | Token for webhook verification (must match Meta app settings) |
| `webhook_path` | STRING | `/whatsapp/webhook` | No | Path for webhook endpoint |
| `filter_phone_numbers` | STRING | `` | No | Comma-separated phone numbers to allow (empty = all) |
| `message_types` | STRING | `text,image,docume...` | No | Comma-separated message types to trigger on |

## Inheritance

Extends: `BaseTriggerNode`
