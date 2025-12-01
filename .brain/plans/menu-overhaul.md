# Menu System Overhaul Plan

## Status: READY

## Problem Statement
The menu system has:
1. Missing handler connections (save_to_scenario)
2. Empty stub handlers (pick_selector, record_workflow)
3. Incomplete Help menu (no Docs, Shortcuts, Updates)
4. Shortcut conflict (Ctrl+Shift+P used twice)

## Files to Modify

| File | Changes |
|------|---------|
| `main_window.py:224` | Connect action_save_to_scenario |
| `main_window.py:630-632` | Add Help menu items |
| `main_window.py:486` | Fix Ctrl+Shift+P conflict |
| `app.py` | Implement pick_selector, record_workflow connections |
| `menu_controller.py` | Wire show_documentation(), show_keyboard_shortcuts() |

## Implementation Steps

### Phase 1: Fix Missing Connections
1. Connect `action_save_to_scenario` to handler
2. Wire `action_pick_selector` in app.py
3. Wire `action_record_workflow` in app.py

### Phase 2: Complete Help Menu
1. Add `Documentation` action (Ctrl+F1) - opens docs in browser
2. Add `Keyboard Shortcuts` action (Ctrl+K, Ctrl+S already exists)
3. Add `Check for Updates` action (optional, can be placeholder)
4. Add separator before About

### Phase 3: Fix Shortcut Conflict
- Change Performance Dashboard from Ctrl+Shift+P to Ctrl+Alt+P
- Keep Command Palette at Ctrl+Shift+P (standard)

### Phase 4: Cleanup
1. Remove empty stub handlers
2. Ensure all actions have status tips
3. Verify all menu items have proper separators

## Test Scenarios
1. All menu items are clickable
2. No shortcut conflicts
3. Help menu shows all items
4. Save to Scenario works
5. Pick/Record show disabled state when no browser

## Agents Required
- refactor: Code changes
- quality: Test creation
- reviewer: Code review gate
