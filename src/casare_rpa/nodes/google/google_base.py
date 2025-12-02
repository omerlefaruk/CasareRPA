"""
CasareRPA - Google Workspace Base Node

Abstract base class for all Google Workspace nodes with shared functionality.
Provides common credential handling, client management, and error handling.
Uses CredentialAwareMixin for vault-integrated credential resolution.
"""

from __future__ import annotations

import os
from abc import abstractmethod
from typing import Any, List, Optional

from loguru import logger

from casare_rpa.domain.credentials import CredentialAwareMixin
from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.value_objects.types import (
    DataType,
    ExecutionResult,
    NodeStatus,
    PortType,
)
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.infrastructure.resources.google_client import (
    GoogleAPIClient,
    GoogleConfig,
    GoogleCredentials,
    GoogleAPIError,
    GoogleAuthError,
    GoogleQuotaError,
    SCOPES,
)


class GoogleBaseNode(CredentialAwareMixin, BaseNode):
    """
    Abstract base class for Google Workspace nodes.

    Provides common functionality:
    - Google API client access with OAuth2 authentication
    - Credential retrieval from vault/credentials manager/environment
    - Standard output ports (success, error)
    - Error handling with quota awareness

    Uses CredentialAwareMixin for unified credential resolution:
    1. Vault lookup (via credential_name parameter)
    2. Direct parameters (access_token, refresh_token)
    3. Service account JSON
    4. Context variables (google_access_token, google_refresh_token)
    5. Environment variables (GOOGLE_ACCESS_TOKEN, GOOGLE_APPLICATION_CREDENTIALS)

    Subclasses implement:
    - REQUIRED_SCOPES: List of OAuth2 scopes needed
    - _execute_google(): Specific API operation

    Example:
        class GmailSendNode(GoogleBaseNode):
            REQUIRED_SCOPES = SCOPES["gmail_send"]

            async def _execute_google(
                self,
                context: ExecutionContext,
                client: GoogleAPIClient,
            ) -> ExecutionResult:
                service = await client.get_service("gmail")
                # ... use Gmail API ...
    """

    # Subclasses must define required OAuth2 scopes
    REQUIRED_SCOPES: List[str] = []

    def __init__(self, node_id: str, name: str = "Google Node", **kwargs: Any) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self._client: Optional[GoogleAPIClient] = None

    def _define_common_input_ports(self) -> None:
        """Define standard Google input ports for credentials."""
        # Credential name for looking up in credential manager
        self.add_input_port(
            "credential_name",
            PortType.INPUT,
            DataType.STRING,
            label="Credential Name",
            required=False,
        )
        # Direct access token (alternative to credential_name)
        self.add_input_port(
            "access_token",
            PortType.INPUT,
            DataType.STRING,
            label="Access Token",
            required=False,
        )
        # Refresh token for automatic token refresh
        self.add_input_port(
            "refresh_token",
            PortType.INPUT,
            DataType.STRING,
            label="Refresh Token",
            required=False,
        )
        # Service account JSON for service-to-service auth
        self.add_input_port(
            "service_account_json",
            PortType.INPUT,
            DataType.DICT,
            label="Service Account JSON",
            required=False,
        )

    def _define_common_output_ports(self) -> None:
        """Define standard Google output ports."""
        self.add_output_port(
            "success",
            PortType.OUTPUT,
            DataType.BOOLEAN,
            label="Success",
        )
        self.add_output_port(
            "error",
            PortType.OUTPUT,
            DataType.STRING,
            label="Error Message",
        )
        self.add_output_port(
            "error_code",
            PortType.OUTPUT,
            DataType.INTEGER,
            label="Error Code",
        )

    async def _get_google_client(self, context: ExecutionContext) -> GoogleAPIClient:
        """
        Get or create Google API client from context.

        Attempts to get credentials in this order:
        1. Existing client in context resources
        2. Direct access_token parameter
        3. Credential manager lookup by credential_name
        4. Service account JSON
        5. Environment variables

        Args:
            context: Execution context

        Returns:
            Configured and authenticated GoogleAPIClient

        Raises:
            GoogleAuthError: If no valid credentials found
        """
        # Check for existing client in context
        if hasattr(context, "resources"):
            if "google_client" in context.resources:
                return context.resources["google_client"]

        # Get credentials
        credentials = await self._get_credentials(context)

        # Create client config
        config = GoogleConfig(
            credentials=credentials,
            timeout=30.0,
            max_retries=3,
        )

        # Create and authenticate client
        client = GoogleAPIClient(config)
        await client.authenticate(scopes=self.REQUIRED_SCOPES)

        # Store in context for reuse
        if hasattr(context, "resources"):
            context.resources["google_client"] = client

        self._client = client
        return client

    async def _get_credentials(self, context: ExecutionContext) -> GoogleCredentials:
        """
        Get Google credentials from various sources using unified credential resolution.

        Resolution order:
        1. Vault lookup (via credential_name parameter)
        2. Direct parameters (access_token, refresh_token)
        3. Service account JSON
        4. Context variables (google_access_token, google_refresh_token)
        5. Environment variables (GOOGLE_ACCESS_TOKEN, GOOGLE_APPLICATION_CREDENTIALS)

        Args:
            context: Execution context

        Returns:
            GoogleCredentials object

        Raises:
            GoogleAuthError: If no credentials found
        """
        # Try vault/credential resolution first using CredentialAwareMixin
        access_token = await self.resolve_credential(
            context,
            credential_name_param="credential_name",
            direct_param="access_token",
            env_var="GOOGLE_ACCESS_TOKEN",
            context_var="google_access_token",
            credential_field="access_token",
            required=False,
        )

        if access_token:
            # Also try to get refresh token from same credential
            refresh_token = await self.resolve_credential(
                context,
                credential_name_param="credential_name",
                direct_param="refresh_token",
                env_var="GOOGLE_REFRESH_TOKEN",
                context_var="google_refresh_token",
                credential_field="refresh_token",
                required=False,
            )

            # Try to get client_id and client_secret from vault credential
            client_id = None
            client_secret = None

            # Check vault credential for OAuth metadata
            cred_name = self.get_parameter("credential_name")
            if cred_name:
                try:
                    provider = await context.get_credential_provider()
                    cred = await provider.get_credential(cred_name)
                    if cred and hasattr(cred, "data"):
                        client_id = cred.data.get("client_id")
                        client_secret = cred.data.get("client_secret")
                except Exception:
                    pass

            if not client_id:
                client_id = os.environ.get("GOOGLE_CLIENT_ID")
            if not client_secret:
                client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")

            logger.debug("Using access token from credential resolution")
            return GoogleCredentials(
                access_token=access_token,
                refresh_token=refresh_token,
                client_id=client_id,
                client_secret=client_secret,
                scopes=self.REQUIRED_SCOPES,
            )

        # Try legacy credential manager for backwards compatibility
        try:
            from casare_rpa.utils.security.credential_manager import credential_manager

            cred_name = self.get_parameter("credential_name")
            if cred_name:
                cred_name = context.resolve_value(cred_name)
                cred = credential_manager.get_credential(cred_name)
                if cred and cred.access_token:
                    logger.debug(f"Using legacy credential from manager: {cred_name}")
                    return GoogleCredentials(
                        access_token=cred.access_token,
                        refresh_token=cred.refresh_token,
                        client_id=cred.metadata.get("client_id"),
                        client_secret=cred.metadata.get("client_secret"),
                        scopes=self.REQUIRED_SCOPES,
                    )

            # Try default credential names in legacy system
            for name in ["google", "google_workspace", "gcloud", "default_google"]:
                try:
                    cred = credential_manager.get_credential(name)
                    if cred and cred.access_token:
                        logger.debug(f"Using legacy default credential: {name}")
                        return GoogleCredentials(
                            access_token=cred.access_token,
                            refresh_token=cred.refresh_token,
                            client_id=cred.metadata.get("client_id"),
                            client_secret=cred.metadata.get("client_secret"),
                            scopes=self.REQUIRED_SCOPES,
                        )
                except Exception:
                    continue

        except ImportError:
            pass
        except Exception as e:
            logger.debug(f"Legacy credential manager lookup failed: {e}")

        # Try service account JSON
        service_account = self.get_parameter("service_account_json")
        if service_account:
            if isinstance(service_account, str):
                import json

                service_account = json.loads(service_account)
            logger.debug("Using service account JSON")
            return GoogleCredentials.from_service_account(service_account)

        # Check for service account file in environment
        sa_file = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        if sa_file and os.path.exists(sa_file):
            import json

            with open(sa_file, "r") as f:
                sa_info = json.load(f)
            logger.debug(f"Using service account file: {sa_file}")
            return GoogleCredentials.from_service_account(sa_info)

        raise GoogleAuthError(
            "No Google credentials found. Provide access_token, credential_name, "
            "service_account_json, or set GOOGLE_ACCESS_TOKEN environment variable."
        )

    def _set_error_outputs(self, error_msg: str, error_code: int = 0) -> None:
        """Set output values for error case."""
        self.set_output_value("success", False)
        self.set_output_value("error", error_msg)
        self.set_output_value("error_code", error_code)

    def _set_success_outputs(self, **data: Any) -> None:
        """
        Set output values for successful response.

        Args:
            **data: Additional output port values to set
        """
        self.set_output_value("success", True)
        self.set_output_value("error", "")
        self.set_output_value("error_code", 0)

        # Set any additional outputs
        for port_name, value in data.items():
            if port_name in self.output_ports:
                self.set_output_value(port_name, value)

    @abstractmethod
    async def _execute_google(
        self,
        context: ExecutionContext,
        client: GoogleAPIClient,
    ) -> ExecutionResult:
        """
        Execute the Google API operation.

        Subclasses must implement this method with their specific API logic.

        Args:
            context: Execution context
            client: Authenticated Google API client

        Returns:
            Execution result dictionary
        """
        ...

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Execute the Google node with client management and error handling."""
        self.status = NodeStatus.RUNNING

        try:
            # Get Google client
            client = await self._get_google_client(context)

            async with client:
                # Execute specific Google operation
                result = await self._execute_google(context, client)

            if result.get("success", False):
                self.status = NodeStatus.SUCCESS
            else:
                self.status = NodeStatus.ERROR

            return result

        except GoogleQuotaError as e:
            error_msg = str(e)
            logger.warning(f"Google API quota exceeded: {error_msg}")
            self._set_error_outputs(error_msg, error_code=429)
            self.status = NodeStatus.ERROR
            return {
                "success": False,
                "error": error_msg,
                "error_code": 429,
                "retry_after": e.retry_after,
                "next_nodes": [],
            }

        except GoogleAuthError as e:
            error_msg = str(e)
            logger.error(f"Google authentication error: {error_msg}")
            self._set_error_outputs(error_msg, error_code=401)
            self.status = NodeStatus.ERROR
            return {
                "success": False,
                "error": error_msg,
                "error_code": 401,
                "next_nodes": [],
            }

        except GoogleAPIError as e:
            error_msg = str(e)
            error_code = e.error_code or 500
            logger.error(f"Google API error: {error_msg}")
            self._set_error_outputs(error_msg, error_code=error_code)
            self.status = NodeStatus.ERROR
            return {
                "success": False,
                "error": error_msg,
                "error_code": error_code,
                "next_nodes": [],
            }

        except Exception as e:
            error_msg = f"Google operation error: {str(e)}"
            logger.error(error_msg)
            self._set_error_outputs(error_msg)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg, "next_nodes": []}


# Scope helper functions for subclasses
def get_gmail_scopes(readonly: bool = False) -> List[str]:
    """Get Gmail OAuth2 scopes."""
    return SCOPES["gmail_readonly"] if readonly else SCOPES["gmail"]


def get_sheets_scopes(readonly: bool = False) -> List[str]:
    """Get Sheets OAuth2 scopes."""
    return SCOPES["sheets_readonly"] if readonly else SCOPES["sheets"]


def get_docs_scopes(readonly: bool = False) -> List[str]:
    """Get Docs OAuth2 scopes."""
    return SCOPES["docs_readonly"] if readonly else SCOPES["docs"]


def get_drive_scopes(readonly: bool = False, file_only: bool = False) -> List[str]:
    """Get Drive OAuth2 scopes."""
    if file_only:
        return SCOPES["drive_file"]
    return SCOPES["drive_readonly"] if readonly else SCOPES["drive"]


__all__ = [
    "GoogleBaseNode",
    "GoogleAPIClient",
    "GoogleCredentials",
    "GoogleAPIError",
    "GoogleAuthError",
    "GoogleQuotaError",
    "SCOPES",
    "get_gmail_scopes",
    "get_sheets_scopes",
    "get_docs_scopes",
    "get_drive_scopes",
]
