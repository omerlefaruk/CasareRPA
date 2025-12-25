# ElevenLabs UI Refactor Plan

**Status**: Planning Phase
**Branch**: `elevenlabs-ui-refactor`
**Complexity**: EPIC (5)
**Estimated Duration**: 12+ hours

---

## Overview

Refactor CasareRPA's entire UI to match ElevenLabs design guidelines, including typography, color system, spacing, border radius, and component styling.

---

## ElevenLabs Design System Summary

### Typography

| Style | Font | Weight | Use Case |
|-------|------|--------|----------|
| **Functional Headings** | Eleven Semi Condensed | Bold/Medium | Default headings |
| **Expressive Headings** | Eleven Semi Condensed | Bold + UPPERCASE | Impactful breaks |
| **Paragraphs** | Eleven Regular | Normal | Body text |
| **Functional UI** | Eleven Medium | Medium | UI elements |
| **Expressive UI** | Eleven Semi Condensed | Medium + UPPERCASE | Marketing elements |

**Fallback**: `Inter, system-ui, Arial` for non-Latin

### Font Sizes

| Element | Size |
|---------|------|
| xs | 10px |
| sm | 11px |
| md | 12px |
| lg | 14px |
| xl | 16px |
| xxl | 20px |

### Radius Tokens

| Name | Value (px) |
|------|------------|
| radius-sm | 4 |
| radius-md | 8 |
| radius-lg | 12 |
| radius-xl | 20 |
| radius-2xl | 28 |
| radius-full | 999 |

### Icon Grid

| Size (px) | Padding (px) | Stroke (px) |
|-----------|--------------|-------------|
| 16 | 2 | 1 |
| 24 | 2 | 1.5 |
| 32 | 2 | 2 |
| 64 | 2 | 4 (marketing only) |

**Default**: 24px for UI, 1.5px stroke

### Color System

**Core**: Black (#000000) + White (#FFFFFF)

**9 Hues × 11 Tints** (50-950 scale):
- Pink, Red, Orange, Amber, Yellow, Lime, Green, Emerald, Teal, Cyan, Sky, Blue, Indigo, Violet, Purple, Fuchsia, Rose, Slate, Neutral, Zinc

**Semantic Colors** (AA Accessible):
- Negative: Red 800 (text), Red 200 (bg), Red 600 (icons)
- Warning: Amber 800 (text), Amber 200 (bg), Amber 600 (icons)
- Positive: Emerald 800 (text), Emerald 200 (bg), Emerald 600 (icons)
- Informative: Blue 800 (text), Blue 200 (bg), Blue 600 (icons)

**Default Tints**: 50 (bg), 300-500 (foreground)

---

## Current vs Target State

### Current CasareRPA Theme

| Category | Current Value | Target (ElevenLabs) |
|----------|---------------|---------------------|
| Font | Segoe UI / Inter | Eleven / Inter fallback |
| Radius | 4, 6, 8, 12 | 4, 8, 12, 20, 28, 999 |
| Spacing | 2, 4, 8, 12, 16, 20, 32 | Same (need validation) |
| Icons | 16, 24, 32 | 24px default, 1.5px stroke |
| Colors | Zinc/Indigo palette | Black/White + tint system |

---

## Implementation Plan

### Phase 1: Foundation (theme_system)

**Files**:
- `src/casare_rpa/presentation/canvas/theme_system/colors.py`
- `src/casare_rpa/presentation/canvas/theme_system/constants.py`
- `src/casare_rpa/presentation/canvas/theme_system/__init__.py`

**Changes**:
1. Add ElevenLabs color tints (9 hues × 11 levels)
2. Update radius tokens to match ElevenLabs
3. Update icon sizing/stroke guidelines
4. Add typography system (Eleven font stack)
5. Create semantic color mapping

### Phase 2: Typography System

**Files**:
- All UI files using hardcoded font sizes
- `src/casare_rpa/presentation/canvas/theme_system/styles.py`

**Changes**:
1. Update font stack to Eleven / Inter
2. Implement weight-based typography (Normal, Medium, Bold)
3. Update line heights (1.5 for paragraphs, 1.2 for headings)
4. Letter spacing adjustments

### Phase 3: Component Redesign

#### 3.1 Buttons
**Files**: All button implementations
**Changes**:
- Radius: 8px (md) default
- Padding: 8px 16px
- Height: 32-44px depending on size
- Font: Medium weight
- Hover: Subtle background shift

#### 3.2 Inputs
**Files**: `validated_input.py`, `file_path_widget.py`, etc.
**Changes**:
- Radius: 8px
- Border: 1px solid neutral-300
- Focus: 2px ring + border change
- Padding: 8px 12px

#### 3.3 Cards/Panels
**Files**: All panel files, dialog files
**Changes**:
- Radius: 12px (lg) default, 20px (xl) for special cards
- Border: 1px solid neutral-200
- Shadow: Subtle elevation

#### 3.4 Dialogs
**Files**: All dialog files in `dialogs/`
**Changes**:
- Radius: 20px (xl) for dialogs
- Header: Bold, 18px
- Padding: 24px
- Actions: Right-aligned with 8px gap

#### 3.5 Tabs
**Files**: Tab implementations
**Changes**:
- Indicator: Bottom border 2px
- Padding: 10px 18px
- Weight: 500
- Color: neutral-500 → neutral-900 (active)

### Phase 4: Widget Updates

| Widget | Priority | Changes |
|--------|----------|---------|
| AI Assistant Dock | HIGH | ChatGPT-style + ElevenLabs colors |
| Toast | HIGH | Radius 8px, shadow, proper positioning |
| Collapsible Section | MEDIUM | Radius 8px, chevron icon |
| Property Panel | HIGH | Input fields, labels, spacing |
| Node Graph | MEDIUM | Node styling, ports, wires |
| Toolbars | LOW | Button hover, pressed states |

### Phase 5: Visual Polish

**Details**:
- Smooth transitions (150-200ms)
- Subtle shadows for elevation
- Proper focus states (2px ring)
- Hover states on all interactive elements

---

## File Inventory

### Core Theme Files (5 files)
```
src/casare_rpa/presentation/canvas/theme_system/
├── __init__.py
├── colors.py
├── constants.py
├── styles.py
└── utils.py
```

### UI Files (100+ files to review)
```
src/casare_rpa/presentation/canvas/ui/
├── dialogs/        (30+ files)
├── panels/         (15+ files)
├── widgets/        (40+ files)
├── toolbars/       (5+ files)
└── property_panel/ (5+ files)
```

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking existing UX | HIGH | Incremental rollout, user testing |
| Performance impact | MEDIUM | Cache stylesheets, minimize repaints |
| Font licensing | LOW | Use Inter as free alternative |
| Incomplete migration | HIGH | Use deprecation warnings |

---

## Success Criteria

- [ ] All theme values use ElevenLabs tokens
- [ ] No hardcoded colors/spacing in UI files
- [ ] Typography matches ElevenLabs guidelines
- [ ] All components use new radius system
- [ ] AA accessibility maintained
- [ ] No visual regressions

---

## Dependencies

- None (can start immediately)
- User approval before main branch merge

---

## Notes

1. **Eleven font** is proprietary. Use `Inter` as the closest free alternative.
2. **Tint system** can be simplified to 5 levels (50, 200, 500, 700, 900) for v1.
3. **Incremental rollout**: Start with dialogs, then panels, then canvas.
4. **Backward compatibility**: Keep old THEME constants, deprecate gradually.
