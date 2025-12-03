"""
HTTP authentication nodes for CasareRPA.

This module provides nodes for configuring HTTP authentication:
- HttpAuthNode: Configure Bearer, Basic, or API Key authentication

Uses CredentialAwareMixin for vault-integrated credential resolution.
"""

from __future__ import annotations

import base64
from typing import Any

from loguru import logger

from casare_rpa.domain.credentials import (
    CredentialAwareMixin,
    CREDENTIAL_NAME_PROP,
)
from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.decorators import executable_node, node_schema
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.domain.value_objects.types import (
    DataType,
    ExecutionResult,
    NodeStatus,
    PortType,
)


# HTTP Auth specific PropertyDef constants
HTTP_TOKEN_PROP = PropertyDef(
    "token",
    PropertyType.STRING,
    default="",
    label="Token / API Key",
    tooltip="Bearer token or API key (or use Credential Name for vault lookup)",
    tab="connection",
)

HTTP_USERNAME_PROP = PropertyDef(
    "username",
    PropertyType.STRING,
    default="",
    label="Username",
    tooltip="Username for Basic authentication (or use Credential Name)",
    tab="connection",
)

HTTP_PASSWORD_PROP = PropertyDef(
    "password",
    PropertyType.STRING,
    default="",
    label="Password",
    tooltip="Password for Basic authentication (or use Credential Name)",
    tab="connection",
)


@node_schema(
    CREDENTIAL_NAME_PROP,
    PropertyDef(
        "auth_type",
        PropertyType.CHOICE,
        default="Bearer",
        choices=["Bearer", "Basic", "ApiKey"],
        label="Authentication Type",
        tooltip="Type of authentication (Bearer, Basic, or API Key)",
    ),
    HTTP_TOKEN_PROP,
    HTTP_USERNAME_PROP,
    HTTP_PASSWORD_PROP,
    PropertyDef(
        "api_key_name",
        PropertyType.STRING,
        default="X-API-Key",
        label="API Key Header Name",
        tooltip="Header name for API key authentication",
    ),
)
@executable_node
class HttpAuthNode(CredentialAwareMixin, BaseNode):
    """
    Configure HTTP authentication headers.

    Supports:
        - Bearer token authentication
        - Basic authentication (username/password)
        - API Key authentication (custom header)

    Credential Resolution (in order):
        1. Vault lookup (via credential_name parameter)
        2. Direct parameters (token, username, password)
        3. Environment variables (HTTP_TOKEN, HTTP_USERNAME, HTTP_PASSWORD)

    Config (via @node_schema):
        credential_name: Credential alias for vault lookup
        auth_type: Type of authentication (Bearer, Basic, ApiKey)
        token: Bearer token or API key
        username: Username for Basic auth
        password: Password for Basic auth
        api_key_name: Header name for API key (default: X-API-Key)

    Inputs:
        auth_type, token, username, password, api_key_name, base_headers

    Outputs:
        headers: Headers with authentication configured
    """

    def __init__(self, node_id: str, name: str = "HTTP Auth", **kwargs: Any) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "HttpAuthNode"

    def _define_ports(self) -> None:
        self.add_input_port("credential_name", PortType.INPUT, DataType.STRING)
        self.add_input_port("auth_type", PortType.INPUT, DataType.STRING)
        self.add_input_port("token", PortType.INPUT, DataType.STRING)
        self.add_input_port("username", PortType.INPUT, DataType.STRING)
        self.add_input_port("password", PortType.INPUT, DataType.STRING)
        self.add_input_port("api_key_name", PortType.INPUT, DataType.STRING)
        self.add_input_port("base_headers", PortType.INPUT, DataType.DICT)

        self.add_output_port("headers", PortType.OUTPUT, DataType.DICT)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            auth_type = self.get_parameter("auth_type", "Bearer")
            api_key_name = self.get_parameter("api_key_name", "X-API-Key")
            base_headers = self.get_input_value("base_headers") or {}

            # Resolve credentials using CredentialAwareMixin
            if auth_type.lower() == "basic":
                username, password = await self.resolve_username_password(
                    context,
                    credential_name_param="credential_name",
                    username_param="username",
                    password_param="password",
                    env_prefix="HTTP",
                    required=False,
                )
                token = None
            else:
                # Bearer or ApiKey - resolve token
                token = await self.resolve_credential(
                    context,
                    credential_name_param="credential_name",
                    direct_param="token",
                    env_var="HTTP_TOKEN",
                    credential_field="api_key",
                    required=False,
                )
                username = None
                password = None

            headers = dict(base_headers)

            if auth_type.lower() == "bearer":
                if not token:
                    raise ValueError("Bearer token is required")
                headers["Authorization"] = f"Bearer {token}"
                logger.debug("Set Bearer token authentication")

            elif auth_type.lower() == "basic":
                if not username or not password:
                    raise ValueError(
                        "Username and password are required for Basic auth"
                    )
                credentials = base64.b64encode(
                    f"{username}:{password}".encode()
                ).decode()
                headers["Authorization"] = f"Basic {credentials}"
                logger.debug("Set Basic authentication")

            elif auth_type.lower() == "apikey":
                if not token:
                    raise ValueError("API key is required")
                headers[api_key_name] = token
                logger.debug(f"Set API key in header: {api_key_name}")

            else:
                raise ValueError(f"Unknown auth type: {auth_type}")

            self.set_output_value("headers", headers)

            self.status = NodeStatus.SUCCESS
            return {
                "success": True,
                "data": {"auth_type": auth_type},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            error_msg = f"HTTP auth error: {str(e)}"
            logger.error(error_msg)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg, "next_nodes": []}


@node_schema(
    PropertyDef(
        "client_id",
        PropertyType.STRING,
        default="",
        label="Client ID",
        tooltip="OAuth 2.0 client ID",
    ),
    PropertyDef(
        "auth_url",
        PropertyType.STRING,
        default="",
        label="Authorization URL",
        tooltip="OAuth 2.0 authorization endpoint URL",
    ),
    PropertyDef(
        "scope",
        PropertyType.STRING,
        default="",
        label="Scope",
        tooltip="OAuth 2.0 scope (space-separated)",
    ),
    PropertyDef(
        "redirect_uri",
        PropertyType.STRING,
        default="http://localhost:8080/callback",
        label="Redirect URI",
        tooltip="OAuth redirect URI (must match app registration)",
    ),
    PropertyDef(
        "state",
        PropertyType.STRING,
        default="",
        label="State",
        tooltip="CSRF protection state parameter (auto-generated if empty)",
    ),
    PropertyDef(
        "response_type",
        PropertyType.CHOICE,
        default="code",
        choices=["code", "token"],
        label="Response Type",
        tooltip="Authorization code flow (code) or implicit flow (token)",
    ),
    PropertyDef(
        "pkce_enabled",
        PropertyType.BOOLEAN,
        default=True,
        label="PKCE Enabled",
        tooltip="Enable PKCE (Proof Key for Code Exchange) for enhanced security",
    ),
)
@executable_node
class OAuth2AuthorizeNode(BaseNode):
    """
    Build OAuth 2.0 authorization URL for user authentication.

    Supports Authorization Code flow (with PKCE) and Implicit flow.
    Use this node to generate the URL that should be opened in a browser
    for the user to authenticate.

    Config (via @node_schema):
        client_id: OAuth 2.0 client ID
        auth_url: Authorization endpoint URL
        scope: Space-separated OAuth scopes
        redirect_uri: Callback URL
        state: CSRF state (auto-generated if empty)
        response_type: 'code' (auth code) or 'token' (implicit)
        pkce_enabled: Enable PKCE for authorization code flow

    Outputs:
        auth_url: Complete authorization URL to open
        state: State value for CSRF verification
        code_verifier: PKCE code verifier (store for token exchange)
        code_challenge: PKCE code challenge sent to server
    """

    def __init__(
        self, node_id: str, name: str = "OAuth2 Authorize", **kwargs: Any
    ) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "OAuth2AuthorizeNode"

    def _define_ports(self) -> None:
        self.add_input_port("client_id", PortType.INPUT, DataType.STRING)
        self.add_input_port("auth_url", PortType.INPUT, DataType.STRING)
        self.add_input_port("scope", PortType.INPUT, DataType.STRING)
        self.add_input_port("redirect_uri", PortType.INPUT, DataType.STRING)
        self.add_input_port("extra_params", PortType.INPUT, DataType.DICT)

        self.add_output_port("auth_url", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("state", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("code_verifier", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("code_challenge", PortType.OUTPUT, DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        import hashlib
        import secrets
        from urllib.parse import urlencode

        self.status = NodeStatus.RUNNING

        try:
            client_id = self.get_parameter("client_id", "")
            auth_url = self.get_parameter("auth_url", "")
            scope = self.get_parameter("scope", "")
            redirect_uri = self.get_parameter(
                "redirect_uri", "http://localhost:8080/callback"
            )
            state = self.get_parameter("state", "")
            response_type = self.get_parameter("response_type", "code")
            pkce_enabled = self.get_parameter("pkce_enabled", True)
            extra_params = self.get_input_value("extra_params") or {}

            # Resolve variables
            client_id = context.resolve_value(client_id)
            auth_url = context.resolve_value(auth_url)
            scope = context.resolve_value(scope)
            redirect_uri = context.resolve_value(redirect_uri)

            if not client_id:
                raise ValueError("client_id is required")
            if not auth_url:
                raise ValueError("auth_url is required")

            # Generate state if not provided
            if not state:
                state = secrets.token_urlsafe(32)

            # Build parameters
            params = {
                "client_id": client_id,
                "response_type": response_type,
                "redirect_uri": redirect_uri,
                "state": state,
            }

            if scope:
                params["scope"] = scope

            # PKCE support for authorization code flow
            code_verifier = ""
            code_challenge = ""
            if response_type == "code" and pkce_enabled:
                # Generate code verifier (43-128 chars)
                code_verifier = secrets.token_urlsafe(64)[:96]
                # Generate code challenge (SHA256 hash, base64url encoded)
                code_challenge_bytes = hashlib.sha256(code_verifier.encode()).digest()
                code_challenge = (
                    base64.urlsafe_b64encode(code_challenge_bytes).rstrip(b"=").decode()
                )
                params["code_challenge"] = code_challenge
                params["code_challenge_method"] = "S256"

            # Add extra params
            params.update(extra_params)

            # Build final URL
            separator = "&" if "?" in auth_url else "?"
            final_url = f"{auth_url}{separator}{urlencode(params)}"

            self.set_output_value("auth_url", final_url)
            self.set_output_value("state", state)
            self.set_output_value("code_verifier", code_verifier)
            self.set_output_value("code_challenge", code_challenge)

            self.status = NodeStatus.SUCCESS
            logger.debug(f"Generated OAuth2 authorization URL for client: {client_id}")
            return {
                "success": True,
                "data": {"auth_url": final_url, "state": state},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            error_msg = f"OAuth2 authorize error: {str(e)}"
            logger.error(error_msg)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg, "next_nodes": []}


@node_schema(
    PropertyDef(
        "client_id",
        PropertyType.STRING,
        default="",
        label="Client ID",
        tooltip="OAuth 2.0 client ID",
    ),
    PropertyDef(
        "client_secret",
        PropertyType.STRING,
        default="",
        label="Client Secret",
        tooltip="OAuth 2.0 client secret (optional for public clients)",
    ),
    PropertyDef(
        "token_url",
        PropertyType.STRING,
        default="",
        label="Token URL",
        tooltip="OAuth 2.0 token endpoint URL",
    ),
    PropertyDef(
        "redirect_uri",
        PropertyType.STRING,
        default="http://localhost:8080/callback",
        label="Redirect URI",
        tooltip="OAuth redirect URI (must match authorization request)",
    ),
    PropertyDef(
        "grant_type",
        PropertyType.CHOICE,
        default="authorization_code",
        choices=[
            "authorization_code",
            "client_credentials",
            "refresh_token",
            "password",
        ],
        label="Grant Type",
        tooltip="OAuth 2.0 grant type",
    ),
)
@executable_node
class OAuth2TokenExchangeNode(BaseNode):
    """
    Exchange OAuth 2.0 authorization code for access token.

    Supports multiple grant types:
    - authorization_code: Exchange auth code for tokens (with PKCE)
    - client_credentials: Get tokens using client credentials
    - refresh_token: Refresh expired access token
    - password: Resource owner password credentials (legacy)

    Config (via @node_schema):
        client_id: OAuth 2.0 client ID
        client_secret: Client secret (optional for public clients)
        token_url: Token endpoint URL
        redirect_uri: Callback URL (for auth code flow)
        grant_type: OAuth grant type

    Inputs:
        code: Authorization code (for auth code flow)
        code_verifier: PKCE code verifier (for auth code flow with PKCE)
        refresh_token: Refresh token (for refresh_token flow)
        username: Username (for password flow)
        password: Password (for password flow)
        scope: Scope override

    Outputs:
        access_token: Access token
        refresh_token: Refresh token (if provided)
        token_type: Token type (usually 'Bearer')
        expires_in: Token lifetime in seconds
        scope: Granted scope
        id_token: ID token (for OIDC)
        full_response: Complete token response
    """

    def __init__(
        self, node_id: str, name: str = "OAuth2 Token Exchange", **kwargs: Any
    ) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "OAuth2TokenExchangeNode"

    def _define_ports(self) -> None:
        self.add_input_port("code", PortType.INPUT, DataType.STRING)
        self.add_input_port("code_verifier", PortType.INPUT, DataType.STRING)
        self.add_input_port("refresh_token", PortType.INPUT, DataType.STRING)
        self.add_input_port("username", PortType.INPUT, DataType.STRING)
        self.add_input_port("password", PortType.INPUT, DataType.STRING)
        self.add_input_port("scope", PortType.INPUT, DataType.STRING)

        self.add_output_port("access_token", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("refresh_token", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("token_type", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("expires_in", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("scope", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("id_token", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("full_response", PortType.OUTPUT, DataType.DICT)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        import aiohttp

        self.status = NodeStatus.RUNNING

        try:
            client_id = self.get_parameter("client_id", "")
            client_secret = self.get_parameter("client_secret", "")
            token_url = self.get_parameter("token_url", "")
            redirect_uri = self.get_parameter("redirect_uri", "")
            grant_type = self.get_parameter("grant_type", "authorization_code")

            code = self.get_input_value("code") or ""
            code_verifier = self.get_input_value("code_verifier") or ""
            refresh_token_input = self.get_input_value("refresh_token") or ""
            username = self.get_input_value("username") or ""
            password_input = self.get_input_value("password") or ""
            scope = self.get_input_value("scope") or ""

            # Resolve variables
            client_id = context.resolve_value(client_id)
            client_secret = context.resolve_value(client_secret)
            token_url = context.resolve_value(token_url)
            code = context.resolve_value(code)
            code_verifier = context.resolve_value(code_verifier)
            refresh_token_input = context.resolve_value(refresh_token_input)

            if not client_id:
                raise ValueError("client_id is required")
            if not token_url:
                raise ValueError("token_url is required")

            # Build token request body
            data = {
                "grant_type": grant_type,
                "client_id": client_id,
            }

            # Add client secret if provided
            if client_secret:
                data["client_secret"] = client_secret

            # Grant-type specific parameters
            if grant_type == "authorization_code":
                if not code:
                    raise ValueError("Authorization code is required")
                data["code"] = code
                data["redirect_uri"] = redirect_uri
                if code_verifier:
                    data["code_verifier"] = code_verifier

            elif grant_type == "refresh_token":
                if not refresh_token_input:
                    raise ValueError("Refresh token is required")
                data["refresh_token"] = refresh_token_input

            elif grant_type == "client_credentials":
                if not client_secret:
                    raise ValueError(
                        "Client secret is required for client_credentials grant"
                    )

            elif grant_type == "password":
                if not username or not password_input:
                    raise ValueError("Username and password are required")
                data["username"] = context.resolve_value(username)
                data["password"] = context.resolve_value(password_input)

            if scope:
                data["scope"] = context.resolve_value(scope)

            # Make token request
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    token_url,
                    data=data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                ) as response:
                    response_data = await response.json()

                    if response.status != 200:
                        error = response_data.get("error", "unknown_error")
                        error_desc = response_data.get(
                            "error_description", "Token exchange failed"
                        )
                        raise ValueError(f"OAuth error: {error} - {error_desc}")

            # Extract tokens from response
            access_token = response_data.get("access_token", "")
            refresh_token = response_data.get("refresh_token", "")
            token_type = response_data.get("token_type", "Bearer")
            expires_in = response_data.get("expires_in", 0)
            granted_scope = response_data.get("scope", "")
            id_token = response_data.get("id_token", "")

            self.set_output_value("access_token", access_token)
            self.set_output_value("refresh_token", refresh_token)
            self.set_output_value("token_type", token_type)
            self.set_output_value("expires_in", expires_in)
            self.set_output_value("scope", granted_scope)
            self.set_output_value("id_token", id_token)
            self.set_output_value("full_response", response_data)

            self.status = NodeStatus.SUCCESS
            logger.info(f"OAuth2 token exchange successful, expires_in: {expires_in}s")
            return {
                "success": True,
                "data": {"token_type": token_type, "expires_in": expires_in},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            error_msg = f"OAuth2 token exchange error: {str(e)}"
            logger.error(error_msg)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg, "next_nodes": []}


@node_schema(
    PropertyDef(
        "port",
        PropertyType.INTEGER,
        default=8080,
        min_value=1024,
        max_value=65535,
        label="Port",
        tooltip="Local port for callback server",
    ),
    PropertyDef(
        "timeout",
        PropertyType.INTEGER,
        default=120,
        min_value=10,
        max_value=600,
        label="Timeout (seconds)",
        tooltip="Maximum time to wait for callback",
    ),
    PropertyDef(
        "path",
        PropertyType.STRING,
        default="/callback",
        label="Callback Path",
        tooltip="URL path for the callback",
    ),
)
@executable_node
class OAuth2CallbackServerNode(BaseNode):
    """
    Start a local server to receive OAuth 2.0 callback.

    This node starts a temporary HTTP server that waits for the OAuth
    provider to redirect back with the authorization code or tokens.

    Config (via @node_schema):
        port: Local port for callback server (default: 8080)
        timeout: Maximum wait time in seconds (default: 120)
        path: Callback URL path (default: /callback)

    Inputs:
        expected_state: Expected state parameter for CSRF verification

    Outputs:
        code: Authorization code (for auth code flow)
        state: Received state parameter
        access_token: Access token (for implicit flow)
        error: Error from OAuth provider (if any)
        error_description: Error description (if any)
    """

    def __init__(
        self, node_id: str, name: str = "OAuth2 Callback Server", **kwargs: Any
    ) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "OAuth2CallbackServerNode"

    def _define_ports(self) -> None:
        self.add_input_port("expected_state", PortType.INPUT, DataType.STRING)

        self.add_output_port("code", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("state", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("access_token", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("error", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("error_description", PortType.OUTPUT, DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        import asyncio
        from aiohttp import web

        self.status = NodeStatus.RUNNING

        try:
            port = int(self.get_parameter("port", 8080))
            timeout = int(self.get_parameter("timeout", 120))
            path = self.get_parameter("path", "/callback")
            expected_state = self.get_input_value("expected_state") or ""

            if expected_state:
                expected_state = context.resolve_value(expected_state)

            # Callback result storage
            result = {"received": False, "data": {}}

            async def callback_handler(request: web.Request) -> web.Response:
                """Handle OAuth callback."""
                # Parse query parameters
                params = dict(request.query)

                # Check for fragment (implicit flow sends tokens in fragment)
                # Note: Fragments aren't sent to server, so we serve HTML that captures it
                if not params:
                    # Serve HTML page that captures fragment and redirects
                    html = """
                    <!DOCTYPE html>
                    <html>
                    <head><title>OAuth Callback</title></head>
                    <body>
                        <script>
                            // Capture fragment parameters
                            var fragment = window.location.hash.substr(1);
                            if (fragment) {
                                // Redirect with fragment as query params
                                window.location = window.location.pathname + '?' + fragment;
                            } else if (window.location.search) {
                                document.body.innerHTML = '<h1>Authentication Complete</h1><p>You can close this window.</p>';
                            }
                        </script>
                        <p>Processing authentication...</p>
                    </body>
                    </html>
                    """
                    return web.Response(text=html, content_type="text/html")

                result["received"] = True
                result["data"] = params

                # Return success page
                html = """
                <!DOCTYPE html>
                <html>
                <head><title>OAuth Callback</title></head>
                <body>
                    <h1>Authentication Complete</h1>
                    <p>You can close this window and return to the application.</p>
                </body>
                </html>
                """
                return web.Response(text=html, content_type="text/html")

            # Create and start server
            app = web.Application()
            app.router.add_get(path, callback_handler)

            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, "127.0.0.1", port)

            try:
                await site.start()
                logger.info(
                    f"OAuth callback server started on http://127.0.0.1:{port}{path}"
                )

                # Wait for callback with timeout
                start_time = asyncio.get_event_loop().time()
                while not result["received"]:
                    if asyncio.get_event_loop().time() - start_time > timeout:
                        raise TimeoutError(
                            f"OAuth callback not received within {timeout} seconds"
                        )
                    await asyncio.sleep(0.1)

            finally:
                await runner.cleanup()

            # Process received data
            data = result["data"]

            # Check for error
            if "error" in data:
                error = data.get("error", "")
                error_desc = data.get("error_description", "")
                self.set_output_value("error", error)
                self.set_output_value("error_description", error_desc)
                raise ValueError(f"OAuth error: {error} - {error_desc}")

            # Verify state for CSRF protection
            received_state = data.get("state", "")
            if expected_state and received_state != expected_state:
                raise ValueError(
                    f"State mismatch: expected '{expected_state}', got '{received_state}'. "
                    "This may indicate a CSRF attack."
                )

            # Extract data
            code = data.get("code", "")
            access_token = data.get("access_token", "")

            self.set_output_value("code", code)
            self.set_output_value("state", received_state)
            self.set_output_value("access_token", access_token)
            self.set_output_value("error", "")
            self.set_output_value("error_description", "")

            self.status = NodeStatus.SUCCESS
            logger.info("OAuth callback received successfully")
            return {
                "success": True,
                "data": {"has_code": bool(code), "has_token": bool(access_token)},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            error_msg = f"OAuth2 callback error: {str(e)}"
            logger.error(error_msg)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg, "next_nodes": []}


@node_schema(
    PropertyDef(
        "introspection_url",
        PropertyType.STRING,
        default="",
        label="Introspection URL",
        tooltip="Token introspection endpoint URL (RFC 7662)",
    ),
    PropertyDef(
        "client_id",
        PropertyType.STRING,
        default="",
        label="Client ID",
        tooltip="Client ID for introspection authentication",
    ),
    PropertyDef(
        "client_secret",
        PropertyType.STRING,
        default="",
        label="Client Secret",
        tooltip="Client secret for introspection authentication",
    ),
)
@executable_node
class OAuth2TokenValidateNode(BaseNode):
    """
    Validate an OAuth 2.0 access token using introspection endpoint.

    Implements RFC 7662 (Token Introspection) to check if a token
    is active and retrieve its metadata.

    Config (via @node_schema):
        introspection_url: Token introspection endpoint URL
        client_id: Client ID for authentication
        client_secret: Client secret for authentication

    Inputs:
        token: Access token to validate

    Outputs:
        active: Whether token is active
        client_id: Token's client ID
        username: Resource owner username
        scope: Token scope
        expires_at: Token expiration timestamp
        token_type: Token type
        full_response: Complete introspection response
    """

    def __init__(
        self, node_id: str, name: str = "OAuth2 Token Validate", **kwargs: Any
    ) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "OAuth2TokenValidateNode"

    def _define_ports(self) -> None:
        self.add_input_port("token", PortType.INPUT, DataType.STRING)

        self.add_output_port("active", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("client_id", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("username", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("scope", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("expires_at", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("token_type", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("full_response", PortType.OUTPUT, DataType.DICT)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        import aiohttp

        self.status = NodeStatus.RUNNING

        try:
            introspection_url = self.get_parameter("introspection_url", "")
            client_id = self.get_parameter("client_id", "")
            client_secret = self.get_parameter("client_secret", "")
            token = self.get_input_value("token") or ""

            # Resolve variables
            introspection_url = context.resolve_value(introspection_url)
            client_id = context.resolve_value(client_id)
            client_secret = context.resolve_value(client_secret)
            token = context.resolve_value(token)

            if not introspection_url:
                raise ValueError("introspection_url is required")
            if not token:
                raise ValueError("token is required")

            # Build introspection request
            data = {"token": token}

            # Client authentication via Basic auth or body
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            if client_id and client_secret:
                credentials = base64.b64encode(
                    f"{client_id}:{client_secret}".encode()
                ).decode()
                headers["Authorization"] = f"Basic {credentials}"
            elif client_id:
                data["client_id"] = client_id

            # Make introspection request
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    introspection_url, data=data, headers=headers
                ) as response:
                    response_data = await response.json()

                    if response.status != 200:
                        raise ValueError(
                            f"Introspection failed: HTTP {response.status}"
                        )

            # Extract token info
            active = response_data.get("active", False)
            token_client_id = response_data.get("client_id", "")
            username = response_data.get("username", "")
            scope = response_data.get("scope", "")
            expires_at = response_data.get("exp", 0)
            token_type = response_data.get("token_type", "")

            self.set_output_value("active", active)
            self.set_output_value("client_id", token_client_id)
            self.set_output_value("username", username)
            self.set_output_value("scope", scope)
            self.set_output_value("expires_at", expires_at)
            self.set_output_value("token_type", token_type)
            self.set_output_value("full_response", response_data)

            self.status = NodeStatus.SUCCESS
            logger.info(f"Token introspection: active={active}")
            return {
                "success": True,
                "data": {"active": active},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            error_msg = f"OAuth2 token validation error: {str(e)}"
            logger.error(error_msg)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg, "next_nodes": []}


__all__ = [
    "HttpAuthNode",
    "OAuth2AuthorizeNode",
    "OAuth2TokenExchangeNode",
    "OAuth2CallbackServerNode",
    "OAuth2TokenValidateNode",
]
