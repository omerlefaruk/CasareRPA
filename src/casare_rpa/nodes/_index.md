# Nodes Index

Quick reference for node implementations. Use for fast discovery.

## Categories

| Category | Path | Description |
|----------|------|-------------|
| browser | `nodes/browser/` | Web automation (Playwright) |
| desktop | `nodes/desktop_nodes/` | Windows UI automation |
| control_flow | `nodes/control_flow_nodes.py` | If/Switch/Loop/Wait |
| data | `nodes/data_nodes.py`, `nodes/data_operation_nodes.py` | Variables, transforms |
| data_operation | `nodes/data_operation/` | Dataset comparison, reconciliation |
| file | `nodes/file/` | File I/O, paths, structured data |
| email | `nodes/email/` | SMTP, IMAP |
| google | `nodes/google/` | Drive, Sheets, Docs, Gmail, Calendar |
| http | `nodes/http/` | REST API calls |
| database | `nodes/database/` | SQL operations |
| messaging | `nodes/messaging/` | Telegram, WhatsApp |
| llm | `nodes/llm/` | AI/LLM integrations |
| trigger | `nodes/trigger_nodes/` | Event triggers |
| system | `nodes/system/` | Dialog boxes, system ops |

## Key Files

| File | Contains |
|------|----------|
| `__init__.py` | _NODE_REGISTRY - all node mappings |
| `basic_nodes.py` | StartNode, EndNode, CommentNode |
| `control_flow_nodes.py` | IfNode, SwitchNode, ForLoopNode, WhileLoopNode |
| `browser_nodes.py` | ClickNode, TypeNode, NavigateNode, etc. |
| `browser/browser_base.py` | BrowserNode base class |
| `desktop_nodes/desktop_base.py` | DesktopNode base class |

## Registration

New nodes require:
1. `nodes/{category}/__init__.py` - Export class
2. `nodes/__init__.py` - Add to _NODE_REGISTRY
3. `workflow_loader.py` - Add to NODE_TYPE_MAP

## Common Patterns

```python
# Base class
from casare_rpa.nodes.browser.browser_base import BrowserNode

# Async execution
async def execute(self, context: ExecutionContext) -> dict:
    page = await context.get_page()
    # ... implementation
    return {"success": True, "result": value}
```

## Sample Workflows

Pre-built workflows in `/workflows/`:

| Workflow | Description | Nodes |
|----------|-------------|-------|
| `invoice_processing.json` | Monitor PDF inbox, OCR text, extract date/total, write CSV | FileWatch, ReadPDF, Regex, WriteCSV |
| `web_scraping_leads.json` | Login to CRM, scrape leads table, save JSON | Browser, Navigation, TableScraper, WriteJSON |
| `data_reconciliation.json` | Compare Excel datasets, report differences | ExcelOpen/GetRange, DataCompare, WriteJSON |
