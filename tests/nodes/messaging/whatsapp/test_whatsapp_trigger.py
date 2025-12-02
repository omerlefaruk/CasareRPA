"""
Tests for WhatsAppTrigger.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import hashlib
import hmac

from casare_rpa.triggers.base import BaseTriggerConfig, TriggerType, TriggerStatus
from casare_rpa.triggers.implementations.whatsapp_trigger import WhatsAppTrigger


@pytest.fixture
def trigger_config():
    """Create a test trigger configuration."""
    return BaseTriggerConfig(
        id="test_whatsapp_trigger_1",
        name="Test WhatsApp Trigger",
        trigger_type=TriggerType.WHATSAPP,
        scenario_id="test_scenario",
        workflow_id="test_workflow",
        config={
            "access_token": "test_access_token",
            "phone_number_id": "123456789",
            "verify_token": "test_verify_token",
        },
    )


@pytest.fixture
def trigger(trigger_config):
    """Create a test trigger instance."""
    callback = AsyncMock()
    return WhatsAppTrigger(trigger_config, event_callback=callback)


class TestWhatsAppTriggerConfig:
    """Tests for trigger configuration validation."""

    def test_validate_config_with_credentials(self, trigger):
        """Test validation passes with credentials."""
        valid, error = trigger.validate_config()
        assert valid is True
        assert error is None

    def test_validate_config_without_token(self):
        """Test validation fails without access token."""
        config = BaseTriggerConfig(
            id="test_trigger",
            name="Test",
            trigger_type=TriggerType.WHATSAPP,
            scenario_id="test_scenario",
            workflow_id="test_workflow",
            config={"phone_number_id": "123456789"},  # No access_token
        )
        trigger = WhatsAppTrigger(config)

        with patch.dict("os.environ", {}, clear=True):
            valid, error = trigger.validate_config()

        assert valid is False
        assert "token" in error.lower()

    def test_validate_config_without_phone_id(self):
        """Test validation fails without phone number ID."""
        config = BaseTriggerConfig(
            id="test_trigger",
            name="Test",
            trigger_type=TriggerType.WHATSAPP,
            scenario_id="test_scenario",
            workflow_id="test_workflow",
            config={"access_token": "test_token"},  # No phone_number_id
        )
        trigger = WhatsAppTrigger(config)

        with patch.dict("os.environ", {}, clear=True):
            valid, error = trigger.validate_config()

        assert valid is False
        assert "phone" in error.lower()


class TestWhatsAppTriggerWebhookVerification:
    """Tests for webhook verification."""

    def test_verify_webhook_success(self, trigger):
        """Test successful webhook verification."""
        result = trigger.verify_webhook(
            mode="subscribe",
            token="test_verify_token",
            challenge="challenge_123",
        )

        assert result == "challenge_123"

    def test_verify_webhook_wrong_mode(self, trigger):
        """Test verification fails with wrong mode."""
        result = trigger.verify_webhook(
            mode="unsubscribe",
            token="test_verify_token",
            challenge="challenge_123",
        )

        assert result is None

    def test_verify_webhook_wrong_token(self, trigger):
        """Test verification fails with wrong token."""
        result = trigger.verify_webhook(
            mode="subscribe",
            token="wrong_token",
            challenge="challenge_123",
        )

        assert result is None


class TestWhatsAppTriggerSignatureVerification:
    """Tests for signature verification."""

    def test_verify_signature_without_secret(self, trigger):
        """Test signature verification passes without app_secret configured."""
        # Without app_secret, should always return True
        result = trigger.verify_signature(b"test payload", "sha256=abc123")

        assert result is True

    def test_verify_signature_with_secret(self, trigger_config):
        """Test signature verification with app_secret."""
        trigger_config.config["app_secret"] = "test_app_secret"
        trigger = WhatsAppTrigger(trigger_config)

        payload = b'{"test": "data"}'
        expected_sig = hmac.new(
            b"test_app_secret",
            payload,
            hashlib.sha256,
        ).hexdigest()

        result = trigger.verify_signature(payload, f"sha256={expected_sig}")

        assert result is True

    def test_verify_signature_invalid(self, trigger_config):
        """Test signature verification fails with wrong signature."""
        trigger_config.config["app_secret"] = "test_app_secret"
        trigger = WhatsAppTrigger(trigger_config)

        result = trigger.verify_signature(b"test payload", "sha256=wrong_signature")

        assert result is False

    def test_verify_signature_invalid_format(self, trigger_config):
        """Test signature verification fails with wrong format."""
        trigger_config.config["app_secret"] = "test_app_secret"
        trigger = WhatsAppTrigger(trigger_config)

        result = trigger.verify_signature(b"test payload", "invalid_format")

        assert result is False


class TestWhatsAppTriggerLifecycle:
    """Tests for trigger lifecycle management."""

    @pytest.mark.asyncio
    async def test_start_trigger(self, trigger):
        """Test starting trigger."""
        mock_client = AsyncMock()

        with patch.object(trigger, "_get_client", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_client

            result = await trigger.start()

            assert result is True
            assert trigger.status == TriggerStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_stop_trigger(self, trigger):
        """Test stopping trigger."""
        trigger._status = TriggerStatus.ACTIVE
        mock_client = AsyncMock()
        mock_client.close = AsyncMock()
        trigger._client = mock_client

        result = await trigger.stop()

        assert result is True
        assert trigger.status == TriggerStatus.INACTIVE
        mock_client.close.assert_called_once()


class TestWhatsAppTriggerWebhookProcessing:
    """Tests for webhook payload processing."""

    @pytest.fixture
    def sample_text_message(self):
        """Create a sample text message webhook payload."""
        return {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "BUSINESS_ACCOUNT_ID",
                    "changes": [
                        {
                            "value": {
                                "messaging_product": "whatsapp",
                                "metadata": {
                                    "display_phone_number": "1234567890",
                                    "phone_number_id": "123456789",
                                },
                                "messages": [
                                    {
                                        "from": "15551234567",
                                        "id": "wamid.test123",
                                        "timestamp": "1234567890",
                                        "type": "text",
                                        "text": {"body": "Hello, bot!"},
                                    }
                                ],
                            },
                            "field": "messages",
                        }
                    ],
                }
            ],
        }

    @pytest.mark.asyncio
    async def test_handle_webhook_text_message(self, trigger, sample_text_message):
        """Test processing a text message webhook."""
        with patch.object(trigger, "emit", new_callable=AsyncMock) as mock_emit:
            result = await trigger.handle_webhook_update(sample_text_message)

            assert result is True
            mock_emit.assert_called_once()
            call_args = mock_emit.call_args
            payload = call_args[1]["payload"]

            assert payload["message_id"] == "wamid.test123"
            assert payload["from_number"] == "15551234567"
            assert payload["text"] == "Hello, bot!"
            assert payload["message_type"] == "text"

    @pytest.mark.asyncio
    async def test_handle_webhook_invalid_object(self, trigger):
        """Test ignoring non-WhatsApp webhooks."""
        payload = {"object": "page", "entry": []}

        with patch.object(trigger, "emit", new_callable=AsyncMock) as mock_emit:
            result = await trigger.handle_webhook_update(payload)

            assert result is True
            mock_emit.assert_not_called()

    @pytest.mark.asyncio
    async def test_filter_by_phone_number(self, trigger_config):
        """Test filtering messages by phone number."""
        trigger_config.config["filter_phone_numbers"] = ["15551234567"]
        trigger = WhatsAppTrigger(trigger_config)

        # Message from allowed number
        allowed_payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "metadata": {
                                    "phone_number_id": "123456789",
                                    "display_phone_number": "1234567890",
                                },
                                "messages": [
                                    {
                                        "from": "15551234567",
                                        "id": "wamid.1",
                                        "type": "text",
                                        "text": {"body": "Hello"},
                                    }
                                ],
                            },
                            "field": "messages",
                        }
                    ],
                }
            ],
        }

        # Message from blocked number
        blocked_payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "metadata": {
                                    "phone_number_id": "123456789",
                                    "display_phone_number": "1234567890",
                                },
                                "messages": [
                                    {
                                        "from": "15559999999",
                                        "id": "wamid.2",
                                        "type": "text",
                                        "text": {"body": "Hello"},
                                    }
                                ],
                            },
                            "field": "messages",
                        }
                    ],
                }
            ],
        }

        with patch.object(trigger, "emit", new_callable=AsyncMock) as mock_emit:
            await trigger.handle_webhook_update(allowed_payload)
            assert mock_emit.called

            mock_emit.reset_mock()

            await trigger.handle_webhook_update(blocked_payload)
            assert not mock_emit.called


class TestWhatsAppTriggerConfigSchema:
    """Tests for configuration schema."""

    def test_get_config_schema(self):
        """Test getting config schema."""
        schema = WhatsAppTrigger.get_config_schema()

        assert "properties" in schema
        assert "access_token" in schema["properties"]
        assert "phone_number_id" in schema["properties"]
        assert "verify_token" in schema["properties"]
        assert "filter_phone_numbers" in schema["properties"]
