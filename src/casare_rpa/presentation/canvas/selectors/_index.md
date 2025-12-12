# Canvas Selectors Index

Quick reference for element selector UI components. Use for fast discovery.

## Overview

| Aspect | Description |
|--------|-------------|
| Purpose | UI components for element selection (browser/desktop) |
| Files | 44 files across subdirectories |
| Exports | 30 total exports |

## Directory Structure

| Directory | Files | Description |
|-----------|-------|-------------|
| `tabs/` | 6 | Selector mode tabs (Browser, Desktop, OCR, Image) |
| `state/` | 2 | State management |
| `widgets/` | 8 | Reusable selector widgets |
| `ui_explorer/` | 16 | Advanced UI explorer |

## Main Dialogs

| Export | Source | Description |
|--------|--------|-------------|
| `ElementSelectorDialog` | `element_selector_dialog.py` | Streamlined element picker (recommended) |
| `UIExplorerDialog` | `ui_explorer/` | Advanced full-featured UI explorer |
| `UnifiedSelectorDialog` | `unified_selector_dialog.py` | Legacy unified dialog |
| `UIExplorerToolbar` | `ui_explorer/toolbar.py` | UI explorer toolbar |

## State Management

| Export | Source | Description |
|--------|--------|-------------|
| `ElementSelectorState` | `state/selector_state.py` | Centralized selector state |
| `StateManager` | `state/selector_state.py` | Qt signals-based state management |
| `AttributeRow` | `state/selector_state.py` | Attribute row data |
| `ValidationStatus` | `state/selector_state.py` | VALID, INVALID, UNKNOWN |
| `PickingMode` | `state/selector_state.py` | BROWSER, DESKTOP, OCR, IMAGE |

## History

| Export | Source | Description |
|--------|--------|-------------|
| `SelectorHistory` | `selector_history.py` | JSON-based history storage |
| `SelectorHistoryEntry` | `selector_history.py` | History entry data |
| `get_selector_history()` | `selector_history.py` | Get history singleton |

## Widgets

| Export | Source | Description |
|--------|--------|-------------|
| `ToolbarWidget` | `widgets/toolbar_widget.py` | Pick/Stop/Mode controls |
| `ModeButton` | `widgets/toolbar_widget.py` | Mode selection button |
| `ElementPreviewWidget` | `widgets/element_preview_widget.py` | HTML preview with properties |
| `SelectorBuilderWidget` | `widgets/selector_builder_widget.py` | Attribute rows with scores |
| `AttributeRowWidget` | `widgets/selector_builder_widget.py` | Single attribute row |
| `AnchorWidget` | `widgets/anchor_widget.py` | Anchor configuration |
| `AdvancedOptionsWidget` | `widgets/advanced_options_widget.py` | Fuzzy/CV/Image options |
| `PickerToolbar` | `widgets/picker_toolbar.py` | Floating toolbar during picking |

## Data Classes

| Export | Source | Description |
|--------|--------|-------------|
| `SelectorResult` | `tabs/base_tab.py` | Selector result data |
| `SelectorStrategy` | `tabs/base_tab.py` | Selection strategy enum |
| `AnchorData` | `tabs/base_tab.py` | Anchor element data |

## UI Explorer Components

Located in `ui_explorer/` subdirectory:

### Panels
- `VisualTreePanel` - Element tree visualization
- `PropertyExplorerPanel` - Property inspection
- `SelectorEditorPanel` - Selector editing
- `SelectorPreviewPanel` - Selector preview
- `SelectedAttrsPanel` - Selected attributes

### Models
- `ElementModel` - Element data model
- `SelectorModel` - Selector data model
- `AnchorModel` - Anchor data model

### Widgets
- `AttributeRow` - Attribute row widget
- `AnchorPanel` - Anchor configuration panel
- `XmlHighlighter` - XML syntax highlighting
- `StatusBarWidget` - Status bar

## Usage Patterns

```python
# Recommended: ElementSelectorDialog
from casare_rpa.presentation.canvas.selectors import (
    ElementSelectorDialog,
    SelectorResult,
)

dialog = ElementSelectorDialog(parent=self)
if dialog.exec():
    result: SelectorResult = dialog.get_result()
    selector = result.selector
    strategy = result.strategy

# Advanced: UIExplorerDialog
from casare_rpa.presentation.canvas.selectors import (
    UIExplorerDialog,
)

explorer = UIExplorerDialog(parent=self)
explorer.show()

# State management
from casare_rpa.presentation.canvas.selectors import (
    ElementSelectorState,
    StateManager,
    PickingMode,
)

state = ElementSelectorState()
state.picking_mode = PickingMode.BROWSER
state.selector = "#my-element"

# History
from casare_rpa.presentation.canvas.selectors import (
    get_selector_history,
    SelectorHistoryEntry,
)

history = get_selector_history()
entries = history.get_recent(10)
history.add(SelectorHistoryEntry(selector="#btn", mode="browser"))
```

## Selector Modes

| Mode | Description |
|------|-------------|
| `BROWSER` | Web element via Playwright |
| `DESKTOP` | Windows UI element via UIA |
| `OCR` | Text recognition |
| `IMAGE` | Image matching |

## Related Modules

| Module | Relation |
|--------|----------|
| `canvas.controllers.selector_controller` | Selector coordination |
| `nodes.browser/` | Browser automation nodes |
| `nodes.desktop_nodes/` | Desktop automation nodes |
| `desktop.context` | Desktop automation context |
