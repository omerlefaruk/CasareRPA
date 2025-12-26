# Agent Instructions - UI Agent

## Your Role
Qt/PySide6 development for Canvas UI.

## Serena Tools (USE AGGRESSIVELY)

### UI Discovery

1. **find_symbol** - Find UI components
```python
mcp__plugin_serena_serena__find_symbol(
    name_path_pattern="*Widget*",
    relative_path="src/casare_rpa/presentation/canvas/ui/widgets/",
    include_body=False,
    depth=1
)
```

2. **get_symbols_overview** - Understand widget structure
```python
mcp__plugin_serena_serena__get_symbols_overview(
    relative_path="src/casare_rpa/presentation/canvas/ui/widgets/my_widget.py",
    depth=2
)
```

3. **search_for_pattern** - Find UI patterns
```python
# Find popup patterns
mcp__plugin_serena_serena__search_for_pattern(
    substring_pattern=r"PopupManager\.register",
    relative_path="src/casare_rpa/presentation/canvas/"
)

# Find THEME usage
mcp__plugin_serena_serena__search_for_pattern(
    substring_pattern=r"THEME\.",
    relative_path="src/casare_rpa/presentation/canvas/ui/"
)
```

### UI Implementation

4. **replace_symbol_body** - Replace UI methods
```python
mcp__plugin_serena_serena__replace_symbol_body(
    name_path="MyWidget/paintEvent",
    relative_path="src/casare_rpa/presentation/canvas/ui/widgets/my_widget.py",
    body="""def paintEvent(self, event):
        painter = QPainter(self)
        painter.setBrush(THEME.background)
        ...
"""
)
```

5. **replace_content** - UI styling changes
```python
mcp__plugin_serena_serena__replace_content(
    relative_path="src/casare_rpa/presentation/canvas/ui/widgets/my_widget.py",
    needle=r"QColor\(\"#[0-9A-Fa-f]{6}\"\)",
    repl="THEME.primary",
    mode="regex"
)
```

## UI Standards (Non-Negotiable)

### Theme System
```python
# CORRECT
from casare_rpa.presentation.canvas.theme import THEME
background = THEME.background
color = THEME.text_primary

# WRONG
background = QColor("#1E1E1E")
color = QColor("#FFFFFF")
```

### PopupManager (All Popups)
```python
def showEvent(self, event):
    super().showEvent(event)
    PopupManager.register(self)
    self.activateWindow()
    self.raise_()

def closeEvent(self, event):
    PopupManager.unregister(self)
    super().closeEvent(event)
```

### Signal/Slot
```python
from PySide6.QtCore import Slot

@Slot()
def on_button_clicked(self):
    ...
```

### Key Components
| Component | Location |
|-----------|----------|
| Theme | `presentation/canvas/theme.py` |
| PopupManager | `presentation/canvas/managers/popup_manager.py` |
| SignalCoordinator | `presentation/canvas/coordinators/signal_coordinator.py` |
| Widgets | `presentation/canvas/ui/widgets/` |
| Panels | `presentation/canvas/ui/panels/` |

## UI Patterns to Follow

**Custom Widget**:
```python
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Slot
from casare_rpa.presentation.canvas.theme import THEME

class MyWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        # Use THEME for all styling
```

**Popup Dialog**:
```python
class MyPopup(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
```
