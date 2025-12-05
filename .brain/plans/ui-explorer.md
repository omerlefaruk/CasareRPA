# UI Explorer Dialog Design Plan

## Overview

A UiPath-style UI Explorer window for deep element inspection and selector building. Complements the existing UnifiedSelectorDialog with advanced features:
- Full visual tree navigation
- Property explorer
- Selector attribute editor (checkbox-based)
- Multi-framework support (Browser/Desktop)

## Target Screenshot Analysis

```
+-------------------------------------------------------------------------------+
| Validate | Indicate Element | Indicate Anchor | Repair | Highlight | Options  |
+-------------------------------------------------------------------------------+
| VISUAL TREE (Left)      | SELECTOR EDITOR (Middle)    | SELECTED ITEMS (Right)|
| [+] html                | [x] tag   html               | [x] tag               |
|   [+] body              | [x] class mysite-container   | [x] class             |
|     [+] div.container   | [ ] css-selector ...         | [x] css-selector      |
|       [-] button#submit | [ ] innertext                | [x] innertext         |
|         "Start"         | [x] visibleinnertext Start   | [ ] isleaf            |
|                         | [ ] parentclass              | [x] parentclass       |
|                         |                              | [x] visibleinnertext  |
+-------------------------+------------------------------+-----------------------+
| PROPERTY EXPLORER (Bottom-Left)                                               |
| aaname        |                                                               |
| aastate       | focusable                                                     |
| app           | msedge.exe                                                    |
| AppPath       | C:\Program Files\...                                          |
| class         | mysite-btn                                                    |
| cls           |                                                               |
| css-selector  | #submit                                                       |
+-------------------------------------------------------------------------------+
| PREVIEW:  <html app='msedge.exe' title='Rpa Challenge' />                    |
|           <button class='mysite-btn' id='submit' text='Start' />             |
+-------------------------------------------------------------------------------+
| Target Element: 'BUTTON'                              | UIAutomation v23.4.4  |
+-------------------------------------------------------------------------------+
```

## Key Differences from UnifiedSelectorDialog

| Feature | UnifiedSelectorDialog | UI Explorer |
|---------|----------------------|-------------|
| Primary Use | Quick element picking | Deep inspection |
| Visual Tree | No | Yes (full hierarchy) |
| Property Explorer | Minimal (preview) | Full property table |
| Selector Editor | Generated list | Checkbox attribute builder |
| Attribute Selection | Auto | Manual toggle |
| Preview | Basic | UiPath XML format |

## Integration Strategy

1. **Standalone dialog** - NOT a replacement for UnifiedSelectorDialog
2. **Launch button** in UnifiedSelectorDialog toolbar ("Open Explorer")
3. **Launch from Properties Panel** - icon next to selector inputs
4. **Bidirectional** - Pass selected element back to UnifiedSelectorDialog

## Component Breakdown

### 1. Toolbar (UIExplorerToolbar)

```
+---------------------------------------------------------------------------+
| [Validate] [Indicate Element] [Indicate Anchor] [Repair] [Highlight] [Opt]|
+---------------------------------------------------------------------------+
```

**Buttons:**
| Button | State | Action |
|--------|-------|--------|
| Validate | Default | Test current selector |
| | Success | Green indicator |
| | Fail | Red indicator |
| Indicate Element | Default | Start picker mode |
| | Active | Pulsing blue |
| Indicate Anchor | Default | Pick anchor element |
| | Active | Pulsing amber |
| Repair | Default | Try healing |
| | Disabled | When no selector |
| Highlight | Default | Flash element on screen |
| | Active | Toggle state |
| Options | Default | Settings dropdown |

**Qt:** QToolBar with QToolButtons

### 2. Visual Tree Panel (VisualTreePanel)

**Widget:** QTreeWidget with lazy loading

**Tree Item Data:**
- Icon (control type)
- Display text: `{ControlType}: {Name} [{AutomationId}]`
- Element reference (browser: ElementFingerprint, desktop: DesktopElement)

**Features:**
- Lazy load children on expand (limit 50)
- Search/filter input
- Context menu (Copy XPath, Highlight, Refresh)
- Auto-expand to selected element

**States:**
| State | Style |
|-------|-------|
| Normal | #e0e0e0 text |
| Selected | #3b82f6 bg, white text |
| Hover | #2a2a2a bg |
| Disabled | #888888 italic |
| Hidden | #aaaaaa text |

**Qt:** Reuse ElementTreeWidget pattern, extend for browser DOM

### 3. Selector Editor Panel (SelectorEditorPanel)

**Layout:**
```
+-----------------------------------------------+
| [x] tag        html                           |
| [x] class      mysite-container               |
| [ ] css-selector  body > div.main > ...       |
| [x] innertext  (empty)                        |
| [x] isleaf     True                           |
| [ ] parentclass wrapper                       |
+-----------------------------------------------+
```

**Row Widget (SelectorAttributeRow):**
- Checkbox (include in selector)
- Attribute name label
- Value display/edit

**States:**
| State | Checkbox | Value Style |
|-------|----------|-------------|
| Checked/Included | Checked, blue accent | Bold, #60a5fa |
| Unchecked | Unchecked | Normal, #888 |
| Required | Checked, disabled | Bold, green |
| Invalid | Red border | Red text |

**Qt:** QScrollArea with QVBoxLayout of row widgets

### 4. Selected Items Panel (SelectedAttributesPanel)

**Purpose:** Quick view of which attributes are in selector

**Layout:** Simple checkbox list mirror of editor

**Qt:** QListWidget with checkable items, synced to editor

### 5. Property Explorer Panel (PropertyExplorerPanel)

**Widget:** QTableWidget (2 columns)

**Properties (Browser):**
- tag, id, class, name, type, value
- href, src, alt, title
- data-* attributes
- aria-* attributes
- innerText, visibleInnerText
- css-selector, xpath

**Properties (Desktop):**
- Name, AutomationId, ControlType, ClassName
- ProcessId, WindowHandle
- IsEnabled, IsOffscreen, IsKeyboardFocusable
- BoundingRectangle
- AccessKey, AcceleratorKey

**States:**
| State | Style |
|-------|-------|
| Normal | Standard table row |
| Computed | Italic text |
| Inherited | Gray text |
| Selected | Highlight row |

**Qt:** QTableWidget with custom item styling

### 6. Selector Preview Panel (SelectorPreviewPanel)

**Format:** UiPath-style XML

```xml
<html app='msedge.exe' title='Rpa Challenge' />
<button class='btn-primary' id='submit' innertext='Start' />
```

**Widget:** QTextEdit (monospace, syntax highlighting)

**Features:**
- Auto-update on attribute toggle
- Copy button
- Edit mode (manual entry)

**Qt:** QTextEdit with QSyntaxHighlighter for XML

### 7. Status Bar (UIExplorerStatusBar)

```
Target Element: 'BUTTON'                    | UIAutomation v23.4.4
```

**Sections:**
- Element type display
- Framework/version info
- Element count (if multiple matches)

**Qt:** QStatusBar with custom widgets

## File Structure

```
src/casare_rpa/presentation/canvas/selectors/
+-- ui_explorer/
|   +-- __init__.py
|   +-- ui_explorer_dialog.py      # Main dialog
|   +-- toolbar.py                 # UIExplorerToolbar
|   +-- panels/
|   |   +-- __init__.py
|   |   +-- visual_tree_panel.py   # Tree with DOM/UI hierarchy
|   |   +-- selector_editor_panel.py
|   |   +-- selected_attrs_panel.py
|   |   +-- property_explorer_panel.py
|   |   +-- selector_preview_panel.py
|   +-- models/
|   |   +-- __init__.py
|   |   +-- element_model.py       # Unified element abstraction
|   |   +-- selector_model.py      # Selector state management
|   +-- widgets/
|       +-- __init__.py
|       +-- attribute_row.py       # Checkbox + name + value
|       +-- xml_highlighter.py     # QSyntaxHighlighter
```

## Integration Points

### 1. UnifiedSelectorDialog Integration

```python
# In unified_selector_dialog.py toolbar creation:
explorer_btn = ModeToolButton("UI", "Open UI Explorer")
explorer_btn.clicked.connect(self._on_open_explorer)

def _on_open_explorer(self):
    from .ui_explorer import UIExplorerDialog
    dialog = UIExplorerDialog(
        parent=self,
        mode=self._current_mode,  # browser/desktop
        browser_page=self._browser_page,
        initial_element=self._element_fingerprint,
    )
    dialog.element_selected.connect(self._on_explorer_element)
    dialog.exec()
```

### 2. Properties Panel Integration

```python
# In properties_panel.py or node widget:
def _create_selector_row(self):
    explorer_btn = QPushButton("...")
    explorer_btn.setToolTip("Open UI Explorer")
    explorer_btn.clicked.connect(self._on_open_explorer)
```

### 3. Shared Components

Reuse from existing:
- `ElementTreeWidget` - extend for browser DOM
- `SelectorValidator` - validation logic
- `SelectorStrategy` - strategy dataclass
- `SelectorResult` - result dataclass
- Tab base classes - `BaseSelectorTab` pattern

## Layout Specification

```
+-----------------------------------------------------------------------------------+
| UIExplorerToolbar (fixed height 48px)                                             |
+---------------+---------------------------+---------------------+-----------------+
| Visual Tree   | Selector Editor           | Selected Attrs      | Property        |
| (25%)         | (35%)                     | (15%)               | Explorer (25%)  |
|               |                           |                     |                 |
| QTreeWidget   | QScrollArea               | QListWidget         | QTableWidget    |
| [splitter]    | [splitter]                | [splitter]          |                 |
+---------------+---------------------------+---------------------+-----------------+
| Selector Preview (fixed height 80px)                                              |
| QTextEdit (monospace, 2-3 lines)                                                  |
+-----------------------------------------------------------------------------------+
| Status Bar (fixed height 24px)                                                    |
+-----------------------------------------------------------------------------------+
```

**Splitter Setup:**
- Main: QSplitter(Horizontal) with 4 widgets
- Ratios: 25% / 35% / 15% / 25%
- Min widths: 200 / 250 / 120 / 200

## State Management

### ElementModel

```python
@dataclass
class UIExplorerElement:
    """Unified element representation."""
    source: str  # "browser" | "desktop"
    tag_or_control: str
    attributes: Dict[str, str]
    rect: Optional[Dict[str, int]]
    children_loaded: bool = False
    fingerprint: Optional[ElementFingerprint] = None
    desktop_element: Optional[DesktopElement] = None
```

### SelectorModel

```python
@dataclass
class SelectorAttribute:
    """Single attribute in selector."""
    name: str
    value: str
    included: bool = False
    required: bool = False
    editable: bool = True

class SelectorModel(QObject):
    """Manages selector state, emits changes."""
    changed = Signal()

    def __init__(self):
        self._attributes: List[SelectorAttribute] = []

    def toggle_attribute(self, name: str):
        ...

    def to_xml(self) -> str:
        ...

    def to_selector_string(self) -> str:
        ...
```

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| F5 | Refresh tree |
| Ctrl+E | Start element picking |
| Ctrl+A | Start anchor picking |
| Ctrl+H | Toggle highlight |
| Ctrl+V | Validate selector |
| Ctrl+C | Copy selector |
| Escape | Cancel picking / Close |

## Implementation Steps

### Phase 1: Core Structure (Est. 4-6 hours)
1. Create `ui_explorer/` directory structure
2. Implement `UIExplorerDialog` main layout
3. Implement `UIExplorerToolbar` with buttons
4. Wire up basic splitter layout

### Phase 2: Visual Tree (Est. 3-4 hours)
1. Extend `ElementTreeWidget` for browser DOM
2. Create `VisualTreePanel` wrapper
3. Implement lazy loading for browser elements
4. Add search/filter

### Phase 3: Selector Editor (Est. 4-5 hours)
1. Create `SelectorAttributeRow` widget
2. Create `SelectorEditorPanel`
3. Implement `SelectorModel` state management
4. Wire checkbox toggles to model

### Phase 4: Property Explorer (Est. 2-3 hours)
1. Create `PropertyExplorerPanel`
2. Populate from element selection
3. Copy value on double-click

### Phase 5: Preview & Integration (Est. 3-4 hours)
1. Create `SelectorPreviewPanel` with XML highlight
2. Create `XMLHighlighter`
3. Wire to SelectorModel
4. Add to UnifiedSelectorDialog

### Phase 6: Polish (Est. 2-3 hours)
1. Keyboard shortcuts
2. Status bar updates
3. Error handling
4. Testing

## Open Questions

1. **Browser DOM access** - How to get full DOM tree from Playwright page?
   - Current: Only selected element fingerprint
   - Needed: Full hierarchy traversal
   - Solution: New JS injection to walk DOM

2. **Anchor relationships** - How to visually show anchor-target connections?
   - Line drawing between tree items?
   - Separate anchor panel?

3. **XML vs JSON selector format** - UiPath uses XML, current system uses JSON
   - Keep both formats?
   - Convert on export?

4. **Performance** - Large DOM trees (1000s of elements)
   - Virtual scrolling for tree?
   - Limit depth?

5. **Desktop picker integration** - Reuse existing or new implementation?
   - Existing `activate_element_picker` works well
   - May need to capture more properties

## Dependencies

- Existing: `ElementTreeWidget`, `SelectorValidator`, `BaseSelectorTab`
- New: `QSyntaxHighlighter` subclass for XML
- External: None (pure Qt)
