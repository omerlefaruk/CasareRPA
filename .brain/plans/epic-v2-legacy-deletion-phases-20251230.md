# Epic V2: Legacy UI Deletion (Phased) — CasareRPA

**Created**: 2025-12-30
**Goal**: Remove all legacy (v1) UI codepaths after v2 reaches parity and becomes default, without breaking runtime imports.

## Preconditions (must be true before deletion begins)
- [ ] V2 is default launch path
- [ ] V1 remains available only behind an escape hatch for one release
- [ ] Cutover readiness checklist completed (see migration plan)
- [ ] Parity verified on at least one packaged build and one dev run

## Safety Rules
- Delete in small batches with a clean build/test after each batch
- Keep a rollback branch/tag before starting hard deletions
- Never delete a module until `rg` shows no runtime imports

---

# Phase D0 — Inventory + Deletion Map

## Epic D0.1 — Identify v1-only surface area
**To do**
- [ ] Produce a list of v1-only entrypoints
- [ ] Produce a list of v1-only packages
- [ ] Produce a list of v1-only tests

**Candidates (expected v1-only; confirm with ripgrep)**
- `src/casare_rpa/presentation/canvas/main_window.py`
- `src/casare_rpa/presentation/canvas/components/`
- `src/casare_rpa/presentation/canvas/initializers/`
- `src/casare_rpa/presentation/canvas/coordinators/signal_coordinator.py`
- `src/casare_rpa/presentation/canvas/managers/panel_manager.py` (keep `popup_manager.py`)
- `src/casare_rpa/presentation/canvas/search/command_palette.py` (legacy command palette)
- `src/casare_rpa/presentation/canvas/ui/widgets/popups/command_palette_v2.py` (v2 command palette)
- `src/casare_rpa/presentation/canvas/search/node_search.py` (legacy)

---

# Phase D1 — Deprecation + Redirects

## Epic D1.1 — Remove legacy entry wiring
**To do**
- [ ] Update `app.py` so v1 is only reachable by explicit flag (or remove entirely after grace period)
- [ ] Remove any “v1 convenience entry” modules (e.g. `presentation/canvas/main.py` if unused)

## Epic D1.2 — Remove v1-only public imports
**To do**
- [ ] Update package `__init__.py` exports to stop exposing v1-only symbols
- [ ] Update docs to point to v2 window and v2 UI packages

---

# Phase D2 — Delete Legacy Modules (Top-Down)

## Epic D2.1 — Delete legacy coordinators/managers/components
**To do**
- [ ] Remove `SignalCoordinator` (if v2 does not use it)
- [ ] Remove `PanelManager` (if v2 has direct panel ownership)
- [ ] Remove `components/*` v1 builders (ActionManager/MenuBuilder/ToolbarBuilder/etc)
- [ ] Remove `initializers/*` (ControllerRegistrar/UIComponentInitializer)

**Verification**
- [ ] `rg "presentation\\.canvas\\.components" src`
- [ ] `rg "presentation\\.canvas\\.initializers" src`
- [ ] App launches and basic UI works

## Epic D2.2 — Delete legacy main window
**To do**
- [ ] Delete `main_window.py`
- [ ] Remove all leftover type-hint imports referencing MainWindow

**Verification**
- [ ] `rg "\\bMainWindow\\b" src/casare_rpa/presentation/canvas`

---

# Phase D3 — Delete Command Palette (Required)

## Epic D3.1 — Delete command palette (v1 + v2)
**To do**
- [ ] Delete `src/casare_rpa/presentation/canvas/search/command_palette.py`
- [ ] Delete `src/casare_rpa/presentation/canvas/ui/widgets/popups/command_palette_v2.py`
- [ ] Remove Ctrl+Shift+P shortcut wiring in v2 (`NewMainWindow`) and any menu action/signal wiring
- [ ] Remove `IMainWindow.get_command_palette()` and any controller call sites (e.g. menu controller)
- [ ] Verify: `rg "command[_ ]palette|CommandPalette" src/casare_rpa/presentation/canvas` returns 0

---

# Phase D4 — Cleanup Couplings + Tech Debt Removal

## Epic D4.1 — Remove legacy attribute reach-ins
**To do**
- [ ] Ensure serializer/deserializer no longer access `_bottom_panel` directly
- [ ] Ensure graph code does not depend on `isinstance(MainWindow)`

## Epic D4.2 — Remove v1-only theme usage in v2 runtime
**To do**
- [ ] `rg "from casare_rpa\\.presentation\\.canvas\\.theme_system import THEME\b"` and verify v2 runtime path does not use it

---

# Phase D5 — Packaging + Runtime Validation

## Epic D5.1 — Build verification
**To do**
- [ ] Run unit tests
- [ ] Run v2 smoke test script
- [ ] Produce a packaged build and validate launch

---

# Phase D6 — Remove Escape Hatch + Final Cleanup

## Epic D6.1 — Remove v1 fallback mode
**To do**
- [ ] Remove `CASARE_UI_V2` flag handling after grace period
- [ ] Make v2 the only UI

---

# Deletion Gate Checklist
- [ ] No imports of `main_window.py` remain
- [ ] No imports of `presentation.canvas.components` remain
- [ ] No imports of `presentation.canvas.initializers` remain
- [ ] No references to `SignalCoordinator` remain
- [ ] No v1-only tests remain
- [ ] App launches, can open/save/run workflows, panels work, layout persists

