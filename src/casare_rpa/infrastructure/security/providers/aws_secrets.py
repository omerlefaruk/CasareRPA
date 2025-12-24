"""
AWS Secrets Manager Provider Implementation.

Supports:
- Environment variable credentials (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
- IAM Role authentication (for EC2/Lambda)
- Profile-based credentials (~/.aws/credentials)
- Secret versioning
- Secret rotation triggers
- Cross-region replication
"""

import json
from datetime import UTC, datetime
from typing import Any

from loguru import logger

from casare_rpa.infrastructure.security.vault_client import (
    CredentialType,
    SecretAccessDeniedError,
    SecretMetadata,
    SecretNotFoundError,
    SecretValue,
    VaultAuthenticationError,
    VaultConfig,
    VaultConnectionError,
    VaultProvider,
)

# Lazy load boto3
_BOTO3_AVAILABLE: bool | None = None
_boto3 = None
_ClientError = None


def _check_boto3_available() -> bool:
    """Check if boto3 is available and import modules."""
    global _BOTO3_AVAILABLE, _boto3, _ClientError

    if _BOTO3_AVAILABLE is not None:
        return _BOTO3_AVAILABLE

    try:
        import boto3
        from botocore.exceptions import ClientError

        _boto3 = boto3
        _ClientError = ClientError
        _BOTO3_AVAILABLE = True
    except ImportError:
        _BOTO3_AVAILABLE = False

    return _BOTO3_AVAILABLE


class AWSSecretsManagerProvider(VaultProvider):
    """
    AWS Secrets Manager provider using boto3 client.

    Supports multiple authentication methods:
    - Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
    - IAM Role (for EC2/Lambda/ECS)
    - Profile from ~/.aws/credentials

    Usage:
        config = VaultConfig(
            backend=VaultBackend.AWS_SECRETS_MANAGER,
            aws_region="us-east-1",
        )
        provider = AWSSecretsManagerProvider(config)
        await provider.connect()
    """

    def __init__(self, config: VaultConfig) -> None:
        """
        Initialize AWS Secrets Manager provider.

        Args:
            config: Vault configuration with AWS settings

        Raises:
            ImportError: If boto3 library is not installed
        """
        if not _check_boto3_available():
            raise ImportError(
                "AWS Secrets Manager support requires boto3 library. "
                "Install with: pip install boto3"
            )

        self._config = config
        self._client = None
        self._session = None

    async def connect(self) -> None:
        """Connect to AWS Secrets Manager."""
        try:
            # Build session options
            session_kwargs: dict[str, Any] = {}

            if self._config.aws_region:
                session_kwargs["region_name"] = self._config.aws_region

            if self._config.aws_profile:
                session_kwargs["profile_name"] = self._config.aws_profile

            # Create session
            self._session = _boto3.Session(**session_kwargs)

            # Build client options
            client_kwargs: dict[str, Any] = {}

            if self._config.aws_region:
                client_kwargs["region_name"] = self._config.aws_region

            # Explicit credentials override environment/IAM role
            if self._config.aws_access_key_id and self._config.aws_secret_access_key:
                client_kwargs["aws_access_key_id"] = self._config.aws_access_key_id
                client_kwargs["aws_secret_access_key"] = (
                    self._config.aws_secret_access_key.get_secret_value()
                )
                if self._config.aws_session_token:
                    client_kwargs["aws_session_token"] = (
                        self._config.aws_session_token.get_secret_value()
                    )

            # Endpoint URL override (for LocalStack, testing)
            if self._config.aws_endpoint_url:
                client_kwargs["endpoint_url"] = self._config.aws_endpoint_url

            # Create Secrets Manager client
            self._client = self._session.client("secretsmanager", **client_kwargs)

            # Verify connection with a simple API call
            try:
                self._client.list_secrets(MaxResults=1)
            except _ClientError as e:
                error_code = e.response.get("Error", {}).get("Code", "")
                if error_code in (
                    "UnauthorizedAccess",
                    "AccessDenied",
                    "InvalidSignature",
                ):
                    raise VaultAuthenticationError(f"AWS authentication failed: {e}") from e
                # Other errors might just mean empty secrets, which is ok
                if error_code not in ("ResourceNotFoundException",):
                    raise

            region = self._config.aws_region or "default"
            logger.info(f"Connected to AWS Secrets Manager in region {region}")

        except VaultAuthenticationError:
            raise
        except _ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code in ("UnauthorizedAccess", "AccessDenied"):
                raise VaultAuthenticationError(f"AWS authentication failed: {e}") from e
            raise VaultConnectionError(f"Failed to connect to AWS Secrets Manager: {e}") from e
        except Exception as e:
            raise VaultConnectionError(f"Failed to connect to AWS Secrets Manager: {e}") from e

    async def disconnect(self) -> None:
        """Disconnect from AWS Secrets Manager."""
        if self._client:
            self._client = None
        if self._session:
            self._session = None
        logger.info("Disconnected from AWS Secrets Manager")

    async def is_connected(self) -> bool:
        """Check if connected to AWS Secrets Manager."""
        if not self._client:
            return False
        try:
            self._client.list_secrets(MaxResults=1)
            return True
        except Exception:
            return False

    def _ensure_connected(self):
        """Ensure client is connected and return it."""
        if not self._client:
            raise VaultConnectionError("Not connected to AWS Secrets Manager")
        return self._client

    async def get_secret(self, path: str, version: int | None = None) -> SecretValue:
        """
        Get secret from AWS Secrets Manager.

        Args:
            path: Secret name or ARN
            version: Optional version stage or version ID

        Returns:
            SecretValue with data and metadata
        """
        client = self._ensure_connected()

        try:
            # Build request
            request: dict[str, Any] = {"SecretId": path}

            if version:
                # In AWS, version can be a stage (AWSCURRENT, AWSPREVIOUS) or version ID
                request["VersionId"] = str(version)

            response = client.get_secret_value(**request)

            # Parse secret value
            if "SecretString" in response:
                try:
                    data = json.loads(response["SecretString"])
                except json.JSONDecodeError:
                    # Plain text secret
                    data = {"value": response["SecretString"]}
            elif "SecretBinary" in response:
                # Binary secret
                import base64

                data = {"binary": base64.b64encode(response["SecretBinary"]).decode()}
            else:
                data = {}

            # Get additional metadata
            describe_response = client.describe_secret(SecretId=path)

            # Determine credential type
            credential_type = self._infer_credential_type(data)

            # Parse rotation info
            rotation_enabled = describe_response.get("RotationEnabled", False)
            next_rotation = describe_response.get("NextRotationDate")

            metadata = SecretMetadata(
                path=path,
                version=1,
                created_at=describe_response.get("CreatedDate", datetime.now(UTC)),
                updated_at=describe_response.get("LastChangedDate", datetime.now(UTC)),
                credential_type=credential_type,
                custom_metadata={
                    "arn": response.get("ARN"),
                    "version_id": response.get("VersionId"),
                    "version_stages": response.get("VersionStages", []),
                    "rotation_enabled": rotation_enabled,
                    "next_rotation_date": str(next_rotation) if next_rotation else None,
                    "tags": {tag["Key"]: tag["Value"] for tag in describe_response.get("Tags", [])},
                },
            )

            return SecretValue(data=data, metadata=metadata)

        except _ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "ResourceNotFoundException":
                raise SecretNotFoundError(f"Secret not found: {path}", path=path) from e
            if error_code in ("AccessDeniedException", "UnauthorizedAccess"):
                raise SecretAccessDeniedError(f"Access denied to secret: {path}", path=path) from e
            logger.error(f"Failed to read secret {path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to read secret {path}: {e}")
            raise

    async def put_secret(
        self,
        path: str,
        data: dict[str, Any],
        credential_type: CredentialType = CredentialType.CUSTOM_KIND,
        metadata: dict[str, Any] | None = None,
    ) -> SecretMetadata:
        """Store secret in AWS Secrets Manager."""
        client = self._ensure_connected()

        try:
            # Serialize data
            secret_string = json.dumps(data)

            # Extract tags from metadata
            tags = []
            if metadata and "tags" in metadata:
                tags = [{"Key": k, "Value": v} for k, v in metadata["tags"].items()]

            # Try to create or update
            try:
                # Try to create first
                response = client.create_secret(
                    Name=path,
                    SecretString=secret_string,
                    Tags=tags if tags else [],
                    Description=(metadata or {}).get("description", ""),
                )
                logger.debug(f"Created new secret: {path}")

            except _ClientError as e:
                error_code = e.response.get("Error", {}).get("Code", "")
                if error_code == "ResourceExistsException":
                    # Secret exists, update it
                    response = client.put_secret_value(
                        SecretId=path,
                        SecretString=secret_string,
                    )
                    logger.debug(f"Updated existing secret: {path}")
                else:
                    raise

            return SecretMetadata(
                path=path,
                version=1,
                credential_type=credential_type,
                custom_metadata={
                    "arn": response.get("ARN"),
                    "version_id": response.get("VersionId"),
                },
            )

        except _ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code in ("AccessDeniedException", "UnauthorizedAccess"):
                raise SecretAccessDeniedError(f"Access denied writing to: {path}", path=path) from e
            logger.error(f"Failed to write secret {path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to write secret {path}: {e}")
            raise

    async def delete_secret(self, path: str) -> bool:
        """
        Delete secret from AWS Secrets Manager.

        By default, schedules deletion with recovery window.
        Use force_delete in metadata to delete immediately.
        """
        client = self._ensure_connected()

        try:
            # Schedule deletion (can be recovered within 7-30 days)
            client.delete_secret(
                SecretId=path,
                RecoveryWindowInDays=7,  # Minimum recovery window
            )

            logger.info(f"Scheduled secret for deletion: {path}")
            return True

        except _ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "ResourceNotFoundException":
                return False
            if error_code in ("AccessDeniedException", "UnauthorizedAccess"):
                raise SecretAccessDeniedError(f"Access denied deleting: {path}", path=path) from e
            logger.error(f"Failed to delete secret {path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to delete secret {path}: {e}")
            raise

    async def list_secrets(self, path_prefix: str) -> list[str]:
        """List secrets in AWS Secrets Manager."""
        client = self._ensure_connected()

        try:
            secrets = []
            paginator = client.get_paginator("list_secrets")

            # Filter by prefix if provided
            filters = []
            if path_prefix:
                filters.append(
                    {
                        "Key": "name",
                        "Values": [path_prefix],
                    }
                )

            page_iterator = paginator.paginate(
                Filters=filters if filters else [],
            )

            for page in page_iterator:
                for secret in page.get("SecretList", []):
                    name = secret.get("Name", "")
                    # Additional prefix filtering (AWS filter is prefix-based)
                    if not path_prefix or name.startswith(path_prefix):
                        secrets.append(name)

            return sorted(secrets)

        except _ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code in ("AccessDeniedException", "UnauthorizedAccess"):
                raise SecretAccessDeniedError(
                    "Access denied listing secrets", path=path_prefix
                ) from e
            logger.error(f"Failed to list secrets: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to list secrets at {path_prefix}: {e}")
            raise

    async def rotate_secret(self, path: str) -> SecretMetadata:
        """
        Trigger secret rotation in AWS Secrets Manager.

        This triggers the configured Lambda rotation function.
        For secrets without rotation configured, generates new values locally.
        """
        client = self._ensure_connected()

        try:
            # Check if rotation is configured
            describe_response = client.describe_secret(SecretId=path)

            if describe_response.get("RotationEnabled"):
                # Trigger AWS rotation
                client.rotate_secret(SecretId=path)
                logger.info(f"Triggered AWS rotation for: {path}")

                # Get updated secret
                return (await self.get_secret(path)).metadata
            else:
                # Manual rotation - generate new values
                current = await self.get_secret(path)
                new_data = self._generate_rotated_values(
                    current.data, current.metadata.credential_type
                )
                return await self.put_secret(
                    path=path,
                    data=new_data,
                    credential_type=current.metadata.credential_type,
                    metadata=current.metadata.custom_metadata,
                )

        except _ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "ResourceNotFoundException":
                raise SecretNotFoundError(f"Secret not found: {path}", path=path) from e
            logger.error(f"Failed to rotate secret {path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to rotate secret {path}: {e}")
            raise

    def _generate_rotated_values(
        self, current_data: dict[str, Any], cred_type: CredentialType
    ) -> dict[str, Any]:
        """Generate new secret values based on type."""
        import secrets as secrets_module

        new_data = current_data.copy()

        if cred_type == CredentialType.USER_PASS_KIND:
            # Generate new password while keeping username
            new_data["password"] = self._generate_password()
            return new_data
        elif cred_type == CredentialType.API_KEY_KIND:
            for key in ["api_key", "apikey", "key", "token", "value"]:
                if key in new_data:
                    new_data[key] = secrets_module.token_urlsafe(32)
                    break
            else:
                new_data["value"] = secrets_module.token_urlsafe(32)
        else:
            for key in ["password", "secret", "key", "value"]:
                if key in new_data:
                    new_data[key] = self._generate_password()
                    break

        return new_data

    def _generate_password(self, length: int = 32) -> str:
        """Generate a secure random password."""
        import secrets as secrets_module

        alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
        return "".join(secrets_module.choice(alphabet) for _ in range(length))

    def _infer_credential_type(self, data: dict[str, Any]) -> CredentialType:
        """Infer credential type from data keys."""
        keys = set(data.keys())

        if "username" in keys and "password" in keys:
            return CredentialType.USER_PASS_KIND
        if "api_key" in keys or "apikey" in keys:
            return CredentialType.API_KEY_KIND
        if "access_token" in keys or "refresh_token" in keys:
            return CredentialType.OAUTH2_TOKEN_KIND
        if "private_key" in keys or "ssh_key" in keys:
            return CredentialType.SSH_KEY
        if "certificate" in keys or "cert" in keys:
            return CredentialType.CERTIFICATE
        if "connection_string" in keys or "dsn" in keys or "host" in keys:
            return CredentialType.DATABASE_CONNECTION
        if "access_key_id" in keys and "secret_access_key" in keys:
            return CredentialType.AWS_CREDENTIALS
        if "client_id" in keys and "client_secret" in keys:
            return CredentialType.AZURE_CREDENTIALS

        return CredentialType.CUSTOM_KIND

    async def restore_secret(self, path: str) -> SecretMetadata:
        """
        Restore a secret scheduled for deletion.

        Args:
            path: Secret name or ARN to restore

        Returns:
            SecretMetadata for restored secret
        """
        client = self._ensure_connected()

        try:
            client.restore_secret(SecretId=path)
            logger.info(f"Restored secret: {path}")

            # Get updated metadata
            return (await self.get_secret(path)).metadata

        except _ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "ResourceNotFoundException":
                raise SecretNotFoundError(f"Secret not found: {path}", path=path) from e
            logger.error(f"Failed to restore secret {path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to restore secret {path}: {e}")
            raise

    async def force_delete_secret(self, path: str) -> bool:
        """
        Immediately delete a secret without recovery window.

        Warning: This action is irreversible!

        Args:
            path: Secret name or ARN to delete

        Returns:
            True if deleted successfully
        """
        client = self._ensure_connected()

        try:
            client.delete_secret(
                SecretId=path,
                ForceDeleteWithoutRecovery=True,
            )

            logger.warning(f"Force deleted secret (no recovery): {path}")
            return True

        except _ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "ResourceNotFoundException":
                return False
            logger.error(f"Failed to force delete secret {path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to force delete secret {path}: {e}")
            raise

    async def get_rotation_status(self, path: str) -> dict[str, Any]:
        """
        Get rotation status for a secret.

        Args:
            path: Secret name or ARN

        Returns:
            Dictionary with rotation configuration and status
        """
        client = self._ensure_connected()

        try:
            response = client.describe_secret(SecretId=path)

            return {
                "rotation_enabled": response.get("RotationEnabled", False),
                "rotation_lambda_arn": response.get("RotationLambdaARN"),
                "rotation_rules": response.get("RotationRules", {}),
                "last_rotated_date": response.get("LastRotatedDate"),
                "next_rotation_date": response.get("NextRotationDate"),
            }

        except _ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "ResourceNotFoundException":
                raise SecretNotFoundError(f"Secret not found: {path}", path=path) from e
            raise
