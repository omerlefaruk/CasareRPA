# Messaging Integrations Research: WhatsApp & Telegram

**Status**: COMPLETE
**Date**: 2025-12-01
**Researcher**: Research Specialist Agent

---

## Executive Summary

Research on n8n's WhatsApp and Telegram integrations to define feature requirements for CasareRPA messaging nodes. Both platforms use webhook-based triggers with comprehensive message/media operations.

---

## 1. WhatsApp Business Cloud Integration

### API Used
- **WhatsApp Business Cloud API** (Meta/Facebook)
- Official Cloud API endpoint: `graph.facebook.com`
- Requires Meta Business Account and WhatsApp Business Account

### Authentication Method
- **OAuth 2.0** with Meta Business credentials
- Required permissions:
  - `whatsapp_business_management`
  - `whatsapp_business_messaging`
  - `business_management`
- Requires Phone Number ID and WhatsApp Business Account ID

### Triggers Available

| Trigger | Description |
|---------|-------------|
| Incoming Message | New message received (text, media, location, contact) |
| Message Status | Delivery status updates (sent, delivered, read, failed) |

**Important Limitations:**
- Only ONE webhook per app (production vs test URL conflict)
- Status updates trigger same webhook as messages (filter needed)
- Meta verify token required for webhook validation

### Operations Available

#### Message Operations

| Operation | Description | Parameters |
|-----------|-------------|------------|
| **Send Text** | Plain text message | recipient, text (max 4096 chars) |
| **Send Template** | Pre-approved templates | template_name, language, components, parameters |
| **Send Image** | Image transmission | recipient, image (URL/media_id/binary), caption |
| **Send Video** | Video transmission | recipient, video (URL/media_id/binary), caption |
| **Send Audio** | Audio file | recipient, audio (URL/media_id/binary) |
| **Send Document** | File attachment | recipient, document (URL/media_id/binary), filename, caption |
| **Send Location** | GPS coordinates | recipient, latitude, longitude, name, address |
| **Send Contact** | vCard contact | recipient, contact (name, phones, emails, addresses) |
| **Send Sticker** | Sticker graphic | recipient, sticker (URL/media_id/binary) |
| **Send and Wait** | Message with response wait | recipient, message, timeout, approval_type |

#### Media Operations

| Operation | Description |
|-----------|-------------|
| **Upload Media** | Upload file to WhatsApp servers |
| **Download Media** | Retrieve media by ID |
| **Delete Media** | Remove uploaded media |

#### Template Components
- **Header**: Text (60 chars), Image, Video, Document, Location
- **Body**: Text with variables ({{1}}, {{2}}, etc.)
- **Footer**: Text only
- **Buttons**: Quick reply, URL, Phone number

### 24-Hour Rule
- Templates can be sent anytime (proactive)
- Free-form messages only within 24-hour window after user message
- Window resets with each user message

---

## 2. Telegram Bot Integration

### API Used
- **Telegram Bot API** (api.telegram.org)
- Bot created via @BotFather
- All operations via bot token

### Authentication Method
- **Bot Token** (from @BotFather)
- Format: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`
- Simple header-based auth (token in URL path)

### Trigger Events (Webhook Mode)

| Event | Description |
|-------|-------------|
| `*` | All updates |
| `message` | New message (text, photo, sticker, etc.) |
| `callback_query` | Inline keyboard button press |
| `inline_query` | Inline mode query (@bot query) |
| `channel_post` | New channel post |
| `edited_message` | Edited message |
| `edited_channel_post` | Edited channel post |
| `poll` | Poll state change |
| `pre_checkout_query` | Payment pre-checkout |
| `shipping_query` | Shipping info request |
| `chat_join_request` | Join request (requires can_invite_users) |

### Webhook vs Polling

| Mode | Pros | Cons |
|------|------|------|
| **Webhook** | Real-time, efficient | Requires HTTPS, public URL |
| **Polling** | Works behind firewall | Higher latency, more requests |

**Webhook Limitation:** Only ONE webhook URL per bot

### Operations Available

#### Message Operations

| Operation | Description | Key Parameters |
|-----------|-------------|----------------|
| **Send Message** | Text message | chat_id, text, parse_mode, reply_markup |
| **Send Photo** | Image | chat_id, photo, caption |
| **Send Video** | Video file | chat_id, video, caption, duration |
| **Send Audio** | Audio in music player | chat_id, audio, title, performer |
| **Send Document** | Generic file | chat_id, document, caption |
| **Send Animation** | GIF/MP4 (no sound) | chat_id, animation, caption |
| **Send Voice** | Voice message (.ogg) | chat_id, voice, duration |
| **Send Video Note** | Round video | chat_id, video_note |
| **Send Sticker** | .WEBP, .TGS, .WEBM | chat_id, sticker |
| **Send Location** | GPS coordinates | chat_id, latitude, longitude, live_period |
| **Send Venue** | Location with name | chat_id, latitude, longitude, title, address |
| **Send Contact** | Phone contact | chat_id, phone_number, first_name |
| **Send Poll** | Poll/Quiz | chat_id, question, options, type |
| **Send Media Group** | Album (2-10 items) | chat_id, media[] |
| **Send Chat Action** | Typing indicator | chat_id, action (typing, upload_photo, etc.) |

#### Message Management

| Operation | Description |
|-----------|-------------|
| **Edit Message Text** | Modify sent text |
| **Edit Message Caption** | Modify media caption |
| **Edit Message Reply Markup** | Update inline keyboard |
| **Delete Message** | Remove message |
| **Forward Message** | Forward to another chat |
| **Copy Message** | Copy without "Forwarded" label |
| **Pin Message** | Pin in chat |
| **Unpin Message** | Remove pin |

#### Callback Operations

| Operation | Description |
|-----------|-------------|
| **Answer Callback Query** | Respond to inline button press |
| **Answer Inline Query** | Respond to @bot inline query |

#### Chat Operations

| Operation | Description |
|-----------|-------------|
| **Get Chat** | Chat details |
| **Get Chat Member** | User info in chat |
| **Get Chat Member Count** | Member count |
| **Leave Chat** | Exit group/channel |
| **Ban Chat Member** | Ban user |
| **Unban Chat Member** | Unban user |
| **Restrict Chat Member** | Limit permissions |
| **Promote Chat Member** | Grant admin rights |

#### File Operations

| Operation | Description |
|-----------|-------------|
| **Get File** | Get file path for download |
| **Download File** | Download by file_id |

### Reply Markup Types
- **InlineKeyboardMarkup** - Buttons attached to message
- **ReplyKeyboardMarkup** - Custom keyboard
- **ReplyKeyboardRemove** - Remove custom keyboard
- **ForceReply** - Force reply to message

---

## 3. Recommended Features for CasareRPA

### Priority 1: Essential Operations

#### WhatsApp Nodes
1. **WhatsAppSendTextNode** - Send plain text
2. **WhatsAppSendTemplateNode** - Send approved templates
3. **WhatsAppSendMediaNode** - Send image/video/audio/document
4. **WhatsAppSendLocationNode** - Send GPS coordinates
5. **WhatsAppTriggerNode** - Webhook for incoming messages

#### Telegram Nodes
1. **TelegramSendMessageNode** - Send text with formatting
2. **TelegramSendPhotoNode** - Send images
3. **TelegramSendDocumentNode** - Send files
4. **TelegramSendLocationNode** - Send coordinates
5. **TelegramTriggerNode** - Webhook for updates

### Priority 2: Interactive Features

#### WhatsApp
6. **WhatsAppSendContactNode** - Send contact cards
7. **WhatsAppDownloadMediaNode** - Download received media
8. **WhatsAppUploadMediaNode** - Pre-upload media

#### Telegram
6. **TelegramSendVideoNode** - Send video
7. **TelegramSendAudioNode** - Send audio
8. **TelegramEditMessageNode** - Edit sent messages
9. **TelegramDeleteMessageNode** - Delete messages
10. **TelegramAnswerCallbackNode** - Handle button presses

### Priority 3: Advanced Features

#### WhatsApp
9. **WhatsAppSendInteractiveNode** - Buttons/lists (if API supports)

#### Telegram
11. **TelegramSendPollNode** - Create polls
12. **TelegramSendMediaGroupNode** - Send albums
13. **TelegramGetChatNode** - Get chat info
14. **TelegramBanMemberNode** - Moderation

---

## 4. Implementation Notes

### WhatsApp
- Use aiohttp for async HTTP requests
- Implement template parameter validation
- Handle 24-hour window logic in documentation
- Store media_id for reuse (efficiency)
- Filter status updates vs actual messages in trigger

### Telegram
- Use python-telegram-bot or direct API calls
- Implement reply_markup builder helpers
- Support both webhook and polling modes
- Handle file download via file_path
- Rate limiting: 30 messages/second to same chat

### Common Patterns
- Both use JSON payloads
- Both support media via URL or binary upload
- Both have message ID for tracking
- Both require credential management

---

## 5. Architecture Recommendation

```
src/casare_rpa/nodes/messaging/
    __init__.py
    base.py              # MessagingBaseNode (shared auth, HTTP client)
    whatsapp/
        __init__.py
        whatsapp_nodes.py    # All WhatsApp action nodes
        whatsapp_trigger.py  # WhatsApp webhook trigger
        templates.py         # Template builder helpers
    telegram/
        __init__.py
        telegram_nodes.py    # All Telegram action nodes
        telegram_trigger.py  # Telegram webhook trigger
        keyboards.py         # Reply markup builders

src/casare_rpa/infrastructure/resources/
    whatsapp_manager.py      # WhatsApp API client
    telegram_manager.py      # Telegram Bot API client
```

---

## Sources

- [n8n WhatsApp Business Cloud Documentation](https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.whatsapp/)
- [n8n WhatsApp Trigger Documentation](https://docs.n8n.io/integrations/builtin/trigger-nodes/n8n-nodes-base.whatsapptrigger/)
- [n8n Telegram Node Documentation](https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.telegram/)
- [n8n Telegram Trigger Documentation](https://docs.n8n.io/integrations/builtin/trigger-nodes/n8n-nodes-base.telegramtrigger/)
- [n8n Telegram Message Operations](https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.telegram/message-operations/)
- [n8n Telegram Callback Operations](https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.telegram/callback-operations/)
- [n8n GitHub - TelegramTrigger.node.ts](https://github.com/n8n-io/n8n/blob/master/packages/nodes-base/nodes/Telegram/TelegramTrigger.node.ts)
- [WhatsApp Business Platform Templates](https://www.postman.com/meta/whatsapp-business-platform/folder/5tgpjyz/sending-message-templates)
- [n8n Community - WhatsApp Integration](https://community.n8n.io/t/how-to-get-whatsapp-business-cloud-webhook-to-trigger/28977)
- [Hostinger - n8n Telegram Integration Guide](https://www.hostinger.com/tutorials/n8n-telegram-integration)
