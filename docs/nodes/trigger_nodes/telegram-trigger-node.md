# TelegramTriggerNode

Telegram trigger node that listens for incoming messages.

`:material-bell: Trigger`


**Module:** `casare_rpa.nodes.trigger_nodes.telegram_trigger_node`
**File:** `src\casare_rpa\nodes\trigger_nodes\telegram_trigger_node.py:109`


## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `message_id` | INTEGER | Message ID |
| `chat_id` | INTEGER | Chat ID |
| `user_id` | INTEGER | User ID |
| `username` | STRING | Username |
| `first_name` | STRING | First Name |
| `text` | STRING | Message Text |
| `is_command` | BOOLEAN | Is Command |
| `command` | STRING | Command Name |
| `command_args` | STRING | Command Args |
| `message_type` | STRING | Message Type |
| `raw_update` | DICT | Raw Update |

## Configuration Properties

### Advanced Tab

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `polling_interval` | INTEGER | `2` | No | Seconds between polls in polling mode |
| `allowed_updates` | STRING | `message` | No | Comma-separated update types to receive |

### Connection Tab

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `bot_token` | STRING | `` | No | Telegram bot token from @BotFather |
| `credential_name` | STRING | `` | No | Name of stored credential (alternative to bot token) |

### Properties Tab

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `mode` | CHOICE | `auto` | No | How to receive updates: webhook (public URL required), polling, or auto Choices: auto, webhook, polling |
| `webhook_url` | STRING | `` | No | Public URL for webhook mode (auto-detected from CASARE_WEBHOOK_URL if empty) |
| `filter_chat_ids` | STRING | `` | No | Comma-separated chat IDs to allow (empty = all) |
| `filter_user_ids` | STRING | `` | No | Comma-separated user IDs to allow (empty = all) |
| `commands_only` | BOOLEAN | `False` | No | Only trigger on bot commands (e.g., /start, /help) |
| `filter_commands` | STRING | `` | No | Comma-separated commands to trigger on (empty = all commands) |

## Inheritance

Extends: `BaseTriggerNode`
