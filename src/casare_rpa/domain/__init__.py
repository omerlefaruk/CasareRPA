"""
CasareRPA Domain Layer - Pure Business Logic

This layer contains:
- Entities: Core business objects (Workflow, Node, Connection)
- Services: Domain services (validation, dependency analysis)
- Ports: Interfaces for adapters (dependency inversion)
- Protocols: Protocol interfaces for dependency inversion
- Decorators: Node class decorators (executable_node)
- Credentials: Credential resolution for nodes (CredentialAwareMixin)

CRITICAL: This layer must have ZERO dependencies on infrastructure or presentation.
All domain logic should be framework-agnostic and testable in isolation.
"""

from casare_rpa.domain.decorators import executable_node
from casare_rpa.domain.credentials import (
    CredentialAwareMixin,
    CREDENTIAL_NAME_PROP,
    API_KEY_PROP,
    USERNAME_PROP,
    PASSWORD_PROP,
    BOT_TOKEN_PROP,
    resolve_node_credential,
)
from casare_rpa.domain.protocols import (
    CredentialProviderProtocol,
    ExecutionContextProtocol,
    ResolvedCredentialData,
)

__all__ = [
    # Decorators
    "executable_node",
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
