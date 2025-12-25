# Decision Tree: Adding a New Feature

## Quick Decision

```
What kind of feature?
├─ NEW NODE → See add-node.md
├─ UI COMPONENT → Step 1: Presentation Layer
├─ API/INTEGRATION → Step 2: Infrastructure Layer
├─ BUSINESS LOGIC → Step 3: Domain Layer
└─ CROSS-CUTTING → Step 4: Multiple Layers
```

---

## Pre-Flight Checklist

Before writing ANY code:

1. **Search existing code** - Someone may have started this
   ```bash
   qdrant-find: "feature description"
   Grep: "keyword" --path src/
   ```

2. **Check plans** - May already be planned
   ```bash
   Grep: "feature" --path .claude/plans/
   ```

3. **Read indexes** - Understand current structure
   - `domain/_index.md`
   - `presentation/canvas/_index.md`
   - `infrastructure/_index.md`

---

## Step 1: UI Component (Presentation Layer)

### Files to Create/Modify

| Component | Location |
|-----------|----------|
| Widget | `presentation/canvas/ui/my_widget.py` |
| Panel | `presentation/canvas/ui/panels/my_panel.py` |
| Dialog | `presentation/canvas/ui/dialogs/my_dialog.py` |
| Action | `presentation/canvas/actions/my_action.py` |

### Template: New Widget

```python
# presentation/canvas/ui/my_widget.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Signal, Slot
from casare_rpa.presentation.canvas.theme import THEME

class MyWidget(QWidget):
    """
    AI-HINT: Custom widget for X feature.
    AI-CONTEXT: Used by MainWindow, triggered from toolbar.
    """

    # Signals for communication
    value_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        self.label = QLabel("My Widget")
        self.label.setStyleSheet(f"color: {THEME['text_primary']};")
        layout.addWidget(self.label)

        self.setStyleSheet(f"""
            background-color: {THEME['bg_primary']};
            border: 1px solid {THEME['border']};
        """)

    def _connect_signals(self):
        # Use named methods, not lambdas
        pass

    @Slot(str)
    def on_external_update(self, value: str):
        """Handle updates from other components."""
        self.label.setText(value)
        self.value_changed.emit(value)
```

### Integration Points

1. **Add to MainWindow** - `presentation/canvas/main_window.py`
2. **Add to PanelManager** - `presentation/canvas/managers/panel_manager.py`
3. **Add toolbar action** - `presentation/canvas/ui/toolbar.py`

---

## Step 2: API/Integration (Infrastructure Layer)

### Files to Create/Modify

| Component | Location |
|-----------|----------|
| API Client | `infrastructure/{service}/client.py` |
| Adapter | `infrastructure/{service}/adapter.py` |
| Config | `infrastructure/config/{service}_config.py` |

### Template: New API Client

```python
# infrastructure/my_service/client.py
from casare_rpa.infrastructure.http import UnifiedHttpClient, HttpClientConfig
from loguru import logger

class MyServiceClient:
    """
    AI-HINT: Client for MyService API.
    AI-CONTEXT: Used by MyServiceNode for external integration.
    AI-WARNING: Requires API key in credentials.
    """

    def __init__(self, api_key: str, base_url: str = "https://api.myservice.com"):
        self._api_key = api_key
        self._base_url = base_url
        self._config = HttpClientConfig(
            max_retries=3,
            timeout=30,
        )

    async def get_data(self, resource_id: str) -> dict:
        """Fetch data from MyService."""
        async with UnifiedHttpClient(self._config) as client:
            response = await client.get(
                f"{self._base_url}/resources/{resource_id}",
                headers={"Authorization": f"Bearer {self._api_key}"}
            )
            return response.json()

    async def create_resource(self, data: dict) -> dict:
        """Create new resource in MyService."""
        async with UnifiedHttpClient(self._config) as client:
            response = await client.post(
                f"{self._base_url}/resources",
                json=data,
                headers={"Authorization": f"Bearer {self._api_key}"}
            )
            return response.json()
```

### Domain Protocol (Interface)

```python
# domain/protocols/my_service.py
from typing import Protocol

class MyServiceProtocol(Protocol):
    """Interface for MyService - domain depends on this, not concrete implementation."""

    async def get_data(self, resource_id: str) -> dict: ...
    async def create_resource(self, data: dict) -> dict: ...
```

---

## Step 3: Business Logic (Domain Layer)

### Files to Create/Modify

| Component | Location |
|-----------|----------|
| Entity | `domain/entities/my_entity.py` |
| Value Object | `domain/value_objects/my_value.py` |
| Domain Service | `domain/services/my_service.py` |
| Event | `domain/events/my_events.py` |

### Template: New Entity

```python
# domain/entities/my_entity.py
from dataclasses import dataclass, field
from typing import Optional
from casare_rpa.domain.value_objects import EntityId

@dataclass
class MyEntity:
    """
    AI-HINT: Domain entity for X concept.
    AI-CONTEXT: Part of Workflow aggregate boundary.
    """

    id: EntityId
    name: str
    config: dict = field(default_factory=dict)

    def validate(self) -> list[str]:
        """Validate entity state. Returns list of validation errors."""
        errors = []
        if not self.name:
            errors.append("Name is required")
        return errors

    def update_config(self, key: str, value: any) -> None:
        """Update configuration value."""
        self.config[key] = value
```

### Template: New Domain Event

```python
# domain/events/my_events.py
from dataclasses import dataclass
from casare_rpa.domain.events import DomainEvent

@dataclass(frozen=True)
class MyEntityCreated(DomainEvent):
    """Raised when MyEntity is created."""
    entity_id: str
    entity_name: str

@dataclass(frozen=True)
class MyEntityUpdated(DomainEvent):
    """Raised when MyEntity is updated."""
    entity_id: str
    changed_fields: tuple[str, ...]
```

---

## Step 4: Cross-Cutting Feature

For features spanning multiple layers:

### Implementation Order

```
1. DOMAIN → Define entities, value objects, events
2. INFRASTRUCTURE → Implement persistence, external APIs
3. APPLICATION → Create use cases, orchestration
4. PRESENTATION → Build UI components
```

### Example: Adding "Workflow Templates"

```
domain/
  entities/workflow_template.py          # 1. Entity
  value_objects/template_metadata.py     # 1. Value object
  events/template_events.py              # 1. Events

infrastructure/
  persistence/template_repository.py     # 2. Storage

application/
  use_cases/apply_template.py            # 3. Use case

presentation/
  canvas/ui/template_browser.py          # 4. UI
  canvas/ui/dialogs/template_dialog.py   # 4. Dialogs
```

---

## Integration Checklist

### Domain Layer
- [ ] Created entity/value object with validation
- [ ] Defined domain events for state changes
- [ ] Added to `domain/__init__.py` exports
- [ ] Updated `domain/_index.md`

### Infrastructure Layer
- [ ] Used `UnifiedHttpClient` for HTTP calls
- [ ] Implemented domain protocol/interface
- [ ] Added error handling with specific exceptions
- [ ] Updated `infrastructure/_index.md`

### Application Layer
- [ ] Created use case class
- [ ] Injected dependencies via constructor
- [ ] Published domain events after success

### Presentation Layer
- [ ] Used `THEME` for all colors
- [ ] Added `@Slot` to all signal handlers
- [ ] No lambdas in signal connections
- [ ] Updated `presentation/canvas/_index.md`

---

## Testing Requirements

| Layer | Test Location | Mock Strategy |
|-------|---------------|---------------|
| Domain | `tests/domain/` | No mocks - use real objects |
| Infrastructure | `tests/infrastructure/` | Mock external APIs |
| Application | `tests/application/` | Mock infrastructure |
| Presentation | `tests/presentation/` | Mock heavy Qt components |

---

## Files That Often Need Updates

| When Adding... | Update These |
|----------------|--------------|
| New entity | `domain/entities/__init__.py`, `domain/_index.md` |
| New node | `nodes/__init__.py`, `nodes/_index.md`, `registry_data.py` |
| New visual node | `visual_nodes/{category}/__init__.py`, `visual_nodes/_index.md` |
| New API client | `infrastructure/{service}/__init__.py`, `infrastructure/_index.md` |
| New event | `domain/events/__init__.py` |

---

*See also: `.brain/systemPatterns.md`, `.brain/projectRules.md`*
