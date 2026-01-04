# Widgets Package

**Path**: `src/casare_rpa/presentation/canvas/ui/widgets/`

**Purpose**: Reusable UI widgets for the CasareRPA canvas and property panels.

---

## Widget Catalog

### Property Input Widgets

| Widget | File | Description |
|--------|------|-------------|
| `ValidatedInput` | `validated_input.py` | Text input with validation feedback |
| `FilePathWidget` | `file_path_widget.py` | File/folder path picker with browse button |
| `SelectorInputWidget` | `selector_input_widget.py` | CSS/XPath selector input with test button |
| `AnchorSelectorWidget` | `anchor_selector_widget.py` | UI element anchor selector |
| `CascadingDropdown` | `cascading_dropdown.py` | Dependent dropdown pairs |
| `VariableEditorWidget` | `variable_editor_widget.py` | Key-value variable editor |

### Popup Widgets

| Widget | File | Description |
|--------|------|-------------|
| `NodeOutputPopup` | `node_output_popup.py` | Node execution output inspector |
| `VariablePickerPopup` | `variable_picker.py` | Variable selection with upstream node detection |
| `ToastNotification` | `toast.py` | Non-blocking toast notifications |

### Expression Editor

**Package**: `expression_editor/`

Enhanced text editing for node properties with syntax highlighting and variable support.

| Component | File | Description |
|-----------|------|-------------|
| `ExpressionEditorPopup` | `expression_editor/expression_editor_popup.py` | Main popup container |
| `EditorFactory` | `expression_editor/editor_factory.py` | Creates appropriate editor |
| `CodeExpressionEditor` | `expression_editor/code_editor.py` | Code with line numbers |
| `MarkdownEditor` | `expression_editor/markdown_editor.py` | Markdown with preview |
| `RichTextEditor` | `expression_editor/rich_text_editor.py` | Text with variable autocomplete |
| `ExpandButton` | `expression_editor/widgets/expand_button.py` | Trigger button for popup |

**Editor Types**:
- `CODE_PYTHON` - Python syntax highlighting
- `CODE_JAVASCRIPT` - JavaScript syntax highlighting
- `CODE_CMD` - Command/shell syntax
- `MARKDOWN` - Markdown with live preview
- `RICH_TEXT` - General text with {{ variable autocomplete

See: `expression_editor/_index.md` for full documentation.

### Google Integration Widgets

| Widget | File | Description |
|--------|------|-------------|
| `GoogleCredentialPicker` | `google_credential_picker.py` | OAuth credential selector |
| `GoogleFolderNavigator` | `google_folder_navigator.py` | Google Drive folder browser |
| `GooglePickers` | `google_pickers.py` | File/folder selection dialogs |

### AI Assistant Widgets

**Package**: `ai_assistant/`

| Widget | File | Description |
|--------|------|-------------|
| `AIDock` | `ai_assistant/dock.py` | Dockable AI assistant panel |
| `ChatArea` | `ai_assistant/chat_area.py` | Chat message display |
| `PreviewCard` | `ai_assistant/preview_card.py` | Workflow preview cards |

### Orchestrator Widgets

**Package**: `orchestrator/`

| Widget | File | Description |
|--------|------|-------------|
| `QueueDock` | `orchestrator/queue_dock.py` | Job queue management |
| `ScheduleDock` | `orchestrator/schedule_dock.py` | Schedule management |
| `QueuesTab` | `orchestrator/queues_tab.py` | Queue list view |
| `TransactionsTab` | `orchestrator/transactions_tab.py` | Transaction history |
| `CalendarWidget` | `orchestrator/calendar_widget.py` | Schedule calendar |

### Process Mining Widgets

**Package**: `process_mining/`

| Widget | File | Description |
|--------|------|-------------|
| `ProcessMap` | `process_mining/process_map.py` | Process flow visualization |

### Utility Widgets

| Widget | File | Description |
|--------|------|-------------|
| `SearchWidget` | `search_widget.py` | Node search input |
| `ZoomWidget` | `zoom_widget.py` | Canvas zoom controls |
| `BreadcrumbNav` | `breadcrumb_nav.py` | Subgraph navigation |
| `CollapsibleSection` | `collapsible_section.py` | Expandable section container |
| `RecordingStatus` | `recording_status.py` | Recording indicator |
| `TenantSelector` | `tenant_selector.py` | Multi-tenant selector |
| `RobotOverrideWidget` | `robot_override_widget.py` | Robot execution override |

### Performance Widgets

| Widget | File | Description |
|--------|------|-------------|
| `PerformanceDashboard` | `performance_dashboard.py` | Execution metrics display |
| `ProfilingTree` | `profiling_tree.py` | Performance profiling tree view |
| `OutputConsoleWidget` | `output_console_widget.py` | Execution output console |

### Syntax Highlighters

| Highlighter | File | Description |
|-------------|------|-------------|
| `JsonSyntaxHighlighter` | `json_syntax_highlighter.py` | JSON syntax coloring |
| `PythonHighlighter` | `expression_editor/syntax/python_highlighter.py` | Python syntax |
| `JavaScriptHighlighter` | `expression_editor/syntax/javascript_highlighter.py` | JavaScript syntax |
| `MarkdownHighlighter` | `expression_editor/syntax/markdown_highlighter.py` | Markdown syntax |

---

## Usage Guidelines

### Theme Compliance

All widgets must use the THEME system:

```python
from casare_rpa.presentation.canvas.theme import THEME, TOKENS

# Get colors
c = THEME
self.setStyleSheet(f"background: {c.bg_surface};")

# Or use THEME directly
self.setStyleSheet(f"color: {THEME.text_primary};")
```

> **Warning**: No hardcoded colors allowed. Always use THEME.

### Signal/Slot Patterns

All signal handlers require `@Slot()` decorator:

```python
from PySide6.QtCore import Slot

@Slot()
def _on_button_clicked(self) -> None:
    """Handle button click."""
    pass

@Slot(str)
def _on_text_changed(self, text: str) -> None:
    """Handle text change."""
    pass
```

> **Warning**: No lambda functions in signal connections. Use `functools.partial` instead.

### Widget Structure

Standard widget initialization pattern:

```python
class MyWidget(QWidget):
    # Signals
    value_changed = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._setup_ui()
        self._apply_styles()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Create and layout child widgets."""
        pass

    def _apply_styles(self) -> None:
        """Apply THEME styling."""
        pass

    def _connect_signals(self) -> None:
        """Connect signals to slots."""
        pass
```

---

## Related Documentation

- `presentation/canvas/ui/theme.py` - THEME system
- `presentation/canvas/ui/panels/_index.md` - Panel widgets
- `.claude/rules/ui/theme-rules.md` - Theme guidelines
- `.claude/rules/ui/signal-slot-rules.md` - Signal/slot patterns
