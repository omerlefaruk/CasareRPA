# Messaging Triggers

CasareRPA provides triggers for popular messaging platforms:

- **TelegramTriggerNode** - Telegram bot message handling
- **WhatsAppTriggerNode** - WhatsApp Business Cloud API integration

---

## TelegramTriggerNode {#telegram-trigger}

The Telegram trigger listens for messages sent to your Telegram bot.

### Overview

| Property | Value |
|----------|-------|
| Node Type | `TelegramTriggerNode` |
| Trigger Type | `TELEGRAM` |
| Icon | telegram |
| Category | triggers |

### Configuration Properties

#### Connection Settings

| Property | Type | Default | Tab | Description |
|----------|------|---------|-----|-------------|
| bot_token | string | `""` | connection | Bot token from @BotFather |
| credential_name | string | `""` | connection | Alternative: stored credential name |

#### Mode Settings

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| mode | choice | `auto` | Update mode: `auto`, `webhook`, `polling` |
| webhook_url | string | `""` | Public URL for webhook mode |
| polling_interval | integer | `2` | Seconds between polls (polling mode) |

#### Filters

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| filter_chat_ids | string | `""` | Comma-separated chat IDs to allow |
| filter_user_ids | string | `""` | Comma-separated user IDs to allow |
| commands_only | boolean | `false` | Only trigger on bot commands |
| filter_commands | string | `""` | Specific commands to trigger on |

#### Advanced

| Property | Type | Default | Tab | Description |
|----------|------|---------|-----|-------------|
| allowed_updates | string | `message` | advanced | Comma-separated update types |

### Output Ports

| Port | Type | Description |
|------|------|-------------|
| message_id | integer | Telegram message ID |
| chat_id | integer | Chat ID |
| user_id | integer | Sender's user ID |
| username | string | Sender's username |
| first_name | string | Sender's first name |
| text | string | Message text content |
| is_command | boolean | Whether message is a bot command |
| command | string | Command name (without `/`) |
| command_args | string | Command arguments |
| message_type | string | Type: `text`, `photo`, `document`, etc. |
| raw_update | dict | Full Telegram update object |
| exec_out | exec | Execution flow continues |

### Bot Setup Requirements

1. **Create a Bot**
   - Message [@BotFather](https://t.me/botfather) on Telegram
   - Send `/newbot` and follow prompts
   - Save the bot token (format: `123456789:ABC-DEF...`)

2. **Configure Bot Settings** (optional)
   - `/setcommands` - Define available commands
   - `/setdescription` - Bot description
   - `/setabouttext` - About text

3. **Add Bot to Chat**
   - For private chats: Start conversation with bot
   - For groups: Add bot as member

### Update Modes

#### Auto Mode (Recommended)

Automatically chooses the best method:
- Uses webhook if `CASARE_WEBHOOK_URL` is set
- Falls back to polling otherwise

```json
{
  "mode": "auto",
  "bot_token": "123456789:ABC-DEF..."
}
```

#### Webhook Mode

For production with public URL:

```json
{
  "mode": "webhook",
  "bot_token": "123456789:ABC-DEF...",
  "webhook_url": "https://your-domain.com/telegram/webhook"
}
```

> **Note:** Webhook requires HTTPS and valid SSL certificate.

#### Polling Mode

For development or when no public URL available:

```json
{
  "mode": "polling",
  "bot_token": "123456789:ABC-DEF...",
  "polling_interval": 2
}
```

### Filter Examples

#### Allow Specific Users

```json
{
  "filter_user_ids": "123456789,987654321"
}
```

#### Allow Specific Groups

```json
{
  "filter_chat_ids": "-1001234567890,-1009876543210"
}
```

> **Note:** Group chat IDs are negative numbers.

#### Commands Only

```json
{
  "commands_only": true,
  "filter_commands": "start,help,run"
}
```

This triggers only on `/start`, `/help`, or `/run` commands.

### Command Handling Example

```json
{
  "bot_token": "123456789:ABC-DEF...",
  "commands_only": true,
  "filter_commands": "process,status,help"
}
```

In workflow:
```python
command = inputs["command"]       # "process"
args = inputs["command_args"]     # "invoice123"
chat_id = inputs["chat_id"]       # For sending reply
```

---

## WhatsAppTriggerNode {#whatsapp-trigger}

The WhatsApp trigger uses the WhatsApp Business Cloud API to receive messages.

### Overview

| Property | Value |
|----------|-------|
| Node Type | `WhatsAppTriggerNode` |
| Trigger Type | `WHATSAPP` |
| Icon | whatsapp |
| Category | triggers |

### Configuration Properties

#### Connection Settings

| Property | Type | Default | Tab | Description |
|----------|------|---------|-----|-------------|
| access_token | string | `""` | connection | WhatsApp Business API access token |
| phone_number_id | string | `""` | connection | WhatsApp Business phone number ID |
| credential_name | string | `""` | connection | Alternative: stored credential name |

#### Webhook Settings

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| verify_token | string | `""` | Token for webhook verification |
| webhook_path | string | `/whatsapp/webhook` | Path for webhook endpoint |

#### Filters

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| filter_phone_numbers | string | `""` | Comma-separated phone numbers to allow |
| message_types | string | `text,image,...` | Message types to trigger on |
| include_status_updates | boolean | `false` | Also trigger on status updates |

### Output Ports

| Port | Type | Description |
|------|------|-------------|
| message_id | string | WhatsApp message ID |
| from_number | string | Sender's phone number |
| to_number | string | Your business phone number |
| timestamp | string | Message timestamp |
| text | string | Message text (for text messages) |
| message_type | string | Type: `text`, `image`, `document`, etc. |
| media_id | string | Media ID for media messages |
| media_url | string | Media URL (if available) |
| caption | string | Media caption |
| contact_name | string | Sender's WhatsApp profile name |
| raw_message | dict | Full message object |
| exec_out | exec | Execution flow continues |

### WhatsApp Business Setup

1. **Create Meta Business Account**
   - Go to [Meta for Developers](https://developers.facebook.com)
   - Create a Meta Business account

2. **Create WhatsApp Business App**
   - Create new app (type: Business)
   - Add WhatsApp product

3. **Get Credentials**
   - Copy permanent access token
   - Copy phone number ID
   - Set verify token for webhook

4. **Configure Webhook**
   - Set webhook URL to your public endpoint
   - Subscribe to messages webhook field
   - Verify with your verify token

### Example Configuration

```json
{
  "access_token": "EAAxxxxxxxx...",
  "phone_number_id": "123456789012345",
  "verify_token": "my-secret-verify-token",
  "webhook_path": "/whatsapp/webhook",
  "message_types": "text,image,document",
  "filter_phone_numbers": "",
  "include_status_updates": false
}
```

### Message Type Filtering

| Type | Description |
|------|-------------|
| `text` | Plain text messages |
| `image` | Image attachments |
| `document` | Document attachments |
| `audio` | Voice messages |
| `video` | Video attachments |
| `location` | Location shares |
| `contacts` | Contact cards |
| `sticker` | Stickers |

```json
{
  "message_types": "text,document,image"
}
```

### Filter by Phone Number

Only respond to specific numbers:

```json
{
  "filter_phone_numbers": "+12025551234,+14155559876"
}
```

---

## Complete Workflow Examples

### Telegram Bot Command Handler

```python
from casare_rpa.nodes.trigger_nodes import TelegramTriggerNode
from casare_rpa.nodes.messaging.telegram import TelegramSendNode
from casare_rpa.nodes.control_flow import SwitchNode

# Telegram trigger for bot commands
trigger = TelegramTriggerNode(
    node_id="telegram_commands",
    config={
        "bot_token": "123456789:ABC-DEF...",
        "commands_only": True,
        "filter_commands": "start,help,status",
    }
)

# Workflow:
# [Telegram Trigger] -> [Switch on command] -> [Handle start]
#                                           -> [Handle help]
#                                           -> [Handle status]
```

### WhatsApp Customer Support

```python
from casare_rpa.nodes.trigger_nodes import WhatsAppTriggerNode
from casare_rpa.nodes.messaging.whatsapp import WhatsAppSendNode

trigger = WhatsAppTriggerNode(
    node_id="whatsapp_support",
    config={
        "access_token": "EAAxxxxxxxx...",
        "phone_number_id": "123456789012345",
        "verify_token": "webhook-verify-token",
        "message_types": "text,image,document",
    }
)

# Workflow:
# [WhatsApp Trigger] -> [Classify Message] -> [Route to Handler]
#        |
#        +-- text          -> Customer question
#        +-- from_number   -> Customer phone
#        +-- contact_name  -> Customer name
```

## Workflow JSON Example

### Telegram Echo Bot

```json
{
  "nodes": [
    {
      "id": "telegram_trigger_1",
      "type": "TelegramTriggerNode",
      "config": {
        "bot_token": "123456789:ABC-DEF...",
        "mode": "polling",
        "polling_interval": 2
      },
      "position": {"x": 100, "y": 200}
    },
    {
      "id": "telegram_send_1",
      "type": "TelegramSendNode",
      "config": {
        "bot_token": "123456789:ABC-DEF...",
        "chat_id": "{{chat_id}}",
        "message": "You said: {{text}}"
      },
      "position": {"x": 400, "y": 200}
    }
  ],
  "connections": [
    {
      "source_node": "telegram_trigger_1",
      "source_port": "exec_out",
      "target_node": "telegram_send_1",
      "target_port": "exec_in"
    }
  ]
}
```

## Common Use Cases

### Customer Support Bot
1. Trigger on incoming message
2. Classify intent using AI
3. Route to appropriate handler
4. Send response

### Order Status Lookup
1. Trigger on `/status` command with order ID
2. Query database for order
3. Format and send status message

### Document Processing
1. Trigger on document messages
2. Download attachment
3. Process document (OCR, extract data)
4. Send confirmation with results

### Appointment Booking
1. Trigger on booking request message
2. Check availability
3. Create appointment
4. Send confirmation with details

## Security Considerations

### Telegram

- **Store tokens securely**: Use credential manager, not config files
- **Filter users/chats**: Restrict who can trigger workflows
- **Validate commands**: Check command format before processing
- **Use webhook in production**: More secure than polling

### WhatsApp

- **Verify webhook requests**: Always validate webhook signatures
- **Use HTTPS**: Required for webhook endpoints
- **Protect access tokens**: Never expose in client-side code
- **Implement rate limiting**: Prevent abuse

## Best Practices

1. **Validate Input**: Always validate message content before processing
2. **Handle Errors Gracefully**: Send user-friendly error messages
3. **Log Conversations**: Track messages for debugging and compliance
4. **Implement Timeouts**: Don't leave users waiting
5. **Use Commands**: Structured commands are easier to process than free text
6. **Confirm Actions**: Acknowledge user input immediately
7. **Test Thoroughly**: Test with various message types and edge cases

## Related

- [Email Triggers](email-triggers.md) - Email-based triggering
- [Google Triggers](google-triggers.md) - Google Workspace triggers
- [Webhook Trigger](webhook.md) - Generic HTTP webhook
- [Trigger Overview](index.md) - All available triggers
