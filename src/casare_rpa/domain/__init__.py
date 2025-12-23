"""
CasareRPA - Domain Layer

Core business logic with zero external dependencies.

Entry Points:
    - entities.base_node.BaseNode: Base class for all automation nodes
    - entities.workflow.WorkflowSchema: Workflow definition and validation
    - protocols.ExecutionContextProtocol: Execution context interface
    - protocols.CredentialProviderProtocol: Credential resolution interface
    - decorators.node: Decorator to register node classes
    - decorators.properties: Decorator for property schemas
    - credentials.CredentialAwareMixin: Mixin for credential-aware nodes
    - value_objects.types: DataType, NodeStatus, PortDefinition

Key Patterns:
    - DDD Entities: Workflow, Node, Connection with identity and lifecycle
    - Value Objects: Immutable types for DataType, PortDefinition, NodeStatus
    - Protocols: Interface contracts for dependency inversion (no concrete implementations)
    - Domain Services: Validation, dependency analysis, port type system
    - Pure Functions: All logic is side-effect free and testable in isolation

Related:
    - Application layer: Orchestrates domain operations via use cases
    - Infrastructure layer: Implements domain protocols (credential providers, persistence)
    - Presentation layer: Uses domain entities through application services
    - Nodes package: Implements BaseNode protocol for automation actions

CRITICAL: This layer must have ZERO dependencies on infrastructure or presentation.
All domain logic should be framework-agnostic and testable in isolation.
"""

from casare_rpa.domain.credentials import (
    API_KEY_PROP,
    BOT_TOKEN_PROP,
    CREDENTIAL_NAME_PROP,
    PASSWORD_PROP,
    USERNAME_PROP,
    CredentialAwareMixin,
    resolve_node_credential,
)
from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.protocols import (
    CredentialProviderProtocol,
    ExecutionContextProtocol,
    ResolvedCredentialData,
)

__all__ = [
    # Decorators
    "node",
    "properties",
    # Credential mixin and props
    "CredentialAwareMixin",
    "CREDENTIAL_NAME_PROP",
    "API_KEY_PROP",
    "USERNAME_PROP",
    "PASSWORD_PROP",
    "BOT_TOKEN_PROP",
    "resolve_node_credential",
    # Protocols for dependency inversion
    "CredentialProviderProtocol",
    "ExecutionContextProtocol",
    "ResolvedCredentialData",
]
