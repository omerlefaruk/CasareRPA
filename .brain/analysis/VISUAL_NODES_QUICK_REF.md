# Visual Nodes Quick Reference

**Fast lookup for visual node status and patterns.**

---

## Coverage at a Glance

```
Total Logic Nodes:      435
Total Visual Nodes:     424
UI-Only Nodes:           3 (Comment, Reroute, Subflow)
Coverage:             97.5%

Missing Visual Wrappers: 11 nodes across 5 categories
```

---

## Missing Visual Nodes (11 Total)

### Category: AI/LLM Advanced
- `PromptTemplateNode`
- `ListTemplatesNode`
- `GetTemplateInfoNode`
- `EmbeddingNode`
- `RAGNode`
- `VectorSearchNode`
- `VectorStoreAddNode`
- `VectorStoreDeleteNode`

**Status:** Enterprise AI features, not yet prioritized
**Priority:** HIGH (3 prompt, 5 RAG)

### Category: Control Flow
- `ForkNode` - Parallel fork
- `JoinNode` - Parallel join
- `ParallelForEachNode` - Parallel iteration

**Status:** Complex layout logic needed
**Priority:** MEDIUM

### Category: Utility/Logging
- `LogNode` - Simple logging
- `ValidateNode` - Data validation
- `TransformNode` - Generic transform

**Status:** Low-priority utility
**Priority:** LOW

### Category: Google Services
- `GmailAddLabelNode`
- `GmailGetLabelsNode`
- `GmailRemoveLabelNode`
- `GmailTrashEmailNode`
- `DriveRemovePermissionNode`
- `DocsAppendTextNode`
- `DocsApplyStyleNode`
- `DocsExportNode`
- `DocsGetTextNode`

**Status:** Feature refinement nodes
**Priority:** MEDIUM

### Category: Desktop Automation
- `DesktopClickElementNode`
- `DesktopTypeTextNode`

**Status:** Unclear if needed (potential duplicates)
**Priority:** LOW (investigate)

---

## Directory Structure (21 Categories)

```
visual_nodes/
├── ai_ml/               (10 nodes)      LLM, AI agents
├── basic/               (3 nodes)       Start, End, Comment
├── browser/             (26 nodes)      Web automation
├── control_flow/        (16 nodes)      If/Loop/TryCatch
├── database/            (10 nodes)      SQL operations
├── data_operations/     (33 nodes)      String/Math/List/Dict
├── desktop_automation/  (36 nodes)      Windows automation
├── document/            (5 nodes)       Document AI
├── email/               (8 nodes)       Email operations
├── error_handling/      (9 nodes)       Retry/Error recovery
├── file_operations/     (42 nodes)      File I/O + Super Nodes
├── google/              (79 nodes)      Gmail/Sheets/Drive/Docs/Calendar
├── messaging/           (16 nodes)      Telegram/WhatsApp
├── mixins/              (--)            Super Node mixin
├── office_automation/   (12 nodes)      Excel/Word/Outlook
├── rest_api/            (7 nodes)       HTTP requests
├── scripts/             (5 nodes)       Python/Batch/JS
├── subflows/            (1 node)        Subflow execution
├── system/              (67 nodes)      Dialogs/Clipboard/Services
├── text/                (13 nodes)      Text operations
├── triggers/            (17 nodes)      Event-based triggers
├── utility/             (28 nodes)      Random/DateTime/Reroute
├── variable/            (3 nodes)       Get/Set/Increment
└── workflow/            (1 node)        Workflow execution
```

---

## Super Nodes (3 Total)

### FileSystemSuperNode
- **Location:** `file_operations/super_nodes.py`
- **Actions:** 12 (Read/Write/Append File, Delete, Copy, Move, Exists, Size, Info, CreateDir, ListFiles, ListDir)
- **Replaces:** 12 atomic nodes
- **Pattern:** Action dropdown → Dynamic ports

### StructuredDataSuperNode
- **Location:** `file_operations/super_nodes.py`
- **Actions:** 7 (Read/Write CSV, Read/Write JSON, Zip/Unzip, ImageConvert)
- **Replaces:** 7 atomic nodes
- **Pattern:** Action dropdown → Dynamic ports

### TextSuperNode
- **Location:** `text/super_nodes.py`
- **Actions:** Planned consolidation
- **Status:** Implementation in progress

### SuperNodeMixin
- **Location:** `mixins/super_node_mixin.py`
- **Provides:** Dynamic port management, conditional visibility
- **Used By:** All Super Nodes

---

## Implementation Template

### Standard Visual Node
```python
"""Visual nodes for [category]."""

from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode


class Visual[NodeName]Node(VisualNode):
    """Visual representation of [NodeName]Node."""

    __identifier__ = "casare_rpa.[category]"
    NODE_NAME = "[Display Name]"
    NODE_CATEGORY = "[category]/[subcategory]"

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("param", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("result", DataType.STRING)
```

### Super Node
```python
class Visual[Name]SuperNode(SuperNodeMixin, VisualNode):
    """Super node with dynamic ports based on action."""

    __identifier__ = "casare_rpa.[category]"
    NODE_NAME = "[Name] (Super)"
    NODE_CATEGORY = "[category]"

    # SuperNodeMixin handles dynamic ports via schema
```

---

## Registry Updates Checklist

When adding new visual nodes:

1. **Create class** in `category/nodes.py` (or `category/file.py` for split files)

2. **Add to** `visual_nodes/__init__.py`:
   ```python
   _VISUAL_NODE_REGISTRY: Dict[str, str] = {
       "VisualNewNode": "category.nodes",
   }
   ```

3. **Add to** `nodes/registry_data.py`:
   ```python
   NODE_REGISTRY: Dict[str, Union[str, Tuple[str, str]]] = {
       "NewNode": "category.module",
   }
   ```

4. **No entry needed** in `graph/node_registry.py` - auto-discovery handles it

---

## Category Details

### Largest Categories
| Category | Nodes | Files | Lines |
|----------|-------|-------|-------|
| Google | 79 | 5 split files | ~1500 |
| System | 67 | 1 file | 1226 |
| File Operations | 42 | 2 files (with super) | ~800 |
| Data Operations | 33 | 1 file | 751 |
| Desktop | 36 | 2 files (with super) | ~900 |

### Most Organized
- **Browser** (26 nodes, 1 file, 705 lines) - Clean single file
- **Google** (79 nodes, 5 files) - Split by service, maintainable
- **Data Operations** (33 nodes, 1 file, 751 lines) - Well-grouped

### Candidates for Splitting
- **System** (67 nodes, 1 file, 1226 lines)
  - Could split: dialogs/, processes/, services/, media/
- **Google** (already split well)

---

## Pattern Consistency Score

| Aspect | Score | Notes |
|--------|-------|-------|
| Class Attributes | 100% | All have `__identifier__`, `NODE_NAME`, `NODE_CATEGORY` |
| Port Naming | 98% | Consistent exec/data port patterns |
| Widget Generation | 95% | Auto-generated via `@properties` (preferred) |
| Type System | 99% | Strong DataType usage |
| Documentation | 90% | Good docstrings, some gaps in complex nodes |

---

## Port Naming Convention

```
Execution Ports:
  Input:  exec_in, exec_input
  Output: exec_out, exec_output

Data Ports (typed):
  Input:  param, input, data, selector, url, text, etc.
  Output: result, output, data, page, browser, success, etc.

Boolean Flags:
  exists, success, found, valid, enabled, etc.

Collections:
  items (singular collection)
  items_list, rows, pages (plural collection)
```

---

## DataType Enum (Common Types)

```python
# Primitive types
DataType.STRING
DataType.INTEGER
DataType.FLOAT
DataType.BOOLEAN

# Collections
DataType.LIST
DataType.DICT
DataType.ARRAY
DataType.TABLE

# Domain types
DataType.BROWSER
DataType.PAGE
DataType.SPREADSHEET
DataType.FILE
DataType.DIRECTORY
DataType.IMAGE

# Special
DataType.DYNAMIC    # Any type
DataType.OBJECT     # Generic object
```

---

## Deprecated & Issues

### Deprecation Status
- **Total Deprecated:** 1 (minimal, healthy)
- **Dead Code:** 0 detected
- **Unused Nodes:** 0 detected

### Known Issues
1. **Loop Duplication:** Both `VisualForLoopNode` and `VisualForLoopStartNode` exist
   - **Status:** Intentional design (composite vs structured)

2. **Google Path Split:** Registry references `"google"` but files split by service
   - **Status:** Works fine, just documentational
   - **Fix:** Update registry comments or docs

3. **Subflow Redundancy:** Both `subflows/` and `workflow/` for subflow execution
   - **Status:** Unclear if intentional
   - **Action:** Investigate consolidation

---

## Performance Notes

### Lazy Loading
- **Essential Nodes:** 8 loaded at startup
- **Deferred Nodes:** 416 loaded on-demand
- **Benefit:** Startup time ~1.5s vs 5s (with all nodes)

### Caching
- **Node Mapping Cache:** `~/.casare_rpa/cache/node_mapping_cache.json`
- **Invalidation:** When registry hash changes
- **Benefit:** Fast node factory operations

---

## File Organization Patterns

### Standard Single-File Category
```
category/
├── __init__.py
└── nodes.py (all classes)
```
Examples: basic, browser, database, email, etc.

### Split by Service (Google)
```
google/
├── __init__.py
├── calendar_nodes.py (12)
├── docs_nodes.py (8)
├── drive_nodes.py (17)
├── gmail_nodes.py (21)
└── sheets_nodes.py (21)
```

### Split by Type (Messaging)
```
messaging/
├── __init__.py
├── nodes.py (base sending)
├── telegram_action_nodes.py (Telegram-specific)
└── whatsapp_nodes.py (WhatsApp-specific)
```

### With Super Nodes
```
category/
├── __init__.py
├── nodes.py (regular nodes)
└── super_nodes.py (dynamic nodes)
```
Examples: file_operations, desktop_automation, text

---

## Quick Statistics

```
Total Categories:           21
Total Visual Node Files:    ~50+ .py files
Total Visual Nodes:         424
Average Nodes/Category:     20
Largest File:              1226 lines (system/nodes.py)
Smallest File:             ~20 lines (basic/nodes.py)

Code Reuse (Super Nodes):  19 consolidated into 3
Token Savings:             ~2% (consolidated 7→2 CSV/JSON)
```

---

## Next Steps for Contributors

1. **Adding a Node:** Use template above, follow checklist in main report
2. **Splitting Large Category:** See System (1226 lines) as candidate
3. **Consolidating Nodes:** Use Super Node pattern (see FileSystem example)
4. **Investigating Gaps:** Start with RAG nodes (highest priority)

---

## Related Documentation

- **Full Report:** `VISUAL_NODES_REPORT.md` (comprehensive analysis)
- **Base Class:** `base_visual_node.py` (VisualNode documentation)
- **Super Node Pattern:** `.brain/docs/super-node-pattern.md`
- **Node Rules:** `agent-rules/rules/03-nodes.md`
- **Registration:** `nodes/registry_data.py` (logic node registry)
