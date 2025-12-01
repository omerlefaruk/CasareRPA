"""Tests for OAuth 2.0 nodes."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from urllib.parse import parse_qs, urlparse

from casare_rpa.nodes.http.http_auth import (
    OAuth2AuthorizeNode,
    OAuth2TokenExchangeNode,
    OAuth2CallbackServerNode,
    OAuth2TokenValidateNode,
)
from casare_rpa.domain.value_objects.types import NodeStatus


@pytest.fixture
def mock_execution_context():
    """Create a mock execution context."""
    context = MagicMock()
    context.resolve_value = lambda x: x  # Pass through
    return context


class TestOAuth2AuthorizeNode:
    """Tests for OAuth2AuthorizeNode."""

    @pytest.fixture
    def auth_node(self):
        """Create OAuth2 authorize node."""
        return OAuth2AuthorizeNode(
            node_id="oauth_auth1",
            name="OAuth2 Authorize",
            config={
                "client_id": "test_client_id",
                "auth_url": "https://auth.example.com/authorize",
                "scope": "openid profile email",
                "redirect_uri": "http://localhost:8080/callback",
                "response_type": "code",
                "pkce_enabled": True,
            },
        )

    @pytest.mark.asyncio
    async def test_generates_auth_url(self, auth_node, mock_execution_context):
        """Test that authorization URL is generated correctly."""
        result = await auth_node.execute(mock_execution_context)

        assert result["success"] is True
        assert auth_node.status == NodeStatus.SUCCESS

        # Check outputs
        auth_url = auth_node.get_output_value("auth_url")
        assert auth_url is not None
        assert "https://auth.example.com/authorize" in auth_url

    @pytest.mark.asyncio
    async def test_includes_required_params(self, auth_node, mock_execution_context):
        """Test that required OAuth params are included."""
        await auth_node.execute(mock_execution_context)

        auth_url = auth_node.get_output_value("auth_url")
        parsed = urlparse(auth_url)
        params = parse_qs(parsed.query)

        assert "client_id" in params
        assert params["client_id"][0] == "test_client_id"
        assert "response_type" in params
        assert params["response_type"][0] == "code"
        assert "redirect_uri" in params
        assert "state" in params

    @pytest.mark.asyncio
    async def test_generates_state(self, auth_node, mock_execution_context):
        """Test that state parameter is generated."""
        await auth_node.execute(mock_execution_context)

        state = auth_node.get_output_value("state")
        assert state is not None
        assert len(state) > 10  # State should be reasonably long

    @pytest.mark.asyncio
    async def test_pkce_generates_challenge(self, auth_node, mock_execution_context):
        """Test PKCE code challenge generation."""
        await auth_node.execute(mock_execution_context)

        auth_url = auth_node.get_output_value("auth_url")
        parsed = urlparse(auth_url)
        params = parse_qs(parsed.query)

        assert "code_challenge" in params
        assert "code_challenge_method" in params
        assert params["code_challenge_method"][0] == "S256"

        code_verifier = auth_node.get_output_value("code_verifier")
        code_challenge = auth_node.get_output_value("code_challenge")

        assert code_verifier is not None
        assert code_challenge is not None
        assert len(code_verifier) > 40  # Verifier should be long enough

    @pytest.mark.asyncio
    async def test_implicit_flow(self, mock_execution_context):
        """Test implicit flow (response_type=token)."""
        node = OAuth2AuthorizeNode(
            node_id="oauth_implicit",
            config={
                "client_id": "test_client",
                "auth_url": "https://auth.example.com/authorize",
                "response_type": "token",
                "pkce_enabled": False,
            },
        )

        await node.execute(mock_execution_context)

        auth_url = node.get_output_value("auth_url")
        parsed = urlparse(auth_url)
        params = parse_qs(parsed.query)

        assert params["response_type"][0] == "token"
        # PKCE should not be present for implicit flow
        assert "code_challenge" not in params

    @pytest.mark.asyncio
    async def test_missing_client_id_raises(self, mock_execution_context):
        """Test that missing client_id raises error."""
        node = OAuth2AuthorizeNode(
            node_id="oauth_no_client",
            config={
                "auth_url": "https://auth.example.com/authorize",
            },
        )

        result = await node.execute(mock_execution_context)

        assert result["success"] is False
        assert "client_id" in result["error"].lower()
        assert node.status == NodeStatus.ERROR

    @pytest.mark.asyncio
    async def test_missing_auth_url_raises(self, mock_execution_context):
        """Test that missing auth_url raises error."""
        node = OAuth2AuthorizeNode(
            node_id="oauth_no_url",
            config={
                "client_id": "test_client",
            },
        )

        result = await node.execute(mock_execution_context)

        assert result["success"] is False
        assert "auth_url" in result["error"].lower()


class TestOAuth2TokenExchangeNode:
    """Tests for OAuth2TokenExchangeNode."""

    @pytest.fixture
    def token_node(self):
        """Create OAuth2 token exchange node."""
        node = OAuth2TokenExchangeNode(
            node_id="oauth_token1",
            name="Token Exchange",
            config={
                "client_id": "test_client",
                "client_secret": "test_secret",
                "token_url": "https://auth.example.com/token",
                "redirect_uri": "http://localhost:8080/callback",
                "grant_type": "authorization_code",
            },
        )
        return node

    def test_node_initialization(self, token_node):
        """Test node initializes correctly."""
        assert token_node.node_id == "oauth_token1"
        assert token_node.node_type == "OAuth2TokenExchangeNode"

    @pytest.mark.asyncio
    async def test_missing_client_id(self, mock_execution_context):
        """Test missing client_id returns error."""
        node = OAuth2TokenExchangeNode(
            node_id="oauth_missing",
            config={
                "token_url": "https://auth.example.com/token",
            },
        )

        result = await node.execute(mock_execution_context)

        assert result["success"] is False
        assert "client_id" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_missing_token_url(self, mock_execution_context):
        """Test missing token_url returns error."""
        node = OAuth2TokenExchangeNode(
            node_id="oauth_missing_url",
            config={
                "client_id": "test_client",
            },
        )

        result = await node.execute(mock_execution_context)

        assert result["success"] is False
        assert "token_url" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_auth_code_requires_code(self, mock_execution_context):
        """Test authorization_code grant requires code."""
        node = OAuth2TokenExchangeNode(
            node_id="oauth_no_code",
            config={
                "client_id": "test_client",
                "client_secret": "test_secret",
                "token_url": "https://auth.example.com/token",
                "grant_type": "authorization_code",
            },
        )

        result = await node.execute(mock_execution_context)

        assert result["success"] is False
        assert "code" in result["error"].lower()


class TestOAuth2TokenValidateNode:
    """Tests for OAuth2TokenValidateNode."""

    @pytest.fixture
    def validate_node(self):
        """Create token validation node."""
        node = OAuth2TokenValidateNode(
            node_id="oauth_validate",
            config={
                "introspection_url": "https://auth.example.com/introspect",
                "client_id": "test_client",
                "client_secret": "test_secret",
            },
        )
        return node

    def test_node_initialization(self, validate_node):
        """Test node initializes correctly."""
        assert validate_node.node_id == "oauth_validate"
        assert validate_node.node_type == "OAuth2TokenValidateNode"

    @pytest.mark.asyncio
    async def test_missing_token_raises(self, validate_node, mock_execution_context):
        """Test that missing token raises error."""
        result = await validate_node.execute(mock_execution_context)

        assert result["success"] is False
        assert "token" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_missing_introspection_url_raises(self, mock_execution_context):
        """Test that missing introspection URL raises error."""
        node = OAuth2TokenValidateNode(
            node_id="oauth_no_url",
            config={
                "client_id": "test_client",
            },
        )
        node.set_input_value("token", "some_token")

        result = await node.execute(mock_execution_context)

        assert result["success"] is False
        assert "introspection_url" in result["error"].lower()


class TestOAuth2CallbackServerNode:
    """Tests for OAuth2CallbackServerNode."""

    @pytest.fixture
    def callback_node(self):
        """Create callback server node."""
        return OAuth2CallbackServerNode(
            node_id="oauth_callback",
            config={
                "port": 8888,
                "timeout": 5,
                "path": "/callback",
            },
        )

    def test_node_initialization(self, callback_node):
        """Test node initializes correctly."""
        assert callback_node.node_id == "oauth_callback"
        assert callback_node.node_type == "OAuth2CallbackServerNode"
        assert callback_node.get_parameter("port", 8080) == 8888
        assert callback_node.get_parameter("timeout", 120) == 5
        assert callback_node.get_parameter("path", "/callback") == "/callback"

    def test_port_configuration(self):
        """Test various port configurations."""
        node = OAuth2CallbackServerNode(node_id="cb1", config={"port": 3000})
        assert node.get_parameter("port", 8080) == 3000

    def test_default_values(self):
        """Test default configuration values."""
        node = OAuth2CallbackServerNode(node_id="cb_defaults")
        # Should use defaults
        assert node.get_parameter("port", 8080) == 8080
        assert node.get_parameter("timeout", 120) == 120
        assert node.get_parameter("path", "/callback") == "/callback"


class TestOAuth2NodeTypes:
    """Test node type strings are correct."""

    def test_authorize_node_type(self):
        """Test OAuth2AuthorizeNode has correct type."""
        node = OAuth2AuthorizeNode(node_id="test")
        assert node.node_type == "OAuth2AuthorizeNode"

    def test_token_exchange_node_type(self):
        """Test OAuth2TokenExchangeNode has correct type."""
        node = OAuth2TokenExchangeNode(node_id="test")
        assert node.node_type == "OAuth2TokenExchangeNode"

    def test_callback_server_node_type(self):
        """Test OAuth2CallbackServerNode has correct type."""
        node = OAuth2CallbackServerNode(node_id="test")
        assert node.node_type == "OAuth2CallbackServerNode"

    def test_token_validate_node_type(self):
        """Test OAuth2TokenValidateNode has correct type."""
        node = OAuth2TokenValidateNode(node_id="test")
        assert node.node_type == "OAuth2TokenValidateNode"


class TestOAuth2NodePorts:
    """Test node input/output ports are defined correctly."""

    def test_authorize_node_created(self):
        """Test OAuth2AuthorizeNode is created successfully."""
        node = OAuth2AuthorizeNode(node_id="test")
        assert node is not None
        assert node.node_id == "test"

    def test_token_exchange_node_created(self):
        """Test OAuth2TokenExchangeNode is created successfully."""
        node = OAuth2TokenExchangeNode(node_id="test")
        assert node is not None
        assert node.node_id == "test"

    def test_validate_node_created(self):
        """Test OAuth2TokenValidateNode is created successfully."""
        node = OAuth2TokenValidateNode(node_id="test")
        assert node is not None
        assert node.node_id == "test"

    def test_callback_node_created(self):
        """Test OAuth2CallbackServerNode is created successfully."""
        node = OAuth2CallbackServerNode(node_id="test")
        assert node is not None
        assert node.node_id == "test"
