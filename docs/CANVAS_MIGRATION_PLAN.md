# Canvas Migration Plan: Old → Presentation Layer

## Goal
Complete migration of `src/casare_rpa/canvas/` (86 files) to `src/casare_rpa/presentation/canvas/`, eliminating duplicate code and establishing Clean Architecture.

## Current State
- Old canvas/: 86 files across 14 subdirectories
- New presentation/canvas/: ~31 files in new structure
- Migration: ~25% complete
- **Blocker**: New code imports from old code (dependency chain must break first)

---

## Migration Strategy: 6-Phase Approach

### Phase 1: Foundation - Graph & Visual Layer (CRITICAL PATH)
**Priority: HIGHEST - Blocks everything else**

#### Why First?
New `presentation/canvas/visual_nodes/base_visual_node.py` imports from old `canvas/graph/`:
```python
from casare_rpa.canvas.graph.custom_node_item import CasareNodeItem
from casare_rpa.canvas.graph.node_icons import CATEGORY_COLORS, get_cached_node_icon_path
```

#### Files to Migrate (11 files):
```
canvas/graph/ → presentation/canvas/graph/
├── custom_node_item.py       # CasareNodeItem - custom rendering
├── custom_pipe.py             # Connection rendering
├── node_icons.py              # Icon cache & CATEGORY_COLORS
├── node_registry.py           # Node auto-discovery (COMPLEX)
├── node_graph_widget.py       # NodeGraphQt wrapper (COMPLEX)
├── node_widgets.py            # Custom Qt widgets for nodes
├── port_shapes.py             # Port visual styling
├── node_quick_actions.py      # Quick action popups
├── viewport_culling.py        # Performance optimization
├── minimap.py                 # Minimap widget
└── node_frame.py              # Node frame rendering
```

#### Steps:
1. Create `presentation/canvas/graph/` directory
2. Move files in dependency order:
   - **First**: `port_shapes.py`, `node_icons.py` (no internal deps)
   - **Second**: `custom_node_item.py`, `custom_pipe.py` (depend on icons/shapes)
   - **Third**: `node_widgets.py`, `node_quick_actions.py`
   - **Fourth**: `viewport_culling.py`, `minimap.py`, `node_frame.py`
   - **Last**: `node_graph_widget.py`, `node_registry.py` (COMPLEX - many deps)

3. Update imports in `presentation/canvas/visual_nodes/base_visual_node.py`:
   ```python
   # OLD
   from casare_rpa.canvas.graph.custom_node_item import CasareNodeItem
   # NEW
   from casare_rpa.presentation.canvas.graph.custom_node_item import CasareNodeItem
   ```

4. Handle circular import in `node_registry.py`:
   - Uses `ALL_VISUAL_NODE_CLASSES` from visual_nodes
   - Apply TYPE_CHECKING guard or lazy import

5. Update `node_graph_widget.py` NodeGraphQt integration:
   - Verify all monkey patches still work
   - Test connection validation integration

#### Testing:
- [ ] Visual nodes render correctly
- [ ] Icons display properly (CATEGORY_COLORS)
- [ ] Node registry auto-discovery works
- [ ] Connections validate and render
- [ ] Performance (viewport culling) intact

---

### Phase 2: Theme & Main Window
**Priority: HIGH - Required by many components**

#### Files to Migrate:
```
canvas/theme.py → presentation/canvas/theme.py
canvas/main_window.py → presentation/canvas/main_window.py
canvas/app.py → presentation/canvas/app.py
```

#### Steps:
1. Move `theme.py` (simple - just colors dataclass)
2. Update import in `main_window.py` (line 176):
   ```python
   # OLD
   from casare_rpa.canvas.theme import get_canvas_stylesheet
   # NEW
   from casare_rpa.presentation.canvas.theme import get_canvas_stylesheet
   ```

3. Move `main_window.py` - UPDATE all component imports to controllers
4. Move `app.py` - UPDATE to use presentation controllers

#### Main Window Refactoring:
- Replace component initialization with controller initialization
- Connect to EventBus instead of direct signal connections
- Delegate to controllers via EventBus pub/sub

---

### Phase 3: Components → Controllers Migration
**Priority: HIGH - Architectural shift**

#### Component-to-Controller Mapping:

| Old Component | New Controller | Action |
|---------------|----------------|--------|
| `workflow_lifecycle_component.py` | `workflow_controller.py` | **CREATE NEW** - Extract workflow lifecycle logic |
| `execution_component.py` | `execution_controller.py` | **CREATE NEW** - Extract execution logic |
| `trigger_component.py` | `trigger_controller.py` | **CREATE NEW** - Extract trigger management |
| `node_registry_component.py` | `node_controller.py` | **CREATE NEW** - Extract node registry logic |
| `selector_component.py` | `selector_controller.py` | **CREATE NEW** - Desktop selector management |
| `project_component.py` | `project_controller.py` | **CREATE NEW** - Project/scenario management |
| `preferences_component.py` | `preferences_controller.py` | **CREATE NEW** - Settings/preferences management |
| `autosave_component.py` | `autosave_controller.py` | **CREATE NEW** - Auto-save functionality |
| `dragdrop_component.py` | `workflow_controller.py` | **INTEGRATE** - Add drag-drop import to workflow controller |
| `base_component.py` | `base_controller.py` | **USE EXISTING** - Controller base class already exists |

#### Migration Pattern (per component):
1. Read old component file
2. **Create new controller** in `presentation/canvas/controllers/`
3. Extract business logic from Qt signal/slots → controller methods
4. Replace Qt signals with EventBus events
5. Subscribe to relevant events in controller.__init__
6. Update main_window to instantiate controller (not component)
7. Delete old component file (no deprecation - clean migration)
8. Create/update controller tests

#### EventBus Integration:
- Use existing `presentation/canvas/events/event_bus.py`
- Define new event types in `event_types.py` as needed
- Use `LazySubscription` for performance (lazy_subscription.py)

---

### Phase 4: UI Layer - Dialogs, Panels, Toolbars
**Priority: MEDIUM - UI components**

#### Dialogs Migration:

| Old Dialog | New Dialog | Action |
|------------|------------|--------|
| `credential_dialog.py` | ❌ | Move to `ui/dialogs/credential_dialog.py` |
| `new_project_dialog.py` | ❌ | Move to `ui/dialogs/project_dialog.py` |
| `new_scenario_dialog.py` | ❌ | Merge into `project_dialog.py` |
| `preferences_dialog.py` | `preferences_dialog.py` | EXISTS - verify complete |
| `recording_dialog.py` | ❌ | Move to `ui/dialogs/recording_dialog.py` |
| `template_browser_dialog.py` | ❌ | Move to `ui/dialogs/template_browser.py` |
| `trigger_config_dialog.py` | ❌ | Move to `ui/dialogs/trigger_config.py` |
| `trigger_type_selector.py` | ❌ | Move to `ui/dialogs/trigger_type_selector.py` |
| `variable_editor_dialog.py` | ❌ | Check if `ui/widgets/variable_editor_widget.py` replaces this |

#### Panels Migration:

| Old Panel | New Panel | Action |
|-----------|-----------|--------|
| `bottom_panel_dock.py` | ❌ | Move to `ui/panels/bottom_panel_dock.py` |
| `debug_toolbar.py` | `debug_toolbar.py` | EXISTS in `ui/toolbars/` - verify |
| `properties_panel.py` | `properties_panel.py` | EXISTS in `ui/panels/` - verify |
| `variable_inspector_dock.py` | `variables_panel.py` | EXISTS - may be renamed |
| `history_tab.py` | ❌ | Move to `ui/panels/` |
| `log_tab.py` | ❌ | Move to `ui/panels/` |
| `output_tab.py` | ❌ | Move to `ui/panels/` |
| `triggers_tab.py` | ❌ | Move to `ui/panels/` |
| `validation_tab.py` | ❌ | Move to `ui/panels/` |

**Decision**: Keep tab files as **separate subcomponents** for better scalability and maintainability. Each tab is a focused, testable unit.

#### Steps:
1. Create missing dialog files in `presentation/canvas/ui/dialogs/`
2. Move panel files to `presentation/canvas/ui/panels/`
3. Update controller imports (controllers reference these dialogs/panels)
4. Verify signal connections to controllers

---

### Phase 5: Subsystems - Connections, Search, Selectors, etc.
**Priority: MEDIUM - Specialized functionality**

#### Subsystem Placement Decisions:

| Subsystem | Files | Destination | Layer |
|-----------|-------|-------------|-------|
| **connections/** | 3 files | `presentation/canvas/connections/` | Presentation |
| **search/** | 4 files | `presentation/canvas/search/` | Presentation |
| **selectors/** | 7 files | `presentation/canvas/selectors/` | Presentation |
| **desktop/** | 2 files | `presentation/canvas/desktop/` | Presentation |
| **toolbar/** | 1 file | `presentation/canvas/ui/toolbars/` | Presentation |
| **ui/** | 3 files | `presentation/canvas/ui/` | Presentation |
| **scheduling/** | `schedule_storage.py` | `application/scheduling/` | **Application** |
| **scheduling/** | `schedule_dialog.py` | `presentation/canvas/ui/dialogs/` | Presentation |
| **execution/** | `trigger_runner.py` | `application/execution/` | **Application** |
| **execution/** | `performance_dashboard.py` | `presentation/canvas/ui/widgets/` | Presentation |
| **execution/** | `execution_timeline.py` | `presentation/canvas/ui/widgets/` | Presentation |
| **workflow/** | `workflow_import.py` | `application/workflow/` | **Application** |
| **workflow/** | `recent_files.py` | `application/workflow/` | **Application** |

#### Migration Priority:
1. **CRITICAL**: `connections/` (connection_validator, auto_connect, connection_cutter)
   - Required by graph/node_graph_widget.py
   - Move to `presentation/canvas/connections/`

2. **HIGH**: `selectors/` (desktop element picker)
   - Required by selector_controller
   - Move to `presentation/canvas/selectors/`

3. **HIGH**: `search/` (command palette)
   - Important UX feature
   - Move to `presentation/canvas/search/`

4. **MEDIUM**: `desktop/` (recording panel, rich comments)
   - Move to `presentation/canvas/desktop/`

5. **MEDIUM**: `toolbar/hotkey_manager.py`
   - Move to `presentation/canvas/ui/toolbars/`

6. **LOW**: `scheduling/` and `execution/` (non-UI parts)
   - Move business logic to `application/` layer
   - Keep UI parts in `presentation/canvas/ui/`

7. **LOW**: `workflow/` (import/export)
   - Move to `application/workflow/`

---

### Phase 6: Import Updates & Old Canvas Deletion
**Priority: CRITICAL - Final cleanup**

#### Import Update Locations (19 files):

**Source Files (11):**
1. `canvas/ui/__init__.py` - Update re-exports
2. `canvas/ui/action_factory.py` - TYPE_CHECKING import
3. `canvas/ui/signal_bridge.py` - TYPE_CHECKING import
4. `canvas/main_window.py` - theme import
5. `presentation/canvas/visual_nodes/base_visual_node.py` - graph imports (DONE in Phase 1)
6-11. Various `canvas/*/___init__.py` - Update or remove

**Test Files (8):**
1. `tests/performance/test_baseline.py`
2. `tests/performance/test_cache_hit_rates.py`
3. `tests/presentation/canvas/components/test_*.py` (3 files)
4. `tests/presentation/canvas/ui/test_*.py` (2 files)
5. `tests/test_visual_nodes_imports.py` - Update to test new paths

**Entry Point (IMMEDIATE UPDATE):**
- `run.py` - Update `from casare_rpa.canvas import main` → `from casare_rpa.presentation.canvas import main`

**Documentation:**
- `CONTRIBUTING.md` line 200 - Update import example

#### Clean Cut Migration Strategy:

**NO deprecation shims** - All imports updated immediately:

1. Update all 19 files at once (scripted find/replace)
2. Update run.py entry point
3. Update documentation
4. **DELETE** entire `src/casare_rpa/canvas/` directory
5. Run full test suite
6. Fix any remaining import errors

#### Mass Import Update Script:
```bash
# Update all imports in one pass
find src tests -name "*.py" -type f -exec sed -i \
  's/from casare_rpa\.canvas\./from casare_rpa.presentation.canvas./g' {} +
find src tests -name "*.py" -type f -exec sed -i \
  's/import casare_rpa\.canvas\./import casare_rpa.presentation.canvas./g' {} +
```

#### Application Layer Imports:
```bash
# Update application layer imports
sed -i 's/casare_rpa\.canvas\.scheduling/casare_rpa.application.scheduling/g' **/*.py
sed -i 's/casare_rpa\.canvas\.workflow/casare_rpa.application.workflow/g' **/*.py
sed -i 's/casare_rpa\.canvas\.execution\.trigger_runner/casare_rpa.application.execution.trigger_runner/g' **/*.py
```

---

## Execution Order Summary

```
1. Phase 1: Graph & Visual Layer (BLOCKS everything)
   ├── Move graph/ (11 files)
   ├── Update base_visual_node.py imports
   └── Test node rendering

2. Phase 2: Theme & Main Window
   ├── Move theme.py, app.py
   ├── Update main_window.py
   └── Test application startup

3. Phase 3: Components → Controllers
   ├── Create 8 new controllers
   ├── Integrate dragdrop into workflow_controller
   ├── Update main_window to use controllers
   └── Test workflow lifecycle

4. Phase 4: UI Layer
   ├── Move 6 dialogs
   ├── Move 5 panels (+ 5 tab files)
   └── Test UI interactions

5. Phase 5: Subsystems
   ├── Move connections/ (3 files)
   ├── Move search/ (4 files)
   ├── Move selectors/ (7 files)
   ├── Move desktop/ (2 files)
   ├── Split scheduling/execution to application/
   └── Test specialized features

6. Phase 6: Import Updates & Deletion
   ├── Mass update all 19 import locations (scripted)
   ├── Update run.py entry point (immediate)
   ├── Update documentation
   ├── **DELETE src/casare_rpa/canvas/ entirely**
   ├── Run full test suite
   └── Fix any remaining import errors
```

---

## Risk Mitigation

### Circular Import Risks:
- **node_registry ↔ visual_nodes**: Use TYPE_CHECKING + lazy import
- **main_window ↔ controllers**: TYPE_CHECKING guards
- **graph_widget ↔ connections**: Try/except import guards (existing pattern)

### Testing Strategy:
- Run full test suite after each phase
- Manual UI testing for visual components
- Performance regression testing (viewport culling)
- Connection validation testing

### Rollback Plan:
- Git branch: `refactor/canvas-to-presentation-migration`
- Commit after each phase completes
- If tests fail after Phase 6 deletion, revert last commit to restore old canvas/

---

## Critical Files to Review Before Starting

Must read before implementation:
1. `canvas/graph/node_graph_widget.py` - Complex NodeGraphQt integration
2. `canvas/graph/node_registry.py` - Auto-discovery logic
3. `canvas/components/workflow_lifecycle_component.py` - Complex workflow logic
4. `canvas/main_window.py` - Component orchestration
5. `presentation/canvas/controllers/base_controller.py` - Controller pattern
6. `presentation/canvas/events/event_bus.py` - EventBus architecture

---

## Success Criteria

- [ ] `src/casare_rpa/canvas/` directory **DELETED** (no files remaining)
- [ ] All imports updated to `presentation.canvas` or `application`
- [ ] All tests passing (pytest tests/ -v)
- [ ] Application starts without errors
- [ ] Workflows execute successfully
- [ ] No circular import errors
- [ ] No deprecation warnings (clean cut migration)
- [ ] Documentation updated (CONTRIBUTING.md, etc.)
- [ ] Controllers created for all 9 components
- [ ] Business logic separated into application/ layer

---

## Final Decisions (User Approved)

1. **Component strategy**: ✅ Create new separate controllers (autosave_controller, selector_controller, project_controller, etc.)
2. **Panel structure**: ✅ Keep as separate subcomponent files for scalability and maintainability
3. **Application split**: ✅ Business logic files (scheduling_storage, workflow_import) move to application/ layer
4. **Entry point**: ✅ Immediate update - change run.py to `from casare_rpa.presentation.canvas import main`
5. **Migration approach**: ✅ **Clean cut** - Delete old canvas/ entirely, no deprecation shims, update all imports immediately
