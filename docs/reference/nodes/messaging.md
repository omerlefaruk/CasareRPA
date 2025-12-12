# Messaging Nodes

Messaging nodes enable communication via Telegram and WhatsApp. These nodes support sending text messages, media files, documents, locations, and interactive content.

## Telegram Nodes

Telegram nodes use the Bot API to send messages through a Telegram bot.

### Prerequisites

1. Create a bot via [@BotFather](https://t.me/BotFather)
2. Get the bot token
3. Start a conversation with the bot (users must initiate contact first)
4. Get the chat ID (use [@userinfobot](https://t.me/userinfobot) or API)

### Common Properties

All Telegram nodes share these connection properties:

| Property | Type | Description |
|----------|------|-------------|
| `bot_token` | STRING | Telegram Bot token from @BotFather |
| `credential_name` | STRING | Vault credential name (alternative to bot_token) |
| `chat_id` | STRING | Target chat ID or @username |

---

### TelegramSendMessageNode

Send a text message via Telegram.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `bot_token` | STRING | `""` | Bot token (Connection tab) |
| `credential_name` | STRING | `""` | Vault credential name |
| `chat_id` | STRING | (required) | Target chat ID or @username |
| `text` | TEXT | (required) | Message text (1-4096 characters) |
| `parse_mode` | CHOICE | `""` | Formatting: Markdown, MarkdownV2, HTML |
| `disable_notification` | BOOLEAN | `false` | Send silently |
| `reply_to_message_id` | INTEGER | `0` | Message ID to reply to |

#### Ports

**Inputs:**
- `text` (STRING) - Message text
- `parse_mode` (STRING) - Parse mode override
- `disable_notification` (BOOLEAN) - Silent mode
- `reply_to_message_id` (INTEGER) - Reply target

**Outputs:**
- `message_id` (INTEGER) - Sent message ID
- `chat_id` (STRING) - Target chat ID
- `text` (STRING) - Sent text
- `success` (BOOLEAN) - Send success
- `error` (STRING) - Error message

#### Example

```python
# Send notification to Telegram channel
send_telegram = TelegramSendMessageNode(
    node_id="notify_team",
    config={
        "bot_token": "{{telegram_bot_token}}",
        "chat_id": "@my_channel",
        "text": "*Alert:* Process {{process_name}} completed!\n\nResults: {{result_count}} items processed.",
        "parse_mode": "Markdown"
    }
)
```

#### Formatting Examples

**Markdown:**
```
*bold* _italic_ `code` ```preformatted```
[link](https://example.com)
```

**HTML:**
```html
<b>bold</b> <i>italic</i> <code>code</code>
<a href="https://example.com">link</a>
```

---

### TelegramSendPhotoNode

Send a photo via Telegram.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `chat_id` | STRING | (required) | Target chat ID |
| `photo` | STRING | (required) | Photo URL, file path, or file_id |
| `caption` | TEXT | `""` | Photo caption (0-1024 chars) |
| `parse_mode` | CHOICE | `""` | Caption formatting |
| `disable_notification` | BOOLEAN | `false` | Send silently |

#### Ports

**Inputs:**
- `photo` (STRING) - Photo source
- `caption` (STRING) - Caption text
- `parse_mode` (STRING) - Parse mode

**Outputs:**
- `message_id` (INTEGER) - Sent message ID
- `chat_id` (STRING) - Target chat
- `photo_path` (STRING) - Photo source used
- `success` (BOOLEAN) - Send success
- `error` (STRING) - Error message

#### Example

```python
# Send screenshot to monitoring channel
send_photo = TelegramSendPhotoNode(
    node_id="send_screenshot",
    config={
        "chat_id": "{{monitor_chat_id}}",
        "photo": "{{screenshot_path}}",
        "caption": "Screenshot captured at {{timestamp}}"
    }
)
```

---

### TelegramSendDocumentNode

Send a document/file via Telegram.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `chat_id` | STRING | (required) | Target chat ID |
| `document` | STRING | (required) | Document URL, path, or file_id |
| `filename` | STRING | `""` | Custom display filename |
| `caption` | TEXT | `""` | Document caption |
| `parse_mode` | CHOICE | `""` | Caption formatting |
| `disable_notification` | BOOLEAN | `false` | Send silently |

#### Ports

**Inputs:**
- `document` (STRING) - Document source
- `filename` (STRING) - Custom filename
- `caption` (STRING) - Caption text

**Outputs:**
- `message_id` (INTEGER) - Sent message ID
- `document_path` (STRING) - Document source
- `success` (BOOLEAN) - Send success

#### Example

```python
# Send daily report as document
send_report = TelegramSendDocumentNode(
    node_id="send_report",
    config={
        "chat_id": "{{reports_chat_id}}",
        "document": "{{report_file_path}}",
        "filename": "DailyReport_{{date}}.pdf",
        "caption": "Daily report for {{date}}"
    }
)
```

---

### TelegramSendLocationNode

Send a location via Telegram.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `chat_id` | STRING | (required) | Target chat ID |
| `latitude` | FLOAT | (required) | Latitude (-90 to 90) |
| `longitude` | FLOAT | (required) | Longitude (-180 to 180) |
| `disable_notification` | BOOLEAN | `false` | Send silently |

#### Ports

**Inputs:**
- `latitude` (FLOAT) - Latitude coordinate
- `longitude` (FLOAT) - Longitude coordinate

**Outputs:**
- `message_id` (INTEGER) - Sent message ID
- `latitude` (FLOAT) - Sent latitude
- `longitude` (FLOAT) - Sent longitude
- `success` (BOOLEAN) - Send success

---

## WhatsApp Nodes

WhatsApp nodes use the WhatsApp Business Cloud API via Meta's Graph API.

### Prerequisites

1. Create a Meta Business account
2. Set up WhatsApp Business API in Meta Business Suite
3. Get Access Token and Phone Number ID
4. For business-initiated messages: Use pre-approved templates

### Common Properties

All WhatsApp nodes share these connection properties:

| Property | Type | Description |
|----------|------|-------------|
| `access_token` | STRING | Meta Graph API access token |
| `phone_number_id` | STRING | WhatsApp Business phone number ID |
| `credential_name` | STRING | Vault credential name |
| `to` | STRING | Recipient phone number (with country code) |

---

### WhatsAppSendMessageNode

Send a text message via WhatsApp.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `access_token` | STRING | `""` | Meta access token |
| `phone_number_id` | STRING | `""` | Phone number ID |
| `credential_name` | STRING | `""` | Vault credential |
| `to` | STRING | (required) | Recipient phone (+country code) |
| `text` | TEXT | (required) | Message text (up to 4096 chars) |
| `preview_url` | BOOLEAN | `false` | Enable URL preview |

#### Ports

**Inputs:**
- `text` (STRING) - Message text
- `preview_url` (BOOLEAN) - URL preview toggle

**Outputs:**
- `message_id` (STRING) - Sent message ID
- `phone_number` (STRING) - Recipient number
- `text` (STRING) - Sent text
- `success` (BOOLEAN) - Send success
- `error` (STRING) - Error message

#### Example

```python
# Send order confirmation
send_confirmation = WhatsAppSendMessageNode(
    node_id="send_confirmation",
    config={
        "access_token": "{{whatsapp_token}}",
        "phone_number_id": "{{phone_number_id}}",
        "to": "{{customer_phone}}",
        "text": "Your order #{{order_id}} has been confirmed. Track: {{tracking_url}}",
        "preview_url": True
    }
)
```

> **Important:** Business-initiated messages require a 24-hour window or pre-approved template.

---

### WhatsAppSendTemplateNode

Send a pre-approved template message.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `to` | STRING | (required) | Recipient phone |
| `template_name` | STRING | (required) | Approved template name |
| `language_code` | STRING | `en_US` | Template language |
| `components` | JSON | `{}` | Template parameters |

#### Template Components Format

```json
[
  {
    "type": "body",
    "parameters": [
      {"type": "text", "text": "John"},
      {"type": "text", "text": "Order123"}
    ]
  },
  {
    "type": "button",
    "sub_type": "url",
    "index": "0",
    "parameters": [
      {"type": "text", "text": "track/12345"}
    ]
  }
]
```

#### Example

```python
# Send order shipped template
send_template = WhatsAppSendTemplateNode(
    node_id="order_shipped",
    config={
        "to": "{{customer_phone}}",
        "template_name": "order_shipped",
        "language_code": "en_US",
        "components": [
            {
                "type": "body",
                "parameters": [
                    {"type": "text", "text": "{{customer_name}}"},
                    {"type": "text", "text": "{{order_id}}"},
                    {"type": "text", "text": "{{delivery_date}}"}
                ]
            }
        ]
    }
)
```

---

### WhatsAppSendImageNode

Send an image via WhatsApp.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `to` | STRING | (required) | Recipient phone |
| `image` | STRING | (required) | Image URL or media ID |
| `caption` | TEXT | `""` | Image caption |

#### Ports

**Outputs:**
- `message_id` (STRING) - Sent message ID
- `image_path` (STRING) - Image source
- `success` (BOOLEAN) - Send success

> **Note:** Images must be hosted on HTTPS URLs accessible by WhatsApp servers.

---

### WhatsAppSendDocumentNode

Send a document via WhatsApp.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `to` | STRING | (required) | Recipient phone |
| `document` | STRING | (required) | Document URL or media ID |
| `filename` | STRING | `""` | Display filename |
| `caption` | TEXT | `""` | Document caption |

---

### WhatsAppSendVideoNode

Send a video via WhatsApp.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `to` | STRING | (required) | Recipient phone |
| `video` | STRING | (required) | Video URL or media ID |
| `caption` | TEXT | `""` | Video caption |

---

### WhatsAppSendLocationNode

Send a location via WhatsApp.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `to` | STRING | (required) | Recipient phone |
| `latitude` | FLOAT | (required) | Latitude (-90 to 90) |
| `longitude` | FLOAT | (required) | Longitude (-180 to 180) |
| `name` | STRING | `""` | Location name |
| `address` | STRING | `""` | Location address |

---

### WhatsAppSendInteractiveNode

Send interactive messages with buttons or lists.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `to` | STRING | (required) | Recipient phone |
| `interactive_type` | CHOICE | `button` | Type: button or list |
| `body_text` | TEXT | (required) | Main message body |
| `action_json` | JSON | (required) | Buttons or list definition |
| `header_json` | JSON | `{}` | Optional header |
| `footer_text` | STRING | `""` | Optional footer |

#### Button Example

```json
{
  "buttons": [
    {"type": "reply", "reply": {"id": "yes", "title": "Yes"}},
    {"type": "reply", "reply": {"id": "no", "title": "No"}}
  ]
}
```

#### List Example

```json
{
  "button": "View Options",
  "sections": [
    {
      "title": "Products",
      "rows": [
        {"id": "prod1", "title": "Product A", "description": "$10.00"},
        {"id": "prod2", "title": "Product B", "description": "$20.00"}
      ]
    }
  ]
}
```

#### Example

```python
# Send confirmation buttons
send_buttons = WhatsAppSendInteractiveNode(
    node_id="confirm_order",
    config={
        "to": "{{customer_phone}}",
        "interactive_type": "button",
        "body_text": "Confirm your order for {{product_name}}?",
        "action_json": {
            "buttons": [
                {"type": "reply", "reply": {"id": "confirm", "title": "Confirm"}},
                {"type": "reply", "reply": {"id": "cancel", "title": "Cancel"}}
            ]
        },
        "footer_text": "Order #{{order_id}}"
    }
)
```

---

## Complete Example: Customer Notification Workflow

```python
# Multi-channel notification workflow

# 1. Send Telegram notification to internal team
telegram_notify = TelegramSendMessageNode(
    node_id="team_notify",
    config={
        "chat_id": "{{team_chat_id}}",
        "text": "New order received!\n\nOrder: #{{order_id}}\nCustomer: {{customer_name}}\nTotal: ${{total}}",
        "parse_mode": "Markdown"
    }
)

# 2. Send WhatsApp confirmation to customer
whatsapp_confirm = WhatsAppSendTemplateNode(
    node_id="customer_confirm",
    config={
        "to": "{{customer_phone}}",
        "template_name": "order_confirmation",
        "components": [
            {
                "type": "body",
                "parameters": [
                    {"type": "text", "text": "{{customer_name}}"},
                    {"type": "text", "text": "{{order_id}}"},
                    {"type": "text", "text": "${{total}}"}
                ]
            }
        ]
    }
)

# 3. Send invoice document
send_invoice = WhatsAppSendDocumentNode(
    node_id="send_invoice",
    config={
        "to": "{{customer_phone}}",
        "document": "{{invoice_url}}",
        "filename": "Invoice_{{order_id}}.pdf",
        "caption": "Your invoice for order #{{order_id}}"
    }
)
```

---

## Best Practices

### Telegram

- Store bot tokens securely in credential vault
- Use parse_mode for rich formatting
- Implement rate limiting (30 messages/second per bot)
- Handle "bot was blocked by user" errors gracefully

### WhatsApp

- Always use templates for business-initiated messages outside 24-hour window
- Pre-approve templates in Meta Business Suite
- Format phone numbers with country code (e.g., +1234567890)
- Handle webhook responses for delivery status
- Respect rate limits (varies by tier)

### Error Handling

```python
# Both platforms output success/error
# Always check success before assuming message was sent
if outputs["success"]:
    message_id = outputs["message_id"]
else:
    error_message = outputs["error"]
    # Handle error (retry, log, alert)
```

### Credential Security

> **Warning:** Never hardcode API tokens. Use:
> - `credential_name` for vault lookup
> - Environment variables
> - Variable placeholders (`{{token}}`)

## Related Documentation

- [Email Nodes](email.md) - Email communication
- [HTTP Nodes](http.md) - Custom API integrations
- [Control Flow](control-flow.md) - Conditional messaging
