# Expression Editor Package

**Path**: `src/casare_rpa/presentation/canvas/ui/widgets/expression_editor/`

**Purpose**: Provides enhanced text editing capabilities for node properties with syntax highlighting, variable support, and multiple editor modes.

---

## Package Overview

The Expression Editor is a feature that provides a popup editor for node properties, similar to n8n and Power Automate. It offers:

- **Code editing** with Python, JavaScript, and CMD syntax highlighting
- **Markdown editing** with preview for email bodies
- **Rich text editing** with variable autocomplete
- **Popup window** following the NodeOutputPopup pattern

---

## Architecture

```
ExpressionEditorPopup (Main Container)
        |
        +-- DraggableHeader (title, mode label, close button)
        |
        +-- EditorContainer (holds injected editor)
        |           |
        |           +-- BaseExpressionEditor (ABC)
        |                   |
        |                   +-- CodeExpressionEditor (Python/JS/CMD)
        |                   +-- MarkdownEditor (with preview)
        |                   +-- RichTextEditor (with autocomplete)
        |
        +-- Footer (keyboard hints, Cancel/Accept buttons)

EditorFactory
        |
        +-- Creates appropriate editor from EditorType enum
        +-- Supports property type mapping
        +-- Node-specific overrides (EmailSendNode -> Markdown, etc.)

Syntax Highlighters
        |
        +-- PythonHighlighter (VSCode Dark+ colors)
        +-- JavaScriptHighlighter
        +-- MarkdownHighlighter

Supporting Widgets
        |
        +-- ExpandButton (triggers popup from property widget)
        +-- EditorToolbar (formatting buttons for Markdown)
        +-- VariableAutocomplete ({{ triggered autocomplete)
```

---

## File Listing

### Core Files

| File | Lines | Description |
|------|-------|-------------|
| `__init__.py` | ~68 | Public exports: EditorType, ExpressionEditorPopup, EditorFactory, editors |
| `base_editor.py` | ~142 | EditorType enum, BaseExpressionEditor ABC with QABCMeta |
| `expression_editor_popup.py` | ~642 | Main popup container with drag, resize, fade animation |
| `editor_factory.py` | ~152 | Factory pattern for creating editors, property type mapping |
| `code_editor.py` | ~368 | Code editor with line numbers and syntax highlighting |
| `markdown_editor.py` | ~471 | Markdown editor with toolbar and live preview |
| `rich_text_editor.py` | ~374 | Rich text with variable autocomplete on {{ trigger |

### Syntax Highlighters (`syntax/`)

| File | Lines | Description |
|------|-------|-------------|
| `__init__.py` | ~27 | Exports PythonHighlighter, JavaScriptHighlighter, MarkdownHighlighter |
| `python_highlighter.py` | ~180 | Python syntax (VSCode Dark+ colors) |
| `javascript_highlighter.py` | ~180 | JavaScript syntax highlighting |
| `markdown_highlighter.py` | ~120 | Markdown syntax (headings, bold, links, code) |

### Supporting Widgets (`widgets/`)

| File | Lines | Description |
|------|-------|-------------|
| `__init__.py` | ~25 | Exports ExpandButton, EditorToolbar, VariableAutocomplete |
| `expand_button.py` | ~84 | Small [...] button to trigger popup from property widgets |
| `toolbar.py` | ~150 | Horizontal toolbar for formatting actions |
| `variable_autocomplete.py` | ~200 | Popup autocomplete dropdown for variables |

---

## Key Classes

### EditorType (Enum)

```python
from casare_rpa.presentation.canvas.ui.widgets.expression_editor import EditorType

class EditorType(Enum):
    CODE_PYTHON = "python"
    CODE_JAVASCRIPT = "javascript"
    CODE_CMD = "cmd"
    MARKDOWN = "markdown"
    RICH_TEXT = "rich_text"
```

### ExpressionEditorPopup

Main container that follows the `node_output_popup.py` pattern:

- Tool-style frameless window with drop shadow
- Draggable header with title and mode label
- Corner resize handles (8px margin)
- Fade-in animation (150ms)
- Keyboard shortcuts: Escape (cancel), Ctrl+Enter (accept)

**Signals**:
- `accepted(str)` - Emitted when user confirms changes
- `cancelled()` - Emitted when user cancels
- `value_changed(str)` - Emitted on any content change

### EditorFactory

Factory pattern for creating editors:

```python
from casare_rpa.presentation.canvas.ui.widgets.expression_editor import (
    EditorFactory,
    EditorType,
)

# Create by editor type
editor = EditorFactory.create(EditorType.CODE_PYTHON)

# Create by property type with node overrides
editor = EditorFactory.create_for_property_type(
    property_type="CODE",
    node_type="BrowserEvaluateNode",
    property_name="script",  # Returns JavaScript editor
)
```

### CodeExpressionEditor

Code editor with:
- QPlainTextEdit with line numbers (LineNumberArea)
- Language-specific syntax highlighting
- Tab-to-spaces conversion (4 spaces)
- Current line highlighting

### MarkdownEditor

Markdown editor with:
- Horizontal split: edit pane + preview pane
- Toolbar: Bold, Italic, Heading, Link, Lists, Code
- Keyboard shortcuts: Ctrl+B, Ctrl+I, Ctrl+K
- Live HTML preview with 300ms debounce

### RichTextEditor

General text editor with:
- Variable insertion via {{ trigger
- VariableAutocomplete integration
- ExpressionHighlighter for {{variable}} syntax
- Validation status (border color: valid/warning/error)

---

## Usage Examples

### Basic Popup Usage

```python
from casare_rpa.presentation.canvas.ui.widgets.expression_editor import (
    ExpressionEditorPopup,
    EditorType,
)

# Create and show popup
popup = ExpressionEditorPopup()
popup.show_for_widget(
    widget=my_line_edit,
    editor_type=EditorType.CODE_PYTHON,
    initial_value="print('hello')",
    title="Edit: Python Script"
)

# Connect to accepted signal
popup.accepted.connect(lambda value: print(f"Accepted: {value}"))
```

### Direct Editor Usage

```python
from casare_rpa.presentation.canvas.ui.widgets.expression_editor import (
    EditorFactory,
    EditorType,
    CodeExpressionEditor,
)

# Create editor via factory
editor = EditorFactory.create(EditorType.CODE_PYTHON)
editor.set_value("def hello():\n    return 'world'")

# Or create directly
code_editor = CodeExpressionEditor(language="python")
code_editor.set_value("import os")

# Get value
content = editor.get_value()

# Insert at cursor
editor.insert_at_cursor("{{variable}}")
```

### Markdown Editor with Preview

```python
from casare_rpa.presentation.canvas.ui.widgets.expression_editor import MarkdownEditor

editor = MarkdownEditor()
editor.set_value("# Hello\n\nThis is **bold** text.")

# Toggle preview visibility
editor._toggle_preview()  # Internal method
```

---

## Integration with Visual Nodes

The Expression Editor is integrated into `base_visual_node.py`:

### Key Methods

```python
class VisualNode:
    def _open_expression_editor(self, property_name: str, property_def: PropertyDef) -> None:
        """Open popup for a property with appropriate editor type."""

    def _get_editor_type_for_property(self, property_def: PropertyDef) -> EditorType:
        """Map property type to editor type with node-specific overrides."""

    @Slot(str)
    def _on_expression_editor_accepted(self, property_name: str, value: str) -> None:
        """Handle accepted value - updates property and CasareNode config."""
```

### Node-Specific Overrides

```python
node_overrides = {
    "EmailSendNode": {"body": EditorType.MARKDOWN, "html_body": EditorType.MARKDOWN},
    "BrowserEvaluateNode": {"script": EditorType.CODE_JAVASCRIPT},
    "RunPythonNode": {"code": EditorType.CODE_PYTHON},
    "CommandNode": {"command": EditorType.CODE_CMD},
    "ExecuteScriptNode": {"script": EditorType.CODE_PYTHON},
}
```

---

## Theme Integration

All components use the THEME system from `presentation/canvas/ui/theme.py`:

- **PopupColors**: Background, header, border, text colors from THEME
- **Syntax Colors**: VSCode Dark+ colors for code highlighting
- **Editor Colors**: Background (#1E1E1E), line numbers (#858585), selection (#264F78)

> **Important**: No hardcoded colors. Always use `THEME.bg_dark`, `THEME.text_primary`, etc.

---

## Signal/Slot Patterns

All Qt signal handlers use `@Slot()` decorator per project rules:

```python
from PySide6.QtCore import Slot

@Slot()
def _on_accept(self) -> None:
    """Handle accept button click."""
    self.accepted.emit(self.get_value())
    self.close()

@Slot(str)
def _on_editor_value_changed(self, value: str) -> None:
    """Handle editor content change."""
    self.value_changed.emit(value)
```

---

## Related Files

- `presentation/canvas/ui/widgets/node_output_popup.py` - Pattern reference for popup
- `presentation/canvas/ui/widgets/variable_picker.py` - VariableProvider integration
- `presentation/canvas/ui/widgets/json_syntax_highlighter.py` - Highlighter pattern
- `presentation/canvas/visual_nodes/base_visual_node.py` - Integration point

---

## Testing

Test files located at:
```
tests/presentation/canvas/ui/widgets/expression_editor/
├── test_expression_editor_popup.py
├── test_code_editor.py
├── test_markdown_editor.py
├── test_rich_text_editor.py
├── test_syntax_highlighters.py
└── test_variable_autocomplete.py
```

Key test scenarios:
- Popup opens with correct editor type
- Variable insertion via {{ trigger
- Keyboard shortcuts (Escape, Ctrl+Enter, Ctrl+B/I/K)
- Value sync back to property
- Resize and drag functionality
