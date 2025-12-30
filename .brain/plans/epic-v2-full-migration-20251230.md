# Epic V2: Full UI Migration to NewMainWindow

**Created**: 2025-12-30
**Strategy**: Big-bang cutover after sequential feature migrations
**Theme**: Everything must use THEME_V2/TOKENS_V2 (no legacy THEME)
**Architecture**: Refactor controllers to be MainWindow-agnostic

---

## North Star

Migrate all UI features from legacy `main_window.py` to `new_main_window.py`:
- 6 menu bars (File, Edit, View, Run, Automation, Help)
- 50+ keyboard shortcuts
- 9 dock panels
- 16 controllers
- 24 dialogs
- All managers/coordinators

---

## Constraints (Hard Requirements)

- **THEME_V2 ONLY**: No legacy THEME imports in migrated code
- **BaseDialogV2**: All dialogs must use v2 base
- **PopupWindowBase**: All popups must use v2 base
- **IMainWindow interface**: Controllers must depend on abstraction
- **No lambdas**: Use functools.partial for signal connections
- **@Slot decorator**: Required on all slot methods

---

## Dependency Graph for Parallel Execution

```
Phase 1 (Foundation) BLOCKS everything
    |
    +-- Phase 2 (Chrome) ──────────────────────────────────────┐
    |       |                                                   |
    |       +-- Phase 3 (Search) ───┐                          |
    |                               |                          |
    +-- Phase 4 (Panels) ────+------+--+--+--+--+--+           |
            |                 |      |  |  |  |  |  |           |
            +─> 4.1 Project  |      |  |  |  |  |  |           |
            +─> 4.2 Variables|      |  |  |  |  |  |           |
            +─> 4.3 Output   |      |  |  |  |  |  |           |
            +─> 4.4 Log      |      |  |  |  |  |  |           |
            +─> 4.5 Terminal |      |  |  |  |  |  |           |
            +─> 4.6 Validation      |  |  |  |  |  |           |
            +─> 4.7 History         |  |  |  |  |  |           |
            +─> 4.8 Debug           |  |  |  |  |  |           |
            +─> 4.9 Breakpoints     |  |  |  |  |  |           |
            +─> 4.10 Minimap        |  |  |  |  |  |           |
            +─> 4.11 Process Mining |  |  |  |  |  |           |
            +─> 4.12 Analytics      |  |  |  |  |  |           |
            +─> 4.13 Robot Picker   |  |  |  |  |  |           |
            +─> 4.14 Job Queue      |  |  |  |  |  |           |
            +─> 4.15 Credentials    |  |  |  |  |  |           |
            +─> 4.16 Recording      |  |  |  |  |  |           |
                                         |  |  |  |  |  |
    +-- Phase 5 (Context Menus) <────────┘  |  |  |  |  |
    |                                         |  |  |  |  |
    +-- Phase 6 (Dialogs) ─────────────────────┘  |  |  |  |
            |                                    |  |  |  |
            +─> 6.1 Preferences                  |  |  |  |
            +─> 6.2 Node Properties              |  |  |  |
            +─> 6.3 Project Manager              |  |  |  |
            +─> 6.4 Hotkey Manager               |  |  |  |
            +─> 6.5 Other Dialogs                |  |  |  |
                                                   |  |  |
    +-- Phase 7 (Advanced) ─────────────────────────┘  |  |
            |       |                                   |  |
            +─> 7.1 Debug Mode <────────────────────────┘  |
            +─> 7.2 Recording System                       |
            +─> 7.3 Element Picker                         |
            +─> 7.4 Quick Node Mode                        |
            +─> 7.5 Auto Features                         |
                                                      |
    +-- Phase 8 (Integration) <─────────────────────────┘
            |
            +─> 8.1 Layout Persistence
            +─> 8.2 Autosave
            +─> 8.3 Recent Files
            +─> 8.4 Signal Coordination
            +─> 8.5 Cutover
```

**Legend**: `─>` = sequential dependency, `|` = can run in parallel

---

# Phase 0 — Parallel Execution Foundation

## Epic 0.1: Dependency Setup for Parallel Work

**Scope**
- Create tracking files for parallel sessions
- Define epic boundaries clearly
- Create epic stub files for concurrent editing

**Dependencies**
- None

**Done when**
- Each epic has its own plan file with clear boundaries
- Session tracking prevents merge conflicts

**Manual test**
- Two sessions can edit different epics without conflicts

**Rollback**
- Delete epic stub files; use this master plan

---

# Phase 1 — Foundation Refactoring

## Epic 1.1: Controller Interface Layer

**Scope**
- Decouple controllers from MainWindow implementation
- Create `IMainWindow` Protocol interface
- Update all 16 controllers to use interface

**Dependencies**
- None (this is the foundation epic)

**Done when**
- `IMainWindow` Protocol exists in `controllers/interfaces.py`
- All controllers type-hint `IMainWindow` instead of `MainWindow`
- Both v1 and v2 MainWindow implement `IMainWindow`
- Controllers import from `interfaces.py`, not `main_window.py`

**Manual test**
- Controllers can be imported without main_window.py
- Type checkers verify interface compatibility

**Rollback**
- Delete interfaces.py; restore direct MainWindow imports

**Files**
- `controllers/interfaces.py` (NEW)
- `controllers/base_controller.py`
- `controllers/workflow_controller.py`
- `controllers/execution_controller.py`
- `controllers/node_controller.py`
- `controllers/panel_controller.py`
- `controllers/viewport_controller.py`
- `controllers/variable_controller.py`
- `controllers/history_controller.py`
- `controllers/debug_controller.py`
- `controllers/breakpoint_controller.py`
- `controllers/recording_controller.py`
- `controllers/selector_controller.py`
- `controllers/bookmark_controller.py`
- `controllers/comment_controller.py`
- `controllers/layout_controller.py`
- `controllers/signal_coordinator.py`

---

## Epic 1.2: ActionManager Refactor for V2

**Scope**
- Create centralized action/shortcut management
- Use THEME_V2 for all styling
- Support hotkey customization (QSettings)

**Dependencies**
- Epic 1.1 (need IMainWindow for signal integration)

**Done when**
- `ActionManagerV2` class exists
- All 50+ actions registered with shortcuts
- Shortcut customization persists to QSettings
- Action state updates work (enable/disable)

**Manual test**
- Register action, trigger via shortcut, verify execution
- Change shortcut, restart, verify persistence

**Rollback**
- Keep ActionManagerV2 unused; continue using legacy actions

**Files**
- `ui/chrome/action_manager_v2.py` (NEW)

---

## Epic 1.3: MenuBuilder Refactor for V2

**Scope**
- Build all menus dynamically using THEME_V2
- 6 top-level menus with full structure
- Dynamic recent files list
- Keyboard shortcut display in menu items
- Icons using IconProviderV2

**Dependencies**
- Epic 1.1 (need IMainWindow)
- Epic 1.2 (need ActionManagerV2)

**Done when**
- `MenuBuilderV2` class exists
- All 6 menus build correctly
- Recent files list is dynamic
- Shortcuts display in menu items
- Icons use IconProviderV2

**Manual test**
- Open each menu, verify structure
- Trigger menu item, verify action executes

**Rollback**
- Keep MenuBuilderV2 unused; continue using legacy menus

**Files**
- `ui/chrome/menu_builder_v2.py` (NEW)

---

# Phase 2 — Core Chrome (Menus + Shortcuts)

## Epic 2.1: Menu Bar Migration to NewMainWindow

**Scope**
- Add `_create_menus()` method to NewMainWindow
- Integrate MenuBuilderV2
- Wire all menu actions to controllers

**Dependencies**
- Epic 1.3 (MenuBuilderV2 must exist)

**Done when**
- NewMainWindow has full menu bar
- All menu items wired to controller methods
- Menu structure matches legacy exactly

**Manual test**
- Open each menu, trigger items
- Verify all expected actions work

**Rollback**
- Remove menu creation from NewMainWindow; keep legacy menus

**Files**
- `new_main_window.py` (modify)

---

## Epic 2.2: Keyboard Shortcuts System

**Scope**
- Complete hotkey system with customization
- Conflict detection
- HotkeyEditorDialog for customization
- Persist to QSettings

**Dependencies**
- Epic 1.2 (ActionManagerV2)

**Done when**
- All 50+ shortcuts registered
- Conflict detection works
- HotkeyEditorDialog allows customization
- Shortcuts persist across restarts

**Manual test**
- Open dialog, change shortcut
- Trigger new shortcut, verify execution
- Restart app, verify persistence

**Rollback**
- Disable customization UI; use default shortcuts

**Files**
- `ui/chrome/hotkey_manager_v2.py` (NEW)
- `ui/dialogs_v2/hotkey_editor_dialog_v2.py` (NEW)

---

# Phase 3 — Search

## Epic 3.1: Remove Command Palette (v1 + v2)

**Decision**: Command palette will not ship.

**Scope**
- Remove legacy `search/command_palette.py`
- Remove v2 `ui/widgets/popups/command_palette_v2.py`
- Remove Ctrl+Shift+P bindings and any “open command palette” menu actions/signals
- Remove `IMainWindow.get_command_palette()` and any controller call sites

**Dependencies**
- None

**Done when**
- Ripgrep for `command_palette|CommandPalette` returns 0 in `src/casare_rpa/presentation/canvas`
- Ctrl+Shift+P is unbound (or repurposed explicitly)

**Manual test**
- Press Ctrl+Shift+P: nothing opens

**Rollback**
- Revert this epic

**Files**
- `search/command_palette.py` (DELETE)
- `ui/widgets/popups/command_palette_v2.py` (DELETE)

---

## Epic 3.2: Node Search V2

**Scope**
- Refactor node search to use THEME_V2
- Ctrl+F to open
- Search by node name/type/property

**Dependencies**
- Epic 1.1 (need IMainWindow for graph access)

**Done when**
- Node search uses THEME_V2
- Search results highlight in graph
- Keyboard navigation works

**Manual test**
- Press Ctrl+F, type query
- Navigate results with arrow keys

**Rollback**
- Keep legacy node search; disable v2

**Files**
- `search/node_search_v2.py` (NEW or refactor existing)

---

# Phase 4 — Panel Migrations

**All panels depend on**: Epic 1.1 (IMainWindow interface)

**Panels can be migrated in parallel** - each panel is independent.

## Epic 4.1: Project Explorer Panel

**Scope**
- Migrate Project Explorer to THEME_V2
- Ensure all CRUD operations work
- Tree view with icons

**Dependencies**
- Epic 1.1
- Epic 2.1 (for menu integration)

**Done when**
- Panel uses THEME_V2 only
- All CRUD operations work (open, create, delete, rename)
- Tree icons use IconProviderV2
- Panel docks correctly in NewMainWindow

**Manual test**
- Create project, verify appears
- Rename project, verify update
- Delete project, verify removal
- Dock/undock panel

**Rollback**
- Keep legacy ProjectExplorerPanel; wire to v2 shell

**Files**
- `ui/panels/project_explorer_panel.py`

---

## Epic 4.2: Variables Panel

**Scope**
- Migrate Variables panel to THEME_V2
- Design/Runtime mode switching
- CRUD operations for variables

**Dependencies**
- Epic 1.1
- Epic 4.1 (optional: for consistency)

**Done when**
- Panel uses THEME_V2 only
- Variable CRUD works
- Design/Runtime mode switching works
- Table displays correctly

**Manual test**
- Create variable, verify appears
- Edit variable value
- Switch modes, verify correct variables shown

**Rollback**
- Keep legacy VariablesPanel

**Files**
- `ui/panels/variables_panel.py`

---

## Epic 4.3: Output Panel

**Scope**
- Migrate Output tab to THEME_V2
- Text display with syntax highlighting
- Clear functionality

**Dependencies**
- Epic 1.1

**Done when**
- Tab uses THEME_V2
- Output displays correctly
- Clear button works
- Auto-scroll works

**Manual test**
- Run workflow, verify output appears
- Click clear, verify empties
- Scroll to bottom, verify follows

**Rollback**
- Keep legacy OutputTab

**Files**
- `ui/panels/output_tab.py`

---

## Epic 4.4: Log Panel

**Scope**
- Migrate Log tab to THEME_V2
- Log streaming with filtering
- Multiple log levels

**Dependencies**
- Epic 1.1

**Done when**
- Tab uses THEME_V2
- Logs stream correctly
- Filtering by level works
- Auto-scroll works

**Manual test**
- Trigger log events, verify display
- Change filter, verify hides/shows correctly

**Rollback**
- Keep legacy LogTab

**Files**
- `ui/panels/log_tab.py`

---

## Epic 4.5: Terminal Panel

**Scope**
- Migrate Terminal tab to THEME_V2
- Terminal output display

**Dependencies**
- Epic 1.1

**Done when**
- Tab uses THEME_V2
- Terminal output displays

**Manual test**
- Run terminal command, verify output appears

**Rollback**
- Keep legacy TerminalTab

**Files**
- `ui/panels/terminal_tab.py`

---

## Epic 4.6: Validation Panel

**Scope**
- Migrate Validation tab to THEME_V2
- Validation results display
- Issue navigation

**Dependencies**
- Epic 1.1

**Done when**
- Tab uses THEME_V2
- Validation errors display
- Click error to navigate to node

**Manual test**
- Trigger validation, verify errors appear
- Click error, verify graph navigates

**Rollback**
- Keep legacy ValidationTab

**Files**
- `ui/panels/validation_tab.py`

---

## Epic 4.7: History Panel

**Scope**
- Migrate History tab to THEME_V2
- Undo/Redo history display

**Dependencies**
- Epic 1.1

**Done when**
- Tab uses THEME_V2
- History displays correctly
- Click to jump to state

**Manual test**
- Make changes, verify history updates
- Click history item, verify state restores

**Rollback**
- Keep legacy HistoryTab

**Files**
- `ui/panels/history_tab.py`

---

## Epic 4.8: Debug Panel

**Scope**
- Create Debug panel with THEME_V2
- Call stack display
- Watch expressions
- Breakpoints integration

**Dependencies**
- Epic 1.1
- Epic 4.9 (Breakpoints panel)

**Done when**
- Panel uses THEME_V2
- Call stack displays during debug
- Watch expressions evaluate
- Can add/remove watches

**Manual test**
- Start debug, verify call stack appears
- Add watch, verify value updates

**Rollback**
- Delete new panel; keep debug in legacy

**Files**
- `ui/panels/debug_panel.py` (NEW)

---

## Epic 4.9: Breakpoints Panel

**Scope**
- Migrate Breakpoints panel to THEME_V2
- Enable/disable breakpoints
- Condition editing

**Dependencies**
- Epic 1.1

**Done when**
- Panel uses THEME_V2
- Can add/remove breakpoints
- Can enable/disable
- Can edit conditions

**Manual test**
- Add breakpoint on node, verify appears
- Disable breakpoint, verify stops triggering
- Edit condition, verify evaluates

**Rollback**
- Keep legacy BreakpointsPanel

**Files**
- `ui/panels/breakpoints_panel.py`

---

## Epic 4.10: Minimap Panel

**Scope**
- Migrate Minimap to THEME_V2
- Viewport sync
- Click-to-navigate

**Dependencies**
- Epic 1.1

**Done when**
- Panel uses THEME_V2
- Minimap shows graph overview
- Clicking minimap navigates viewport
- Viewport rectangle updates on pan/zoom

**Manual test**
- Pan graph, verify rectangle moves
- Click minimap, verify viewport jumps

**Rollback**
- Keep legacy MinimapPanel

**Files**
- `ui/panels/minimap_panel.py`

---

## Epic 4.11: Process Mining Panel

**Scope**
- Migrate Process Mining to THEME_V2
- Process graph visualization
- Metrics display

**Dependencies**
- Epic 1.1

**Done when**
- Panel uses THEME_V2
- Process graph displays
- Metrics show correctly

**Manual test**
- Load process mining data, verify visualization

**Rollback**
- Keep legacy ProcessMiningPanel

**Files**
- `ui/panels/process_mining_panel.py`

---

## Epic 4.12: Analytics Panel

**Scope**
- Migrate Analytics to THEME_V2
- Charts and metrics display

**Dependencies**
- Epic 1.1

**Done when**
- Panel uses THEME_V2
- Charts render correctly
- Metrics update

**Manual test**
- Load analytics data, verify display

**Rollback**
- Keep legacy AnalyticsPanel

**Files**
- `ui/panels/analytics_panel.py`

---

## Epic 4.13: Robot Picker Panel

**Scope**
- Migrate Robot Picker to THEME_V2
- Robot selection
- Status indicators

**Dependencies**
- Epic 1.1

**Done when**
- Panel uses THEME_V2
- Robot list displays
- Status indicators show correct state
- Selection works

**Manual test**
- Select robot, verify selection propagates

**Rollback**
- Keep legacy RobotPickerPanel

**Files**
- `ui/panels/robot_picker_panel.py`

---

## Epic 4.14: Job Queue Panel

**Scope**
- Migrate Job Queue to THEME_V2
- Job queue tabs
- Job actions (cancel, retry, etc.)

**Dependencies**
- Epic 1.1

**Done when**
- Panel uses THEME_V2
- Jobs display in tabs
- Actions work correctly

**Manual test**
- Submit job, verify appears in queue
- Cancel job, verify removes

**Rollback**
- Keep legacy JobQueuePanel

**Files**
- `ui/panels/job_queue_panel.py`

---

## Epic 4.15: Credentials Panel

**Scope**
- Migrate Credentials to THEME_V2
- Credential CRUD
- Masking/unmasking

**Dependencies**
- Epic 1.1

**Done when**
- Panel uses THEME_V2
- Can create/delete/edit credentials
- Values are masked
- Unmask works

**Manual test**
- Create credential, verify appears masked
- Click show, verify reveals
- Delete, verify removes

**Rollback**
- Keep legacy CredentialsPanel

**Files**
- `ui/panels/credentials_panel.py`

---

## Epic 4.16: Recording Panels

**Scope**
- Migrate Browser Recording and Recorded Actions to THEME_V2
- Recording workflow
- Action preview/edit

**Dependencies**
- Epic 1.1
- Epic 7.2 (Recording system)

**Done when**
- Panels use THEME_V2
- Recording starts/stops
- Actions appear in list
- Can edit recorded actions

**Manual test**
- Start recording, perform action
- Verify action appears in list
- Edit action, verify updates

**Rollback**
- Keep legacy recording panels

**Files**
- `ui/panels/browser_recording_panel.py`
- `ui/panels/recorded_actions_panel.py`

---

# Phase 5 — Context Menus

## Epic 5.1: Graph Context Menu

**Scope**
- Complete graph context menu using PopupWindowBase
- Cut, Copy, Paste, Duplicate, Delete
- Disable, Enable
- Edit Properties
- Create Frame
- Navigate to (subflows)
- Align, Distribute
- Auto Layout

**Dependencies**
- Epic 1.1 (need IMainWindow)
- Epic 3.1 (command system)
- Epic 4.x (panels for "add to frame" etc.)

**Done when**
- Context menu shows on right-click
- All actions wired to controllers
- Menu uses THEME_V2
- Icons use IconProviderV2

**Manual test**
- Right-click graph, verify menu appears
- Click each action, verify executes

**Rollback**
- Unbind right-click; use legacy menu

**Files**
- `ui/widgets/popups/context_menu_v2.py` (extend existing)

---

## Epic 5.2: Node Context Menu

**Scope**
- Node-specific context menu
- Port-specific actions
- Node enable/disable
- Properties
- Delete

**Dependencies**
- Epic 5.1 (reuse context menu infrastructure)

**Done when**
- Node menu shows on right-click
- All actions work
- Port actions show on port right-click

**Manual test**
- Right-click various node types
- Verify correct actions appear

**Rollback**
- Use legacy node menu

**Files**
- `ui/widgets/popups/node_context_menu_v2.py` (NEW or extend)

---

# Phase 6 — Dialog Migrations

**Dialogs can be migrated in parallel** - each dialog is independent.

**All dialogs depend on**:
- Epic 7.1 (BaseDialogV2 must exist) - see UX_REDESIGN_PLAN.md
- Epic 1.1 (IMainWindow interface)

## Epic 6.1: Preferences Dialog

**Scope**
- Create PreferencesDialogV2 using BaseDialogV2
- Migrate all preference pages
- Use v2 form components

**Dependencies**
- Epic 7.1 (BaseDialogV2)
- Epic 1.1

**Pages**:
- General, Theme, Editor, Execution, Autosave, Keymaps, Advanced

**Done when**
- Dialog uses BaseDialogV2
- All pages migrate to THEME_V2
- Form components use v2 primitives
- Settings persist to QSettings

**Manual test**
- Open dialog, navigate tabs
- Change settings, verify persist

**Rollback**
- Keep legacy PreferencesDialog

**Files**
- `ui/dialogs_v2/preferences_dialog_v2.py` (NEW)

---

## Epic 6.2: Node Properties Dialog

**Scope**
- Create NodePropertiesDialogV2 using BaseDialogV2
- Migrate all property editors
- Dynamic form generation from node schema

**Dependencies**
- Epic 7.1 (BaseDialogV2)
- Epic 1.1

**Done when**
- Dialog uses BaseDialogV2
- Property editors use v2 components
- Schema-driven form generation
- Validation works

**Manual test**
- Open properties for various node types
- Edit values, verify propagate

**Rollback**
- Keep legacy NodePropertiesDialog

**Files**
- `ui/dialogs_v2/node_properties_dialog_v2.py` (NEW)

---

## Epic 6.3: Project Manager Dialog

**Scope**
- Create ProjectManagerDialogV2 using BaseDialogV2
- Project CRUD operations
- Recent projects list

**Dependencies**
- Epic 7.1 (BaseDialogV2)
- Epic 1.1
- Epic 4.1 (Project Explorer panel)

**Done when**
- Dialog uses BaseDialogV2
- Can create/open/delete/rename projects
- Recent projects list shows

**Manual test**
- Create project, verify appears
- Delete project, verify removes

**Rollback**
- Keep legacy ProjectManagerDialog

**Files**
- `ui/dialogs_v2/project_manager_dialog_v2.py` (NEW)

---

## Epic 6.4: Hotkey Manager Dialog

**Scope**
- Create HotkeyManagerDialogV2 using BaseDialogV2
- Edit all shortcuts
- Conflict detection

**Dependencies**
- Epic 7.1 (BaseDialogV2)
- Epic 1.1
- Epic 2.2 (HotkeyManagerV2)

**Done when**
- Dialog uses BaseDialogV2
- Can edit shortcuts
- Conflicts detected and shown
- Changes persist

**Manual test**
- Change shortcut, verify updates
- Create conflict, verify warning

**Rollback**
- Keep legacy hotkey dialog (or Epic 2.2's editor)

**Files**
- `ui/dialogs_v2/hotkey_manager_dialog_v2.py` (NEW or merge with 2.2)

---

## Epic 6.5: Other Dialogs

**Scope**
- Migrate remaining dialogs to v2

**Dependencies**
- Epic 7.1 (BaseDialogV2)
- Epic 1.1

**Dialogs**:
- Workflow Settings
- Credential Manager
- Quick Node Config
- Fleet Dashboard
- Performance Dashboard
- Breakpoint Edit
- Subworkflow Picker
- Cron Builder
- Environment Editor

**Done when**
- All dialogs use BaseDialogV2
- All use THEME_V2
- Form components use v2 primitives

**Manual test**
- Open each dialog, verify styling
- Test main actions

**Rollback**
- Keep legacy versions

**Files** (each can be separate epic or batch):
- `ui/dialogs_v2/workflow_settings_dialog_v2.py`
- `ui/dialogs_v2/credential_manager_dialog_v2.py`
- `ui/dialogs_v2/quick_node_config_dialog_v2.py`
- `ui/dialogs_v2/fleet_dashboard_v2.py`
- `ui/dialogs_v2/performance_dashboard_v2.py`
- `ui/dialogs_v2/breakpoint_edit_dialog_v2.py`
- `ui/dialogs_v2/subworkflow_picker_dialog_v2.py`
- `ui/dialogs_v2/cron_builder_dialog_v2.py`
- `ui/dialogs_v2/environment_editor_v2.py`

---

# Phase 7 — Advanced Features

## Epic 7.1: Debug Mode

**Scope**
- Debug toolbar integration
- Breakpoint management UI
- Step controls (Step Over, Step Into, Step Out)
- Watch expressions
- Call stack display

**Dependencies**
- Epic 4.8 (Debug panel)
- Epic 4.9 (Breakpoints panel)
- Epic 1.1

**Done when**
- Debug toolbar shows/hides
- Step controls work
- Breakpoints visual in graph
- Watch expressions evaluate

**Manual test**
- Set breakpoint, run workflow
- Step through, verify execution flow
- Add watch, verify value updates

**Rollback**
- Disable debug mode UI; keep backend

**Files**
- `ui/toolbars/debug_toolbar_v2.py` (NEW or refactor)
- Debug controller integration

---

## Epic 7.2: Recording System

**Scope**
- Browser recording integration
- Desktop recording integration
- Recording toolbar
- Action preview/edit
- Workflow generation from recording

**Dependencies**
- Epic 4.16 (Recording panels)
- Epic 1.1

**Done when**
- Recording toolbar shows/hides
- Can start/stop recording
- Recorded actions appear in panel
- Can generate workflow from actions

**Manual test**
- Start recording, perform browser action
- Verify action appears
- Generate workflow, verify creates nodes

**Rollback**
- Disable recording UI; keep backend

**Files**
- `ui/toolbars/recording_toolbar_v2.py` (NEW or refactor)
- Recording controller integration

---

## Epic 7.3: Element Picker

**Scope**
- SelectorController refactor to v2
- UnifiedSelectorDialogV2
- Browser picker integration
- Desktop picker integration
- Recording integration

**Dependencies**
- Epic 7.1 (BaseDialogV2)
- Epic 1.1
- Epic 7.2 (Recording system)

**Done when**
- UnifiedSelectorDialogV2 uses BaseDialogV2
- Browser picker highlights elements
- Desktop picker highlights elements
- Selected selector inserts into property

**Manual test**
- Open picker, select element
- Verify selector appears in property

**Rollback**
- Keep legacy selector dialogs

**Files**
- `selectors/unified_selector_dialog_v2.py` (NEW or refactor)
- `selectors/selector_controller_v2.py` (NEW or refactor)

---

## Epic 7.4: Quick Node Mode

**Scope**
- Hotkey-driven node creation
- Configuration dialog
- Integration with node registry

**Dependencies**
- Epic 3.1 (Command palette)
- Epic 6.2 (Node Properties)
- Epic 1.1

**Done when**
- Press hotkey, node picker appears
- Type to filter nodes
- Select node, places on graph
- Config dialog opens

**Manual test**
- Press quick node hotkey
- Type node name
- Select, verify appears on graph

**Rollback**
- Unbind hotkey; disable feature

**Files**
- `ui/widgets/popups/quick_node_picker_v2.py` (NEW)
- Controller integration

---

## Epic 7.5: Auto Features

**Scope**
- Auto connect mode
- Auto layout
- Grid snap
- Frame creation

**Dependencies**
- Epic 1.1
- Epic 5.1 (Context menu for frame creation)

**Done when**
- Auto connect toggle works
- Auto layout arranges nodes
- Grid snap toggles
- Frame selection creates frame

**Manual test**
- Enable auto connect, drag between ports
- Enable grid snap, move node
- Select nodes, create frame

**Rollback**
- Disable auto features; keep manual

**Files**
- Controller integrations (no new files likely)

---

# Phase 8 — Final Integration

## Epic 8.1: Layout Persistence

**Scope**
- Save/restore dock layout
- Save/restore panel states
- Save/restore window geometry
- Reset layout functionality

**Dependencies**
- All panel epics complete (Epic 4.x)
- Epic 1.1

**Done when**
- Layout saves on close
- Layout restores on open
- Reset layout returns to default
- Panel visibility persists

**Manual test**
- Rearrange panels, close app
- Reopen, verify layout restores
- Reset layout, verify returns to default

**Rollback**
- Disable persistence; use default layout

**Files**
- `new_main_window.py` (add save/restore methods)

---

## Epic 8.2: Autosave

**Scope**
- Workflow autosave integration
- Project autosave integration
- Recovery on crash

**Dependencies**
- Epic 1.1

**Done when**
- Workflow autosaves periodically
- Project autosaves on change
- Recovery dialog shows after crash
- Can recover lost work

**Manual test**
- Make changes, wait for autosave
- Kill app, reopen
- Verify recovery dialog appears

**Rollback**
- Disable autosave; keep manual save

**Files**
- Autosave controller integration

---

## Epic 8.3: Recent Files

**Scope**
- Recent files manager
- Menu integration
- Persistence to QSettings

**Dependencies**
- Epic 2.1 (Menu bar)
- Epic 1.1

**Done when**
- Recent files list updates on open
- Menu shows recent files
- Click recent file opens it
- Persists across sessions

**Manual test**
- Open files, verify recent list updates
- Click recent file, verify opens
- Restart app, verify list persists

**Rollback**
- Hide recent files submenu

**Files**
- Recent files manager (may already exist)
- Menu integration

---

## Epic 8.4: Signal Coordination

**Scope**
- Create SignalCoordinatorV2
- Wire all actions
- Test all signal flows

**Dependencies**
- All previous phases (signals from all components)

**Done when**
- SignalCoordinatorV2 exists
- All actions wired correctly
- No orphaned signals
- No signal loops

**Manual test**
- Trigger each action, verify correct response
- Check for memory leaks in signals

**Rollback**
- Keep legacy signal coordinator

**Files**
- `coordinators/signal_coordinator_v2.py` (NEW or refactor)

---

## Epic 8.5: Cutover

**Scope**
- Make NewMainWindow the default
- Keep v1 behind flag temporarily
- Update documentation
- Final testing

**Dependencies**
- ALL previous epics complete

**Done when**
- NewMainWindow launches by default
- All features work
- Legacy only accessible via flag
- Documentation updated

**Manual test**
- Launch app, verify v2 opens
- Test full workflow: create, edit, run, save
- Test all major features

**Rollback**
- Switch flag back to v1 default

**Files**
- `app.py` (change default)
- Documentation updates

---

## Testing Checklist (Every Epic)

- [ ] Uses THEME_V2/TOKENS_V2 only (no legacy THEME)
- [ ] Uses IconProviderV2 for icons
- [ ] Uses BaseDialogV2 for dialogs (where applicable)
- [ ] Uses PopupWindowBase for popups (where applicable)
- [ ] Uses v2 form components (where applicable)
- [ ] Controllers use IMainWindow interface
- [ ] All signal/slot connections use @Slot decorator
- [ ] No lambdas (use functools.partial)
- [ ] Error handling with loguru
- [ ] Tests passing
- [ ] Manual tests documented
- [ ] Rollback plan exists

---

## Progress Tracking

| Phase | Epic | Status | Dependencies |
|-------|------|--------|--------------|
| 0 | 0.1 Dependency Setup | ⏳ | None |
| 1 | 1.1 Controller Interface | ⏳ | None |
| 1 | 1.2 ActionManager | ⏳ | 1.1 |
| 1 | 1.3 MenuBuilder | ⏳ | 1.1, 1.2 |
| 2 | 2.1 Menu Bar | ⏳ | 1.3 |
| 2 | 2.2 Shortcuts | ⏳ | 1.2 |
| 3 | 3.1 Remove Command Palette | ⏳ | None |
| 3 | 3.2 Node Search | ⏳ | 1.1 |
| 4 | 4.1 Project Explorer | ⏳ | 1.1, 2.1 |
| 4 | 4.2 Variables | ⏳ | 1.1 |
| 4 | 4.3 Output | ⏳ | 1.1 |
| 4 | 4.4 Log | ⏳ | 1.1 |
| 4 | 4.5 Terminal | ⏳ | 1.1 |
| 4 | 4.6 Validation | ⏳ | 1.1 |
| 4 | 4.7 History | ⏳ | 1.1 |
| 4 | 4.8 Debug | ⏳ | 1.1, 4.9 |
| 4 | 4.9 Breakpoints | ⏳ | 1.1 |
| 4 | 4.10 Minimap | ⏳ | 1.1 |
| 4 | 4.11 Process Mining | ⏳ | 1.1 |
| 4 | 4.12 Analytics | ⏳ | 1.1 |
| 4 | 4.13 Robot Picker | ⏳ | 1.1 |
| 4 | 4.14 Job Queue | ⏳ | 1.1 |
| 4 | 4.15 Credentials | ⏳ | 1.1 |
| 4 | 4.16 Recording | ⏳ | 1.1, 7.2 |
| 5 | 5.1 Graph Context Menu | ⏳ | 1.1, 3.1, 4.x |
| 5 | 5.2 Node Context Menu | ⏳ | 5.1 |
| 6 | 6.1 Preferences | ⏳ | 7.1, 1.1 |
| 6 | 6.2 Node Properties | ⏳ | 7.1, 1.1 |
| 6 | 6.3 Project Manager | ⏳ | 7.1, 1.1, 4.1 |
| 6 | 6.4 Hotkey Manager | ⏳ | 7.1, 1.1, 2.2 |
| 6 | 6.5 Other Dialogs | ⏳ | 7.1, 1.1 |
| 7 | 7.1 Debug Mode | ⏳ | 4.8, 4.9, 1.1 |
| 7 | 7.2 Recording System | ⏳ | 4.16, 1.1 |
| 7 | 7.3 Element Picker | ⏳ | 7.1, 1.1, 7.2 |
| 7 | 7.4 Quick Node Mode | ⏳ | 3.1, 6.2, 1.1 |
| 7 | 7.5 Auto Features | ⏳ | 1.1, 5.1 |
| 8 | 8.1 Layout Persistence | ⏳ | All 4.x |
| 8 | 8.2 Autosave | ⏳ | 1.1 |
| 8 | 8.3 Recent Files | ⏳ | 2.1, 1.1 |
| 8 | 8.4 Signal Coordination | ⏳ | All previous |
| 8 | 8.5 Cutover | ⏳ | ALL |

---

**Total Epics**: 40+
**Total Estimated Files**: 80+
**Parallel Opportunities**: Phases 4, 5, 6, 7 can have concurrent sessions
