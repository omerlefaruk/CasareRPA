---
paths: src/casare_rpa/presentation/**/*.py
---

# PySide6 Signal/Slot Rules

## @Slot Decorator (MANDATORY)

**ALWAYS** decorate slot methods with `@Slot(types...)`

```python
from PySide6.QtCore import Slot

# CORRECT
@Slot()
def _on_button_clicked(self) -> None:
    ...

@Slot(str)
def _on_text_changed(self, text: str) -> None:
    ...

@Slot(bool)
def _on_toggled(self, checked: bool) -> None:
    ...

# WRONG - Missing decorator
def _on_button_clicked(self) -> None:  # NO!
    ...
```

## Type Mapping

| Signal Type | @Slot Decorator |
|-------------|-----------------|
| `Signal()` | `@Slot()` |
| `Signal(str)` | `@Slot(str)` |
| `Signal(bool)` | `@Slot(bool)` |
| `Signal(int)` | `@Slot(int)` |
| `Signal(dict)` | `@Slot(dict)` |
| `Signal(object)` | `@Slot(object)` |
| `Signal(str, str)` | `@Slot(str, str)` |

## No Lambda Connections

**NEVER** use lambdas in signal connections

```python
# WRONG - Lambda connection
button.clicked.connect(lambda: self._do_thing())  # NO!

# CORRECT - Named method
@Slot()
def _on_button_clicked(self) -> None:
    self._do_thing()

button.clicked.connect(self._on_button_clicked)
```

## Captured Variables (Use functools.partial)

```python
from functools import partial

# WRONG - Lambda with capture
for item in items:
    btn.clicked.connect(lambda _, i=item: self._handle(i))  # NO!

# CORRECT - functools.partial
for item in items:
    btn.clicked.connect(partial(self._handle_item, item))

def _handle_item(self, item, *args) -> None:
    ...
```

## Thread Safety

**Cross-thread signals MUST use QueuedConnection:**

```python
from PySide6.QtCore import Qt

# Background thread -> UI thread
worker.finished.connect(
    self._on_finished,
    Qt.ConnectionType.QueuedConnection
)
```

## Cleanup Pattern

Controllers/panels managing connections should implement cleanup:

```python
class MyController:
    def __init__(self):
        self._connections: list = []

    def _connect(self, signal, slot):
        signal.connect(slot)
        self._connections.append((signal, slot))

    def cleanup(self) -> None:
        for signal, slot in self._connections:
            try:
                signal.disconnect(slot)
            except RuntimeError:
                pass
        self._connections.clear()
```

## Context Menu Pattern

Store context before showing menu, retrieve in slot:

```python
def _show_context_menu(self, pos):
    self._context_item = self._get_item_at(pos)  # Store context
    menu.exec(pos)

@Slot()
def _on_context_action(self) -> None:
    item = self._context_item  # Retrieve context
    self._do_action(item)
```

## Reference Files

- `coordinators/signal_coordinator.py` - 54 @Slot methods example
- `ui/debug_panel.py` - Context menu + cleanup pattern
- `controllers/execution_controller.py` - Thread-safe EventBus bridge
