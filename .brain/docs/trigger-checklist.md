# Trigger Node Implementation Checklist

> Trigger nodes are DIFFERENT from executable nodes. They START workflows, not run within them.

## Key Differences from Executable Nodes
- Use `@trigger_node` decorator (NOT `@executable_node`)
- Extend `BaseTriggerNode` (NOT `BaseNode`)
- NO exec_in port (triggers START workflows)
- Only exec_out port + payload ports
- Must implement: `get_trigger_type()`, `get_trigger_config()`, `_define_payload_ports()`

## Checklist

### 1. @trigger_node decorator
```python
from casare_rpa.nodes.trigger_nodes import trigger_node
```

### 2. @node_schema decorator
Same as executable nodes. Tab "connection" for API tokens/credentials.

```python
@node_schema(
    PropertyDef("bot_token", PropertyType.STRING, tab="connection", ...),
    PropertyDef("filter_chat_ids", PropertyType.STRING, ...),
)
@trigger_node
class TelegramTriggerNode(BaseTriggerNode): ...
```

### 3. Extend BaseTriggerNode
```python
from casare_rpa.nodes.trigger_nodes import BaseTriggerNode

class MyTriggerNode(BaseTriggerNode):
    trigger_display_name = "Telegram"
    trigger_description = "Trigger on Telegram message"
    trigger_icon = "telegram"
    trigger_category = "triggers"
```

### 4. Implement required methods
```python
def _define_payload_ports(self) -> None:
    """Define output ports for trigger data."""
    self.add_output_port("message_id", DataType.INTEGER, "Message ID")
    self.add_output_port("text", DataType.STRING, "Message Text")

def get_trigger_type(self) -> TriggerType:
    """Return the TriggerType enum value."""
    return TriggerType.TELEGRAM

def get_trigger_config(self) -> Dict[str, Any]:
    """Return trigger-specific config dict."""
    return {
        "bot_token": self.config.get("bot_token", ""),
        "filter_chat_ids": [...],
    }
```

### 5. Visual trigger node
Create in: `presentation/canvas/visual_nodes/triggers/nodes.py`
Extend: `VisualTriggerNode` (NOT `VisualNode`)

```python
class VisualTelegramTriggerNode(VisualTriggerNode):
    __identifier__ = "casare_rpa.triggers"
    NODE_NAME = "Telegram Trigger"
    NODE_CATEGORY = "triggers"
    CASARE_NODE_CLASS = "TelegramTriggerNode"

    def _setup_payload_ports(self) -> None:
        self.add_typed_output("message_id", DataType.INTEGER)
        self.add_typed_output("text", DataType.STRING)
```

### 6. Register in _NODE_REGISTRY
File: `src/casare_rpa/nodes/__init__.py`
```python
"TelegramTriggerNode": "trigger_nodes.telegram_trigger_node",
```

### 7. Export from packages
- Logic: `trigger_nodes/__init__.py`
- Visual: `presentation/canvas/visual_nodes/triggers/__init__.py`

## Available TriggerTypes
From `casare_rpa.triggers.base.TriggerType`:
```
MANUAL, SCHEDULED, WEBHOOK, FILE_WATCH, APP_EVENT, EMAIL, ERROR,
WORKFLOW_CALL, FORM, CHAT, RSS_FEED, SSE, TELEGRAM, WHATSAPP,
GMAIL, SHEETS, DRIVE, CALENDAR
```

## File Structure
```
# Logic node
src/casare_rpa/nodes/trigger_nodes/
├── telegram_trigger_node.py   # @node_schema + @trigger_node + BaseTriggerNode

# Visual node
src/casare_rpa/presentation/canvas/visual_nodes/triggers/
└── nodes.py                   # VisualTelegramTriggerNode(VisualTriggerNode)
```
