"""
CasareRPA - Node Credential System

Provides standardized credential resolution for nodes that require authentication.
Integrates with VaultCredentialProvider for enterprise credential management.

Design:
- CredentialAwareMixin: Mixin for nodes that need credential resolution
- Standard PropertyDef constants for common credential types
- Fallback hierarchy: vault → project binding → direct parameter → environment

Usage:
    from casare_rpa.domain.credentials import (
        CredentialAwareMixin,
        CREDENTIAL_NAME_PROP,
        API_KEY_PROP,
    )

    @node_schema(
        CREDENTIAL_NAME_PROP,
        API_KEY_PROP,
        ...
    )
    @executable_node
    class MyApiNode(CredentialAwareMixin, BaseNode):
        async def execute(self, context: ExecutionContext) -> ExecutionResult:
            # Get API key with automatic vault resolution
            api_key = await self.resolve_credential(
                context,
                credential_name_param="credential_name",
                direct_param="api_key",
                env_var="MY_API_KEY",
                credential_field="api_key",
            )
"""

from __future__ import annotations

import os
from typing import Any, Optional, TYPE_CHECKING

from loguru import logger

from casare_rpa.domain.schemas import PropertyDef, PropertyType

if TYPE_CHECKING:
    from casare_rpa.infrastructure.execution import ExecutionContext
    from casare_rpa.infrastructure.security.credential_provider import (
        ResolvedCredential,
        VaultCredentialProvider,
    )


# =============================================================================
# STANDARD CREDENTIAL PROPERTY DEFINITIONS
# =============================================================================

# Generic credential name (for vault lookup)
CREDENTIAL_NAME_PROP = PropertyDef(
    "credential_name",
    PropertyType.STRING,
    default="",
    label="Credential Name",
    placeholder="my_credential",
    tooltip="Name of stored credential in vault (alternative to direct credentials)",
    tab="connection",
)

# API Key (for REST APIs, LLM providers, etc.)
API_KEY_PROP = PropertyDef(
    "api_key",
    PropertyType.STRING,
    default="",
    label="API Key",
    placeholder="sk-...",
    tooltip="API key (or use Credential Name for vault lookup)",
    tab="connection",
)

# OAuth Token
OAUTH_TOKEN_PROP = PropertyDef(
    "oauth_token",
    PropertyType.STRING,
    default="",
    label="OAuth Token",
    placeholder="ya29.a0...",
    tooltip="OAuth access token (or use Credential Name for vault lookup)",
    tab="connection",
)

# Username/Password pair
USERNAME_PROP = PropertyDef(
    "username",
    PropertyType.STRING,
    default="",
    label="Username",
    tooltip="Username (or use Credential Name for vault lookup)",
    tab="connection",
)

PASSWORD_PROP = PropertyDef(
    "password",
    PropertyType.STRING,
    default="",
    label="Password",
    tooltip="Password (or use Credential Name for vault lookup)",
    tab="connection",
)

# Database connection string
CONNECTION_STRING_PROP = PropertyDef(
    "connection_string",
    PropertyType.STRING,
    default="",
    label="Connection String",
    placeholder="postgresql://user:pass@host:5432/db",
    tooltip="Database connection string (or use Credential Name for vault lookup)",
    tab="connection",
)

# Bot Token (for messaging platforms)
BOT_TOKEN_PROP = PropertyDef(
    "bot_token",
    PropertyType.STRING,
    default="",
    label="Bot Token",
    tooltip="Bot/API token (or use Credential Name for vault lookup)",
    tab="connection",
)

# Client ID/Secret pair (for OAuth apps)
CLIENT_ID_PROP = PropertyDef(
    "client_id",
    PropertyType.STRING,
    default="",
    label="Client ID",
    tooltip="OAuth Client ID (or use Credential Name for vault lookup)",
    tab="connection",
)

CLIENT_SECRET_PROP = PropertyDef(
    "client_secret",
    PropertyType.STRING,
    default="",
    label="Client Secret",
    tooltip="OAuth Client Secret (or use Credential Name for vault lookup)",
    tab="connection",
)

# Bearer Token
BEARER_TOKEN_PROP = PropertyDef(
    "bearer_token",
    PropertyType.STRING,
    default="",
    label="Bearer Token",
    tooltip="Bearer authentication token (or use Credential Name for vault lookup)",
    tab="connection",
)

# SMTP/IMAP Server credentials
SMTP_SERVER_PROP = PropertyDef(
    "smtp_server",
    PropertyType.STRING,
    default="smtp.gmail.com",
    label="SMTP Server",
    tooltip="SMTP server hostname",
    tab="connection",
)

SMTP_PORT_PROP = PropertyDef(
    "smtp_port",
    PropertyType.INTEGER,
    default=587,
    label="SMTP Port",
    tooltip="SMTP server port (587 for TLS, 465 for SSL)",
    tab="connection",
)

IMAP_SERVER_PROP = PropertyDef(
    "imap_server",
    PropertyType.STRING,
    default="imap.gmail.com",
    label="IMAP Server",
    tooltip="IMAP server hostname",
    tab="connection",
)

IMAP_PORT_PROP = PropertyDef(
    "imap_port",
    PropertyType.INTEGER,
    default=993,
    label="IMAP Port",
    tooltip="IMAP server port (usually 993 for SSL)",
    tab="connection",
)


# =============================================================================
# CREDENTIAL RESOLUTION MIXIN
# =============================================================================


class CredentialAwareMixin:
    """
    Mixin for nodes that require credential resolution.

    Provides a standardized way to resolve credentials from multiple sources:
    1. Vault (via credential_name parameter)
    2. Project bindings (via project context)
    3. Direct parameter (e.g., api_key, password)
    4. Environment variable
    5. Context variable

    Usage:
        class MyNode(CredentialAwareMixin, BaseNode):
            async def execute(self, context):
                api_key = await self.resolve_credential(
                    context,
                    credential_name_param="credential_name",
                    direct_param="api_key",
                    env_var="MY_API_KEY",
                    credential_field="api_key",
                )
    """

    async def resolve_credential(
        self,
        context: "ExecutionContext",
        credential_name_param: str = "credential_name",
        direct_param: Optional[str] = None,
        env_var: Optional[str] = None,
        context_var: Optional[str] = None,
        credential_field: str = "api_key",
        required: bool = False,
    ) -> Optional[str]:
        """
        Resolve a credential value from multiple sources.

        Resolution order:
        1. Vault lookup (if credential_name is set)
        2. Direct parameter value
        3. Context variable
        4. Environment variable

        Args:
            context: ExecutionContext with credential provider
            credential_name_param: Parameter name for credential alias
            direct_param: Parameter name for direct credential value
            env_var: Environment variable name fallback
            context_var: Context variable name fallback
            credential_field: Field to extract from vault credential
                             (api_key, password, username, connection_string)
            required: If True, raises error when credential not found

        Returns:
            Credential value or None if not found and not required

        Raises:
            ValueError: If required=True and credential not found
        """
        # 1. Try vault lookup via credential_name
        cred_name = self.get_parameter(credential_name_param, "")  # type: ignore
        if cred_name:
            cred_name = context.resolve_value(cred_name)
            if cred_name:
                resolved = await self._get_from_vault(
                    context, cred_name, credential_field
                )
                if resolved:
                    logger.debug(f"Resolved {credential_field} from vault: {cred_name}")
                    return resolved

        # 2. Try direct parameter
        if direct_param:
            value = self.get_parameter(direct_param, "")  # type: ignore
            if value:
                value = context.resolve_value(value)
                if value:
                    logger.debug(f"Using direct parameter: {direct_param}")
                    return value

        # 3. Try context variable
        if context_var:
            value = context.get_variable(context_var)
            if value:
                logger.debug(f"Using context variable: {context_var}")
                return str(value)

        # 4. Try environment variable
        if env_var:
            value = os.environ.get(env_var)
            if value:
                logger.debug(f"Using environment variable: {env_var}")
                return value

        # Not found
        if required:
            sources = []
            if credential_name_param:
                sources.append(f"credential_name='{credential_name_param}'")
            if direct_param:
                sources.append(f"parameter='{direct_param}'")
            if context_var:
                sources.append(f"context_var='{context_var}'")
            if env_var:
                sources.append(f"env='{env_var}'")
            raise ValueError(
                f"Required credential not found. Tried: {', '.join(sources)}"
            )

        return None

    async def resolve_username_password(
        self,
        context: "ExecutionContext",
        credential_name_param: str = "credential_name",
        username_param: str = "username",
        password_param: str = "password",
        env_prefix: Optional[str] = None,
        required: bool = False,
    ) -> tuple[Optional[str], Optional[str]]:
        """
        Resolve username and password credentials.

        Args:
            context: ExecutionContext
            credential_name_param: Parameter for credential alias
            username_param: Parameter for direct username
            password_param: Parameter for direct password
            env_prefix: Environment variable prefix (e.g., "SMTP" -> SMTP_USERNAME, SMTP_PASSWORD)
            required: If True, raises error when credentials not found

        Returns:
            Tuple of (username, password)
        """
        username = None
        password = None

        # 1. Try vault lookup
        cred_name = self.get_parameter(credential_name_param, "")  # type: ignore
        if cred_name:
            cred_name = context.resolve_value(cred_name)
            if cred_name:
                cred = await self._get_full_credential(context, cred_name)
                if cred:
                    username = cred.username
                    password = cred.password
                    if username and password:
                        logger.debug(
                            f"Resolved username/password from vault: {cred_name}"
                        )
                        return username, password

        # 2. Try direct parameters
        username = self.get_parameter(username_param, "")  # type: ignore
        password = self.get_parameter(password_param, "")  # type: ignore

        if username:
            username = context.resolve_value(username)
        if password:
            password = context.resolve_value(password)

        if username and password:
            logger.debug("Using direct username/password parameters")
            return username, password

        # 3. Try environment variables
        if env_prefix:
            username = username or os.environ.get(f"{env_prefix}_USERNAME")
            password = password or os.environ.get(f"{env_prefix}_PASSWORD")

            if username and password:
                logger.debug(f"Using {env_prefix}_* environment variables")
                return username, password

        if required and (not username or not password):
            raise ValueError(
                f"Required username/password not found. "
                f"Set credential_name='{credential_name_param}' or "
                f"provide {username_param}/{password_param} parameters"
            )

        return username, password

    async def resolve_oauth_credentials(
        self,
        context: "ExecutionContext",
        credential_name_param: str = "credential_name",
        client_id_param: str = "client_id",
        client_secret_param: str = "client_secret",
        env_prefix: Optional[str] = None,
        required: bool = False,
    ) -> tuple[Optional[str], Optional[str]]:
        """
        Resolve OAuth client credentials (client_id, client_secret).

        Args:
            context: ExecutionContext
            credential_name_param: Parameter for credential alias
            client_id_param: Parameter for direct client ID
            client_secret_param: Parameter for direct client secret
            env_prefix: Environment variable prefix (e.g., "OAUTH" -> OAUTH_CLIENT_ID)
            required: If True, raises error when credentials not found

        Returns:
            Tuple of (client_id, client_secret)
        """
        client_id = None
        client_secret = None

        # 1. Try vault lookup
        cred_name = self.get_parameter(credential_name_param, "")  # type: ignore
        if cred_name:
            cred_name = context.resolve_value(cred_name)
            if cred_name:
                cred = await self._get_full_credential(context, cred_name)
                if cred and cred.data:
                    client_id = cred.data.get("client_id")
                    client_secret = cred.data.get("client_secret")
                    if client_id:
                        logger.debug(
                            f"Resolved OAuth credentials from vault: {cred_name}"
                        )
                        return client_id, client_secret

        # 2. Try direct parameters
        client_id = self.get_parameter(client_id_param, "")  # type: ignore
        client_secret = self.get_parameter(client_secret_param, "")  # type: ignore

        if client_id:
            client_id = context.resolve_value(client_id)
        if client_secret:
            client_secret = context.resolve_value(client_secret)

        if client_id:
            logger.debug("Using direct OAuth parameters")
            return client_id, client_secret

        # 3. Try environment variables
        if env_prefix:
            client_id = client_id or os.environ.get(f"{env_prefix}_CLIENT_ID")
            client_secret = client_secret or os.environ.get(
                f"{env_prefix}_CLIENT_SECRET"
            )

            if client_id:
                logger.debug(f"Using {env_prefix}_* environment variables")
                return client_id, client_secret

        if required and not client_id:
            raise ValueError(
                f"Required OAuth credentials not found. "
                f"Set credential_name='{credential_name_param}' or "
                f"provide {client_id_param} parameter"
            )

        return client_id, client_secret

    async def _get_from_vault(
        self,
        context: "ExecutionContext",
        credential_name: str,
        field: str,
    ) -> Optional[str]:
        """
        Get a specific field from a vault credential.

        Args:
            context: ExecutionContext with credential provider
            credential_name: Credential alias or vault path
            field: Field to extract (api_key, password, username, etc.)

        Returns:
            Field value or None
        """
        cred = await self._get_full_credential(context, credential_name)
        if not cred:
            return None

        # Map field names to credential attributes
        field_map = {
            "api_key": cred.api_key,
            "password": cred.password,
            "username": cred.username,
            "connection_string": cred.connection_string,
            "token": cred.api_key or cred.password,  # Token fallback
            "bot_token": cred.api_key or cred.data.get("bot_token"),
        }

        # Try direct field
        if field in field_map:
            return field_map[field]

        # Try from data dict
        if cred.data and field in cred.data:
            return str(cred.data[field])

        return None

    async def _get_full_credential(
        self,
        context: "ExecutionContext",
        credential_name: str,
    ) -> Optional["ResolvedCredential"]:
        """
        Get full resolved credential from vault.

        Args:
            context: ExecutionContext
            credential_name: Credential alias or vault path

        Returns:
            ResolvedCredential or None
        """
        try:
            # Get credential provider from context
            provider = await self._get_credential_provider(context)
            if not provider:
                logger.debug("No credential provider available")
                return None

            # Try to resolve via alias first
            try:
                return await provider.get_credential(credential_name, required=False)
            except Exception:
                pass

            # Try direct vault path
            if "/" in credential_name:
                try:
                    return await provider.get_credential_by_path(credential_name)
                except Exception:
                    pass

            return None

        except Exception as e:
            logger.warning(f"Failed to resolve credential '{credential_name}': {e}")
            return None

    async def _get_credential_provider(
        self, context: "ExecutionContext"
    ) -> Optional["VaultCredentialProvider"]:
        """
        Get credential provider from context.

        Lazily initializes provider if not present.
        """
        # Check if provider exists in context
        if hasattr(context, "_credential_provider") and context._credential_provider:
            return context._credential_provider

        # Try to get from context resources
        if hasattr(context, "resources") and "credential_provider" in context.resources:
            return context.resources["credential_provider"]

        # Try to create provider
        try:
            from casare_rpa.infrastructure.security.credential_provider import (
                VaultCredentialProvider,
            )

            provider = VaultCredentialProvider()
            await provider.initialize()

            # Register project bindings if available
            if context.has_project_context and context.project_context:
                bindings = context.project_context.get_credential_bindings()
                if bindings:
                    provider.register_bindings(bindings)

            # Store in context for reuse
            if hasattr(context, "resources"):
                context.resources["credential_provider"] = provider

            return provider

        except Exception as e:
            logger.debug(f"Could not create credential provider: {e}")
            return None


# =============================================================================
# CONVENIENCE FUNCTION FOR NON-MIXIN USAGE
# =============================================================================


async def resolve_node_credential(
    context: "ExecutionContext",
    node: Any,
    credential_name_param: str = "credential_name",
    direct_param: Optional[str] = None,
    env_var: Optional[str] = None,
    credential_field: str = "api_key",
    required: bool = False,
) -> Optional[str]:
    """
    Standalone credential resolution function.

    For nodes that don't use the mixin pattern.

    Args:
        context: ExecutionContext
        node: Node instance (must have get_parameter method)
        credential_name_param: Parameter name for credential alias
        direct_param: Parameter name for direct credential value
        env_var: Environment variable fallback
        credential_field: Field to extract from vault credential
        required: If True, raises error when not found

    Returns:
        Credential value or None
    """
    # Try credential name lookup
    cred_name = node.get_parameter(credential_name_param, "")
    if cred_name:
        cred_name = context.resolve_value(cred_name)
        if cred_name:
            provider = await _get_provider(context)
            if provider:
                try:
                    cred = await provider.get_credential(cred_name, required=False)
                    if cred:
                        value = getattr(cred, credential_field, None)
                        if value:
                            return value
                        if cred.data and credential_field in cred.data:
                            return str(cred.data[credential_field])
                except Exception as e:
                    logger.debug(f"Vault lookup failed: {e}")

    # Try direct parameter
    if direct_param:
        value = node.get_parameter(direct_param, "")
        if value:
            return context.resolve_value(value)

    # Try environment
    if env_var:
        value = os.environ.get(env_var)
        if value:
            return value

    if required:
        raise ValueError(f"Required credential not found for {credential_field}")

    return None


async def _get_provider(
    context: "ExecutionContext",
) -> Optional["VaultCredentialProvider"]:
    """Get or create credential provider from context."""
    if hasattr(context, "resources") and "credential_provider" in context.resources:
        return context.resources["credential_provider"]

    try:
        from casare_rpa.infrastructure.security.credential_provider import (
            VaultCredentialProvider,
        )

        provider = VaultCredentialProvider()
        await provider.initialize()

        if hasattr(context, "resources"):
            context.resources["credential_provider"] = provider

        return provider
    except Exception:
        return None


__all__ = [
    # Mixin
    "CredentialAwareMixin",
    # PropertyDef constants
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
    # Convenience function
    "resolve_node_credential",
]
