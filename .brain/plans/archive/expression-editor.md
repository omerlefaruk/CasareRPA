# Expression Editor Feature - Implementation Plan

**Status**: IMPLEMENTED
**Created**: 2025-12-14
**Completed**: 2025-12-14
**Target**: CasareRPA Canvas (Presentation Layer)
**Index**: `presentation/canvas/ui/widgets/expression_editor/_index.md`

---

## Completion Notes

All phases have been implemented:

- **Phase 1**: Core Infrastructure - ExpressionEditorPopup, BaseExpressionEditor, EditorFactory, ExpandButton
- **Phase 2**: Code Editor - CodeExpressionEditor with line numbers, PythonHighlighter, JavaScriptHighlighter
- **Phase 3**: Markdown Editor - MarkdownEditor with toolbar and live preview
- **Phase 4**: Rich Text Editor - RichTextEditor with variable autocomplete on {{ trigger
- **Phase 5**: Integration - base_visual_node.py integration with _open_expression_editor()
- **Phase 6**: Styling - THEME compliance, fade animations, resize handles

### Files Created

| File | Lines | Status |
|------|-------|--------|
| `expression_editor/__init__.py` | ~68 | Complete |
| `expression_editor/base_editor.py` | ~142 | Complete |
| `expression_editor/expression_editor_popup.py` | ~642 | Complete |
| `expression_editor/editor_factory.py` | ~152 | Complete |
| `expression_editor/code_editor.py` | ~368 | Complete |
| `expression_editor/markdown_editor.py` | ~471 | Complete |
| `expression_editor/rich_text_editor.py` | ~374 | Complete |
| `expression_editor/syntax/__init__.py` | ~27 | Complete |
| `expression_editor/syntax/python_highlighter.py` | ~180 | Complete |
| `expression_editor/syntax/javascript_highlighter.py` | ~180 | Complete |
| `expression_editor/syntax/markdown_highlighter.py` | ~120 | Complete |
| `expression_editor/widgets/__init__.py` | ~25 | Complete |
| `expression_editor/widgets/expand_button.py` | ~84 | Complete |
| `expression_editor/widgets/toolbar.py` | ~150 | Complete |
| `expression_editor/widgets/variable_autocomplete.py` | ~200 | Complete |

**Total**: ~2,500 lines of new code

---

## Original Plan (Below)

## Overview

Detailed expression editor feature providing enhanced text editing capabilities for node properties. Opens as a hover/popup window with context-aware editing modes, variable insertion, and autocomplete support.

## Feature Summary

| Feature | Description |
|---------|-------------|
| **Popup Window** | Tool-style frameless window with shadow, draggable header, resize handles |
| **Editor Modes** | Code (Python/JS/CMD), Markdown (HTML email), Rich Text (general) |
| **Variable Support** | Integration with existing `VariablePickerPopup` pattern |
| **Autocomplete** | Variable and expression autocomplete with fuzzy matching |
| **Theme** | VSCode Dark+ via THEME system |

---

## Component Architecture

### Core Components

```
src/casare_rpa/presentation/canvas/ui/widgets/expression_editor/
├── __init__.py                     # Public exports
├── expression_editor_popup.py      # Main popup container (like NodeOutputPopup)
├── editor_factory.py               # Factory for creating appropriate editor
├── base_editor.py                  # Abstract base for all editors
├── code_editor.py                  # Python/JS/CMD with syntax highlighting
├── markdown_editor.py              # Rich markdown for emails
├── rich_text_editor.py             # General text with variable support
├── syntax/
│   ├── __init__.py
│   ├── python_highlighter.py       # Python syntax highlighter
│   ├── javascript_highlighter.py   # JavaScript syntax highlighter
│   └── markdown_highlighter.py     # Markdown syntax highlighter
└── widgets/
    ├── __init__.py
    ├── expand_button.py            # Button to trigger popup
    ├── variable_autocomplete.py    # Autocomplete dropdown
    └── toolbar.py                  # Editor toolbar (bold, italic, etc.)
```

### Class Hierarchy

```
BaseExpressionEditor (ABC)
├── CodeExpressionEditor
│   ├── PythonEditor
│   ├── JavaScriptEditor
│   └── CommandEditor
├── MarkdownEditor
└── RichTextEditor
```

---

## Detailed Component Specifications

### 1. ExpressionEditorPopup (Main Container)

**File**: `expression_editor_popup.py`

**Based on**: `node_output_popup.py` pattern

```python
class ExpressionEditorPopup(QFrame):
    """
    Popup container for expression editing.

    Features:
    - Tool window with frameless hint
    - Drop shadow effect
    - Draggable header
    - Corner resize handles
    - Fade-in animation (150ms)
    - Keyboard shortcuts (Escape, Ctrl+Enter to accept)

    Signals:
        accepted: Emitted when user confirms changes (str: value)
        cancelled: Emitted when user cancels
        value_changed: Emitted on any content change
    """

    DEFAULT_WIDTH = 600
    DEFAULT_HEIGHT = 400
    MIN_WIDTH = 400
    MIN_HEIGHT = 250
```

**Key Methods**:
- `show_for_widget(widget: QWidget, editor_type: EditorType, initial_value: str)`
- `get_value() -> str`
- `set_value(value: str)`

### 2. BaseExpressionEditor (Abstract Base)

**File**: `base_editor.py`

```python
class EditorType(Enum):
    """Editor type enumeration."""
    CODE_PYTHON = "python"
    CODE_JAVASCRIPT = "javascript"
    CODE_CMD = "cmd"
    MARKDOWN = "markdown"
    RICH_TEXT = "rich_text"


class BaseExpressionEditor(QWidget, ABC):
    """
    Abstract base class for all expression editors.

    Provides:
    - Variable insertion interface
    - Value get/set
    - Change tracking
    - Common toolbar hooks
    """

    value_changed = Signal(str)

    @abstractmethod
    def get_value(self) -> str: ...

    @abstractmethod
    def set_value(self, value: str) -> None: ...

    @abstractmethod
    def insert_at_cursor(self, text: str) -> None: ...

    @abstractmethod
    def get_cursor_position(self) -> int: ...

    def insert_variable(self, var_text: str) -> None:
        """Insert variable reference at cursor."""
        self.insert_at_cursor(var_text)
```

### 3. CodeExpressionEditor

**File**: `code_editor.py`

```python
class CodeExpressionEditor(BaseExpressionEditor):
    """
    Code editor with syntax highlighting.

    Features:
    - QPlainTextEdit with line numbers
    - Language-specific syntax highlighting
    - Tab/indent handling
    - Bracket matching
    - Variable insertion ({{var}} syntax)
    """

    def __init__(
        self,
        language: str = "python",
        parent: Optional[QWidget] = None
    ) -> None:
        ...
```

**Supported Languages**:
| Language | Highlighter | Use Case |
|----------|-------------|----------|
| Python | `PythonHighlighter` | Python script nodes |
| JavaScript | `JavaScriptHighlighter` | Browser evaluate nodes |
| CMD | `CommandHighlighter` | Command/shell nodes |

### 4. MarkdownEditor

**File**: `markdown_editor.py`

```python
class MarkdownEditor(BaseExpressionEditor):
    """
    Markdown editor for email HTML body.

    Features:
    - Side-by-side edit/preview (optional)
    - Toolbar: bold, italic, link, heading, list
    - HTML preview rendering
    - Image insertion
    - Variable insertion in markdown
    """
```

**Toolbar Actions**:
- Bold (Ctrl+B)
- Italic (Ctrl+I)
- Heading (Ctrl+H)
- Link (Ctrl+K)
- Bullet List
- Numbered List
- Code Block

### 5. RichTextEditor

**File**: `rich_text_editor.py`

```python
class RichTextEditor(BaseExpressionEditor):
    """
    General-purpose rich text editor.

    Features:
    - QTextEdit base
    - Variable insertion with autocomplete
    - Expression syntax support
    - Inline validation
    """
```

### 6. Syntax Highlighters

#### PythonHighlighter

**File**: `syntax/python_highlighter.py`

**Colors (VSCode Dark+)**:
| Token | Color | Example |
|-------|-------|---------|
| Keywords | `#C586C0` | `def`, `if`, `for`, `import` |
| Functions | `#DCDCAA` | `print`, `len`, custom functions |
| Strings | `#CE9178` | `"hello"`, `'world'` |
| Numbers | `#B5CEA8` | `123`, `3.14` |
| Comments | `#6A9955` | `# comment` |
| Built-ins | `#4EC9B0` | `True`, `False`, `None` |
| Decorators | `#DCDCAA` | `@property` |
| Variables | `#9CDCFE` | Variable references |

#### JavaScriptHighlighter

**File**: `syntax/javascript_highlighter.py`

**Colors (VSCode Dark+)**:
| Token | Color | Example |
|-------|-------|---------|
| Keywords | `#C586C0` | `const`, `let`, `function`, `async` |
| Functions | `#DCDCAA` | `console.log`, custom |
| Strings | `#CE9178` | `"hello"`, template literals |
| Numbers | `#B5CEA8` | `123`, `3.14` |
| Comments | `#6A9955` | `// comment`, `/* block */` |
| Built-ins | `#4EC9B0` | `document`, `window` |
| Regex | `#D16969` | `/pattern/g` |

#### MarkdownHighlighter

**File**: `syntax/markdown_highlighter.py`

**Colors**:
| Token | Color | Example |
|-------|-------|---------|
| Headings | `#569CD6` | `# Heading` |
| Bold | `#CE9178` | `**bold**` |
| Italic | `#9CDCFE` | `*italic*` |
| Links | `#4EC9B0` | `[text](url)` |
| Code | `#D4D4D4` on `#2D2D30` | `` `code` `` |
| Lists | `#C586C0` | `- item`, `1. item` |

### 7. ExpandButton Widget

**File**: `widgets/expand_button.py`

```python
class ExpandButton(QPushButton):
    """
    Small button to expand property widget into full editor.

    Appearance: [...] or expand icon
    Position: Right side of property widget (next to variable button)
    Size: 20x20px
    """

    clicked_expand = Signal()  # Emitted when expand requested
```

### 8. VariableAutocomplete

**File**: `widgets/variable_autocomplete.py`

```python
class VariableAutocomplete(QListWidget):
    """
    Autocomplete dropdown for variables and expressions.

    Features:
    - Fuzzy matching (using existing fuzzy_match from variable_picker)
    - Keyboard navigation (up/down/enter/escape)
    - Type badges from existing TYPE_BADGES
    - Source grouping (workflow, node outputs, system)

    Triggered by:
    - Typing {{
    - Ctrl+Space shortcut
    """
```

---

## Integration Points

### 1. Property Widget Integration

**File to modify**: `base_visual_node.py`

Add expand button to property widgets that support expressions:

```python
def _auto_create_widgets_from_schema(self) -> None:
    for prop_def in schema.properties:
        if prop_def.type in (PropertyType.TEXT, PropertyType.CODE, PropertyType.STRING):
            if prop_def.supports_expressions:
                # Add expand button alongside variable button
                widget = self._add_variable_aware_text_input(...)
                expand_btn = ExpandButton()
                expand_btn.clicked_expand.connect(
                    lambda p=prop_def: self._open_expression_editor(p)
                )
```

### 2. PropertyType to EditorType Mapping

```python
PROPERTY_TYPE_TO_EDITOR = {
    PropertyType.CODE: EditorType.CODE_PYTHON,  # Default, can override
    PropertyType.TEXT: EditorType.RICH_TEXT,
    PropertyType.STRING: EditorType.RICH_TEXT,
    PropertyType.JSON: EditorType.CODE_JAVASCRIPT,
}

# Special node overrides
NODE_EDITOR_OVERRIDES = {
    "EmailSendNode": {
        "body": EditorType.MARKDOWN,
    },
    "BrowserEvaluateNode": {
        "script": EditorType.CODE_JAVASCRIPT,
    },
    "RunPythonNode": {
        "code": EditorType.CODE_PYTHON,
    },
    "CommandNode": {
        "command": EditorType.CODE_CMD,
    },
}
```

### 3. Variable Provider Integration

Reuse existing `VariableProvider` singleton:

```python
from casare_rpa.presentation.canvas.ui.widgets.variable_picker import (
    VariableProvider,
    VariableInfo,
)

class ExpressionEditorPopup:
    def _setup_variable_integration(self):
        provider = VariableProvider.get_instance()
        variables = provider.get_all_variables(
            self._current_node_id,
            self._graph
        )
```

---

## File Structure (New Files)

```
src/casare_rpa/presentation/canvas/ui/widgets/expression_editor/
├── __init__.py                         # ~30 lines
├── expression_editor_popup.py          # ~500 lines (main container)
├── editor_factory.py                   # ~80 lines
├── base_editor.py                      # ~150 lines
├── code_editor.py                      # ~300 lines
├── markdown_editor.py                  # ~350 lines
├── rich_text_editor.py                 # ~200 lines
├── syntax/
│   ├── __init__.py                     # ~20 lines
│   ├── python_highlighter.py           # ~180 lines
│   ├── javascript_highlighter.py       # ~180 lines
│   └── markdown_highlighter.py         # ~120 lines
└── widgets/
    ├── __init__.py                     # ~15 lines
    ├── expand_button.py                # ~60 lines
    ├── variable_autocomplete.py        # ~200 lines
    └── toolbar.py                      # ~150 lines

Total: ~2,500 lines of new code
```

## Files to Modify

| File | Changes |
|------|---------|
| `base_visual_node.py` | Add `_open_expression_editor()` method, expand button creation |
| `property_schema.py` | Add `editor_type` field to PropertyDef (optional) |
| `theme.py` | Add editor-specific colors (code bg, line numbers, etc.) |

---

## Implementation Phases

### Phase 1: Core Infrastructure (builder agent)
**Estimated Time**: 4 hours

1. Create directory structure
2. Implement `BaseExpressionEditor` abstract class
3. Implement `ExpressionEditorPopup` container
4. Implement `EditorFactory`
5. Create `ExpandButton` widget

**Deliverables**:
- Basic popup opens/closes
- Placeholder editors render
- Expand button appears on widgets

### Phase 2: Code Editor (builder agent)
**Estimated Time**: 3 hours

1. Implement `CodeExpressionEditor` base
2. Implement `PythonHighlighter`
3. Implement `JavaScriptHighlighter`
4. Add line numbers widget
5. Add bracket matching

**Deliverables**:
- Python code with syntax highlighting
- JavaScript code with syntax highlighting
- Line numbers displayed

### Phase 3: Markdown Editor (builder agent)
**Estimated Time**: 2 hours

1. Implement `MarkdownHighlighter`
2. Implement `MarkdownEditor`
3. Add toolbar with formatting buttons
4. Add preview panel (optional toggle)

**Deliverables**:
- Markdown editing with highlighting
- Toolbar for common formatting
- HTML preview (side-by-side)

### Phase 4: Rich Text Editor (builder agent)
**Estimated Time**: 2 hours

1. Implement `RichTextEditor`
2. Integrate variable autocomplete
3. Add inline validation display

**Deliverables**:
- General text editing
- Variable autocomplete on `{{`
- Validation feedback

### Phase 5: Integration (ui agent)
**Estimated Time**: 3 hours

1. Modify `base_visual_node.py` to add expand buttons
2. Connect popup to property widgets
3. Handle value sync (popup -> widget -> casare_node.config)
4. Add keyboard shortcuts

**Deliverables**:
- Expand button on TEXT/CODE properties
- Popup opens with correct editor type
- Values sync back to node

### Phase 6: Styling & Polish (ui agent)
**Estimated Time**: 2 hours

1. Apply THEME colors consistently
2. Add fade animations
3. Polish resize behavior
4. Add tooltips and help text

**Deliverables**:
- Consistent dark theme
- Smooth animations
- Professional polish

---

## Agent Assignments

### builder agent
- Phase 1: Core Infrastructure
- Phase 2: Code Editor
- Phase 3: Markdown Editor
- Phase 4: Rich Text Editor

### ui agent
- Phase 5: Integration
- Phase 6: Styling & Polish

### Parallel Opportunities

These tasks can run in parallel:

1. **Parallel Set A** (within Phase 2):
   - `python_highlighter.py`
   - `javascript_highlighter.py`

2. **Parallel Set B** (Phase 3 + Phase 4 can overlap):
   - `MarkdownEditor` implementation
   - `RichTextEditor` implementation

3. **Parallel Set C** (Phase 5 + Phase 6):
   - Integration code
   - Theme/styling code

---

## Test Plan

### Unit Tests

```python
# tests/presentation/canvas/ui/widgets/expression_editor/
test_expression_editor_popup.py
test_code_editor.py
test_markdown_editor.py
test_rich_text_editor.py
test_syntax_highlighters.py
test_variable_autocomplete.py
```

### Key Test Scenarios

| Scenario | Expected Behavior |
|----------|-------------------|
| Open popup for STRING property | RichTextEditor appears |
| Open popup for CODE property | CodeExpressionEditor with Python |
| Open popup for email body | MarkdownEditor appears |
| Type `{{` | Autocomplete dropdown shows |
| Press Ctrl+Space | Variable picker opens |
| Press Escape | Popup closes without saving |
| Press Ctrl+Enter | Popup closes, value saved |
| Resize popup | Minimum size enforced |
| Drag header | Popup moves |
| Click outside popup | Popup closes (if not pinned) |

### Integration Tests

| Test | Coverage |
|------|----------|
| Create node, expand property | Full flow |
| Edit value in popup, verify sync | Data binding |
| Variable insertion | Variable system |
| Undo/redo with popup edits | Undo stack |

---

## Risks & Mitigations

### Risk 1: Qt Thread Safety
**Risk**: Syntax highlighting on large files may cause UI lag.
**Mitigation**:
- Use `QSyntaxHighlighter.rehighlightBlock()` for incremental updates
- Debounce highlighting (100ms delay after last keystroke)

### Risk 2: Memory Leaks
**Risk**: Popup not properly destroyed.
**Mitigation**:
- Use `Qt.WA_DeleteOnClose` attribute
- Clear references in `closeEvent()`
- Remove app event filter on close (like `VariablePickerPopup`)

### Risk 3: Focus Issues
**Risk**: Popup loses focus unexpectedly.
**Mitigation**:
- Use `Qt.WindowType.Tool` flag
- Implement `activateWindow()` on show
- Handle `focusOutEvent` carefully

### Risk 4: Variable Resolution
**Risk**: Variables not resolving in popup preview.
**Mitigation**:
- Popup is edit-only, no live preview of resolved values
- Use same resolution logic as `VariableAwareLineEdit`

### Risk 5: Undo/Redo Integration
**Risk**: Popup edits not in undo stack.
**Mitigation**:
- Call `set_property()` on accept (triggers undo)
- Cancel reverts to original value

---

## Acceptance Criteria

### Must Have
- [ ] Popup opens for STRING, TEXT, CODE property types
- [ ] Code editor with Python syntax highlighting
- [ ] Variable insertion via `{{` or Ctrl+Space
- [ ] Escape to cancel, Ctrl+Enter to accept
- [ ] Values sync back to node config
- [ ] THEME colors throughout

### Should Have
- [ ] JavaScript syntax highlighting
- [ ] Markdown editor with toolbar
- [ ] Autocomplete dropdown
- [ ] Line numbers in code editor
- [ ] Resize handles

### Nice to Have
- [ ] Markdown preview panel
- [ ] Bracket matching
- [ ] Multiple cursors
- [ ] Search/replace in editor

---

## Dependencies

### Existing Code (Reuse)
- `node_output_popup.py` - Popup pattern, DraggableHeader
- `variable_picker.py` - VariableProvider, VariableInfo, fuzzy_match
- `json_syntax_highlighter.py` - QSyntaxHighlighter pattern
- `xml_highlighter.py` - Additional highlighter reference
- `dialog_styles.py` - DialogStyles, color constants
- `theme.py` - THEME system, Colors dataclass

### External Libraries (Already in project)
- PySide6 (Qt)
- loguru (logging)

---

## Appendix: Color Reference (VSCode Dark+)

```python
# From theme.py - existing JSON colors we can extend
SYNTAX_COLORS = {
    # Keywords/Control
    "keyword": "#C586C0",        # Purple (if, for, def)
    "control": "#C586C0",        # Purple (return, break)

    # Functions/Methods
    "function_def": "#DCDCAA",   # Yellow (function definitions)
    "function_call": "#DCDCAA", # Yellow (function calls)

    # Strings
    "string": "#CE9178",         # Orange-brown
    "string_escape": "#D7BA7D",  # Gold (escape sequences)

    # Numbers
    "number": "#B5CEA8",         # Light green

    # Comments
    "comment": "#6A9955",        # Green (comments)

    # Types/Classes
    "class": "#4EC9B0",          # Teal
    "type": "#4EC9B0",           # Teal

    # Variables
    "variable": "#9CDCFE",       # Light blue
    "parameter": "#9CDCFE",      # Light blue

    # Operators
    "operator": "#D4D4D4",       # Gray

    # Decorators
    "decorator": "#DCDCAA",      # Yellow

    # Regex
    "regex": "#D16969",          # Red

    # Markdown specific
    "heading": "#569CD6",        # Blue
    "bold": "#CE9178",           # Orange
    "italic": "#9CDCFE",         # Light blue
    "link": "#4EC9B0",           # Teal
    "code_inline": "#D4D4D4",    # Gray on darker bg
}

# Editor background colors
EDITOR_COLORS = {
    "bg": "#1E1E1E",            # Editor background
    "line_number_bg": "#1E1E1E", # Line number gutter
    "line_number_fg": "#858585", # Line numbers
    "current_line": "#282828",   # Current line highlight
    "selection": "#264F78",      # Selection background
    "matching_bracket": "#515151", # Bracket match
}
```

---

## Notes

- This plan follows existing CasareRPA patterns exactly
- All UI code stays in presentation layer
- No changes to domain layer required
- Theme compliance is mandatory (no hardcoded colors)
- Signal/Slot pattern with `@Slot()` decorator required
