# UI/UX and Canvas Experience Improvements Research

**Date**: 2025-12-11
**Researcher**: Technical Research Specialist
**Focus**: Canvas interactions, node grouping, minimap, zoom, shortcuts, themes, accessibility

---

## Executive Summary

CasareRPA has a solid foundation with NodeGraphQt and PySide6, but significant opportunities exist to match modern workflow editor standards set by UiPath Studio, Power Automate Desktop, n8n, and Node-RED. This research identifies 32 specific improvements across 7 categories with implementation priorities.

---

## 1. Current State Analysis

### Existing Canvas Features (CasareRPA)

| Feature | Status | Implementation |
|---------|--------|----------------|
| Minimap | Implemented | `graph/minimap.py` - 200x140px, click-to-navigate, event-driven updates |
| Node Frames/Groups | Implemented | `graph/node_frame.py` - Collapsible, colored, serializable |
| Zoom Controls | Partial | Smooth zoom via `viewport_controller.py`, 0.1-2.0x range |
| Keyboard Shortcuts | Extensive | 40+ shortcuts via `action_manager.py` |
| Theme System | Comprehensive | `ui/theme.py` - Dark theme only, 1866 lines |
| GPU Acceleration | Enabled | OpenGL 3.3, 4x MSAA via `node_graph_widget.py` |
| Wire Bundling | Implemented | `connections/wire_bundler.py` |
| Smart Routing | Implemented | `connections/smart_routing.py` |
| Auto-Connect | Implemented | `connections/auto_connect.py` |
| Viewport Culling | Implemented | `graph/viewport_culling.py` |
| LOD Manager | Implemented | `graph/lod_manager.py` |
| Breadcrumb Navigation | Implemented | Subflow dive in/out (V/C keys) |

### Key Files (278 total in presentation/canvas)
- **Core Canvas**: `graph/node_graph_widget.py` (2.4K+ lines)
- **Theming**: `ui/theme.py` (1866 lines - comprehensive)
- **Actions**: `components/action_manager.py` (40+ shortcuts)
- **Viewport**: `controllers/viewport_controller.py` (smooth zoom)
- **Frames**: `graph/node_frame.py` (grouping, collapse)
- **Minimap**: `graph/minimap.py` (event-driven)

---

## 2. Competitor Analysis

### UiPath Studio 2024

| Feature | UiPath Implementation | CasareRPA Gap |
|---------|----------------------|---------------|
| Infinite Canvas | Canvas expands as workflow grows | No auto-expand |
| Declutter Canvas | Auto-arranges overlapping nodes | No auto-layout |
| Snap-to-Grid | Alignment assistance | No snap grid |
| Flow Decision Visual | Redesigned decision/switch nodes | Standard nodes |
| Contextual AI Suggestions | AI suggests next activities | Basic AI assist |
| Simplified Ribbon | Collapsible toolbar | Fixed toolbar |
| Breakpoint Annotations | Visual markers on all node types | Limited markers |
| Code Selection Expand | Ctrl+Shift+Num+/- for syntax selection | Not applicable |

**Key Shortcuts (UiPath)**:
- Ctrl+T: Wrap in Try/Catch
- Ctrl+K: Auto-create variable
- F10/F11: Step Over/Into
- Alt+Left/Right: Navigate history

### Power Automate Desktop 2024

| Feature | PAD Implementation | CasareRPA Gap |
|---------|-------------------|---------------|
| Dark Mode | Now available (Dec 2024) | Already have |
| AI Toolbox Panel | Dedicated AI section | In assistant panel |
| UI Element Collections | Reusable selector modules | Per-workflow only |
| Image Fallback | Screenshot-based element finding | OCR separate |
| Copilot Repair | AI-suggested selector fixes | Manual only |
| Connector Library | 350+ cloud connectors tab | Node library only |
| Schema v2 | Enhanced element sharing | N/A |

### n8n Workflow Editor

| Feature | n8n Implementation | CasareRPA Gap |
|---------|-------------------|---------------|
| Node Library Sidebar | Left panel with search | Tab menu only |
| Table/JSON/Schema Views | Multiple data views | Output popup only |
| Ask Assistant Button | Always-visible AI help | Panel-based |
| Node Display Notes | Notes shown under nodes | Properties only |
| Version Control | Built-in versioning | File-based |
| Cluster Nodes | AI node groups | Subflows |
| 350+ Integrations | Native connectors | 250+ nodes |

### Node-RED

| Feature | Node-RED Implementation | CasareRPA Gap |
|---------|------------------------|---------------|
| View Navigator | Scaled-down workflow view | Minimap exists |
| Alignment Shortcuts | Alt+A L/R/C/T/M/B/V/H | No alignment |
| Group Ctrl+Shift+G | Quick grouping | Manual frame |
| Zoom Memory | Restore zoom on reload | No persistence |
| Scroll Memory | Restore position on reload | No persistence |
| Flow Groups | First-class grouping | Frame-based |

---

## 3. Modern Workflow Editor Best Practices

### Canvas Interaction Patterns (Figma/n8n/Node-RED)

1. **Infinite Canvas** - Auto-expand boundaries
2. **Snap-to-Grid** - Optional alignment assistance
3. **Auto-Layout/Declutter** - Automatic arrangement
4. **Selection Lasso** - Rectangle + free-form selection
5. **Multi-select Alignment** - Distribute/align selected
6. **Connection Preview** - Show compatible ports while dragging
7. **Quick Insert** - Tab/space for rapid node creation
8. **Smart Duplication** - Alt+drag or Ctrl+D with offset

### Accessibility Standards (WCAG 2.1)

| Requirement | Standard | CasareRPA Status |
|-------------|----------|------------------|
| Color Contrast (Graphics) | 3:1 minimum | Mostly compliant |
| Color Contrast (Text) | 4.5:1 minimum | Compliant |
| Keyboard Navigation | Full keyboard access | Partial |
| Screen Reader Support | ARIA labels | Not implemented |
| Focus Indicators | Visible focus state | Partial |
| Color Independence | Don't rely on color alone | Some gaps |
| Reduced Motion | prefers-reduced-motion | Not checked |

---

## 4. Recommendations

### Priority 1: High Impact, Medium Effort

#### 4.1 Auto-Layout / Declutter Canvas
**Gap**: Users must manually arrange nodes
**Solution**: Implement layout algorithms (Dagre/ELK)
**Benefit**: Cleaner workflows, matches UiPath's "Declutter Canvas"

```
Implementation: presentation/canvas/graph/auto_layout.py
- Use Dagre.js algorithm (port to Python or use PyGraphviz)
- Horizontal/Vertical layout options
- Preserve relative positions where possible
- Undo support required
```

#### 4.2 Snap-to-Grid with Visual Guidelines
**Gap**: No alignment assistance
**Solution**: Optional snap grid + alignment guides
**Benefit**: Professional-looking workflows

```
Implementation: presentation/canvas/graph/snap_grid.py
- Toggle via View menu (Ctrl+Shift+G)
- Show guidelines when dragging near alignment
- 50px default grid size, configurable
- Smart snapping to nearby nodes
```

#### 4.3 Node Alignment Toolbar
**Gap**: No quick alignment tools
**Solution**: Alignment buttons + shortcuts
**Benefit**: Matches Node-RED's Alt+A shortcuts

```
Shortcuts:
- Alt+A L: Align Left
- Alt+A R: Align Right
- Alt+A T: Align Top
- Alt+A B: Align Bottom
- Alt+A H: Distribute Horizontally
- Alt+A V: Distribute Vertically
- Alt+A C: Align Center (horizontal)
- Alt+A M: Align Middle (vertical)
```

#### 4.4 Viewport State Persistence
**Gap**: Zoom/scroll lost on reload
**Solution**: Save/restore view state
**Benefit**: Matches Node-RED, improves UX

```
Implementation: controllers/viewport_controller.py
- Store in workflow JSON: zoom_level, center_x, center_y
- Restore on workflow load
- Option in preferences to enable/disable
```

### Priority 2: Medium Impact, Medium Effort

#### 4.5 Connection Preview on Drag
**Gap**: No visual hint of valid connections
**Solution**: Highlight compatible ports during drag
**Benefit**: Reduces connection errors, modern UX

```
Implementation: connections/connection_preview.py
- On drag start: scan all visible ports
- Highlight compatible ports (green glow)
- Dim incompatible ports (gray out)
- Use existing port type validation
```

#### 4.6 Quick Node Panel (Sidebar)
**Gap**: Tab menu only, no persistent browser
**Solution**: Left-side node library panel
**Benefit**: Matches n8n/UiPath pattern

```
Implementation: ui/panels/node_library_panel.py
- Collapsible left dock
- Categorized tree view
- Search/filter at top
- Drag-and-drop to canvas
- Recently used section
```

#### 4.7 Node Notes Display
**Gap**: Notes only in properties panel
**Solution**: Optional note display under nodes
**Benefit**: Better workflow documentation

```
Implementation: graph/custom_node_item.py
- Add "Display Note" toggle in node context menu
- Render note text below node body
- Truncate with "..." for long notes
- Yellow/beige background like sticky notes
```

#### 4.8 Selection Statistics Bar
**Gap**: No info about current selection
**Solution**: Status bar shows selection details
**Benefit**: Quick feedback during editing

```
Implementation: components/status_bar_manager.py
- "3 nodes selected" or "Frame: Loop Group"
- Show combined execution time for selected
- Quick actions: "Disable All", "Enable All"
```

### Priority 3: Medium Impact, Low Effort

#### 4.9 Keyboard Shortcut Enhancements

| New Shortcut | Action | Rationale |
|--------------|--------|-----------|
| Ctrl+T | Wrap selection in Try/Catch | UiPath standard |
| Ctrl+Shift+G | Create group/frame | Node-RED standard |
| Ctrl+0 | Reset zoom to 100% | Universal standard |
| Ctrl+- / Ctrl+= | Zoom out/in | Universal standard |
| Space (hold) | Pan mode | Figma/design tool standard |
| Shift+Scroll | Horizontal scroll | Modern editor standard |
| Home | Jump to Start node | Workflow navigation |
| End | Jump to End node | Workflow navigation |

#### 4.10 Zoom Percentage Display
**Gap**: Zoom level not visible
**Solution**: Show zoom % in status bar
**Benefit**: User awareness of view state

```
Already partial implementation in viewport_controller.py
Need: Add clickable zoom indicator to status bar
- Click to open zoom preset menu (50%, 75%, 100%, 150%, 200%)
- Ctrl+click to reset to 100%
```

#### 4.11 Improved Minimap
**Current**: 200x140px, basic rendering
**Enhancements**:
- Drag viewport rectangle in minimap
- Show node colors matching category
- Toggle button in corner (not just Ctrl+M)
- Resize handle for user preference
- Hide when zoomed out far enough

#### 4.12 Selection Lasso Mode
**Gap**: Rectangle selection only
**Solution**: Add freehand lasso option
**Benefit**: Select non-rectangular groups

```
Implementation: graph/selection_manager.py
- L key to toggle lasso mode
- Draw freeform path
- Select nodes whose center is inside path
- Visual feedback with dashed line
```

### Priority 4: Accessibility Improvements

#### 4.13 Keyboard-Only Navigation
**Current**: Partial support
**Required**:
- Arrow keys move between connected nodes
- Enter/Space to select/edit focused node
- Tab cycles through node ports
- Escape closes popups/menus

```
Implementation: graph/keyboard_navigator.py
- Track "focused" node separate from "selected"
- Visual focus ring (blue outline)
- Announce node name for screen readers
```

#### 4.14 ARIA Labels for Screen Readers
**Gap**: No screen reader support
**Solution**: Add ARIA labels to key elements

```
Implementation: All node and canvas widgets
- role="application" on canvas
- aria-label on nodes: "Click Browser Element node, connected to Navigate node"
- aria-live regions for status updates
- Screen reader announcements on selection change
```

#### 4.15 Reduced Motion Support
**Gap**: No motion preference check
**Solution**: Check `prefers-reduced-motion`

```
Implementation: ui/theme.py ANIMATIONS class
def get_duration(base_ms: int) -> int:
    if prefers_reduced_motion():
        return 0  # Instant transitions
    return base_ms
```

#### 4.16 High Contrast Mode
**Gap**: Single dark theme only
**Solution**: High contrast theme variant

```
Implementation: ui/theme.py
- Add ThemeMode.HIGH_CONTRAST
- Increase all borders to 2px minimum
- Increase text contrast ratios
- Add patterns/textures to differentiate
```

### Priority 5: Advanced Features (Future)

#### 4.17 Copilot-Style Error Repair
**Inspiration**: Power Automate's Copilot Repair
**Feature**: AI suggests fixes for broken selectors

#### 4.18 Version Control Integration
**Inspiration**: n8n's versioning
**Feature**: Built-in workflow history with diff view

#### 4.19 Multi-User Collaboration
**Inspiration**: Figma multiplayer
**Feature**: Real-time collaborative editing (long-term)

#### 4.20 Workflow Templates Gallery
**Feature**: Pre-built workflow templates with preview

---

## 5. Implementation Roadmap

### Phase 1 (Q1 - Foundation)
1. Snap-to-Grid with guidelines
2. Viewport state persistence
3. Zoom % display + presets
4. Enhanced minimap (drag, resize)
5. Keyboard shortcut additions

### Phase 2 (Q2 - Alignment & Layout)
6. Node alignment toolbar + shortcuts
7. Auto-layout (Dagre algorithm)
8. Selection statistics bar
9. Quick node library panel

### Phase 3 (Q3 - Polish & Accessibility)
10. Connection preview highlighting
11. Node notes display
12. Selection lasso mode
13. Keyboard-only navigation
14. ARIA labels for screen readers
15. Reduced motion support

### Phase 4 (Q4 - Advanced)
16. High contrast theme
17. AI-powered error suggestions
18. Workflow versioning
19. Template gallery

---

## 6. Technical Considerations

### Performance Impact

| Feature | Impact | Mitigation |
|---------|--------|------------|
| Snap-to-Grid | Low | Only calculate on drag |
| Auto-Layout | Medium | Run in worker thread |
| Connection Preview | Medium | Cache port positions |
| Minimap Enhancements | Low | Already event-driven |
| ARIA Labels | Low | Text only |
| Node Notes | Low | Only render visible |

### Dependencies

| Feature | Dependency | Notes |
|---------|------------|-------|
| Auto-Layout | PyGraphviz or Dagre port | Dagre preferred |
| ARIA Support | PySide6 accessibility API | Built-in |
| Versioning | Git or custom diff | TBD |

### Breaking Changes
- None expected for Phase 1-2
- Workflow JSON schema extension for view state persistence

---

## 7. Competitive Positioning

After implementing Phase 1-3, CasareRPA would match or exceed:

| Feature Area | UiPath | PAD | n8n | Node-RED | CasareRPA |
|--------------|--------|-----|-----|----------|-----------|
| Auto-Layout | Yes | No | No | No | Planned |
| Snap Grid | Yes | No | No | No | Planned |
| Alignment Tools | No | No | No | Yes | Planned |
| Minimap | Yes | No | No | Yes | Enhanced |
| View Persistence | Yes | Yes | Yes | Yes | Planned |
| Dark Theme | Yes | Yes | Yes | Yes | Yes |
| Keyboard Nav | Partial | Partial | Partial | Yes | Planned |
| Screen Reader | No | No | No | No | Planned |
| Wire Bundling | No | No | No | No | Yes |
| Smart Routing | No | No | No | No | Yes |
| GPU Rendering | Unknown | Unknown | No | No | Yes |

**Unique CasareRPA Advantages** (already implemented):
- GPU-accelerated rendering (OpenGL 3.3)
- Wire bundling for cleaner complex workflows
- Smart wire routing around obstacles
- LOD-based rendering optimization
- Comprehensive theme system (1866 lines)

---

## Sources

### UiPath Documentation
- [UiPath Studio 2024.10 Release Notes](https://docs.uipath.com/studio/standalone/2024.10/user-guide/release-notes-2024-10-1)
- [UiPath Keyboard Shortcuts](https://docs.uipath.com/studio/standalone/2024.10/user-guide/keyboard-shortcuts)
- [UiPath Workflow Design](https://docs.uipath.com/studio/standalone/2024.10/user-guide/workflow-design)

### Power Automate Desktop
- [December 2024 Update](https://www.powercommunity.com/december-2024-update-of-power-automate-for-desktop/)
- [April 2024 Update](https://www.microsoft.com/en-us/power-platform/blog/power-automate/april-2024-update-of-power-automate-for-desktop/)
- [UI Elements Documentation](https://learn.microsoft.com/en-us/power-automate/desktop-flows/ui-elements)

### n8n
- [Editor UI Documentation](https://docs.n8n.io/courses/level-one/chapter-1/)
- [Node UI Design Guide](https://docs.n8n.io/integrations/creating-nodes/plan/node-ui-design/)

### Node-RED
- [Workspace Documentation](https://nodered.org/docs/user-guide/editor/workspace/)
- [Keyboard Shortcuts](https://flowfuse.com/node-red/keyboard/)

### Accessibility
- [Synergy Codes - Accessibility-First Workflow Builder](https://www.synergycodes.com/portfolio/accessibility-in-workflow-builder)
- [JointJS - Accessible Diagrams](https://www.jointjs.com/blog/diagram-accessibility)
- [Cambridge Intelligence - Accessible Graph Visualization](https://cambridge-intelligence.com/build-accessible-data-visualization-apps-with-keylines/)

---

## Appendix: Current Keyboard Shortcuts (CasareRPA)

### File Operations
| Shortcut | Action |
|----------|--------|
| Ctrl+N | New Workflow |
| Ctrl+O | Open Workflow |
| Ctrl+S | Save |
| Ctrl+Shift+S | Save as Scenario |

### Editing
| Shortcut | Action |
|----------|--------|
| Ctrl+Z | Undo |
| Ctrl+Shift+Z | Redo |
| Ctrl+X | Cut |
| Ctrl+C | Copy |
| Ctrl+V | Paste |
| Ctrl+D | Duplicate |
| Del / X | Delete |
| Ctrl+A | Select All |
| Ctrl+F | Find Node |
| F2 | Rename Node |

### View
| Shortcut | Action |
|----------|--------|
| F | Focus View (zoom to selection) |
| G | Home All (fit all nodes) |
| Ctrl+M | Toggle Minimap |
| Tab | Open Node Menu |

### Numpad/Quick Actions
| Shortcut | Action |
|----------|--------|
| 1 | Collapse/Expand Nearest |
| 2 | Select Nearest Node |
| 3 | Get Exec Out Port |
| 4 | Disable/Enable Nearest |
| 5 | Disable All Selected |
| 6 | Toggle Bottom Panel |

### Execution
| Shortcut | Action |
|----------|--------|
| F5 | Run Workflow |
| F6 | Pause |
| F7 | Stop |
| F8 | Restart |
| F9 | Start Listening |
| Shift+F9 | Stop Listening |
| Ctrl+F4 | Run To Node |
| Ctrl+F10 | Run Single Node |

### Canvas Interaction
| Shortcut | Action |
|----------|--------|
| Alt+Drag | Duplicate Node |
| V | Dive Into Subflow |
| C | Go Back from Subflow |
| Escape | Cancel Connection |
| Y+Drag | Cut Connections |
| Alt+Click Wire | Insert Reroute |
