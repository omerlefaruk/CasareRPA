# Breadcrumb Navigation Fix Plan

## Problem
The breadcrumb shows `[V: d` instead of `root / {subflow_name}` format.

## Current State
- BreadcrumbNavWidget shows keyboard hints `[V: dive in | C: go back]` which is cluttering the display
- Separator changed to `/` ✓
- Root name changed to "root" ✓

## Desired Behavior
1. When at root level: breadcrumb **hidden** (nothing to navigate back to)
2. When inside subflow: show `root / SubflowName` where:
   - `root` is clickable → returns to main workflow
   - `/` is the separator
   - `SubflowName` is the current subflow (not clickable, it's current)
3. **No keyboard hints** displayed - the user already knows V/C

## Implementation Steps

### 1. Remove keyboard hint label
In `BreadcrumbNavWidget._setup_ui()`:
- Remove the `_hint_label` widget entirely

### 2. Simplify the breadcrumb display
Keep only:
- Back button `<` (optional, can remove since C key works)
- Breadcrumb path: `root / SubflowName`

### 3. Verify visibility logic
- Hidden at root level (≤1 item in path)
- Visible when inside subflow (>1 item)

## Files to Modify
- `src/casare_rpa/presentation/canvas/ui/widgets/breadcrumb_nav.py`
