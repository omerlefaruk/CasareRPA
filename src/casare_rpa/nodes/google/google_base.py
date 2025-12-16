"""
CasareRPA - Google Workspace Base Node

Abstract base class for all Google Workspace nodes with shared functionality.
Provides common credential handling, client management, and error handling.
Uses CredentialAwareMixin for vault-integrated credential resolution.

This module provides:
- GoogleBaseNode: Abstract base for all Google Workspace nodes
- Service-specific base classes: GmailBaseNode, DocsBaseNode, SheetsBaseNode, DriveBaseNode
- Shared PropertyDef constants for credential configuration
- Utility functions for OAuth scope management
"""

from __future__ import annotations

import os
from abc import abstractmethod
from typing import Any, List, Optional

from loguru import logger

from casare_rpa.domain.credentials import CredentialAwareMixin
from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.value_objects.types import (
    DataType,
    ExecutionResult,
    NodeStatus,
)
from casare_rpa.domain.schemas.property_schema import PropertyDef
from casare_rpa.domain.schemas.property_types import PropertyType
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
from casare_rpa.infrastructure.resources.gmail_client import (
    GmailClient,
    GmailConfig,
)


# =============================================================================
# Shared PropertyDef Constants for Google Nodes
# =============================================================================

# Credential-related properties (shared across all Google nodes)
GOOGLE_CREDENTIAL_NAME = PropertyDef(
    name="credential_name",
    type=PropertyType.STRING,
    default="",
    label="Credential Name",
    tooltip="Name of stored Google credential in vault/credential manager",
    tab="connection",
    required=False,
)

GOOGLE_ACCESS_TOKEN = PropertyDef(
    name="access_token",
    type=PropertyType.STRING,
    default="",
    label="Access Token",
    tooltip="OAuth2 access token (alternative to credential_name)",
    tab="connection",
    required=False,
)

GOOGLE_REFRESH_TOKEN = PropertyDef(
    name="refresh_token",
    type=PropertyType.STRING,
    default="",
    label="Refresh Token",
    tooltip="OAuth2 refresh token for automatic token renewal",
    tab="connection",
    required=False,
)

GOOGLE_SERVICE_ACCOUNT_JSON = PropertyDef(
    name="service_account_json",
    type=PropertyType.JSON,
    default=None,
    label="Service Account JSON",
    tooltip="Service account credentials JSON for server-to-server auth",
    tab="connection",
    required=False,
)

# Common advanced properties
GOOGLE_TIMEOUT = PropertyDef(
    name="timeout",
    type=PropertyType.FLOAT,
    default=30.0,
    label="Timeout (seconds)",
    tooltip="Request timeout in seconds",
    tab="advanced",
    required=False,
)

GOOGLE_MAX_RETRIES = PropertyDef(
    name="max_retries",
    type=PropertyType.INTEGER,
    default=3,
    label="Max Retries",
    tooltip="Maximum number of retry attempts on failure",
    tab="advanced",
    required=False,
)

# All credential-related properties as a tuple for use in @properties
GOOGLE_CREDENTIAL_PROPERTIES = (
    GOOGLE_CREDENTIAL_NAME,
    GOOGLE_ACCESS_TOKEN,
    GOOGLE_REFRESH_TOKEN,
    GOOGLE_SERVICE_ACCOUNT_JSON,
)

# Common Google properties including advanced
GOOGLE_COMMON_PROPERTIES = (
    *GOOGLE_CREDENTIAL_PROPERTIES,
    GOOGLE_TIMEOUT,
    GOOGLE_MAX_RETRIES,
)


@properties()
@node(category="google")
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

    # @category: google
    # @requires: none
    # @ports: none -> none

    # Subclasses must define required OAuth2 scopes
    REQUIRED_SCOPES: List[str] = []

    def __init__(self, node_id: str, name: str = "Google Node", **kwargs: Any) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self._client: Optional[GoogleAPIClient] = None

    def _define_common_input_ports(self) -> None:
        """Define standard Google input ports.

        NOTE: Credential-related input ports (access_token, credential_name, etc.)
        are NOT defined here. Credential selection is handled by
        NodeGoogleCredentialWidget in the visual layer, which sets the
        credential_id property. The GoogleBaseNode._get_credentials() method
        resolves credentials from the credential_id or falls back to other sources.
        """
        # No credential ports - handled by visual layer's credential picker
        pass

    def _define_common_output_ports(self) -> None:
        """Define standard Google output ports."""
        self.add_output_port(
            "success",
            DataType.BOOLEAN,
            label="Success",
        )
        self.add_output_port(
            "error",
            DataType.STRING,
            label="Error Message",
        )
        self.add_output_port(
            "error_code",
            DataType.INTEGER,
            label="Error Code",
        )

    def _resolve_value(self, context: ExecutionContext, value: Any) -> Any:
        """Resolve a value that may contain variable references."""
        if value is None:
            return None
        if hasattr(context, "resolve_value"):
            return context.resolve_value(value)
        return value

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

        # Get credentials (with auto-refresh via GoogleOAuthManager)
        credentials = await self._get_credentials(context)

        # Get credential_id for OAuth auto-refresh at client level
        cred_id = self.get_parameter("credential_id") or self.config.get(
            "credential_id"
        )
        if cred_id:
            cred_id = context.resolve_value(cred_id)

        # Create client config with credential_id for auto-refresh
        config = GoogleConfig(
            credentials=credentials,
            credential_id=cred_id,  # Enable auto-refresh at client level
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
        Get Google credentials with automatic OAuth token refresh.

        Uses GoogleOAuthManager for automatic token refresh when credentials
        are stored in the credential store. Falls back to other sources if
        credential_id is not available.

        Resolution order:
        1. GoogleOAuthManager with auto-refresh (via credential_id from picker widget)
        2. Vault lookup (via credential_id)
        3. Direct parameters (access_token, refresh_token) - for programmatic use
        4. Service account JSON
        5. Context variables (google_access_token, google_refresh_token)
        6. Environment variables (GOOGLE_ACCESS_TOKEN, GOOGLE_APPLICATION_CREDENTIALS)

        Args:
            context: Execution context

        Returns:
            GoogleCredentials object with valid (auto-refreshed) access token

        Raises:
            GoogleAuthError: If no credentials found
        """
        # DEBUG: Log credential_id from config (using INFO so it shows in logs)
        cred_id_from_config = self.config.get("credential_id")
        cred_id_from_param = self.get_parameter("credential_id")
        logger.info(
            f"Google credential lookup - config: {cred_id_from_config}, param: {cred_id_from_param}"
        )

        # Get credential_id (from picker widget or direct config)
        cred_id = self.get_parameter("credential_id") or self.config.get(
            "credential_id"
        )
        if cred_id:
            cred_id = context.resolve_value(cred_id)

        # PRIMARY PATH: Use GoogleOAuthManager for automatic token refresh
        # This is the recommended path for stored credentials
        if cred_id:
            try:
                from casare_rpa.infrastructure.security.google_oauth import (
                    get_google_access_token,
                    GoogleOAuthManager,
                    TokenRefreshError,
                    InvalidCredentialError,
                )
                from casare_rpa.infrastructure.security.credential_store import (
                    get_credential_store,
                )

                # Get valid access token (auto-refreshes if expired)
                logger.info(f"Using GoogleOAuthManager for auto-refresh: {cred_id}")
                access_token = await get_google_access_token(cred_id)

                # Get full credential data for client_id/secret/refresh_token
                store = get_credential_store()
                data = store.get_credential(cred_id)

                if data:
                    # Parse expiry timestamp
                    expiry = None
                    if data.get("token_expiry"):
                        from datetime import datetime

                        try:
                            exp_str = data["token_expiry"]
                            if exp_str.endswith("Z"):
                                exp_str = exp_str[:-1] + "+00:00"
                            exp_dt = datetime.fromisoformat(exp_str)
                            expiry = exp_dt.timestamp()
                        except Exception:
                            pass

                    logger.info(f"Credential auto-refresh successful: {cred_id}")
                    return GoogleCredentials(
                        access_token=access_token,  # Fresh token from OAuth manager
                        refresh_token=data.get("refresh_token"),
                        client_id=data.get("client_id"),
                        client_secret=data.get("client_secret"),
                        scopes=self.REQUIRED_SCOPES,
                        expiry=expiry,
                    )

            except (TokenRefreshError, InvalidCredentialError) as e:
                logger.warning(f"OAuth auto-refresh failed for {cred_id}: {e}")
                # Fall through to try other methods
            except ImportError:
                logger.debug("GoogleOAuthManager not available, using fallback")
            except Exception as e:
                logger.warning(f"Unexpected error in OAuth auto-refresh: {e}")
                # Fall through to try other methods

        # FALLBACK: Try vault/credential resolution using CredentialAwareMixin
        # The credential_id is set by NodeGoogleCredentialWidget in the visual layer
        access_token = await self.resolve_credential(
            context,
            credential_name_param="credential_id",  # From picker widget
            direct_param="access_token",  # Fallback for programmatic use
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
            cred_name = self.get_parameter("credential_id")
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

            cred_name = self.get_parameter("credential_id")
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

        # Try credential_store directly (without OAuth manager - last resort)
        try:
            from casare_rpa.infrastructure.security.credential_store import (
                get_credential_store,
            )

            store = get_credential_store()
            if cred_id:
                # Get decrypted credential data by ID
                data = store.get_credential(cred_id)
                if data and data.get("access_token"):
                    logger.warning(
                        f"Using credential from store WITHOUT auto-refresh: {cred_id}"
                    )

                    # Parse expiry timestamp
                    expiry = None
                    if data.get("token_expiry"):
                        from datetime import datetime

                        try:
                            exp_str = data["token_expiry"]
                            if exp_str.endswith("Z"):
                                exp_str = exp_str[:-1] + "+00:00"
                            exp_dt = datetime.fromisoformat(exp_str)
                            expiry = exp_dt.timestamp()
                        except Exception:
                            pass

                    return GoogleCredentials(
                        access_token=data.get("access_token"),
                        refresh_token=data.get("refresh_token"),
                        client_id=data.get("client_id"),
                        client_secret=data.get("client_secret"),
                        scopes=self.REQUIRED_SCOPES,
                        expiry=expiry,
                    )
        except ImportError:
            pass
        except Exception as e:
            logger.debug(f"Credential store lookup failed: {e}")

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


def get_calendar_scopes(readonly: bool = False) -> List[str]:
    """Get Calendar OAuth2 scopes."""
    return (
        SCOPES.get("calendar_readonly", []) if readonly else SCOPES.get("calendar", [])
    )


# =============================================================================
# Service-Specific Base Classes
# =============================================================================


@properties()
@node(category="google")
class GmailBaseNode(GoogleBaseNode):
    """
    Base class for Gmail nodes.

    Extends GoogleBaseNode with Gmail-specific functionality:
    - GmailClient for async email operations
    - Gmail-specific scopes (gmail.modify)
    - Email message handling utilities

    Subclasses implement _execute_gmail() instead of _execute_google().
    The _execute_gmail method receives a GmailClient instance.
    """

    # @category: google
    # @requires: none
    # @ports: none -> none

    # Gmail requires modify scope for most operations
    REQUIRED_SCOPES: List[str] = SCOPES.get("gmail", [])
    SERVICE_NAME = "gmail"
    SERVICE_VERSION = "v1"

    async def _execute_google(
        self,
        context: ExecutionContext,
        client: GoogleAPIClient,
    ) -> ExecutionResult:
        """
        Delegate to Gmail-specific execution with GmailClient.

        Creates a GmailClient using the access token from credentials
        and delegates to the _execute_gmail method.
        """
        # Get access token from the credentials in client config
        access_token = client.config.credentials.access_token
        if not access_token:
            raise GoogleAuthError("No access token available for Gmail operations")

        # Create GmailClient with the access token
        gmail_config = GmailConfig(
            access_token=access_token,
            timeout=client.config.timeout or 30.0,
        )
        gmail_client = GmailClient(gmail_config)

        try:
            async with gmail_client:
                return await self._execute_gmail(context, gmail_client)
        finally:
            # Ensure cleanup even if gmail client is already closed
            pass

    @abstractmethod
    async def _execute_gmail(
        self,
        context: ExecutionContext,
        client: GmailClient,
    ) -> ExecutionResult:
        """
        Execute the Gmail operation.

        Args:
            context: Execution context
            client: GmailClient instance for async Gmail API operations

        Returns:
            Execution result dictionary
        """
        ...


@properties()
@node(category="google")
class DocsBaseNode(GoogleBaseNode):
    """
    Base class for Google Docs nodes.

    Extends GoogleBaseNode with Docs-specific functionality:
    - Docs API service access (docs/v1)
    - Docs-specific scopes
    - Document manipulation utilities

    Subclasses implement _execute_docs() instead of _execute_google().
    """

    # @category: google
    # @requires: none
    # @ports: none -> none

    REQUIRED_SCOPES: List[str] = SCOPES.get("docs", [])
    SERVICE_NAME = "docs"
    SERVICE_VERSION = "v1"

    def _define_document_id_port(self) -> None:
        """Define document_id input port for Docs operations."""
        self.add_input_port(
            "document_id",
            DataType.STRING,
            label="Document ID",
            required=True,
        )

    def _get_document_id(self, context: ExecutionContext) -> str:
        """Get document ID from parameter, resolving variables."""
        doc_id = self.get_parameter("document_id")
        if hasattr(context, "resolve_value"):
            doc_id = context.resolve_value(doc_id)
        return str(doc_id) if doc_id else ""

    async def _execute_google(
        self,
        context: ExecutionContext,
        client: GoogleAPIClient,
    ) -> ExecutionResult:
        """Delegate to Docs-specific execution."""
        service = await client.get_service(self.SERVICE_NAME, self.SERVICE_VERSION)
        return await self._execute_docs(context, client, service)

    @abstractmethod
    async def _execute_docs(
        self,
        context: ExecutionContext,
        client: GoogleAPIClient,
        service: Any,
    ) -> ExecutionResult:
        """
        Execute the Google Docs operation.

        Args:
            context: Execution context
            client: Google API client
            service: Docs API service object

        Returns:
            Execution result dictionary
        """
        ...


@properties()
@node(category="google")
class SheetsBaseNode(GoogleBaseNode):
    """
    Base class for Google Sheets nodes.

    Extends GoogleBaseNode with Sheets-specific functionality:
    - Sheets API service access (sheets/v4)
    - Sheets-specific scopes
    - A1 notation utilities for cell/range addressing

    Subclasses implement _execute_sheets() instead of _execute_google().
    """

    # @category: google
    # @requires: none
    # @ports: none -> none

    REQUIRED_SCOPES: List[str] = SCOPES.get("sheets", [])
    SERVICE_NAME = "sheets"
    SERVICE_VERSION = "v4"

    def _define_spreadsheet_id_port(self) -> None:
        """Define spreadsheet_id input port for Sheets operations."""
        self.add_input_port(
            "spreadsheet_id",
            DataType.STRING,
            label="Spreadsheet ID",
            required=True,
        )

    def _define_sheet_name_port(self) -> None:
        """Define sheet_name input port."""
        self.add_input_port(
            "sheet_name",
            DataType.STRING,
            label="Sheet Name",
            required=False,
        )

    def _get_spreadsheet_id(self, context: ExecutionContext) -> str:
        """Get spreadsheet ID from parameter, resolving variables."""
        sheet_id = self.get_parameter("spreadsheet_id")
        if hasattr(context, "resolve_value"):
            sheet_id = context.resolve_value(sheet_id)
        return str(sheet_id) if sheet_id else ""

    def _get_sheet_name(
        self, context: ExecutionContext, default: str = "Sheet1"
    ) -> str:
        """Get sheet name from parameter, resolving variables."""
        name = self.get_parameter("sheet_name") or self.get_input_value("sheet_name")
        if hasattr(context, "resolve_value") and name:
            name = context.resolve_value(name)
        return str(name) if name else default

    # A1 notation utilities
    @staticmethod
    def column_letter_to_index(column: str) -> int:
        """Convert column letter(s) to 0-based index. A=0, B=1, ..., Z=25, AA=26."""
        result = 0
        for char in column.upper():
            result = result * 26 + (ord(char) - ord("A") + 1)
        return result - 1

    @staticmethod
    def index_to_column_letter(index: int) -> str:
        """Convert 0-based index to column letter(s). 0=A, 1=B, ..., 25=Z, 26=AA."""
        result = ""
        index += 1
        while index > 0:
            index, remainder = divmod(index - 1, 26)
            result = chr(ord("A") + remainder) + result
        return result

    @classmethod
    def cell_to_indices(cls, cell: str) -> tuple:
        """Convert A1 notation cell to (row, col) 0-based indices."""
        import re

        match = re.match(r"([A-Z]+)(\d+)", cell.upper())
        if not match:
            raise ValueError(f"Invalid cell reference: {cell}")
        col = cls.column_letter_to_index(match.group(1))
        row = int(match.group(2)) - 1
        return row, col

    @classmethod
    def indices_to_cell(cls, row: int, col: int) -> str:
        """Convert (row, col) 0-based indices to A1 notation."""
        return f"{cls.index_to_column_letter(col)}{row + 1}"

    @classmethod
    def build_a1_range(
        cls,
        sheet_name: Optional[str] = None,
        start_cell: Optional[str] = None,
        end_cell: Optional[str] = None,
        start_row: Optional[int] = None,
        start_col: Optional[int] = None,
        end_row: Optional[int] = None,
        end_col: Optional[int] = None,
    ) -> str:
        """Build A1 notation range string from cells or indices."""
        if start_cell:
            cell_ref = start_cell
            if end_cell:
                cell_ref = f"{start_cell}:{end_cell}"
        elif start_row is not None and start_col is not None:
            start = cls.indices_to_cell(start_row, start_col)
            if end_row is not None and end_col is not None:
                end = cls.indices_to_cell(end_row, end_col)
                cell_ref = f"{start}:{end}"
            else:
                cell_ref = start
        else:
            cell_ref = "A1"

        if sheet_name:
            if " " in sheet_name or "!" in sheet_name or "'" in sheet_name:
                safe_name = sheet_name.replace("'", "''")
                sheet_name = f"'{safe_name}'"
            return f"{sheet_name}!{cell_ref}"
        return cell_ref

    async def _execute_google(
        self,
        context: ExecutionContext,
        client: GoogleAPIClient,
    ) -> ExecutionResult:
        """Delegate to Sheets-specific execution."""
        service = await client.get_service(self.SERVICE_NAME, self.SERVICE_VERSION)
        return await self._execute_sheets(context, client, service)

    @abstractmethod
    async def _execute_sheets(
        self,
        context: ExecutionContext,
        client: GoogleAPIClient,
        service: Any,
    ) -> ExecutionResult:
        """
        Execute the Google Sheets operation.

        Args:
            context: Execution context
            client: Google API client
            service: Sheets API service object

        Returns:
            Execution result dictionary
        """
        ...


@properties()
@node(category="google")
class DriveBaseNode(GoogleBaseNode):
    """
    Base class for Google Drive nodes.

    Extends GoogleBaseNode with Drive-specific functionality:
    - Uses GoogleDriveClient (aiohttp-based) for Drive API access
    - Drive-specific scopes
    - File/folder handling utilities

    Subclasses implement _execute_drive() instead of _execute_google().
    """

    # @category: google
    # @requires: none
    # @ports: none -> none

    REQUIRED_SCOPES: List[str] = SCOPES.get("drive", [])
    SERVICE_NAME = "drive"
    SERVICE_VERSION = "v3"

    def _define_file_id_port(self) -> None:
        """Define file_id input port for Drive operations."""
        self.add_input_port(
            "file_id",
            DataType.STRING,
            label="File ID",
            required=True,
        )

    def _get_file_id(self, context: ExecutionContext) -> str:
        """Get file ID from parameter, resolving variables."""
        file_id = self.get_parameter("file_id") or self.get_input_value("file_id")
        if hasattr(context, "resolve_value") and file_id:
            file_id = context.resolve_value(file_id)
        return str(file_id) if file_id else ""

    @staticmethod
    def get_mime_type_from_extension(file_path: str) -> str:
        """Get MIME type from file extension."""
        from pathlib import Path
        import mimetypes

        ext = Path(file_path).suffix.lower()
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type or "application/octet-stream"

    @staticmethod
    def is_google_workspace_type(mime_type: str) -> bool:
        """Check if MIME type is a Google Workspace document."""
        return mime_type.startswith("application/vnd.google-apps.")

    async def _execute_google(
        self,
        context: ExecutionContext,
        client: GoogleAPIClient,
    ) -> ExecutionResult:
        """Delegate to Drive-specific execution using GoogleDriveClient."""
        from casare_rpa.infrastructure.resources.google_drive_client import (
            GoogleDriveClient,
            DriveConfig,
        )

        # Ensure token is fresh (will refresh if expired)
        access_token = await client._ensure_valid_token()

        # Create GoogleDriveClient with fresh token
        drive_client = GoogleDriveClient(
            config=DriveConfig(
                access_token=access_token,
            )
        )

        try:
            return await self._execute_drive(context, drive_client)
        finally:
            await drive_client.close()

    @abstractmethod
    async def _execute_drive(
        self,
        context: ExecutionContext,
        client: "GoogleDriveClient",
    ) -> ExecutionResult:
        """
        Execute the Google Drive operation.

        Args:
            context: Execution context
            client: GoogleDriveClient (aiohttp-based async client)

        Returns:
            Execution result dictionary
        """
        ...


@properties()
@node(category="google")
class CalendarBaseNode(GoogleBaseNode):
    """
    Base class for Google Calendar nodes.

    Extends GoogleBaseNode with Calendar-specific functionality:
    - Calendar API service access (calendar/v3)
    - Calendar-specific scopes
    - Event/calendar handling utilities

    Subclasses implement _execute_calendar() instead of _execute_google().
    """

    # @category: google
    # @requires: none
    # @ports: none -> none

    REQUIRED_SCOPES: List[str] = SCOPES.get("calendar", [])
    SERVICE_NAME = "calendar"
    SERVICE_VERSION = "v3"

    def _define_calendar_id_port(self) -> None:
        """Define calendar_id input port."""
        self.add_input_port(
            "calendar_id",
            DataType.STRING,
            label="Calendar ID",
            required=False,
        )

    def _get_calendar_id(
        self, context: ExecutionContext, default: str = "primary"
    ) -> str:
        """Get calendar ID from parameter, resolving variables."""
        cal_id = self.get_parameter("calendar_id") or self.get_input_value(
            "calendar_id"
        )
        if hasattr(context, "resolve_value") and cal_id:
            cal_id = context.resolve_value(cal_id)
        return str(cal_id) if cal_id else default

    async def _execute_google(
        self,
        context: ExecutionContext,
        client: GoogleAPIClient,
    ) -> ExecutionResult:
        """Delegate to Calendar-specific execution."""
        service = await client.get_service(self.SERVICE_NAME, self.SERVICE_VERSION)
        return await self._execute_calendar(context, client, service)

    @abstractmethod
    async def _execute_calendar(
        self,
        context: ExecutionContext,
        client: GoogleAPIClient,
        service: Any,
    ) -> ExecutionResult:
        """
        Execute the Google Calendar operation.

        Args:
            context: Execution context
            client: Google API client
            service: Calendar API service object

        Returns:
            Execution result dictionary
        """
        ...


__all__ = [
    # Base classes
    "GoogleBaseNode",
    "GmailBaseNode",
    "DocsBaseNode",
    "SheetsBaseNode",
    "DriveBaseNode",
    "CalendarBaseNode",
    # Client and credentials
    "GoogleAPIClient",
    "GoogleCredentials",
    # Errors
    "GoogleAPIError",
    "GoogleAuthError",
    "GoogleQuotaError",
    # Scopes
    "SCOPES",
    "get_gmail_scopes",
    "get_sheets_scopes",
    "get_docs_scopes",
    "get_drive_scopes",
    "get_calendar_scopes",
    # PropertyDef constants
    "GOOGLE_CREDENTIAL_NAME",
    "GOOGLE_ACCESS_TOKEN",
    "GOOGLE_REFRESH_TOKEN",
    "GOOGLE_SERVICE_ACCOUNT_JSON",
    "GOOGLE_TIMEOUT",
    "GOOGLE_MAX_RETRIES",
    "GOOGLE_CREDENTIAL_PROPERTIES",
    "GOOGLE_COMMON_PROPERTIES",
]
