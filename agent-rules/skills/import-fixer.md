# Import Fixer Skill

Fix import errors and organize imports.

## Common Patterns

### Domain Layer
```python
from casare_rpa.domain.entities import BaseNode
from casare_rpa.domain.value_objects import DataType, NodeStatus
from casare_rpa.domain.services import ExecutionOrchestrator
from casare_rpa.domain.decorators import executable_node, node_schema
from casare_rpa.domain.schemas import PropertyDef, PropertyType
```

### Application Layer
```python
from casare_rpa.application.use_cases import ExecuteWorkflowUseCase
from casare_rpa.application.services import ExecutionLifecycleManager
```

### Infrastructure Layer
```python
from casare_rpa.infrastructure.browser import PlaywrightManager
from casare_rpa.infrastructure.http import UnifiedHttpClient
from casare_rpa.infrastructure.execution import ExecutionContext
```

### Nodes
```python
from casare_rpa.nodes.browser import BrowserBaseNode
from casare_rpa.nodes import StartNode, EndNode
```

## Rules
- Use absolute imports
- Order: stdlib → third-party → local
- Group by layer
