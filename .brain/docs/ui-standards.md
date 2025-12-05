# UI Standards

> All buttons/dialogs MUST follow these sizing/color standards.

## Button Heights

| Type | Height | Usage |
|------|--------|-------|
| Action buttons | 32px | Footer, dialog buttons (Save, Cancel) |
| Inline buttons | 28px | Form buttons (Find, Copy, Browse) |
| Inputs | 28px | QLineEdit, QComboBox, QSpinBox |
| Toolbar buttons | 32px | Mode toggles, toolbar actions |
| Small buttons | 24px | Compact spaces (use sparingly) |

## Theme Colors (VSCode Dark+)

```css
/* Backgrounds */
--bg-primary: #252526;      /* Card/panel */
--bg-secondary: #2D2D30;    /* Button */
--bg-tertiary: #1E1E1E;     /* Dialog */
--bg-hover: #2A2D2E;        /* Hover */

/* Text */
--text-primary: #D4D4D4;
--text-secondary: #CCCCCC;
--text-disabled: #6B6B6B;

/* Accent */
--accent-primary: #007ACC;  /* VSCode blue */
--accent-hover: #1177BB;

/* Borders */
--border: #3E3E42;
--border-light: #454545;
```

## Standard Button Styles

### Action Button (32px)
```css
QPushButton {
    background: #2D2D30;
    border: 1px solid #454545;
    border-radius: 4px;
    padding: 0 16px;
    color: #D4D4D4;
    font-size: 12px;
    font-weight: 500;
    min-height: 32px;
}
QPushButton:hover {
    background: #2A2D2E;
    border-color: #007ACC;
    color: white;
}
QPushButton:default {
    background: #007ACC;
    border-color: #007ACC;
    color: white;
}
```

### Inline Button (28px)
```css
QPushButton {
    background: #007ACC;
    border: none;
    border-radius: 4px;
    padding: 0 12px;
    color: white;
    font-size: 11px;
    font-weight: 600;
    min-height: 28px;
}
QPushButton:hover { background: #1177BB; }
```

## QMessageBox Styling

**NEVER use static methods directly:**
- `QMessageBox.information()` - NO
- `QMessageBox.warning()` - NO
- `QMessageBox.critical()` - NO

**USE helper methods instead:**

```python
def _show_styled_message(
    self,
    title: str,
    text: str,
    info: str = "",
    icon: QMessageBox.Icon = QMessageBox.Icon.Warning
) -> None:
    msg = QMessageBox(self.main_window)
    msg.setWindowTitle(title)
    msg.setText(text)
    if info:
        msg.setInformativeText(info)
    msg.setIcon(icon)
    msg.setStyleSheet(self._get_message_box_style())
    msg.exec()

def _show_styled_question(
    self,
    title: str,
    text: str,
    buttons: QMessageBox.StandardButton,
    default: QMessageBox.StandardButton
) -> QMessageBox.StandardButton:
    msg = QMessageBox(self.main_window)
    msg.setWindowTitle(title)
    msg.setText(text)
    msg.setStandardButtons(buttons)
    msg.setDefaultButton(default)
    msg.setStyleSheet(self._get_message_box_style())
    return msg.exec()

def _get_message_box_style(self) -> str:
    return """
        QMessageBox { background: #252526; }
        QMessageBox QLabel { color: #D4D4D4; font-size: 12px; }
        QPushButton {
            background: #2D2D30;
            border: 1px solid #454545;
            border-radius: 4px;
            padding: 0 16px;
            color: #D4D4D4;
            font-size: 12px;
            font-weight: 500;
            min-height: 32px;
            min-width: 80px;
        }
        QPushButton:hover { background: #2A2D2E; border-color: #007ACC; color: white; }
        QPushButton:default { background: #007ACC; border-color: #007ACC; color: white; }
    """
```

## Usage Examples

```python
# Warning
self._show_styled_message("Warning", "No nodes selected", icon=QMessageBox.Icon.Warning)

# Error
self._show_styled_message("Error", "Execution failed", f"Details: {error}", QMessageBox.Icon.Critical)

# Confirmation
result = self._show_styled_question(
    "Unsaved Changes",
    "Save changes before closing?",
    QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
    QMessageBox.StandardButton.Save
)
```

## Controllers with helpers
- workflow_controller.py
- execution_controller.py
- menu_controller.py
- main_window.py
