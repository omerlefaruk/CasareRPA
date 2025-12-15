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
| `file/` | File I/O, **Super Nodes** | ReadFileNode, WriteFileNode, **FileSystemSuperNode**, **StructuredDataSuperNode** |
| `google/` | Google services | SheetsNode, DriveNode, DocsNode |
| `http/` | HTTP requests | HttpRequestNode |
| `llm/` | AI/LLM nodes | LLMNode, PromptNode |
| `messaging/` | Telegram, WhatsApp | TelegramNode |
| `system/` | System operations | RunProcessNode |
| `trigger_nodes/` | Workflow triggers | ScheduleNode, WebhookNode |
| `workflow/` | Subflows | SubflowNode |

## Super Nodes

Super Nodes are consolidated action-based nodes that replace multiple atomic nodes with a single configurable node. They use dynamic ports and conditional widget visibility.

| Super Node | Actions | File |
|------------|---------|------|
| `FileSystemSuperNode` | Read/Write/Append/Delete/Copy/Move File, File Exists, Get File Size/Info, Create Directory, List Files/Directory (12 actions) | `file/super_node.py` |
| `StructuredDataSuperNode` | Read/Write CSV, Read/Write JSON, Zip/Unzip Files, Image Convert (7 actions) | `file/super_node.py` |

See [Super Node Pattern Documentation](../../../../.brain/docs/super-node-pattern.md) for implementation guide.

## Key Files (Root)

| File | Contains | Lines |
|------|----------|-------|
| `__init__.py` | Lazy-load registry | ~1400 |
| `registry_data.py` | `NODE_REGISTRY` (single source of truth) | ~25000 |
| `data_nodes.py` | Browser extraction nodes (legacy file placement) | ~700 |
| `wait_nodes.py` | Wait operations (legacy file placement) | ~400 |
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

Nodes are registered in `NODE_REGISTRY` in `registry_data.py` (single source of truth):
```python
NODE_REGISTRY = {
    "LaunchBrowserNode": "browser.lifecycle",
    "ClickElementNode": "browser.interaction",
    # ...
}
```

## Creating New Nodes

See `.brain/docs/node-checklist.md` for the canonical checklist:
1. Check existing nodes first
2. Implement with `@properties(...)` + `@node(...)`
3. Add to `src/casare_rpa/nodes/registry_data.py`
4. Create tests in `tests/nodes/`

## Related Indexes

- [browser/_index.md](browser/_index.md) - Browser automation base
- [control_flow/_index.md](control_flow/_index.md) - Control flow nodes
- [desktop_nodes/_index.md](desktop_nodes/_index.md) - Desktop automation
- [file/_index.md](file/_index.md) - File I/O and image processing
- [google/_index.md](google/_index.md) - Google services (Drive, Sheets, Docs, Gmail)
