# ChatTriggerNode

Chat trigger node that fires when a chat message is received.

`:material-bell: Trigger`


**Module:** `casare_rpa.nodes.trigger_nodes.chat_trigger_node`
**File:** `src\casare_rpa\nodes\trigger_nodes\chat_trigger_node.py:78`


## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `message` | STRING | Message |
| `user_id` | STRING | User ID |
| `user_name` | STRING | User Name |
| `channel_id` | STRING | Channel ID |
| `platform` | STRING | Platform |
| `timestamp` | STRING | Timestamp |
| `reply_to` | STRING | Reply To |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `welcome_message` | STRING | `Hello! How can I ...` | No | Welcome Message |
| `input_placeholder` | STRING | `Type your message...` | No | Input Placeholder |
| `platform` | CHOICE | `web` | No | Chat platform to receive messages from Choices: web, slack, teams, discord, telegram |
| `channel_id` | STRING | `` | No | Channel/room ID for platform-specific triggers |
| `bot_token` | STRING | `` | No | Bot token for platform authentication |
| `message_pattern` | STRING | `` | No | Regex pattern to filter messages |
| `allow_dm` | BOOLEAN | `True` | No | Allow Direct Messages |
| `allow_mentions` | BOOLEAN | `True` | No | Respond to Mentions |

## Inheritance

Extends: `BaseTriggerNode`
