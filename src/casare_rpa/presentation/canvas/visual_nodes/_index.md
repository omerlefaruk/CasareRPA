# Visual Nodes Index

Quick reference for visual node implementations. Use for fast discovery.

## Directory Structure

| Directory | Purpose | Node Count | Key Exports |
|-----------|---------|------------|-------------|
| `ai_ml/` | AI/ML nodes | 6 | LLMCompletion, LLMChat, LLMExtractData, LLMSummarize, LLMClassify, LLMTranslate |
| `basic/` | Core workflow nodes | 3 | VisualStartNode, VisualEndNode, VisualCommentNode |
| `browser/` | Web automation | 23 | LaunchBrowser, CloseBrowser, GoToURL, ClickElement, TypeText, ExtractText, TableScraper |
| `control_flow/` | Flow control | 16 | If, ForLoop, WhileLoop, Switch, Break, Continue, Merge, TryCatchFinally |
| `data_operations/` | Data manipulation | 33 | Concatenate, Regex, Math, List ops, Dict ops, DataCompare |
| `database/` | SQL operations | 10 | DatabaseConnect, ExecuteQuery, Transaction, TableExists |
| `desktop_automation/` | Windows UI automation | 36 | LaunchApplication, ActivateWindow, ClickElement, TypeText, SendKeys, OCR |
| `document/` | Document AI | 5 | ClassifyDocument, ExtractForm, ExtractInvoice, ExtractTable |
| `email/` | Email operations | 8 | SendEmail, ReadEmails, GetEmailContent, FilterEmails |
| `error_handling/` | Error recovery | 9 | Retry, ThrowError, OnError, ErrorRecovery, Assert |
| `file_operations/` | File I/O, **Super Nodes** | 42 | ReadFile, WriteFile, CSV, JSON, XML, PDF, FTP, **VisualFileSystemSuperNode**, **VisualStructuredDataSuperNode** |
| `google/` | Google services | 79 | Calendar (12), Gmail (21), Sheets (21), Docs (8), Drive (17) |
| `messaging/` | Chat platforms | 16 | Telegram (9), WhatsApp (7) |
| `office_automation/` | MS Office | 12 | Excel, Word, Outlook |
| `rest_api/` | HTTP/REST | 7 | HttpRequest, SetHeaders, HttpAuth, DownloadFile |
| `scripts/` | Code execution | 5 | RunPythonScript, RunBatchScript, RunJavaScript, EvalExpression |
| `subflows/` | Reusable workflows | 1 | VisualSubflowNode |
| `system/` | System operations | 67 | Clipboard, Dialogs, Services, Process, FileWatcher, QRCode |
| `triggers/` | Event triggers | 17 | Webhook, Schedule, FileWatch, Email, Telegram, Calendar |
| `utility/` | Helpers | 27 | Random, DateTime, Text operations, Reroute |
| `variable/` | Variable management | 3 | SetVariable, GetVariable, IncrementVariable |

**Total: 407 visual nodes across 21 categories**

## Super Nodes (Mixins)

Super Nodes use the `SuperNodeMixin` to provide dynamic port management based on action selection.

| Mixin/File | Purpose |
|------------|---------|
| `mixins/super_node_mixin.py` | Base mixin for dynamic ports and conditional widget visibility |
| `file_operations/super_nodes.py` | Visual implementations for FileSystemSuperNode, StructuredDataSuperNode |

**Super Node Features:**
- Dynamic port creation/deletion based on action dropdown
- Conditional widget visibility via `display_when`/`hidden_when`
- Port schema defined in domain layer (`DynamicPortSchema`)

See [Super Node Pattern Documentation](../../../../../.brain/docs/super-node-pattern.md) for implementation guide.

## Key Files

| File | Contains | Lines |
|------|----------|-------|
| `__init__.py` | `_VISUAL_NODE_REGISTRY` - lazy loading registry, `get_all_visual_node_classes()` | ~610 |
| `base_visual_node.py` | `VisualNode` base class - bridges CasareRPA BaseNode with NodeGraphQt | ~1222 |

## Entry Points

```python
# Import specific visual nodes (lazy-loaded)
from casare_rpa.presentation.canvas.visual_nodes import (
    VisualStartNode,
    VisualEndNode,
    VisualClickElementNode,
    VisualTypeTextNode,
)

# Get all visual node classes (triggers full load)
from casare_rpa.presentation.canvas.visual_nodes import get_all_visual_node_classes
all_nodes = get_all_visual_node_classes()

# Preload specific nodes for performance
from casare_rpa.presentation.canvas.visual_nodes import preload_visual_nodes
preload_visual_nodes(["VisualStartNode", "VisualEndNode"])

# Base class for creating new visual nodes
from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode
```

## Node Counts by Category

| Category | Count | Description |
|----------|-------|-------------|
| system | 67 | Dialogs, clipboard, services, processes |
| google | 79 | Gmail, Sheets, Drive, Docs, Calendar |
| file_operations | 40 | File I/O, CSV, JSON, XML, PDF, FTP |
| desktop_automation | 36 | Windows UI automation |
| data_operations | 33 | String, list, dict operations |
| utility | 27 | Random, datetime, text helpers |
| browser | 23 | Playwright web automation |
| triggers | 17 | Event-based workflow triggers |
| control_flow | 16 | If/Loop/Switch/TryCatch |
| messaging | 16 | Telegram, WhatsApp |
| office_automation | 12 | Excel, Word, Outlook |
| database | 10 | SQL connections and queries |
| error_handling | 9 | Retry, error recovery |
| email | 8 | SMTP/IMAP operations |
| rest_api | 7 | HTTP requests |
| ai_ml | 6 | LLM integrations |
| document | 5 | Document AI extraction |
| scripts | 5 | Python/JS/Batch execution |
| basic | 3 | Start, End, Comment |
| variable | 3 | Variable get/set/increment |
| subflows | 1 | Reusable workflow blocks |

## Visual Node Architecture

```
VisualNode (base_visual_node.py)
    |
    +-- Inherits from: NodeGraphQt.BaseNode
    |
    +-- Links to: CasareRPA BaseNode (_casare_node)
    |
    +-- Key Methods:
        +-- setup_ports() - Define exec/data ports
        +-- setup_widgets() - Custom UI widgets
        +-- _auto_create_widgets_from_schema() - Generate from @properties
        +-- set_collapsed() / toggle_collapse() - Show/hide non-essential widgets
        +-- update_status() - Visual execution feedback
```

## Registration Pattern

New visual nodes require:

1. Create node class in appropriate category directory
2. Add to `_VISUAL_NODE_REGISTRY` in `__init__.py`
3. Map to CasareRPA node in `graph/node_registry.py`

```python
# Example: Adding a new visual node
# 1. In category/nodes.py:
class VisualMyNewNode(VisualNode):
    __identifier__ = "casare_rpa"
    NODE_NAME = "My New Node"
    NODE_CATEGORY = "mycategory"

    def setup_ports(self):
        self.add_exec_input()
        self.add_exec_output()
        self.add_typed_input("input", DataType.STRING)
        self.add_typed_output("output", DataType.STRING)

# 2. In __init__.py _VISUAL_NODE_REGISTRY:
"VisualMyNewNode": "mycategory.nodes",

# 3. In graph/node_registry.py VISUAL_TO_CASARE_NODE_MAP:
VisualMyNewNode: MyNewNode,
```

## Related Indexes

- [nodes/_index.md](../../../../../nodes/_index.md) - CasareRPA node implementations (execution logic)
- [canvas/_index.md](../../_index.md) - Canvas presentation layer (coming soon)
- [domain/_index.md](../../../../../domain/_index.md) - Domain layer entities and types
