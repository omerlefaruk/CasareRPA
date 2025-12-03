"""
Domain Layer Protocols Package.

This package contains Protocol interfaces for the domain layer
that enable dependency inversion. Infrastructure components
implement these protocols, allowing domain code to remain pure.

Available protocols:
- CredentialProviderProtocol: Interface for credential vault providers
- ExecutionContextProtocol: Interface for execution context
- ResolvedCredentialData: Value object for resolved credentials
"""

from casare_rpa.domain.protocols.credential_protocols import (
    CredentialProviderProtocol,
    ExecutionContextProtocol,
    ResolvedCredentialData,
)

__all__ = [
    "CredentialProviderProtocol",
    "ExecutionContextProtocol",
    "ResolvedCredentialData",
]
