# P1-P2 Theme Refactor Implementation Plan

## Overview
Replace remaining hardcoded colors with theme tokens in OAuth dialogs, panels, and syntax highlighters.

## Pre-Analysis Summary
- **Total files affected**: 9 files
- **Total replacements**: ~20 hardcoded colors
- **New tokens needed**: 8 tokens

---

## Phase 1: Add Missing Tokens to colors.py

**File**: `src/casare_rpa/presentation/canvas/theme_system/colors.py`

**Add to `CanvasThemeColors` dataclass**:

```python
# Brand colors for OAuth (extended)
brand_google: str = "#4285f4"
brand_google_light: str = "#5a95f5"  # NEW - hover state
brand_google_dark: str = "#2d5a9e"   # NEW - disabled state
brand_gemini: str = "#9C27B0"
brand_gemini_hover: str = "#B026B8"  # Already exists as brand_gemini_hover

# Console log level colors
console_text: str = "#f4f4f5"         # NEW - default console text
console_info: str = "#3b82f6"         # NEW - info level
console_success: str = "#10b981"      # NEW - success level
console_warning: str = "#f59e0b"      # NEW - warning level
console_error: str = "#ef4444"        # NEW - error level
console_debug: str = "#71717a"        # NEW - debug level
```

**Verification**: Run `python -c "from casare_rpa.presentation.canvas.theme import THEME; print(THEME.brand_google_light)"`

---

## Phase 2: Fix OAuth Dialogs

### 2.1 google_oauth_dialog.py

**File**: `src/casare_rpa/presentation/canvas/ui/dialogs/google_oauth_dialog.py`

**Replacements** (use regex mode):

| Search | Replace | Line Context |
|--------|---------|--------------|
| `background-color: #4285f4;` | `background-color: {THEME.brand_google};` | Authorize button |
| `#5a95f5` | `{THEME.brand_google_light}` | Button hover |
| `#2d5a9e` | `{THEME.brand_google_dark}` | Button disabled |

**Regex pattern**: `background-color: #4285f4;` → `background-color: \{THEME\.brand_google\};`

### 2.2 antigravity_oauth_dialog.py

**File**: `src/casare_rpa/presentation/canvas/ui/dialogs/antigravity_oauth_dialog.py`

**Same 3 replacements as google_oauth_dialog.py**

### 2.3 credential_manager_dialog.py

**File**: `src/casare_rpa/presentation/canvas/ui/dialogs/credential_manager_dialog.py`

**Replacements**:

| Search | Replace | Context |
|--------|---------|---------|
| `background-color: #4285F4;` | `background-color: {THEME.brand_google};` | Google add button |
| `#5a95f5` | `{THEME.brand_google_light}` | Google hover |
| `#9C27B0` | `{THEME.brand_gemini};` | Gemini button |
| `#B026B8` | `{THEME.brand_gemini_hover}` | Gemini hover |

---

## Phase 3: Fix Panels

### 3.1 history_tab.py

**File**: `src/casare_rpa/presentation/canvas/ui/panels/history_tab.py`

**Replacements**:

| Search | Replace | Context |
|--------|---------|---------|
| `"#1a3d1a"` | `THEME.selection_success_bg` | Success row background |
| `"#3d1a1a"` | `THEME.selection_error_bg` | Error row background |

**Note**: These are already in `colors.py` as `selection_success_bg` and `selection_error_bg`.

### 3.2 log_tab.py

**File**: `src/casare_rpa/presentation/canvas/ui/panels/log_tab.py`

**Replacements**:

| Search | Replace | Context |
|--------|---------|---------|
| `"#1a3d1a"` | `THEME.selection_success_bg` | Success log background |
| `"#3d1a1a"` | `THEME.selection_error_bg` | Error log background |
| `"#3d3a1a"` | `THEME.selection_warning_bg` | Warning log background |

---

## Phase 4: Fix Syntax Highlighters

### 4.1 json_highlighter.py

**File**: `src/casare_rpa/presentation/canvas/ui/widgets/expression_editor/syntax/json_highlighter.py`

**Replacement**:

```python
# selection-color: #FFFFFF → selection-color: {THEME.text_primary}
```

### 4.2 python_highlighter.py

**File**: `src/casare_rpa/presentation/canvas/ui/widgets/expression_editor/syntax/python_highlighter.py`

**Same replacement as json_highlighter.py**

### 4.3 markdown_highlighter.py

**File**: `src/casare_rpa/presentation/canvas/ui/widgets/expression_editor/syntax/markdown_highlighter.py`

**Same replacement as json_highlighter.py**

### 4.4 yaml_highlighter.py

**File**: `src/casare_rpa/presentation/canvas/ui/widgets/expression_editor/syntax/yaml_highlighter.py`

**Same replacement as json_highlighter.py**

---

## Execution Commands (Serena MCP)

### Phase 1
```python
replace_content(
    relative_path="src/casare_rpa/presentation/canvas/theme_system/colors.py",
    needle=r"brand_google_hover: str = \"#5a95f5\"",
    repl="brand_google_light: str = \"#5a95f5\"  # Hover state for Google OAuth\n    brand_google_dark: str = \"#2d5a9e\"   # Disabled state for Google OAuth",
    mode="regex"
)
```

### Phase 2 Example (google_oauth_dialog.py)
```python
replace_content(
    relative_path="src/casare_rpa/presentation/canvas/ui/dialogs/google_oauth_dialog.py",
    needle=r"background-color: #4285f4;",
    repl="background-color: {THEME.brand_google};",
    mode="regex",
    allow_multiple_occurrences=True
)
```

---

## Success Criteria

1. All hardcoded OAuth colors replaced with THEME tokens
2. All panel selection backgrounds use THEME tokens
3. All syntax highlighters use THEME.text_primary for selection
4. No hardcoded hex colors remaining in target files
5. Canvas runs without visual regression

---

## Testing

```bash
# Verify tokens exist
python -c "from casare_rpa.presentation.canvas.theme import THEME; print(dir(THEME))"

# Run canvas
python manage.py canvas

# Check for remaining hardcoded colors (optional audit)
rg "#[0-9a-fA-F]{6}" src/casare_rpa/presentation/canvas/ui/dialogs/google_oauth_dialog.py
```

---

## Files Summary

| Phase | File | Changes |
|-------|------|---------|
| 1 | colors.py | +8 tokens |
| 2 | google_oauth_dialog.py | 3 replacements |
| 2 | antigravity_oauth_dialog.py | 3 replacements |
| 2 | credential_manager_dialog.py | 4 replacements |
| 3 | history_tab.py | 2 replacements |
| 3 | log_tab.py | 3 replacements |
| 4 | json_highlighter.py | 1 replacement |
| 4 | python_highlighter.py | 1 replacement |
| 4 | markdown_highlighter.py | 1 replacement |
| 4 | yaml_highlighter.py | 1 replacement |

**Total**: 10 files, ~27 replacements
