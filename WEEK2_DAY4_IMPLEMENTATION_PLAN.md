# Week 2 Day 4: Dependency Injection & Orchestration

**Implementation Plan for rpa-engine-architect**

**Version**: 1.0.0
**Created**: November 27, 2025
**Target Completion**: 1 Working Day (8 hours)
**Prerequisite Days**: Days 1-3 (Domain Entities, WorkflowRunner Decomposition, Infrastructure Layer)

---

## Executive Summary

This plan details the implementation of a Dependency Injection (DI) container and the final wiring of all architectural layers. The goal is to reduce the current `WorkflowRunner` (legacy wrapper) and `ExecuteWorkflowUseCase` to clean, maintainable orchestrators that rely on injected dependencies rather than hard-coded instantiation.

### Key Deliverables

1. **DI Container** (`application/dependency_injection/container.py`)
2. **Service Registration Module** (`application/dependency_injection/registrations.py`)
3. **Refactored ExecuteWorkflowUseCase** (~200 lines with injected dependencies)
4. **Integration Points** for Canvas, Robot, and Orchestrator
5. **Test Fixtures** for isolated unit testing

### Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| ExecuteWorkflowUseCase LOC | ~560 | ~200 |
| Hard-coded dependencies | 8+ | 0 |
| Constructor parameters (use case) | 5 | 3 (workflow, settings, container) |
| Test setup complexity | High | Low (mock container) |

---

## Hour-by-Hour Schedule

### Hour 1-2: DI Container Foundation (Core Infrastructure)

**Objective**: Create the dependency injection container with lifecycle management

**Tasks**:
1. Choose DI approach (Manual vs Library)
2. Implement `Container` class
3. Implement `ServiceRegistry` for registration DSL
4. Add singleton and transient scope management

### Hour 3: Service Registrations (Wiring Layer)

**Objective**: Register all services, repositories, and infrastructure components

**Tasks**:
1. Create `registrations.py` with all service bindings
2. Define factory methods for complex objects
3. Implement lazy initialization for expensive resources

### Hour 4-5: Refactor ExecuteWorkflowUseCase (Application Layer)

**Objective**: Refactor use case to accept injected dependencies

**Tasks**:
1. Extract dependencies to constructor injection
2. Remove all `from ... import` patterns for dependencies
3. Create interface contracts for all dependencies
4. Implement the clean orchestration pattern

### Hour 6: Integration Points (Presentation/Robot)

**Objective**: Wire DI container into Canvas MainWindow and Robot Agent

**Tasks**:
1. Create application bootstrap module
2. Update Canvas entry point (`run.py`)
3. Update Robot entry point (`tray_icon.py`)
4. Update Orchestrator entry point (`main_window.py`)

### Hour 7: Testing Infrastructure

**Objective**: Create test fixtures and validate DI setup

**Tasks**:
1. Create mock container for unit tests
2. Add integration tests for full workflow execution
3. Validate dependency graph (no circular dependencies)

### Hour 8: Documentation & Validation

**Objective**: Document patterns and verify all tests pass

**Tasks**:
1. Update CLAUDE.md with DI patterns
2. Run full test suite
3. Manual Canvas launch verification
4. Performance benchmark comparison

---

## File Structure and Locations

### New Files to Create

```
src/casare_rpa/
├── application/
│   ├── dependency_injection/
│   │   ├── __init__.py              # Public API exports
│   │   ├── container.py             # DI Container implementation
│   │   ├── registrations.py         # Service registration definitions
│   │   ├── scopes.py               # Scope definitions (singleton, transient)
│   │   ├── interfaces.py           # Protocol definitions for dependencies
│   │   └── factories.py            # Factory functions for complex objects
│   └── bootstrap.py                 # Application bootstrap/initialization
├── core/
│   └── ports/                       # NEW: Port interfaces moved to core
│       ├── __init__.py
│       ├── event_publisher.py       # IEventPublisher protocol
│       └── metrics_collector.py     # IMetricsCollector protocol
```

### Files to Modify

```
src/casare_rpa/
├── application/
│   └── use_cases/
│       └── execute_workflow.py      # Refactor to use injected dependencies
├── runner/
│   └── workflow_runner.py           # Update to use container (legacy wrapper)
├── canvas/
│   └── main_window.py              # Initialize container on startup
├── robot/
│   └── tray_icon.py                # Initialize container for Robot
│   └── agent.py                    # Use injected executor
├── orchestrator/
│   └── main_window.py              # Initialize container for Orchestrator
└── run.py                          # Bootstrap application with container
```

---

## DI Library Decision: Manual Implementation

### Rationale

After analyzing the codebase requirements, a **manual DI implementation** is recommended over external libraries like `dependency-injector` or `injector`:

1. **Simplicity**: CasareRPA has ~15-20 injectable services, not hundreds
2. **No External Dependency**: Reduces dependency footprint
3. **Full Control**: Async lifecycle management is critical for Playwright
4. **Transparency**: Easier for contributors to understand
5. **Type Safety**: Native Python protocols work well with type checkers

### Alternative Considered: dependency-injector

If the team prefers a library, `dependency-injector` is the best choice:
- Well-maintained, async-friendly
- Good PySide6 compatibility
- Declarative configuration

---

## Code Patterns and Examples

### 1. Container Implementation

```python
# src/casare_rpa/application/dependency_injection/container.py
"""
CasareRPA Dependency Injection Container

Manual DI implementation with lifecycle management for clean architecture.
Supports singleton and transient scopes with async initialization.
"""

from typing import (
    Any, Callable, Dict, Generic, Optional, Type, TypeVar, Union
)
from enum import Enum, auto
import asyncio
from loguru import logger


class Scope(Enum):
    """Dependency lifetime scope."""
    SINGLETON = auto()  # One instance per container
    TRANSIENT = auto()  # New instance each time
    SCOPED = auto()     # One instance per execution scope


T = TypeVar("T")


class ServiceDescriptor(Generic[T]):
    """Describes how to create and manage a service."""

    def __init__(
        self,
        service_type: Type[T],
        factory: Callable[["Container"], T],
        scope: Scope = Scope.TRANSIENT,
    ) -> None:
        self.service_type = service_type
        self.factory = factory
        self.scope = scope


class Container:
    """
    Dependency Injection Container.

    Manages service registration, resolution, and lifecycle.
    Thread-safe for singleton access.

    Usage:
        container = Container()
        container.register(IEventBus, lambda c: EventBus(), Scope.SINGLETON)
        event_bus = container.resolve(IEventBus)
    """

    def __init__(self) -> None:
        self._descriptors: Dict[Type, ServiceDescriptor] = {}
        self._singletons: Dict[Type, Any] = {}
        self._lock = asyncio.Lock()
        self._initialized = False

    def register(
        self,
        service_type: Type[T],
        factory: Callable[["Container"], T],
        scope: Scope = Scope.TRANSIENT,
    ) -> "Container":
        """
        Register a service with the container.

        Args:
            service_type: Interface or base type to register
            factory: Factory function that creates the service
            scope: Lifetime scope for the service

        Returns:
            Self for method chaining
        """
        self._descriptors[service_type] = ServiceDescriptor(
            service_type=service_type,
            factory=factory,
            scope=scope,
        )
        logger.debug(f"Registered {service_type.__name__} with scope {scope.name}")
        return self

    def register_instance(
        self,
        service_type: Type[T],
        instance: T,
    ) -> "Container":
        """
        Register an existing instance as singleton.

        Args:
            service_type: Interface or base type
            instance: Pre-created instance

        Returns:
            Self for method chaining
        """
        self._singletons[service_type] = instance
        self._descriptors[service_type] = ServiceDescriptor(
            service_type=service_type,
            factory=lambda c: instance,
            scope=Scope.SINGLETON,
        )
        return self

    def resolve(self, service_type: Type[T]) -> T:
        """
        Resolve a service from the container.

        Args:
            service_type: Type to resolve

        Returns:
            Service instance

        Raises:
            KeyError: If service not registered
        """
        if service_type not in self._descriptors:
            raise KeyError(
                f"Service {service_type.__name__} not registered. "
                f"Available services: {list(self._descriptors.keys())}"
            )

        descriptor = self._descriptors[service_type]

        if descriptor.scope == Scope.SINGLETON:
            if service_type not in self._singletons:
                self._singletons[service_type] = descriptor.factory(self)
                logger.debug(f"Created singleton: {service_type.__name__}")
            return self._singletons[service_type]

        # Transient: create new instance each time
        return descriptor.factory(self)

    def try_resolve(self, service_type: Type[T]) -> Optional[T]:
        """
        Try to resolve a service, returning None if not registered.
        """
        try:
            return self.resolve(service_type)
        except KeyError:
            return None

    async def initialize_async(self) -> None:
        """
        Initialize all singleton services that require async setup.

        Call this during application bootstrap.
        """
        async with self._lock:
            if self._initialized:
                return

            for service_type, descriptor in self._descriptors.items():
                if descriptor.scope == Scope.SINGLETON:
                    instance = self.resolve(service_type)

                    # Check for async initialization method
                    if hasattr(instance, "initialize"):
                        if asyncio.iscoroutinefunction(instance.initialize):
                            await instance.initialize()
                            logger.debug(
                                f"Async initialized: {service_type.__name__}"
                            )

            self._initialized = True
            logger.info("Container initialization complete")

    async def cleanup_async(self) -> None:
        """
        Cleanup all singleton services with async dispose methods.

        Call this during application shutdown.
        """
        for service_type, instance in self._singletons.items():
            if hasattr(instance, "cleanup"):
                try:
                    if asyncio.iscoroutinefunction(instance.cleanup):
                        await instance.cleanup()
                    else:
                        instance.cleanup()
                    logger.debug(f"Cleaned up: {service_type.__name__}")
                except Exception as e:
                    logger.error(f"Error cleaning up {service_type.__name__}: {e}")

        self._singletons.clear()
        self._initialized = False

    def create_scope(self) -> "ScopedContainer":
        """
        Create a scoped container for request-level dependencies.

        Returns:
            ScopedContainer that shares singletons but has own scoped instances
        """
        return ScopedContainer(self)


class ScopedContainer:
    """
    Scoped container for request/execution-level dependencies.

    Shares singletons with parent but maintains own scoped instances.
    """

    def __init__(self, parent: Container) -> None:
        self._parent = parent
        self._scoped: Dict[Type, Any] = {}

    def resolve(self, service_type: Type[T]) -> T:
        """Resolve from scoped container, falling back to parent."""
        descriptor = self._parent._descriptors.get(service_type)

        if descriptor is None:
            raise KeyError(f"Service {service_type.__name__} not registered")

        if descriptor.scope == Scope.SCOPED:
            if service_type not in self._scoped:
                self._scoped[service_type] = descriptor.factory(self._parent)
            return self._scoped[service_type]

        return self._parent.resolve(service_type)

    async def cleanup_async(self) -> None:
        """Cleanup scoped instances only."""
        for instance in self._scoped.values():
            if hasattr(instance, "cleanup"):
                try:
                    if asyncio.iscoroutinefunction(instance.cleanup):
                        await instance.cleanup()
                    else:
                        instance.cleanup()
                except Exception as e:
                    logger.error(f"Error cleaning up scoped instance: {e}")
        self._scoped.clear()
```

### 2. Interface Definitions (Protocols)

```python
# src/casare_rpa/application/dependency_injection/interfaces.py
"""
Protocol definitions for injectable dependencies.

Using Protocol from typing allows structural subtyping without
requiring inheritance, making mocking easier.
"""

from typing import Any, Callable, Dict, List, Optional, Protocol, Set
from datetime import datetime

from ...core.types import EventType, NodeId


# ==============================================================================
# Event System Protocols
# ==============================================================================

class IEvent(Protocol):
    """Protocol for event objects."""
    event_type: EventType
    data: Dict[str, Any]
    node_id: Optional[NodeId]
    timestamp: datetime


class IEventBus(Protocol):
    """Protocol for event bus."""

    def subscribe(
        self,
        event_type: EventType,
        handler: Callable[[IEvent], None]
    ) -> None:
        """Subscribe to an event type."""
        ...

    def unsubscribe(
        self,
        event_type: EventType,
        handler: Callable[[IEvent], None]
    ) -> None:
        """Unsubscribe from an event type."""
        ...

    def publish(self, event: IEvent) -> None:
        """Publish an event."""
        ...


# ==============================================================================
# Execution Protocols
# ==============================================================================

class IExecutionOrchestrator(Protocol):
    """Protocol for execution routing logic (domain service)."""

    def find_start_node(self) -> Optional[NodeId]:
        """Find the StartNode in workflow."""
        ...

    def get_next_nodes(
        self,
        current_node_id: NodeId,
        execution_result: Optional[Dict[str, Any]] = None
    ) -> List[NodeId]:
        """Determine next nodes to execute."""
        ...

    def is_reachable(self, start: NodeId, target: NodeId) -> bool:
        """Check if target is reachable from start."""
        ...

    def calculate_execution_path(
        self,
        start_node_id: NodeId,
        target_node_id: Optional[NodeId] = None
    ) -> Set[NodeId]:
        """Calculate nodes in execution path."""
        ...


class IExecutionContext(Protocol):
    """Protocol for execution context (infrastructure)."""

    def set_variable(self, name: str, value: Any) -> None:
        """Set a variable."""
        ...

    def get_variable(self, name: str, default: Any = None) -> Any:
        """Get a variable."""
        ...

    async def cleanup(self) -> None:
        """Cleanup resources."""
        ...


class INodeExecutor(Protocol):
    """Protocol for node execution."""

    async def execute(
        self,
        node: Any,
        context: IExecutionContext,
        timeout: float = 120.0
    ) -> Dict[str, Any]:
        """Execute a single node."""
        ...


# ==============================================================================
# Metrics Protocols
# ==============================================================================

class IMetricsCollector(Protocol):
    """Protocol for performance metrics collection."""

    def record_workflow_start(self, workflow_name: str) -> None:
        """Record workflow start."""
        ...

    def record_workflow_complete(
        self,
        workflow_name: str,
        duration_ms: float,
        success: bool
    ) -> None:
        """Record workflow completion."""
        ...

    def record_node_start(self, node_type: str, node_id: str) -> None:
        """Record node execution start."""
        ...

    def record_node_complete(
        self,
        node_type: str,
        node_id: str,
        duration_ms: float,
        success: bool
    ) -> None:
        """Record node execution completion."""
        ...


# ==============================================================================
# Repository Protocols
# ==============================================================================

class IWorkflowRepository(Protocol):
    """Protocol for workflow persistence."""

    async def save(self, workflow: Any, path: str) -> None:
        """Save workflow to storage."""
        ...

    async def load(self, path: str) -> Any:
        """Load workflow from storage."""
        ...

    async def exists(self, path: str) -> bool:
        """Check if workflow exists."""
        ...


# ==============================================================================
# Factory Protocols
# ==============================================================================

class IExecutionContextFactory(Protocol):
    """Protocol for creating execution contexts."""

    def create(
        self,
        workflow_name: str,
        initial_variables: Optional[Dict[str, Any]] = None,
        project_context: Optional[Any] = None
    ) -> IExecutionContext:
        """Create a new execution context."""
        ...


class IOrchestratorFactory(Protocol):
    """Protocol for creating execution orchestrators."""

    def create(self, workflow: Any) -> IExecutionOrchestrator:
        """Create orchestrator for a workflow."""
        ...
```

### 3. Service Registrations

```python
# src/casare_rpa/application/dependency_injection/registrations.py
"""
Service registration definitions for CasareRPA.

This module defines all service bindings for the DI container.
Called during application bootstrap to configure dependencies.
"""

from loguru import logger

from .container import Container, Scope
from .interfaces import (
    IEventBus,
    IMetricsCollector,
    IExecutionContextFactory,
    IOrchestratorFactory,
    INodeExecutor,
    IWorkflowRepository,
)


def register_core_services(container: Container) -> Container:
    """
    Register core services (singletons shared across application).

    Args:
        container: DI container to register with

    Returns:
        Container for method chaining
    """
    # EventBus - Singleton, shared across all components
    container.register(
        IEventBus,
        lambda c: _create_event_bus(),
        Scope.SINGLETON
    )

    # Metrics Collector - Singleton for performance tracking
    container.register(
        IMetricsCollector,
        lambda c: _create_metrics_collector(),
        Scope.SINGLETON
    )

    logger.info("Core services registered")
    return container


def register_factories(container: Container) -> Container:
    """
    Register factory services for creating execution components.

    Args:
        container: DI container to register with

    Returns:
        Container for method chaining
    """
    # ExecutionContext Factory - Creates new context per workflow execution
    container.register(
        IExecutionContextFactory,
        lambda c: _create_context_factory(),
        Scope.SINGLETON
    )

    # Orchestrator Factory - Creates orchestrator for workflow
    container.register(
        IOrchestratorFactory,
        lambda c: _create_orchestrator_factory(),
        Scope.SINGLETON
    )

    # Node Executor - Transient, stateless
    container.register(
        INodeExecutor,
        lambda c: _create_node_executor(),
        Scope.TRANSIENT
    )

    logger.info("Factory services registered")
    return container


def register_repositories(container: Container) -> Container:
    """
    Register repository services for persistence.

    Args:
        container: DI container to register with

    Returns:
        Container for method chaining
    """
    # Workflow Repository - Singleton for file operations
    container.register(
        IWorkflowRepository,
        lambda c: _create_workflow_repository(),
        Scope.SINGLETON
    )

    logger.info("Repository services registered")
    return container


def configure_container() -> Container:
    """
    Create and configure a fully-wired container.

    This is the main entry point for container setup.

    Returns:
        Configured DI container
    """
    container = Container()

    register_core_services(container)
    register_factories(container)
    register_repositories(container)

    logger.info("DI container configured with all services")
    return container


# ==============================================================================
# Factory Functions (Implementation Details)
# ==============================================================================

def _create_event_bus():
    """Create EventBus instance."""
    from ...core.events import EventBus
    return EventBus()


def _create_metrics_collector():
    """Create MetricsCollector instance."""
    from ...utils.performance.performance_metrics import get_metrics
    return get_metrics()


def _create_context_factory():
    """Create ExecutionContextFactory instance."""
    from .factories import ExecutionContextFactory
    return ExecutionContextFactory()


def _create_orchestrator_factory():
    """Create OrchestratorFactory instance."""
    from .factories import OrchestratorFactory
    return OrchestratorFactory()


def _create_node_executor():
    """Create NodeExecutor instance."""
    from .factories import DefaultNodeExecutor
    return DefaultNodeExecutor()


def _create_workflow_repository():
    """Create WorkflowRepository instance."""
    from ...infrastructure.persistence.workflow_repository import (
        JsonWorkflowRepository
    )
    return JsonWorkflowRepository()
```

### 4. Factory Implementations

```python
# src/casare_rpa/application/dependency_injection/factories.py
"""
Factory implementations for creating execution components.

Factories encapsulate the creation logic for complex objects,
allowing the DI container to remain simple.
"""

import asyncio
from typing import Any, Dict, Optional
from loguru import logger

from .interfaces import (
    IExecutionContext,
    IExecutionContextFactory,
    IExecutionOrchestrator,
    IOrchestratorFactory,
    INodeExecutor,
)
from ...core.execution_context import ExecutionContext
from ...domain.services.execution_orchestrator import ExecutionOrchestrator


class ExecutionContextFactory:
    """Factory for creating ExecutionContext instances."""

    def create(
        self,
        workflow_name: str,
        initial_variables: Optional[Dict[str, Any]] = None,
        project_context: Optional[Any] = None
    ) -> IExecutionContext:
        """
        Create a new execution context.

        Args:
            workflow_name: Name of workflow being executed
            initial_variables: Optional initial variables
            project_context: Optional project context

        Returns:
            Configured ExecutionContext
        """
        return ExecutionContext(
            workflow_name=workflow_name,
            initial_variables=initial_variables,
            project_context=project_context,
        )


class OrchestratorFactory:
    """Factory for creating ExecutionOrchestrator instances."""

    def create(self, workflow: Any) -> IExecutionOrchestrator:
        """
        Create an orchestrator for a workflow.

        Args:
            workflow: WorkflowSchema to orchestrate

        Returns:
            Configured ExecutionOrchestrator
        """
        return ExecutionOrchestrator(workflow)


class DefaultNodeExecutor:
    """
    Default node executor implementation.

    Executes nodes with timeout and error handling.
    """

    async def execute(
        self,
        node: Any,
        context: IExecutionContext,
        timeout: float = 120.0
    ) -> Dict[str, Any]:
        """
        Execute a single node.

        Args:
            node: Node instance to execute
            context: Execution context
            timeout: Execution timeout in seconds

        Returns:
            Execution result dictionary
        """
        try:
            result = await asyncio.wait_for(
                node.execute(context),
                timeout=timeout
            )
            return result or {"success": False, "error": "No result returned"}

        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": f"Node {node.node_id} timed out after {timeout}s"
            }
        except Exception as e:
            logger.exception(f"Node execution error: {node.node_id}")
            return {
                "success": False,
                "error": str(e)
            }
```

### 5. Refactored ExecuteWorkflowUseCase

```python
# src/casare_rpa/application/use_cases/execute_workflow.py (REFACTORED)
"""
CasareRPA - Application Use Case: Execute Workflow (Refactored)

Clean implementation using dependency injection.
Reduced from ~560 lines to ~200 lines.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from loguru import logger

from ..dependency_injection.container import Container, ScopedContainer
from ..dependency_injection.interfaces import (
    IEventBus,
    IMetricsCollector,
    IExecutionContextFactory,
    IOrchestratorFactory,
    INodeExecutor,
)
from ...domain.entities.workflow import WorkflowSchema
from ...core.types import EventType, NodeId, NodeStatus
from ...core.events import Event


class ExecutionSettings:
    """Execution settings value object (unchanged)."""

    def __init__(
        self,
        continue_on_error: bool = False,
        node_timeout: float = 120.0,
        target_node_id: Optional[NodeId] = None,
    ) -> None:
        self.continue_on_error = continue_on_error
        self.node_timeout = node_timeout
        self.target_node_id = target_node_id


class ExecuteWorkflowUseCase:
    """
    Application use case for executing workflows.

    REFACTORED: Uses dependency injection for all collaborators.

    Dependencies (injected via container):
    - IEventBus: Event publishing
    - IMetricsCollector: Performance metrics
    - IExecutionContextFactory: Creates execution contexts
    - IOrchestratorFactory: Creates execution orchestrators
    - INodeExecutor: Executes individual nodes
    """

    def __init__(
        self,
        workflow: WorkflowSchema,
        container: Container,
        settings: Optional[ExecutionSettings] = None,
        initial_variables: Optional[Dict[str, Any]] = None,
        project_context: Optional[Any] = None,
    ) -> None:
        """
        Initialize use case with injected dependencies.

        Args:
            workflow: Workflow to execute
            container: DI container for resolving dependencies
            settings: Execution settings
            initial_variables: Initial variables for context
            project_context: Optional project context
        """
        self.workflow = workflow
        self.settings = settings or ExecutionSettings()
        self._initial_variables = initial_variables or {}
        self._project_context = project_context

        # Resolve dependencies from container
        self._event_bus: IEventBus = container.resolve(IEventBus)
        self._metrics: IMetricsCollector = container.resolve(IMetricsCollector)
        self._context_factory: IExecutionContextFactory = container.resolve(
            IExecutionContextFactory
        )
        self._orchestrator_factory: IOrchestratorFactory = container.resolve(
            IOrchestratorFactory
        )
        self._node_executor: INodeExecutor = container.resolve(INodeExecutor)

        # Create domain orchestrator for this workflow
        self.orchestrator = self._orchestrator_factory.create(workflow)

        # Execution state
        self.context = None
        self.executed_nodes: Set[NodeId] = set()
        self.current_node_id: Optional[NodeId] = None
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self._stop_requested = False

        # Run-To-Node support
        self._target_reached = False
        self._subgraph_nodes: Optional[Set[NodeId]] = None

        if self.settings.target_node_id:
            self._calculate_subgraph()

    def _calculate_subgraph(self) -> None:
        """Calculate subgraph for Run-To-Node execution."""
        if not self.settings.target_node_id:
            return

        start_node_id = self.orchestrator.find_start_node()
        if not start_node_id:
            logger.error("Cannot calculate subgraph: no StartNode found")
            return

        if not self.orchestrator.is_reachable(
            start_node_id, self.settings.target_node_id
        ):
            logger.error(f"Target {self.settings.target_node_id} not reachable")
            return

        self._subgraph_nodes = self.orchestrator.calculate_execution_path(
            start_node_id, self.settings.target_node_id
        )
        logger.info(f"Subgraph: {len(self._subgraph_nodes)} nodes to execute")

    def _emit_event(self, event_type: EventType, data: Dict[str, Any]) -> None:
        """Emit event via injected event bus."""
        event = Event(
            event_type=event_type,
            data=data,
            node_id=self.current_node_id,
        )
        self._event_bus.publish(event)

    def _calculate_progress(self) -> float:
        """Calculate execution progress percentage."""
        total = (
            len(self._subgraph_nodes)
            if self._subgraph_nodes
            else len(self.workflow.nodes)
        )
        if total == 0:
            return 0.0
        return (len(self.executed_nodes) / total) * 100

    def _should_execute_node(self, node_id: NodeId) -> bool:
        """Check if node should be executed based on subgraph."""
        if self._subgraph_nodes is None:
            return True
        return node_id in self._subgraph_nodes

    async def execute(self) -> bool:
        """
        Execute the workflow.

        Returns:
            True if completed successfully, False otherwise
        """
        self.start_time = datetime.now()
        self._stop_requested = False
        self.executed_nodes.clear()

        # Create execution context via factory
        self.context = self._context_factory.create(
            workflow_name=self.workflow.metadata.name,
            initial_variables=self._initial_variables,
            project_context=self._project_context,
        )

        # Record metrics and emit start event
        self._metrics.record_workflow_start(self.workflow.metadata.name)
        self._emit_event(
            EventType.WORKFLOW_STARTED,
            {
                "workflow_name": self.workflow.metadata.name,
                "total_nodes": len(self._subgraph_nodes or self.workflow.nodes),
            },
        )

        logger.info(f"Starting workflow: {self.workflow.metadata.name}")

        try:
            start_node_id = self.orchestrator.find_start_node()
            if not start_node_id:
                raise ValueError("No StartNode found in workflow")

            await self._execute_from_node(start_node_id)

            return self._finalize_execution()

        except Exception as e:
            return self._handle_execution_error(e)

        finally:
            await self._cleanup()

    async def _execute_from_node(self, start_node_id: NodeId) -> None:
        """Execute workflow from a specific node."""
        nodes_to_execute: List[NodeId] = [start_node_id]

        while nodes_to_execute and not self._stop_requested:
            current_node_id = nodes_to_execute.pop(0)

            # Skip if already executed (except loops)
            is_loop = self.orchestrator.is_control_flow_node(current_node_id)
            if current_node_id in self.executed_nodes and not is_loop:
                continue

            # Skip nodes not in subgraph
            if not self._should_execute_node(current_node_id):
                continue

            node = self.workflow.nodes.get(current_node_id)
            if not node:
                continue

            # Transfer data and execute
            self._transfer_data(current_node_id)
            success, result = await self._execute_node(node)

            if not success and not self.settings.continue_on_error:
                break

            # Check target reached
            if success and self.settings.target_node_id == current_node_id:
                self._target_reached = True
                break

            # Queue next nodes
            next_nodes = self.orchestrator.get_next_nodes(current_node_id, result)
            nodes_to_execute.extend(next_nodes)

    async def _execute_node(self, node: Any) -> tuple[bool, Optional[Dict]]:
        """Execute a single node using injected executor."""
        self.current_node_id = node.node_id
        node.status = NodeStatus.RUNNING

        self._emit_event(
            EventType.NODE_STARTED,
            {"node_id": node.node_id, "node_type": node.__class__.__name__},
        )

        import time
        start_time = time.time()
        self._metrics.record_node_start(node.__class__.__name__, node.node_id)

        # Execute via injected executor
        result = await self._node_executor.execute(
            node, self.context, self.settings.node_timeout
        )

        execution_time = time.time() - start_time
        success = result.get("success", False)

        # Update node state and emit events
        node.status = NodeStatus.SUCCESS if success else NodeStatus.ERROR
        if success:
            self.executed_nodes.add(node.node_id)

        event_type = EventType.NODE_COMPLETED if success else EventType.NODE_ERROR
        self._emit_event(event_type, {
            "node_id": node.node_id,
            "execution_time": execution_time,
            "progress": self._calculate_progress(),
            **({"error": result.get("error")} if not success else {}),
        })

        self._metrics.record_node_complete(
            node.__class__.__name__, node.node_id,
            execution_time * 1000, success
        )

        return success, result

    def _transfer_data(self, target_node_id: NodeId) -> None:
        """Transfer data from connected input ports."""
        for conn in self.workflow.connections:
            if conn.target_node == target_node_id:
                source = self.workflow.nodes.get(conn.source_node)
                target = self.workflow.nodes.get(conn.target_node)
                if source and target:
                    value = source.get_output_value(conn.source_port)
                    if value is not None:
                        target.set_input_value(conn.target_port, value)

    def _finalize_execution(self) -> bool:
        """Finalize execution and emit completion events."""
        self.end_time = datetime.now()
        duration = (self.end_time - self.start_time).total_seconds()

        if self._stop_requested:
            self._emit_event(EventType.WORKFLOW_STOPPED, {
                "executed_nodes": len(self.executed_nodes),
            })
            self._metrics.record_workflow_complete(
                self.workflow.metadata.name, duration * 1000, False
            )
            return False

        self._emit_event(EventType.WORKFLOW_COMPLETED, {
            "executed_nodes": len(self.executed_nodes),
            "duration": duration,
        })
        self._metrics.record_workflow_complete(
            self.workflow.metadata.name, duration * 1000, True
        )
        logger.info(f"Workflow completed in {duration:.2f}s")
        return True

    def _handle_execution_error(self, error: Exception) -> bool:
        """Handle execution error."""
        self.end_time = datetime.now()
        duration = (self.end_time - self.start_time).total_seconds()

        self._emit_event(EventType.WORKFLOW_ERROR, {"error": str(error)})
        self._metrics.record_workflow_complete(
            self.workflow.metadata.name, duration * 1000, False
        )
        logger.exception("Workflow execution failed")
        return False

    async def _cleanup(self) -> None:
        """Cleanup execution context."""
        if self.context:
            try:
                await asyncio.wait_for(self.context.cleanup(), timeout=30.0)
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
        self.current_node_id = None

    def stop(self) -> None:
        """Stop workflow execution."""
        self._stop_requested = True
        logger.info("Workflow stop requested")
```

### 6. Application Bootstrap

```python
# src/casare_rpa/application/bootstrap.py
"""
Application Bootstrap Module

Initializes the DI container and wires up all application components.
This is the composition root for the application.
"""

import asyncio
from typing import Optional
from loguru import logger

from .dependency_injection.container import Container
from .dependency_injection.registrations import configure_container
from .dependency_injection.interfaces import IEventBus


# Global container instance (singleton)
_container: Optional[Container] = None


def get_container() -> Container:
    """
    Get the global DI container.

    Creates container if not exists. Thread-safe.

    Returns:
        Configured DI container
    """
    global _container

    if _container is None:
        _container = configure_container()
        logger.info("Global DI container created")

    return _container


async def initialize_application() -> Container:
    """
    Initialize the application with async resources.

    Call this during application startup to:
    1. Create DI container
    2. Initialize async singletons

    Returns:
        Initialized container
    """
    container = get_container()
    await container.initialize_async()

    logger.info("Application initialized successfully")
    return container


async def shutdown_application() -> None:
    """
    Shutdown the application and cleanup resources.

    Call this during application shutdown to:
    1. Cleanup async resources
    2. Close connections
    """
    global _container

    if _container:
        await _container.cleanup_async()
        _container = None
        logger.info("Application shutdown complete")


def reset_container() -> None:
    """
    Reset the global container (for testing).

    Creates a fresh container on next get_container() call.
    """
    global _container
    _container = None


# Convenience function for getting EventBus
def get_event_bus() -> IEventBus:
    """
    Get the global EventBus instance.

    Convenience method for components that only need EventBus.

    Returns:
        EventBus singleton
    """
    return get_container().resolve(IEventBus)
```

---

## Integration Points

### 1. Canvas Entry Point Update

```python
# run.py (UPDATED)
"""
CasareRPA Canvas Entry Point

Updated to use DI container for proper initialization.
"""

import sys
import asyncio
from loguru import logger

# Configure logging first
from casare_rpa.utils.logging_config import configure_logging
configure_logging()


async def main():
    """Main entry point with async initialization."""
    from PySide6.QtWidgets import QApplication
    import qasync

    # Create Qt application
    app = QApplication(sys.argv)

    # Initialize DI container
    from casare_rpa.application.bootstrap import initialize_application
    container = await initialize_application()

    # Create main window with container
    from casare_rpa.canvas.casare_rpa_app import CasareRPAApp
    main_app = CasareRPAApp(container=container)
    main_app.show()

    # Run event loop
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    try:
        with loop:
            loop.run_forever()
    finally:
        # Cleanup on exit
        from casare_rpa.application.bootstrap import shutdown_application
        asyncio.get_event_loop().run_until_complete(shutdown_application())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application interrupted")
```

### 2. Robot Entry Point Update

```python
# src/casare_rpa/robot/tray_icon.py (UPDATED section)

async def run(self):
    """Run the application loop."""
    # Initialize DI container for Robot
    from casare_rpa.application.bootstrap import initialize_application
    self._container = await initialize_application()

    # ... rest of initialization ...

    # Pass container to agent
    self.agent = RobotAgent(container=self._container)
```

### 3. CasareRPAApp Update

```python
# src/casare_rpa/canvas/casare_rpa_app.py (UPDATED constructor)

class CasareRPAApp(QMainWindow):
    """Main application class with DI support."""

    def __init__(
        self,
        container: Optional[Container] = None,
        parent: Optional[QWidget] = None
    ) -> None:
        super().__init__(parent)

        # Store container for dependency resolution
        self._container = container or get_container()

        # Resolve event bus from container
        self._event_bus = self._container.resolve(IEventBus)

        # ... rest of initialization ...
```

---

## Data Contracts

### Service Registration Schema

```python
# Type definitions for registration

@dataclass
class ServiceRegistration:
    """Defines a service registration."""
    interface: Type                    # Protocol/ABC type
    implementation: Type               # Concrete class
    scope: Scope                       # SINGLETON, TRANSIENT, SCOPED
    factory: Optional[Callable] = None # Custom factory if needed
    requires_async_init: bool = False  # Needs async initialization
```

### Configuration Schema (Optional)

```yaml
# config/services.yaml (if external config desired)
services:
  core:
    - interface: IEventBus
      implementation: casare_rpa.core.events.EventBus
      scope: singleton

    - interface: IMetricsCollector
      implementation: casare_rpa.utils.performance.performance_metrics.PerformanceMetrics
      scope: singleton

  factories:
    - interface: IExecutionContextFactory
      implementation: casare_rpa.application.dependency_injection.factories.ExecutionContextFactory
      scope: singleton

  repositories:
    - interface: IWorkflowRepository
      implementation: casare_rpa.infrastructure.persistence.workflow_repository.JsonWorkflowRepository
      scope: singleton
```

---

## Dependencies and Prerequisites

### Integration with Days 1-3 Components

| Day | Component | How Day 4 Uses It |
|-----|-----------|-------------------|
| Day 1 | Domain Entities | Injected into use cases via factories |
| Day 2 | WorkflowRunner Decomposition | Extracted components become injectable services |
| Day 3 | Infrastructure Layer | Repository implementations registered in container |

### Required Before Starting

1. **Day 1 Complete**: Domain entities (`Workflow`, `Node`, `Connection`, `ExecutionState`) must exist
2. **Day 2 Complete**: `ExecutionOrchestrator` must be functional
3. **Day 3 Complete**: Infrastructure persistence must work

### Circular Dependency Resolution

**Potential Issue**: EventBus -> UseCase -> EventBus

**Resolution**:
- EventBus is resolved at use case construction time
- Use cases don't register themselves with EventBus
- UI components subscribe to EventBus, not use cases

```python
# Correct dependency flow (no cycles)
Container
  -> IEventBus (singleton)
  -> IExecutionContextFactory (singleton, no deps)
  -> IOrchestratorFactory (singleton, no deps)
  -> INodeExecutor (transient, no deps)

ExecuteWorkflowUseCase
  <- IEventBus (injected)
  <- IExecutionContextFactory (injected)
  <- IOrchestratorFactory (injected)
  <- INodeExecutor (injected)
```

---

## Success Criteria and Validation

### Unit Test Strategy with DI

```python
# tests/application/test_execute_workflow_di.py
"""Tests for ExecuteWorkflowUseCase with DI."""

import pytest
from unittest.mock import Mock, AsyncMock
from casare_rpa.application.dependency_injection.container import Container, Scope
from casare_rpa.application.use_cases.execute_workflow import (
    ExecuteWorkflowUseCase,
    ExecutionSettings,
)


@pytest.fixture
def mock_container():
    """Create container with mock dependencies."""
    container = Container()

    # Mock EventBus
    mock_event_bus = Mock()
    mock_event_bus.publish = Mock()
    container.register_instance(IEventBus, mock_event_bus)

    # Mock Metrics
    mock_metrics = Mock()
    container.register_instance(IMetricsCollector, mock_metrics)

    # Mock Factories
    mock_context_factory = Mock()
    mock_context_factory.create = Mock(return_value=Mock())
    container.register_instance(IExecutionContextFactory, mock_context_factory)

    mock_orchestrator_factory = Mock()
    container.register_instance(IOrchestratorFactory, mock_orchestrator_factory)

    # Mock Node Executor
    mock_executor = AsyncMock()
    mock_executor.execute = AsyncMock(return_value={"success": True})
    container.register_instance(INodeExecutor, mock_executor)

    return container


@pytest.fixture
def simple_workflow():
    """Create a simple test workflow."""
    from casare_rpa.domain.entities.workflow import WorkflowSchema
    # ... create workflow with Start -> End nodes
    pass


@pytest.mark.asyncio
async def test_use_case_with_injected_dependencies(mock_container, simple_workflow):
    """Test that use case works with injected mock dependencies."""
    use_case = ExecuteWorkflowUseCase(
        workflow=simple_workflow,
        container=mock_container,
    )

    result = await use_case.execute()

    # Verify execution
    assert result is True

    # Verify event bus was called
    mock_event_bus = mock_container.resolve(IEventBus)
    assert mock_event_bus.publish.called


@pytest.mark.asyncio
async def test_container_resolves_all_dependencies(mock_container):
    """Test that container can resolve all required dependencies."""
    from casare_rpa.application.dependency_injection.interfaces import (
        IEventBus,
        IMetricsCollector,
        IExecutionContextFactory,
        IOrchestratorFactory,
        INodeExecutor,
    )

    # All these should resolve without error
    assert mock_container.resolve(IEventBus) is not None
    assert mock_container.resolve(IMetricsCollector) is not None
    assert mock_container.resolve(IExecutionContextFactory) is not None
    assert mock_container.resolve(IOrchestratorFactory) is not None
    assert mock_container.resolve(INodeExecutor) is not None
```

### Integration Test

```python
# tests/integration/test_di_full_workflow.py
"""Integration tests with real container."""

import pytest
from casare_rpa.application.bootstrap import (
    get_container,
    initialize_application,
    shutdown_application,
    reset_container,
)


@pytest.fixture(autouse=True)
async def reset_app():
    """Reset container before each test."""
    reset_container()
    yield
    await shutdown_application()


@pytest.mark.asyncio
async def test_full_workflow_execution_with_di():
    """Test complete workflow execution through DI."""
    # Initialize application
    container = await initialize_application()

    # Create workflow
    workflow = create_test_workflow()

    # Execute via use case
    from casare_rpa.application.use_cases.execute_workflow import (
        ExecuteWorkflowUseCase
    )

    use_case = ExecuteWorkflowUseCase(
        workflow=workflow,
        container=container,
    )

    result = await use_case.execute()

    assert result is True


@pytest.mark.asyncio
async def test_container_lifecycle():
    """Test container initialization and cleanup."""
    container = await initialize_application()

    # Container should be initialized
    assert container._initialized is True

    # Cleanup
    await shutdown_application()

    # Global container should be None
    from casare_rpa.application.bootstrap import _container
    assert _container is None
```

### Performance Benchmark

```python
# tests/performance/test_di_overhead.py
"""Benchmark DI overhead."""

import pytest
import time


@pytest.mark.benchmark
async def test_container_resolution_performance():
    """Test that container resolution is fast."""
    from casare_rpa.application.bootstrap import get_container
    from casare_rpa.application.dependency_injection.interfaces import IEventBus

    container = get_container()

    # Warm up
    container.resolve(IEventBus)

    # Benchmark 1000 resolutions
    start = time.perf_counter()
    for _ in range(1000):
        container.resolve(IEventBus)
    elapsed = time.perf_counter() - start

    # Should be < 10ms for 1000 resolutions
    assert elapsed < 0.010, f"Resolution too slow: {elapsed:.4f}s"


@pytest.mark.benchmark
async def test_workflow_execution_with_di_overhead():
    """Compare execution time with DI vs direct instantiation."""
    # This test compares performance to ensure DI doesn't add
    # significant overhead to workflow execution
    pass
```

### Code Complexity Validation

```bash
# Run complexity analysis
radon cc src/casare_rpa/application/use_cases/execute_workflow.py -s

# Expected output:
# execute_workflow.py
#     ExecuteWorkflowUseCase - A (complexity: 5-10)
#
# Before refactoring: B-C (complexity: 15-25)
# After refactoring: A (complexity: 5-10)
```

---

## Risk Assessment and Mitigation

### Risk 1: Circular Dependencies

**Risk Level**: Medium
**Description**: Services depending on each other creating cycles

**Mitigation**:
- Use factory pattern to delay instantiation
- Define clear dependency graph before implementation
- Use interface segregation to break cycles
- Add validation in container to detect cycles

```python
# Container validation
def validate_no_cycles(self) -> bool:
    """Detect circular dependencies."""
    # Topological sort on dependency graph
    # Raise error if cycle detected
    pass
```

### Risk 2: Performance Overhead

**Risk Level**: Low
**Description**: DI container adds latency to service resolution

**Mitigation**:
- Use singleton scope for expensive services
- Cache resolved instances
- Lazy initialization for rarely-used services
- Benchmark and optimize hot paths

### Risk 3: Configuration Complexity

**Risk Level**: Medium
**Description**: Registration code becomes complex and hard to maintain

**Mitigation**:
- Group registrations by layer (core, factories, repositories)
- Add clear documentation for each registration
- Use convention-based registration where possible
- Keep registration in single file for discoverability

### Risk 4: Backward Compatibility

**Risk Level**: High
**Description**: Breaking existing code that creates use cases directly

**Mitigation**:
- Keep `WorkflowRunner` as compatibility wrapper (already done)
- Add default container resolution if none provided
- Deprecation warnings for direct instantiation
- Migration guide in documentation

```python
# Backward compatibility in ExecuteWorkflowUseCase
def __init__(
    self,
    workflow: WorkflowSchema,
    container: Optional[Container] = None,  # Optional!
    ...
) -> None:
    # Default to global container if not provided
    if container is None:
        from .bootstrap import get_container
        container = get_container()
    ...
```

### Risk 5: Testing Complexity

**Risk Level**: Medium
**Description**: Tests become complex due to DI setup

**Mitigation**:
- Provide `MockContainer` fixture
- Document mock patterns clearly
- Keep mock setup minimal
- Use protocol-based mocking (no inheritance needed)

---

## Implementation Guide for rpa-engine-architect

### Step-by-Step Wiring Sequence

1. **Create Container Module** (Hour 1)
   ```
   Create: src/casare_rpa/application/dependency_injection/container.py
   - Implement Container class
   - Implement ServiceDescriptor
   - Add Scope enum
   - Add lifecycle methods (initialize_async, cleanup_async)
   ```

2. **Create Interface Definitions** (Hour 1)
   ```
   Create: src/casare_rpa/application/dependency_injection/interfaces.py
   - Define all Protocol classes
   - Ensure protocols match existing implementations
   ```

3. **Create Factories** (Hour 2)
   ```
   Create: src/casare_rpa/application/dependency_injection/factories.py
   - ExecutionContextFactory
   - OrchestratorFactory
   - DefaultNodeExecutor
   ```

4. **Create Registrations** (Hour 3)
   ```
   Create: src/casare_rpa/application/dependency_injection/registrations.py
   - register_core_services()
   - register_factories()
   - register_repositories()
   - configure_container()
   ```

5. **Create Bootstrap** (Hour 3)
   ```
   Create: src/casare_rpa/application/bootstrap.py
   - get_container()
   - initialize_application()
   - shutdown_application()
   ```

6. **Refactor ExecuteWorkflowUseCase** (Hour 4-5)
   ```
   Modify: src/casare_rpa/application/use_cases/execute_workflow.py
   - Add container parameter
   - Remove hard-coded imports
   - Resolve dependencies in __init__
   - Simplify execute() method
   ```

7. **Update Entry Points** (Hour 6)
   ```
   Modify: run.py
   - Add async main()
   - Initialize container
   - Pass to CasareRPAApp

   Modify: src/casare_rpa/robot/tray_icon.py
   - Initialize container in run()
   - Pass to RobotAgent
   ```

8. **Create Tests** (Hour 7)
   ```
   Create: tests/application/dependency_injection/test_container.py
   Create: tests/application/dependency_injection/test_registrations.py
   Create: tests/application/test_execute_workflow_di.py
   Create: tests/integration/test_di_full_workflow.py
   ```

9. **Validate and Document** (Hour 8)
   ```
   Run: pytest tests/ -v
   Run: python run.py (verify Canvas loads)
   Update: CLAUDE.md with DI patterns
   ```

### Incremental Refactoring Strategy

**Phase 1: Add DI Without Breaking**
```python
# Add container as optional parameter
def __init__(
    self,
    workflow: WorkflowSchema,
    container: Optional[Container] = None,  # NEW
    event_bus: Optional[EventBus] = None,   # KEEP for now
    ...
):
    # Resolve from container OR use direct parameter
    if container:
        self._event_bus = container.resolve(IEventBus)
    else:
        self._event_bus = event_bus or EventBus()
```

**Phase 2: Deprecate Direct Parameters**
```python
def __init__(
    self,
    workflow: WorkflowSchema,
    container: Optional[Container] = None,
    event_bus: Optional[EventBus] = None,  # DEPRECATED
    ...
):
    if event_bus is not None:
        warnings.warn(
            "event_bus parameter is deprecated. Use container instead.",
            DeprecationWarning
        )
```

**Phase 3: Remove Direct Parameters**
```python
# Final clean implementation
def __init__(
    self,
    workflow: WorkflowSchema,
    container: Container,  # REQUIRED
    settings: Optional[ExecutionSettings] = None,
):
    ...
```

### Rollback Plan

If issues arise, rollback is straightforward:

1. **Container issues**: Revert to direct instantiation in use cases
2. **Performance issues**: Add caching, switch to singleton scope
3. **Test failures**: Use mock container fixture
4. **Canvas won't load**: Check `run.py` bootstrap, ensure async init works

### Testing at Each Step

| Step | Test Command | Expected Result |
|------|--------------|-----------------|
| After Container | `pytest tests/application/dependency_injection/test_container.py` | All pass |
| After Registrations | `pytest tests/application/dependency_injection/` | All pass |
| After UseCase Refactor | `pytest tests/application/test_execute_workflow.py` | All pass |
| After Entry Points | `python run.py` (manual) | Canvas loads |
| Final | `pytest tests/ -v` | 1255+ tests pass |

---

## Safe Failure Considerations

### Error Handling in Container

```python
class Container:
    def resolve(self, service_type: Type[T]) -> T:
        try:
            # Resolution logic
            ...
        except Exception as e:
            logger.error(
                f"Failed to resolve {service_type.__name__}: {e}",
                exc_info=True
            )
            # Re-raise with context
            raise DependencyResolutionError(
                f"Cannot resolve {service_type.__name__}",
                service_type=service_type,
                cause=e
            ) from e
```

### Graceful Degradation

```python
# If DI fails, fall back to direct instantiation
def get_event_bus() -> IEventBus:
    try:
        return get_container().resolve(IEventBus)
    except Exception as e:
        logger.warning(f"DI resolution failed, using fallback: {e}")
        from ..core.events import EventBus
        return EventBus()
```

### Orchestrator Error Propagation

```python
# In ExecuteWorkflowUseCase
async def execute(self) -> bool:
    try:
        ...
    except DependencyResolutionError as e:
        # Log for debugging
        logger.error(f"Dependency resolution failed: {e}")
        # Emit error event so UI knows
        self._emit_event(
            EventType.WORKFLOW_ERROR,
            {
                "error": f"Configuration error: {e}",
                "type": "dependency_error"
            }
        )
        return False
```

---

## Architecture Diagram

```mermaid
graph TB
    subgraph Presentation["Presentation Layer"]
        Canvas[Canvas MainWindow]
        Robot[Robot TrayIcon]
        Orchestrator[Orchestrator]
    end

    subgraph Bootstrap["Bootstrap"]
        Bootstrap[bootstrap.py]
        Container[DI Container]
    end

    subgraph Application["Application Layer"]
        UseCase[ExecuteWorkflowUseCase]
        Registrations[registrations.py]
    end

    subgraph Interfaces["Protocols"]
        IEventBus[IEventBus]
        IMetrics[IMetricsCollector]
        IContextFactory[IExecutionContextFactory]
        IOrchestratorFactory[IOrchestratorFactory]
        INodeExecutor[INodeExecutor]
    end

    subgraph Domain["Domain Layer"]
        Orchestrator_Domain[ExecutionOrchestrator]
        Entities[Domain Entities]
    end

    subgraph Infrastructure["Infrastructure Layer"]
        EventBus[EventBus]
        Metrics[PerformanceMetrics]
        Context[ExecutionContext]
        Repository[WorkflowRepository]
    end

    %% Bootstrap flow
    Canvas --> Bootstrap
    Robot --> Bootstrap
    Orchestrator --> Bootstrap
    Bootstrap --> Container
    Container --> Registrations

    %% Registration binds interfaces to implementations
    Registrations --> IEventBus
    Registrations --> IMetrics
    Registrations --> IContextFactory
    Registrations --> IOrchestratorFactory
    Registrations --> INodeExecutor

    IEventBus -.-> EventBus
    IMetrics -.-> Metrics
    IContextFactory -.-> Context
    IOrchestratorFactory -.-> Orchestrator_Domain

    %% Use case depends on interfaces
    UseCase --> IEventBus
    UseCase --> IMetrics
    UseCase --> IContextFactory
    UseCase --> IOrchestratorFactory
    UseCase --> INodeExecutor

    %% Domain is independent
    Orchestrator_Domain --> Entities

    style Container fill:#f9f,stroke:#333,stroke-width:2px
    style UseCase fill:#bbf,stroke:#333,stroke-width:2px
    style Orchestrator_Domain fill:#bfb,stroke:#333,stroke-width:2px
```

---

## Appendix: File Checklist

### Files to Create (9 files)

- [ ] `src/casare_rpa/application/dependency_injection/__init__.py`
- [ ] `src/casare_rpa/application/dependency_injection/container.py`
- [ ] `src/casare_rpa/application/dependency_injection/interfaces.py`
- [ ] `src/casare_rpa/application/dependency_injection/factories.py`
- [ ] `src/casare_rpa/application/dependency_injection/registrations.py`
- [ ] `src/casare_rpa/application/dependency_injection/scopes.py`
- [ ] `src/casare_rpa/application/bootstrap.py`
- [ ] `tests/application/dependency_injection/test_container.py`
- [ ] `tests/integration/test_di_full_workflow.py`

### Files to Modify (6 files)

- [ ] `src/casare_rpa/application/use_cases/execute_workflow.py`
- [ ] `src/casare_rpa/runner/workflow_runner.py`
- [ ] `src/casare_rpa/canvas/casare_rpa_app.py`
- [ ] `src/casare_rpa/robot/tray_icon.py`
- [ ] `run.py`
- [ ] `CLAUDE.md`

---

## Summary

This implementation plan provides:

1. **Complete DI container implementation** with lifecycle management
2. **Protocol-based interfaces** for all injectable dependencies
3. **Clean refactoring path** for ExecuteWorkflowUseCase
4. **Integration points** for Canvas, Robot, and Orchestrator
5. **Comprehensive testing strategy** with mock fixtures
6. **Risk mitigation** and rollback procedures
7. **Step-by-step implementation guide** with validation at each step

The result will be a maintainable, testable architecture where:
- ExecuteWorkflowUseCase is reduced to ~200 lines
- All dependencies are explicit and injectable
- Testing is simplified with mock containers
- The application follows clean architecture principles
