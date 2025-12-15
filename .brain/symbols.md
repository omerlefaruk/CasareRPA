# Symbol Registry - CasareRPA

Quick lookup for key classes, functions, and constants. Use for fast navigation.

**Search Strategy**: Use this file first, then `Grep` for exact matches.

---

## Base Classes (Inheritance Entry Points)

| Symbol | Path | Purpose |
|--------|------|---------|
| `BaseNode` | `domain/entities/base_node.py:44` | All automation nodes inherit from this |
| `BrowserBaseNode` | `nodes/browser/browser_base.py:331` | All browser/Playwright nodes inherit |
| `VisualNode` | `presentation/canvas/visual_nodes/base_visual_node.py:25` | All visual canvas nodes inherit |
| `AbstractUnitOfWork` | `domain/interfaces/unit_of_work.py:15` | Unit of Work pattern interface |

---

## Decorators

| Symbol | Path | Purpose |
|--------|------|---------|
| `@node` | `domain/decorators.py:30` | Register node class, auto-add exec ports |
| `@properties` | `domain/decorators.py:142` | Define node property schema |
| `@executable_node` | `nodes/decorators.py:10` | Legacy node registration (use `@node`) |
| `@node_schema` | `nodes/decorators.py:45` | Legacy property schema (use `@properties`) |

---

## Singletons & Factories

| Symbol | Path | Purpose |
|--------|------|---------|
| `get_event_bus()` | `domain/events/bus.py:152` | Get domain event bus singleton |
| `get_node_registry()` | `nodes/__init__.py:50` | Get node class registry |
| `THEME` | `presentation/canvas/theme.py:97` | UI theme constants singleton |

---

## Domain Events

| Symbol | Path | Attributes |
|--------|------|------------|
| `NodeStarted` | `domain/events/__init__.py` | node_id, node_type, workflow_id |
| `NodeCompleted` | `domain/events/__init__.py` | node_id, node_type, workflow_id, execution_time_ms |
| `NodeFailed` | `domain/events/__init__.py` | node_id, node_type, error_code, error_message |
| `WorkflowStarted` | `domain/events/__init__.py` | workflow_id, workflow_name, total_nodes |
| `WorkflowCompleted` | `domain/events/__init__.py` | workflow_id, execution_time_ms, nodes_executed |
| `WorkflowFailed` | `domain/events/__init__.py` | workflow_id, failed_node_id, error_message |

---

## Value Objects & Enums

| Symbol | Path | Values/Purpose |
|--------|------|----------------|
| `DataType` | `domain/value_objects/types.py:15` | STRING, INTEGER, FLOAT, BOOLEAN, LIST, DICT, ANY, EXEC, PAGE, ELEMENT |
| `NodeStatus` | `domain/value_objects/types.py:45` | IDLE, RUNNING, SUCCESS, ERROR, SKIPPED |
| `PortType` | `domain/value_objects/types.py:60` | INPUT, OUTPUT, EXEC_INPUT, EXEC_OUTPUT |
| `PropertyType` | `domain/schemas/property_types.py:10` | STRING, INTEGER, FLOAT, BOOLEAN, CHOICE, FILE_PATH, SELECTOR, etc. |
| `Port` | `domain/value_objects/port.py:10` | Immutable port definition |
| `ExecutionResult` | `domain/value_objects/types.py:80` | TypedDict for node execution results |

---

## Domain Entities

| Symbol | Path | Purpose |
|--------|------|---------|
| `Workflow` | `domain/aggregates/workflow.py:20` | Aggregate root for workflow operations |
| `WorkflowId` | `domain/aggregates/workflow.py:10` | Value object for workflow identity |
| `WorkflowSchema` | `domain/entities/workflow.py:15` | Workflow definition schema |
| `Variable` | `domain/entities/variable.py:10` | Variable definition entity |
| `Project` | `domain/entities/project/project.py:15` | Project entity |
| `Scenario` | `domain/entities/project/scenario.py:10` | Scenario entity |
| `Subflow` | `domain/entities/subflow.py:10` | Reusable workflow block |

---

## Schemas & Property Definitions

| Symbol | Path | Purpose |
|--------|------|---------|
| `PropertyDef` | `domain/schemas/property_schema.py:25` | Single property definition |
| `NodeSchema` | `domain/schemas/property_schema.py:120` | Complete node schema |
| `BROWSER_TIMEOUT` | `nodes/browser/property_constants.py:10` | Timeout PropertyDef constant |
| `BROWSER_RETRY_COUNT` | `nodes/browser/property_constants.py:20` | Retry count PropertyDef constant |
| `BROWSER_SELECTOR_STRICT` | `nodes/browser/property_constants.py:40` | Strict selector PropertyDef |

---

## Protocols (Interfaces)

| Symbol | Path | Purpose |
|--------|------|---------|
| `INode` | `domain/interfaces/__init__.py:10` | Node execution interface |
| `IExecutionContext` | `domain/interfaces/__init__.py:25` | Execution context protocol |
| `CredentialProviderProtocol` | `domain/protocols/__init__.py:10` | Credential resolution interface |
| `ExecutionContextProtocol` | `domain/protocols/__init__.py:30` | Context protocol |

---

## Mixins

| Symbol | Path | Purpose |
|--------|------|---------|
| `CredentialAwareMixin` | `domain/credentials.py:25` | Add credential support to nodes |

---

## Infrastructure Services

| Symbol | Path | Purpose |
|--------|------|---------|
| `UnifiedHttpClient` | `infrastructure/http/unified_http_client.py:141` | HTTP client with resilience |
| `HttpClientConfig` | `infrastructure/http/unified_http_client.py:68` | HTTP client configuration |
| `BrowserResourceManager` | `infrastructure/resources/browser_resource_manager.py:20` | Playwright browser lifecycle |
| `ExecutionContext` | `infrastructure/execution/execution_context.py:15` | Concrete execution context |

---

## Presentation Components

| Symbol | Path | Purpose |
|--------|------|---------|
| `CanvasGraphicsView` | `presentation/canvas/graph/canvas_view.py:25` | Main canvas widget |
| `NodeGraphicsItem` | `presentation/canvas/graph/node_item.py:20` | Visual node on canvas |
| `ConnectionItem` | `presentation/canvas/connections/connection_item.py:15` | Wire between ports |
| `SignalCoordinator` | `presentation/canvas/coordinators/signal_coordinator.py:20` | Action callback handler |
| `PanelManager` | `presentation/canvas/managers/panel_manager.py:15` | Panel visibility manager |
| `EventBus` | `presentation/canvas/events/__init__.py:20` | Presentation event bus |

---

## Application Services

| Symbol | Path | Purpose |
|--------|------|---------|
| `ExecutionOrchestrator` | `domain/services/__init__.py` | Workflow execution orchestration |
| `WorkflowValidator` | `domain/validation/__init__.py:15` | Workflow validation service |
| `resolve_variables` | `domain/variable_resolver.py:10` | Variable pattern resolution |

---

## Test Fixtures (tests/conftest.py)

| Symbol | Path | Purpose |
|--------|------|---------|
| `execution_context` | `tests/conftest.py` | Mock execution context fixture |
| `mock_page` | `tests/nodes/browser/conftest.py` | Mock Playwright page |
| `mock_browser` | `tests/nodes/browser/conftest.py` | Mock Playwright browser |
| `chain_executor` | `tests/nodes/chain/conftest.py` | Workflow chain executor |

---

## Key Constants

| Symbol | Path | Value/Purpose |
|--------|------|---------------|
| `_NODE_REGISTRY` | `nodes/__init__.py:25` | Node name to module mapping |
| `COLLECTION_NAME` | `scripts/index_codebase_qdrant.py:35` | "casare_codebase" |
| `VECTOR_NAME` | `scripts/index_codebase_qdrant.py:39` | "fast-all-minilm-l6-v2" |

---

## Port Helper Methods (BaseNode)

| Method | Purpose |
|--------|---------|
| `add_input_port(name, data_type, description)` | Add data input port |
| `add_output_port(name, data_type, description)` | Add data output port |
| `add_exec_input(name="exec_in")` | Add execution input port |
| `add_exec_output(name="exec_out")` | Add execution output port |
| `get_input_value(name)` | Get connected input value |
| `set_output_value(name, value)` | Set output port value |
| `get_parameter(name)` | Get config parameter |

---

## Quick Import Patterns

```python
# Node development
from casare_rpa.domain import node, properties, CredentialAwareMixin
from casare_rpa.domain.entities import BaseNode
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects import DataType, Port, ExecutionResult

# Browser nodes
from casare_rpa.nodes.browser import BrowserBaseNode, get_page_from_context
from casare_rpa.nodes.browser.property_constants import BROWSER_TIMEOUT, BROWSER_RETRY_COUNT

# Events
from casare_rpa.domain.events import get_event_bus, NodeCompleted, WorkflowStarted

# Visual nodes
from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode
from casare_rpa.presentation.canvas.theme import THEME

# Infrastructure
from casare_rpa.infrastructure.http import UnifiedHttpClient, HttpClientConfig

# Testing
from casare_rpa.domain.value_objects import ExecutionResult
```

---

*Last updated: 2025-12-14*
*Auto-regenerate: `python scripts/generate_symbols.py`*
