"""
Tests for AWS Secrets Manager Provider.

These tests mock boto3 to avoid requiring actual AWS credentials.
"""

import pytest
import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from casare_rpa.infrastructure.security.vault_client import (
    VaultConfig,
    VaultBackend,
    SecretNotFoundError,
    VaultConnectionError,
    VaultAuthenticationError,
    SecretAccessDeniedError,
    CredentialType,
)


# Skip all tests if boto3 not available
pytest.importorskip("boto3")


from casare_rpa.infrastructure.security.providers.aws_secrets import (
    AWSSecretsManagerProvider,
    _check_boto3_available,
)


@pytest.fixture
def mock_secret_response():
    """Create a mock get_secret_value response."""
    return {
        "ARN": "arn:aws:secretsmanager:us-east-1:123456789:secret:test-secret-abc123",
        "Name": "test-secret",
        "VersionId": "version-1",
        "SecretString": json.dumps({"username": "testuser", "password": "testpass"}),
        "VersionStages": ["AWSCURRENT"],
        "CreatedDate": datetime(2024, 1, 1, tzinfo=timezone.utc),
    }


@pytest.fixture
def mock_describe_response():
    """Create a mock describe_secret response."""
    return {
        "ARN": "arn:aws:secretsmanager:us-east-1:123456789:secret:test-secret-abc123",
        "Name": "test-secret",
        "CreatedDate": datetime(2024, 1, 1, tzinfo=timezone.utc),
        "LastChangedDate": datetime(2024, 6, 1, tzinfo=timezone.utc),
        "RotationEnabled": False,
        "Tags": [{"Key": "env", "Value": "test"}],
    }


@pytest.fixture
def aws_config():
    """Create AWS Secrets Manager configuration."""
    return VaultConfig(
        backend=VaultBackend.AWS_SECRETS_MANAGER,
        aws_region="us-east-1",
    )


@pytest.fixture
def aws_explicit_creds_config():
    """Create AWS config with explicit credentials."""
    from pydantic import SecretStr

    return VaultConfig(
        backend=VaultBackend.AWS_SECRETS_MANAGER,
        aws_region="us-east-1",
        aws_access_key_id="AKIAIOSFODNN7EXAMPLE",
        aws_secret_access_key=SecretStr("wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"),
    )


@pytest.fixture
def mock_boto3_client():
    """Create a mock boto3 client."""
    client = MagicMock()
    client.list_secrets.return_value = {"SecretList": []}
    return client


class TestAWSSecretsManagerProvider:
    """Test AWS Secrets Manager provider."""

    def test_init_requires_boto3(self, aws_config):
        """Provider initializes when boto3 is available."""
        provider = AWSSecretsManagerProvider(aws_config)
        assert provider._config == aws_config
        assert provider._client is None

    @pytest.mark.asyncio
    async def test_connect_with_region(self, aws_config):
        """Connect creates client with specified region."""
        provider = AWSSecretsManagerProvider(aws_config)

        with patch(
            "casare_rpa.infrastructure.security.providers.aws_secrets._boto3"
        ) as mock_boto3:
            mock_session = MagicMock()
            mock_client = MagicMock()
            mock_client.list_secrets.return_value = {"SecretList": []}
            mock_session.client.return_value = mock_client
            mock_boto3.Session.return_value = mock_session

            await provider.connect()

            mock_boto3.Session.assert_called_once_with(region_name="us-east-1")
            mock_session.client.assert_called_once()
            assert provider._client is not None

    @pytest.mark.asyncio
    async def test_connect_with_explicit_credentials(self, aws_explicit_creds_config):
        """Connect uses explicit credentials when provided."""
        provider = AWSSecretsManagerProvider(aws_explicit_creds_config)

        with patch(
            "casare_rpa.infrastructure.security.providers.aws_secrets._boto3"
        ) as mock_boto3:
            mock_session = MagicMock()
            mock_client = MagicMock()
            mock_client.list_secrets.return_value = {"SecretList": []}
            mock_session.client.return_value = mock_client
            mock_boto3.Session.return_value = mock_session

            await provider.connect()

            # Verify client was called with credentials
            call_kwargs = mock_session.client.call_args[1]
            assert call_kwargs["aws_access_key_id"] == "AKIAIOSFODNN7EXAMPLE"
            assert (
                call_kwargs["aws_secret_access_key"]
                == "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
            )

    @pytest.mark.asyncio
    async def test_connect_with_profile(self):
        """Connect uses profile when specified."""
        config = VaultConfig(
            backend=VaultBackend.AWS_SECRETS_MANAGER,
            aws_profile="my-profile",
        )
        provider = AWSSecretsManagerProvider(config)

        with patch(
            "casare_rpa.infrastructure.security.providers.aws_secrets._boto3"
        ) as mock_boto3:
            mock_session = MagicMock()
            mock_client = MagicMock()
            mock_client.list_secrets.return_value = {"SecretList": []}
            mock_session.client.return_value = mock_client
            mock_boto3.Session.return_value = mock_session

            await provider.connect()

            mock_boto3.Session.assert_called_once_with(profile_name="my-profile")

    @pytest.mark.asyncio
    async def test_disconnect(self, aws_config, mock_boto3_client):
        """Disconnect clears client and session."""
        provider = AWSSecretsManagerProvider(aws_config)
        provider._client = mock_boto3_client
        provider._session = MagicMock()

        await provider.disconnect()

        assert provider._client is None
        assert provider._session is None

    @pytest.mark.asyncio
    async def test_is_connected_false_when_no_client(self, aws_config):
        """is_connected returns False when not connected."""
        provider = AWSSecretsManagerProvider(aws_config)
        assert await provider.is_connected() is False

    @pytest.mark.asyncio
    async def test_get_secret_success(
        self,
        aws_config,
        mock_boto3_client,
        mock_secret_response,
        mock_describe_response,
    ):
        """Get secret returns data and metadata."""
        provider = AWSSecretsManagerProvider(aws_config)
        provider._client = mock_boto3_client
        mock_boto3_client.get_secret_value.return_value = mock_secret_response
        mock_boto3_client.describe_secret.return_value = mock_describe_response

        result = await provider.get_secret("test-secret")

        assert result.data == {"username": "testuser", "password": "testpass"}
        assert result.metadata.path == "test-secret"
        assert "arn" in result.metadata.custom_metadata
        mock_boto3_client.get_secret_value.assert_called_once_with(
            SecretId="test-secret"
        )

    @pytest.mark.asyncio
    async def test_get_secret_plain_text(
        self, aws_config, mock_boto3_client, mock_describe_response
    ):
        """Get secret handles plain text values."""
        provider = AWSSecretsManagerProvider(aws_config)
        provider._client = mock_boto3_client

        mock_boto3_client.get_secret_value.return_value = {
            "ARN": "arn:aws:secretsmanager:us-east-1:123:secret:plain",
            "Name": "plain-secret",
            "VersionId": "v1",
            "SecretString": "plain-text-value",
            "VersionStages": ["AWSCURRENT"],
        }
        mock_boto3_client.describe_secret.return_value = mock_describe_response

        result = await provider.get_secret("plain-secret")

        assert result.data == {"value": "plain-text-value"}

    @pytest.mark.asyncio
    async def test_get_secret_binary(
        self, aws_config, mock_boto3_client, mock_describe_response
    ):
        """Get secret handles binary values."""
        provider = AWSSecretsManagerProvider(aws_config)
        provider._client = mock_boto3_client

        mock_boto3_client.get_secret_value.return_value = {
            "ARN": "arn:aws:secretsmanager:us-east-1:123:secret:binary",
            "Name": "binary-secret",
            "VersionId": "v1",
            "SecretBinary": b"binary data",
            "VersionStages": ["AWSCURRENT"],
        }
        mock_boto3_client.describe_secret.return_value = mock_describe_response

        result = await provider.get_secret("binary-secret")

        assert "binary" in result.data

    @pytest.mark.asyncio
    async def test_get_secret_not_found(self, aws_config, mock_boto3_client):
        """Get secret raises SecretNotFoundError when not found."""
        provider = AWSSecretsManagerProvider(aws_config)
        provider._client = mock_boto3_client

        from botocore.exceptions import ClientError

        mock_boto3_client.get_secret_value.side_effect = ClientError(
            {"Error": {"Code": "ResourceNotFoundException", "Message": "Not found"}},
            "GetSecretValue",
        )

        with pytest.raises(SecretNotFoundError, match="not found"):
            await provider.get_secret("missing-secret")

    @pytest.mark.asyncio
    async def test_get_secret_access_denied(self, aws_config, mock_boto3_client):
        """Get secret raises SecretAccessDeniedError on AccessDenied."""
        provider = AWSSecretsManagerProvider(aws_config)
        provider._client = mock_boto3_client

        from botocore.exceptions import ClientError

        mock_boto3_client.get_secret_value.side_effect = ClientError(
            {"Error": {"Code": "AccessDeniedException", "Message": "Denied"}},
            "GetSecretValue",
        )

        with pytest.raises(SecretAccessDeniedError):
            await provider.get_secret("forbidden-secret")

    @pytest.mark.asyncio
    async def test_put_secret_create_new(self, aws_config, mock_boto3_client):
        """Put secret creates new secret when it doesn't exist."""
        provider = AWSSecretsManagerProvider(aws_config)
        provider._client = mock_boto3_client

        mock_boto3_client.create_secret.return_value = {
            "ARN": "arn:aws:secretsmanager:us-east-1:123:secret:new-secret",
            "Name": "new-secret",
            "VersionId": "v1",
        }

        result = await provider.put_secret(
            "new-secret",
            {"username": "user", "password": "pass"},
            CredentialType.USERNAME_PASSWORD,
        )

        assert result.path == "new-secret"
        mock_boto3_client.create_secret.assert_called_once()

    @pytest.mark.asyncio
    async def test_put_secret_update_existing(self, aws_config, mock_boto3_client):
        """Put secret updates existing secret."""
        provider = AWSSecretsManagerProvider(aws_config)
        provider._client = mock_boto3_client

        from botocore.exceptions import ClientError

        mock_boto3_client.create_secret.side_effect = ClientError(
            {"Error": {"Code": "ResourceExistsException", "Message": "Exists"}},
            "CreateSecret",
        )
        mock_boto3_client.put_secret_value.return_value = {
            "ARN": "arn:aws:secretsmanager:us-east-1:123:secret:existing",
            "Name": "existing",
            "VersionId": "v2",
        }

        result = await provider.put_secret(
            "existing",
            {"key": "updated-value"},
            CredentialType.API_KEY,
        )

        assert result.path == "existing"
        mock_boto3_client.put_secret_value.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_secret_success(self, aws_config, mock_boto3_client):
        """Delete secret schedules deletion."""
        provider = AWSSecretsManagerProvider(aws_config)
        provider._client = mock_boto3_client

        result = await provider.delete_secret("to-delete")

        assert result is True
        mock_boto3_client.delete_secret.assert_called_once_with(
            SecretId="to-delete",
            RecoveryWindowInDays=7,
        )

    @pytest.mark.asyncio
    async def test_delete_secret_not_found(self, aws_config, mock_boto3_client):
        """Delete secret returns False when not found."""
        provider = AWSSecretsManagerProvider(aws_config)
        provider._client = mock_boto3_client

        from botocore.exceptions import ClientError

        mock_boto3_client.delete_secret.side_effect = ClientError(
            {"Error": {"Code": "ResourceNotFoundException", "Message": "Not found"}},
            "DeleteSecret",
        )

        result = await provider.delete_secret("missing")

        assert result is False

    @pytest.mark.asyncio
    async def test_list_secrets(self, aws_config, mock_boto3_client):
        """List secrets returns secret names."""
        provider = AWSSecretsManagerProvider(aws_config)
        provider._client = mock_boto3_client

        paginator = MagicMock()
        paginator.paginate.return_value = [
            {
                "SecretList": [
                    {"Name": "secret-1"},
                    {"Name": "secret-2"},
                ]
            }
        ]
        mock_boto3_client.get_paginator.return_value = paginator

        result = await provider.list_secrets("")

        assert result == ["secret-1", "secret-2"]

    @pytest.mark.asyncio
    async def test_list_secrets_with_prefix(self, aws_config, mock_boto3_client):
        """List secrets filters by prefix."""
        provider = AWSSecretsManagerProvider(aws_config)
        provider._client = mock_boto3_client

        paginator = MagicMock()
        paginator.paginate.return_value = [
            {
                "SecretList": [
                    {"Name": "app/secret-1"},
                    {"Name": "app/secret-2"},
                    {"Name": "other/secret"},
                ]
            }
        ]
        mock_boto3_client.get_paginator.return_value = paginator

        result = await provider.list_secrets("app/")

        assert result == ["app/secret-1", "app/secret-2"]

    @pytest.mark.asyncio
    async def test_rotate_secret_with_lambda(self, aws_config, mock_boto3_client):
        """Rotate secret triggers Lambda rotation."""
        provider = AWSSecretsManagerProvider(aws_config)
        provider._client = mock_boto3_client

        mock_boto3_client.describe_secret.return_value = {
            "RotationEnabled": True,
            "RotationLambdaARN": "arn:aws:lambda:us-east-1:123:function:rotate",
            "CreatedDate": datetime.now(timezone.utc),
            "LastChangedDate": datetime.now(timezone.utc),
            "Tags": [],
        }
        mock_boto3_client.get_secret_value.return_value = {
            "ARN": "arn",
            "Name": "rotated",
            "VersionId": "v2",
            "SecretString": "{}",
            "VersionStages": ["AWSCURRENT"],
        }

        result = await provider.rotate_secret("rotated-secret")

        mock_boto3_client.rotate_secret.assert_called_once_with(
            SecretId="rotated-secret"
        )
        assert result.path == "rotated-secret"

    @pytest.mark.asyncio
    async def test_rotate_secret_manual(self, aws_config, mock_boto3_client):
        """Rotate secret generates new values when no Lambda."""
        provider = AWSSecretsManagerProvider(aws_config)
        provider._client = mock_boto3_client

        mock_boto3_client.describe_secret.return_value = {
            "RotationEnabled": False,
            "CreatedDate": datetime.now(timezone.utc),
            "LastChangedDate": datetime.now(timezone.utc),
            "Tags": [],
        }
        mock_boto3_client.get_secret_value.return_value = {
            "ARN": "arn",
            "Name": "manual",
            "VersionId": "v1",
            "SecretString": json.dumps({"password": "old-pass"}),
            "VersionStages": ["AWSCURRENT"],
        }

        from botocore.exceptions import ClientError

        mock_boto3_client.create_secret.side_effect = ClientError(
            {"Error": {"Code": "ResourceExistsException", "Message": "Exists"}},
            "CreateSecret",
        )
        mock_boto3_client.put_secret_value.return_value = {
            "ARN": "arn",
            "Name": "manual",
            "VersionId": "v2",
        }

        result = await provider.rotate_secret("manual-secret")

        # Should have called put_secret_value with new password
        mock_boto3_client.put_secret_value.assert_called_once()

    def test_infer_credential_type(self, aws_config):
        """Credential type inference from data keys."""
        provider = AWSSecretsManagerProvider(aws_config)

        assert (
            provider._infer_credential_type({"username": "u", "password": "p"})
            == CredentialType.USERNAME_PASSWORD
        )

        assert (
            provider._infer_credential_type({"api_key": "key123"})
            == CredentialType.API_KEY
        )

        assert (
            provider._infer_credential_type(
                {"access_key_id": "AKIA", "secret_access_key": "secret"}
            )
            == CredentialType.AWS_CREDENTIALS
        )

        assert (
            provider._infer_credential_type({"custom": "value"})
            == CredentialType.CUSTOM
        )

    @pytest.mark.asyncio
    async def test_restore_secret(
        self, aws_config, mock_boto3_client, mock_describe_response
    ):
        """Restore secret cancels scheduled deletion."""
        provider = AWSSecretsManagerProvider(aws_config)
        provider._client = mock_boto3_client

        mock_boto3_client.describe_secret.return_value = mock_describe_response
        mock_boto3_client.get_secret_value.return_value = {
            "ARN": "arn",
            "Name": "restored",
            "VersionId": "v1",
            "SecretString": "{}",
            "VersionStages": ["AWSCURRENT"],
        }

        result = await provider.restore_secret("deleted-secret")

        mock_boto3_client.restore_secret.assert_called_once_with(
            SecretId="deleted-secret"
        )
        assert result.path == "deleted-secret"

    @pytest.mark.asyncio
    async def test_force_delete_secret(self, aws_config, mock_boto3_client):
        """Force delete permanently removes secret."""
        provider = AWSSecretsManagerProvider(aws_config)
        provider._client = mock_boto3_client

        result = await provider.force_delete_secret("permanent-delete")

        assert result is True
        mock_boto3_client.delete_secret.assert_called_once_with(
            SecretId="permanent-delete",
            ForceDeleteWithoutRecovery=True,
        )

    @pytest.mark.asyncio
    async def test_get_rotation_status(self, aws_config, mock_boto3_client):
        """Get rotation status returns configuration."""
        provider = AWSSecretsManagerProvider(aws_config)
        provider._client = mock_boto3_client

        mock_boto3_client.describe_secret.return_value = {
            "RotationEnabled": True,
            "RotationLambdaARN": "arn:aws:lambda:us-east-1:123:function:rotate",
            "RotationRules": {"AutomaticallyAfterDays": 30},
            "LastRotatedDate": datetime(2024, 5, 1, tzinfo=timezone.utc),
            "NextRotationDate": datetime(2024, 6, 1, tzinfo=timezone.utc),
        }

        result = await provider.get_rotation_status("rotated-secret")

        assert result["rotation_enabled"] is True
        assert "rotation_lambda_arn" in result
        assert result["rotation_rules"]["AutomaticallyAfterDays"] == 30


class TestAWSSecretsManagerProviderEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_not_connected_raises_error(self, aws_config):
        """Operations fail when not connected."""
        provider = AWSSecretsManagerProvider(aws_config)

        with pytest.raises(VaultConnectionError, match="Not connected"):
            await provider.get_secret("any")

    @pytest.mark.asyncio
    async def test_custom_endpoint_url(self):
        """Custom endpoint URL for LocalStack/testing."""
        config = VaultConfig(
            backend=VaultBackend.AWS_SECRETS_MANAGER,
            aws_region="us-east-1",
            aws_endpoint_url="http://localhost:4566",
        )

        provider = AWSSecretsManagerProvider(config)

        with patch(
            "casare_rpa.infrastructure.security.providers.aws_secrets._boto3"
        ) as mock_boto3:
            mock_session = MagicMock()
            mock_client = MagicMock()
            mock_client.list_secrets.return_value = {"SecretList": []}
            mock_session.client.return_value = mock_client
            mock_boto3.Session.return_value = mock_session

            await provider.connect()

            call_kwargs = mock_session.client.call_args[1]
            assert call_kwargs["endpoint_url"] == "http://localhost:4566"

    def test_boto3_availability_check(self):
        """boto3 availability check returns bool."""
        result = _check_boto3_available()
        assert isinstance(result, bool)
        assert result is True  # We imported it, so it's available
