"""
Tests for Trigger nodes.

Tests 11 trigger node types:
- BaseTriggerNode behavior (3 tests)
- WebhookTriggerNode (4 tests)
- ScheduleTriggerNode (4 tests)
- FileWatchTriggerNode (3 tests)
- EmailTriggerNode (3 tests)
- AppEventTriggerNode (3 tests)
- ErrorTriggerNode (3 tests)
- WorkflowCallTriggerNode (3 tests)
- FormTriggerNode (3 tests)
- ChatTriggerNode (3 tests)
- RSSFeedTriggerNode (3 tests)
- SSETriggerNode (3 tests)
"""

import pytest
from unittest.mock import Mock, AsyncMock

from casare_rpa.domain.value_objects.types import NodeStatus
from casare_rpa.triggers.base import TriggerType


# Note: execution_context fixture is provided by tests/conftest.py


class TestBaseTriggerNodeBehavior:
    """Tests for common trigger node behavior."""

    def test_trigger_nodes_have_no_exec_in_port(self) -> None:
        """Test that trigger nodes have no exec_in port (they START workflows)."""
        from casare_rpa.nodes.trigger_nodes import WebhookTriggerNode

        node = WebhookTriggerNode(node_id="webhook_1")

        # Trigger nodes should NOT have exec_in
        assert "exec_in" not in node.input_ports
        # But they should have exec_out
        assert "exec_out" in node.output_ports

    def test_trigger_nodes_are_marked_as_triggers(self) -> None:
        """Test that trigger nodes have is_trigger_node = True."""
        from casare_rpa.nodes.trigger_nodes import (
            WebhookTriggerNode,
            ScheduleTriggerNode,
            FileWatchTriggerNode,
        )

        assert WebhookTriggerNode.is_trigger_node is True
        assert ScheduleTriggerNode.is_trigger_node is True
        assert FileWatchTriggerNode.is_trigger_node is True

    def test_trigger_nodes_belong_to_triggers_category(self) -> None:
        """Test that trigger nodes are in 'triggers' category."""
        from casare_rpa.nodes.trigger_nodes import WebhookTriggerNode

        node = WebhookTriggerNode(node_id="webhook_1")
        assert node.category == "triggers"


class TestWebhookTriggerNode:
    """Tests for WebhookTriggerNode - HTTP webhook trigger."""

    @pytest.mark.asyncio
    async def test_webhook_executes_successfully(self, execution_context) -> None:
        """Test WebhookTriggerNode executes as pass-through."""
        from casare_rpa.nodes.trigger_nodes import WebhookTriggerNode

        node = WebhookTriggerNode(node_id="webhook_1", config={"endpoint": "/test"})

        result = await node.execute(execution_context)

        assert result["success"] is True

    def test_webhook_has_payload_output_ports(self) -> None:
        """Test WebhookTriggerNode has expected output ports."""
        from casare_rpa.nodes.trigger_nodes import WebhookTriggerNode

        node = WebhookTriggerNode(node_id="webhook_1")

        # Should have payload-related output ports
        assert "payload" in node.output_ports
        assert "headers" in node.output_ports
        assert "query_params" in node.output_ports
        assert "method" in node.output_ports
        assert "exec_out" in node.output_ports

    def test_webhook_returns_correct_trigger_type(self) -> None:
        """Test WebhookTriggerNode returns WEBHOOK trigger type."""
        from casare_rpa.nodes.trigger_nodes import WebhookTriggerNode

        node = WebhookTriggerNode(node_id="webhook_1")

        assert node.get_trigger_type() == TriggerType.WEBHOOK

    def test_webhook_creates_valid_trigger_config(self) -> None:
        """Test WebhookTriggerNode creates valid trigger config."""
        from casare_rpa.nodes.trigger_nodes import WebhookTriggerNode

        node = WebhookTriggerNode(
            node_id="webhook_1",
            config={
                "endpoint": "/my-webhook",
                "methods": "POST,GET",
                "auth_type": "header",
                "auth_header_name": "X-API-Key",
                "auth_header_value": "secret123",
            },
        )

        config = node.create_trigger_config(workflow_id="wf_1", scenario_id="sc_1")

        assert config.trigger_type == TriggerType.WEBHOOK
        assert config.workflow_id == "wf_1"
        assert config.scenario_id == "sc_1"
        assert "endpoint" in config.config


class TestScheduleTriggerNode:
    """Tests for ScheduleTriggerNode - time-based trigger."""

    @pytest.mark.asyncio
    async def test_schedule_executes_successfully(self, execution_context) -> None:
        """Test ScheduleTriggerNode executes as pass-through."""
        from casare_rpa.nodes.trigger_nodes import ScheduleTriggerNode

        node = ScheduleTriggerNode(node_id="schedule_1")

        result = await node.execute(execution_context)

        assert result["success"] is True

    def test_schedule_has_time_output_ports(self) -> None:
        """Test ScheduleTriggerNode has expected output ports."""
        from casare_rpa.nodes.trigger_nodes import ScheduleTriggerNode

        node = ScheduleTriggerNode(node_id="schedule_1")

        assert "trigger_time" in node.output_ports
        assert "run_number" in node.output_ports
        assert "exec_out" in node.output_ports

    def test_schedule_returns_correct_trigger_type(self) -> None:
        """Test ScheduleTriggerNode returns SCHEDULED trigger type."""
        from casare_rpa.nodes.trigger_nodes import ScheduleTriggerNode

        node = ScheduleTriggerNode(node_id="schedule_1")

        assert node.get_trigger_type() == TriggerType.SCHEDULED

    def test_schedule_with_cron_expression(self) -> None:
        """Test ScheduleTriggerNode with cron expression config."""
        from casare_rpa.nodes.trigger_nodes import ScheduleTriggerNode

        node = ScheduleTriggerNode(
            node_id="schedule_1",
            config={
                "frequency": "cron",
                "cron_expression": "0 9 * * MON-FRI",
                "timezone": "America/New_York",
            },
        )

        config = node.get_trigger_config()

        assert config["frequency"] == "cron"
        assert config["cron_expression"] == "0 9 * * MON-FRI"


class TestFileWatchTriggerNode:
    """Tests for FileWatchTriggerNode - file system trigger."""

    @pytest.mark.asyncio
    async def test_filewatch_executes_successfully(self, execution_context) -> None:
        """Test FileWatchTriggerNode executes as pass-through."""
        from casare_rpa.nodes.trigger_nodes import FileWatchTriggerNode

        node = FileWatchTriggerNode(node_id="filewatch_1")

        result = await node.execute(execution_context)

        assert result["success"] is True

    def test_filewatch_has_file_output_ports(self) -> None:
        """Test FileWatchTriggerNode has expected output ports."""
        from casare_rpa.nodes.trigger_nodes import FileWatchTriggerNode

        node = FileWatchTriggerNode(node_id="filewatch_1")

        assert "file_path" in node.output_ports
        assert "file_name" in node.output_ports
        assert "event_type" in node.output_ports
        assert "exec_out" in node.output_ports

    def test_filewatch_returns_correct_trigger_type(self) -> None:
        """Test FileWatchTriggerNode returns FILE_WATCH trigger type."""
        from casare_rpa.nodes.trigger_nodes import FileWatchTriggerNode

        node = FileWatchTriggerNode(node_id="filewatch_1")

        assert node.get_trigger_type() == TriggerType.FILE_WATCH


class TestEmailTriggerNode:
    """Tests for EmailTriggerNode - email-based trigger."""

    @pytest.mark.asyncio
    async def test_email_executes_successfully(self, execution_context) -> None:
        """Test EmailTriggerNode executes as pass-through."""
        from casare_rpa.nodes.trigger_nodes import EmailTriggerNode

        node = EmailTriggerNode(node_id="email_1")

        result = await node.execute(execution_context)

        assert result["success"] is True

    def test_email_has_email_output_ports(self) -> None:
        """Test EmailTriggerNode has expected output ports."""
        from casare_rpa.nodes.trigger_nodes import EmailTriggerNode

        node = EmailTriggerNode(node_id="email_1")

        assert "subject" in node.output_ports
        assert "sender" in node.output_ports  # Uses 'sender' not 'from_address'
        assert "body" in node.output_ports
        assert "exec_out" in node.output_ports

    def test_email_returns_correct_trigger_type(self) -> None:
        """Test EmailTriggerNode returns EMAIL trigger type."""
        from casare_rpa.nodes.trigger_nodes import EmailTriggerNode

        node = EmailTriggerNode(node_id="email_1")

        assert node.get_trigger_type() == TriggerType.EMAIL


class TestAppEventTriggerNode:
    """Tests for AppEventTriggerNode - application event trigger."""

    @pytest.mark.asyncio
    async def test_appevent_executes_successfully(self, execution_context) -> None:
        """Test AppEventTriggerNode executes as pass-through."""
        from casare_rpa.nodes.trigger_nodes import AppEventTriggerNode

        node = AppEventTriggerNode(node_id="appevent_1")

        result = await node.execute(execution_context)

        assert result["success"] is True

    def test_appevent_has_event_output_ports(self) -> None:
        """Test AppEventTriggerNode has expected output ports."""
        from casare_rpa.nodes.trigger_nodes import AppEventTriggerNode

        node = AppEventTriggerNode(node_id="appevent_1")

        assert "event_type" in node.output_ports  # Uses 'event_type' not 'event_name'
        assert "event_data" in node.output_ports
        assert "exec_out" in node.output_ports

    def test_appevent_returns_correct_trigger_type(self) -> None:
        """Test AppEventTriggerNode returns APP_EVENT trigger type."""
        from casare_rpa.nodes.trigger_nodes import AppEventTriggerNode

        node = AppEventTriggerNode(node_id="appevent_1")

        assert node.get_trigger_type() == TriggerType.APP_EVENT


class TestErrorTriggerNode:
    """Tests for ErrorTriggerNode - error event trigger."""

    @pytest.mark.asyncio
    async def test_error_executes_successfully(self, execution_context) -> None:
        """Test ErrorTriggerNode executes as pass-through."""
        from casare_rpa.nodes.trigger_nodes import ErrorTriggerNode

        node = ErrorTriggerNode(node_id="error_1")

        result = await node.execute(execution_context)

        assert result["success"] is True

    def test_error_has_error_output_ports(self) -> None:
        """Test ErrorTriggerNode has expected output ports."""
        from casare_rpa.nodes.trigger_nodes import ErrorTriggerNode

        node = ErrorTriggerNode(node_id="error_1")

        assert "error_message" in node.output_ports
        assert "error_type" in node.output_ports
        assert "exec_out" in node.output_ports

    def test_error_returns_correct_trigger_type(self) -> None:
        """Test ErrorTriggerNode returns ERROR trigger type."""
        from casare_rpa.nodes.trigger_nodes import ErrorTriggerNode

        node = ErrorTriggerNode(node_id="error_1")

        assert node.get_trigger_type() == TriggerType.ERROR


class TestWorkflowCallTriggerNode:
    """Tests for WorkflowCallTriggerNode - sub-workflow trigger."""

    @pytest.mark.asyncio
    async def test_workflowcall_executes_successfully(self, execution_context) -> None:
        """Test WorkflowCallTriggerNode executes as pass-through."""
        from casare_rpa.nodes.trigger_nodes import WorkflowCallTriggerNode

        node = WorkflowCallTriggerNode(node_id="workflowcall_1")

        result = await node.execute(execution_context)

        assert result["success"] is True

    def test_workflowcall_has_call_output_ports(self) -> None:
        """Test WorkflowCallTriggerNode has expected output ports."""
        from casare_rpa.nodes.trigger_nodes import WorkflowCallTriggerNode

        node = WorkflowCallTriggerNode(node_id="workflowcall_1")

        assert "caller_workflow_id" in node.output_ports
        assert "params" in node.output_ports  # Uses 'params' not 'input_data'
        assert "exec_out" in node.output_ports

    def test_workflowcall_returns_correct_trigger_type(self) -> None:
        """Test WorkflowCallTriggerNode returns WORKFLOW_CALL trigger type."""
        from casare_rpa.nodes.trigger_nodes import WorkflowCallTriggerNode

        node = WorkflowCallTriggerNode(node_id="workflowcall_1")

        assert node.get_trigger_type() == TriggerType.WORKFLOW_CALL


class TestFormTriggerNode:
    """Tests for FormTriggerNode - form submission trigger."""

    @pytest.mark.asyncio
    async def test_form_executes_successfully(self, execution_context) -> None:
        """Test FormTriggerNode executes as pass-through."""
        from casare_rpa.nodes.trigger_nodes import FormTriggerNode

        node = FormTriggerNode(node_id="form_1")

        result = await node.execute(execution_context)

        assert result["success"] is True

    def test_form_has_form_output_ports(self) -> None:
        """Test FormTriggerNode has expected output ports."""
        from casare_rpa.nodes.trigger_nodes import FormTriggerNode

        node = FormTriggerNode(node_id="form_1")

        assert "form_data" in node.output_ports
        assert "exec_out" in node.output_ports

    def test_form_returns_correct_trigger_type(self) -> None:
        """Test FormTriggerNode returns FORM trigger type."""
        from casare_rpa.nodes.trigger_nodes import FormTriggerNode

        node = FormTriggerNode(node_id="form_1")

        assert node.get_trigger_type() == TriggerType.FORM


class TestChatTriggerNode:
    """Tests for ChatTriggerNode - chat message trigger."""

    @pytest.mark.asyncio
    async def test_chat_executes_successfully(self, execution_context) -> None:
        """Test ChatTriggerNode executes as pass-through."""
        from casare_rpa.nodes.trigger_nodes import ChatTriggerNode

        node = ChatTriggerNode(node_id="chat_1")

        result = await node.execute(execution_context)

        assert result["success"] is True

    def test_chat_has_chat_output_ports(self) -> None:
        """Test ChatTriggerNode has expected output ports."""
        from casare_rpa.nodes.trigger_nodes import ChatTriggerNode

        node = ChatTriggerNode(node_id="chat_1")

        assert "message" in node.output_ports
        assert "user_id" in node.output_ports
        assert "exec_out" in node.output_ports

    def test_chat_returns_correct_trigger_type(self) -> None:
        """Test ChatTriggerNode returns CHAT trigger type."""
        from casare_rpa.nodes.trigger_nodes import ChatTriggerNode

        node = ChatTriggerNode(node_id="chat_1")

        assert node.get_trigger_type() == TriggerType.CHAT


class TestRSSFeedTriggerNode:
    """Tests for RSSFeedTriggerNode - RSS/Atom feed trigger."""

    @pytest.mark.asyncio
    async def test_rssfeed_executes_successfully(self, execution_context) -> None:
        """Test RSSFeedTriggerNode executes as pass-through."""
        from casare_rpa.nodes.trigger_nodes import RSSFeedTriggerNode

        node = RSSFeedTriggerNode(node_id="rss_1")

        result = await node.execute(execution_context)

        assert result["success"] is True

    def test_rssfeed_has_rss_output_ports(self) -> None:
        """Test RSSFeedTriggerNode has expected output ports."""
        from casare_rpa.nodes.trigger_nodes import RSSFeedTriggerNode

        node = RSSFeedTriggerNode(node_id="rss_1")

        assert "title" in node.output_ports
        assert "link" in node.output_ports
        assert "description" in node.output_ports
        assert "exec_out" in node.output_ports

    def test_rssfeed_returns_correct_trigger_type(self) -> None:
        """Test RSSFeedTriggerNode returns RSS_FEED trigger type."""
        from casare_rpa.nodes.trigger_nodes import RSSFeedTriggerNode

        node = RSSFeedTriggerNode(node_id="rss_1")

        assert node.get_trigger_type() == TriggerType.RSS_FEED


class TestSSETriggerNode:
    """Tests for SSETriggerNode - Server-Sent Events trigger."""

    @pytest.mark.asyncio
    async def test_sse_executes_successfully(self, execution_context) -> None:
        """Test SSETriggerNode executes as pass-through."""
        from casare_rpa.nodes.trigger_nodes import SSETriggerNode

        node = SSETriggerNode(node_id="sse_1")

        result = await node.execute(execution_context)

        assert result["success"] is True

    def test_sse_has_sse_output_ports(self) -> None:
        """Test SSETriggerNode has expected output ports."""
        from casare_rpa.nodes.trigger_nodes import SSETriggerNode

        node = SSETriggerNode(node_id="sse_1")

        assert "event_type" in node.output_ports
        assert "data" in node.output_ports
        assert "exec_out" in node.output_ports

    def test_sse_returns_correct_trigger_type(self) -> None:
        """Test SSETriggerNode returns SSE trigger type."""
        from casare_rpa.nodes.trigger_nodes import SSETriggerNode

        node = SSETriggerNode(node_id="sse_1")

        assert node.get_trigger_type() == TriggerType.SSE


class TestTriggerNodePopulatePayload:
    """Tests for trigger payload population."""

    def test_populate_from_trigger_event(self) -> None:
        """Test trigger node can populate output ports from event payload."""
        from casare_rpa.nodes.trigger_nodes import WebhookTriggerNode

        node = WebhookTriggerNode(node_id="webhook_1")

        # Simulate trigger event payload
        payload = {
            "payload": {"user": "test", "action": "click"},
            "headers": {"Content-Type": "application/json"},
            "query_params": {"id": "123"},
            "method": "POST",
        }

        node.populate_from_trigger_event(payload)

        # Verify output ports are populated
        assert node.output_ports["payload"].get_value() == payload["payload"]
        assert node.output_ports["headers"].get_value() == payload["headers"]
        assert node.output_ports["method"].get_value() == "POST"

    def test_populate_ignores_unknown_fields(self) -> None:
        """Test populate_from_trigger_event ignores unknown payload fields."""
        from casare_rpa.nodes.trigger_nodes import WebhookTriggerNode

        node = WebhookTriggerNode(node_id="webhook_1")

        # Payload with unknown fields
        payload = {
            "payload": {"data": "value"},
            "unknown_field": "ignored",
            "another_unknown": 123,
        }

        # Should not raise error
        node.populate_from_trigger_event(payload)

        assert node.output_ports["payload"].get_value() == {"data": "value"}


class TestTriggerNodeListeningState:
    """Tests for trigger listening state management."""

    def test_trigger_initially_not_listening(self) -> None:
        """Test trigger nodes start in not-listening state."""
        from casare_rpa.nodes.trigger_nodes import WebhookTriggerNode

        node = WebhookTriggerNode(node_id="webhook_1")

        assert node.is_listening is False

    def test_set_listening_state(self) -> None:
        """Test setting trigger listening state."""
        from casare_rpa.nodes.trigger_nodes import WebhookTriggerNode

        node = WebhookTriggerNode(node_id="webhook_1")

        node.set_listening(True)
        assert node.is_listening is True

        node.set_listening(False)
        assert node.is_listening is False
