# Node UI/UX Overhaul Plan

**Created:** 2025-12-06
**Status:** Planning Phase
**Owner:** UI/UX Designer

---

## 1. Current State Analysis

### 1.1 Architecture Overview

The node UI is built on **NodeGraphQt** with extensive customization:

```
┌─────────────────────────────────────────────────────────────┐
│                    VISUAL LAYER                             │
├─────────────────────────────────────────────────────────────┤
│  VisualNode (base_visual_node.py)                          │
│    └── Extends NodeGraphQt.BaseNode                        │
│    └── Links to CasareBaseNode (domain layer)              │
│    └── Auto-creates widgets from @node_schema              │
│                                                             │
│  CasareNodeItem (custom_node_item.py)                      │
│    └── Custom QPainter rendering                           │
│    └── Status indicators (running, success, error)         │
│    └── Execution time badge                                │
│    └── Collapse/expand button                              │
│    └── LOD rendering at <30% zoom                          │
├─────────────────────────────────────────────────────────────┤
│                    WIDGET LAYER                             │
├─────────────────────────────────────────────────────────────┤
│  node_widgets.py                                           │
│    └── NodeFilePathWidget, NodeDirectoryPathWidget         │
│    └── NodeSelectorWidget (element picker)                 │
│    └── VariableAwareLineEdit integration                   │
│                                                             │
│  variable_picker.py                                        │
│    └── VariableButton ({x} button)                         │
│    └── VariablePickerPopup (dropdown with search)          │
│    └── Fuzzy matching, type badges, value preview          │
├─────────────────────────────────────────────────────────────┤
│                    PORT LAYER                               │
├─────────────────────────────────────────────────────────────┤
│  port_shapes.py                                            │
│    └── Shape-per-type for accessibility                    │
│    └── Circle, Diamond, Square, Hexagon, Triangle          │
│                                                             │
│  custom_pipe.py (CasarePipe)                               │
│    └── Dotted line when dragging                           │
│    └── Data type labels on connections                     │
│    └── Hover preview of output values                      │
│    └── Insert highlight for node insertion                 │
├─────────────────────────────────────────────────────────────┤
│                    ICON LAYER                               │
├─────────────────────────────────────────────────────────────┤
│  node_icons.py                                             │
│    └── Unicode emoji-based icons                           │
│    └── Category color scheme (VSCode syntax colors)        │
│    └── Dual cache (QPixmap + file path)                    │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Current Node Appearance

```
┌────────────────────────────────────────────┐
│ ┌─────────────────────────────────────┬──┐ │
│ │     ● Node Name                     │-+│ │  <- Header (maroon #552D32)
│ └─────────────────────────────────────┴──┘ │     with collapse button
├────────────────────────────────────────────┤
│  ○ exec_in          ▶                      │  <- Exec ports (triangles)
│                                            │
│  ● selector         ○ page                 │  <- Data ports (various shapes)
│  ┌──────────────────────────────────┬──┐   │
│  │ #my-button                       │..│   │  <- Widget with picker
│  └──────────────────────────────────┴──┘   │
│                                            │
│  ● timeout                                 │
│  ┌──────────────────────────────────┬──┐   │
│  │ 30000                            │{x}│  │  <- Variable-aware input
│  └──────────────────────────────────┴──┘   │
│                                            │
│            ▶ exec_out                      │
└────────────────────────────────────────────┘
     │
     │ 42ms  <- Execution time badge (above node when completed)
```

### 1.3 Identified Pain Points

| Category | Issue | Severity |
|----------|-------|----------|
| **Visual Hierarchy** | Header color (maroon) doesn't match category semantics | Medium |
| **Visual Hierarchy** | Node icons (emojis) inconsistent across platforms | Medium |
| **Visual Hierarchy** | Collapse button in header competes with node name | Low |
| **Port Design** | Port labels can overlap with long names | High |
| **Port Design** | No visual feedback during connection compatibility check | Medium |
| **Port Design** | Port tooltips missing detailed type info | Low |
| **Status Indicators** | Success checkmark overlaps with collapse button area | Medium |
| **Status Indicators** | No visual indicator for disabled/skipped nodes | High |
| **Property Editing** | Variable picker popup can extend off-screen | Medium |
| **Property Editing** | No inline validation feedback for invalid values | High |
| **Property Editing** | Tab navigation between widgets not implemented | Medium |
| **Canvas Interactions** | Multi-select doesn't show combined bounding box | Low |
| **Canvas Interactions** | No keyboard shortcuts for common node operations | Medium |
| **Accessibility** | Port shapes help colorblind users, but need legend | Low |
| **Accessibility** | Some contrast ratios below 4.5:1 | Medium |

### 1.4 Current Color Scheme

**Theme Colors (VSCode Dark+):**
```
Background:    #1E1E1E (canvas), #252526 (node body)
Header:        #552D32 (maroon) - NOT category-aware
Border:        #444444 (normal), #FFD700 (selected/running)
Text:          #D4D4D4 (primary), #808080 (secondary)
Accent:        #007ACC (blue), #4CAF50 (success), #F44336 (error)
```

**Category Colors (from node_icons.py):**
```
basic:              #569CD6 (keyword blue)
browser:            #C586C0 (control flow purple)
navigation:         #4EC9B0 (type teal)
interaction:        #CE9178 (string orange)
data:               #89D185 (success green)
control_flow:       #F48771 (error red)
desktop_automation: #C586C0 (purple)
triggers:           #9C27B0 (material purple)
ai_ml:              #00BCD4 (cyan)
```

---

## 2. Competitor/Inspiration Research

### 2.1 UiPath Studio

**Strengths:**
- Clear activity icons with consistent style (not emojis)
- Category color strips on left edge of activities
- Inline validation with red underlines
- Collapsible sections within properties panel
- Quick actions on hover (delete, disable, comment)

**Applicable Ideas:**
- Left-edge category indicator strip
- Inline validation indicators
- Hover quick actions

### 2.2 n8n

**Strengths:**
- Clean, minimal node design
- Status dot in corner (running/success/error)
- Connection labels showing data flow
- Consistent iconography (custom SVG icons)
- Graceful handling of many connections

**Applicable Ideas:**
- Smaller, cleaner status indicators
- Connection data preview on hover

### 2.3 Node-RED

**Strengths:**
- Color-coded by node type (input=pink, output=green, function=yellow)
- Status indicators below node name
- Compact design with fewer distractions
- Config nodes shown with dashed borders

**Applicable Ideas:**
- Node-type coloring for quick identification
- Dashed border for special node types (triggers, subflows)

### 2.4 Unreal Engine Blueprints

**Strengths:**
- Clear execution flow (white triangle pins)
- Data flow with type-colored wires
- Compact/expanded node states
- Pin tooltips with type and description
- Reroute nodes for wire organization

**Applicable Ideas:**
- Reroute nodes for clean wire paths
- Detailed pin tooltips
- Clear visual distinction between exec and data pins

### 2.5 Blender Geometry Nodes

**Strengths:**
- Socket shapes indicate type (circle, diamond, triangle)
- Wire noodles with bezier curves
- Group nodes with custom colors
- Muted (disabled) nodes clearly grayed out

**Applicable Ideas:**
- Socket shapes (ALREADY IMPLEMENTED via port_shapes.py)
- Muted/disabled visual state

---

## 3. Proposed Improvements

### 3.1 Node Appearance

#### 3.1.1 Category-Aware Header ✅ DECIDED

**Current:** All nodes have maroon (#552D32) header.

**Decision:** Semi-transparent category color header

```
┌────────────────────────────────────────────┐
│ ● Click Element                       [−] │  <- Entire header tinted
└────────────────────────────────────────────┘     with category color
```

**Implementation:**
- Header background = category color at 40% opacity
- Keep text white for contrast
- Add subtle gradient for depth

```python
# In custom_node_item.py _draw_text()
category_color = CATEGORY_COLORS.get(self._category, default)
header_color = QColor(category_color)
header_color.setAlpha(100)  # 40% opacity
# Gradient from header_color to slightly darker
gradient = QLinearGradient(0, 0, 0, header_height)
gradient.setColorAt(0, header_color)
gradient.setColorAt(1, header_color.darker(120))
```

#### 3.1.2 Custom SVG Icons (Replace Emojis) ✅ DECIDED

**Current:** Unicode emojis rendered via QPainter.

**Problem:** Emojis render inconsistently across Windows versions.

**Decision:** Custom **multi-color** SVG icon set for distinctiveness.

```
assets/
└── icons/
    └── nodes/
        ├── click.svg        # Orange pointer + element
        ├── type.svg         # Blue keyboard
        ├── navigate.svg     # Teal compass/arrow
        ├── browser.svg      # Purple browser window
        ├── loop.svg         # Green circular arrows
        ├── condition.svg    # Yellow diamond/branch
        ├── data.svg         # Green database
        ├── ai.svg           # Cyan brain/chip
        └── ...
```

**Implementation:**
- Create ~40 multi-color SVG icons
- Each icon uses 2-3 colors max for clarity
- Use QSvgRenderer for crisp rendering at any zoom
- Fallback to category-colored circle for unknown nodes
- Icons should be 24x24 base size, scalable

#### 3.1.3 Improved Status Indicators

**Current:** 20px circle in top-right corner.

**Proposed:** Smaller, corner-hugging indicators:

```
┌───────────────────────────────────────┬─●─┐
│                                       │ ┊ │  <- 12px indicator
│  Node Content                         │ ┊ │     in corner gap
│                                       │ ┊ │
└───────────────────────────────────────┴───┘

States:
  ● Idle:      No indicator
  ◐ Running:   Pulsing blue dot with ring animation
  ✓ Success:   Green checkmark (smaller)
  ✗ Error:     Red X icon
  ⊘ Disabled:  Gray diagonal slash overlay
  ⏭ Skipped:   Gray arrow (fast-forward)
```

**Implementation:**
- Move status to top-right corner, outside collapse button
- Add disabled/skipped states (currently missing)
- Use CSS animation for running state pulse

#### 3.1.4 Collapse Button Redesign

**Current:** +/- button in header, can conflict with status.

**Proposed:** Chevron on left side of header:

```
┌────────────────────────────────────────────┐
│ ▶ Click Element                       ●    │  <- Chevron left, status right
└────────────────────────────────────────────┘

Expanded:
│ ▼ Click Element                       ●    │
```

**Implementation:**
- Move collapse toggle to left of node name
- Use ▶ (collapsed) / ▼ (expanded) chevrons
- Larger click target (16x16 + 4px padding)

### 3.2 Port Design

#### 3.2.1 Port Labels with Truncation

**Current:** Labels can extend beyond node width.

**Proposed:** Truncate long labels with ellipsis, show full on hover:

```
Input:   ● selector_for_el...  ← Truncated at 15 chars
Hover:   Shows tooltip "selector_for_element_to_click"
```

**Implementation:**
- Calculate max label width based on node width
- Use QFontMetrics.elidedText() for truncation
- Show full label in tooltip

#### 3.2.2 Connection Compatibility Feedback

**Current:** No visual feedback when dragging incompatible connection.

**Proposed:** Visual feedback during drag:

```
Compatible:   Target port glows green
Incompatible: Target port shows red X overlay
              Connection wire turns red/dashed
```

**Implementation:**
- In CasarePipe, check type compatibility during drag
- If incompatible, change wire color to #F44336 (red)
- Add glow effect to compatible target ports

#### 3.2.3 Port Tooltips Enhancement

**Current:** Basic port name only.

**Proposed:** Rich tooltips with type info and description:

```
┌──────────────────────────────────┐
│ selector                         │
│ Type: STRING                     │
│ Description: CSS or XPath        │
│ selector for target element      │
│                                  │
│ Accepts: STRING, ANY             │
└──────────────────────────────────┘
```

**Implementation:**
- Get port description from PropertyDef.tooltip
- Show compatible types
- Use QToolTip with HTML formatting

### 3.3 Status Indicators

#### 3.3.1 Add Missing States

**Current states:** idle, running, success, error
**Missing states:** disabled, skipped, warning

**Proposed visual treatment:**

| State | Border | Background | Overlay |
|-------|--------|------------|---------|
| idle | #444444 | #252526 | None |
| running | #FFD700 animated | #252526 | None |
| success | #444444 | #252526 | Green check (corner) |
| error | #F44336 | #252526 | Red X (corner) |
| disabled | #444444 | #252526 50% | Diagonal gray lines |
| skipped | #444444 | #252526 | Gray fast-forward |
| warning | #FF9800 | #252526 | Yellow triangle |

#### 3.3.2 Execution Progress ✅ DECIDED

**Current:** Only shows final execution time after completion.

**Decision:** Progress bar for nodes that support it + elapsed time.

```
Running state (with progress):
┌─────────────────────────────────────────┐
│ Download File                    ◐      │
├─────────────────────────────────────────┤
│ [████████░░░░░░░░░░░░]  45%  12.5s      │  <- Progress + time
└─────────────────────────────────────────┘

Running state (without progress):
┌─────────────────────────────────────────┐
│ Click Element                    ◐      │
├─────────────────────────────────────────┤
│ ○○○○○  5.2s                             │  <- Indeterminate + time
└─────────────────────────────────────────┘
```

**Implementation:**
- Add `ProgressMixin` for nodes that support progress reporting
- Progress bar shows when node calls `self.set_progress(0.0-1.0)`
- Indeterminate animation (dots) for nodes without progress
- Always show elapsed time counter
- Nodes to add progress: ForEachLoop, Download, DataTransform, AI nodes

### 3.4 Property Editing UX

#### 3.4.1 Inline Validation Feedback

**Current:** Validation errors only shown at execution time.

**Proposed:** Real-time validation with visual feedback:

```
Valid:     ┌──────────────────────────┐
           │ 30000                    │
           └──────────────────────────┘

Invalid:   ┌──────────────────────────┐
           │ -5                       │  <- Red border
           └──────────────────────────┘
           ⚠ Value must be >= 0

Warning:   ┌──────────────────────────┐
           │ #nonexistent-id          │  <- Orange border
           └──────────────────────────┘
           ⚠ Selector not found in page
```

**Implementation:**
- Add validation method to PropertyDef
- Run validation on editingFinished signal
- Show error icon + message below widget

#### 3.4.2 Variable Picker Improvements

**Current issues:**
- Popup can extend off-screen
- No keyboard-only workflow

**Proposed improvements:**
- Smart positioning (flip up if near screen bottom)
- Tab to accept first suggestion
- Inline autocomplete after `{{`

#### 3.4.3 Tab Navigation

**Current:** No tab navigation between widgets.

**Proposed:** Tab moves between widgets within node:

```
Tab order:
  1. selector input
  2. timeout input
  3. retry_count input
  ...

Shift+Tab: Reverse order
Enter in last widget: Focus next node in execution order
```

**Implementation:**
- Set Qt.FocusPolicy.TabFocus on all input widgets
- Define explicit tab order in node

### 3.5 Canvas Interactions

#### 3.5.1 Selection Improvements

**Current:** Individual yellow borders on selected nodes.

**Proposed:** Multi-select bounding box + individual highlights:

```
┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐
│ ┌─────────────┐  ┌─────────────┐ │
│ │  Node A     │  │  Node B     │ │  <- Blue dashed bounding box
│ └─────────────┘  └─────────────┘ │     around selection group
│                                   │
│        ┌─────────────┐           │
│        │  Node C     │           │
│        └─────────────┘           │
└ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘
```

#### 3.5.2 Quick Actions Toolbar

**Current:** Right-click context menu only.

**Proposed:** Floating toolbar on hover:

```
           ┌─────────────────────────────────┐
           │ 🗑 📋 ⬜ 💬 ⚙                    │  <- Toolbar above node
           └─────────────────────────────────┘
           ┌─────────────────────────────────┐
           │                                 │
           │        Node Content             │
           │                                 │
           └─────────────────────────────────┘

Icons:
  🗑 Delete node
  📋 Duplicate node
  ⬜ Disable/Enable toggle
  💬 Add comment
  ⚙  Open properties panel
```

**Implementation:**
- Show on node hover after 500ms delay
- Position above node
- Hide on mouse leave or action

#### 3.5.3 Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Delete/Backspace | Delete selected nodes |
| Ctrl+D | Duplicate selection |
| Ctrl+G | Group selection into frame |
| Ctrl+E | Toggle node enable/disable |
| F2 | Rename node |
| Ctrl+Enter | Execute from selected node |
| Space | Pan canvas (drag mode) |
| Tab | Select next connected node |
| Shift+Tab | Select previous connected node |

### 3.6 Connection Lines (Pipes)

#### 3.6.1 Current State

```
Current features (custom_pipe.py):
- Dotted line when dragging
- Data type labels at midpoint
- Output value preview on hover
- Insert highlight (orange) when node dragged over
- Hover highlight (cyan)
- LOD rendering at <30% zoom (straight lines)
```

#### 3.6.2 Type-Colored Wires

**Current:** All connections use same color (with label showing type).

**Proposed:** Wire color matches data type (like Unreal Blueprints):

```
┌───────────┐                    ┌───────────┐
│  Node A   │═══════════════════▶│  Node B   │  <- White = Execution
│           │────────────────────│           │  <- Blue = String
│           │════════════════════│           │  <- Green = List
│           │────────────────────│           │  <- Orange = Object
└───────────┘                    └───────────┘
```

**Color Scheme:**
| Data Type | Color | Hex |
|-----------|-------|-----|
| Execution | White | #FFFFFF |
| String | Light Blue | #569CD6 |
| Integer | Teal | #4EC9B0 |
| Boolean | Red | #F48771 |
| List/Array | Green | #89D185 |
| Dict/Object | Orange | #CE9178 |
| Page/Element | Purple | #C586C0 |
| Any | Gray | #808080 |

**Implementation:**
```python
# In custom_pipe.py
TYPE_COLORS = {
    DataType.EXEC: QColor("#FFFFFF"),
    DataType.STRING: QColor("#569CD6"),
    DataType.INTEGER: QColor("#4EC9B0"),
    DataType.BOOLEAN: QColor("#F48771"),
    DataType.LIST: QColor("#89D185"),
    DataType.DICT: QColor("#CE9178"),
    DataType.PAGE: QColor("#C586C0"),
    DataType.ANY: QColor("#808080"),
}

def _get_wire_color(self) -> QColor:
    if self.output_port:
        data_type = self._get_port_data_type()
        return TYPE_COLORS.get(data_type, TYPE_COLORS[DataType.ANY])
    return self.color
```

#### 3.6.3 Execution Flow Animation ✅ DECIDED

**Current:** No animation showing data flow.

**Decision:** **Continuous** animation during execution (not just on transition).

```
Idle:       ────────────────────────
Executing:  ─●──────────────────────  (dot loops continuously)
            ────●───────────────────
            ────────●───────────────
            ────────────●───────────
            ─●────────────────────── (loops back)
Completed:  ════════════════════════  (brief glow, then stop)
```

**Implementation:**
- QPainterPath animation using `pointAtPercent(t)`
- Small glowing dot travels from source to target **continuously**
- Loop duration: ~500ms per cycle
- Only animate wires connected to currently executing node
- Stop animation + brief glow on node completion

```python
class AnimatedPipe(CasarePipe):
    def __init__(self):
        super().__init__()
        self._animation_progress = 0.0  # 0.0 to 1.0
        self._is_animating = False

    def start_flow_animation(self):
        self._is_animating = True
        # Use QPropertyAnimation or manual timer

    def _draw_flow_dot(self, painter: QPainter):
        if not self._is_animating:
            return
        pos = self.path().pointAtPercent(self._animation_progress)
        painter.setBrush(QBrush(QColor(255, 255, 255, 200)))
        painter.drawEllipse(pos, 4, 4)
```

#### 3.6.4 Reroute Nodes ✅ DECIDED

**Current:** No way to organize complex wire paths.

**Decision:** Alt+LMB on wire to insert reroute point.

```
Before:
┌───────────┐                              ┌───────────┐
│  Node A   │──────────────────────────────│  Node B   │
└───────────┘        ╲                     └───────────┘
                      ╲
                       ╲───────────────────┌───────────┐
                                           │  Node C   │
                                           └───────────┘

After (with reroute):
┌───────────┐           ┌───────────┐
│  Node A   │───────────│  Node B   │
└───────────┘           └───────────┘
        │
        ◆ <- Reroute node (Alt+LMB on wire to add)
        │
        └───────────────┌───────────┐
                        │  Node C   │
                        └───────────┘
```

**Features:**
- **Alt+LMB** on wire to insert reroute point
- Drag reroute point to reposition
- Delete key removes reroute point
- Multiple reroute points per wire allowed
- Reroute points are small diamonds (◆)

**Implementation:**
- Create `RerouteNode` as minimal node with single in/out port
- Store reroute positions in connection metadata
- Auto-remove reroute when wire deleted

#### 3.6.5 Connection Bundling ✅ DECIDED

**Current:** Many parallel wires create visual clutter.

**Decision:** Bundle at **3+ wires** between same node pairs.

```
Before (cluttered):
┌───────────┐    ───────────────    ┌───────────┐
│  Node A   │    ───────────────    │  Node B   │
│           │    ───────────────    │           │
│           │    ───────────────    │           │
└───────────┘    ───────────────    └───────────┘

After (bundled):
┌───────────┐                       ┌───────────┐
│  Node A   │═══════[3]═════════════│  Node B   │
│           │                       │           │
└───────────┘                       └───────────┘
         Bundle indicator shows "3 connections"
         Hover to expand and see individual wires
```

**Implementation:**
- Bundle threshold: 3+ connections between same source/target
- Render as thick bundled wire with count badge
- Hover expands to show individual connections
- Click badge to select all bundled connections

#### 3.6.6 Wire Thickness by Data Type

**Current:** All wires same thickness.

**Proposed:** Visual hierarchy through thickness:

| Wire Type | Thickness | Purpose |
|-----------|-----------|---------|
| Execution | 3px | Primary flow, most prominent |
| Data (active) | 2px | Data that was actually used |
| Data (idle) | 1.5px | Default data connections |
| Optional | 1px dashed | Optional/nullable connections |

#### 3.6.7 Smart Wire Routing ✅ DECIDED

**Current:** Basic bezier curves.

**Decision:** Keep **curved bezier** style, add smart routing to avoid overlaps.

```
Bad (current):                Good (smart bezier routing):
┌─────┐   ┌─────┐             ┌─────┐   ┌─────┐
│  A  │───│  B  │─────┐       │  A  │───│  B  │
└─────┘   └─────┘     │       └─────┘   └─────┘
     ┌─────┐          │            │
     │  C  │──────────┤       ┌────╰────╮
     └─────┘          │       │         │
          ┌───────────┘       │    ┌─────┐
          ▼                   │    │  C  │──╮
     ┌─────┐                  │    └─────┘  │
     │  D  │                  ╰─────────────╯
     └─────┘                        │
                              ┌─────╰─────┐
                              │     D     │
                              └───────────┘
```

**Implementation:**
- Keep curved bezier as primary style (no orthogonal)
- Path finding to avoid node bounding boxes
- Adjust bezier control points to route around obstacles
- Manual reroute nodes (Alt+LMB) for fine control

### 3.7 Subflows (Composite Nodes) ✅ DECIDED

**Decision:** Implement subflows for reusable, composable workflows.

```
Subflow Node (collapsed):
┌─────────────────────────────────────────┐
│ ⎔ Login Sequence                   [▶]  │  <- ⎔ icon = subflow
├─────────────────────────────────────────┤
│ ● username           ● success          │
│ ● password           ● session_token    │
│                      ▶ exec_out         │
│ ▶ exec_in                               │
└─────────────────────────────────────────┘
  [▶] = Double-click or button to expand/edit

Subflow Node (expanded in-place):
┌─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─┐
│  Login Sequence                    [−]  │  <- Dashed border
│ ┌───────────┐    ┌───────────┐         │
│ │ Navigate  │───▶│ Type User │───▶...  │
│ └───────────┘    └───────────┘         │
└ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘
```

**Features:**
- **Create:** Select nodes → Right-click → "Create Subflow"
- **Edit:** Double-click to expand in-place or open in new tab
- **Inputs/Outputs:** Auto-detected from unconnected ports, or manually defined
- **Reuse:** Drag from "My Subflows" palette, or copy/paste
- **Versioning:** Subflows stored as separate .json files, versionable
- **Nesting:** Subflows can contain other subflows (max depth: 3)

**Visual Distinction:**
- Dashed border when expanded
- ⎔ icon in header (or custom icon per subflow)
- Different header color tint (suggestion: blue-gray)
- Badge showing "3 nodes" count when collapsed

**Implementation:**
```
src/casare_rpa/
├── domain/
│   └── entities/
│       └── subflow.py          # Subflow entity
├── application/
│   └── use_cases/
│       └── subflow_executor.py # Execute subflow as unit
├── presentation/
│   └── canvas/
│       └── visual_nodes/
│           └── subflow_node.py # Visual representation
```

**File Format:**
```json
{
  "id": "subflow_login_sequence",
  "name": "Login Sequence",
  "version": "1.0.0",
  "inputs": [
    {"name": "username", "type": "STRING"},
    {"name": "password", "type": "STRING"}
  ],
  "outputs": [
    {"name": "success", "type": "BOOLEAN"},
    {"name": "session_token", "type": "STRING"}
  ],
  "nodes": [...],
  "connections": [...]
}
```

### 3.7 Accessibility Improvements

#### 3.7.1 Port Shape Legend ✅ DECIDED

**Decision:** Auto-hide overlay with per-node pinning option.

```
Default (auto-hide):
┌────────────────────────────────────────────────────────┐
│  Canvas                     ┌─────────────────┐        │
│                             │ PORT LEGEND [📌]│ ← Pin  │
│    [nodes...]               │ ▶ Execution     │  button│
│                             │ ● String        │        │
│                             │ ◇ Boolean       │        │
│                             │ ■ List          │        │
│                             └─────────────────┘        │
└────────────────────────────────────────────────────────┘
  Shows on: F1 key, hover on "?" button, or first-time user
  Hides after: 5s idle or click elsewhere

Pinned (per-session):
  - Click 📌 to keep visible
  - Draggable to any position
  - Remembers position per session
```

**Implementation:**
- Auto-show on F1 or "?" button in toolbar
- 5 second auto-hide timer (reset on hover)
- Pin button toggles persistent mode
- Store pinned position in session state
- First-time users: auto-show for 10s with "Pin to keep visible" hint

#### 3.7.2 Contrast Ratio Fixes

**Current issues:**
- Secondary text (#808080) on dark backgrounds: 4.0:1
- Some port labels below 4.5:1

**Proposed fixes:**
- Increase secondary text to #AAAAAA (5.5:1)
- Port labels to #D4D4D4 (10:1)

#### 3.7.3 Screen Reader Support

- Add accessibility labels to all interactive elements
- Announce node selection changes
- Describe connection creation/deletion

---

## 4. Implementation Priority

### 4.1 Quick Wins (1-2 hours each)

| Task | Impact | Effort |
|------|--------|--------|
| Add disabled/skipped status states | High | Low |
| Fix contrast ratios for accessibility | Medium | Low |
| Port label truncation with tooltip | Medium | Low |
| Category-aware left edge strip | Medium | Low |
| Keyboard shortcuts (Delete, Ctrl+D) | High | Low |

### 4.2 Medium Effort (1-2 days each)

| Task | Impact | Effort |
|------|--------|--------|
| Inline validation feedback | High | Medium |
| Variable picker positioning fix | Medium | Medium |
| Connection compatibility feedback | High | Medium |
| **Type-colored wires** | **High** | **Medium** |
| **Wire thickness by type** | **Medium** | **Low** |
| Collapse button redesign | Low | Medium |
| Tab navigation between widgets | Medium | Medium |
| Quick actions toolbar | Medium | Medium |

### 4.3 Major Changes (1+ weeks)

| Task | Impact | Effort |
|------|--------|--------|
| **Subflows system** | **High** | **Very High** |
| **Execution flow animation** | **High** | **Medium** |
| **Reroute nodes** | **Medium** | **High** |
| **Smart wire routing** | **Medium** | **Very High** |
| **Connection bundling** | **Low** | **High** |
| Custom SVG icon set (40+ icons) | High | High |
| Category-aware header theming | Medium | Medium |
| Execution progress indicator | Medium | High |
| Multi-select bounding box | Low | Medium |
| Screen reader accessibility | Medium | High |
| Port shape legend panel | Low | Medium |

### 4.4 Recommended Implementation Order

**Phase 1: Foundation (Week 1)**
1. Add disabled/skipped status states
2. Fix contrast ratios
3. Port label truncation
4. Basic keyboard shortcuts

**Phase 2: Visual Polish (Week 2)**
5. Category-aware header colors
6. Collapse button redesign
7. Status indicator relocation
8. Connection compatibility feedback
9. **Type-colored wires**
10. **Wire thickness by type**

**Phase 3: Editing UX (Week 3)**
11. Inline validation feedback
12. Variable picker positioning
13. Tab navigation
14. Quick actions toolbar

**Phase 4: Icons & Accessibility (Week 4)**
15. Custom SVG icon set (subset)
16. Port shape legend
17. Screen reader labels

**Phase 5: Connection Lines (Week 5)**
18. **Execution flow animation**
19. **Reroute nodes**

**Phase 6: Subflows (Week 6-7)**
20. Subflow domain entity and file format
21. Subflow executor (execution as unit)
22. Subflow visual node (collapsed view)
23. Create subflow from selection
24. Subflow palette and reuse
25. In-place expansion editing

**Phase 7: Advanced (Future)**
26. Smart wire routing (bezier pathfinding)
27. Connection bundling (3+ threshold)

---

## 5. Design Decisions (Resolved)

| Question | Decision | Rationale |
|----------|----------|-----------|
| **Icon Style** | Multi-color | More distinctive, helps quick identification |
| **Category Header** | Semi-transparent category color | More colorful, easier category spotting at a glance |
| **Quick Actions** | Hover (500ms delay) | Faster access than right-click |
| **Execution Progress** | Progress bar for supported nodes | Richer feedback for long operations |
| **Port Legend** | Auto-hide + per-node pin option | On-demand by default, pinnable for learning |
| **Tab Navigation** | Within single node | Logical grouping, predictable behavior |
| **Disabled Connections** | Grayed out | Shows flow structure while indicating inactive |
| **Grouping System** | Implement subflows | Needed for reusable, composable workflows |
| **Wire Routing Style** | Curved bezier | Smoother visual flow, familiar from other tools |
| **Flow Animation** | Continuous during execution | Clear feedback of active execution |
| **Bundling Threshold** | 3+ wires | Balance between cleanliness and visibility |
| **Reroute Interaction** | Alt+LMB on wire | Double-click reserved for other actions |

---

## 6. Technical Notes

### 6.1 NodeGraphQt Limitations

- Cannot easily change port positions (always left/right)
- Limited control over connection routing
- No built-in support for bezier reroute nodes
- Port rendering is handled internally, harder to customize

### 6.2 Performance Considerations

- LOD rendering at <30% zoom already implemented
- Icon caching via `_icon_pixmap_cache` and `_icon_path_cache`
- AnimationCoordinator centralizes running animations
- Any new features should respect these optimizations

### 6.3 Qt/QSS Constraints

- QGraphicsProxyWidget has z-order issues with popups (already fixed for combos)
- Complex animations should use QPainter, not QPropertyAnimation
- Custom painting should use cached QColor/QFont/QPen objects

---

*Last Updated: 2025-12-06 (Added Connection Lines section)*
