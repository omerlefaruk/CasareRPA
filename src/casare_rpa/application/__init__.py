"""
CasareRPA - Application Layer

Use cases, orchestration services, and application-specific business rules.

Entry Points:
    - use_cases.execute_workflow.ExecuteWorkflow: Main workflow execution use case
    - use_cases.node_executor.NodeExecutor: Individual node execution orchestration
    - use_cases.variable_resolver.VariableResolver: Variable interpolation service
    - orchestrator.services.job_lifecycle_service: Job state management
    - services.event_bus.EventBus: Decoupled event communication

Key Patterns:
    - Use Cases: Single-responsibility operations (Execute, Validate, Transform)
    - Application Services: Cross-cutting concerns (logging, retry, event bus)
    - Dependency Injection: Services receive dependencies via constructor
    - Async-First: All workflow execution is asynchronous
    - Event-Driven: EventBus for decoupled communication between components

Related:
    - Domain layer: Provides entities, value objects, and protocols
    - Infrastructure layer: Provides concrete implementations (DB, file, network)
    - Presentation layer: Invokes use cases via controllers
    - Nodes package: Nodes are executed by NodeExecutor use case

Depends on: Domain layer
Independent of: Infrastructure implementation details, Presentation
"""

__all__ = []
