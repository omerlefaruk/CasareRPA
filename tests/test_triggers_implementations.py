"""
CasareRPA - Trigger Implementations Tests

Comprehensive tests for all trigger implementations:
- WebhookTrigger
- FileWatchTrigger
- EmailTrigger
- AppEventTrigger
- ErrorTrigger
- WorkflowCallTrigger
- FormTrigger
- ChatTrigger
"""

import asyncio
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import tempfile
import os

import pytest

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from casare_rpa.triggers.base import BaseTriggerConfig, TriggerStatus, TriggerType, TriggerEvent
from casare_rpa.triggers.registry import get_trigger_registry, TriggerRegistry


# =============================================================================
# Registry Tests
# =============================================================================

class TestTriggerRegistry:
    """Tests for the trigger registry."""

    def test_registry_singleton(self):
        """Test registry is a singleton."""
        registry1 = get_trigger_registry()
        registry2 = get_trigger_registry()
        assert registry1 is registry2

    def test_all_triggers_registered(self):
        """Test all expected triggers are registered."""
        registry = get_trigger_registry()

        expected_types = [
            TriggerType.WEBHOOK,
            TriggerType.SCHEDULED,
            TriggerType.FILE_WATCH,
            TriggerType.EMAIL,
            TriggerType.APP_EVENT,
            TriggerType.ERROR,
            TriggerType.WORKFLOW_CALL,
            TriggerType.FORM,
            TriggerType.CHAT,
        ]

        for trigger_type in expected_types:
            trigger_class = registry.get(trigger_type)
            assert trigger_class is not None, f"Trigger type {trigger_type} not registered"

    def test_get_all_triggers(self):
        """Test getting all registered triggers."""
        registry = get_trigger_registry()
        all_triggers = registry.get_all()

        assert len(all_triggers) >= 9
        assert isinstance(all_triggers, dict)

    def test_get_by_category(self):
        """Test registry contains categorized triggers."""
        registry = get_trigger_registry()
        all_triggers = registry.get_all()

        # All triggers should have a category attribute
        for trigger_type, trigger_class in all_triggers.items():
            assert hasattr(trigger_class, 'category')
            assert trigger_class.category is not None


# =============================================================================
# Webhook Trigger Tests
# =============================================================================

class TestWebhookTrigger:
    """Tests for WebhookTrigger."""

    @pytest.fixture
    def webhook_config(self):
        """Create webhook trigger config."""
        return BaseTriggerConfig(
            id="webhook_test",
            name="Test Webhook",
            trigger_type=TriggerType.WEBHOOK,
            scenario_id="sc",
            workflow_id="wf",
            config={
                "endpoint": "/api/webhook/test",
                "method": "POST",
                "secret": "test_secret"
            }
        )

    def test_webhook_trigger_type(self):
        """Test webhook trigger has correct type."""
        from casare_rpa.triggers.implementations.webhook import WebhookTrigger
        assert WebhookTrigger.trigger_type == TriggerType.WEBHOOK

    def test_webhook_display_name(self):
        """Test webhook display name."""
        from casare_rpa.triggers.implementations.webhook import WebhookTrigger
        assert "Webhook" in WebhookTrigger.display_name

    def test_webhook_validate_config(self, webhook_config):
        """Test webhook config validation."""
        from casare_rpa.triggers.implementations.webhook import WebhookTrigger
        trigger = WebhookTrigger(webhook_config)
        is_valid, error = trigger.validate_config()
        assert is_valid is True

    def test_webhook_config_schema(self):
        """Test webhook config schema."""
        from casare_rpa.triggers.implementations.webhook import WebhookTrigger
        schema = WebhookTrigger.get_config_schema()

        assert "properties" in schema
        props = schema["properties"]
        assert "endpoint" in props or "path" in props or "port" in props


# =============================================================================
# File Watch Trigger Tests
# =============================================================================

class TestFileWatchTrigger:
    """Tests for FileWatchTrigger."""

    @pytest.fixture
    def file_watch_config(self, tmp_path):
        """Create file watch trigger config."""
        return BaseTriggerConfig(
            id="file_watch_test",
            name="Test File Watch",
            trigger_type=TriggerType.FILE_WATCH,
            scenario_id="sc",
            workflow_id="wf",
            config={
                "watch_path": str(tmp_path),
                "patterns": ["*.txt"],
                "recursive": False,
                "events": ["created", "modified"]
            }
        )

    def test_file_watch_trigger_type(self):
        """Test file watch trigger has correct type."""
        from casare_rpa.triggers.implementations.file_watch import FileWatchTrigger
        assert FileWatchTrigger.trigger_type == TriggerType.FILE_WATCH

    def test_file_watch_display_name(self):
        """Test file watch display name."""
        from casare_rpa.triggers.implementations.file_watch import FileWatchTrigger
        assert "File" in FileWatchTrigger.display_name

    def test_file_watch_validate_config(self, file_watch_config):
        """Test file watch config validation."""
        from casare_rpa.triggers.implementations.file_watch import FileWatchTrigger
        trigger = FileWatchTrigger(file_watch_config)
        is_valid, error = trigger.validate_config()
        assert is_valid is True

    def test_file_watch_invalid_path(self, file_watch_config):
        """Test file watch with invalid path."""
        from casare_rpa.triggers.implementations.file_watch import FileWatchTrigger
        file_watch_config.config["watch_path"] = "/nonexistent/path/12345"
        trigger = FileWatchTrigger(file_watch_config)
        is_valid, error = trigger.validate_config()
        # Validation may or may not check path existence
        # This test just ensures it doesn't crash

    def test_file_watch_config_schema(self):
        """Test file watch config schema."""
        from casare_rpa.triggers.implementations.file_watch import FileWatchTrigger
        schema = FileWatchTrigger.get_config_schema()

        assert "properties" in schema
        props = schema["properties"]
        assert "watch_path" in props

    @pytest.mark.asyncio
    async def test_file_watch_start_stop(self, file_watch_config):
        """Test starting and stopping file watch trigger."""
        from casare_rpa.triggers.implementations.file_watch import FileWatchTrigger
        trigger = FileWatchTrigger(file_watch_config)

        result = await trigger.start()
        assert result is True
        assert trigger.status == TriggerStatus.ACTIVE

        result = await trigger.stop()
        assert result is True
        assert trigger.status == TriggerStatus.INACTIVE


# =============================================================================
# Email Trigger Tests
# =============================================================================

class TestEmailTrigger:
    """Tests for EmailTrigger."""

    @pytest.fixture
    def email_config(self):
        """Create email trigger config."""
        return BaseTriggerConfig(
            id="email_test",
            name="Test Email Trigger",
            trigger_type=TriggerType.EMAIL,
            scenario_id="sc",
            workflow_id="wf",
            config={
                "server": "imap.test.com",
                "port": 993,
                "username": "test@test.com",
                "password": "password",
                "use_ssl": True,
                "folder": "INBOX",
                "check_interval": 60
            }
        )

    def test_email_trigger_type(self):
        """Test email trigger has correct type."""
        from casare_rpa.triggers.implementations.email_trigger import EmailTrigger
        assert EmailTrigger.trigger_type == TriggerType.EMAIL

    def test_email_display_name(self):
        """Test email display name."""
        from casare_rpa.triggers.implementations.email_trigger import EmailTrigger
        assert "Email" in EmailTrigger.display_name

    def test_email_config_schema(self):
        """Test email config schema."""
        from casare_rpa.triggers.implementations.email_trigger import EmailTrigger
        schema = EmailTrigger.get_config_schema()

        assert "properties" in schema
        props = schema["properties"]
        assert "server" in props or "host" in props


# =============================================================================
# App Event Trigger Tests
# =============================================================================

class TestAppEventTrigger:
    """Tests for AppEventTrigger."""

    @pytest.fixture
    def app_event_config(self):
        """Create app event trigger config."""
        return BaseTriggerConfig(
            id="app_event_test",
            name="Test App Event",
            trigger_type=TriggerType.APP_EVENT,
            scenario_id="sc",
            workflow_id="wf",
            config={
                "app_name": "notepad.exe",
                "event_type": "window_opened",
                "window_title": "*Untitled*"
            }
        )

    def test_app_event_trigger_type(self):
        """Test app event trigger has correct type."""
        from casare_rpa.triggers.implementations.app_event import AppEventTrigger
        assert AppEventTrigger.trigger_type == TriggerType.APP_EVENT

    def test_app_event_display_name(self):
        """Test app event display name."""
        from casare_rpa.triggers.implementations.app_event import AppEventTrigger
        assert "App" in AppEventTrigger.display_name or "Event" in AppEventTrigger.display_name

    def test_app_event_config_schema(self):
        """Test app event config schema."""
        from casare_rpa.triggers.implementations.app_event import AppEventTrigger
        schema = AppEventTrigger.get_config_schema()

        assert "properties" in schema


# =============================================================================
# Error Trigger Tests
# =============================================================================

class TestErrorTrigger:
    """Tests for ErrorTrigger."""

    @pytest.fixture
    def error_config(self):
        """Create error trigger config."""
        return BaseTriggerConfig(
            id="error_test",
            name="Test Error Trigger",
            trigger_type=TriggerType.ERROR,
            scenario_id="sc",
            workflow_id="wf",
            config={
                "error_types": ["RuntimeError", "ValueError"],
                "source_workflow": "*",
                "retry_count": 3
            }
        )

    def test_error_trigger_type(self):
        """Test error trigger has correct type."""
        from casare_rpa.triggers.implementations.error_trigger import ErrorTrigger
        assert ErrorTrigger.trigger_type == TriggerType.ERROR

    def test_error_display_name(self):
        """Test error display name."""
        from casare_rpa.triggers.implementations.error_trigger import ErrorTrigger
        assert "Error" in ErrorTrigger.display_name

    def test_error_config_schema(self):
        """Test error config schema."""
        from casare_rpa.triggers.implementations.error_trigger import ErrorTrigger
        schema = ErrorTrigger.get_config_schema()

        assert "properties" in schema

    @pytest.mark.asyncio
    async def test_error_trigger_start_stop(self, error_config):
        """Test starting and stopping error trigger."""
        from casare_rpa.triggers.implementations.error_trigger import ErrorTrigger
        trigger = ErrorTrigger(error_config)

        result = await trigger.start()
        assert result is True
        assert trigger.status == TriggerStatus.ACTIVE

        result = await trigger.stop()
        assert result is True
        assert trigger.status == TriggerStatus.INACTIVE


# =============================================================================
# Workflow Call Trigger Tests
# =============================================================================

class TestWorkflowCallTrigger:
    """Tests for WorkflowCallTrigger."""

    @pytest.fixture
    def workflow_call_config(self):
        """Create workflow call trigger config."""
        return BaseTriggerConfig(
            id="workflow_call_test",
            name="Test Workflow Call",
            trigger_type=TriggerType.WORKFLOW_CALL,
            scenario_id="sc",
            workflow_id="wf",
            config={
                "call_alias": "test_workflow",
                "synchronous": True,
                "allowed_callers": []
            }
        )

    def test_workflow_call_trigger_type(self):
        """Test workflow call trigger has correct type."""
        from casare_rpa.triggers.implementations.workflow_call import WorkflowCallTrigger
        assert WorkflowCallTrigger.trigger_type == TriggerType.WORKFLOW_CALL

    def test_workflow_call_display_name(self):
        """Test workflow call display name."""
        from casare_rpa.triggers.implementations.workflow_call import WorkflowCallTrigger
        assert "Workflow" in WorkflowCallTrigger.display_name or "Call" in WorkflowCallTrigger.display_name

    def test_workflow_call_config_schema(self):
        """Test workflow call config schema."""
        from casare_rpa.triggers.implementations.workflow_call import WorkflowCallTrigger
        schema = WorkflowCallTrigger.get_config_schema()

        assert "properties" in schema

    @pytest.mark.asyncio
    async def test_workflow_call_start_stop(self, workflow_call_config):
        """Test starting and stopping workflow call trigger."""
        from casare_rpa.triggers.implementations.workflow_call import WorkflowCallTrigger
        trigger = WorkflowCallTrigger(workflow_call_config)

        result = await trigger.start()
        assert result is True
        assert trigger.status == TriggerStatus.ACTIVE

        result = await trigger.stop()
        assert result is True
        assert trigger.status == TriggerStatus.INACTIVE


# =============================================================================
# Form Trigger Tests
# =============================================================================

class TestFormTrigger:
    """Tests for FormTrigger."""

    @pytest.fixture
    def form_config(self):
        """Create form trigger config."""
        return BaseTriggerConfig(
            id="form_test",
            name="Test Form Trigger",
            trigger_type=TriggerType.FORM,
            scenario_id="sc",
            workflow_id="wf",
            config={
                "form_id": "contact_form",
                "fields": ["name", "email", "message"]
            }
        )

    def test_form_trigger_type(self):
        """Test form trigger has correct type."""
        from casare_rpa.triggers.implementations.form_trigger import FormTrigger
        assert FormTrigger.trigger_type == TriggerType.FORM

    def test_form_display_name(self):
        """Test form display name."""
        from casare_rpa.triggers.implementations.form_trigger import FormTrigger
        assert "Form" in FormTrigger.display_name

    def test_form_config_schema(self):
        """Test form config schema."""
        from casare_rpa.triggers.implementations.form_trigger import FormTrigger
        schema = FormTrigger.get_config_schema()

        assert "properties" in schema


# =============================================================================
# Chat Trigger Tests
# =============================================================================

class TestChatTrigger:
    """Tests for ChatTrigger."""

    @pytest.fixture
    def chat_config(self):
        """Create chat trigger config."""
        return BaseTriggerConfig(
            id="chat_test",
            name="Test Chat Trigger",
            trigger_type=TriggerType.CHAT,
            scenario_id="sc",
            workflow_id="wf",
            config={
                "keywords": ["help", "support"],
                "channels": ["*"],
                "case_sensitive": False
            }
        )

    def test_chat_trigger_type(self):
        """Test chat trigger has correct type."""
        from casare_rpa.triggers.implementations.chat_trigger import ChatTrigger
        assert ChatTrigger.trigger_type == TriggerType.CHAT

    def test_chat_display_name(self):
        """Test chat display name."""
        from casare_rpa.triggers.implementations.chat_trigger import ChatTrigger
        assert "Chat" in ChatTrigger.display_name

    def test_chat_config_schema(self):
        """Test chat config schema."""
        from casare_rpa.triggers.implementations.chat_trigger import ChatTrigger
        schema = ChatTrigger.get_config_schema()

        assert "properties" in schema


# =============================================================================
# Cross-Trigger Integration Tests
# =============================================================================

class TestTriggerIntegration:
    """Integration tests across trigger types."""

    def test_all_triggers_have_validate_config(self):
        """Test all triggers implement validate_config."""
        registry = get_trigger_registry()

        for trigger_type, trigger_class in registry.get_all().items():
            assert hasattr(trigger_class, 'validate_config')

            # Create instance with minimal config
            config = BaseTriggerConfig(
                id="test",
                name="Test",
                trigger_type=trigger_type,
                scenario_id="sc",
                workflow_id="wf",
                config={}
            )
            trigger = trigger_class(config)

            # Should not raise
            result = trigger.validate_config()
            assert isinstance(result, tuple)
            assert len(result) == 2

    def test_all_triggers_have_config_schema(self):
        """Test all triggers provide config schema."""
        registry = get_trigger_registry()

        for trigger_type, trigger_class in registry.get_all().items():
            schema = trigger_class.get_config_schema()

            assert isinstance(schema, dict)
            assert "type" in schema
            assert "properties" in schema

    def test_all_triggers_have_display_info(self):
        """Test all triggers provide display info."""
        registry = get_trigger_registry()

        for trigger_type, trigger_class in registry.get_all().items():
            info = trigger_class.get_display_info()

            assert "type" in info
            assert "display_name" in info
            assert "description" in info
            assert "icon" in info
            assert "category" in info

    @pytest.mark.asyncio
    async def test_all_triggers_start_stop_cycle(self):
        """Test all triggers can start and stop."""
        registry = get_trigger_registry()

        for trigger_type, trigger_class in registry.get_all().items():
            config = BaseTriggerConfig(
                id=f"test_{trigger_type.value}",
                name=f"Test {trigger_type.value}",
                trigger_type=trigger_type,
                scenario_id="sc",
                workflow_id="wf",
                config={}
            )
            trigger = trigger_class(config)

            # May or may not start successfully depending on config
            try:
                await trigger.start()
            except Exception:
                pass  # Some triggers need specific config

            # Stop should always work
            result = await trigger.stop()
            assert result is True
            assert trigger.status == TriggerStatus.INACTIVE

    def test_all_triggers_inherit_from_base(self):
        """Test all triggers inherit from BaseTrigger."""
        from casare_rpa.triggers.base import BaseTrigger
        registry = get_trigger_registry()

        for trigger_type, trigger_class in registry.get_all().items():
            assert issubclass(trigger_class, BaseTrigger)

    def test_trigger_event_creation_from_all_types(self):
        """Test TriggerEvent can be created for all trigger types."""
        for trigger_type in TriggerType:
            event = TriggerEvent(
                trigger_id=f"test_{trigger_type.value}",
                trigger_type=trigger_type,
                workflow_id="wf",
                scenario_id="sc",
                payload={"test": True}
            )

            assert event.trigger_type == trigger_type

            # Test serialization
            data = event.to_dict()
            restored = TriggerEvent.from_dict(data)
            assert restored.trigger_type == trigger_type
