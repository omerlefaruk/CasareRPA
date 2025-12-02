"""
Tests for the credential resolution system.

Tests CredentialAwareMixin and related functionality for vault-integrated
credential resolution in nodes.
"""

import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from casare_rpa.domain.credentials import (
    CredentialAwareMixin,
    CREDENTIAL_NAME_PROP,
    API_KEY_PROP,
    USERNAME_PROP,
    PASSWORD_PROP,
    BOT_TOKEN_PROP,
    resolve_node_credential,
)
from casare_rpa.domain.schemas import PropertyType


# =============================================================================
# Test PropertyDef Constants
# =============================================================================


class TestCredentialPropertyDefs:
    """Test standard credential PropertyDef constants."""

    def test_credential_name_prop_has_connection_tab(self):
        """Credential name should be in connection tab."""
        assert CREDENTIAL_NAME_PROP.tab == "connection"
        assert CREDENTIAL_NAME_PROP.name == "credential_name"

    def test_api_key_prop_has_connection_tab(self):
        """API key should be in connection tab."""
        assert API_KEY_PROP.tab == "connection"
        assert API_KEY_PROP.name == "api_key"

    def test_username_password_props_have_connection_tab(self):
        """Username/password should be in connection tab."""
        assert USERNAME_PROP.tab == "connection"
        assert PASSWORD_PROP.tab == "connection"

    def test_bot_token_prop_has_connection_tab(self):
        """Bot token should be in connection tab."""
        assert BOT_TOKEN_PROP.tab == "connection"
        assert BOT_TOKEN_PROP.name == "bot_token"

    def test_all_props_have_string_type(self):
        """Credential properties should be STRING type."""
        assert CREDENTIAL_NAME_PROP.type == PropertyType.STRING
        assert API_KEY_PROP.type == PropertyType.STRING
        assert USERNAME_PROP.type == PropertyType.STRING
        assert PASSWORD_PROP.type == PropertyType.STRING


# =============================================================================
# Test CredentialAwareMixin
# =============================================================================


class MockNode(CredentialAwareMixin):
    """Mock node for testing the mixin."""

    def __init__(self):
        self._parameters = {}

    def get_parameter(self, name: str, default: str = "") -> str:
        return self._parameters.get(name, default)

    def set_parameter(self, name: str, value: str) -> None:
        self._parameters[name] = value


@pytest.fixture
def mock_context():
    """Create mock execution context."""
    context = MagicMock()
    context.resolve_value = lambda x: x  # Pass-through
    context.get_variable = MagicMock(return_value=None)
    context.has_project_context = False
    context.resources = {}
    return context


@pytest.fixture
def mock_provider():
    """Create mock credential provider."""
    provider = AsyncMock()
    provider.get_credential = AsyncMock(return_value=None)
    provider.initialize = AsyncMock()
    return provider


class TestCredentialAwareMixin:
    """Test CredentialAwareMixin credential resolution."""

    @pytest.mark.asyncio
    async def test_resolve_from_direct_parameter(self, mock_context):
        """Should resolve credential from direct parameter."""
        node = MockNode()
        node.set_parameter("api_key", "sk-test-key")

        result = await node.resolve_credential(
            mock_context,
            credential_name_param="credential_name",
            direct_param="api_key",
        )

        assert result == "sk-test-key"

    @pytest.mark.asyncio
    async def test_resolve_from_environment(self, mock_context):
        """Should resolve credential from environment variable."""
        node = MockNode()

        with patch.dict(os.environ, {"TEST_API_KEY": "env-key-123"}):
            result = await node.resolve_credential(
                mock_context,
                credential_name_param="credential_name",
                env_var="TEST_API_KEY",
            )

        assert result == "env-key-123"

    @pytest.mark.asyncio
    async def test_resolve_from_context_variable(self, mock_context):
        """Should resolve credential from context variable."""
        node = MockNode()
        mock_context.get_variable.return_value = "context-var-key"

        result = await node.resolve_credential(
            mock_context,
            credential_name_param="credential_name",
            context_var="my_api_key",
        )

        assert result == "context-var-key"
        mock_context.get_variable.assert_called_with("my_api_key")

    @pytest.mark.asyncio
    async def test_resolve_direct_param_takes_priority_over_env(self, mock_context):
        """Direct parameter should take priority over environment."""
        node = MockNode()
        node.set_parameter("api_key", "direct-key")

        with patch.dict(os.environ, {"TEST_API_KEY": "env-key"}):
            result = await node.resolve_credential(
                mock_context,
                credential_name_param="credential_name",
                direct_param="api_key",
                env_var="TEST_API_KEY",
            )

        assert result == "direct-key"

    @pytest.mark.asyncio
    async def test_resolve_returns_none_when_not_found(self, mock_context):
        """Should return None when credential not found and not required."""
        node = MockNode()

        result = await node.resolve_credential(
            mock_context,
            credential_name_param="credential_name",
            direct_param="api_key",
            required=False,
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_resolve_raises_when_required_and_not_found(self, mock_context):
        """Should raise ValueError when required credential not found."""
        node = MockNode()

        with pytest.raises(ValueError, match="Required credential not found"):
            await node.resolve_credential(
                mock_context,
                credential_name_param="credential_name",
                direct_param="api_key",
                required=True,
            )

    @pytest.mark.asyncio
    async def test_resolve_username_password_from_params(self, mock_context):
        """Should resolve username/password from direct parameters."""
        node = MockNode()
        node.set_parameter("username", "test_user")
        node.set_parameter("password", "test_pass")

        username, password = await node.resolve_username_password(
            mock_context,
            username_param="username",
            password_param="password",
        )

        assert username == "test_user"
        assert password == "test_pass"

    @pytest.mark.asyncio
    async def test_resolve_username_password_from_env(self, mock_context):
        """Should resolve username/password from environment."""
        node = MockNode()

        with patch.dict(
            os.environ,
            {
                "SMTP_USERNAME": "env_user",
                "SMTP_PASSWORD": "env_pass",
            },
        ):
            username, password = await node.resolve_username_password(
                mock_context,
                env_prefix="SMTP",
            )

        assert username == "env_user"
        assert password == "env_pass"

    @pytest.mark.asyncio
    async def test_resolve_username_password_raises_when_required(self, mock_context):
        """Should raise when required and credentials not found."""
        node = MockNode()

        with pytest.raises(ValueError, match="Required username/password not found"):
            await node.resolve_username_password(
                mock_context,
                required=True,
            )


# =============================================================================
# Test Vault Integration
# =============================================================================


class TestVaultIntegration:
    """Test credential resolution with vault provider."""

    @pytest.mark.asyncio
    async def test_resolve_from_vault(self, mock_context, mock_provider):
        """Should resolve credential from vault when credential_name is set."""
        node = MockNode()
        node.set_parameter("credential_name", "my_telegram")

        # Mock the vault credential
        mock_credential = MagicMock()
        mock_credential.api_key = "vault-api-key-123"
        mock_credential.data = {}
        mock_provider.get_credential.return_value = mock_credential

        # Inject provider into context
        mock_context.resources["credential_provider"] = mock_provider

        # Mock _get_credential_provider to return our mock
        with patch.object(
            node,
            "_get_credential_provider",
            return_value=mock_provider,
        ):
            result = await node.resolve_credential(
                mock_context,
                credential_name_param="credential_name",
                direct_param="api_key",
                credential_field="api_key",
            )

        assert result == "vault-api-key-123"

    @pytest.mark.asyncio
    async def test_vault_credential_takes_priority(self, mock_context, mock_provider):
        """Vault credential should take priority over direct parameter."""
        node = MockNode()
        node.set_parameter("credential_name", "my_cred")
        node.set_parameter("api_key", "direct-key")  # Should be ignored

        mock_credential = MagicMock()
        mock_credential.api_key = "vault-key"
        mock_credential.data = {}
        mock_provider.get_credential.return_value = mock_credential

        mock_context.resources["credential_provider"] = mock_provider

        with patch.object(
            node,
            "_get_credential_provider",
            return_value=mock_provider,
        ):
            result = await node.resolve_credential(
                mock_context,
                credential_name_param="credential_name",
                direct_param="api_key",
                credential_field="api_key",
            )

        # Vault takes priority
        assert result == "vault-key"

    @pytest.mark.asyncio
    async def test_fallback_to_direct_when_vault_empty(
        self, mock_context, mock_provider
    ):
        """Should fall back to direct param when vault returns None."""
        node = MockNode()
        node.set_parameter("credential_name", "nonexistent")
        node.set_parameter("api_key", "fallback-key")

        mock_provider.get_credential.return_value = None
        mock_context.resources["credential_provider"] = mock_provider

        with patch.object(
            node,
            "_get_credential_provider",
            return_value=mock_provider,
        ):
            result = await node.resolve_credential(
                mock_context,
                credential_name_param="credential_name",
                direct_param="api_key",
                credential_field="api_key",
            )

        assert result == "fallback-key"


# =============================================================================
# Test resolve_node_credential Standalone Function
# =============================================================================


class TestResolveNodeCredentialFunction:
    """Test the standalone resolve_node_credential function."""

    @pytest.mark.asyncio
    async def test_resolve_from_direct_param(self, mock_context):
        """Should resolve from direct parameter."""
        mock_node = MagicMock()
        mock_node.get_parameter.side_effect = lambda n, d="": {
            "credential_name": "",
            "api_key": "direct-api-key",
        }.get(n, d)

        result = await resolve_node_credential(
            mock_context,
            mock_node,
            direct_param="api_key",
        )

        assert result == "direct-api-key"

    @pytest.mark.asyncio
    async def test_resolve_from_env_var(self, mock_context):
        """Should resolve from environment variable."""
        mock_node = MagicMock()
        mock_node.get_parameter.return_value = ""

        with patch.dict(os.environ, {"MY_API_KEY": "env-api-key"}):
            result = await resolve_node_credential(
                mock_context,
                mock_node,
                env_var="MY_API_KEY",
            )

        assert result == "env-api-key"


# =============================================================================
# Test ExecutionContext Integration
# =============================================================================


class TestExecutionContextCredentials:
    """Test credential provider in ExecutionContext."""

    @pytest.mark.asyncio
    async def test_get_credential_provider_lazy_init(self):
        """Credential provider should be lazily initialized."""
        from casare_rpa.infrastructure.execution import ExecutionContext

        context = ExecutionContext(workflow_name="test")

        # Provider should not be initialized yet
        assert context._credential_provider is None

        # After getting provider, it should be cached
        with patch(
            "casare_rpa.infrastructure.security.credential_provider.VaultCredentialProvider"
        ) as MockProvider:
            mock_instance = AsyncMock()
            MockProvider.return_value = mock_instance

            provider = await context.get_credential_provider()

            # Provider should be initialized and cached
            mock_instance.initialize.assert_called_once()
            assert context._credential_provider is mock_instance

    @pytest.mark.asyncio
    async def test_resolve_credential_method(self):
        """ExecutionContext should have resolve_credential method."""
        from casare_rpa.infrastructure.execution import ExecutionContext

        context = ExecutionContext(workflow_name="test")

        # Mock the provider
        with patch.object(context, "get_credential_provider") as mock_get:
            mock_provider = AsyncMock()
            mock_provider.get_credential.return_value = MagicMock(api_key="test-key")
            mock_get.return_value = mock_provider

            result = await context.resolve_credential("my_alias")

            mock_provider.get_credential.assert_called_once_with(
                "my_alias", required=False
            )

    @pytest.mark.asyncio
    async def test_cleanup_shuts_down_provider(self):
        """Cleanup should shutdown credential provider."""
        from casare_rpa.infrastructure.execution import ExecutionContext

        context = ExecutionContext(workflow_name="test")

        # Mock provider
        mock_provider = AsyncMock()
        context._credential_provider = mock_provider
        context.resources["credential_provider"] = mock_provider

        await context.cleanup()

        mock_provider.shutdown.assert_called_once()
        assert context._credential_provider is None


# =============================================================================
# Test Telegram Node Integration
# =============================================================================


class TestTelegramNodeCredentials:
    """Test credential resolution in Telegram nodes."""

    @pytest.mark.asyncio
    async def test_telegram_base_node_uses_mixin(self):
        """TelegramBaseNode should inherit CredentialAwareMixin."""
        from casare_rpa.nodes.messaging.telegram.telegram_base import TelegramBaseNode

        assert issubclass(TelegramBaseNode, CredentialAwareMixin)

    @pytest.mark.asyncio
    async def test_telegram_get_bot_token_uses_credential_resolution(
        self, mock_context
    ):
        """_get_bot_token should use credential resolution."""
        from casare_rpa.nodes.messaging.telegram.telegram_base import TelegramBaseNode

        # Create a concrete subclass for testing
        class TestTelegramNode(TelegramBaseNode):
            def _define_ports(self):
                """Required by BaseNode."""
                pass

            async def _execute_telegram(self, context, client):
                return {"success": True}

        node = TestTelegramNode("test_id")
        node.config = {"bot_token": "direct-bot-token"}

        token = await node._get_bot_token(mock_context)

        assert token == "direct-bot-token"


# =============================================================================
# Test Email Node Integration
# =============================================================================


class TestEmailNodeCredentials:
    """Test credential resolution in Email nodes."""

    def test_send_email_node_uses_mixin(self):
        """SendEmailNode should inherit CredentialAwareMixin."""
        from casare_rpa.nodes.email_nodes import SendEmailNode

        assert issubclass(SendEmailNode, CredentialAwareMixin)

    def test_read_emails_node_uses_mixin(self):
        """ReadEmailsNode should inherit CredentialAwareMixin."""
        from casare_rpa.nodes.email_nodes import ReadEmailsNode

        assert issubclass(ReadEmailsNode, CredentialAwareMixin)
