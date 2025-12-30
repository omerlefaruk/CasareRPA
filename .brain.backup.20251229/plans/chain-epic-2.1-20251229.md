# Implementation Plan: Epic 2.1 - Icon System v2

**Epic**: Phase 2, Epic 2.1 from `docs/UX_REDESIGN_PLAN.md`
**Status**: COMPLETED
**Created**: 2025-12-29
**Completed**: 2025-12-29
**Dependencies**: Epic 1.1 (colors), Epic 1.3 (QSS v2)

---

## Overview

Created an icon provider using **Lucide SVG icons** downloaded from [lucide.dev](https://lucide.dev/).
Icons are bundled as assets and rendered with `QSvgRenderer`, applying `THEME_V2` colors dynamically.
Single-color (neutral + accent blue) with disabled state.

**Decision**: Option A - SVG assets (preferred for design quality and breadth of icon set)

**Icon Source**: [Lucide Icons](https://lucide.dev/) - ISC license (free for commercial use)

---

## Files to Create

| File | Purpose | Status |
|------|---------|--------|
| `src/casare_rpa/presentation/canvas/theme_system/icons_v2.py` | IconProviderV2 class with SVG rendering | ✓ Created |
| `tests/presentation/canvas/theme/test_icons_v2.py` | Tests for icon provider | ✓ Created |
| `src/casare_rpa/resources/icons/*.svg` | 61 Lucide SVG icons | ✓ Downloaded |

---

## Files to Modify

| File | Changes |
|------|---------|
| `src/casare_rpa/presentation/canvas/theme_system/__init__.py` | Export IconProviderV2, icon_v2 singleton |
| `src/casare_rpa/presentation/canvas/theme_system/style_gallery.py` | Add icon grid section |

---

## Implementation Details

### IconProviderV2 Class Design

```python
class IconProviderV2:
    """Zero-asset icon provider using QPainterPath rendering.

    Features:
    - Icons defined as QPainterPath (no SVG files)
    - Three sizes: 16/20/24 (from TOKENS_V2.sizes)
    - Single color: neutral (normal) + blue (accent)
    - Disabled state: muted neutral
    - Internal cache for rendered icons
    """

    def get_icon(self, name: str, size: int = 16, state: str = "normal") -> QIcon
    def get_pixmap(self, name: str, size: int = 16, state: str = "normal") -> QPixmap
    def _create_icon_path(self, name: str) -> QPainterPath | None
    def _render_icon(self, path: QPainterPath, size: int, color: str) -> QPixmap
```

### Color Mapping

| State | Color Source |
|-------|--------------|
| normal | `THEME_V2.text_primary` (#a0a0a0) |
| accent | `THEME_V2.primary` (#0066ff) |
| disabled | `THEME_V2.text_disabled` (#404040) |

### Stroke Specifications

- Width: 1.5px (consistent across all icons)
- Line cap: `Qt.PenCapStyle.RoundCap`
- Line join: `Qt.PenJoinStyle.RoundJoin`

### Icon Set (MVP - Core Chrome)

| Name | Description | Use Location |
|------|-------------|--------------|
| file | File/document | Project panel, menus |
| folder | Folder/directory | Project panel |
| edit | Edit/pencil | Toolbar, context menu |
| save | Save diskette | Toolbar, file menu |
| run | Play triangle | Toolbar (execute) |
| stop | Stop square | Toolbar (execution) |
| settings | Gear/cog | Settings menu, toolbar |
| search | Magnifying glass | Search inputs |
| plus | Plus/add | New item buttons |
| minus | Minus/remove | Delete buttons |
| close | X mark | Tab close, dialog close |
| menu | Hamburger lines | Menu toggle |
| chevron_down | Down arrow | Dropdowns, accordions |
| chevron_right | Right arrow | Tree expanders |
| chevron_left | Left arrow | Back navigation |
| chevron_up | Up arrow | Sort headers |
| check | Checkmark | Completed states |
| refresh | Circular arrows | Reload, refresh |
| trash | Trash can | Delete actions |
| copy | Duplicate pages | Copy actions |
| paste | Clipboard | Paste actions |
| undo | Curved left arrow | Undo |
| redo | Curved right arrow | Redo |
| zoom_in | Magnifier with plus | Zoom controls |
| zoom_out | Magnifier with minus | Zoom controls |
| panel_left | Left panel icon | Dock toggles |
| panel_right | Right panel icon | Dock toggles |
| panel_bottom | Bottom panel icon | Dock toggles |

---

## Implementation Steps

### Step 1: Create IconProviderV2 skeleton
- Create `icons_v2.py` with class structure
- Add cache dict for rendered icons
- Add `_create_icon_path()` with path definitions
- Start with 5 simple icons (plus, minus, close, chevron_down, search)

### Step 2: Implement core rendering
- `_render_icon()`: Create QPixmap, QPainter, draw path
- Handle size scaling (16/20/24)
- Apply stroke width (1.5px) and caps
- `get_icon()`: Return cached or newly rendered QIcon

### Step 3: Implement color states
- Map state strings to THEME_V2 colors
- Support: "normal", "accent", "disabled"
- Fallback to normal for unknown state

### Step 4: Add remaining icons
- Expand `_create_icon_path()` with full icon set
- Group by complexity (lines, curves, combined)

### Step 5: Export from theme_system
- Add imports to `__init__.py`
- Export singleton `icon_v2 = IconProviderV2()`
- Update `__all__`

### Step 6: Add icon gallery to style_gallery
- Create `_create_icons_section()`
- Grid display: icon name + visual + size variants
- Show all three states (normal, accent, disabled)

### Step 7: Write tests
- Follow `test_font_loader.py` pattern
- Test: singleton exists, get_icon returns QIcon
- Test: unknown name returns empty icon (graceful)
- Test: size variants (16/20/24)
- Test: disabled state uses correct color
- Test: caching works (same instance returned)

---

## Parallel Opportunities

After Step 1 (skeleton exists):
- **Parallel 1**: Implement icon path definitions (Step 1-2)
- **Parallel 2**: Write test file structure (Step 7 skeleton)

After Step 4 (icons complete):
- **Parallel 1**: Update `__init__.py` exports (Step 5)
- **Parallel 2**: Add icon gallery section (Step 6)
- **Parallel 3**: Write full tests (Step 7)

---

## Risks and Mitigation

| Risk | Mitigation |
|------|------------|
| QPainterPath complexity for curves | Start with simple line icons, add curves incrementally |
| Performance on first render | Use LRU cache; pre-render common icons at startup |
| Icon appearance at different DPIs | Test at 100%/125%/150% DPI; use float coordinates |
| Too many icons to define | Start with core chrome (20 icons), add per epic as needed |
| Visual inconsistency | Create a reference grid for all paths on same coordinate system |

---

## Test Approach

Following `test_tokens_v2.py` and `test_font_loader.py` patterns:

```python
class TestIconProviderV2Singleton:
    def test_icon_v2_singleton_exists()
    def test_icon_v2_has_expected_methods()

class TestIconRendering:
    def test_get_icon_returns_qicon()
    def test_get_pixmap_returns_qpixmap()
    def test_unknown_name_returns_empty_icon()

class TestIconSizes:
    def test_icon_size_16()
    def test_icon_size_20()
    def test_icon_size_24()

class TestIconStates:
    def test_normal_state_uses_text_primary()
    def test_accent_state_uses_primary_blue()
    def test_disabled_state_uses_text_disabled()

class TestIconCaching:
    def test_same_icon_returns_cached_instance()
    def test_cache_key_includes_size_and_state()
```

---

## Manual Verification

After implementation:
1. Run `python run.py` with v2 shell
2. Open style gallery: `show_style_gallery_v2()`
3. Verify icon grid displays correctly
4. Check:
   - All icons render (no blank spaces)
   - Sizes align visually (16/20/24)
   - Colors match THEME_V2 values
   - Disabled icons are visibly muted
   - No pixelation at 125%/150% DPI

---

## Rollback Plan

If issues arise:
1. Keep `icons_v2.py` unused until Epic 2.2
2. Legacy icons (`ui/icons.py`, `node_icons.py`) remain unchanged
3. Revert `__init__.py` exports only (keep file for later)
4. Remove icon gallery section from `style_gallery.py`

---

## Epic Completion Criteria

- [x] IconProviderV2 class created and exported
- [x] 61 Lucide SVG icons downloaded (exceeds 25+ requirement)
- [x] Tests pass (40 tests in test_icons_v2.py)
- [x] Icon gallery shows all icons in style gallery
- [x] SVG icons bundled as PyInstaller assets
- [x] DPI scaling works (QSvgRenderer handles this natively)

---

## Implementation Summary

### What Was Built

1. **IconProviderV2 class** (`theme_system/icons_v2.py`):
   - Loads SVG icons from `resources/icons/`
   - Applies THEME_V2 colors by replacing `currentColor` in SVG
   - Supports 3 sizes: 16/20/24 (from TOKENS_V2.sizes)
   - Supports 3 states: normal, disabled, accent
   - Internal caching for performance

2. **61 Lucide SVG icons** downloaded to `resources/icons/`:
   - File operations: file, folder, folder-open, save, download, upload, trash
   - Edit operations: edit (pencil), copy, cut (scissors), paste, undo, redo
   - Actions: play, pause, stop (square), plus, minus, check, search, refresh
   - Navigation: chevron-up/down/left/right, zoom-in/out
   - Chrome: settings, menu, close (x), more-horizontal/vertical
   - Panels: panel-left, panel-right, panel-bottom
   - Git: branch, commit, merge
   - RPA: mouse, keyboard, camera, mic, eye, eye-off, lock, unlock
   - Other: code, database, globe, home, image, link, mail, terminal
   - Status: alert, info, warning, error, calendar, clock

3. **Tests** (`tests/presentation/canvas/theme/test_icons_v2.py`):
   - 40 tests covering singleton, rendering, sizes, states, caching, directory resolution, exports, theme integration

4. **Style Gallery** updated with icon grid section showing all icons in 3 sizes and 3 states

### Usage Example

```python
from casare_rpa.presentation.canvas.theme_system.icons_v2 import icon_v2

# Get themed icon
icon = icon_v2.get_icon("play", size=24, state="accent")
play_action.setIcon(icon)

# Get pixmap for custom painting
pixmap = icon_v2.get_pixmap("check", size=16, state="normal")
painter.drawPixmap(x, y, pixmap)
```

## References

- `docs/UX_REDESIGN_PLAN.md` Phase 2 Epic 2.1
- `src/casare_rpa/presentation/canvas/theme_system/tokens_v2.py` (colors, sizes)
- `src/casare_rpa/presentation/canvas/theme_system/style_gallery.py` (pattern for gallery)
- `tests/presentation/canvas/theme/test_tokens_v2.py` (test patterns)
- `tests/presentation/canvas/theme/test_font_loader.py` (test patterns)
