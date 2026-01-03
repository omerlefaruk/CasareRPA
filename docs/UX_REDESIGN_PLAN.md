# CasareRPA UX/UI Overhaul Plan (PySide6, Windows 10/11)

This is the implementation plan for a full UI redesign to a **Cursor/VS Code–like**, **dark-only**, **compact**, **dock-only IDE workspace** for power users. It is written to be **modular** so each epic can be implemented and tested independently, while still supporting a final “cutover” to the new UI.

---

## North Star

Build a fast, minimal, coherent IDE shell for an RPA power-user workflow:
- Dock-only panels (no floating), resizable splitters, tabbed docks, collapsible sidebars.
- Dark theme only, compact density similar to VS Code/Cursor.
- One accent color: **Cursor-like blue** (single complement) + neutral ramps.
- No animations anywhere (0ms). No drop shadows.
- One icon style: minimalist line icons, single color (plus neutral disabled).
- Fonts: **Geist Sans + Geist Mono** (bundled for PyInstaller), with clean fallbacks.

---

## Constraints (Hard Requirements)

- **Qt-only** UI (PySide6). No embedded web UI.
- **Dock-only**: no dock floating; panels must remain docked inside main window.
- **No command palette**: remove/disable command palette feature.
- **Popups**: can be draggable and resizable; still managed by centralized popup lifecycle.
- **Performance**: avoid costly effects; minimize repaints; keep startup fast.
- **Big-bang replacement (final cutover)**: legacy UI deleted/disabled only at the end, after the new UI is functionally complete.

---

## Current Repo Findings (Where UI Lives)

**Entry / App**
- App setup: `src/casare_rpa/presentation/canvas/app.py`
- Main window: `src/casare_rpa/presentation/canvas/main_window.py`

**Theme System (already exists, but needs alignment)**
- Colors: `src/casare_rpa/presentation/canvas/theme/colors.py`
- Tokens: `src/casare_rpa/presentation/canvas/theme/design_tokens.py`
- QSS generators: `src/casare_rpa/presentation/canvas/theme/styles.py`

**UI Surface Area**
- Panels: `src/casare_rpa/presentation/canvas/ui/panels/`
- Dialogs: `src/casare_rpa/presentation/canvas/ui/dialogs/`
- Widgets: `src/casare_rpa/presentation/canvas/ui/widgets/`
- Toolbars: `src/casare_rpa/presentation/canvas/ui/toolbars/`

**Popup foundation already present**
- Click-outside: `src/casare_rpa/presentation/canvas/managers/popup_manager.py`

**Known policy conflicts**
- Animations/shadows exist today in multiple areas (must be removed).
- Hardcoded hex styles exist (notably `src/casare_rpa/presentation/setup/setup_wizard.py` and `src/casare_rpa/presentation/canvas/ui/base_widget.py`).

---

## Delivery Strategy (Modular + Testable)

We’ll build the new “UX framework” in parallel with legacy UI and ship it behind a **feature flag / alternate entry path**, then switch the default at the end.

- Each epic has:
  - Scope
  - Dependencies
  - “Done when”
  - Quick manual tests
  - Rollback plan

---

# Phase 0 — Foundations for Safe Iteration

## Epic 0.1: Create a parallel UI entry (“new shell”) without breaking legacy
**Scope**
- Add a new startup path that opens a “NewMainWindow” shell, while keeping the current `MainWindow` available.

**Dependencies**
- None

**Done when**
- App can launch either old or new shell using an env var/config flag (e.g., `CASARE_UI_V2=1`).

**Manual test**
- Run app in both modes; ensure it starts and closes cleanly.

**Rollback**
- Remove the flag path and keep legacy default.

---

# Phase 1 — Design System v2 (Tokens + Fonts + QSS)

## Epic 1.1: Token spec v2 (dark-only, compact)
**Scope**
- Define an explicit v2 token contract:
  - Colors: neutral ramps + Cursor-blue accent ramp + semantic status.
  - Typography: sizes/weights/line-height for compact UI.
  - Spacing: 4px grid with tight presets.
  - Radii: small, consistent.
  - Borders: always 1px; focus ring rules.
  - Motion: explicitly **none** (0ms).

**Dependencies**
- Phase 0 complete (so we can test in new shell).

**Done when**
- There is a single source of truth used by both QSS and custom-painted widgets.

**Manual test**
- Token change visibly updates the new shell without hunting down hex strings.

**Rollback**
- Keep v2 tokens unused; no impact on legacy.

## Epic 1.2: Font bundling + loader for PyInstaller (Geist Sans/Mono)
**Scope**
- Add `assets/fonts/` with Geist Sans + Geist Mono.
- Implement font registration at app start (before UI creation).
- Define fallbacks: Segoe UI + Cascadia Code.

**Dependencies**
- Epic 1.1 (typography tokens)

**Done when**
- New shell renders in Geist, both on dev runs and in a PyInstaller build.

**Manual test**
- Verify font family/metrics in a “Typography preview” screen.

**Rollback**
- Fall back to system fonts only.

## Epic 1.3: Global QSS v2 generated from tokens (no per-widget setStyleSheet)
**Scope**
- Generate one global QSS for the entire app (new shell mode).
- Ensure common Qt widgets are styled consistently:
  - QMainWindow/QDockWidget/QTabBar/QMenu/QToolBar/QStatusBar
  - Inputs, comboboxes, checkboxes
  - Scrollbars, headers, tables

**Dependencies**
- Epic 1.1

**Done when**
- In new shell mode, there are no ad-hoc `setStyleSheet()` calls required for baseline styling.

**Manual test**
- Open new shell; create a “style gallery” window showing all primitives.

**Rollback**
- Keep v2 QSS only applied in v2 mode.

---

# Phase 2 — Icon System v2 (Cursor-like line icons)

## Epic 2.1: Icon rules and pipeline
**Scope**
- Define:
  - Sizes: 16/20/24
  - Stroke: consistent line weight
  - Color: one neutral + accent blue (no multi-color)
  - Disabled: neutral-muted
- Decide representation:
  - Option A: SVG assets in `assets/icons/` (preferred for design iteration)
  - Option B: QPainter path icons (preferred for zero-asset + fast load)

**Dependencies**
- Epic 1.1 (colors)

**Done when**
- A single `IconProvider` API exists and is used by new shell/toolbars/menus.

**Manual test**
- Render an icon grid in the style gallery.

**Rollback**
- Keep legacy icon paths unchanged until cutover.

## Epic 2.2: Replace toolbar/menu icons in v2 shell
**Scope**
- Convert core chrome icons: New/Open/Save/Run/Stop, Panel toggles, Settings, etc.

**Dependencies**
- Epic 2.1, Epic 1.3

**Done when**
- No Qt standard icons used in v2 shell chrome.

**Manual test**
- Visual inspection for alignment, pixel snapping, and color consistency.

**Rollback**
- Temporarily map IconProvider calls back to standard icons.

---

# Phase 3 — PopupWindow Component Library (Unified Popups)

## Epic 3.1: PopupWindowBase (draggable/resizable + click-outside) ✅ **DONE**
**Scope**
- Create a unified popup framework:
  - `PopupWindowBase` (top-level or tool window)
  - Optional pin state integration with `PopupManager`
  - Behavior: close-on-outside-click (unless pinned), close-on-escape
  - Draggable header region, optional resize grips
  - Positioning helpers: anchor-to-widget + screen-boundary clamp
  - No animations/shadows; crisp border + subtle separation via neutrals

**Dependencies**
- Epic 1.1, Epic 1.3

**Implementation** (2025-12-29)
- `src/casare_rpa/presentation/canvas/ui/widgets/popups/popup_window_base.py`
  - `PopupWindowBase` class with all required features
  - `DraggableHeader` helper class
  - `AnchorPosition` enum for positioning
- `src/casare_rpa/presentation/canvas/managers/popup_manager.py`
  - Added `is_any_dragging()` helper
- `src/casare_rpa/presentation/canvas/theme/styles_v2.py`
  - Added `get_popup_styles_v2()` function
- Tests: 29 passing in `tests/presentation/canvas/ui/widgets/popups/`

**Done when**
- ✅ A sample "Popover" can open from a button, be dragged/resized, and closes correctly.
- ✅ All tests passing (29/29)

**Manual test**
- ✅ Open popover, click outside to close, pin then click outside (stays), escape closes when unpinned.

**Rollback**
- Keep existing bespoke popups.

## Epic 3.2: Popup variants
**Scope**
- Implement standardized variants using the base:
  - ContextMenu (Cursor-like)
  - Dropdown menu surface
  - Tooltip / hint bubble
  - Toast (but without animations; can auto-dismiss via timer only)
  - Inspector popover (for node output)
  - Autocomplete popup

**Dependencies**
- Epic 3.1

**Done when**
- Existing popup use-cases can be migrated one by one.

**Manual test**
- Open each popup; ensure z-order is correct over NodeGraphQt scene and docks.

**Rollback**
- Each popup migration is reversible by switching back to old widget.

---

# Phase 4 — IDE Shell v2 (Dock-Only Workspace)

## Epic 4.1: NewMainWindow skeleton (dock-only rules enforced)
**Scope**
- Build `NewMainWindow`:
  - Central workspace: NodeGraphQt graph widget
  - Dock containers on left/right/bottom
  - Tabbed docks
  - Dock-only enforcement: remove floatable features, disallow detached windows
  - Persist layout using `QSettings` and “Reset Layout”

**Dependencies**
- Phase 1 complete (visual baseline)

**Done when**
- You can resize panels, tab them, hide/show them, restore layout on restart.

**Manual test**
- Rearrange docks, restart app, layout restores; reset layout works.

**Rollback**
- Keep current `MainWindow` default.

## Epic 4.2: Chrome: top toolbar + status bar v2
**Scope**
- Rebuild core chrome with v2 styling and icons:
  - Primary actions: Run/Stop, Save, etc.
  - Status: connection/robot status, execution status, zoom, cursor position (if needed)

**Dependencies**
- Epic 4.1, Phase 2

**Done when**
- Chrome looks like a cohesive VS Code/Cursor variant and uses only v2 components.

**Manual test**
- Trigger actions; ensure no regressions in wiring.

**Rollback**
- Use legacy toolbar/status bar managers.

---

# Phase 5 — Component Library v2 (Reusable Widgets)

## Epic 5.1: Core primitives
**Scope**
- Create v2 versions (or wrappers) of:
  - Buttons (primary/secondary/ghost), toolbuttons
  - Inputs/search boxes
  - Select/combobox base
  - Tabs
  - List/Tree/Table base styling rules
  - Section headers, dividers, empty states

**Dependencies**
- Phase 1

**Done when**
- Panels and dialogs can be written without per-screen styling.

**Manual test**
- Style gallery shows all primitives and states.

**Rollback**
- Keep existing widgets; adopt v2 only in new screens first.

## Epic 5.2: Forms + validation patterns
**Scope**
- Standardize:
  - Labeled rows, inline errors, required markers
  - Read-only fields
  - File/folder pickers (consistent UX)
  - Variable insertion UX (if still desired)

**Dependencies**
- Epic 5.1

**Done when**
- A sample settings dialog uses only v2 form components.

**Manual test**
- Tab/enter behavior feels tight and predictable.

**Rollback**
- Keep dialog-specific styling until migration complete.

---

# Phase 6 — Migrate Panels (One by One)

This phase is intentionally modular: migrate one dock/panel per PR, keep the rest legacy until ready.

## Recommended default panel set (initial v2)
We will start with a minimal IDE set and add as needed:
- Left: Project / Explorer
- Right: Properties / Inspector
- Bottom: Output/Logs + Errors/Validation
- Optional: Robots/Orchestrator (as another bottom tab)

## Epic 6.1+: Panel migration template (repeatable)
**Scope**
- For each panel:
  - Replace layout + widgets with v2 components
  - Remove inline QSS/hex usage
  - Ensure it docks correctly in NewMainWindow

**Dependencies**
- Phase 4 + Phase 5

**Done when**
- Panel is visually consistent, dock-only, and works functionally.

**Manual test**
- Open panel, exercise main actions, close/reopen, persist layout.

**Rollback**
- Keep old panel class wired behind a toggle until stable.

Panels to migrate (suggested order)
1) Project Explorer: `src/casare_rpa/presentation/canvas/ui/panels/project_explorer_panel.py`
2) Properties: `src/casare_rpa/presentation/canvas/ui/property_panel/property_renderer.py`
3) Output/Logs: `src/casare_rpa/presentation/canvas/ui/panels/output_tab.py`, `log_tab.py`, `terminal_tab.py`
4) Variables: `variables_panel.py`, `variables_tab.py`
5) Recording-related: `browser_recording_panel.py`, `recorded_actions_panel.py`
6) Orchestrator: `ui/widgets/orchestrator/*`
7) Remaining specialized panels (analytics, process mining, debug consoles)

---

# Phase 7 — Dialogs + Setup Wizard (No Hex, v2 Components)

## Epic 7.1: Dialog framework v2
**Scope**
- Standardize:
  - Title area, body padding, footer buttons
  - Primary/secondary/destructive button placement
  - Keyboard defaults (Enter = primary; Esc = cancel)
  - No QGraphicsDropShadowEffect, no animations

**Dependencies**
- Phase 5

**Done when**
- A v2 dialog base replaces ad-hoc `DialogStyles` usage in v2 mode.

**Manual test**
- Focus trapping, tab order, escape/enter behavior.

**Rollback**
- Keep existing dialog implementations until migrated.

## Epic 7.2: Replace Setup Wizard styling (remove hardcoded hex)
**Scope**
- Refactor `src/casare_rpa/presentation/setup/setup_wizard.py` to use v2 tokens/QSS.
- Ensure it looks consistent with the rest of the app.

**Dependencies**
- Phase 1

**Done when**
- No hardcoded colors in setup wizard; consistent typography and spacing.

**Manual test**
- Walk through pages; verify readability and input UX.

**Rollback**
- Keep old wizard stylesheet if needed.

## Epic 7.3: Replace QMessageBox/QInputDialog usage (standardized v2 prompts)
**Scope**
- Provide v2 equivalents:
  - Non-blocking toasts for “info”
  - Modal confirm dialogs for destructive actions
  - Inline error banners where possible
- Migrate call sites gradually.

**Dependencies**
- Phase 3 + Phase 7.1

**Done when**
- NewMainWindow mode no longer uses raw QMessageBox/QInputDialog for app UX flows.

**Manual test**
- Confirm flows in panels/actions.

**Rollback**
- Keep legacy calls in legacy mode.

---

# Phase 8 — Remove Animations + Shadows Everywhere (Strict)

## Epic 8.1: Global "no animation" audit and removal ✅ **DONE**
**Scope**
- Remove/disable:
  - `QPropertyAnimation`, `QVariantAnimation`, `QEasingCurve`
  - `QGraphicsDropShadowEffect`
  - Any opacity fades / animated collapses
- Replace with instant state changes (show/hide, resize, style swap).

**Dependencies**
- None (can be done incrementally), but safer after v2 popups exist.

**Implementation** (2025-12-30)
- Files Modified: 11 files
  - `ui/widgets/toast.py` - Removed fade animations
  - `ui/widgets/collapsible_section.py` - Removed collapse animations
  - `ui/widgets/node_output_popup.py` - Removed shadow + animations
  - `ui/widgets/expression_editor/expression_editor_popup.py` - Removed shadow + animations
  - `ui/widgets/popups/popup_window_base.py` - Removed shadow + animations
  - `controllers/viewport_controller.py` - Removed zoom animation
  - `graph/auto_layout_manager.py` - Removed layout animations
  - `graph/focus_ring.py` - Removed focus animations
  - `connections/shake_to_detach.py` - Removed shake animations
  - `ui/base_widget.py` - Removed shadow effect base class
  - `ui/icons.py` - Removed animation-related icon helpers

**Policy Enforced**:
- Zero-motion: all `QPropertyAnimation`, `QVariantAnimation`, `QEasingCurve` removed from scope files
- Zero-shadow: all `QGraphicsDropShadowEffect` removed from scope files
- Instant state changes (show/hide, resize, style swap)

**Done when**
- ✅ Ripgrep for `QPropertyAnimation|QEasingCurve|QGraphicsDropShadowEffect` returns zero in v2 paths
- ✅ All tests passing (45 popup tests, 70 token tests)

**Manual test**
- ✅ Zoom, popup behavior, node layout work without animations

**Rollback**
- Feature flag: allow animations only in legacy mode temporarily if needed.

---

# Phase 9 — Cutover + Cleanup (Big-Bang Moment)

## Epic 9.1: Make NewMainWindow the default
**Scope**
- Switch default to v2 shell once parity is acceptable.
- Keep legacy behind an escape hatch flag for one release.

**Done when**
- v2 is default and stable.

## Epic 9.2: Delete legacy UI code and resources
**Scope**
- Remove legacy panel/dialog/widget codepaths that are no longer used.
- Remove old icon pipelines.
- Remove command palette entirely.

**Done when**
- No legacy UI import paths in production code.

**Rollback**
- Tag/branch before deletion (Git).

---

## Testing Checklist (Every Epic)
- Launch app (v2 mode), open/close.
- Dock layout: resize, tab, hide/show, restart restore, reset layout.
- DPI sanity: 100%, 125%, 150% (at least).
- Keyboard: Esc closes popups/dialogs; Enter triggers primary action when appropriate.
- No animations: verify no fades, no sliding, no drop shadows.
- No hex in v2 paths: new code uses tokens only.

---

## Decision Log
- Theme: dark-only
- Accent: Cursor-like blue (final hex ramp defined in token spec v2)
- Docking: dock-only (no floating)
- Popups: Qt-only, draggable + resizable
- Command palette: removed
- Fonts: Geist Sans + Geist Mono (bundled for PyInstaller)


