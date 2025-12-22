# Creating Trigger Nodes

Trigger nodes are workflow entry points that **start** workflows (no `exec_in`).

## Trigger Node Contract

- Base class: `BaseTriggerNode` (`src/casare_rpa/nodes/trigger_nodes/base_trigger_node.py`)
- Decorators (mandatory):
  - `@properties(...)` for schema/UI widgets
  - `@node(category="triggers", exec_inputs=[])` to enforce **no `exec_in`**
- Exec ports:
  - Inputs: none
  - Outputs: `exec_out` (default) plus payload outputs you define
- Registry: add to `src/casare_rpa/nodes/registry_data.py` (`NODE_REGISTRY`)
- Visual node: add/update in `src/casare_rpa/presentation/canvas/visual_nodes/triggers/`

## Quick Start Example

```python
from typing import Any, Dict

from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.nodes.trigger_nodes.base_trigger_node import BaseTriggerNode
from casare_rpa.triggers.base import TriggerType


@properties(
    PropertyDef(
        "bot_token",
        PropertyType.STRING,
        required=True,
        tab="connection",
        label="Bot Token",
        tooltip="Telegram bot API token",
        essential=True,
    ),
)
@node(category="triggers", exec_inputs=[])
class TelegramTriggerNode(BaseTriggerNode):
    trigger_display_name = "Telegram"
    trigger_description = "Trigger on Telegram message"
    trigger_icon = "telegram"
    trigger_category = "triggers"

    def _define_payload_ports(self) -> None:
        self.add_output_port("chat_id", DataType.INTEGER)
        self.add_output_port("text", DataType.STRING)

    def get_trigger_type(self) -> TriggerType:
        return TriggerType.TELEGRAM

    def get_trigger_config(self) -> Dict[str, Any]:
        return {"bot_token": self.get_parameter("bot_token", "")}
```

## Checklist

1. Implement trigger node with `@properties(...)` + `@node(category="triggers", exec_inputs=[])`
2. Define payload outputs in `_define_payload_ports()`
3. Implement `get_trigger_type()` and `get_trigger_config()`
4. Register the executable node in `src/casare_rpa/nodes/registry_data.py`
5. Create/update the visual node under `src/casare_rpa/presentation/canvas/visual_nodes/triggers/`
6. Add tests:
   - Unit tests for config extraction (fast)
   - UI E2E test coverage is handled by the canvas roundtrip suite
