"""
User Notification and Escalation Patterns

When automated recovery fails, notify humans appropriately.

Patterns covered:
1. In-workflow notification (toast/balloon during execution)
2. Post-workflow escalation (email, dashboard alert)
3. Screenshot capture for UI errors
4. Interactive retry prompt (for attended robots)
"""

from dataclasses import dataclass
from typing import Any

from loguru import logger

from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.events import NodeFailed, get_event_bus
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import DataType


@dataclass
class NotificationConfig:
    """Configuration for user notifications."""

    level: str  # "info", "warning", "error", "critical"
    title: str
    message: str
    action_button: str | None = None
    dismiss_after_ms: int = 5000
    requires_acknowledgment: bool = False


class NotificationHelper:
    """Helper for creating structured notifications."""

    @staticmethod
    def error(title: str, message: str, action: str | None = None) -> NotificationConfig:
        return NotificationConfig(
            level="error",
            title=title,
            message=message,
            action_button=action,
            requires_acknowledgment=True,
        )

    @staticmethod
    def warning(title: str, message: str) -> NotificationConfig:
        return NotificationConfig(
            level="warning",
            title=title,
            message=message,
            dismiss_after_ms=10000,
        )

    @staticmethod
    def info(title: str, message: str) -> NotificationConfig:
        return NotificationConfig(
            level="info",
            title=title,
            message=message,
            dismiss_after_ms=5000,
        )


@properties(
    PropertyDef("notification_config", PropertyType.JSON, required=True),
)
@node(category="system")
class NotifyUserNode(BaseNode):
    """
    Display notification to user during workflow execution.

    For attended RPA scenarios where a human is monitoring.
    Supports toast messages, interactive prompts, and escalation.
    """

    def _define_ports(self) -> None:
        self.add_exec_input()
        self.add_exec_output("acknowledged")
        self.add_exec_output("dismissed")
        self.add_exec_output("timed_out")

        self.add_input_port("notification_config", DataType.DICT)
        self.add_output_port("user_response", DataType.STRING)

    async def execute(self, context) -> dict:
        config_dict = self.get_parameter("notification_config")
        config = NotificationConfig(**config_dict)

        # Publish notification event (presentation layer will display)
        event_bus = get_event_bus()
        event_bus.publish(
            NodeFailed(
                node_id=self.node_id,
                node_type=self.node_type,
                workflow_id=context.get_variable("workflow_id", ""),
                error_message=f"{config.title}: {config.message}",
                is_retryable=False,
            )
        )

        # Log based on severity
        if config.level == "critical":
            logger.error(f"CRITICAL: {config.title} - {config.message}")
        elif config.level == "error":
            logger.error(f"ERROR: {config.title} - {config.message}")
        elif config.level == "warning":
            logger.warning(f"WARNING: {config.title} - {config.message}")
        else:
            logger.info(f"INFO: {config.title} - {config.message}")

        # Store for UI consumption
        context.set_variable(
            "_notification", config.to_dict() if hasattr(config, "to_dict") else config_dict
        )

        # Route based on acknowledgment requirement
        if config.requires_acknowledgment:
            self.set_output_value("user_response", "awaiting_ack")
            return {"success": True, "next_nodes": ["acknowledged"]}
        else:
            return {"success": True, "next_nodes": ["dismissed"]}


@properties(
    PropertyDef("recipients", PropertyType.JSON, required=True),
    PropertyDef("subject", PropertyType.STRING, required=True),
    PropertyDef("body_template", PropertyType.TEXT, required=True),
    PropertyDef("include_screenshot", PropertyType.BOOLEAN, default=False),
)
@node(category="google")
class EscalateErrorNode(BaseNode):
    """
        Escalate error via email with context.

        Sends detailed error report including:
    - Error message and stack trace
    - Node and workflow context
    - Variable values (sanitized)
    - Screenshot (if UI error and enabled)
    """

    def _define_ports(self) -> None:
        self.add_exec_input()
        self.add_exec_output()

        self.add_input_port("error_context", DataType.DICT)
        self.add_input_port("recipients", DataType.LIST)
        self.add_output_port("escalation_id", DataType.STRING)

    async def execute(self, context) -> dict:
        recipients = self.get_parameter("recipients")
        subject = self.get_parameter("subject")
        body_template = self.get_parameter("body_template")
        include_screenshot = self.get_parameter("include_screenshot", False)

        error_context = self.get_input_value("error_context", {})

        # Build email body
        body = self._build_error_body(
            template=body_template,
            error_context=error_context,
            workflow_id=context.get_variable("workflow_id", "unknown"),
            node_id=self.node_id,
        )

        # Capture screenshot if enabled and relevant
        screenshot_path = None
        if include_screenshot and error_context.get("is_ui_error"):
            screenshot_path = await self._capture_screenshot(context)
            body += f"\n\nScreenshot attached: {screenshot_path}"

        # Send escalation email
        escalation_id = await self._send_escalation_email(
            recipients=recipients,
            subject=f"[ESCALATION] {subject}",
            body=body,
            screenshot_path=screenshot_path,
        )

        logger.info(f"Error escalated to {len(recipients)} recipients: {escalation_id}")
        self.set_output_value("escalation_id", escalation_id)

        return {"success": True, "next_nodes": ["exec_out"]}

    def _build_error_body(
        self,
        template: str,
        error_context: dict,
        workflow_id: str,
        node_id: str,
    ) -> str:
        """Build formatted error email body."""
        body = "Workflow Error Escalation\n"
        body += "=" * 40 + "\n\n"
        body += f"Workflow ID: {workflow_id}\n"
        body += f"Node ID: {node_id}\n"
        body += f"Error: {error_context.get('message', 'Unknown error')}\n"
        body += f"Time: {error_context.get('timestamp', 'Unknown')}\n\n"

        if "stack_trace" in error_context:
            body += f"Stack Trace:\n{error_context['stack_trace']}\n\n"

        if "additional_data" in error_context:
            body += "Additional Context:\n"
            for key, value in error_context["additional_data"].items():
                body += f"  {key}: {value}\n"

        body += f"\n{template}"
        return body

    async def _capture_screenshot(self, context) -> str | None:
        """Capture screenshot of current page state."""
        try:
            page = context.get_active_page()
            if page:
                path = f"error_screenshots/{self.node_id}_{context.get_variable('workflow_id')}.png"
                await page.screenshot(path=path)
                return path
        except Exception as exc:
            logger.warning(f"Screenshot capture failed: {exc}")
        return None

    async def _send_escalation_email(
        self,
        recipients: list[str],
        subject: str,
        body: str,
        screenshot_path: str | None,
    ) -> str:
        """Send escalation email (simplified)."""
        import time

        escalation_id = f"esc_{int(time.time())}"
        # In production, use GmailClient
        return escalation_id


@properties(
    PropertyDef("error_message", PropertyType.STRING, required=True),
    PropertyDef("max_retries", PropertyType.INTEGER, default=3),
    PropertyDef("timeout_seconds", PropertyType.INTEGER, default=60),
)
@node(category="control_flow")
class InteractiveRetryNode(BaseNode):
    """
    Pause execution and prompt user for action.

    For attended RPA where human can:
    - Fix the issue and click retry
    - Skip the failed operation
    - Abort the workflow
    """

    def _define_ports(self) -> None:
        self.add_exec_input()
        self.add_exec_output("retry")
        self.add_exec_output("skip")
        self.add_exec_output("abort")

        self.add_input_port("error_message", DataType.STRING)
        self.add_output_port("user_action", DataType.STRING)

    async def execute(self, context) -> dict:
        error_message = self.get_parameter("error_message")
        timeout = self.get_parameter("timeout_seconds", 60)

        # Set prompt in context for UI to display
        prompt_data = {
            "type": "error_prompt",
            "message": error_message,
            "options": ["retry", "skip", "abort"],
            "timeout": timeout,
        }
        context.set_variable("_user_prompt", prompt_data)

        logger.info(f"Awaiting user response for error: {error_message}")

        # In production, this would wait for UI event
        # For now, return retry as default
        user_action = "retry"  # Default action

        self.set_output_value("user_action", user_action)

        route_map = {
            "retry": "retry",
            "skip": "skip",
            "abort": "abort",
        }

        return {"success": True, "next_nodes": [route_map.get(user_action, "abort")]}


__all__ = [
    "NotifyUserNode",
    "EscalateErrorNode",
    "InteractiveRetryNode",
    "NotificationHelper",
]
