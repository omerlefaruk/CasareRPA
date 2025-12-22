# Node Reference

CasareRPA provides a large library of automation nodes organized into categories. Each node performs a specific, atomic operation that can be connected to build complex workflows.


## Node Categories

| Category | Count | Description |
|----------|-------|-------------|
| [Basic](basic.md) | 5 | Workflow entry/exit points, comments, logging |
| [Browser](browser.md) | 23+ | Web automation with Playwright |
| [Control Flow](control-flow.md) | 15+ | Conditionals, loops, error handling |
| [Data Operations](data-operations.md) | 40+ | String, list, dict, math operations |
| [File Operations](file-operations.md) | 20+ | Read/write files, CSV, JSON, ZIP |
| Desktop | 30+ | Windows UI automation |
| HTTP | 8+ | REST API requests |
| Email | 10+ | SMTP, IMAP email operations |
| Messaging | 15+ | Telegram, WhatsApp integration |
| Google | 50+ | Sheets, Drive, Gmail |
| System | 25+ | Clipboard, commands, dialogs |
| Script | 5+ | Python, JavaScript, batch scripts |
| PDF | 6+ | Read, merge, split PDFs |
| FTP | 10+ | FTP file transfers |
| Trigger | 20+ | Workflow triggers (webhook, schedule) |


## Node Anatomy

Every node in CasareRPA follows a consistent structure:

### Properties

Properties define the node's configuration. They appear in the property panel when a node is selected.

```
+---------------------------+
|     Node Properties       |
+---------------------------+
| URL: [https://example.com]|  <- STRING property
| Timeout: [30000]          |  <- INTEGER property
| Headless: [ ] No          |  <- BOOLEAN property
| Browser: [chromium v]     |  <- CHOICE property
+---------------------------+
```

### Ports

Ports define how data flows between nodes:

- **Execution Ports (white)**: Control flow connections
  - `exec_in`: Node receives execution
  - `exec_out`: Node passes execution to next node

- **Data Ports (colored by type)**: Data connections
  - Input ports: Receive data from other nodes
  - Output ports: Send data to other nodes

### Port Data Types

| Type | Color | Description |
|------|-------|-------------|
| EXEC | White | Execution flow |
| STRING | Green | Text data |
| INTEGER | Blue | Whole numbers |
| FLOAT | Cyan | Decimal numbers |
| BOOLEAN | Red | True/False |
| LIST | Yellow | Arrays/collections |
| ANY | Gray | Any data type |
| PAGE | Purple | Browser page |
| BROWSER | Orange | Browser instance |

## Property Types Reference

| Type | Widget | Description |
|------|--------|-------------|
| `STRING` | Text input | Single-line text |
| `TEXT` | Text area | Multi-line text |
| `INTEGER` | Number input | Whole numbers |
| `FLOAT` | Number input | Decimal numbers |
| `BOOLEAN` | Checkbox | True/False toggle |
| `CHOICE` | Dropdown | Select from options |
| `MULTI_CHOICE` | Multi-select | Select multiple options |
| `FILE_PATH` | File picker | Select a file |
| `DIRECTORY_PATH` | Folder picker | Select a directory |
| `SELECTOR` | Selector builder | CSS/XPath selector |
| `JSON` | Code editor | JSON structure |
| `CODE` | Code editor | Script code |
| `COLOR` | Color picker | Color selection |
| `DATE` | Date picker | Date selection |
| `TIME` | Time picker | Time selection |
| `DATETIME` | DateTime picker | Date and time |
| `LIST` | List editor | List of values |

## Variable Expressions

Properties support variable expressions using double curly braces:

```
{{variable_name}}
```

**Example:**
```
URL: https://example.com/{{user_id}}/profile
```

Variables are resolved from the execution context at runtime.

## Common Node Patterns

### Page Passthrough

Browser nodes typically pass the page through:

```
[LaunchBrowser] --page--> [GoToURL] --page--> [ClickElement]
```

### Data Output

Nodes output data to named ports:

```
[ReadCSV] --data--> [ForEachLoop]
          --headers-->
          --row_count-->
```

### Conditional Routing

Control flow nodes route execution:

```
[If] --true--> [ActionA]
     --false-> [ActionB]
```

## Error Handling

Nodes report success/failure in their result:

```python
# Success
{"success": True, "data": {...}, "next_nodes": ["exec_out"]}

# Failure
{"success": False, "error": "Error message", "next_nodes": []}
```

Use `TryNode`, `CatchNode`, and `FinallyNode` for structured error handling.

## Getting Started

1. **Start with basics**: Every workflow needs a `StartNode` and `EndNode`
2. **Add automation**: Choose nodes from the relevant category
3. **Connect ports**: Draw connections between compatible ports
4. **Configure properties**: Set node-specific options
5. **Test execution**: Run the workflow to verify behavior

## Quick Navigation

- [Basic Nodes](basic.md) - Start, End, Comment, Log
- [Browser Nodes](browser.md) - Web automation
- [Control Flow Nodes](control-flow.md) - Logic and loops
- [Data Operation Nodes](data-operations.md) - Data manipulation
- [File Operation Nodes](file-operations.md) - File I/O
