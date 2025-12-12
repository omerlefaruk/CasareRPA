# Nodes Package Index

Quick reference for automation nodes. 413+ nodes across 18 categories.

## Directory Structure

| Directory | Purpose | Key Nodes |
|-----------|---------|-----------|
| `browser/` | Web automation base | BrowserBaseNode, SmartSelectorNode |
| `control_flow/` | Conditionals, loops | IfNode, ForLoopNode, SwitchNode |
| `data/` | Data operations | JSONNode, CSVNode |
| `data_operation/` | Data comparison | DataCompareNode |
| `database/` | SQL operations | DatabaseQueryNode |
| `desktop_nodes/` | Desktop automation | FindElementNode, ClickElementNode |
| `document/` | PDF, Office | PDFReaderNode |
| `email/` | Email automation | SendEmailNode, IMAPNode |
| `error_handling/` | Error recovery | TryCatchNode, RetryNode |
| `file/` | File I/O | ReadFileNode, WriteFileNode |
| `google/` | Google services | SheetsNode, DriveNode, DocsNode |
| `http/` | HTTP requests | HttpRequestNode |
| `llm/` | AI/LLM nodes | LLMNode, PromptNode |
| `messaging/` | Telegram, WhatsApp | TelegramNode |
| `system/` | System operations | RunProcessNode |
| `trigger_nodes/` | Workflow triggers | ScheduleNode, WebhookNode |
| `workflow/` | Subflows | SubflowNode |

## Key Files (Root)

| File | Contains | Lines |
|------|----------|-------|
| `__init__.py` | Lazy-load registry | ~1400 |
| `browser_nodes.py` | Browser lifecycle | ~1540 |
| `interaction_nodes.py` | Click, type, scroll | ~1200 |
| `navigation_nodes.py` | Goto, back, forward | ~700 |
| `text_nodes.py` | Text extraction | ~1200 |
| `data_nodes.py` | Data transforms | ~700 |
| `wait_nodes.py` | Wait operations | ~400 |
| `variable_nodes.py` | Variables | ~400 |

## Entry Points

```python
# Import specific nodes
from casare_rpa.nodes import LaunchBrowserNode, ClickElementNode, TypeInputNode

# Import browser base
from casare_rpa.nodes.browser import BrowserBaseNode, get_page_from_context

# Import control flow
from casare_rpa.nodes.control_flow import IfNode, ForLoopStartNode, BreakNode
```

## Node Registry

Nodes are registered in `_NODE_REGISTRY` dict in `__init__.py`:
```python
_NODE_REGISTRY = {
    "LaunchBrowserNode": "browser_nodes",
    "ClickElementNode": "interaction_nodes",
    # ...
}
```

## Creating New Nodes

See `agent-rules/rules/10-node-workflow.md` for full protocol:
1. Check existing nodes first
2. Create node file with `@executable_node` decorator
3. Add to `_NODE_REGISTRY`
4. Create tests in `tests/nodes/`

## Related Indexes

- [browser/_index.md](browser/_index.md) - Browser automation base
- [control_flow/_index.md](control_flow/_index.md) - Control flow nodes
- [desktop_nodes/_index.md](desktop_nodes/_index.md) - Desktop automation
