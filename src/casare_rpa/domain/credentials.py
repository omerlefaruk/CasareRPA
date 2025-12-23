"""
CasareRPA - Node Credential System

Provides standardized credential resolution for nodes.
Integrates with Vault via `CredentialProviderProtocol`.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Protocol, cast

# Import definitions to re-export them (backward compatibility)
from casare_rpa.domain.credential_definitions import (
    API_KEY_PROP,
    BEARER_TOKEN_PROP,
    BOT_TOKEN_PROP,
    CLIENT_ID_PROP,
    CLIENT_SECRET_PROP,
    CONNECTION_STRING_PROP,
    CREDENTIAL_NAME_PROP,
    IMAP_PORT_PROP,
    IMAP_SERVER_PROP,
    OAUTH_TOKEN_PROP,
    PASSWORD_PROP,
    SMTP_PORT_PROP,
    SMTP_SERVER_PROP,
    USERNAME_PROP,
)
from casare_rpa.domain.protocols.credential_protocols import (
    CredentialProviderProtocol,
    ExecutionContextProtocol,
    ResolvedCredentialData,
)

logger = logging.getLogger(__name__)


class HasGetParameter(Protocol):
    """Protocol for objects with `get_parameter` (e.g. BaseNode)."""

    def get_parameter(self, name: str, default: Any = None) -> Any: ...


class CredentialAwareMixin:
    """Mixin for nodes needing credential resolution (Vault > Param > Env)."""

    async def resolve_credential(
        self,
        context: ExecutionContextProtocol,
        credential_name_param: str = "credential_name",
        direct_param: str | None = None,
        env_var: str | None = None,
        context_var: str | None = None,
        credential_field: str = "api_key",
        required: bool = False,
    ) -> str | None:
        """Resolves credential from Vault > Direct Param > Context > EnvVar.

        Args:
            context: Provider for vault access and variables.
            credential_field: Field to extract from vault (e.g. 'api_key', 'password').
            required: If True, raises ValueError on failure.
        """
        # 1. Vault
        cred_name = self.get_parameter(credential_name_param, "")
        if cred_name:
            cred_name = context.resolve_value(cred_name)
            if cred_name:
                resolved = await self._get_from_vault(context, cred_name, credential_field)
                if resolved:
                    return resolved

        # 2. Direct Param
        if direct_param:
            value = self.get_parameter(direct_param, "")
            if value:
                resolved = context.resolve_value(value)
                if resolved:
                    return str(resolved)

        # 3. Context Variable
        if context_var:
            value = context.get_variable(context_var)
            if value:
                return str(value)

        # 4. Environment
        if env_var:
            value = os.environ.get(env_var)
            if value:
                return value

        if required:
            raise ValueError(
                f"Required credential '{credential_field}' not found via "
                f"vault('{credential_name_param}'), param('{direct_param}'), "
                f"ctx('{context_var}'), or env('{env_var}')"
            )

        return None

    async def resolve_username_password(
        self,
        context: ExecutionContextProtocol,
        credential_name_param: str = "credential_name",
        username_param: str = "username",
        password_param: str = "password",
        env_prefix: str | None = None,
        required: bool = False,
    ) -> tuple[str | None, str | None]:
        """Resolves (username, password) tuple from Vault > Params > Env.

        Args:
            env_prefix: Prefix for env vars (e.g. 'SMTP' -> SMTP_USERNAME).
        """
        username, password = None, None

        # 1. Vault
        cred_name = self.get_parameter(credential_name_param, "")
        if cred_name:
            cred_name = context.resolve_value(cred_name)
            if cred_name:
                cred = await self._get_full_credential(context, cred_name)
                if cred and cred.username and cred.password:
                    return cred.username, cred.password

        # 2. params
        u_val = self.get_parameter(username_param, "")
        p_val = self.get_parameter(password_param, "")
        if u_val:
            username = context.resolve_value(u_val)
        if p_val:
            password = context.resolve_value(p_val)

        if username and password:
            return str(username), str(password)

        # 3. Env
        if env_prefix:
            username = username or os.environ.get(f"{env_prefix}_USERNAME")
            password = password or os.environ.get(f"{env_prefix}_PASSWORD")

        if required and (not username or not password):
            raise ValueError(f"Required username/password not found (prefix: {env_prefix})")

        return username, password

    async def resolve_oauth_credentials(
        self,
        context: ExecutionContextProtocol,
        credential_name_param: str = "credential_name",
        client_id_param: str = "client_id",
        client_secret_param: str = "client_secret",
        env_prefix: str | None = None,
        required: bool = False,
    ) -> tuple[str | None, str | None]:
        """Resolves (client_id, client_secret) from Vault > Params > Env."""
        cid, secret = None, None

        # 1. Vault
        cred_name = self.get_parameter(credential_name_param, "")
        if cred_name:
            cred_name = context.resolve_value(cred_name)
            if cred_name:
                cred = await self._get_full_credential(context, cred_name)
                if cred and cred.data:
                    cid = cred.data.get("client_id")
                    secret = cred.data.get("client_secret")
                    if cid:
                        return cid, secret

        # 2. Params
        c_val = self.get_parameter(client_id_param, "")
        s_val = self.get_parameter(client_secret_param, "")
        if c_val:
            cid = context.resolve_value(c_val)
        if s_val:
            secret = context.resolve_value(s_val)

        if cid:
            return str(cid), str(secret)

        # 3. Env
        if env_prefix:
            cid = cid or os.environ.get(f"{env_prefix}_CLIENT_ID")
            secret = secret or os.environ.get(f"{env_prefix}_CLIENT_SECRET")

        if required and not cid:
            raise ValueError(f"Required OAuth credentials not found (prefix: {env_prefix})")

        return cid, secret

    async def _get_from_vault(
        self,
        context: ExecutionContextProtocol,
        credential_name: str,
        field: str,
    ) -> str | None:
        """Extracts specific field from vault credential."""
        cred = await self._get_full_credential(context, credential_name)
        if not cred:
            return None

        # Normalized mapping
        if field == "token" and (cred.api_key or cred.password):
            return cred.api_key or cred.password

        # Direct attributes
        val = getattr(cred, field, None)
        if val:
            return str(val)

        # Data dict
        if cred.data and field in cred.data:
            return str(cred.data[field])

        return None

    async def _get_full_credential(
        self,
        context: ExecutionContextProtocol,
        credential_name: str,
    ) -> ResolvedCredentialData | None:
        """Retrieves full credential object from provider."""
        try:
            provider = await _get_provider(context)
            if not provider:
                return None

            # Try by alias
            try:
                return await provider.get_credential(credential_name, required=False)
            except Exception:
                pass

            # Try by path
            if "/" in credential_name:
                try:
                    return await provider.get_credential_by_path(credential_name)
                except Exception:
                    pass

            return None
        except Exception as e:
            logger.warning(f"Vault resolution error: {e}")
            return None

    # Protocol Stub - MUST delegate to base class via super()
    # This stub is for type checkers but MUST NOT shadow BaseNode.get_parameter!
    # Using NotImplementedError ensures we detect if MRO is wrong
    def get_parameter(self, name: str, default: Any = None) -> Any:
        """Delegate to actual implementation in Host Node (BaseNode)."""
        # Use super() to call the next class in MRO (BaseNode.get_parameter)
        return super().get_parameter(name, default)  # type: ignore[misc]


async def resolve_node_credential(
    context: ExecutionContextProtocol,
    node: Any,
    credential_name_param: str = "credential_name",
    direct_param: str | None = None,
    env_var: str | None = None,
    credential_field: str = "api_key",
    required: bool = False,
) -> str | None:
    """Standalone credential resolution (Functional)."""
    # 1. Vault
    cred_name = node.get_parameter(credential_name_param, "")
    if cred_name:
        cred_name = context.resolve_value(cred_name)
        if cred_name:
            provider = await _get_provider(context)
            if provider:
                try:
                    cred = await provider.get_credential(cred_name, required=False)
                    if cred:
                        val = getattr(cred, credential_field, None)
                        if val:
                            return str(val)
                        if cred.data and credential_field in cred.data:
                            return str(cred.data[credential_field])
                except Exception:
                    pass

    # 2. Param
    if direct_param:
        val = node.get_parameter(direct_param, "")
        if val:
            resolved = context.resolve_value(val)
            if resolved:
                return str(resolved)

    # 3. Env
    if env_var:
        val = os.environ.get(env_var)
        if val:
            return val

    if required:
        raise ValueError(f"Required credential '{credential_field}' not found")

    return None


async def _get_provider(
    context: ExecutionContextProtocol,
) -> CredentialProviderProtocol | None:
    """Locates CredentialProvider in Context (Attr -> Resource)."""
    if hasattr(context, "_credential_provider"):
        p = getattr(context, "_credential_provider", None)
        if p:
            return cast(CredentialProviderProtocol, p)

    if hasattr(context, "resources") and "credential_provider" in context.resources:
        return cast(CredentialProviderProtocol, context.resources["credential_provider"])

    return None


__all__ = [
    "CredentialAwareMixin",
    "resolve_node_credential",
    # Re-exported definitions
    "CREDENTIAL_NAME_PROP",
    "API_KEY_PROP",
    "OAUTH_TOKEN_PROP",
    "USERNAME_PROP",
    "PASSWORD_PROP",
    "CONNECTION_STRING_PROP",
    "BOT_TOKEN_PROP",
    "CLIENT_ID_PROP",
    "CLIENT_SECRET_PROP",
    "BEARER_TOKEN_PROP",
    "SMTP_SERVER_PROP",
    "SMTP_PORT_PROP",
    "IMAP_SERVER_PROP",
    "IMAP_PORT_PROP",
]
