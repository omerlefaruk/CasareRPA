"""
CasareRPA - Credential Bindings

Credential binding classes for project security management.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from casare_rpa.domain.entities.project.base import PROJECT_SCHEMA_VERSION


@dataclass
class CredentialBinding:
    """
    Maps a local alias to a Vault credential path.

    Domain entity for credential reference management.

    Attributes:
        alias: Local name used in workflows (e.g., "erp_login")
        vault_path: Path in HashiCorp Vault (e.g., "projects/proj_123/erp_creds")
        credential_type: Type of credential (username_password, api_key, etc.)
        description: Description of what this credential is for
        required: If True, workflow execution fails if credential is missing
    """

    alias: str
    vault_path: str
    credential_type: str = "username_password"
    description: str = ""
    required: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "alias": self.alias,
            "vault_path": self.vault_path,
            "credential_type": self.credential_type,
            "description": self.description,
            "required": self.required,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CredentialBinding":
        """Create from dictionary."""
        return cls(
            alias=data.get("alias", ""),
            vault_path=data.get("vault_path", ""),
            credential_type=data.get("credential_type", "username_password"),
            description=data.get("description", ""),
            required=data.get("required", True),
        )


@dataclass
class CredentialBindingsFile:
    """Container for credential bindings in credentials.json files."""

    scope: str = "project"
    bindings: Dict[str, CredentialBinding] = field(default_factory=dict)
    schema_version: str = PROJECT_SCHEMA_VERSION

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "$schema_version": self.schema_version,
            "scope": self.scope,
            "bindings": {
                alias: binding.to_dict() for alias, binding in self.bindings.items()
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CredentialBindingsFile":
        """Create from dictionary."""
        bindings_data = data.get("bindings", {})

        bindings = {
            alias: CredentialBinding.from_dict(binding_data)
            for alias, binding_data in bindings_data.items()
        }

        return cls(
            scope=data.get("scope", "project"),
            bindings=bindings,
            schema_version=data.get("$schema_version", PROJECT_SCHEMA_VERSION),
        )

    def get_binding(self, alias: str) -> Optional[CredentialBinding]:
        """Get binding by alias."""
        return self.bindings.get(alias)

    def set_binding(self, binding: CredentialBinding) -> None:
        """Add or update a binding."""
        self.bindings[binding.alias] = binding

    def remove_binding(self, alias: str) -> bool:
        """Remove a binding. Returns True if removed."""
        if alias in self.bindings:
            del self.bindings[alias]
            return True
        return False

    def resolve_vault_path(self, alias: str) -> Optional[str]:
        """Get the Vault path for an alias."""
        binding = self.bindings.get(alias)
        return binding.vault_path if binding else None
