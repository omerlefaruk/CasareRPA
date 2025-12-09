# UI Standards

> All buttons/dialogs MUST follow these sizing/color standards.
> **NEVER hardcode hex colors** - use Theme constants.
> Use `dialog_styles.py` for standardized dialog styling.

## Key Imports

```python
# Theme system (REQUIRED for all UI code)
from casare_rpa.presentation.canvas.ui.theme import (
    Theme, ThemeMode,
    SPACING, BORDER_RADIUS, FONT_SIZES, BUTTON_SIZES, ICON_SIZES, ANIMATIONS,
    get_node_status_color, get_wire_color, get_type_color, get_type_badge
)

# Dialog styling
from casare_rpa.presentation.canvas.ui.dialogs.dialog_styles import (
    DialogStyles, DialogSize, apply_dialog_style,
    show_styled_message, show_styled_warning, show_styled_error, show_styled_question
)

# UI coordination (for MainWindow components)
from casare_rpa.presentation.canvas.coordinators import SignalCoordinator
from casare_rpa.presentation.canvas.managers import PanelManager
```

## Theme Module (`theme.py`)

Central theme system with frozen dataclasses for type safety.

### Constants
| Constant | Values |
|----------|--------|
| `SPACING` | xs=4, sm=8, md=16, lg=24, xl=32 |
| `BORDER_RADIUS` | none=0, sm=4, md=8, lg=12, full=9999 |
| `FONT_SIZES` | xs=10, sm=11, md=12, lg=14, xl=16, xxl=20 |
| `BUTTON_SIZES` | sm=24, md=28, lg=32 |
| `ICON_SIZES` | xs=12, sm=16, md=20, lg=32 |
| `ANIMATIONS` | fast=150, normal=300, slow=500 (ms) |

### CSS Generation Methods
```python
Theme.button_style(size="md", variant="primary|danger|default")
Theme.panel_style()
Theme.input_style()
Theme.message_box_style()
Theme.toolbar_button_style()
Theme.combo_box_style()
Theme.variable_button_style()
```

### Helper Functions
```python
get_node_status_color(status)  # idle, running, success, error, skipped
get_wire_color(data_type)      # exec, bool, string, number, list, dict, table
get_status_color(status)       # General status coloring
get_type_color(type_name)      # Data type colors for badges
get_type_badge(type_name)      # Badge characters (T, #, ?, [], {})
```

## Dialog Styling Module

Import from `casare_rpa.presentation.canvas.ui.dialogs.dialog_styles`:

```python
from casare_rpa.presentation.canvas.ui.dialogs import (
    DialogStyles,
    DialogSize,
    apply_dialog_style,
    show_styled_warning,
    show_styled_error,
    show_styled_question,
)

# Apply standardized styling to any dialog:
apply_dialog_style(self, DialogSize.MD)  # SM, MD, LG, XL

# Use styled message boxes:
show_styled_warning(self, "Title", "Message")
show_styled_error(self, "Title", "Message")
result = show_styled_question(self, "Title", "Question?")

# Use individual style methods:
self.setStyleSheet(DialogStyles.full_dialog_style())
header.setStyleSheet(DialogStyles.header(font_size=16))
button.setStyleSheet(DialogStyles.button_primary())
```

## Dialog Sizes

| Size | Dimensions | Usage |
|------|------------|-------|
| SM | 400x300 | Simple confirmations, small forms |
| MD | 600x450 | Standard forms, settings |
| LG | 800x600 | Complex forms, multi-tab dialogs |
| XL | 1000x750 | Wizards, dashboards |

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

## SignalCoordinator & PanelManager

**NEVER connect signals directly in MainWindow.** Delegate to coordinators:

### SignalCoordinator
Routes Qt signals for decoupled communication:
- Workflow actions (new, open, save, import, export)
- Execution actions (run, pause, stop, restart)
- Debug actions (step_over, step_into, debug_workflow)
- Node/View actions (select, rename, focus, zoom)
- Mode toggles (auto_connect, high_performance)
- Recording actions (browser recording with action replay)

### PanelManager
Manages dock panel lifecycle:

**Bottom Panel Tabs:** Variables, Output, Log, Validation, History
**Side Panel Tabs:** Debug, Process Mining, Robot Picker, Analytics

```python
# Show/hide panels
panel_manager.show_bottom_panel()
panel_manager.toggle_side_panel()
panel_manager.toggle_panel_tab("log")  # Switch to specific tab

# Access panel widgets
panel_manager.log_viewer
panel_manager.validation_panel
panel_manager.debug_panel
```

## Deprecated Patterns

| Old Pattern | New Pattern |
|-------------|-------------|
| Hardcoded `#007ACC` | `Theme.colors.accent_primary` |
| Direct signal connects in MainWindow | Use `SignalCoordinator` |
| Direct panel show/hide | Use `PanelManager` |
| `QMessageBox.warning()` | `show_styled_warning()` |
