# Expression Editor Research: Best Practices and Implementation Strategy

**Research Date**: 2025-12-14
**Purpose**: Implement n8n/Power Automate-style expression editor for CasareRPA

## Executive Summary

This research covers expression editor implementations from n8n, Power Automate, and Qt best practices. CasareRPA already has solid foundations with `ExpressionEvaluator`, `VariablePickerPopup`, and `JsonSyntaxHighlighter`. The recommended approach is to enhance these existing components rather than introducing new dependencies like QScintilla.

---

## 1. n8n Expression Editor Analysis

### Architecture
- **Editor**: CodeMirror 6 (web-based)
- **Language Support**: Custom `codemirror-lang-n8n-expression` package
- **Parser**: Lezer-based (JavaScript parser for resolvable expressions)

### Key Implementation Patterns

1. **Expression Syntax**: Uses `{{ expression }}` or `${{ }}` for templating
2. **Resolvable Nodes**: Parser detects "Resolvable" nodes and switches to JavaScript parsing
3. **Variable Insertion**: Inline autocomplete triggered by typing `{{`
4. **Preview**: Real-time expression evaluation preview

### UI Patterns
- Search box at top of popup
- Grouped sections (Variables, Node Outputs, System)
- Type badges with color coding
- Keyboard navigation (arrows, Enter, Escape)
- Fuzzy matching for search

**Source**: [n8n CodeMirror Lang](https://github.com/n8n-io/codemirror-lang-n8n)

---

## 2. Power Automate Expression Editor Analysis

### Key Patterns

1. **Expression Builder UI**:
   - Folders Pane (functions, variables, datasets)
   - Contents Pane (items within selected folder)
   - Expression Pane (where expression is built)
   - Operators List

2. **Variable Insertion Patterns**:
   - **Click-to-Insert**: Double-click adds element to expression
   - **Insert Button**: Button appears on right side of input (% symbol)
   - **F2 Hotkey**: Opens expression builder
   - **Cursor Position Insertion**: Items inserted at cursor location

3. **IntelliSense/Autocomplete**:
   - Drop-down list appears while typing
   - Tab or Enter to confirm selection
   - Function signatures with parameter hints

4. **Dynamic Content Picker**:
   - Tab-based UI (Dynamic Content | Expression)
   - Search within content
   - Shows outputs from previous steps

**Sources**:
- [Power Automate Expression Builder](https://learn.microsoft.com/en-us/troubleshoot/power-platform/power-automate/flow-creation/dynamic-content-picker-missing-dynamic-content-from-previous-steps)
- [Automate Expression Builder](https://help.globalscape.com/help/am8/using_expression_builder.htm)

---

## 3. PySide6/Qt Implementation Strategies

### Option A: QPlainTextEdit + QSyntaxHighlighter (RECOMMENDED)

**Why QPlainTextEdit over QTextEdit?**
- Optimized for plain text and large documents
- Block-based scrolling (vs. pixel-exact)
- Simpler internal structure for syntax highlighting
- Qt's official recommendation for code editors

**Implementation Pattern**:
```python
from PySide6.QtWidgets import QPlainTextEdit
from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat

class ExpressionHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self._setup_formats()

    def _setup_formats(self):
        # Variable format: {{varName}}
        self.var_format = QTextCharFormat()
        self.var_format.setForeground(QColor("#9CDCFE"))

        # Expression format: @{func()}
        self.expr_format = QTextCharFormat()
        self.expr_format.setForeground(QColor("#DCDCAA"))

        # Function format
        self.func_format = QTextCharFormat()
        self.func_format.setForeground(QColor("#569CD6"))

    def highlightBlock(self, text):
        # Pattern matching with regex
        patterns = [
            (r'\{\{[^}]+\}\}', self.var_format),     # {{variable}}
            (r'@\{[^}]+\}', self.expr_format),        # @{expression}
            (r'\b(concat|upper|if|coalesce)\b', self.func_format),
        ]
        for pattern, fmt in patterns:
            for match in re.finditer(pattern, text):
                self.setFormat(match.start(), len(match.group()), fmt)
```

**Source**: [Qt Syntax Highlighter Example](https://doc.qt.io/qt-6/qtwidgets-richtext-syntaxhighlighter-example.html)

### Option B: QScintilla

**Pros**:
- Full-featured code editor (autocompletion, code folding, margins)
- Lexer-based highlighting with many built-in languages
- Call tips and brace matching

**Cons**:
- **PyQt6 dependency** - `PyQt6-QScintilla` package is for PyQt6, not PySide6
- Heavier dependency footprint
- May require compatibility shims for PySide6

**Recommendation**: Avoid unless advanced features are essential

**Source**: [QScintilla](https://qscintilla.com/)

### Option C: Pygments + QSyntaxHighlighter

**Integration Pattern**:
```python
from pygments.lexers import get_lexer_by_name
from pygments.token import Token
from PySide6.QtGui import QSyntaxHighlighter

class PygmentsHighlighter(QSyntaxHighlighter):
    def __init__(self, document, lexer_name='python'):
        super().__init__(document)
        self._lexer = get_lexer_by_name(lexer_name)
        self._token_formats = self._create_token_formats()

    def highlightBlock(self, text):
        for index, token_type, value in self._lexer.get_tokens(text):
            if token_type in self._token_formats:
                self.setFormat(index, len(value), self._token_formats[token_type])
```

**Use Case**: When you need syntax highlighting for standard languages (Python, JavaScript, SQL)

---

## 4. Autocomplete/QCompleter Implementation

### Qt Pattern (from Custom Completer Example)

```python
from PySide6.QtWidgets import QPlainTextEdit, QCompleter
from PySide6.QtCore import Qt

class ExpressionEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._completer = None

    def setCompleter(self, completer: QCompleter):
        if self._completer:
            self._completer.activated.disconnect()

        self._completer = completer
        self._completer.setWidget(self)
        self._completer.setCompletionMode(QCompleter.PopupCompletion)
        self._completer.setCaseSensitivity(Qt.CaseInsensitive)
        self._completer.activated.connect(self._insertCompletion)

    def keyPressEvent(self, event):
        # Forward special keys to completer when popup visible
        if self._completer and self._completer.popup().isVisible():
            if event.key() in (Qt.Key_Enter, Qt.Key_Return, Qt.Key_Escape, Qt.Key_Tab):
                event.ignore()
                return

        super().keyPressEvent(event)

        # Trigger completion
        self._updateCompleter()

    def _updateCompleter(self):
        prefix = self._textUnderCursor()
        if len(prefix) < 2:
            self._completer.popup().hide()
            return

        self._completer.setCompletionPrefix(prefix)

        # Position popup
        cr = self.cursorRect()
        cr.setWidth(self._completer.popup().sizeHintForColumn(0) +
                    self._completer.popup().verticalScrollBar().sizeHint().width())
        self._completer.complete(cr)

    def _insertCompletion(self, completion):
        tc = self.textCursor()
        extra = len(completion) - len(self._completer.completionPrefix())
        tc.insertText(completion[-extra:])
        self.setTextCursor(tc)
```

**Source**: [Qt Custom Completer Example](https://doc.qt.io/qt-6/qtwidgets-tools-customcompleter-example.html)

---

## 5. Popup/Overlay Widget Patterns

### Qt Popup Approach
```python
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt

class ExpressionPopup(QWidget):
    def __init__(self, parent=None):
        super().__init__(
            parent,
            Qt.WindowType.Tool |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )

        # Click outside to close
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
```

### Key Patterns:
1. `Qt.Popup` flag auto-closes on click outside
2. `Qt.FramelessWindowHint` removes window decorations
3. App-level event filter for click-outside-to-close
4. Focus proxy to keep keyboard on main widget

**Source**: [Qt Popup Window Blog](https://blog.bachi.net/?p=11707)

---

## 6. CasareRPA Existing Implementation Analysis

### Current Components

#### ExpressionEvaluator (`domain/services/expression_evaluator.py`)
- **Syntax Support**:
  - Legacy: `{{variable_name}}`
  - New: `@{expression}` (Power Automate style)
- **Functions**: 30+ built-in (string, logic, date, JSON, collection, math)
- **Security**: No eval/exec, regex-based tokenization
- **Variable Resolution**: Dot notation (`user.name`), array index (`items[0]`)

#### VariablePickerPopup (`presentation/canvas/ui/widgets/variable_picker.py`)
- **Features**:
  - Search with fuzzy matching (score-based ranking)
  - Tree widget with grouped sections
  - Type badges with color coding
  - Keyboard navigation
  - Drag-and-drop support
  - Upstream node variable detection

#### VariableAwareLineEdit
- **Features**:
  - `{x}` button for variable insertion
  - Ctrl+Space shortcut
  - Drag-and-drop support
  - Inline validation with visual feedback

#### JsonSyntaxHighlighter
- VSCode Dark+ color scheme
- Handles keys, strings, numbers, booleans, null, brackets

---

## 7. Recommended Implementation Strategy

### Phase 1: Enhanced Expression Editor Widget

Create a new `ExpressionEditorWidget` that combines existing components:

```python
class ExpressionEditorWidget(QWidget):
    """
    Rich expression editor with syntax highlighting and autocomplete.

    Features:
    - QPlainTextEdit with expression syntax highlighting
    - Variable picker popup (existing VariablePickerPopup)
    - Function autocomplete
    - Real-time expression preview
    - Multi-line support
    """
```

**Key Components**:
1. `QPlainTextEdit` as the editor base
2. `ExpressionSyntaxHighlighter` (new) for `{{}}` and `@{}` syntax
3. `QCompleter` for function/variable autocomplete
4. `VariablePickerPopup` (existing) for variable selection
5. Preview pane showing evaluated result

### Phase 2: Expression Syntax Highlighter

```python
class ExpressionSyntaxHighlighter(QSyntaxHighlighter):
    """
    Highlights CasareRPA expression syntax:
    - {{variable}} - Variable references (light blue)
    - @{function(args)} - Expressions (yellow)
    - Built-in functions - Keywords (blue)
    - Strings, numbers, booleans in expressions
    """

    PATTERNS = [
        (r'\{\{[^}]+\}\}', 'variable'),           # {{var}}
        (r'@\{[^}]+\}', 'expression'),            # @{expr}
        (r'\b(concat|upper|lower|if|coalesce|now|today)\b', 'function'),
        (r'"[^"]*"', 'string'),
        (r"'[^']*'", 'string'),
        (r'\b\d+\.?\d*\b', 'number'),
        (r'\b(true|false|null)\b', 'boolean'),
    ]
```

### Phase 3: Inline Autocomplete

Trigger autocomplete on:
1. `{{` typed - show variables
2. `@{` typed - show functions
3. `.` after variable - show nested properties
4. `(` after function - show parameter hints

### Phase 4: Expression Preview

Real-time evaluation preview:
- Show result type and value
- Display errors inline (red border)
- Support mock data for design-time preview

---

## 8. UI/UX Recommendations

### Variable Insertion Pattern (like n8n/Power Automate)

1. **Trigger Button**: `{x}` icon on right side of input (already implemented)
2. **Keyboard Shortcut**: Ctrl+Space (already implemented)
3. **Inline Trigger**: Type `{{` to show popup with filtering

### Popup Design (already implemented, enhancements)

1. **Search Box**: Top of popup with fuzzy search
2. **Grouped Sections**: Variables | Node Outputs | System | Functions
3. **Type Badges**: Color-coded type indicators
4. **Preview**: Show value preview on hover

### Expression Builder Mode (for complex expressions)

1. **Multi-line Editor**: QPlainTextEdit with syntax highlighting
2. **Function Browser**: Sidebar with categorized functions
3. **Documentation**: Function signatures and examples
4. **Preview Pane**: Live result preview

---

## 9. Implementation Checklist

### Immediate (Use Existing)
- [x] Variable picker popup with search
- [x] `{x}` button integration
- [x] Ctrl+Space shortcut
- [x] Drag-and-drop from Output Inspector
- [x] JSON syntax highlighting

### Short-term (Enhance)
- [ ] Expression syntax highlighter for `{{}}` and `@{}`
- [ ] Inline autocomplete with QCompleter
- [ ] Function documentation tooltips
- [ ] Multi-line expression editor widget

### Medium-term (New Features)
- [ ] Expression builder dialog (modal)
- [ ] Function browser with categories
- [ ] Parameter hints/call tips
- [ ] Expression validation with error messages
- [ ] Mock data for design-time preview

---

## 10. Library Recommendations

### Use Native Qt (Recommended)
| Component | Implementation |
|-----------|----------------|
| Editor | QPlainTextEdit |
| Highlighting | QSyntaxHighlighter (custom) |
| Autocomplete | QCompleter |
| Popup | QWidget with Qt.Tool flag |

### Avoid
| Library | Reason |
|---------|--------|
| QScintilla | PyQt6 dependency, heavyweight |
| Monaco/CodeMirror | Web-based, not native Qt |
| Custom Lezer parser | Over-engineered for expression syntax |

### Consider for Future
| Library | Use Case |
|---------|----------|
| Pygments | If needing Python/JS code highlighting |
| tree-sitter | If needing AST-based analysis |

---

## Sources

### n8n
- [n8n CodeMirror Lang](https://github.com/n8n-io/codemirror-lang-n8n)
- [n8n Expressions Docs](https://docs.n8n.io/code/expressions/)

### Power Automate
- [Dynamic Content Picker](https://learn.microsoft.com/en-us/troubleshoot/power-platform/power-automate/flow-creation/dynamic-content-picker-missing-dynamic-content-from-previous-steps)
- [Expression Builder Guide](https://help.globalscape.com/help/am8/using_expression_builder.htm)

### Qt/PySide6
- [QSyntaxHighlighter](https://doc.qt.io/qtforpython-6/PySide6/QtGui/QSyntaxHighlighter.html)
- [Qt Syntax Highlighter Example](https://doc.qt.io/qt-6/qtwidgets-richtext-syntaxhighlighter-example.html)
- [Qt Custom Completer Example](https://doc.qt.io/qt-6/qtwidgets-tools-customcompleter-example.html)
- [QPlainTextEdit for Code Editors](https://doc.qt.io/qt-6/qplaintextedit.html)

### QScintilla
- [QScintilla Documentation](https://qscintilla.com/)
- [PyQt6-QScintilla PyPI](https://pypi.org/project/PyQt6-QScintilla/)
