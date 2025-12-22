# UI Widget Skill

Guide for creating custom PySide6 widgets for nodes.

## Widget Template

```python
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit
from PySide6.QtCore import Signal

class CustomNodeWidget(QWidget):
    value_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        self.label = QLabel("Input:")
        self.input = QLineEdit()
        self.input.textChanged.connect(self.value_changed.emit)

        layout.addWidget(self.label)
        layout.addWidget(self.input)

    def get_value(self) -> str:
        return self.input.text()

    def set_value(self, value: str):
        self.input.setText(value)
```

## Styling

```python
# Use stylesheets
self.setStyleSheet("""
    QLineEdit {
        background: #2d2d2d;
        color: #ffffff;
        border: 1px solid #444;
        border-radius: 4px;
        padding: 4px;
    }
    QLineEdit:focus {
        border-color: #0078d4;
    }
""")
```

## Signals & Slots

```python
# Emit signal
self.value_changed.emit(new_value)

# Connect signal to slot
widget.value_changed.connect(self.on_value_changed)

# Slot method
def on_value_changed(self, value: str):
    self.node.set_property("input", value)
```

## Integration with Node

```python
class VisualMyNode(VisualNodeMixin, MyNode):
    def _setup_widgets(self):
        self.custom_widget = CustomNodeWidget()
        self.custom_widget.value_changed.connect(
            lambda v: self.set_property("input", v)
        )
        self.add_custom_widget(self.custom_widget)
```

## Common Widgets

| Widget | Use Case |
|:---|:---|
| `QLineEdit` | Text input |
| `QComboBox` | Dropdown selection |
| `QSpinBox` | Integer input |
| `QCheckBox` | Boolean toggle |
| `QTextEdit` | Multi-line text |
| `QPushButton` | Actions |

## Best Practices

1. Keep widgets compact for node canvas
2. Use dark theme colors
3. Emit signals on value changes
4. Handle focus properly
5. Use `setContentsMargins(4, 4, 4, 4)` for tight layouts
