"""
CasareRPA - WhatsApp Base Node

Abstract base class for all WhatsApp nodes with shared functionality.
Uses CredentialAwareMixin for vault-integrated credential resolution.
"""

from __future__ import annotations
from casare_rpa.domain.decorators import node, properties


from abc import abstractmethod
from typing import Any, Optional

from loguru import logger

from casare_rpa.domain.credentials import CredentialAwareMixin
from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.value_objects.types import (
    DataType,
    ExecutionResult,
    NodeStatus,
)
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.infrastructure.resources.whatsapp_client import (
    WhatsAppClient,
    WhatsAppConfig,
    WhatsAppAPIError,
)


@properties()
@node(category="messaging")
class WhatsAppBaseNode(CredentialAwareMixin, BaseNode):
    """
    Abstract base class for WhatsApp nodes.

    Provides common functionality:
    - WhatsApp client access
    - Access token configuration from vault/credentials/env
    - Error handling
    - Standard output ports

    Uses CredentialAwareMixin for unified credential resolution:
    1. Vault lookup (via credential_name parameter)
    2. Direct parameter (access_token, phone_number_id)
    3. Context variable (whatsapp_access_token, whatsapp_phone_number_id)
    4. Environment variables (WHATSAPP_ACCESS_TOKEN, WHATSAPP_PHONE_NUMBER_ID)

    Subclasses implement _execute_whatsapp() for specific operations.
    """

    # @category: integration
    # @requires: none
    # @ports: none -> none

    def __init__(self, node_id: str, name: str = "WhatsApp Node", **kwargs: Any) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self._client: Optional[WhatsAppClient] = None

    def _define_common_input_ports(self) -> None:
        """Define standard WhatsApp input ports."""
        self.add_input_port("access_token", DataType.STRING, required=False)
        self.add_input_port("phone_number_id", DataType.STRING, required=False)
        self.add_input_port("credential_name", DataType.STRING, required=False)
        self.add_input_port("to", DataType.STRING, required=True)

    def _define_common_output_ports(self) -> None:
        """Define standard WhatsApp output ports."""
        self.add_output_port("message_id", DataType.STRING)
        self.add_output_port("phone_number", DataType.STRING)
        self.add_output_port("success", DataType.BOOLEAN)
        self.add_output_port("error", DataType.STRING)

    async def _get_whatsapp_client(self, context: ExecutionContext) -> WhatsAppClient:
        """
        Get or create WhatsApp client from context.

        Args:
            context: Execution context

        Returns:
            Configured WhatsApp client instance
        """
        # Check if client exists in context
        if hasattr(context, "resources") and "whatsapp" in context.resources:
            return context.resources["whatsapp"]

        # Get credentials
        access_token = await self._get_access_token(context)
        phone_number_id = await self._get_phone_number_id(context)

        if not access_token:
            raise WhatsAppAPIError("No WhatsApp access token configured")
        if not phone_number_id:
            raise WhatsAppAPIError("No WhatsApp phone number ID configured")

        # Get optional business account ID
        business_account_id = self.get_parameter("business_account_id")

        # Create client
        config = WhatsAppConfig(
            access_token=access_token,
            phone_number_id=phone_number_id,
            business_account_id=business_account_id,
        )
        client = WhatsAppClient(config)

        # Store in context for reuse
        if hasattr(context, "resources"):
            context.resources["whatsapp"] = client

        self._client = client
        return client

    async def _get_access_token(self, context: ExecutionContext) -> Optional[str]:
        """
        Get access token using unified credential resolution.

        Resolution order:
        1. Vault lookup (via credential_name parameter)
        2. Direct parameter (access_token)
        3. Context variable (whatsapp_access_token)
        4. Environment variable (WHATSAPP_ACCESS_TOKEN)

        Args:
            context: ExecutionContext with credential provider

        Returns:
            Access token string or None
        """
        # Use CredentialAwareMixin's resolve_credential method
        token = await self.resolve_credential(
            context,
            credential_name_param="credential_name",
            direct_param="access_token",
            env_var="WHATSAPP_ACCESS_TOKEN",
            context_var="whatsapp_access_token",
            credential_field="access_token",
            required=False,
        )

        if token:
            return token

        # Fallback: try legacy credential manager for backwards compatibility
        try:
            from casare_rpa.utils.security.credential_manager import credential_manager

            cred_name = self.get_parameter("credential_name")
            if cred_name:
                cred = credential_manager.get_whatsapp_credential(cred_name)
                if cred and cred.access_token:
                    logger.debug(f"Using legacy credential manager: {cred_name}")
                    return cred.access_token

            # Try default credential names in legacy system
            for name in ["whatsapp", "whatsapp_business", "default_whatsapp"]:
                cred = credential_manager.get_whatsapp_credential(name)
                if cred and cred.access_token:
                    logger.debug(f"Using legacy default credential: {name}")
                    return cred.access_token
        except ImportError:
            # Legacy credential manager not available
            pass
        except Exception as e:
            logger.debug(f"Legacy credential manager lookup failed: {e}")

        return None

    async def _get_phone_number_id(self, context: ExecutionContext) -> Optional[str]:
        """
        Get phone number ID using unified credential resolution.

        Resolution order:
        1. Vault lookup (via credential_name parameter)
        2. Direct parameter (phone_number_id)
        3. Context variable (whatsapp_phone_number_id)
        4. Environment variable (WHATSAPP_PHONE_NUMBER_ID)

        Args:
            context: ExecutionContext with credential provider

        Returns:
            Phone number ID string or None
        """
        # Use CredentialAwareMixin's resolve_credential method
        phone_id = await self.resolve_credential(
            context,
            credential_name_param="credential_name",
            direct_param="phone_number_id",
            env_var="WHATSAPP_PHONE_NUMBER_ID",
            context_var="whatsapp_phone_number_id",
            credential_field="phone_number_id",
            required=False,
        )

        if phone_id:
            return phone_id

        # Fallback: try legacy credential manager for backwards compatibility
        try:
            from casare_rpa.utils.security.credential_manager import credential_manager

            cred_name = self.get_parameter("credential_name")
            if cred_name:
                cred = credential_manager.get_whatsapp_credential(cred_name)
                if cred and cred.phone_number_id:
                    logger.debug(f"Using legacy credential for phone_number_id: {cred_name}")
                    return cred.phone_number_id

            # Try default credential names in legacy system
            for name in ["whatsapp", "whatsapp_business", "default_whatsapp"]:
                cred = credential_manager.get_whatsapp_credential(name)
                if cred and cred.phone_number_id:
                    logger.debug(f"Using legacy default phone_number_id: {name}")
                    return cred.phone_number_id
        except ImportError:
            # Legacy credential manager not available
            pass
        except Exception as e:
            logger.debug(f"Legacy credential manager lookup failed: {e}")

        return None

    def _get_recipient(self, context: ExecutionContext) -> str:
        """Get recipient phone number from parameter, resolving variables."""
        to = self.get_parameter("to")
        return str(to)

    def _set_error_outputs(self, error_msg: str) -> None:
        """Set output values for error case."""
        self.set_output_value("success", False)
        self.set_output_value("error", error_msg)
        self.set_output_value("message_id", "")
        self.set_output_value("phone_number", "")

    def _set_success_outputs(
        self,
        message_id: str,
        phone_number: str,
    ) -> None:
        """Set output values for successful response."""
        self.set_output_value("success", True)
        self.set_output_value("error", "")
        self.set_output_value("message_id", message_id)
        self.set_output_value("phone_number", phone_number)

    @abstractmethod
    async def _execute_whatsapp(
        self,
        context: ExecutionContext,
        client: WhatsAppClient,
    ) -> ExecutionResult:
        """
        Execute the WhatsApp operation.

        Args:
            context: Execution context
            client: WhatsApp client

        Returns:
            Execution result
        """
        ...

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Execute the WhatsApp node."""
        self.status = NodeStatus.RUNNING

        try:
            # Get WhatsApp client
            client = await self._get_whatsapp_client(context)

            async with client:
                # Execute specific WhatsApp operation
                result = await self._execute_whatsapp(context, client)

            if result.get("success", False):
                self.status = NodeStatus.SUCCESS
            else:
                self.status = NodeStatus.ERROR

            return result

        except WhatsAppAPIError as e:
            error_msg = str(e)
            logger.error(f"WhatsApp API error: {error_msg}")
            self._set_error_outputs(error_msg)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg, "next_nodes": []}

        except Exception as e:
            error_msg = f"WhatsApp error: {str(e)}"
            logger.error(error_msg)
            self._set_error_outputs(error_msg)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg, "next_nodes": []}


__all__ = ["WhatsAppBaseNode"]
