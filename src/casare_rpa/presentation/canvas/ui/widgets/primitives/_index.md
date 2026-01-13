# UI Primitives v2 - Epic 5.1

Component Library v2: 11 modules, ~50 reusable components.

## Modules

| Module | Components |
|--------|------------|
| `base_primitive.py` | BasePrimitive, SizeVariant, FontVariant, MarginPreset |
| `buttons.py` | PushButton, ToolButton, ButtonGroup |
| `inputs.py` | TextInput, SearchInput, SpinBox, DoubleSpinBox |
| `selects.py` | Select, ComboBox, ItemList |
| `selection.py` | CheckBox, Switch, RadioButton, RadioGroup |
| `range.py` | Slider, ProgressBar, Dial |
| `tabs.py` | TabWidget, TabBar, Tab dataclass |
| `lists.py` | ListItem, TreeItem, TableHeader, style helpers |
| `structural.py` | SectionHeader, Divider, EmptyState, Card |
| `feedback.py` | Badge, InlineAlert, Breadcrumb, Avatar, set_tooltip |
| `loading.py` | Skeleton, Spinner |

## Usage

```python
from casare_rpa.presentation.canvas.ui.widgets.primitives import (
    PushButton, TextInput, CheckBox, Switch, Slider
)

# All components use THEME_V2/TOKENS_V2 (zero hardcoded colors)
btn = PushButton(text="Save", variant="primary", size="md")
input = TextInput(placeholder="Enter text", clearable=True)
checkbox = CheckBox(text="Enable feature", checked=True)
slider = Slider(min=0, max=100, value=50, show_value=True)
```

## Gallery

Visual verification via `primitive_gallery.py`:

```python
from casare_rpa.presentation.canvas.theme_system import show_primitive_gallery_v2
show_primitive_gallery_v2()
```

## Tests

`tests/presentation/canvas/ui/widgets/primitives/` - 450+ tests

## Cross-References

- Theme tokens: `theme_system/tokens_v2.py`
- Icon provider: `theme_system/icons_v2.py`
- UX Plan: `docs/UX_REDESIGN_PLAN.md` Phase 5 Epic 5.1
