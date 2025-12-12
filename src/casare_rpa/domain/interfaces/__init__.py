"""
Domain Layer Interfaces Package.

This package contains Protocol interfaces for the domain layer
that enable dependency inversion. Infrastructure components
implement these protocols, allowing Application and Domain code
to remain decoupled from Infrastructure.

Entry Points:
    - INode: Protocol for automation nodes (execute, validate, ports)
    - IExecutionContext: Protocol for execution runtime services
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

from casare_rpa.domain.interfaces.execution_context import IExecutionContext
from casare_rpa.domain.interfaces.node import INode
from casare_rpa.domain.interfaces.repositories import (
    IFolderStorage,
    IEnvironmentStorage,
    ITemplateStorage,
)
from casare_rpa.domain.interfaces.unit_of_work import AbstractUnitOfWork

__all__ = [
    # Core Protocols
    "INode",
    "IExecutionContext",
    # Storage/Repositories
    "IFolderStorage",
    "IEnvironmentStorage",
    "ITemplateStorage",
    # Unit of Work
    "AbstractUnitOfWork",
]
