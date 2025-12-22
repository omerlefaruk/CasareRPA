# Dependency Graph - CasareRPA

Visual and textual representation of module dependencies for AI agents.

---

## Layer Dependencies (High Level)

```
┌─────────────────────────────────────────────────────────────┐
│                      PRESENTATION                            │
│  (UI, Canvas, Visual Nodes, Controllers)                     │
│  - Can import from: Application, Domain, Infrastructure*     │
└─────────────────────────────────────┬───────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────┐
│                       APPLICATION                            │
│  (Use Cases, Orchestrators, Handlers)                        │
│  - Can import from: Domain                                   │
│  - Must NOT import from: Infrastructure, Presentation        │
└─────────────────────────────────────┬───────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────┐
│                         DOMAIN                               │
│  (Entities, Value Objects, Services, Events, Protocols)      │
│  - Can import from: NOTHING (pure Python only)               │
│  - stdlib only: typing, dataclasses, enum, abc               │
└─────────────────────────────────────────────────────────────┘
                                      ▲
                                      │
┌─────────────────────────────────────┴───────────────────────┐
│                      INFRASTRUCTURE                          │
│  (Adapters, Persistence, HTTP, Resources)                    │
│  - Can import from: Domain (interfaces/protocols)            │
│  - Implements domain protocols                               │
└─────────────────────────────────────────────────────────────┘

* Presentation can import Infrastructure for DI wiring only
```

---

## Module Import Rules

### Domain (`src/casare_rpa/domain/`)

```python
# ALLOWED
from typing import Protocol, Any, Optional
from dataclasses import dataclass, field
from enum import Enum, auto
from abc import ABC, abstractmethod
import uuid
import re

# FORBIDDEN
from casare_rpa.infrastructure import *  # ❌
from casare_rpa.presentation import *    # ❌
from casare_rpa.application import *     # ❌
import httpx                             # ❌
from PySide6 import *                    # ❌
from playwright import *                 # ❌
```

### Application (`src/casare_rpa/application/`)

```python
# ALLOWED
from casare_rpa.domain.entities import BaseNode, Workflow
from casare_rpa.domain.value_objects import DataType, NodeStatus
from casare_rpa.domain.events import get_event_bus, NodeCompleted
from casare_rpa.domain.protocols import CredentialProviderProtocol
from casare_rpa.domain.interfaces import IExecutionContext

# FORBIDDEN
from casare_rpa.infrastructure import *  # ❌
from casare_rpa.presentation import *    # ❌
```

### Infrastructure (`src/casare_rpa/infrastructure/`)

```python
# ALLOWED
from casare_rpa.domain.interfaces import IExecutionContext
from casare_rpa.domain.protocols import CredentialProviderProtocol
from casare_rpa.domain.value_objects import DataType
import httpx
from playwright.async_api import async_playwright
import aiofiles

# FORBIDDEN
from casare_rpa.application import *     # ❌
from casare_rpa.presentation import *    # ❌
```

### Presentation (`src/casare_rpa/presentation/`)

```python
# ALLOWED
from casare_rpa.domain.entities import BaseNode
from casare_rpa.domain.value_objects import DataType
from casare_rpa.domain.events import get_event_bus
from casare_rpa.application.use_cases import ExecuteWorkflowUseCase
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Signal, Slot

# Infrastructure for DI only
from casare_rpa.infrastructure.execution import ExecutionContext
```

---

## Key File Dependencies

### Node Execution Flow

```
nodes/browser/click_node.py
    │
    ├── imports: domain/entities/base_node.py (BaseNode)
    ├── imports: domain/value_objects/types.py (DataType)
    ├── imports: domain/schemas/property_schema.py (PropertyDef)
    ├── imports: nodes/browser/browser_base.py (BrowserBaseNode)
    │       │
    │       └── imports: playwright (Page, Locator)
    │
    └── called by: application/execution/workflow_executor.py
            │
            └── provides: ExecutionContext
                    │
                    └── from: infrastructure/execution/execution_context.py
```

### Event Flow

```
domain/events.py (EventBus singleton)
    │
    ├── publishes: NodeCompleted, WorkflowStarted, etc.
    │
    ├── subscribed by: application/handlers/execution_handler.py
    │
    └── bridged to: presentation/canvas/coordinators/event_bridge.py
            │
            └── emits: Qt Signals
                    │
                    └── received by: presentation/canvas/ui/*.py (widgets)
```

### Workflow Serialization

```
presentation/canvas/serialization/workflow_serializer.py
    │
    ├── imports: domain/entities/workflow.py (WorkflowSchema)
    ├── imports: domain/value_objects/types.py (DataType, PortType)
    │
    ├── writes to: .json files
    │
    └── read by: utils/workflow/workflow_loader.py
            │
            └── imports: nodes/__init__.py (node registry)
```

---

## Hot Paths (High-Impact Dependencies)

These files, if changed, affect many others:

| File | Dependents | Impact |
|------|------------|--------|
| `domain/entities/base_node.py` | All 400+ nodes | CRITICAL |
| `domain/value_objects/types.py` | Everything | CRITICAL |
| `domain/events.py` | All event handlers | HIGH |
| `nodes/__init__.py` | All node imports | HIGH |
| `presentation/canvas/theme.py` | All UI components | MEDIUM |
| `domain/schemas/property_schema.py` | All node schemas | HIGH |

---

## Dependency Injection Points

Where concrete implementations are wired:

```
presentation/canvas/main_window.py
    │
    ├── creates: ExecutionContext (infrastructure)
    ├── creates: WorkflowExecutor (application)
    ├── creates: EventBridge (presentation)
    │
    └── wires together via constructor injection
```

```
application/dependency_injection/container.py
    │
    ├── registers: CredentialProvider → infrastructure implementation
    ├── registers: WorkflowRepository → infrastructure implementation
    ├── registers: ExecutionContext → infrastructure implementation
    │
    └── provides: get_container() singleton
```

---

## Package Import Patterns

### Correct Import Chain

```python
# In a node file
from casare_rpa.domain import node, properties  # decorators
from casare_rpa.domain.entities import BaseNode  # base class
from casare_rpa.domain.schemas import PropertyDef, PropertyType  # schema
from casare_rpa.domain.value_objects import DataType, Port  # types
```

### Anti-Pattern Detection

```python
# RED FLAG: Application importing Infrastructure
# File: application/use_cases/execute_workflow.py
from casare_rpa.infrastructure.execution import ExecutionContext  # ❌ WRONG

# CORRECT: Use domain interface
from casare_rpa.domain.interfaces import IExecutionContext  # ✓ RIGHT
```

---

## External Dependencies by Layer

### Domain (stdlib only)
- `typing`
- `dataclasses`
- `enum`
- `abc`
- `uuid`
- `re`
- `datetime`

### Application
- Same as Domain
- `asyncio`
- `loguru` (logging)

### Infrastructure
- `httpx` / `aiohttp` (HTTP)
- `playwright` (browser automation)
- `uiautomation` (desktop automation)
- `aiofiles` (async file I/O)
- `qdrant-client` (vector DB)
- `cryptography` (credentials)

### Presentation
- `PySide6` (Qt6)
- `qasync` (Qt async integration)
- All of the above (for DI wiring)

---

## Change Impact Matrix

| If you change... | Also check/update... |
|------------------|---------------------|
| `BaseNode` signature | All 400+ node subclasses |
| `DataType` enum | Serialization, port compatibility |
| `PropertyDef` | Node schemas, visual node widgets |
| Event class | Event handlers, event bridge |
| `THEME` colors | All styled widgets |
| Port types | Connection validation, visual wires |
| Node registry | Visual node registry, workflow loader |

---

## Circular Dependency Prevention

### Problem Pattern

```python
# domain/entities/node.py
from casare_rpa.domain.services import validate_node  # ❌ Creates cycle

# domain/services/validator.py
from casare_rpa.domain.entities import Node  # Part of cycle
```

### Solution: Dependency Inversion

```python
# domain/entities/node.py
from casare_rpa.domain.protocols import ValidatorProtocol

class Node:
    def validate(self, validator: ValidatorProtocol):
        return validator.validate(self)

# domain/services/validator.py
from casare_rpa.domain.protocols import ValidatorProtocol

class NodeValidator(ValidatorProtocol):
    def validate(self, node) -> list[str]:
        # Validation logic
        pass
```

---

## Quick Reference: "Can X import from Y?"

|  | Domain | Application | Infrastructure | Presentation |
|--|--------|-------------|----------------|--------------|
| **Domain** | ✓ | ✗ | ✗ | ✗ |
| **Application** | ✓ | ✓ | ✗ | ✗ |
| **Infrastructure** | ✓ (protocols) | ✗ | ✓ | ✗ |
| **Presentation** | ✓ | ✓ | ✓ (DI only) | ✓ |

---

*Last updated: 2025-12-14*
