# Canvas UI Overhaul Plan

## Executive Summary

CasareRPA's Canvas IDE already has a solid foundation with VSCode Dark+ theming, NodeGraphQt integration, and comprehensive panel system. This overhaul focuses on **visual polish**, **consistency**, and **professional-grade UX** rather than architectural changes. Target: achieve visual parity with JetBrains IDEs and VS Code.

**Key Themes:**
1. Node visual refinement with better category differentiation
2. Connection/wire system enhancement
3. Panel modernization with better information density
4. Canvas interaction improvements
5. Accessibility and keyboard-first design

---

## Current State Analysis

### Technology Stack (Keep)
| Component | Technology | Status |
|-----------|-----------|--------|
| Framework | PySide6/Qt 6 | Solid |
| Node Graph | NodeGraphQt | Keep - well integrated |
| Theming | QSS + CanvasThemeColors dataclass | Good foundation |
| Custom Rendering | CasareNodeItem (QGraphicsItem) | Extensible |
| Connection Pipes | CasarePipe | Customized already |

### Existing Components Inventory

**Main Window Architecture:**
- `main_window.py` - Controller-based architecture, 3-tier loading (Critical/Normal/Deferred)
- Component managers: ActionManager, MenuBuilder, ToolbarBuilder, StatusBarManager, DockCreator
- Controller system for MVC separation

**Panel System:**
- `BottomPanelDock` - 6 tabs (Variables, Output, Log, Validation, History, Terminal)
- `PropertiesPanel` - CollapsibleSection pattern, robot override support
- `VariableInspectorDock` - Runtime variable monitoring
- `DebugPanel` - Call stack, watch expressions, breakpoints
- `ProcessMiningPanel`, `AnalyticsPanel`, `RobotPickerPanel`

**Node System:**
- `base_visual_node.py` - VisualNode base with typed ports, auto-widget generation
- `custom_node_item.py` - CasareNodeItem with custom painting, status indicators
- Category-based coloring in `node_icons.py`

**Canvas Features:**
- `Minimap` - Event-driven updates, viewport indicator
- `CommandPalette` - Fuzzy search, keyboard navigation
- `CasarePipe` - Dotted dragging, hover highlights, insert mode

### Identified Pain Points

**1. Node Design**
- Header color hardcoded maroon (#553245) - doesn't match category
- Icon system uses emoji fallbacks - unprofessional
- Port labels not visible on canvas
- Widget inputs inside nodes have poor contrast
- No visual grouping/frames support

**2. Connections/Wires**
- Data type labels overlap on dense graphs
- No animated flow direction indicator
- Connection preview could be smoother
- No "noodle" snap-to-port feedback

**3. Panels**
- Properties panel lacks schema-driven grouping
- CollapsibleSection styling inconsistent
- No keyboard shortcuts for tab switching
- Missing filter/search in Variables tab

**4. Toolbar/Menus**
- Toolbar icons are text-based fallbacks
- No contextual toolbar (changes based on selection)
- Quick actions bar missing

**5. Canvas**
- Grid not visible (or very faint)
- No smart guides for alignment
- Zoom controls only in status bar
- Background is flat - no subtle texture

**6. Accessibility**
- Some contrast ratios may not meet 4.5:1
- No screen reader support for nodes
- Missing focus indicators on some widgets

---

## Proposed Changes by Component

### 1. Node Design Overhaul

**Goal:** Professional, category-differentiated nodes like Unreal Blueprints or n8n

```
Current Node:                    Proposed Node:
+------------------+            +----[Browser]---------------+
| [maroon header]  |            | [Category-colored header]  |
|  Node Name       |    =>      |   Launch Browser      [ic] |
+------------------+            +----------------------------+
| [dark body]      |            | url: [input___________]   |
|  input widgets   |            | timeout: [30000        ]  |
+------------------+            +----------------------------+
| o exec_in        |            | o exec_in    exec_out o   |
|     exec_out o   |            | o url        browser o    |
|                  |            | o timeout    page    o    |
+------------------+            +----------------------------+
```

**Changes:**
- **Header matches category color** - Use `CATEGORY_COLORS` from `node_icons.py`
- **Category badge** - Small pill showing "Browser", "Desktop", etc.
- **Icon upgrade** - SVG icons instead of emoji (create icon set)
- **Port labels visible** - Show data type on hover, name always
- **Execution status badges** - Checkmark, error, running indicators already good
- **Execution time badge** - Already implemented, polish positioning

**Implementation:**
- Modify `CasareNodeItem._draw_text()` to use category color
- Create `assets/icons/` folder with SVG icons per category
- Add port label rendering in `CasareNodeItem.paint()`
- Update `_apply_category_colors()` in `base_visual_node.py`

### 2. Connection/Wire System Enhancement

**Goal:** Clear data flow visualization with type awareness

**Current:**
- Solid colored lines based on data type
- Dotted when dragging
- Insert highlight (orange) when node dragged over

**Proposed:**
- **Animated flow pulses** - Subtle dots moving along exec wires during execution
- **Type-colored gradients** - Gradient from source to target type if compatible
- **Thickness variation** - Exec wires thicker (3px), data wires thinner (2px)
- **Hover tooltip** - Show connected port names and current value
- **Bezier curve refinement** - Smoother curves, avoid sharp bends

**Implementation:**
- Enhance `CasarePipe.paint()` with animated QPen dash offset
- Add gradient brush for heterogeneous type connections
- Create `ConnectionTooltip` widget for hover data

### 3. Panel Redesign

#### 3.1 Properties Panel Modernization

**Current:** Simple collapsible sections with basic input widgets

**Proposed:**
```
+--[Properties]------------------+
| Launch Browser            [x] |
| Type: VisualLaunchBrowserNode |
| ID: abc123...                 |
+-------------------------------+
| [v] Connection                |
|     Profile: [Default_____|v] |
|     Headless: [ ] Off         |
+-------------------------------+
| [v] Configuration             |
|     URL:     [https://...__]  |
|     Timeout: [30000____] ms   |
+-------------------------------+
| [v] Advanced                  |
|     Viewport: [1920]x[1080]   |
|     User Agent: [____________]|
+-------------------------------+
| [v] Target Robot              |
|     Mode: [Local________|v]   |
+-------------------------------+
```

**Changes:**
- **Tab-based grouping** - From `@node_schema` decorator's `tab` field
- **Inline validation** - Red border + message for invalid values
- **Smart defaults** - Show placeholder with default value
- **Quick actions** - Copy config, reset to defaults buttons
- **Rich inputs** - File picker for paths, color picker for colors

#### 3.2 Bottom Panel Enhancement

**Current:** 6 tabs with basic table/log views

**Proposed:**
- **Tab keyboard shortcuts** - Alt+1 for Variables, Alt+2 for Output, etc.
- **Filter/Search bar** - In Variables and Log tabs
- **Badge refinement** - Error count in red, warning in yellow
- **Sticky headers** - In log view for timestamp grouping
- **Export buttons** - Export log/history to file

#### 3.3 Node Palette Panel (NEW)

**Currently missing dedicated panel - uses menu**

**Proposed:**
```
+--[Nodes]----------------------+
| [Search nodes...        ] [x] |
+-------------------------------+
| [v] Browser                   |
|     Launch Browser            |
|     Close Browser             |
|     Go To URL                 |
|     ...                       |
| [v] Desktop                   |
|     Launch Application        |
|     ...                       |
| [>] Control Flow              |
| [>] Data Operations           |
| [>] File Operations           |
+-------------------------------+
| [Recent]                      |
|   Click Element               |
|   Type Text                   |
+-------------------------------+
```

**Features:**
- Searchable tree with fuzzy match
- Drag-and-drop to canvas
- Recent/favorites section
- Icon preview per node

### 4. Toolbar/Menu Redesign

**Current:** Single MainToolbar with file/edit/run actions

**Proposed Layout:**
```
+--[File]--[Edit]--[View]--[Run]--[Automation]--[Help]----------------+
| [New][Open][Save] | [Undo][Redo] | [Run][Pause][Stop] | [Mode: v] |
+--------------------------------------------------------------------+
```

**Contextual Toolbar (NEW):**
Appears when node(s) selected:
```
+--[Node Actions]------------------+
| [Disable][Enable] [Delete] [Cut] [Copy] | [Run Single] [Run To Here] |
+----------------------------------+
```

**Changes:**
- **SVG icons** - Replace text-based icons with proper SVG
- **Icon-only mode** - Toggle text labels off for compact view
- **Contextual toolbar** - Floating toolbar near selection
- **Separator styling** - More visible separators between groups

### 5. Canvas Improvements

#### 5.1 Grid and Background

**Current:** Solid dark background (#1E1E1E), no visible grid

**Proposed:**
- **Subtle dot grid** - Light dots at 20px intervals, opacity 0.1
- **Major grid lines** - At 100px, opacity 0.05
- **Background texture** - Subtle noise or gradient
- **Snap indicators** - Highlight grid when snapping

#### 5.2 Zoom Controls

**Current:** Status bar zoom display + mouse wheel

**Proposed:**
- **Floating zoom control** - Bottom-right corner
  ```
  [ - ] [100%] [ + ] [Fit]
  ```
- **Zoom presets** - 25%, 50%, 100%, 150%, 200%
- **Fit to selection** - Button and shortcut (Ctrl+Shift+F)

#### 5.3 Minimap Enhancement

**Current:** Bottom-left overlay, viewport rectangle

**Proposed:**
- **Resizable** - Drag corner to resize
- **Node colors** - Match actual node category colors
- **Execution highlight** - Show running node pulse
- **Collapse option** - Minimize to icon when not needed

#### 5.4 Smart Guides (NEW)

**Proposed:**
- **Alignment guides** - Blue lines when aligning with other nodes
- **Equal spacing** - Purple guides for equidistant placement
- **Snap feedback** - Subtle haptic-style animation on snap

### 6. Visual Node Group/Frames (NEW)

**Not currently implemented**

**Proposed:**
```
+--[Frame: Authentication Flow]------------------------------+
| Color: Blue   Collapse: [ ]                                |
|                                                            |
|   +------------+     +------------+     +------------+     |
|   | Login Page |---->| Type User  |---->| Type Pass  |     |
|   +------------+     +------------+     +------------+     |
|                                                            |
+------------------------------------------------------------+
```

**Features:**
- Collapsible groups
- Custom label and color
- Auto-resize to fit contents
- Comment/documentation field

---

## Implementation Phases

### Phase 1: Foundation Polish (Week 1-2)

**Priority: Critical visual improvements**

| Task | File(s) | Effort |
|------|---------|--------|
| Category-colored node headers | `custom_node_item.py`, `base_visual_node.py` | 1d |
| SVG icon system | New `assets/icons/`, `node_icons.py` | 2d |
| Port label rendering | `custom_node_item.py` | 1d |
| Grid background | `theme.py`, custom QGraphicsScene | 1d |
| Connection wire thickness | `custom_pipe.py` | 0.5d |

**Deliverable:** Nodes look professional, clear visual hierarchy

### Phase 2: Panel Enhancements (Week 3-4)

| Task | File(s) | Effort |
|------|---------|--------|
| Properties panel tab grouping | `properties_panel.py` | 2d |
| Node Palette panel | New `node_palette_panel.py` | 3d |
| Bottom panel keyboard shortcuts | `bottom_panel_dock.py` | 0.5d |
| Filter/search in Variables | `variables_tab.py` | 1d |
| Tab badges refinement | `bottom_panel_dock.py` | 0.5d |

**Deliverable:** Panels are power-user friendly

### Phase 3: Canvas Interactions (Week 5-6)

| Task | File(s) | Effort |
|------|---------|--------|
| Floating zoom controls | New `zoom_controls.py` | 1d |
| Smart alignment guides | New `alignment_guides.py` | 2d |
| Minimap enhancements | `minimap.py` | 1d |
| Connection animation (exec flow) | `custom_pipe.py` | 2d |
| Contextual toolbar | New `contextual_toolbar.py` | 2d |

**Deliverable:** Canvas interactions feel polished

### Phase 4: Advanced Features (Week 7-8)

| Task | File(s) | Effort |
|------|---------|--------|
| Node Groups/Frames | New `node_group.py`, `visual_frame.py` | 3d |
| Toolbar SVG icons | `main_toolbar.py`, `icons.py` | 1d |
| Accessibility audit | Multiple files | 2d |
| Performance optimization | Profile + optimize | 2d |

**Deliverable:** Feature-complete, accessible UI

---

## Technology Recommendations

### Keep NodeGraphQt
- Already deeply integrated
- Customization via CasareNodeItem works well
- Performance is adequate (viewport culling implemented)

### Styling Approach: Hybrid
- **QSS** for standard Qt widgets (buttons, inputs, panels)
- **Code-based** for canvas elements (nodes, connections)
- **Theme dataclass** (`CanvasThemeColors`) as single source of truth

### Icon Strategy
- Create SVG icon set (24x24 base size)
- Use `QIcon.fromTheme()` fallback
- Cache pixmaps in `_icon_pixmap_cache`

### Performance Considerations
- Use `AnimationCoordinator` pattern (already exists) for any new animations
- Batch updates for multi-node selection
- Event-driven updates over polling where possible

---

## Open Questions

1. **Node Palette Placement** - Left dock (like VS Code) or right dock (like UiPath)?
   - Recommendation: Left dock, below menu bar

2. **Frame/Group Feature** - Is this high priority for users?
   - Recommendation: Phase 4, implement after core polish

3. **Icon Style** - Outlined or filled? Mono or color?
   - Recommendation: Filled, monochrome with category accent color

4. **Toolbar Density** - Icon-only or icon+text?
   - Recommendation: Icon+text default, icon-only option in preferences

5. **Dark Theme Only?** - Should light theme be supported?
   - Recommendation: Dark only for v1, simplifies maintenance

6. **Wire Animation** - During execution only or always?
   - Recommendation: Execution only, with preference toggle

---

## Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Visual consistency (subjective) | 6/10 | 9/10 |
| Node readability | Basic | Excellent |
| Keyboard coverage | 70% | 95% |
| Panel information density | Medium | High |
| Accessibility compliance | Unknown | WCAG AA |

---

## File Locations Reference

```
src/casare_rpa/presentation/canvas/
|-- main_window.py              # MainWindow controller
|-- theme.py                    # CanvasThemeColors, get_canvas_stylesheet()
|-- graph/
|   |-- custom_node_item.py     # CasareNodeItem (node rendering)
|   |-- custom_pipe.py          # CasarePipe (connection rendering)
|   |-- minimap.py              # Minimap widget
|   |-- node_icons.py           # Icon generation, category colors
|   |-- node_registry.py        # Visual node registration
|-- ui/
|   |-- panels/
|   |   |-- properties_panel.py # Properties panel
|   |   |-- bottom_panel_dock.py # Bottom panel tabs
|   |   |-- variables_tab.py    # Variables tab
|   |-- toolbars/
|   |   |-- main_toolbar.py     # Main toolbar
|   |-- icons.py                # Icon utilities
|-- visual_nodes/
|   |-- base_visual_node.py     # VisualNode base class
|   |-- browser/nodes.py        # Browser visual nodes
|   |-- (other categories)
|-- search/
|   |-- command_palette.py      # Command palette
|-- components/
|   |-- dock_creator.py         # Dock widget factory
```

---

*Plan created: 2024-12-04*
*Author: UI Designer Agent*
*Status: DRAFT - Awaiting Review*
