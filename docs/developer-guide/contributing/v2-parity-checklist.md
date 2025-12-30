# V2 Parity Checklist (QA)

This document serves as the repeatable manual QA checklist to verify that the V2 UI (`NewMainWindow`) has achieved feature parity with the legacy V1 UI.

## 1. Application Launch
- [ ] Default startup: `python manage.py canvas` launches V2 UI.
- [ ] Legacy fallback: `python manage.py canvas --v1` launches V1 UI.
- [ ] High-DPI scaling: UI looks crisp on 4K/scaled monitors.
- [ ] Font rendering: Geist font family is applied to all UI elements.

## 2. Workflow Lifecycle
- [ ] **New**: `File > New Workflow` clears the canvas.
- [ ] **Open**: `File > Open...` successfully loads a `.casare` workflow.
- [ ] **Recent Files**: `File > Recent Files` menu is populated and functional.
- [ ] **Save**: `File > Save` updates the current file.
- [ ] **Save As**: `File > Save As...` prompts for location and saves copy.
- [ ] **Reload**: `File > Reload` re-syncs canvas with disk.

## 3. Execution Controls
- [ ] **Run (F5)**: Starts execution; "Run" button changes state.
- [ ] **Stop (F7)**: Aborts execution.
- [ ] **Pause (F6)**: Pauses execution; "Pause" button toggles.
- [ ] **Restart (F8)**: Stops and restarts execution.
- [ ] **Run To Node**: Right-click node > Run to Node works.
- [ ] **Run Single Node**: Right-click node > Run This Node works.

## 4. UI Panels (Docks)
- [ ] **Bottom Panel (6)**: Docks correctly; contains Variables, Output, Log, Validation.
- [ ] **Side Panel (7)**: Docks correctly; contains Debug, Robot Picker, Analytics.
- [ ] **Minimap (Ctrl+M)**: Shows functional overview of canvas.
- [ ] **No Floating**: Verify docks cannot be floated (dock-only enforcement).

## 5. Editing Operations
- [ ] **Undo/Redo (Ctrl+Z / Ctrl+Y)**: Works for node creation, movement, and deletion.
- [ ] **Cut/Copy/Paste**: Works across different workflows or within same canvas.
- [ ] **Duplicate (Ctrl+D)**: Duplicates selected nodes at cursor position.
- [ ] **Delete (Del)**: Removes selected nodes and frames.
- [ ] **Select All (Ctrl+A)**: Selects every item on canvas.

## 6. Canvas Navigation
- [ ] **Zoom**: Wheel zoom and `Ctrl++`/`Ctrl+-` work.
- [ ] **Focus (F)**: Zooms and centers on selected node.
- [ ] **Home (G)**: Fits all nodes into view.
- [ ] **Auto-Layout (Ctrl+L)**: Arranges nodes using the layout engine.

## 7. Search and Discovery
- [ ] **Node Search (Ctrl+F)**: Opens fuzzy search popup; selects result on canvas.
- [ ] **Quick Node Mode (Shift+LMB)**: Rapidly adds nodes to canvas.

## 8. Layout Persistence
- [ ] **Save Layout**: Stores dock positions and sizes.
- [ ] **Restore Layout**: App starts with previously saved layout.
- [ ] **Reset Layout**: Reverts to default 6-menu factory layout.

---

## "Cutover-Ready" Gate
The V2 UI is considered "Cutover-Ready" when:
1. All items in sections 1-6 are checked.
2. No critical "Coming soon" placeholders remain in primary workflows.
3. Performance is equal to or better than V1 on workflows with >100 nodes.
