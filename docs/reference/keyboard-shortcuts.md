# Keyboard Shortcuts Reference

Complete reference for keyboard shortcuts in the CasareRPA Canvas Designer.

---

## Quick Reference

| Shortcut | Action |
|----------|--------|
| `F5` | Run workflow |
| `F6` | Pause execution |
| `F7` | Stop execution |
| `Ctrl+S` | Save workflow |
| `Ctrl+Z` | Undo |
| `Ctrl+Y` / `Ctrl+Shift+Z` | Redo |
| `Del` | Delete selected |
| `F` | Focus on selected node |
| `G` | Fit all nodes in view |

---

## File Operations

| Shortcut | Action | Description |
|----------|--------|-------------|
| `Ctrl+N` | New Workflow | Create a new empty workflow |
| `Ctrl+O` | Open | Open existing workflow file |
| `Ctrl+S` | Save | Save current workflow |
| `Ctrl+Shift+S` | Save As | Save workflow with new name/location |
| `Ctrl+Q` | Exit | Close the application |

---

## Edit Operations

| Shortcut | Action | Description |
|----------|--------|-------------|
| `Ctrl+Z` | Undo | Undo last action |
| `Ctrl+Y` | Redo | Redo last undone action |
| `Ctrl+Shift+Z` | Redo | Alternative redo shortcut |
| `Ctrl+X` | Cut | Cut selected nodes |
| `Ctrl+C` | Copy | Copy selected nodes |
| `Ctrl+V` | Paste | Paste copied nodes |
| `Ctrl+D` | Duplicate | Duplicate selected nodes |
| `Del` | Delete | Delete selected nodes |
| `Ctrl+A` | Select All | Select all nodes on canvas |
| `Ctrl+F` | Find Node | Search for nodes |
| `F2` | Rename Node | Rename selected node |

---

## Execution Controls

| Shortcut | Action | Description |
|----------|--------|-------------|
| `F5` | Run | Execute the workflow |
| `Shift+F3` | Run All | Execute all workflows concurrently |
| `F6` | Pause | Pause workflow execution |
| `F7` | Stop | Stop workflow execution |
| `F9` | Toggle Breakpoint | Add/remove breakpoint on node |
| `F10` | Step Over | Execute current node, move to next |
| `F11` | Step Into | Step into subflow |
| `Shift+F11` | Step Out | Step out of current subflow |

---

## View Operations

| Shortcut | Action | Description |
|----------|--------|-------------|
| `F` | Focus View | Zoom to selected node and center |
| `G` | Home All | Fit all nodes in view |
| `Ctrl+M` | Minimap | Toggle minimap overview |
| `6` | Toggle Panel | Show/hide bottom panel |
| `7` | Side Panel | Show/hide side panel |

### Zoom Controls

| Shortcut | Action |
|----------|--------|
| `Ctrl+Mouse Wheel` | Zoom in/out |
| `Ctrl++` | Zoom in |
| `Ctrl+-` | Zoom out |
| `Ctrl+0` | Reset zoom to 100% |

---

## Node Operations

| Shortcut | Action | Description |
|----------|--------|-------------|
| `1` | Collapse/Expand | Toggle collapse on nearest node to cursor |
| `2` | Select Nearest | Select nearest node to mouse cursor |
| `3` | Get Exec Out | Get exec_out port of nearest node |
| `4` | Disable Node | Toggle disable on nearest node |
| `5` | Disable Selected | Toggle disable on all selected nodes |

### Selection

| Shortcut | Action |
|----------|--------|
| `Click` | Select node |
| `Ctrl+Click` | Add to selection |
| `Shift+Click` | Range select |
| `Drag` | Select multiple (marquee) |
| `Escape` | Deselect all |

---

## Panel Shortcuts

| Shortcut | Panel | Description |
|----------|-------|-------------|
| `Ctrl+Shift+D` | Debug Panel | Show execution debug panel |
| `Ctrl+Shift+E` | Project Explorer | Show project file browser |
| `Ctrl+Shift+C` | Credentials | Show credentials manager |
| `Ctrl+Shift+G` | AI Assistant | Show AI workflow generator |
| `Ctrl+Shift+R` | Robot Picker | Show robot selection |
| `Ctrl+Shift+A` | Analytics | Show analytics panel |
| `Ctrl+Shift+M` | Process Mining | Show process mining panel |
| `Ctrl+Shift+F` | Fleet Dashboard | Show robot fleet management |
| `Ctrl+B` | Breakpoints | Show breakpoints panel |

---

## Canvas Navigation

| Shortcut | Action |
|----------|--------|
| `Middle Mouse + Drag` | Pan canvas |
| `Space + Drag` | Pan canvas (alternative) |
| `Right Mouse + Drag` | Context pan |
| `Arrow Keys` | Move selected nodes |
| `Shift+Arrow Keys` | Move nodes faster |

---

## Connection Shortcuts

| Action | Method |
|--------|--------|
| Create connection | Drag from output port to input port |
| Delete connection | Click connection, press `Del` |
| Reroute connection | Right-click connection, select "Add Reroute" |

---

## Context Menu

Right-click on canvas or nodes to access context menus:

### Canvas Context Menu

| Item | Description |
|------|-------------|
| Add Node | Open node palette |
| Paste | Paste copied nodes |
| Select All | Select all nodes |
| Zoom to Fit | Fit all nodes in view |

### Node Context Menu

| Item | Shortcut | Description |
|------|----------|-------------|
| Copy | `Ctrl+C` | Copy node |
| Cut | `Ctrl+X` | Cut node |
| Duplicate | `Ctrl+D` | Duplicate node |
| Delete | `Del` | Delete node |
| Disable | `4` | Toggle node disable |
| Rename | `F2` | Rename node |
| Toggle Breakpoint | `F9` | Add/remove breakpoint |
| Focus | `F` | Center view on node |

---

## Help Shortcuts

| Shortcut | Action |
|----------|--------|
| `F1` | Open documentation |
| `Ctrl+Shift+?` | Show keyboard shortcuts dialog |

---

## Platform-Specific Notes

### Windows

All shortcuts use `Ctrl` as the modifier key.

### Alternative Keys

Some users may prefer:

| Standard | Alternative |
|----------|-------------|
| `Ctrl+Y` | `Ctrl+Shift+Z` (Redo) |
| `Del` | `Backspace` (Delete) |

---

## Customization

Keyboard shortcuts can be customized in:

**Edit > Preferences > Keyboard Shortcuts**

Or via configuration:

```yaml
# config/shortcuts.yaml
shortcuts:
  run: "F5"
  stop: "F7"
  save: "Ctrl+S"
  # Add custom mappings
```

---

## Printable Quick Reference Card

```
+------------------------------------------+
|       CASARE RPA QUICK SHORTCUTS         |
+------------------------------------------+
| FILE                                     |
| Ctrl+N  New    Ctrl+O  Open              |
| Ctrl+S  Save   Ctrl+Q  Exit              |
+------------------------------------------+
| EDIT                                     |
| Ctrl+Z  Undo   Ctrl+Y  Redo              |
| Ctrl+C  Copy   Ctrl+V  Paste             |
| Ctrl+D  Duplicate     Del  Delete        |
| Ctrl+A  Select All    F2   Rename        |
+------------------------------------------+
| RUN                                      |
| F5   Run       F6   Pause   F7   Stop    |
| F9   Breakpoint      F10  Step Over      |
+------------------------------------------+
| VIEW                                     |
| F   Focus      G   Fit All               |
| Ctrl+M  Minimap     6  Toggle Panel      |
+------------------------------------------+
| NODES                                    |
| 1  Collapse    2  Select Nearest         |
| 4  Disable     5  Disable Selected       |
+------------------------------------------+
```

---

## Related Documentation

- [Canvas Overview](../user-guide/getting-started/canvas-overview.md) - Canvas interface guide
- [First Workflow](../user-guide/getting-started/first-workflow.md) - Getting started tutorial
- [Debugging](../user-guide/guides/debugging.md) - Debug workflow execution
