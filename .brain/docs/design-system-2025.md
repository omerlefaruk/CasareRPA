# Design System 2025

CasareRPA's unified design token system.

## Overview

A minimal, semantic design system following 2025 best practices.
All tokens are frozen dataclasses - single source of truth.

## Token Structure

```python
from casare_rpa.presentation.canvas.theme_system import TOKENS, THEME

# Spacing (4px base)
TOKENS.spacing.md    # 16px - default gap
TOKENS.spacing.lg    # 24px - large gap

# Sizes
TOKENS.sizes.button_md   # 32px height
TOKENS.sizes.dialog_md   # 600px width

# Border Radius
TOKENS.radius.sm    # 4px - buttons, inputs
TOKENS.radius.md    # 8px - cards, panels

# Typography
TOKENS.typography.body    # 12pt default
TOKENS.typography.heading_l  # 14pt

# Colors (semantic)
THEME.primary      # Electric Indigo (#6366f1)
THEME.bg_surface   # Dark panel (#18181b)
THEME.text_primary # White text (#f4f4f5)
THEME.success      # Emerald (#10b981)
THEME.error        # Red (#ef4444)
```

## Color Palette

### Backgrounds
| Name | Hex | Usage |
|------|-----|-------|
| `bg_canvas` | #09090b | Main canvas |
| `bg_surface` | #18181b | Panels, dialogs |
| `bg_elevated` | #27272a | Cards, headers |
| `bg_component` | #3f3f46 | Inputs, dropdowns |
| `bg_border` | #52525b | Borders |

### Text
| Name | Hex | Usage |
|------|-----|-------|
| `text_primary` | #f4f4f5 | Headings, labels |
| `text_secondary` | #a1a1aa | Descriptions |
| `text_muted` | #71717a | Placeholders |
| `text_disabled` | #52525b | Disabled |

### Semantic
| Name | Hex | Usage |
|------|-----|-------|
| `primary` | #6366f1 | Brand color |
| `success` | #10b981 | Success states |
| `warning` | #f59e0b | Warnings |
| `error` | #ef4444 | Errors |
| `info` | #3b82f6 | Information |

## Migration

Old → New token mapping:

| Old | New |
|-----|-----|
| `TOKENS.sizes.button_height_sm` | `TOKENS.sizes.button_sm` |
| `TOKENS.radii.sm` | `TOKENS.radius.sm` |
| `THEME.bg_darkest` | `THEME.bg_canvas` |
| `THEME.accent_primary` | `THEME.primary` |

## See Also

- `.brain/plans/design-system-unified-2025.md` - Full refactor plan
