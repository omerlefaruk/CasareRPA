# Implementation Plan: Epic 2.2 - Replace Toolbar/Menu Icons in v2 Shell

**Epic**: Phase 2, Epic 2.2 from `docs/UX_REDESIGN_PLAN.md`
**Status**: COMPLETE (2025-12-29)
**Created**: 2025-12-29
**Dependencies**: Epic 2.1 (IconProviderV2 complete), Epic 1.3 (QSS v2)

---

## Overview

Replace Qt standard icons (QStyle.StandardPixmap) with IconProviderV2 Lucide SVG icons across:
- Main toolbar (file operations, execution controls, undo/redo)
- Debug toolbar (step controls, run from here)
- Recording toolbar (record, pause, stop)
- Alignment toolbar (align/distribute/auto-layout icons)
- Toolbar builder (MainWindow unified toolbar)
- Menu items (File, Edit, View, Run, Automation, Help)

**Strategy**: Create a new `get_icon_v2()` function in `ui/icons.py` that wraps IconProviderV2, then incrementally replace `get_toolbar_icon()` calls.

---

## Icon Name Mapping Table (Legacy -> V2)

| Legacy Name | V2 Icon | Notes | State |
|-------------|---------|-------|-------|
| new | file | File icon | normal |
| open | folder | Folder icon | normal |
| reload | refresh | Circular arrows | normal |
| save | save | Save diskette | normal |
| save_as | save | Reuse save icon | normal |
| undo | undo | Curved left arrow | normal |
| redo | redo | Curved right arrow | normal |
| run | play | Play triangle | accent |
| pause | pause | Two vertical bars | normal |
| resume | play | Reuse play icon | accent |
| stop | stop | Square | accent |
| restart | refresh | Reuse refresh icon | normal |
| step | chevron-right | Step forward | normal |
| continue | chevron-right | Continue execution | normal |
| debug | code | Debug icon | normal |
| breakpoint | alert | Breakpoint icon | normal |
| clear_breakpoints | trash | Clear breakpoints | normal |
| record | circle | Need to add | accent |
| pick_selector | cursor | Pick element | normal |
| preferences | settings | Settings gear | normal |
| help | info | Help/info | normal |
| about | info | About (reuse help) | normal |
| settings | settings | Settings gear | normal |
| project | folder | Project folder | normal |
| fleet | database | Fleet dashboard | normal |
| layout | panel-left | Layout management | normal |
| performance | activity | Need to add | normal |
| dashboard | home | Dashboard | normal |
| metrics | bar-chart | Need to add | normal |
| ai_assistant | brain | Need to add | accent |
| credentials | lock | Credential manager | normal |

---

## Icons to Add (Missing from Current Set)

| Icon Name | Source | Priority |
|-----------|--------|----------|
| circle | Lucide (circle.svg) | HIGH (record button) |
| activity | Lucide (activity.svg) | MEDIUM (performance) |
| bar-chart | Lucide (bar-chart-2.svg) | LOW (metrics) |
| brain | Custom or Lucide alternative | LOW (AI assistant) |

**Note**: The custom "brain" icon exists in legacy `_create_colored_icon()` but should be ported as SVG or kept as custom drawing.

---

## Files to Create

| File | Purpose |
|------|---------|
| `src/casare_rpa/presentation/canvas/ui/icons_v2_adapter.py` | Adapter providing `get_icon_v2()` wrapper |

---

## Files to Modify

| File | Changes | Lines |
|------|---------|-------|
| `ui/icons.py` | Import adapter, keep legacy for rollback | ~20 |
| `ui/toolbars/main_toolbar.py` | Replace `get_toolbar_icon()` with `get_icon_v2()` | ~15 |
| `ui/toolbars/debug_toolbar.py` | Add icons to actions (currently text-only) | ~10 |
| `ui/toolbars/recording_toolbar.py` | Replace `get_toolbar_icon()` with `get_icon_v2()` | ~8 |
| `ui/toolbars/alignment_toolbar.py` | Replace `_create_icon()` with IconProviderV2 | ~150 |
| `components/toolbar_builder.py` | Replace `get_toolbar_icon()` with `get_icon_v2()` | ~20 |
| `components/menu_builder.py` | Add icons to menu actions | ~40 |
| `theme_system/__init__.py` | Export adapter if needed | ~2 |

**Total estimated changes**: ~265 lines across 8 files

---

## Implementation Steps

### Step 1: Create Icon Adapter (NEW FILE)
- Create `ui/icons_v2_adapter.py`
- Add `get_icon_v2(name: str, size: int = 20, state: str = "normal") -> QIcon`
- Implement legacy -> v2 name mapping
- Handle missing icons gracefully (fallback to legacy or empty)
- Add `is_v2_enabled()` flag for easy rollback

### Step 2: Export from ui/icons.py
- Import adapter at module level
- Re-export `get_icon_v2` for convenience
- Keep legacy `get_toolbar_icon()` unchanged
- Add feature flag constant: `USE_V2_ICONS = True`

### Step 3: Update MainToolbar
- Replace `get_toolbar_icon()` calls with `get_icon_v2()`
- Use appropriate sizes (20 for toolbar)
- Use "accent" state for run/stop actions
- Test: Open app, verify toolbar icons render

### Step 4: Update DebugToolbar
- Add icons to step actions (currently text-only)
- Map: step_over -> chevron-down, step_into -> chevron-right, step_out -> chevron-left
- Map: continue -> play, run_from_here -> play + arrow
- Test: Enable debug mode, verify icons

### Step 5: Update RecordingToolbar
- Replace `get_toolbar_icon()` calls with `get_icon_v2()`
- Add "circle" icon for record buttons (if available) or reuse legacy
- Use "accent" state for active recording
- Test: Start recording, verify icon states

### Step 6: Update AlignmentToolbar (LARGEST CHANGE)
- Remove entire `_create_icon()` method and drawing helpers
- Import `icon_v2` directly
- Replace with `icon_v2.get_icon(align_left, size=16)`
- Create mapping: align_left/center_v/right, distribute_h/v
- Use Lucide icons: align-left, align-center-h, align-center-v, etc.
- **Note**: May need to add alignment-specific SVG icons

### Step 7: Update ToolbarBuilder
- Replace `get_toolbar_icon()` with `get_icon_v2()`
- Use consistent size (16 or 20)
- Map all action names to v2 equivalents
- Test: Run app, verify main toolbar icons

### Step 8: Update MenuBuilder
- Add icons to File menu items (new, open, save, save_as, exit)
- Add icons to Edit menu items (undo, redo, cut, copy, paste, delete)
- Add icons to View menu items (panel toggles, dashboards)
- Add icons to Run menu items (run, pause, stop, restart)
- Add icons to Automation menu (record, pick, validate)
- Add icons to Help menu (documentation, preferences, about)
- Test: Open each menu, verify icons

### Step 9: Add Missing SVG Icons
- Download missing Lucide icons:
  - `circle.svg` (for record)
  - `activity.svg` (for performance)
  - `bar-chart-2.svg` (for metrics)
- Copy to `src/casare_rpa/resources/icons/`
- Update mapping table

### Step 10: Update Tests
- Extend `test_icons_v2.py` with adapter tests
- Test legacy name mappings resolve correctly
- Test fallback to empty icon for unknown names
- Test size variants for toolbar/menu

---

## Parallel Opportunities

**After Step 1 (adapter exists):**
- **Parallel A**: Steps 3-5 (toolbars - independent files)
- **Parallel B**: Steps 6-7 (alignment + toolbar builder - independent)
- **Parallel C**: Step 8 (menu builder - independent)
- **Parallel D**: Step 9 (download icons - quick task)

**Recommended grouping:**
1. Agent 1: Steps 3, 4, 5 (main, debug, recording toolbars)
2. Agent 2: Steps 6, 7 (alignment, toolbar builder)
3. Agent 3: Steps 8, 9 (menu builder + download icons)

---

## Agent Assignments

| Agent | Tasks | Files | Estimated Effort |
|-------|-------|-------|------------------|
| builder | Steps 3-5 (execution toolbars) | main_toolbar.py, debug_toolbar.py, recording_toolbar.py | ~40 lines |
| builder | Steps 6-7 (alignment + toolbar builder) | alignment_toolbar.py, toolbar_builder.py | ~170 lines |
| ui | Step 8 (menu icons) + Step 1 (adapter) | menu_builder.py, icons_v2_adapter.py | ~55 lines |
| quality | Step 10 (tests) | test_icons_v2.py | ~50 lines |

**Total agent effort**: ~315 lines (including new adapter file)

---

## Test Approach

### Unit Tests (test_icons_v2.py extension)
```python
class TestIconAdapter:
    def test_legacy_name_maps_to_v2()
    def test_unknown_name_returns_empty_icon()
    def test_adapter_respects_size_parameter()
    def test_adapter_respects_state_parameter()
    def test_feature_flag_disables_v2()

class TestIconMappings:
    @pytest.mark.parametrize("legacy,v2", [
        ("new", "file"),
        ("open", "folder"),
        ("run", "play"),
        ("stop", "stop"),
    ])
    def test_core_mappings(self, legacy, v2)
```

### Manual Verification Checklist
- [ ] Main toolbar shows file, save, undo/redo icons
- [ ] Run button uses accent color (blue)
- [ ] Stop button uses accent color (red/blue based on theme)
- [ ] Debug toolbar shows step icons (chevrons)
- [ ] Recording toolbar shows pause/stop icons
- [ ] Alignment toolbar shows alignment icons
- [ ] All menu items have appropriate icons
- [ ] Disabled icons appear muted
- [ ] Icons render at correct sizes (16/20/24)
- [ ] No blank/missing icon placeholders

---

## Rollback Strategy

**Level 1 - Quick Toggle (Single Line):**
```python
# In ui/icons_v2_adapter.py
USE_V2_ICONS = False  # Toggle off to revert
```

**Level 2 - Import Revert:**
```python
# In each toolbar file, revert import:
# from casare_rpa.presentation.canvas.ui.icons import get_icon_v2
from casare_rpa.presentation.canvas.ui.icons import get_toolbar_icon  # Legacy

# Then replace get_icon_v2 -> get_toolbar_icon throughout
```

**Level 3 - Full Revert:**
- Delete `ui/icons_v2_adapter.py`
- Revert all changes to toolbar files
- Remove icons from menu_builder.py
- Keep IconProviderV2 (Epic 2.1) intact

**Rollback Time Estimate:**
- Level 1: 1 minute
- Level 2: 15 minutes
- Level 3: 30 minutes

---

## Epic Completion Criteria

- [ ] Adapter `get_icon_v2()` created and exported
- [ ] All 6 toolbar files use v2 icons
- [ ] MenuBuilder adds icons to all 6 menus
- [ ] Missing SVG icons downloaded (circle, activity, bar-chart-2)
- [ ] Tests pass (adapter tests + existing icon tests)
- [ ] Manual verification checklist complete
- [ ] No Qt standard icons in v2 shell chrome
- [ ] Rollback tested (toggle off, verify legacy works)

---

## References

- `docs/UX_REDESIGN_PLAN.md` Phase 2 Epic 2.2
- `.brain/plans/chain-epic-2.1-20251229.md` (IconProviderV2 implementation)
- `src/casare_rpa/presentation/canvas/theme_system/icons_v2.py`
- `src/casare_rpa/presentation/canvas/ui/icons.py`
- `src/casare_rpa/presentation/canvas/ui/toolbars/*.py`
