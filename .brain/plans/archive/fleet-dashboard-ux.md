# Fleet Dashboard UX Improvements

Date: 2025-12-15

Status: Complete

## Goal
Improve Fleet Management Dashboard UX in Canvas: clearer navigation, non-blocking feedback, consistent theming.

## Constraints
- Presentation/UI must use theme tokens (`casare_rpa.presentation.canvas.theme.THEME`); avoid new hardcoded colors.
- No silent failures; log via `loguru`.
- Keep changes localized to fleet dashboard UI + manager.

## Success Criteria
- Fleet dashboard opens non-modally and remains usable while interacting with Canvas.
- Sidebar navigation (with icons) replaces cramped tab row without adding new screens.
- Blocking `QMessageBox` calls during refresh/errors replaced with toasts.
- Tenant selector remains hidden unless it’s actually usable (super admin + multiple tenants).
- Fleet dashboard styles align with Canvas theme.

## Scope / Files
- `src/casare_rpa/presentation/canvas/ui/dialogs/fleet_dashboard.py`
- `src/casare_rpa/presentation/canvas/ui/dialogs/fleet_tabs/*`
- `src/casare_rpa/presentation/canvas/ui/dialogs/fleet_tabs/constants.py`
- `src/casare_rpa/presentation/canvas/components/fleet_dashboard_manager.py`
- `src/casare_rpa/presentation/canvas/ui/widgets/` (new toast widget)

## Implementation Notes
- Use a `QStackedWidget` for pages; sidebar uses `QToolButton` with custom-drawn `QIcon` (QPainter) in theme colors.
- Add `show_toast(message, level)` on dashboard; manager calls this instead of `QMessageBox`.

## Test Strategy
- Run `pytest tests/ -k fleet_dashboard -v` (or nearest UI/presentation targeted suite).
- Run import/syntax check on modified modules.
