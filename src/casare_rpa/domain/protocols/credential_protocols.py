"""
Domain Layer Credential Protocols.

This module defines protocols for credential resolution that allow
the domain layer to remain pure (no infrastructure dependencies).

The actual implementations live in the infrastructure layer:
- ExecutionContext: infrastructure.execution.execution_context
- VaultCredentialProvider: infrastructure.security.credential_provider
- ResolvedCredential: infrastructure.security.credential_provider

These protocols follow Dependency Inversion Principle - domain code
depends on abstractions (protocols), not concrete implementations.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional, Protocol, runtime_checkable


@dataclass
class ResolvedCredentialData:
    """
    Domain value object representing resolved credential data.

    This is a pure data container with no infrastructure dependencies.
    The infrastructure layer maps its ResolvedCredential to this type.

    Attributes:
        alias: Credential alias/name used for lookup
        vault_path: Full path in the credential vault
        data: Raw credential data dictionary
        username: Extracted username (if present)
        password: Extracted password (if present)
        api_key: Extracted API key (if present)
        connection_string: Extracted connection string (if present)
        is_dynamic: Whether credential was dynamically generated
        expires_at: Expiration time for dynamic credentials
    """

    alias: str
    vault_path: str
    data: dict[str, Any]
    username: str | None = None
    password: str | None = None
    api_key: str | None = None
    connection_string: str | None = None
    is_dynamic: bool = False
    expires_at: datetime | None = None


@runtime_checkable
class CredentialProviderProtocol(Protocol):
    """
    Protocol defining the interface for credential providers.

    This protocol enables domain code to work with credentials
    without depending on the infrastructure VaultCredentialProvider.

    Infrastructure implementations must provide:
    - get_credential(alias, required) -> ResolvedCredentialData or None
    - get_credential_by_path(path, alias) -> ResolvedCredentialData
    - register_bindings(bindings) -> None
    """

    async def get_credential(
        self,
        alias: str,
        required: bool = True,
    ) -> ResolvedCredentialData | None:
        """
        Get credential by alias.

        Args:
            alias: Credential alias
            required: If True, raises error when not found

        Returns:
            ResolvedCredentialData or None if not required and not found

        Raises:
            SecretNotFoundError: If required and alias not registered
        """
        ...

    async def get_credential_by_path(
        self,
        vault_path: str,
        alias: str | None = None,
    ) -> ResolvedCredentialData:
        """
        Get credential by direct vault path.

        Args:
            vault_path: Full vault path
            alias: Optional alias for reference

        Returns:
            ResolvedCredentialData with all extracted fields
        """
        ...

    def register_bindings(self, bindings: dict[str, str]) -> None:
        """
        Register multiple credential bindings.

        Args:
            bindings: Dictionary mapping alias to vault path
        """
        ...


@runtime_checkable
class ExecutionContextProtocol(Protocol):
    """
    Protocol defining the execution context interface for credential resolution.

    This protocol allows CredentialAwareMixin to work with any execution
    context implementation without importing from infrastructure.

    The infrastructure ExecutionContext implements this protocol.
    """

    @property
    def resources(self) -> dict[str, Any]:
        """Get resources dictionary for storing/retrieving resources."""
        ...

    @property
    def has_project_context(self) -> bool:
        """Check if a project context is available."""
        ...

    @property
    def project_context(self) -> Any | None:
        """Get the project context (if any)."""
        ...

    def resolve_value(self, value: Any) -> Any:
        """
        Resolve {{variable_name}} patterns in a value.

        Args:
            value: The value to resolve (only strings are processed)

        Returns:
            The resolved value with all {{variable}} patterns replaced.
        """
        ...

    def get_variable(self, name: str, default: Any = None) -> Any:
        """
        Get a variable from the context.

        Args:
            name: Variable name
            default: Default value if variable not found

        Returns:
            Variable value or default
        """
        ...


__all__ = [
    "ResolvedCredentialData",
    "CredentialProviderProtocol",
    "ExecutionContextProtocol",
]
