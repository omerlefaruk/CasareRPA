# Epic V2: Full UI Migration (Phased) — CasareRPA

**Created**: 2025-12-30
**Audience**: Engineering
**Goal**: Move all UI + UI-adjacent behavior from legacy `MainWindow` to `NewMainWindow` (v2), reaching functional parity before deleting legacy UI.

## Scope

### In Scope
- V2 UI shell becomes fully functional (no placeholders/stubs)
- All user-facing UI features present in v1 are available in v2
- Controllers become window-agnostic (depend on `IMainWindow` only)
- Dock-only enforcement everywhere in v2
- V2 theme/tokens + icon system consistently used in v2

### Out of Scope (for this migration plan)
- New feature development not required for parity
- Domain/model refactors not required to support v2

## Hard Requirements (from `docs/UX_REDESIGN_PLAN.md`)
- Qt-only UI (PySide6)
- Dock-only (no floating docks)
- No animations (0ms) and no drop shadows
- Dark-only + compact density

## Decision Gates (must resolve before “Cutover Ready”)

### DG-1: Command Palette
`docs/UX_REDESIGN_PLAN.md` says “No command palette”, but code currently includes `CommandPaletteV2`.
- [x] **DECIDED: Remove command palette** (do not ship it in v2)
- [ ] Remove v2 command palette: `src/casare_rpa/presentation/canvas/ui/widgets/popups/command_palette_v2.py`
- [ ] Remove legacy command palette: `src/casare_rpa/presentation/canvas/search/command_palette.py`
- [ ] Remove Ctrl+Shift+P bindings and any “open command palette” menu items/signals
- [ ] Remove `IMainWindow.get_command_palette()` and any controller call sites that reference it
- [ ] Re-run static audit: `rg "command[_ ]palette|CommandPalette" src/casare_rpa/presentation/canvas`

### DG-2: Dock-only enforcement scope
- [ ] Confirm: *all* docks (bottom/side/debug/analytics/etc) must be non-floatable in v2
- [ ] Confirm policy for popups (draggable/resizable is allowed; they are not docks)

### DG-3: Animation policy scope
- [ ] Confirm: “no animations” means **no** `QPropertyAnimation/QVariantAnimation/QEasingCurve` anywhere in UI codepaths
- [ ] Decide exception policy (if any) for non-UI node dialogs

---

# Phase 0 — Parallel Entry + Guardrails

## Epic 0.1 — V2 entry flag + run modes
**User story**: As a developer, I can launch either v1 or v2 UI without breaking workflows.

**Acceptance**
- v2 enabled via env var (`CASARE_UI_V2=1`)
- v1 remains available as fallback until cutover

**To do**
- [ ] Confirm v2 entry is stable on fresh machine
- [ ] Add a visible “V2 UI” indicator in window title/status (already present; keep)
- [ ] Document run modes in README (or docs)

## Epic 0.2 — Parity checklist harness
**User story**: As QA/dev, I can verify parity via a repeatable checklist.

**To do**
- [ ] Define “parity complete” checklist (see “Cutover Gate” section below)
- [ ] Add manual QA script (steps + expected results)

---

# Phase 1 — Theme/Tokens/QSS Foundation (V2)

## Epic 1.1 — V2 tokens contract
**User story**: As a developer, I can change V2 tokens and see consistent UI changes without hunting hex strings.

**Acceptance**
- V2 screens use `THEME_V2/TOKENS_V2` (no `THEME/TOKENS`)
- No hardcoded hex in v2-only UI codepaths (allow category colors for node type maps if required)

**To do**
- [ ] Audit v2-only modules for `THEME` imports
- [ ] Replace remaining “legacy theme” usage in v2 UI entry path

## Epic 1.2 — Geist fonts bundled + validated
**User story**: As a user, the app renders consistently with Geist fonts in dev + packaged builds.

**To do**
- [ ] Ensure font loader resolves correct fonts path in dev + PyInstaller
- [ ] Verify typography preview test widget renders in Geist

## Epic 1.3 — Global QSS v2
**User story**: As a developer, baseline styling comes from one global QSS in v2 mode.

**To do**
- [ ] Identify v2 widgets still using per-widget `setStyleSheet()` for core primitives
- [ ] Replace per-widget styling with QSS where feasible (keep per-widget style only for truly custom cases)

---

# Phase 2 — Icon System v2

## Epic 2.1 — IconProviderV2 contract
**User story**: As a developer, I can request icons by name/state and get consistent glyphs.

**To do**
- [ ] Ensure `MenuBarV2/ToolbarV2` use IconProviderV2 exclusively
- [ ] Audit any remaining legacy icon pipelines in v2 paths

---

# Phase 3 — Popup Library v2

## Epic 3.1 — PopupWindowBase
**Status**: Exists; validate compliance.

**To do**
- [ ] Confirm click-outside close works consistently in v2 mode
- [ ] Confirm no shadows/animations in popup base

## Epic 3.2 — Popups consolidation
**User story**: As a developer, there is one canonical V2 node search implementation.

**To do**
- [ ] Remove/merge duplicate NodeSearchV2 implementations (`search/node_search_v2.py` vs `ui/widgets/popups/node_search_v2.py`)
- [ ] Ensure `NodeController.find_node()` uses the canonical implementation
- [ ] Remove any remaining references to command palette from popup exports / docs

---

# Phase 4 — V2 IDE Shell (Dock-only Workspace)

## Epic 4.1 — Replace placeholder docks with real panels
**User story**: As a user, the v2 shell provides the same panel surface area as v1.

**Acceptance**
- V2 window creates actual docks/panels (no placeholder “Coming soon”)
- Dock-only enforced (no floating)

**To do**
- [ ] Create/own v2 docks: Bottom, Side, Project Explorer, Properties/Inspector
- [ ] Wire v2 layout persistence to real docks
- [ ] Implement `IMainWindow` panel getters (`get_bottom_panel`, `get_side_panel`, etc) to return real instances

## Epic 4.2 — Action plumbing parity (QActions)
**User story**: As a user, undo/redo/cut/copy/paste/delete/select-all work the same in v2.

**Acceptance**
- `app.py` can connect to real `QAction`s in v2 (no stub action objects)
- Enable/disable states reflect undo stack and selection

**To do**
- [ ] Replace `StubAction` pattern in `NewMainWindow`
- [ ] Ensure actions are added to window so shortcuts work globally
- [ ] Ensure menu/toolbar actions map 1:1 to action layer

## Epic 4.3 — Controller parity in v2 startup
**User story**: As a user, all controllers that existed in v1 run in v2 mode.

**To do**
- [ ] Decide: instantiate MainWindow-era controllers in v2 OR create dedicated v2 coordinator layer
- [ ] Ensure these controllers exist in v2: PanelController, MenuController, ViewportController, UIStateController, ProjectController, RobotController, ProjectAutosaveController, EventBusController, ConnectionController
- [ ] Ensure controllers depend on `IMainWindow` and do not import `main_window.py`

## Epic 4.4 — Remove direct MainWindow coupling in graph/serialization
**User story**: As a developer, graph and serialization code works with v2 without `isinstance(MainWindow)` checks or `_bottom_panel` attribute peeks.

**To do**
- [ ] Replace `NodeGraphWidget._find_main_window()` type check with a generic `QMainWindow`/`IMainWindow` approach
- [ ] Replace serializer/deserializer “reach into `_bottom_panel`” with `IMainWindow.get_bottom_panel()` or a dedicated variables provider interface

---

# Phase 5 — Component Library v2 (Reusable Widgets)

## Epic 5.1 — Core primitives
**User story**: As a developer, I build panels/dialogs from a stable set of v2 primitives.

**To do**
- [ ] Confirm primitives cover all common needs (buttons/inputs/tables/list items/badges)
- [ ] Remove remaining ad-hoc widget styling in v2-only screens

## Epic 5.2 — Forms + validation patterns
**User story**: As a user, forms behave consistently (focus, errors, enter/esc semantics).

**To do**
- [ ] Standardize validation patterns and error display

---

# Phase 6 — Panel Migration (Functional, not just themed)

## Epic 6.0 — Panel wiring into v2 shell
**User story**: As a user, panels are accessible via View menu and remember layout.

**To do**
- [ ] Add panels to v2 docks
- [ ] Ensure View menu toggles call real show/hide logic (not stubs)

## Epic 6.1 — Bottom panel parity
**Panels**: Variables / Output / Log / Validation / History / Terminal

**To do**
- [ ] Ensure bottom panel exists in v2 mode and emits required signals
- [ ] Enforce dock-only (remove `DockWidgetFloatable`)

## Epic 6.2 — Side panel parity
**Panels**: Debug / Process Mining / Robot Picker / Analytics / Credentials (as applicable)

**To do**
- [ ] Ensure side panel exists in v2 mode
- [ ] Enforce dock-only (remove `DockWidgetFloatable`)

## Epic 6.3 — Project Explorer + Properties
**To do**
- [ ] Mount Project Explorer in left dock
- [ ] Mount Properties/Inspector in right dock (ensure property panel works)

---

# Phase 7 — Dialogs + Setup Wizard

## Epic 7.1 — BaseDialogV2 everywhere
**User story**: As a user, dialogs look/behave consistently in v2.

**To do**
- [ ] Migrate remaining dialogs not inheriting `BaseDialogV2` (OAuth dialogs, Project Wizard, Remote Robot, MFA setup, etc.)
- [ ] Remove legacy `dialog_styles.py` usage from v2 flows

## Epic 7.2 — Setup wizard v2 styling
**To do**
- [ ] Remove remaining hardcoded styling patterns and align with v2 tokens

## Epic 7.3 — Replace QMessageBox/QInputDialog in v2 flows
**To do**
- [ ] Convert blocking dialogs into v2 prompts/toasts where appropriate

---

# Phase 8 — Global No-Animation + No-Shadow Enforcement

## Epic 8.1 — Remove animations/shadows (global)
**Acceptance**
- `rg` for `QPropertyAnimation|QVariantAnimation|QEasingCurve|QGraphicsDropShadowEffect` returns 0 in UI paths

**To do**
- [ ] Remove remaining animations in graph + AI assistant scrolling
- [ ] Decide policy for non-UI node dialogs using animations

---

# Phase 9 — Cutover Gate

## Epic 9.1 — Cutover readiness criteria
**Cutover Ready when ALL are true**
- [ ] V2 has real panels (no placeholders/stubs)
- [ ] Undo/redo/cut/copy/paste/delete/select-all work
- [ ] Workflow open/save/save-as/reload work
- [ ] Run/pause/stop/restart/run-to-node/run-single-node work
- [ ] Validation panel works (auto + manual)
- [ ] Layout persistence works with real docks
- [ ] No v1-only UI modules imported in v2 runtime path
- [ ] Dock-only enforced across all docks

## Epic 9.2 — Make v2 default (v1 behind escape hatch)
**To do**
- [ ] Flip default startup to v2
- [ ] Keep `CASARE_UI_V2=0` as fallback for one release

---

# Phase 10 — Migration Verification Checklist (Operational)

## Static audits
- [ ] `rg "presentation\\.canvas\\.main_window" src/casare_rpa/presentation/canvas`
- [ ] `rg "isinstance\(.*MainWindow" src/casare_rpa/presentation/canvas`
- [ ] `rg "_bottom_panel" src/casare_rpa/presentation/canvas` (ensure only via interface/provider)

## Runtime smoke tests
- [ ] Launch v2
- [ ] Create workflow → save → reopen
- [ ] Add nodes → connect → run → stop
- [ ] Trigger validation issues → navigate to node
- [ ] Rearrange docks → restart → verify layout restore

