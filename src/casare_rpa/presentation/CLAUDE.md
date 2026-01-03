# Presentation Layer Rules

**Qt/PySide6 UI for Canvas application.**

## Core Principles

1. **Theme Only**: Use `THEME.*` constants, never hardcoded colors
2. **Signal/Slot**: `@Slot()` decorator required, no lambdas
3. **MVC Pattern**: Controllers handle logic, widgets display only
4. **Qt Lifetime**: Guard delayed callbacks against deleted objects

## Theme (MANDATORY)

```python
# CORRECT
from casare_rpa.presentation.canvas.theme import THEME, TOKENS
widget.setStyleSheet(f"color: {THEME.text_primary};")

# WRONG
widget.setStyleSheet("color: #ffffff;")  # NO
```

See `@ui/theme.py` for all theme tokens.

## Signal/Slot Rules

```python
# CORRECT
from PySide6.QtCore import Slot
from functools import partial

@Slot()
def on_clicked(self):
    self.button.clicked.connect(partial(self._handle, id="x"))

# WRONG
self.button.clicked.connect(lambda: self.handle(id="x"))  # NO
```

## Dialog System

```python
from casare_rpa.presentation.canvas.ui.dialogs import BaseDialog
from casare_rpa.presentation.canvas.ui.dialogs.dialog_styles import (
    show_error, show_warning, show_info
)

show_error(parent=self, message="Error occurred")
```

## MVC Controllers

```python
from casare_rpa.presentation.canvas.controllers import BaseController

class MyController(BaseController):
    def __init__(self, model, view):
        super().__init__(model, view)
```

See `@controllers/` for controller patterns.

## Cross-References

- Domain events: `../domain/_index.md`
- UI components: `canvas/_index.md`
- Root guide: `../../../../CLAUDE.md`

