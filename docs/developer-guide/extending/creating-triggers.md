# Creating Trigger Nodes

Trigger nodes are workflow entry points that START workflows rather than run within them. This guide covers how to create trigger nodes for CasareRPA.

## Triggers vs Executable Nodes

| Aspect | Executable Node | Trigger Node |
|--------|-----------------|--------------|
| Purpose | Performs operation within workflow | Starts a workflow |
| `exec_in` port | Yes (receives execution flow) | **No** (is the entry point) |
| `exec_out` port | Yes | Yes |
| Base class | `BaseNode` | `BaseTriggerNode` |
| Decorator | `@node` | `@trigger_node` (via `@properties`) |
| Execution | Called during workflow run | Listens for external events |

## Trigger Architecture

```
External Event (HTTP, Schedule, File Change, etc.)
        |
        v
+------------------+
| Trigger System   |  <-- Listens for events
+------------------+
        |
        v
+------------------+
| Trigger Node     |  <-- Populates payload ports
+------------------+
        |
        v (exec_out)
+------------------+
| Next Node        |  <-- Workflow continues
+------------------+
```

## Quick Start Example

```python
"""Telegram Trigger Node - Fires on incoming Telegram messages."""

from typing import Any, Dict

from casare_rpa.domain.decorators import properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.nodes.trigger_nodes import trigger_node, BaseTriggerNode
from casare_rpa.triggers.base import TriggerType


@properties(
    PropertyDef(
        "bot_token",
        PropertyType.STRING,
        required=True,
        label="Bot Token",
        tab="connection",
        tooltip="Telegram bot API token from @BotFather",
    ),
    PropertyDef(
        "filter_chat_ids",
        PropertyType.STRING,
        default="",
        label="Filter Chat IDs",
        tooltip="Comma-separated chat IDs to filter (empty = all)",
    ),
)
@trigger_node
class TelegramTriggerNode(BaseTriggerNode):
    """
    Triggers workflow on incoming Telegram messages.

    Config:
        bot_token: Telegram bot API token (required)
        filter_chat_ids: Comma-separated chat IDs to filter

    Payload Outputs:
        message_id: The Telegram message ID
        chat_id: The chat ID where message was sent
        text: The message text content
        from_user: Dictionary with sender information
    """

    trigger_display_name = "Telegram"
    trigger_description = "Trigger on Telegram message"
    trigger_icon = "telegram"
    trigger_category = "triggers"

    def _define_payload_ports(self) -> None:
        """Define output ports for trigger payload data."""
        self.add_output_port("message_id", DataType.INTEGER)
        self.add_output_port("chat_id", DataType.INTEGER)
        self.add_output_port("text", DataType.STRING)
        self.add_output_port("from_user", DataType.DICT)

    def get_trigger_type(self) -> TriggerType:
        """Return the TriggerType enum value."""
        return TriggerType.TELEGRAM

    def get_trigger_config(self) -> Dict[str, Any]:
        """Return trigger-specific configuration."""
        filter_ids = self.config.get("filter_chat_ids", "")
        chat_ids = [int(x.strip()) for x in filter_ids.split(",") if x.strip()]

        return {
            "bot_token": self.config.get("bot_token", ""),
            "filter_chat_ids": chat_ids,
        }
```

## Implementation Checklist

1. Apply `@trigger_node` decorator
2. Apply `@properties` decorator (credentials in "connection" tab)
3. Extend `BaseTriggerNode`
4. Implement `_define_payload_ports()`
5. Implement `get_trigger_type()`
6. Implement `get_trigger_config()`
7. Create visual trigger node
8. Register in `_NODE_REGISTRY`
9. Export from packages

## Step 1: @trigger_node Decorator

Use the trigger node decorator instead of `@node`:

```python
from casare_rpa.nodes.trigger_nodes import trigger_node

@trigger_node
class MyTriggerNode(BaseTriggerNode):
    ...
```

This decorator:
- Does NOT add `exec_in` port (triggers start workflows)
- Marks the node as a trigger node
- Registers trigger-specific metadata

## Step 2: @properties Decorator

Same as executable nodes, but use the "connection" tab for credentials:

```python
@properties(
    # Connection properties first
    PropertyDef(
        "api_key",
        PropertyType.STRING,
        required=True,
        label="API Key",
        tab="connection",
    ),
    PropertyDef(
        "webhook_secret",
        PropertyType.STRING,
        label="Webhook Secret",
        tab="connection",
    ),
    # Main properties
    PropertyDef(
        "filter_pattern",
        PropertyType.STRING,
        default="*",
        label="Filter Pattern",
        tab="properties",
    ),
)
```

## Step 3: BaseTriggerNode

Extend `BaseTriggerNode` and set trigger metadata:

```python
from casare_rpa.nodes.trigger_nodes import BaseTriggerNode

class MyTriggerNode(BaseTriggerNode):
    """My custom trigger node."""

    # Trigger metadata
    trigger_display_name = "My Trigger"
    trigger_description = "Triggers when my event occurs"
    trigger_icon = "my_trigger"  # Icon identifier
    trigger_category = "triggers"

    def __init__(self, node_id, config=None):
        super().__init__(node_id, config)
        # Trigger-specific initialization
```

## Step 4: Define Payload Ports

Implement `_define_payload_ports()` to define output ports for trigger data:

```python
def _define_payload_ports(self) -> None:
    """Define output ports for trigger payload data."""
    from casare_rpa.domain.value_objects.types import DataType

    self.add_output_port("payload", DataType.DICT)
    self.add_output_port("headers", DataType.DICT)
    self.add_output_port("timestamp", DataType.STRING)
```

Common port types:

| DataType | Use For |
|----------|---------|
| `STRING` | Text values (IDs, names, content) |
| `INTEGER` | Numeric IDs, counts |
| `FLOAT` | Decimal values |
| `BOOLEAN` | Flags |
| `DICT` | Complex objects (JSON payloads) |
| `LIST` | Arrays of values |
| `ANY` | Dynamic/unknown type |

## Step 5: get_trigger_type()

Return the appropriate `TriggerType` enum value:

```python
from casare_rpa.triggers.base import TriggerType

def get_trigger_type(self) -> TriggerType:
    """Return the TriggerType enum value."""
    return TriggerType.WEBHOOK
```

### Available TriggerTypes

```python
class TriggerType(Enum):
    # Core triggers
    MANUAL = "manual"           # Manual start
    SCHEDULED = "scheduled"     # Cron/interval schedule
    WEBHOOK = "webhook"         # HTTP webhook
    FILE_WATCH = "file_watch"   # File system changes
    APP_EVENT = "app_event"     # Application events
    ERROR = "error"             # Error handling trigger

    # Communication
    EMAIL = "email"             # Email trigger
    TELEGRAM = "telegram"       # Telegram messages
    WHATSAPP = "whatsapp"       # WhatsApp messages
    CHAT = "chat"               # Generic chat

    # Google Workspace
    GMAIL = "gmail"             # Gmail messages
    SHEETS = "sheets"           # Google Sheets changes
    DRIVE = "drive"             # Google Drive events
    CALENDAR = "calendar"       # Google Calendar events

    # Data sources
    RSS_FEED = "rss_feed"       # RSS feed updates
    SSE = "sse"                 # Server-Sent Events

    # Workflow
    WORKFLOW_CALL = "workflow_call"  # Called by another workflow
    FORM = "form"               # Form submission
```

## Step 6: get_trigger_config()

Return a dictionary with trigger-specific configuration:

```python
def get_trigger_config(self) -> Dict[str, Any]:
    """Return trigger-specific configuration."""
    return {
        "api_key": self.config.get("api_key", ""),
        "webhook_url": self.config.get("webhook_url", ""),
        "events": self.config.get("events", ["push"]),
        "filters": {
            "branches": self.config.get("filter_branches", []),
        },
    }
```

This configuration is passed to the trigger system for event listening.

## Step 7: Visual Trigger Node

Create the visual representation extending `VisualTriggerNode`:

```python
"""Visual trigger node for Telegram."""

from casare_rpa.presentation.canvas.visual_nodes.triggers.base import (
    VisualTriggerNode,
)
from casare_rpa.domain.value_objects.types import DataType


class VisualTelegramTriggerNode(VisualTriggerNode):
    """Visual representation of TelegramTriggerNode."""

    __identifier__ = "casare_rpa.triggers"
    NODE_NAME = "Telegram Trigger"
    NODE_CATEGORY = "triggers"
    CASARE_NODE_CLASS = "TelegramTriggerNode"

    def _setup_payload_ports(self) -> None:
        """Setup the visual payload output ports."""
        self.add_typed_output("message_id", DataType.INTEGER)
        self.add_typed_output("chat_id", DataType.INTEGER)
        self.add_typed_output("text", DataType.STRING)
        self.add_typed_output("from_user", DataType.DICT)
```

Key differences from regular `VisualNode`:

- Extends `VisualTriggerNode` (not `VisualNode`)
- Implements `_setup_payload_ports()` instead of `setup_ports()`
- No `exec_in` port (auto-excluded)
- Visual styling indicates it's a trigger (green header)

## Step 8: Registration

### _NODE_REGISTRY

In `src/casare_rpa/nodes/__init__.py`:

```python
_NODE_REGISTRY = {
    # ... existing nodes ...
    "TelegramTriggerNode": "trigger_nodes.telegram_trigger_node",
}
```

### Export from Packages

Logic node in `src/casare_rpa/nodes/trigger_nodes/__init__.py`:

```python
from .telegram_trigger_node import TelegramTriggerNode

__all__ = [
    # ... existing exports ...
    "TelegramTriggerNode",
]
```

Visual node in `src/casare_rpa/presentation/canvas/visual_nodes/triggers/__init__.py`:

```python
from .nodes import VisualTelegramTriggerNode

__all__ = [
    # ... existing exports ...
    "VisualTelegramTriggerNode",
]
```

## Trigger Node Categories

### Event-based Triggers

| Node | TriggerType | Purpose |
|------|-------------|---------|
| `WebhookTriggerNode` | `WEBHOOK` | HTTP webhook endpoint |
| `AppEventTriggerNode` | `APP_EVENT` | Application events |
| `ErrorTriggerNode` | `ERROR` | Error handling |

### Time-based Triggers

| Node | TriggerType | Purpose |
|------|-------------|---------|
| `ScheduleTriggerNode` | `SCHEDULED` | Cron/interval schedules |

### File-based Triggers

| Node | TriggerType | Purpose |
|------|-------------|---------|
| `FileWatchTriggerNode` | `FILE_WATCH` | File system changes |

### Communication Triggers

| Node | TriggerType | Purpose |
|------|-------------|---------|
| `EmailTriggerNode` | `EMAIL` | Email messages |
| `GmailTriggerNode` | `GMAIL` | Gmail-specific |
| `TelegramTriggerNode` | `TELEGRAM` | Telegram messages |
| `WhatsAppTriggerNode` | `WHATSAPP` | WhatsApp messages |

### Google Workspace Triggers

| Node | TriggerType | Purpose |
|------|-------------|---------|
| `DriveTriggerNode` | `DRIVE` | Drive file events |
| `SheetsTriggerNode` | `SHEETS` | Sheets changes |
| `CalendarTriggerNode` | `CALENDAR` | Calendar events |

### Data Source Triggers

| Node | TriggerType | Purpose |
|------|-------------|---------|
| `RSSFeedTriggerNode` | `RSS_FEED` | RSS feed updates |
| `SSETriggerNode` | `SSE` | Server-Sent Events |

### Workflow Triggers

| Node | TriggerType | Purpose |
|------|-------------|---------|
| `WorkflowCallTriggerNode` | `WORKFLOW_CALL` | Called by workflow |
| `FormTriggerNode` | `FORM` | Form submission |
| `ChatTriggerNode` | `CHAT` | Chat interface |

## Complete Example: Webhook Trigger

```python
"""Webhook Trigger Node - Fires on incoming HTTP requests."""

from typing import Any, Dict

from casare_rpa.domain.decorators import properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.nodes.trigger_nodes import trigger_node, BaseTriggerNode
from casare_rpa.triggers.base import TriggerType


@properties(
    PropertyDef(
        "path",
        PropertyType.STRING,
        default="/webhook",
        required=True,
        label="Webhook Path",
        tooltip="URL path for the webhook endpoint",
        essential=True,
    ),
    PropertyDef(
        "methods",
        PropertyType.MULTI_CHOICE,
        default=["POST"],
        choices=["GET", "POST", "PUT", "PATCH", "DELETE"],
        label="HTTP Methods",
        tooltip="Allowed HTTP methods",
    ),
    PropertyDef(
        "secret",
        PropertyType.STRING,
        label="Webhook Secret",
        tab="connection",
        tooltip="Secret for signature validation (optional)",
    ),
)
@trigger_node
class WebhookTriggerNode(BaseTriggerNode):
    """
    Triggers workflow on incoming HTTP webhook requests.

    Config:
        path: Webhook URL path (default: /webhook)
        methods: Allowed HTTP methods (default: POST)
        secret: Optional secret for signature validation

    Payload Outputs:
        body: Request body (JSON or form data)
        headers: Request headers dictionary
        query: Query parameters dictionary
        method: HTTP method used
    """

    trigger_display_name = "Webhook"
    trigger_description = "Trigger on HTTP webhook request"
    trigger_icon = "webhook"
    trigger_category = "triggers"

    def _define_payload_ports(self) -> None:
        """Define output ports for webhook payload."""
        self.add_output_port("body", DataType.DICT)
        self.add_output_port("headers", DataType.DICT)
        self.add_output_port("query", DataType.DICT)
        self.add_output_port("method", DataType.STRING)

    def get_trigger_type(self) -> TriggerType:
        return TriggerType.WEBHOOK

    def get_trigger_config(self) -> Dict[str, Any]:
        return {
            "path": self.config.get("path", "/webhook"),
            "methods": self.config.get("methods", ["POST"]),
            "secret": self.config.get("secret", ""),
        }
```

## File Structure

```
src/casare_rpa/
├── nodes/
│   └── trigger_nodes/
│       ├── __init__.py           # Exports
│       ├── base_trigger_node.py  # BaseTriggerNode
│       ├── webhook_trigger_node.py
│       ├── telegram_trigger_node.py
│       └── ...
│
└── presentation/
    └── canvas/
        └── visual_nodes/
            └── triggers/
                ├── __init__.py   # Exports
                ├── base.py       # VisualTriggerNode
                └── nodes.py      # Visual implementations
```

## Next Steps

- [Creating Nodes](creating-nodes.md) - Standard executable nodes
- [Visual Nodes](visual-nodes.md) - Custom UI rendering
- [Custom Widgets](custom-widgets.md) - Property widget development
