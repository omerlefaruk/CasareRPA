# Epic 5.1: Core Primitives for Component Library v2

**Status**: Planning
**Created**: 2025-12-29
**Phase**: Phase 5 - Component Library v2

---

## Overview

Create v2 versions of core UI primitive widgets that wrap Qt controls with consistent styling, behavior, and API. These primitives will be the building blocks for all higher-level v2 components.

**Key Principles**
- Use `THEME_V2` and `TOKENS_V2` exclusively (no v1 THEME/TOKENS)
- No hardcoded colors
- Zero animations (0ms motion policy)
- Dark-only styling
- Compact density (VS Code/Cursor-like)
- Consistent signal/slot patterns with `@Slot` decorator
- Full test coverage with pytest

---

## Component Specifications

### 5.1.1 Buttons

| Component | Variants | Props | Signals |
|-----------|----------|-------|---------|
| `PushButton` | primary, secondary, ghost, danger | text, icon, size, disabled, loading | clicked |
| `ToolButton` | icon-only, icon-text, toggle | icon, tooltip, checked, checked_icon | clicked, toggled |
| `ButtonGroup` | horizontal, vertical | buttons, exclusive | button_clicked |

**Sizes**: sm (22px), md (28px), lg (34px)
**Icon Sizes**: sm (16px), md (20px), lg (24px)

### 5.1.2 Inputs

| Component | Variants | Props | Signals |
|-----------|----------|-------|---------|
| `TextInput` | text, password, search | placeholder, value, clearable, readonly | text_changed, editing_finished |
| `SearchInput` | with-clear-button | placeholder, value, search_delay (50ms) | search_requested, text_changed |
| `SpinBox` | integer, decimal | min, max, step, value, prefix, suffix | value_changed |

**Sizes**: sm (22px), md (28px), lg (34px)

### 5.1.3 Select/Combobox

| Component | Variants | Props | Signals |
|-----------|----------|-------|---------|
| `Select` | single, searchable | items, placeholder, value, clearable | current_changed |
| `ComboBox` | editable, read-only | items, placeholder, value | current_changed, edit_text_changed |
| `ItemList` | single-select, multi-select | items, selected, icons | selection_changed |

### 5.1.4 Tabs

| Component | Variants | Props | Signals |
|-----------|----------|-------|---------|
| `TabWidget` | standard, closable, draggable | tabs, position, closable | tab_changed, tab_close_requested |
| `TabBar` | with-context-menu | tabs, position, tab_context_menu | tab_moved, tab_context_menu_requested |

**Tab height**: 32px
**Min tab width**: 90px

### 5.1.5 List/Tree/Table Base Styles

| Component | Purpose | Props | Signals |
|-----------|---------|-------|---------|
| `ListItem` | Single list item | text, icon, selected, enabled | clicked, double_clicked |
| `TreeItem` | Single tree item | text, icon, expanded, children | expanded_changed, clicked |
| `TableHeader` | Column header | text, sortable, sort_order | sort_requested |

**Row heights**: standard (28px), compact (22px)
**Selection**: `THEME_V2.bg_selected` (subtle blue)

### 5.1.6 Structural Components

| Component | Purpose | Props |
|-----------|---------|-------|
| `SectionHeader` | Labeled section with optional collapse | text, collapsible, collapsed |
| `Divider` | Visual separator | orientation, margin |
| `EmptyState` | Placeholder for empty content | icon, text, action_text |
| `Card` | Container with border/background | title, content_widget |

### 5.1.7 Selection Controls (NEW)

| Component | Purpose | Props | Signals |
|-----------|---------|-------|---------|
| `CheckBox` | Boolean selection | text, checked, tristate | checked_changed |
| `Switch` | Toggle switch (modern checkbox) | text, checked, on_text, off_text | checked_changed |
| `RadioGroup` | Single choice from options | items (value, label), selected | selection_changed |
| `RadioButton` | Single radio button | text, checked | clicked |

**Note**: Qt's native `QCheckBox` and `QRadioButton` wrapped with v2 styling.

### 5.1.8 Range Inputs (NEW)

| Component | Purpose | Props | Signals |
|-----------|---------|-------|---------|
| `Slider` | Numeric range input | min, max, value, step, show_value | value_changed, slider_pressed, slider_released |
| `ProgressBar` | Progress indicator | value, min, max, indeterminate, text | (display only) |
| `Dial` | Circular value input (optional) | min, max, value, wrapping | value_changed |

**Uses**: Qt's `QSlider` wrapped with v2 styling; custom `ProgressBar` for indeterminate support.

### 5.1.9 Feedback Components (NEW)

| Component | Purpose | Props | Signals |
|-----------|---------|-------|---------|
| `Badge` | Small count/status indicator | text, variant (dot, count, label), color | (display only) |
| `Tooltip` | Hover info popup | text, delay, position | (Qt tooltip wrapper) |
| `InlineAlert` | Contextual message | text, variant (info, warning, error, success), dismissible | dismissed |
| `Breadcrumb` | Navigation path | items (label, data), separator | item_clicked |
| `Avatar` | User/profile placeholder | text, image, size, variant (circle, square) | clicked |

**Note**: `Tooltip` uses Qt's native with v2 delay/styling; `InlineAlert` is a styled widget for in-place feedback.

### 5.1.10 Loading States (NEW)

| Component | Purpose | Props |
|-----------|---------|-------|
| `Skeleton` | Loading placeholder (shimmer effect) | width, height, variant (rect, circle, text) |
| `Spinner` | Circular loading indicator | size, stroke_width |

**Note**: "Shimmer" is static (no animation per zero-motion policy); use color bands instead.

---

## Files to Create

### New Widget Files
```
src/casare_rpa/presentation/canvas/ui/widgets/primitives/
├── __init__.py                    # Exports all primitives
├── base_primitive.py              # Base class for v2 primitives
├── buttons.py                     # PushButton, ToolButton, ButtonGroup
├── inputs.py                      # TextInput, SearchInput, SpinBox
├── selects.py                     # Select, ComboBox, ItemList
├── selection.py                   # CheckBox, Switch, RadioGroup, RadioButton
├── range.py                       # Slider, ProgressBar, Dial
├── tabs.py                        # TabWidget, TabBar v2 wrappers
├── lists.py                       # ListItem, TreeItem wrappers
├── structural.py                  # SectionHeader, Divider, EmptyState, Card
├── feedback.py                    # Badge, Tooltip, InlineAlert, Breadcrumb, Avatar
├── loading.py                     # Skeleton, Spinner
└── styles.py                      # Primitive-specific QSS (extends styles_v2.py)
```

### Test Files
```
tests/presentation/canvas/ui/widgets/primitives/
├── __init__.py
├── conftest.py                    # Shared fixtures (qapp, signal_capture)
├── test_buttons.py                # Button tests
├── test_inputs.py                 # Input tests
├── test_selects.py                # Select/combobox tests
├── test_selection.py              # CheckBox, Switch, Radio tests
├── test_range.py                  # Slider, ProgressBar tests
├── test_tabs.py                   # Tab tests
├── test_lists.py                  # List/tree tests
├── test_structural.py             # Structural component tests
├── test_feedback.py               # Badge, Tooltip, Alert, Breadcrumb tests
└── test_loading.py                # Skeleton, Spinner tests
```

### Style Gallery Extension
```
src/casare_rpa/presentation/canvas/theme_system/
└── primitive_gallery.py           # Visual verification dialog
```

---

## Files to Modify

### Exports
| File | Change |
|------|--------|
| `ui/widgets/__init__.py` | Add primitives imports |
| `ui/__init__.py` | Re-export primitives |
| `theme_system/__init__.py` | Add `show_primitive_gallery_v2` |

### Documentation
| File | Change |
|------|--------|
| `ui/_index.md` | Add primitives section |
| `.brain/context/current.md` | Update with Epic 5.1 progress |

---

## Implementation Steps

### Step 1: Base Primitive Class (Agent: builder)
**File**: `base_primitive.py`

Create `BasePrimitive` extending `BaseWidget` with v2-specific patterns:
- `_apply_v2_theme()` method using `THEME_V2`/`TOKENS_V2`
- `_set_size()` helper using `SizesV2`
- `_set_font()` helper using `TypographyV2`
- Common signals: `value_changed`, `state_changed`

```python
class BasePrimitive(QWidget, metaclass=QABCMeta):
    """Base class for v2 primitive widgets."""

    value_changed = Signal(object)
    state_changed = Signal(str, object)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setup_ui()
        self._apply_v2_theme()
        self.connect_signals()

    @abstractmethod
    def setup_ui(self) -> None: ...

    def _apply_v2_theme(self) -> None:
        """Apply v2 theme using THEME_V2 and TOKENS_V2."""
        self.setStyleSheet(self._get_v2_stylesheet())

    def _get_v2_stylesheet(self) -> str:
        """Get v2-specific stylesheet (override in subclasses)."""
        return ""
```

### Step 2: Buttons (Agent: builder)
**Files**: `buttons.py`, `test_buttons.py`

Create `PushButton` with variants via property selectors:
- Primary: `setProperty("primary", True)`
- Ghost: `setProperty("ghost", True)`
- Danger: `setProperty("danger", True)`
- Sizes: via `TOKENS_V2.sizes.button_sm/md/lg`

```python
class PushButton(BasePrimitive):
    def __init__(
        self,
        text: str = "",
        icon: QIcon | None = None,
        variant: Literal["primary", "secondary", "ghost", "danger"] = "secondary",
        size: Literal["sm", "md", "lg"] = "md",
        parent: QWidget | None = None,
    ):
        self._variant = variant
        self._size = size
        super().__init__(parent)
        # ... setup UI
```

### Step 3: Inputs (Agent: builder)
**Files**: `inputs.py`, `test_inputs.py`

Create `TextInput` wrapping `QLineEdit`:
- Placeholder text using `THEME_V2.text_muted`
- Clear button (icon from `icon_v2`)
- Search variant with magnifying glass icon

```python
class TextInput(BasePrimitive):
    text_changed = Signal(str)
    editing_finished = Signal()

    def __init__(
        self,
        placeholder: str = "",
        value: str = "",
        clearable: bool = False,
        password: bool = False,
        size: Literal["sm", "md", "lg"] = "md",
        parent: QWidget | None = None,
    ):
        # ...
```

### Step 4: Selects (Agent: builder)
**Files**: `selects.py`, `test_selects.py`

Create `Select` wrapping `QComboBox`:
- Items as list of tuples `(value, label, icon)`
- Searchable filter
- Clear button

### Step 5: Tabs (Agent: builder)
**Files**: `tabs.py`, `test_tabs.py`

Create `TabWidget` wrapping `QTabWidget`:
- Closable tabs
- Tab context menu
- Draggable tabs (optional, Epic 5.2)

### Step 6: Lists/Trees (Agent: builder)
**Files**: `lists.py`, `test_lists.py`

Create styled delegates and item wrappers:
- `ListItem` with hover/selected states
- `TreeItem` with expand/collapse
- Table header with sort indicators

### Step 7: Structural Components (Agent: builder)
**Files**: `structural.py`, `test_structural.py`

Create structural components:
- `SectionHeader` with collapse button
- `Divider` (horizontal/vertical)
- `EmptyState` with icon, text, action button
- `Card` container

### Step 8: Selection Controls (Agent: builder)
**Files**: `selection.py`, `test_selection.py`

Create selection controls wrapping Qt widgets:
- `CheckBox` wrapping `QCheckBox` with v2 styling
- `Switch` - toggle switch (pill-shaped track + circle thumb)
- `RadioGroup` - container managing radio button exclusivity
- `RadioButton` wrapping `QRadioButton`

```python
class Switch(BasePrimitive):
    """Toggle switch for boolean settings."""
    checked_changed = Signal(bool)

    def __init__(
        self,
        text: str = "",
        checked: bool = False,
        on_text: str = "On",
        off_text: str = "Off",
        parent: QWidget | None = None,
    ):
        # ... track pill (THEME_V2.primary) + circle thumb
```

### Step 9: Range Inputs (Agent: builder)
**Files**: `range.py`, `test_range.py`

Create range input components:
- `Slider` wrapping `QSlider` with v2 track/groove styling
- `ProgressBar` with determinate/indeterminate modes
- `Dial` wrapping `QDial` (optional, for future use)

```python
class ProgressBar(BasePrimitive):
    """Progress indicator with optional text."""
    def __init__(
        self,
        value: int = 0,
        min: int = 0,
        max: int = 100,
        indeterminate: bool = False,
        show_text: bool = True,
        parent: QWidget | None = None,
    ):
        # ... custom painted or styled QProgressBar
```

### Step 10: Feedback Components (Agent: builder)
**Files**: `feedback.py`, `test_feedback.py`

Create feedback/display components:
- `Badge` - small colored label/dot for counts/status
- `Tooltip` helper (wraps `QWidget.setToolTip()` with v2 delay)
- `InlineAlert` - styled banner with icon + text + dismiss button
- `Breadcrumb` - path navigation with clickable items
- `Avatar` - circular/square placeholder with initials or image

```python
class Badge(BasePrimitive):
    """Small indicator for counts or status."""
    def __init__(
        self,
        text: str = "",
        variant: Literal["dot", "count", "label"] = "count",
        color: str | None = None,  # defaults to THEME_V2.primary
        parent: QWidget | None = None,
    ):
        # ... QLabel subclass with v2 styling
```

### Step 11: Loading States (Agent: builder)
**Files**: `loading.py`, `test_loading.py`

Create loading placeholder components:
- `Skeleton` - placeholder with colored bands (no animation)
- `Spinner` - circular arc painted with `THEME_V2.primary`

```python
class Skeleton(BasePrimitive):
    """Loading placeholder (static, no shimmer animation)."""
    def __init__(
        self,
        width: int = 100,
        height: int = 20,
        variant: Literal["rect", "circle", "text"] = "rect",
        parent: QWidget | None = None,
    ):
        # ... paintEvent with THEME_V2.bg_component bands
```

### Step 12: Style Gallery (Agent: ui)
**File**: `primitive_gallery.py`

Create visual verification dialog:
- Showcase each primitive with all variants
- Interactive states (hover, pressed, disabled, focused)
- Size comparisons
- Export screenshot capability

### Step 13: Update Exports (Agent: refactor)
**Files**: `__init__.py` files

Add exports to:
- `ui/widgets/primitives/__init__.py`
- `ui/widgets/__init__.py`
- `ui/__init__.py`
- `theme_system/__init__.py`

---

## Parallel Opportunities

| Tasks | Can Parallel? | Dependencies |
|-------|---------------|--------------|
| Buttons + Inputs | Yes | Base primitive class |
| Selects + Selection + Range | Yes | Base primitive class |
| Tabs + Lists + Structural | Yes | Base primitive class |
| Feedback + Loading | Yes | Base primitive class |
| Tests for each | Yes | After component created |

**Recommended parallel groups**:
1. Group A: Base Primitive, Buttons, Inputs
2. Group B: Selects, Selection Controls, Range Inputs
3. Group C: Tabs, Lists, Structural
4. Group D: Feedback Components, Loading States
5. Group E: Tests (can run in parallel with implementation)
6. Group F: Style Gallery (after all components)

---

## Test Approach

### Test Categories
Each component test should cover:

1. **Instantiation**
   - Widget can be created
   - Default values are correct
   - Parent/child relationships work

2. **Signals**
   - All required signals exist
   - Signals emit with correct values
   - `@Slot` decorators used (no lambdas)

3. **Appearance**
   - Correct size applied
   - Theme colors used (no hardcoded values)
   - Variant-specific styling

4. **State**
   - Enabled/disabled states
   - Value changes propagate
   - Focus states

5. **Edge Cases**
   - Empty values
   - Very long text
   - Rapid state changes
   - None/null handling

### Test Fixtures (conftest.py)
```python
@pytest.fixture(scope="module")
def qapp():
    """QApplication for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app

@pytest.fixture
def signal_capture():
    """Capture Qt signals for testing."""
    return SignalCapture()

@pytest.fixture
def mock_theme():
    """Mock THEME_V2 for testing."""
    return THEME_V2
```

### Headless Testing
Run tests with `QT_QPA_PLATFORM=offscreen`:
```bash
QT_QPA_PLATFORM=offscreen pytest tests/presentation/canvas/ui/widgets/primitives/ -v
```

---

## Risks and Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Hardcoded colors slip in | Theme not consistent | Code review: grep for `#[0-9a-f]` and `rgb(` |
| State management inconsistent | Bugs in complex widgets | Use `_state` dict pattern from BaseWidget |
| Signal/slot memory leaks | Performance degradation | Use weak references where appropriate |
| Test flakiness with Qt | Unreliable CI | Use `qapp` fixture, proper cleanup |
| API inconsistency | Confusing for users | Follow strict naming conventions |

---

## Success Criteria

Epic 5.1 is complete when:

1. All primitive widgets are implemented and tested
2. Style gallery shows all components with variants
3. No hardcoded colors in any primitive file
4. All tests pass with `pytest tests/presentation/canvas/ui/widgets/primitives/ -v`
5. Code coverage > 80% for primitives
6. `ui/widgets/primitives/` index updated in `_index.md`
7. No lint errors (ruff, mypy)

---

## Agent Assignments

| Step | Agent | Output |
|------|-------|--------|
| 1. Base class | builder | `base_primitive.py` |
| 2. Buttons | builder | `buttons.py` + `test_buttons.py` |
| 3. Inputs | builder | `inputs.py` + `test_inputs.py` |
| 4. Selects | builder | `selects.py` + `test_selects.py` |
| 5. Tabs | builder | `tabs.py` + `test_tabs.py` |
| 6. Lists | builder | `lists.py` + `test_lists.py` |
| 7. Structural | builder | `structural.py` + `test_structural.py` |
| 8. Selection Controls | builder | `selection.py` + `test_selection.py` |
| 9. Range Inputs | builder | `range.py` + `test_range.py` |
| 10. Feedback | builder | `feedback.py` + `test_feedback.py` |
| 11. Loading States | builder | `loading.py` + `test_loading.py` |
| 12. Gallery | ui | `primitive_gallery.py` |
| 13. Exports | refactor | Updated `__init__.py` files |
| 14. Docs | docs | Updated `_index.md` |

---

## Next Epic

After Epic 5.1:
- **Epic 5.2**: Advanced Components (DataGrid, TreeView, SplitContainer)
- **Epic 5.3**: Form Components (Form, FormField, Validation)
- **Epic 5.4**: Feedback Components (Toast, Progress, Badge)

---

*Last updated: 2025-12-29*
