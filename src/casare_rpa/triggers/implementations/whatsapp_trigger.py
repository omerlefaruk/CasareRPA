"""
CasareRPA - WhatsApp Trigger

Trigger that fires when a WhatsApp message is received.
Webhook-only mode with Meta/Facebook verify token support.
Uses vault-integrated credential resolution.
"""

import hashlib
import hmac
import os
from typing import Any, Dict, Optional

from loguru import logger

from ..base import BaseTrigger, BaseTriggerConfig, TriggerStatus, TriggerType
from ..registry import register_trigger
from casare_rpa.infrastructure.resources.whatsapp_client import (
    WhatsAppClient,
    WhatsAppConfig,
    WhatsAppAPIError,
)


@register_trigger
class WhatsAppTrigger(BaseTrigger):
    """
    Trigger that responds to WhatsApp messages.

    WhatsApp Business Cloud API only supports webhook mode.
    Requires a public URL that Meta can reach.

    Configuration options:
        access_token: WhatsApp Business Cloud API access token
        phone_number_id: WhatsApp phone number ID
        credential_name: Name of stored credential (alternative)
        verify_token: Webhook verification token (for Meta to verify endpoint)
        app_secret: App secret for signature verification (optional but recommended)
        filter_phone_numbers: Only trigger for specific phone numbers (optional)
        message_types: List of message types to receive (optional)

    Payload variables:
        message_id: ID of the received message
        from_number: Sender's phone number
        phone_number_id: Receiving phone number ID
        text: Message text content (if text message)
        message_type: Type of message (text, image, document, etc.)
        timestamp: Message timestamp
        is_reply: Whether message is a reply
        context: Reply context if is_reply
        raw_message: Full message object from WhatsApp
    """

    trigger_type = TriggerType.WHATSAPP
    display_name = "WhatsApp"
    description = "Trigger workflow when WhatsApp message is received"
    icon = "whatsapp"
    category = "Messaging"

    def __init__(
        self,
        config: BaseTriggerConfig,
        event_callback=None,
    ) -> None:
        super().__init__(config, event_callback)
        self._client: Optional[WhatsAppClient] = None
        self._verify_token: Optional[str] = None

    async def _get_client(self) -> WhatsAppClient:
        """Get or create WhatsApp client."""
        if self._client:
            return self._client

        # Get credentials
        access_token = await self._get_access_token()
        phone_number_id = await self._get_phone_number_id()

        if not access_token:
            raise WhatsAppAPIError("No WhatsApp access token configured")
        if not phone_number_id:
            raise WhatsAppAPIError("No WhatsApp phone number ID configured")

        config = WhatsAppConfig(
            access_token=access_token,
            phone_number_id=phone_number_id,
        )
        self._client = WhatsAppClient(config)
        return self._client

    async def _get_access_token(self) -> Optional[str]:
        """
        Get access token using unified credential resolution.

        Resolution order:
        1. Direct config (access_token)
        2. Vault credential lookup (via credential_name)
        3. Legacy credential manager (for backwards compatibility)
        4. Environment variable (WHATSAPP_ACCESS_TOKEN)

        Returns:
            Access token string or None
        """
        # Try direct config
        token = self.config.config.get("access_token")
        if token:
            return token

        # Try vault credential provider
        cred_name = self.config.config.get("credential_name")
        if cred_name:
            try:
                from casare_rpa.infrastructure.security.credential_provider import (
                    VaultCredentialProvider,
                )

                provider = VaultCredentialProvider()
                await provider.initialize()
                try:
                    cred = await provider.get_credential(cred_name)
                    if cred:
                        access_token = getattr(cred, "access_token", None)
                        if access_token:
                            logger.debug(f"Using vault credential: {cred_name}")
                            return access_token
                        if hasattr(cred, "data") and cred.data:
                            access_token = cred.data.get("access_token")
                            if access_token:
                                logger.debug(
                                    f"Using vault credential data: {cred_name}"
                                )
                                return access_token
                finally:
                    await provider.shutdown()
            except ImportError:
                logger.debug("Vault credential provider not available")
            except Exception as e:
                logger.debug(f"Vault credential lookup failed: {e}")

        # Try legacy credential manager for backwards compatibility
        try:
            from casare_rpa.utils.security.credential_manager import credential_manager

            if cred_name:
                cred = credential_manager.get_whatsapp_credential(cred_name)
                if cred and cred.access_token:
                    logger.debug(f"Using legacy credential: {cred_name}")
                    return cred.access_token

            # Try default names in legacy system
            for name in ["whatsapp", "whatsapp_business", "default_whatsapp"]:
                cred = credential_manager.get_whatsapp_credential(name)
                if cred and cred.access_token:
                    logger.debug(f"Using legacy default credential: {name}")
                    return cred.access_token
        except ImportError:
            pass
        except Exception as e:
            logger.debug(f"Legacy credential lookup failed: {e}")

        # Try environment
        return os.environ.get("WHATSAPP_ACCESS_TOKEN")

    async def _get_phone_number_id(self) -> Optional[str]:
        """
        Get phone number ID using unified credential resolution.

        Resolution order:
        1. Direct config (phone_number_id)
        2. Vault credential lookup (via credential_name)
        3. Legacy credential manager (for backwards compatibility)
        4. Environment variable (WHATSAPP_PHONE_NUMBER_ID)

        Returns:
            Phone number ID string or None
        """
        # Try direct config
        phone_id = self.config.config.get("phone_number_id")
        if phone_id:
            return phone_id

        # Try vault credential provider
        cred_name = self.config.config.get("credential_name")
        if cred_name:
            try:
                from casare_rpa.infrastructure.security.credential_provider import (
                    VaultCredentialProvider,
                )

                provider = VaultCredentialProvider()
                await provider.initialize()
                try:
                    cred = await provider.get_credential(cred_name)
                    if cred:
                        phone_number_id = getattr(cred, "phone_number_id", None)
                        if phone_number_id:
                            logger.debug(
                                f"Using vault credential phone_number_id: {cred_name}"
                            )
                            return phone_number_id
                        if hasattr(cred, "data") and cred.data:
                            phone_number_id = cred.data.get("phone_number_id")
                            if phone_number_id:
                                logger.debug(
                                    f"Using vault credential data phone_number_id: {cred_name}"
                                )
                                return phone_number_id
                finally:
                    await provider.shutdown()
            except ImportError:
                logger.debug("Vault credential provider not available")
            except Exception as e:
                logger.debug(f"Vault credential lookup failed: {e}")

        # Try legacy credential manager for backwards compatibility
        try:
            from casare_rpa.utils.security.credential_manager import credential_manager

            if cred_name:
                cred = credential_manager.get_whatsapp_credential(cred_name)
                if cred and cred.phone_number_id:
                    logger.debug(
                        f"Using legacy credential phone_number_id: {cred_name}"
                    )
                    return cred.phone_number_id

            # Try default names in legacy system
            for name in ["whatsapp", "whatsapp_business", "default_whatsapp"]:
                cred = credential_manager.get_whatsapp_credential(name)
                if cred and cred.phone_number_id:
                    logger.debug(f"Using legacy default phone_number_id: {name}")
                    return cred.phone_number_id
        except ImportError:
            pass
        except Exception as e:
            logger.debug(f"Legacy credential lookup failed: {e}")

        # Try environment
        return os.environ.get("WHATSAPP_PHONE_NUMBER_ID")

    def _get_verify_token(self) -> str:
        """Get verify token for webhook verification."""
        if self._verify_token:
            return self._verify_token

        # Try config
        token = self.config.config.get("verify_token")
        if token:
            self._verify_token = token
            return token

        # Try credential manager
        try:
            from casare_rpa.utils.security.credential_manager import credential_manager

            cred_name = self.config.config.get("credential_name")
            if cred_name:
                cred = credential_manager.get_whatsapp_credential(cred_name)
                if cred and cred.verify_token:
                    self._verify_token = cred.verify_token
                    return cred.verify_token
        except Exception:
            pass

        # Try environment
        token = os.environ.get("WHATSAPP_VERIFY_TOKEN")
        if token:
            self._verify_token = token
            return token

        # Generate one if not set
        import secrets

        self._verify_token = secrets.token_urlsafe(32)
        logger.warning(
            f"No verify_token configured, generated: {self._verify_token[:20]}..."
        )
        return self._verify_token

    async def start(self) -> bool:
        """Start the WhatsApp trigger."""
        self._status = TriggerStatus.STARTING

        try:
            # Verify credentials are available
            client = await self._get_client()

            # Just ensure we can create a client
            logger.info(f"WhatsApp trigger ready for webhooks: {self.config.name}")
            logger.info(f"Webhook URL: {self._get_webhook_url()}")
            logger.info(f"Verify Token: {self._get_verify_token()[:20]}...")

            self._status = TriggerStatus.ACTIVE
            return True

        except Exception as e:
            self._status = TriggerStatus.ERROR
            self._error_message = str(e)
            logger.error(f"Failed to start WhatsApp trigger: {e}")
            return False

    async def stop(self) -> bool:
        """Stop the WhatsApp trigger."""
        self._status = TriggerStatus.STOPPING

        try:
            # Close client if exists
            if self._client:
                await self._client.close()
                self._client = None

            self._status = TriggerStatus.INACTIVE
            logger.info(f"WhatsApp trigger stopped: {self.config.name}")
            return True

        except Exception as e:
            self._error_message = str(e)
            logger.error(f"Error stopping WhatsApp trigger: {e}")
            return False

    def validate_config(self) -> tuple[bool, Optional[str]]:
        """Validate WhatsApp trigger configuration."""
        config = self.config.config

        # Check for access token source
        has_token = bool(config.get("access_token"))
        has_phone_id = bool(config.get("phone_number_id"))
        has_credential = bool(config.get("credential_name"))
        has_env_token = bool(os.environ.get("WHATSAPP_ACCESS_TOKEN"))
        has_env_phone = bool(os.environ.get("WHATSAPP_PHONE_NUMBER_ID"))

        if not (has_token or has_credential or has_env_token):
            return (
                False,
                "Access token required: provide access_token, credential_name, or WHATSAPP_ACCESS_TOKEN env",
            )

        if not (has_phone_id or has_credential or has_env_phone):
            return (
                False,
                "Phone number ID required: provide phone_number_id, credential_name, or WHATSAPP_PHONE_NUMBER_ID env",
            )

        # Validate filter arrays
        for key in ["filter_phone_numbers", "message_types"]:
            value = config.get(key)
            if value is not None and not isinstance(value, list):
                return False, f"{key} must be a list"

        return True, None

    def _get_webhook_url(self) -> str:
        """Get the webhook URL for this trigger."""
        # Use configured URL
        webhook_url = self.config.config.get("webhook_url")
        if webhook_url:
            return f"{webhook_url}/whatsapp/{self.config.id}"

        # Use environment URL
        env_url = os.environ.get("CASARE_WEBHOOK_URL")
        if env_url:
            return f"{env_url}/whatsapp/{self.config.id}"

        return f"https://your-domain.com/whatsapp/{self.config.id}"

    def verify_webhook(
        self,
        mode: str,
        token: str,
        challenge: str,
    ) -> Optional[str]:
        """
        Verify webhook subscription request from Meta.

        Called by TriggerManager for GET requests to webhook URL.

        Args:
            mode: hub.mode parameter (should be "subscribe")
            token: hub.verify_token parameter
            challenge: hub.challenge parameter

        Returns:
            Challenge string if verified, None otherwise
        """
        expected_token = self._get_verify_token()

        if mode == "subscribe" and token == expected_token:
            logger.info(f"WhatsApp webhook verified: {self.config.name}")
            return challenge

        logger.warning(
            f"WhatsApp webhook verification failed: mode={mode}, token_match={token == expected_token}"
        )
        return None

    def verify_signature(
        self,
        payload: bytes,
        signature: str,
    ) -> bool:
        """
        Verify webhook payload signature.

        Args:
            payload: Raw request body bytes
            signature: X-Hub-Signature-256 header value

        Returns:
            True if signature is valid
        """
        app_secret = self.config.config.get("app_secret")
        if not app_secret:
            app_secret = os.environ.get("WHATSAPP_APP_SECRET")

        if not app_secret:
            # Can't verify without app secret
            logger.warning("No app_secret configured, skipping signature verification")
            return True

        # Signature format: sha256=abc123...
        if not signature.startswith("sha256="):
            return False

        expected_sig = signature[7:]  # Remove "sha256=" prefix

        # Calculate expected signature
        computed = hmac.new(
            app_secret.encode("utf-8"),
            payload,
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(computed, expected_sig)

    async def handle_webhook_update(
        self,
        payload: Dict[str, Any],
        signature: Optional[str] = None,
        raw_body: Optional[bytes] = None,
    ) -> bool:
        """
        Handle an update received via webhook.

        Called by TriggerManager when webhook request is received.

        Args:
            payload: Parsed JSON payload
            signature: X-Hub-Signature-256 header (optional)
            raw_body: Raw request body for signature verification

        Returns:
            True if processed successfully
        """
        try:
            # Verify signature if provided
            if signature and raw_body:
                if not self.verify_signature(raw_body, signature):
                    logger.warning("WhatsApp webhook signature verification failed")
                    return False

            await self._process_webhook(payload)
            return True

        except Exception as e:
            logger.error(f"Error processing WhatsApp webhook: {e}")
            return False

    async def _process_webhook(self, payload: Dict[str, Any]) -> None:
        """Process WhatsApp webhook payload."""
        # WhatsApp webhook structure:
        # {
        #   "object": "whatsapp_business_account",
        #   "entry": [{
        #     "id": "WHATSAPP_BUSINESS_ACCOUNT_ID",
        #     "changes": [{
        #       "value": {
        #         "messaging_product": "whatsapp",
        #         "metadata": {...},
        #         "messages": [...],
        #         "statuses": [...],
        #       },
        #       "field": "messages"
        #     }]
        #   }]
        # }

        if payload.get("object") != "whatsapp_business_account":
            logger.debug(f"Ignoring non-WhatsApp webhook: {payload.get('object')}")
            return

        entries = payload.get("entry", [])
        for entry in entries:
            changes = entry.get("changes", [])
            for change in changes:
                if change.get("field") == "messages":
                    value = change.get("value", {})
                    await self._process_messages_change(value)

    async def _process_messages_change(self, value: Dict[str, Any]) -> None:
        """Process messages change from webhook."""
        metadata = value.get("metadata", {})
        phone_number_id = metadata.get("phone_number_id")
        display_phone = metadata.get("display_phone_number")

        # Process messages
        messages = value.get("messages", [])
        for message in messages:
            await self._process_message(message, phone_number_id, display_phone)

        # Process statuses if needed
        statuses = value.get("statuses", [])
        for status in statuses:
            await self._process_status(status)

    async def _process_message(
        self,
        message: Dict[str, Any],
        phone_number_id: str,
        display_phone: str,
    ) -> None:
        """Process a single WhatsApp message."""
        from_number = message.get("from", "")
        message_type = message.get("type", "unknown")

        # Apply filters
        if not self._passes_filters(from_number, message_type):
            logger.debug(
                f"Message filtered out: from={from_number}, type={message_type}"
            )
            return

        # Build payload
        payload = self._build_payload(message, phone_number_id, display_phone)

        # Emit trigger event
        await self.emit(
            payload=payload,
            metadata={
                "message_id": message.get("id"),
                "message_type": message_type,
                "from_number": from_number,
            },
        )

    async def _process_status(self, status: Dict[str, Any]) -> None:
        """Process a message status update (optional handling)."""
        # Status updates: sent, delivered, read, failed
        # Can be used for tracking message delivery
        status_type = status.get("status")
        message_id = status.get("id")
        recipient = status.get("recipient_id")

        logger.debug(f"WhatsApp status: {status_type} for {message_id} to {recipient}")

    def _passes_filters(self, from_number: str, message_type: str) -> bool:
        """Check if message passes configured filters."""
        config = self.config.config

        # Filter by phone number
        filter_phones = config.get("filter_phone_numbers")
        if filter_phones and from_number not in filter_phones:
            return False

        # Filter by message type
        message_types = config.get("message_types")
        if message_types and message_type not in message_types:
            return False

        return True

    def _build_payload(
        self,
        message: Dict[str, Any],
        phone_number_id: str,
        display_phone: str,
    ) -> Dict[str, Any]:
        """Build payload from WhatsApp message."""
        message_type = message.get("type", "unknown")

        # Extract text content based on message type
        text = ""
        if message_type == "text":
            text = message.get("text", {}).get("body", "")
        elif message_type == "interactive":
            # Button reply or list reply
            interactive = message.get("interactive", {})
            int_type = interactive.get("type")
            if int_type == "button_reply":
                text = interactive.get("button_reply", {}).get("title", "")
            elif int_type == "list_reply":
                text = interactive.get("list_reply", {}).get("title", "")

        # Check for reply context
        context = message.get("context", {})
        is_reply = bool(context.get("message_id"))

        # Extract media info if present
        media_info = {}
        if message_type in ["image", "video", "audio", "document", "sticker"]:
            media_data = message.get(message_type, {})
            media_info = {
                "media_id": media_data.get("id"),
                "mime_type": media_data.get("mime_type"),
                "sha256": media_data.get("sha256"),
                "caption": media_data.get("caption", ""),
            }
            if message_type == "document":
                media_info["filename"] = media_data.get("filename", "")

        # Location info
        location_info = {}
        if message_type == "location":
            loc = message.get("location", {})
            location_info = {
                "latitude": loc.get("latitude"),
                "longitude": loc.get("longitude"),
                "name": loc.get("name", ""),
                "address": loc.get("address", ""),
            }

        return {
            "message_id": message.get("id"),
            "from_number": message.get("from", ""),
            "phone_number_id": phone_number_id,
            "display_phone_number": display_phone,
            "text": text,
            "message_type": message_type,
            "timestamp": message.get("timestamp"),
            "is_reply": is_reply,
            "reply_to_message_id": context.get("message_id"),
            "media": media_info,
            "location": location_info,
            "raw_message": message,
        }

    @classmethod
    def get_config_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for WhatsApp trigger configuration."""
        return {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Trigger name"},
                "enabled": {"type": "boolean", "default": True},
                "priority": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 3,
                    "default": 1,
                },
                "cooldown_seconds": {"type": "integer", "minimum": 0, "default": 0},
                "access_token": {
                    "type": "string",
                    "description": "WhatsApp Business Cloud API access token",
                },
                "phone_number_id": {
                    "type": "string",
                    "description": "WhatsApp phone number ID",
                },
                "credential_name": {
                    "type": "string",
                    "description": "Name of stored WhatsApp credential",
                },
                "verify_token": {
                    "type": "string",
                    "description": "Webhook verification token for Meta",
                },
                "app_secret": {
                    "type": "string",
                    "description": "App secret for signature verification",
                },
                "webhook_url": {
                    "type": "string",
                    "description": "Public URL for webhook (for display)",
                },
                "filter_phone_numbers": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Only trigger for these phone numbers",
                },
                "message_types": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Only trigger for these message types (text, image, etc.)",
                },
            },
            "required": ["name"],
        }


__all__ = ["WhatsAppTrigger"]
