# Epic V2: Full Migration + Legacy Deletion (Single Source of Truth) — CasareRPA

**Created**: 2025-12-30
**Use this file**: This is the single plan to follow. The other v2 migration/deletion plan files are now reference-only.

## Goal
1) Finish migrating all UI/features to `NewMainWindow` (v2) with parity.
2) Cut over so v2 is default.
3) Delete legacy (v1) UI code safely in phases.

## Hard Requirements
- Qt-only (PySide6)

- Dock-only (no floating docks)
- Dark-only + compact density
- No animations and no drop shadows
- **No command palette** (explicit decision)

## Decision Log
- **2025-12-30: Command palette will NOT ship.** Remove both legacy and v2 implementations and all bindings.

## “Done” Definitions

### Migration Done (Cutover-Ready)
- V2 has real panels (no placeholder docks / stub methods)
- Undo/redo/cut/copy/paste/delete/select-all work in v2
- Workflow: new/open/reload/save/save-as works
- Run: run/pause/stop/restart/run-to-node/run-single-node works
- Validation works (auto + manual) and navigates to nodes
- Layout persistence works with real docks
- Dock-only is enforced across all docks
- V2 runtime path has no dependency on legacy `MainWindow` modules

### Deletion Done
- No remaining runtime imports or references to legacy UI modules
- App launches and passes smoke tests with v2 as the only UI

---

# Part A — Full Migration to V2 (Phases)

## Phase A0 — Parallel Entry + Guardrails

### Epic A0.1 — V2 entry flag + run modes ✅ COMPLETE
**Story**: As a developer, I can launch v2 without breaking v1 while migration is in progress.

**Acceptance**
- `CASARE_UI_V2=1` launches v2
- v1 remains available until cutover

**To do**
- [x] Ensure v2 launch path is stable on a clean environment
- [x] Document run modes (dev + packaged) in `README.md` or `docs/`

### Epic A0.2 — Parity checklist harness ✅ COMPLETE
**Story**: As QA/dev, I can verify parity via a repeatable checklist.

**To do**
- [x] Create a manual QA checklist (launch, workflow lifecycle, run controls, panels, layout persistence)
- [x] Define “Cutover-Ready” gate (see Part C)

---

## Phase A1 — V2 Design System Compliance

### Epic A1.1 — THEME_V2/TOKENS_V2-only in v2 runtime ✅ COMPLETE
**Story**: As a developer, the v2 UI has zero hidden dependencies on legacy `THEME`.

**To do**
- [x] Audit `new_main_window.py` and `ui/` for non-V2 theme imports
- [x] Ensure all v2 components use `THEME_V2` or `TOKENS_V2`

### Epic A1.2 — Fonts bundling validated ✅ COMPLETE
**Story**: As a user, the UI uses Geist Sans/Mono even if not installed on the OS.

**To do**
- [x] Verify `ensure_font_registered()` is called in `app.py`
- [x] Verify Geist font registration works after `QApplication` creation

### Epic A1.3 — Global QSS instead of per-widget setup ✅ COMPLETE
**Story**: As a developer, I can change the entire app's look by editing one file.

**To do**
- [x] Apply `get_canvas_stylesheet_v2()` to `NewMainWindow`
- [x] Reduce usage of per-widget `setStyleSheet()` in favor of object names/selectors

### Epic A1.4 — Geist fonts bundling ✅ COMPLETE
**Story**: As a developer, the fonts are distributed with the source.

**To do**
- [x] Add font files to `src/casare_rpa/resources/fonts/` (verified 38 files present)

---

## Phase A2 — Icons v2

### Epic A2.1 — IconProviderV2-only in v2 chrome ✅ COMPLETE
**Story**: As a user, icons are consistent across menus/toolbars.

**Acceptance**
- v2 chrome uses IconProviderV2 exclusively
- Legacy icon pipelines are removed

**To do**
- [x] Ensure v2 chrome uses IconProviderV2 exclusively
- [x] Remove legacy icon pipelines from v2 runtime path (ToolbarIcons, manual drawing)

**Files Updated**:
- `icons.py`: Consolidated as a thin wrapper around v2 icon system; removed legacy code.
- `icons_v2_adapter.py`: Removed USE_V2_ICONS flag/logic; added missing mappings for AI and credentials.
- `file_path_widget.py`: Switched from system icons to v2 Lucide icons.
- `menu_builder.py`: Removed v2-enabled checks; icons are now always v2.

**Verification**
- [x] `rg "USE_V2_ICONS" src/casare_rpa/presentation/canvas` — 0 results (2025-12-30)
- [x] `rg "ToolbarIcons|StandardPixmap" src/casare_rpa/presentation/canvas` — 0 results (except for comments or adapter code)

---

## Phase A3 — Search + Popups (No Command Palette)

### Epic A3.1 — Remove command palette (v1 + v2) ✅ COMPLETE
**Story**: As a user, there is no command palette feature in v2.

**Acceptance**
- Ctrl+Shift+P does not open any palette (now Project Manager)
- No command palette code remains in presentation/canvas runtime

**To do**
- [x] Delete legacy palette: `src/casare_rpa/presentation/canvas/search/command_palette.py`
- [x] Delete v2 palette: `src/casare_rpa/presentation/canvas/ui/widgets/popups/command_palette_v2.py`
- [x] Remove Ctrl+Shift+P wiring from v2 window
- [x] Remove menu/controller wiring for “open command palette”
- [x] Remove `IMainWindow.get_command_palette()` and call sites

**Verification**
- [x] `rg "command[_ ]palette|CommandPalette" src/casare_rpa/presentation/canvas` — returns 0 active usages (2025-12-30)
- [x] Verified `main_window.py` code removed.
- [x] Verified `SignalCoordinator.py` code removed.
- [x] Verified `MenuController.py` code removed.

### Epic A3.2 — Node Search canonicalization (pick ONE implementation) ✅ COMPLETE
**Story**: As a user, Ctrl+F opens node search and selects/navigates reliably.

**To do**
- [x] Choose canonical NodeSearchV2 implementation: `src/casare_rpa/presentation/canvas/ui/widgets/popups/node_search_v2.py`
- [x] Remove/merge the duplicate implementation in `search/`
- [x] Ensure `NewMainWindow` uses the canonical implementation for Ctrl+F

---

## Phase A4 — V2 Shell Becomes Real (No stubs/placeholders)

### Epic A4.1 — Replace placeholder docks with real panels ✅ COMPLETE
**Story**: As a user, v2 shows the same panels as v1.

**Acceptance**
- No “Coming soon” placeholder docks
- Real docks exist and are wired to menu toggles

**To do**
- [x] Create/own v2 docks for: bottom panel, side panel, project explorer, properties/inspector
- [x] Implement panel getters (`get_bottom_panel`, `get_side_panel`, etc.) to return real instances

### Epic A4.2 — Real QAction plumbing in v2 ✅ COMPLETE
**Story**: As a user, editing actions work and shortcuts behave like v1.

**Acceptance**
- `app.py` connects to actual `QAction` objects in v2
- Undo stack enables/disables undo/redo correctly

**To do**
- [x] Remove stub action pattern in v2
- [x] Register/add actions to window so shortcuts work globally (via ActionManagerV2)
- [x] Ensure menu/toolbar items map to the same underlying actions

### Epic A4.3 — Controller parity in v2 startup ✅ COMPLETE
**Story**: As a user, features driven by controllers exist in v2.

**To do**
- [x] Instantiate/initialize v1-era “MainWindow-owned” controllers for v2 (handled in `app.py` and `NewMainWindow.set_controllers`)
- [x] Ensure controllers depend on `IMainWindow` (verified for core controllers)

### Epic A4.4 — Remove direct legacy coupling in graph + serialization ✅ COMPLETE
**Story**: As a developer, core graph/serialization works under v2 with no `MainWindow`-specific hacks.

**To do**
- [x] Replace `isinstance(MainWindow)` checks with generic window discovery or Protocol (verified in serializers)
- [x] Replace serializer/deserializer `_bottom_panel` attribute peeks with interface/provider calls (`get_variables`)
- [x] Decouple `WorkflowSerializer`/`WorkflowDeserializer` via `IMainWindow` protocol

---

## Phase A5 — Dock-only Enforcement Everywhere

### Epic A5.1 — Dock widgets are not floatable in v2 ✅ COMPLETE
**Story**: As a user, all panels remain docked within the main window.

**To do**
- [x] Remove `DockWidgetFloatable` from all docks used in v2
- [x] Ensure no code path re-enables floating

**Verification**
- [x] Audit: `rg "DockWidgetFloatable" src/casare_rpa/presentation/canvas/ui` — 0 active usages (only comments)
- [x] Application launches and runs with dock-only enforcement (2025-12-30)

---

## Phase A6 — Dialogs (BaseDialogV2 everywhere)

### Epic A6.1 — Migrate remaining dialogs 🚧 IN PROGRESS
**Story**: As a user, all dialogs feel consistent with the v2 design system.

**To do**
- [x] List all remaining v1 dialogs (`ui/dialogs/` audit)
- [ ] Migrate critical dialogs (Preferences, AI Config, Credential selection)
- [ ] Ensure all use `BaseDialogV2`

**Remaining v1 Dialogs:**
- [x] `BreakpointEditDialog`
- [x] `CredentialManagerDialog`
- [x] `CronBuilderDialog`
- [x] `GoogleOAuthDialog` (BaseDialogV2 with THEME_V2)
- [x] `LoginDialog`
- [x] `MFASetupDialog`
- [x] `NodePropertiesDialog`
- [x] `ParameterPromotionDialog`
- [x] `PreferencesDialog`
- [x] `ProjectManagerDialog`
- [x] `QuickNodeConfigDialog`
- [x] `RecordingDialog`
- [x] `RecordingReviewDialog`
- [x] `RemoteRobotDialog`
- [x] `SubflowPickerDialog`
- [x] `UpdateDialog`
- [x] `WorkflowSettingsDialog`
- [x] `FleetDashboard` (BaseDialogV2 with THEME_V2)
- [x] `EnvironmentEditor`
- [x] `ProjectWizard`

---

## Phase A7 — No-Animation/No-Shadow (Global)
- [x] Verify no `QPropertyAnimation` or `QGraphicsDropShadowEffect` remains in `presentation/canvas`.
- [x] Ensure `BaseDialogV2` and `ToastV2` relying solely on `QTimer` or instant state changes.

**To do**
- [x] Remove remaining `QPropertyAnimation/QEasingCurve` usage in canvas UI paths
- [x] Confirm policy for non-canvas UI (if any) and align

**Files Updated**:
- `chat_area.py`: Removed scroll animation, now uses instant scroll
- `node_aligner.py`: Removed all animation code, positions change instantly
- `custom_pipe.py`: Removed flow animation (animated dot), uses static execution state
- `custom_node_item.py`: Removed AnimationCoordinator timer, uses static indicators

**Verification**
- [x] `rg "QPropertyAnimation|QVariantAnimation|QEasingCurve|QGraphicsDropShadowEffect" src/casare_rpa/presentation/canvas` — only comments remain (2025-12-30)

---

# Part B — Cutover

## Phase B0 — Make v2 default with a temporary escape hatch

### Epic B0.1 — Cutover to v2 default ✅ COMPLETE
**Story**: As a user, the app opens v2 by default.

**To do**
- [x] Make v2 the default startup path (verified in `app.py`)
- [x] Keep v1 behind an explicit fallback flag for one release (`CASARE_UI_V1=1`)

---

# Part C — Legacy Deletion (Phased)

## Phase C0 — Inventory + Deletion Map

### Epic C0.1 — Identify v1-only surface area
**Story**: As a developer, I can delete legacy code without breaking imports.

**To do**
- [ ] Create a “deletion map” (module → importers)
- [ ] Confirm which packages are v1-only

---

## Phase C1 — Delete Command Palette (Required)

### Epic C1.1 — Ensure palette code is gone ✅ COMPLETE
**To do**
- [x] Delete v1 palette module
- [x] Delete v2 palette module
- [x] Remove bindings, interfaces, call sites

**Verification**
- [x] `rg "command[_ ]palette|CommandPalette" src/casare_rpa/presentation/canvas` — returns 0 active usages (2025-12-30)

---

## Phase C2 — Remove v1 entry wiring and convenience modules

### Epic C2.1 — Remove v1-only entrypoints
**To do**
- [ ] Remove any “v1 convenience entry” modules not needed
- [ ] Ensure docs point only to v2

---

## Phase C3 — Delete legacy coordinators/managers/components/initializers

### Epic C3.1 — Delete v1-only infrastructure
**To do**
- [ ] Remove legacy coordinator (`SignalCoordinator`) if v2 does not use it
- [ ] Remove legacy `PanelManager` if v2 owns panels directly
- [ ] Remove `components/*` v1 builders
- [ ] Remove `initializers/*`

**Verification**
- [ ] `rg "presentation\.canvas\.components" src`
- [ ] `rg "presentation\.canvas\.initializers" src`

---

## Phase C4 — Delete legacy main window

### Epic C4.1 — Delete `MainWindow`
**To do**
- [ ] Delete `src/casare_rpa/presentation/canvas/main_window.py`
- [ ] Remove leftover type-hint imports

**Verification**
- [ ] `rg "\\bMainWindow\\b" src/casare_rpa/presentation/canvas` returns 0

---

## Phase C5 — Packaging + Runtime Validation

### Epic C5.1 — Build and smoke-test
**To do**
- [ ] Run tests
- [ ] Run v2 smoke test script
- [ ] Validate packaged build launches and core flows work

---

## Phase C6 — Remove escape hatch

### Epic C6.1 — Remove v1 fallback completely
**To do**
- [ ] Remove `CASARE_UI_V2` fallback logic
- [ ] Make v2 the only UI

---

## Final Verification Checklist
- [ ] App launches (v2)
- [ ] New/open/save/save-as/reload work
- [ ] Run/pause/stop/restart/run-to-node/run-single-node work
- [ ] Panels work and are dock-only
- [ ] Layout persistence works
- [ ] `rg "MainWindow|main_window\.py|PanelManager|SignalCoordinator" src/casare_rpa/presentation/canvas` finds nothing relevant
