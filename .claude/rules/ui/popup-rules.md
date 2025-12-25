# Popup Development Rules

## PopupManager Pattern (MANDATORY for all new popups)

All popup windows MUST use `PopupManager` for click-outside-to-close handling.

### Why PopupManager?

| Problem | Solution |
|---------|----------|
| Each popup installing its own app-level filter | Single global filter in PopupManager |
| Event filters not reinstalled on subsequent shows | PopupManager filter is permanent |
| Memory leaks from stale popup references | WeakSet auto-cleanup |
| Inconsistent behavior across popups | Centralized implementation |

### Basic Usage

```python
from casare_rpa.presentation.canvas.managers.popup_manager import PopupManager

class MyPopup(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        # Window setup
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
        # ... setup UI ...

    def showEvent(self, event) -> None:
        super().showEvent(event)
        # Register for click-outside-to-close handling
        PopupManager.register(self)
        # CRITICAL: Activate window so keyboard events work
        self.activateWindow()
        self.raise_()

    def closeEvent(self, event) -> None:
        # Unregister from PopupManager
        PopupManager.unregister(self)
        # Clean up any event filters on child widgets
        super().closeEvent(event)
```

## Escape Key Handling

### For Simple Popups (no text widgets)

Override `keyPressEvent`:

```python
def keyPressEvent(self, event: QKeyEvent) -> None:
    if event.key() == Qt.Key.Key_Escape:
        self.close()
        event.accept()
        return
    super().keyPressEvent(event)
```

### For Popups with Text Widgets (QTextEdit, QLineEdit, etc.)

Text widgets consume key events before parent sees them. Install `eventFilter` on child widgets AND their viewports:

```python
def _setup_ui(self) -> None:
    # Create child widgets
    self._text_edit = QTextEdit()
    self._search_input = QLineEdit()

    # Install event filters on widget + viewport
    widgets_to_filter = [self._text_edit, self._search_input]
    for widget in widgets_to_filter:
        widget.installEventFilter(self)
        if hasattr(widget, 'viewport'):
            widget.viewport().installEventFilter(self)

def eventFilter(self, obj: QObject, event: QEvent) -> bool:
    """Catch Escape key from child widgets."""
    if event.type() in (QEvent.Type.KeyPress, QEvent.Type.ShortcutOverride):
        key_event = event
        if hasattr(key_event, 'key') and key_event.key() == Qt.Key.Key_Escape:
            self.close()
            return True  # Consume the event
    return False

def closeEvent(self, event) -> None:
    """Clean up event filters."""
    for widget in [self._text_edit, self._search_input]:
        try:
            widget.removeEventFilter(self)
            if hasattr(widget, 'viewport'):
                widget.viewport().removeEventFilter(self)
        except RuntimeError:
            pass  # Widget already deleted
    PopupManager.unregister(self)
    super().closeEvent(event)
```

## Window Attributes

### Required Settings

```python
# Tool window - popup style
self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)

# Transparent background for rounded corners
self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

# CRITICAL: Allow keyboard events (Escape, etc.)
self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, False)
```

### WA_ShowWithoutActivating = False

- **True**: Popup won't steal focus, Escape key won't work
- **False**: Popup takes focus when shown, Escape key works
- **Default**: Use `False` unless popup explicitly shouldn't take focus

## Focus Management

Always call these in your `show()` or `show_at_position()` method:

```python
def show_at_position(self, pos: QPoint) -> None:
    self.move(pos)
    self.show()
    # CRITICAL: Enable keyboard events
    self.activateWindow()
    self.raise_()
    self.setFocus()
```

## Pin State (Optional)

If your popup supports pinning (stays open when clicking outside):

```python
# Register as pinned
PopupManager.register(self, pinned=True)

# Toggle pin state
@property
def is_pinned(self) -> bool:
    return getattr(self, "_popup_manager_pinned", False)

def set_pinned(self, pinned: bool) -> None:
    # Update PopupManager's internal state
    PopupManager.unregister(self)
    PopupManager.register(self, pinned=pinned)
    # Update UI to show pin state
    self._pin_button.setChecked(pinned)
```

## Checklist

Before committing a new popup:

- [ ] Uses `PopupManager.register()` in `showEvent` or `show_at_position`
- [ ] Uses `PopupManager.unregister()` in `closeEvent`
- [ ] Escape key works (either `keyPressEvent` or `eventFilter` on children)
- [ ] `WA_ShowWithoutActivating = False` (unless intentional)
- [ ] `activateWindow()`, `raise_()`, `setFocus()` called when shown
- [ ] Event filters removed in `closeEvent` with `RuntimeError` guards
- [ ] No app-level `installEventFilter` on `QApplication` in popup code

## Examples

Reference implementations:
- `VariablePickerPopup` - Simple popup with search box
- `ExpressionEditorPopup` - Complex popup with text editor
- `NodeOutputPopup` - MMB menu with multiple views

---

*Parent: [../_index.md](../_index.md)*
