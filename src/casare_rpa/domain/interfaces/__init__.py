"""
Domain Layer Interfaces Package.

This package contains Protocol interfaces for the domain layer
that enable dependency inversion. Infrastructure components
implement these protocols, allowing Application and Domain code
to remain decoupled from Infrastructure.

Entry Points:
    - INode: Protocol for automation nodes (execute, validate, ports)
    - IExecutionContext: Protocol for execution runtime services
    - IExecutionContextFactory: Factory for execution contexts
    - ICacheManager: Protocol for cache invalidation operations
    - ICacheKeyGenerator: Protocol for cache key generation
    - IBrowserRecorder: Protocol for browser recording
    - IBrowserRecorderFactory: Factory for browser recorders
    - IBrowserWorkflowGenerator: Protocol for workflow generation from browser actions
    - IRecoveryStrategyRegistry: Protocol for executing recovery decisions
    - IFolderStorage: Interface for folder storage operations
    - IEnvironmentStorage: Interface for environment storage operations
    - ITemplateStorage: Interface for template storage operations

Usage:
    from casare_rpa.domain.interfaces import INode, IExecutionContext

    async def execute_node(node: INode, context: IExecutionContext) -> ExecutionResult:
        is_valid, error = node.validate()
        if not is_valid:
            return {"success": False, "error": error}
        return await node.execute(context)

Design Pattern: Dependency Inversion Principle
- High-level modules (Application) depend on abstractions (these interfaces)
- Low-level modules (Infrastructure) implement these abstractions
- Both depend on abstractions, not on each other

Related:
    - domain.entities.base_node.BaseNode implements INode
    - infrastructure.execution.ExecutionContext implements IExecutionContext
"""

from casare_rpa.domain.interfaces.browser import (
    IBrowserRecorder,
    IBrowserRecorderFactory,
    IBrowserWorkflowGenerator,
)
from casare_rpa.domain.interfaces.cache import ICacheManager
from casare_rpa.domain.interfaces.cache_keys import ICacheKeyGenerator
from casare_rpa.domain.interfaces.execution_context import IExecutionContext
from casare_rpa.domain.interfaces.execution_context_factory import IExecutionContextFactory
from casare_rpa.domain.interfaces.llm import ILLMManager, ILLMResponse
from casare_rpa.domain.interfaces.node import INode
from casare_rpa.domain.interfaces.node_manifest import INodeManifestProvider
from casare_rpa.domain.interfaces.recovery import IRecoveryStrategyRegistry
from casare_rpa.domain.interfaces.repositories import (
    IEnvironmentStorage,
    IFolderStorage,
    ITemplateStorage,
)
from casare_rpa.domain.interfaces.unit_of_work import AbstractUnitOfWork

__all__ = [
    # Core Protocols
    "INode",
    "IExecutionContext",
    "IExecutionContextFactory",
    "ICacheManager",
    "ICacheKeyGenerator",
    "IBrowserRecorder",
    "IBrowserRecorderFactory",
    "IBrowserWorkflowGenerator",
    "IRecoveryStrategyRegistry",
    "ILLMManager",
    "ILLMResponse",
    "INodeManifestProvider",
    # Storage/Repositories
    "IFolderStorage",
    "IEnvironmentStorage",
    "ITemplateStorage",
    # Unit of Work
    "AbstractUnitOfWork",
]
