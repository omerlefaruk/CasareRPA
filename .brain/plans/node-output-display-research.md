# Research: Node Output Value Display UI/UX

**Date**: 2025-12-08
**Topic**: Best practices for displaying node output values in visual programming environments

---

## 1. Competitor Analysis

### 1.1 n8n Approach

**How it works:**
- When clicking a node, a side panel opens showing **INPUT** and **OUTPUT** tabs
- Three view modes: **Table | JSON | Schema**
- Table view is default - rows=records, columns=attributes
- JSON view with syntax highlighting, expandable nested objects
- Schema view for quick structural overview
- **Data Pinning**: Can "pin" output data during development for testing

**Key UX Features:**
- Drag-and-drop data mapping from output to other node inputs
- Fast feedback loops - outputs appear immediately after execution
- Node hints can display dynamic messages post-execution
- 100 message limit in debug sidebar (performance optimization)
- Inline editing in JSON view

**Strengths:**
- Multiple view modes for different use cases
- Data pinning reduces repeated API calls
- Direct data mapping via drag-drop
- Real-time feedback during development

**Sources:**
- [n8n Node UI Design](https://docs.n8n.io/integrations/creating-nodes/plan/node-ui-design/)
- [n8n Data Mapping UI](https://docs.n8n.io/data/data-mapping/data-mapping-ui/)
- [n8n Data Pinning](https://docs.n8n.io/data/data-pinning/)

---

### 1.2 Unreal Engine Blueprints

**How it works:**
- **Watch Window**: Consolidated list of watched variables across Blueprints
- Values only show after node executes (no speculative preview)
- Arrays/Sets/Maps are expandable with drill-down
- Yellow border indicates currently paused node
- Red octagon breakpoint indicator on node corner

**Debug Features:**
- Step Over (F10), Step Into (F11), Step Out (Shift+F11)
- Breakpoints with visual indicators
- Call stack view
- Live variable updates when paused
- Third-party plugin adds live values in Actor details panel

**Strengths:**
- Clear visual indication of execution state
- Deep data structure inspection
- Consolidated watch window across multiple graphs
- Keyboard shortcuts for stepping

**Sources:**
- [Blueprint Debugger](https://dev.epicgames.com/documentation/en-us/unreal-engine/blueprint-debugger-in-unreal-engine)
- [Live Blueprint Variable Debugging Plugin](https://github.com/jlnordin/LiveBlueprintVariableDebugging)

---

### 1.3 Node-RED

**How it works:**
- **Debug Sidebar**: Dedicated sidebar panel for debug output
- Messages structured with expand/collapse for objects/arrays
- Color-coded: `node.warn()` = yellow, `node.error()` = red
- 100 message limit (hidden messages count toward limit)
- Can open in separate browser window

**Key Features:**
- Per-node debug toggle button in workspace
- Filtering by source node
- JSONata transform support for human-readable output
- Resizable sidebar
- Ctrl/Cmd-Space to show/hide

**Strengths:**
- Clean separation of debug output
- Easy toggle per-node
- Structured message display
- Separate window option for multi-monitor

**Sources:**
- [Node-RED Debug Sidebar](https://nodered.org/docs/user-guide/editor/sidebar/debug/)
- [Node-RED Debug Node](https://flowfuse.com/node-red/core-nodes/debug/)

---

### 1.4 Power Automate Desktop

**How it works:**
- **Run History**: Last 28 days of execution data
- Per-action logs with start time, subflow, action index
- "See inputs/outputs details" click to expand
- Progressive logging (V2) for real-time updates
- Secure inputs/outputs show `{}` only

**Limitations:**
- 32MB max action log (~50-80k entries)
- Designer-launched flows don't collect action logs
- Dataverse integration for detailed run data

**Strengths:**
- Historical run comparison
- Per-action granular logging
- Progressive real-time updates

**Sources:**
- [Power Automate Monitor Run Details](https://learn.microsoft.com/en-us/power-automate/desktop-flows/monitor-run-details)
- [Power Automate Run History](https://www.encodian.com/blog/power-automate-run-history-inputs-and-outputs/)

---

### 1.5 Blender Geometry/Shader Nodes

**How it works:**
- **Viewer Node**: Connect any socket to visualize in 3D viewport
- **Inline Value Display**: Single-value sockets show evaluated value directly in node editor
- Shift+Ctrl+LMB shortcut to connect to viewer
- Spreadsheet editor for tabular data inspection
- Third-party "Node Preview" add-on for shader thumbnails

**Key Features:**
- Values update interactively as parameters change
- Only scalar/small types shown inline (Float, Int, Bool, Vector)
- Complex types require Viewer node
- AOV rendering for batch preview

**Strengths:**
- Inline values reduce context switching
- Interactive updates
- Visual preview in 3D space
- Keyboard shortcuts for quick inspection

**Sources:**
- [Blender Viewer Node](https://docs.blender.org/manual/en/latest/modeling/geometry_nodes/output/viewer.html)
- [Blender Node Preview](https://superhivemarket.com/products/node-preview)

---

## 2. UI/UX Patterns Analysis

### 2.1 Inline Expansion vs Modal/Panel

| Approach | Pros | Cons |
|----------|------|------|
| **Inline Expansion** | No context switch, immediate visibility, compact | Limited space, clutters canvas, affects layout |
| **Side Panel** | More space, doesn't affect canvas, consistent location | Context switch, may obscure nodes |
| **Modal/Dialog** | Full screen real estate, focused inspection | Blocks workflow, heavy context switch |
| **Tooltip/Hover** | Quick glance, no click required | Disappears on mouse move, limited size |
| **Docked Panel** | Persistent, resizable, doesn't block canvas | Takes screen space, may be hidden |

**Recommendation for RPA**: **Side Panel with optional inline hints**
- Primary: Side panel for detailed inspection (like n8n)
- Secondary: Inline value hints for simple types (like Blender)

---

### 2.2 Tree View for Nested Data

**Best Practices:**
- Expand/collapse controls for all nested levels
- Show item count: `dict (5 items)`, `list (12 items)`
- Truncate long values with "..." and full tooltip
- Type indicators with colors or icons
- Copy-to-clipboard on individual values
- Search/filter within tree

**Qt/PySide6 Implementation:**
- Use `QTreeView` with custom model or `QTreeWidget`
- `expandToDepth(1)` for initial expand level
- `setAlternatingRowColors(True)` for readability
- Custom delegate for type-colored values

**Sources:**
- [Qt JSON Model Example](https://doc.qt.io/qtforpython-6/examples/example_widgets_itemviews_jsonmodel.html)
- [QJsonModel](https://github.com/dridk/QJsonModel)
- [qt-json-view](https://github.com/PaulSchweizer/qt-json-view)

---

### 2.3 JSON Viewer Features

**Essential:**
- Syntax highlighting (keys, strings, numbers, booleans, null)
- Expand/collapse all
- Line numbers
- Search within JSON
- Copy entire JSON or path

**Advanced:**
- Multiple modes: tree, form (edit), text, preview
- JSON Schema validation
- Path breadcrumb (e.g., `$.data[0].name`)
- Bidirectional navigation (tree <-> text)
- Large document handling (500MB+)

**Color Scheme (VSCode Dark):**
- Strings: `#CE9178` (orange)
- Numbers: `#B5CEA8` (green)
- Booleans: `#569CD6` (blue)
- Null: `#808080` (gray)
- Keys/Properties: `#9CDCFE` (light blue)

---

### 2.4 Tabular Display for Arrays

**When to use:** Arrays of objects with consistent structure

**Features:**
- Column headers from object keys
- Sortable columns
- Resizable columns
- Row selection for detail view
- Pagination for large arrays
- Export to CSV/Excel

**Implementation:**
- `QTableWidget` for simple cases
- `QTableView` + custom model for large datasets
- Virtual scrolling for performance

---

### 2.5 Type Indicators and Icons

| Type | Icon | Color | Example |
|------|------|-------|---------|
| String | `"abc"` or T | `#CE9178` | `"hello"` |
| Integer | `123` or # | `#B5CEA8` | `42` |
| Float | `1.0` or . | `#B5CEA8` | `3.14` |
| Boolean | `T/F` or checkbox | `#569CD6` | `true` |
| List | `[...]` | `#89D185` | `[1, 2, 3]` |
| Dict | `{...}` | `#DCDCAA` | `{"a": 1}` |
| Null | `null` or -- | `#808080` | `null` |
| Page/Element | Browser icon | `#C586C0` | `<Page>` |
| Error | X or ! | `#F44747` | `Exception` |

---

## 3. Interaction Patterns

### 3.1 Hover vs Click to Show

**Hover (Tooltip):**
- Use for: Quick preview of simple values
- Delay: 300-500ms to avoid flickering
- Auto-hide: On mouse leave
- Max size: ~200-300 chars
- No interactive elements (links, buttons)

**Click (Panel/Toggletip):**
- Use for: Complex data, interactive elements
- Stays open until dismissed
- Can contain: Copy button, expand/collapse, links
- Position: Near triggering element or side panel

**Hybrid Approach:**
- Hover shows preview
- Click pins the panel open
- Shift+Click opens in side panel

---

### 3.2 Expandable/Collapsible Sections

**Behavior:**
- Single-click to toggle
- Double-click to expand all children
- Arrow indicator (> or v)
- Remember state during session
- Expand to depth on initial load

**Animation:**
- Optional smooth animation (100-200ms)
- Disable animation in high-performance mode
- `QTreeView.setAnimated(True)` in Qt

---

### 3.3 Copy-to-Clipboard

**UI Patterns:**
- Icon button next to value
- Context menu "Copy Value"
- Keyboard shortcut (Ctrl+C on selection)
- "Copied!" feedback for 1-2 seconds

**Data Formatting:**
- Strings: Copy raw value
- Objects: Copy formatted JSON (`JSON.stringify(obj, null, 2)`)
- Arrays: Copy formatted JSON
- Path: Copy JSON path (e.g., `$.data[0].name`)

**Implementation:**
```python
from PySide6.QtWidgets import QApplication
clipboard = QApplication.clipboard()
clipboard.setText(formatted_text)
```

---

### 3.4 Search/Filter Within Large Outputs

**Features:**
- Search input with instant results
- Highlight matches in tree
- Show match count
- Navigate between matches (F3 / Shift+F3)
- Filter: Hide non-matching items

**Implementation:**
- Recursive item visibility toggle
- Store match indices for navigation
- Throttle search for performance (150-300ms debounce)

---

## 4. RPA-Specific Best Practices

### 4.1 Data Flow Between Nodes

**Visualization:**
- Wire color indicates data type (already implemented)
- Value preview on wire hover (optional)
- Data flow animation during execution (already implemented)
- Clear indication of which port produced value

**Implementation:**
- Store output values per-port in execution context
- Show port-level output in side panel
- Highlight wire when hovering output value

---

### 4.2 Debugging Workflow Execution

**Essential Features:**
1. **Step Controls**: Step Over, Step Into, Step Out, Continue
2. **Breakpoints**: Click to toggle, conditional breakpoints
3. **Variable Watch**: Track specific values
4. **Call Stack**: Show nested node execution
5. **Execution History**: Previous run values

**Value Timing:**
- Show "Not yet executed" for unexecuted nodes
- Show timestamp of when value was captured
- Diff view between runs

---

### 4.3 Variable Inspection During Development

**Current CasareRPA Debug Panel:**
- Already has Variables tab with tree view
- Search/filter capability
- Copy to clipboard via context menu
- Expand/collapse all buttons
- Refresh button

**Gaps to Address:**
- No inline value display on nodes
- No output panel when clicking node
- No data pinning feature
- No Table | JSON | Schema view toggle

---

## 5. Recommended Approach for CasareRPA

### 5.1 Top 5 UI Approaches (Ranked by PySide6 Suitability)

| Rank | Approach | Effort | UX Impact | Recommendation |
|------|----------|--------|-----------|----------------|
| 1 | **Node Output Panel** (n8n-style) | Medium | High | **Primary** |
| 2 | **Inline Value Hints** (Blender-style) | Low | Medium | Secondary |
| 3 | **Enhanced Tree View** | Low | Medium | Existing, enhance |
| 4 | **Wire Hover Preview** | Medium | Medium | Future |
| 5 | **Data Pinning** | Medium | Medium | Future |

---

### 5.2 Primary Recommendation: Node Output Panel

**Why:**
- Matches user expectations from n8n, Power Automate
- Provides adequate space for complex data
- Doesn't clutter canvas
- Can show both INPUT and OUTPUT
- Supports multiple view modes

**Implementation Plan:**

#### Phase 1: Basic Output Panel
1. Create `NodeOutputPanel` widget
2. Show on node selection (single node)
3. Display last execution output in tree view
4. Add to Side Panel dock as new tab

#### Phase 2: Multiple View Modes
1. Add view toggle: Table | JSON | Tree
2. Table view for array of objects
3. JSON view with syntax highlighting
4. Tree view (existing pattern)

#### Phase 3: Enhanced Features
1. Search within output
2. Copy individual values
3. Copy entire output as JSON
4. Data pinning for development

**Key UI Components:**

```
+------------------------------------------+
|  Node Output                      [x]    |
+------------------------------------------+
| [Input] [Output]                         |
+------------------------------------------+
| View: [Table] [JSON] [Tree]   [Search]   |
+------------------------------------------+
|  Name        | Value          | Type     |
|--------------|----------------|----------|
|  result      | "success"      | str      |
|  data        | {...}          | dict     |
|    > items   | [...] (5)      | list     |
|    > count   | 5              | int      |
+------------------------------------------+
| [Copy All] [Pin Data]        Last: 10:30 |
+------------------------------------------+
```

---

### 5.3 Secondary Recommendation: Inline Value Hints

**Why:**
- Quick glance without opening panel
- Works for simple scalar outputs
- Low implementation effort
- Blender-validated pattern

**Implementation:**
1. Add small value label below output port
2. Show only for executed nodes
3. Truncate to ~15 chars with tooltip for full value
4. Only for: str, int, float, bool (not complex types)
5. Toggle in View menu: "Show Inline Values"

**Visual:**
```
+--------------------+
|  Click Element     |
+--------------------+
| > exec_in          |
| selector: input    |
|                    |
| < exec_out         |
| < success: true    |  <- Inline hint
| < element_text     |
|     "Submit"       |  <- Truncated inline value
+--------------------+
```

---

### 5.4 Interaction Design Recommendations

1. **Single Click on Node**: Show output in side panel
2. **Double Click on Output Port**: Copy value to clipboard
3. **Hover on Output Port** (500ms): Show tooltip with value preview
4. **Right-Click on Output Port**: Context menu (Copy, Watch, Pin)
5. **Ctrl+Shift+O**: Toggle output panel visibility
6. **F12**: Jump to selected node's output in panel

---

### 5.5 Key UI Components Needed

| Component | Qt Class | Purpose |
|-----------|----------|---------|
| `NodeOutputPanel` | `QWidget` | Main container |
| `OutputTreeView` | `QTreeWidget` | Hierarchical data display |
| `OutputTableView` | `QTableWidget` | Array/tabular data |
| `JsonSyntaxHighlighter` | `QSyntaxHighlighter` | JSON highlighting |
| `ValueSearchWidget` | `QLineEdit` | Search within output |
| `ViewModeToggle` | `QButtonGroup` | Table/JSON/Tree toggle |
| `CopyButton` | `QPushButton` | Copy to clipboard |
| `PinDataButton` | `QPushButton` | Pin output data |

---

## 6. Implementation Priority

### Immediate (Phase 1)
1. Create `NodeOutputPanel` widget
2. Integrate with Side Panel dock
3. Show output on node selection
4. Basic tree view with expand/collapse

### Short-term (Phase 2)
1. Add Table view for arrays
2. Add JSON view with highlighting
3. Add search functionality
4. Port-level output display

### Medium-term (Phase 3)
1. Inline value hints on nodes
2. Data pinning feature
3. Wire hover preview
4. Input/Output tab split

### Long-term (Phase 4)
1. Execution history comparison
2. Value diff between runs
3. Export to file (JSON, CSV)
4. Watch expressions integration

---

## 7. Sources Summary

**n8n:**
- [Node UI Design](https://docs.n8n.io/integrations/creating-nodes/plan/node-ui-design/)
- [Data Mapping UI](https://docs.n8n.io/data/data-mapping/data-mapping-ui/)
- [Data Pinning](https://docs.n8n.io/data/data-pinning/)
- [Data Editing](https://docs.n8n.io/data/data-editing/)

**Unreal Engine:**
- [Blueprint Debugger](https://dev.epicgames.com/documentation/en-us/unreal-engine/blueprint-debugger-in-unreal-engine)
- [Blueprint Debugging Example](https://dev.epicgames.com/documentation/en-us/unreal-engine/blueprint-debugging-example-in-unreal-engine)

**Node-RED:**
- [Debug Sidebar](https://nodered.org/docs/user-guide/editor/sidebar/debug/)
- [Debug Node](https://flowfuse.com/node-red/core-nodes/debug/)

**Power Automate:**
- [Monitor Run Details](https://learn.microsoft.com/en-us/power-automate/desktop-flows/monitor-run-details)
- [Run History](https://www.encodian.com/blog/power-automate-run-history-inputs-and-outputs/)

**Blender:**
- [Viewer Node](https://docs.blender.org/manual/en/latest/modeling/geometry_nodes/output/viewer.html)
- [Node Preview Add-on](https://superhivemarket.com/products/node-preview)

**Qt/PySide6:**
- [JSON Model Example](https://doc.qt.io/qtforpython-6/examples/example_widgets_itemviews_jsonmodel.html)
- [QTreeView](https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QTreeView.html)
- [QJsonModel](https://github.com/dridk/QJsonModel)

**UX Design:**
- [Tooltip Guidelines](https://uxdworld.com/tooltip-guidelines/)
- [Designing Better Tooltips](https://blog.logrocket.com/ux-design/designing-better-tooltips-improved-ux/)
- [JSON Visualization Tools](https://blog.logrocket.com/visualize-json-data-popular-tools/)
