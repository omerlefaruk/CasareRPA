"""
Error handling nodes for CasareRPA.

This module implements error handling capabilities including try/catch,
retry logic, error throwing, notifications, and recovery strategies
for robust workflow execution.
"""

from typing import Any, Optional, Dict
from loguru import logger
import asyncio
import json

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.decorators import executable_node, node_schema
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.domain.value_objects.types import (
    PortType,
    DataType,
    NodeStatus,
    ExecutionResult,
)


@executable_node
class TryNode(BaseNode):
    """
    Try block node for error handling.

    Wraps a section of workflow to catch errors. If the try block succeeds,
    execution continues to 'success' output. If an error occurs, routes to
    'catch' output with error details.
    """

    def __init__(self, node_id: str, config: Optional[dict] = None) -> None:
        """Initialize Try node."""
        super().__init__(node_id, config)
        self.name = "Try"
        self.node_type = "TryNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_output_port("try_body", PortType.EXEC_OUTPUT)
        self.add_output_port("success", PortType.EXEC_OUTPUT)
        self.add_output_port("catch", PortType.EXEC_OUTPUT)
        self.add_output_port("error_message", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("error_type", PortType.OUTPUT, DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Execute try block.

        This node marks the beginning of a try block. The actual error catching
        happens in the WorkflowRunner which monitors execution of the try_body.

        Args:
            context: Execution context

        Returns:
            Result routing to try_body for initial execution
        """
        self.status = NodeStatus.RUNNING

        try:
            # Store try block state
            try_state_key = f"{self.node_id}_state"

            if try_state_key not in context.variables:
                # First execution - enter try block
                context.variables[try_state_key] = {
                    "in_try_block": True,
                    "error_occurred": False,
                }
                logger.info(f"Entering try block: {self.node_id}")

                self.status = NodeStatus.SUCCESS
                return {"success": True, "next_nodes": ["try_body"]}
            else:
                # Returning from try block
                try_state = context.variables[try_state_key]
                del context.variables[try_state_key]

                if try_state.get("error_occurred"):
                    # Error occurred - route to catch
                    error_msg = try_state.get("error_message", "Unknown error")
                    error_type = try_state.get("error_type", "Exception")

                    self.set_output_value("error_message", error_msg)
                    self.set_output_value("error_type", error_type)

                    logger.warning(
                        f"Error caught in try block: {error_type}: {error_msg}"
                    )

                    self.status = NodeStatus.SUCCESS
                    return {
                        "success": True,
                        "data": {"error_message": error_msg, "error_type": error_type},
                        "next_nodes": ["catch"],
                    }
                else:
                    # No error - route to success
                    logger.info(f"Try block completed successfully: {self.node_id}")

                    self.status = NodeStatus.SUCCESS
                    return {"success": True, "next_nodes": ["success"]}

        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"Try node execution failed: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}


@node_schema(
    PropertyDef(
        "max_attempts",
        PropertyType.INTEGER,
        default=3,
        min_value=1,
        label="Max Attempts",
        tooltip="Maximum number of retry attempts",
    ),
    PropertyDef(
        "initial_delay",
        PropertyType.FLOAT,
        default=1.0,
        min_value=0.0,
        label="Initial Delay (seconds)",
        tooltip="Initial delay before first retry",
    ),
    PropertyDef(
        "backoff_multiplier",
        PropertyType.FLOAT,
        default=2.0,
        min_value=1.0,
        label="Backoff Multiplier",
        tooltip="Exponential backoff multiplier for retry delays",
    ),
)
@executable_node
class RetryNode(BaseNode):
    """
    Retry node for automatic retry with backoff.

    Retries a failed operation multiple times with configurable delay and
    exponential backoff. Useful for handling transient failures.
    """

    def __init__(self, node_id: str, config: Optional[dict] = None) -> None:
        """Initialize Retry node."""
        super().__init__(node_id, config)
        self.name = "Retry"
        self.node_type = "RetryNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_output_port("retry_body", PortType.EXEC_OUTPUT)
        self.add_output_port("success", PortType.EXEC_OUTPUT)
        self.add_output_port("failed", PortType.EXEC_OUTPUT)
        self.add_output_port("attempt", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("last_error", PortType.OUTPUT, DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Execute retry logic.

        Args:
            context: Execution context

        Returns:
            Result with retry routing
        """
        self.status = NodeStatus.RUNNING

        try:
            max_attempts = self.get_parameter("max_attempts", 3)
            initial_delay = self.get_parameter("initial_delay", 1.0)
            backoff_multiplier = self.get_parameter("backoff_multiplier", 2.0)

            retry_state_key = f"{self.node_id}_retry_state"

            if retry_state_key not in context.variables:
                # First attempt
                context.variables[retry_state_key] = {
                    "attempt": 0,
                    "max_attempts": max_attempts,
                    "initial_delay": initial_delay,
                    "backoff_multiplier": backoff_multiplier,
                    "last_error": None,
                }

            retry_state = context.variables[retry_state_key]
            retry_state["attempt"] += 1
            current_attempt = retry_state["attempt"]

            self.set_output_value("attempt", current_attempt)

            if current_attempt <= max_attempts:
                # Attempt execution
                if current_attempt > 1:
                    # Apply delay with exponential backoff (except for first attempt)
                    delay = initial_delay * (
                        backoff_multiplier ** (current_attempt - 2)
                    )
                    logger.info(
                        f"Retry attempt {current_attempt}/{max_attempts} after {delay:.2f}s delay"
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.info(
                        f"Retry attempt {current_attempt}/{max_attempts} (initial)"
                    )

                self.status = NodeStatus.RUNNING
                return {
                    "success": True,
                    "data": {"attempt": current_attempt},
                    "next_nodes": ["retry_body"],
                }
            else:
                # Max attempts reached - fail
                last_error = retry_state.get(
                    "last_error", "Max retry attempts exceeded"
                )
                self.set_output_value("last_error", last_error)

                logger.error(
                    f"Retry failed after {max_attempts} attempts: {last_error}"
                )

                # Clean up state
                del context.variables[retry_state_key]

                self.status = NodeStatus.ERROR
                return {
                    "success": False,
                    "data": {"attempts": max_attempts, "last_error": last_error},
                    "next_nodes": ["failed"],
                }

        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"Retry node execution failed: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}


@executable_node
class RetrySuccessNode(BaseNode):
    """
    Marks successful completion of retry body.

    This node signals that the retry operation succeeded and should exit
    the retry loop.
    """

    def __init__(self, node_id: str, config: Optional[dict] = None) -> None:
        """Initialize RetrySuccess node."""
        super().__init__(node_id, config)
        self.name = "Retry Success"
        self.node_type = "RetrySuccessNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        pass  # exec_in and exec_out added by @executable_node decorator

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Signal retry success.

        Args:
            context: Execution context

        Returns:
            Result with success signal
        """
        self.status = NodeStatus.RUNNING

        try:
            logger.info("Retry operation succeeded")

            self.status = NodeStatus.SUCCESS
            return {
                "success": True,
                "control_flow": "retry_success",
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"RetrySuccess execution failed: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}


@executable_node
class RetryFailNode(BaseNode):
    """
    Marks failed attempt in retry body.

    This node signals that the retry operation failed and should be retried.
    """

    def __init__(self, node_id: str, config: Optional[dict] = None) -> None:
        """Initialize RetryFail node."""
        super().__init__(node_id, config)
        self.name = "Retry Fail"
        self.node_type = "RetryFailNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("error_message", PortType.INPUT, DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Signal retry failure.

        Args:
            context: Execution context

        Returns:
            Result with failure signal
        """
        self.status = NodeStatus.RUNNING

        try:
            error_message = self.get_input_value("error_message") or "Operation failed"

            logger.warning(f"Retry attempt failed: {error_message}")

            self.status = NodeStatus.SUCCESS
            return {
                "success": True,
                "control_flow": "retry_fail",
                "data": {"error_message": error_message},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"RetryFail execution failed: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}


@node_schema(
    PropertyDef(
        "error_message",
        PropertyType.STRING,
        default="Custom error",
        label="Error Message",
        tooltip="Error message to throw",
        placeholder="Something went wrong",
    ),
)
@executable_node
class ThrowErrorNode(BaseNode):
    """
    Throws a custom error to trigger error handling.

    Intentionally raises an error with a custom message to trigger
    try/catch blocks or other error handling mechanisms.
    """

    def __init__(self, node_id: str, config: Optional[dict] = None) -> None:
        """Initialize ThrowError node."""
        super().__init__(node_id, config)
        self.name = "Throw Error"
        self.node_type = "ThrowErrorNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("error_message", PortType.INPUT, DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Throw error.

        Args:
            context: Execution context

        Returns:
            Result with error
        """
        self.status = NodeStatus.RUNNING

        try:
            error_message = self.get_parameter("error_message", "Custom error")

            logger.error(f"Throwing error: {error_message}")

            self.status = NodeStatus.ERROR
            return {
                "success": False,
                "error": error_message,
                "error_type": "CustomError",
                "next_nodes": [],
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"ThrowError node failed: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}


@node_schema(
    PropertyDef(
        "webhook_url",
        PropertyType.STRING,
        required=True,
        label="Webhook URL",
        tooltip="URL to send webhook notification to",
        placeholder="https://hooks.slack.com/services/...",
    ),
    PropertyDef(
        "message",
        PropertyType.STRING,
        default="Error notification from CasareRPA",
        label="Message",
        tooltip="Notification message",
    ),
    PropertyDef(
        "format",
        PropertyType.CHOICE,
        default="generic",
        choices=["generic", "slack", "discord", "teams"],
        label="Format",
        tooltip="Webhook payload format",
    ),
    PropertyDef(
        "timeout",
        PropertyType.INTEGER,
        default=30,
        min_value=1,
        label="Timeout (seconds)",
        tooltip="Request timeout in seconds",
    ),
    PropertyDef(
        "retry_count",
        PropertyType.INTEGER,
        default=0,
        min_value=0,
        label="Retry Count",
        tooltip="Number of retry attempts",
    ),
    PropertyDef(
        "retry_delay",
        PropertyType.FLOAT,
        default=2.0,
        min_value=0.0,
        label="Retry Delay (seconds)",
        tooltip="Delay between retries",
    ),
)
@executable_node
class WebhookNotifyNode(BaseNode):
    """
    Send error notifications via webhook.

    Sends HTTP POST requests to configured webhook URLs when errors occur,
    enabling integration with Slack, Teams, Discord, or custom endpoints.
    """

    def __init__(self, node_id: str, config: Optional[dict] = None) -> None:
        """Initialize WebhookNotify node."""
        super().__init__(node_id, config)
        self.name = "Webhook Notify"
        self.node_type = "WebhookNotifyNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("webhook_url", PortType.INPUT, DataType.STRING)
        self.add_input_port("message", PortType.INPUT, DataType.STRING)
        self.add_input_port("error_details", PortType.INPUT, DataType.DICT)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("response", PortType.OUTPUT, DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Send webhook notification.

        Args:
            context: Execution context

        Returns:
            Result with notification status
        """
        self.status = NodeStatus.RUNNING

        try:
            webhook_url = self.get_parameter("webhook_url")
            message = self.get_parameter("message", "Error notification from CasareRPA")
            error_details = self.get_input_value("error_details") or {}
            format_type = self.get_parameter("format", "generic")
            timeout_seconds = self.get_parameter("timeout", 30)
            retry_count = self.get_parameter("retry_count", 0)
            retry_delay = self.get_parameter("retry_delay", 2.0)

            if not webhook_url:
                self.set_output_value("success", False)
                self.set_output_value("response", "No webhook URL provided")
                self.status = NodeStatus.ERROR
                return {
                    "success": False,
                    "error": "No webhook URL provided",
                    "next_nodes": ["exec_out"],
                }

            # Build payload
            payload = self._build_payload(format_type, message, error_details)

            # Send webhook with retry
            import aiohttp

            for attempt in range(max(1, retry_count + 1)):
                try:
                    async with aiohttp.ClientSession() as session:
                        timeout = aiohttp.ClientTimeout(total=timeout_seconds)
                        headers = {"Content-Type": "application/json"}

                        async with session.post(
                            webhook_url, json=payload, headers=headers, timeout=timeout
                        ) as response:
                            response_text = await response.text()
                            success = response.status < 400

                            self.set_output_value("success", success)
                            self.set_output_value("response", response_text)

                            if success:
                                logger.info(
                                    f"Webhook notification sent successfully to {webhook_url} (attempt {attempt + 1})"
                                )
                                self.status = NodeStatus.SUCCESS
                                return {
                                    "success": True,
                                    "data": {
                                        "response": response_text,
                                        "attempts": attempt + 1,
                                    },
                                    "next_nodes": ["exec_out"],
                                }
                            else:
                                logger.warning(
                                    f"Webhook notification failed: {response.status}"
                                )
                                self.status = (
                                    NodeStatus.SUCCESS
                                )  # Node succeeded, webhook failed
                                return {
                                    "success": True,
                                    "data": {
                                        "webhook_failed": True,
                                        "status": response.status,
                                    },
                                    "next_nodes": ["exec_out"],
                                }

                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    if attempt < retry_count:
                        logger.warning(
                            f"Webhook request failed (attempt {attempt + 1}/{retry_count + 1}): {e}"
                        )
                        await asyncio.sleep(retry_delay)
                    else:
                        raise

        except ImportError:
            self.set_output_value("success", False)
            self.set_output_value("response", "aiohttp not installed")
            self.status = NodeStatus.ERROR
            logger.error("aiohttp required for webhook notifications")
            return {
                "success": False,
                "error": "aiohttp package required. Install with: pip install aiohttp",
                "next_nodes": [],
            }
        except Exception as e:
            self.set_output_value("success", False)
            self.set_output_value("response", str(e))
            self.status = NodeStatus.ERROR
            logger.error(f"Webhook notification failed: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}

    def _build_payload(
        self, format_type: str, message: str, error_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build webhook payload based on configured format."""
        if format_type == "slack":
            return {
                "text": message,
                "attachments": [
                    {
                        "color": "danger",
                        "title": "Error Details",
                        "fields": [
                            {"title": k, "value": str(v), "short": True}
                            for k, v in error_details.items()
                        ],
                    }
                ]
                if error_details
                else [],
            }
        elif format_type == "discord":
            return {
                "content": message,
                "embeds": [
                    {
                        "title": "Error Details",
                        "color": 15158332,  # Red
                        "fields": [
                            {"name": k, "value": str(v)[:1024], "inline": True}
                            for k, v in error_details.items()
                        ],
                    }
                ]
                if error_details
                else [],
            }
        elif format_type == "teams":
            return {
                "@type": "MessageCard",
                "themeColor": "FF0000",
                "summary": message,
                "sections": [
                    {
                        "activityTitle": message,
                        "facts": [
                            {"name": k, "value": str(v)}
                            for k, v in error_details.items()
                        ],
                    }
                ],
            }
        else:
            # Generic format
            return {
                "message": message,
                "details": error_details,
                "source": "CasareRPA",
            }


@executable_node
class OnErrorNode(BaseNode):
    """
    Global error handler node.

    Catches unhandled errors in the workflow and routes to configured
    error handling path. Can be placed anywhere in workflow to catch
    errors from connected nodes.
    """

    def __init__(self, node_id: str, config: Optional[dict] = None) -> None:
        """Initialize OnError node."""
        super().__init__(node_id, config)
        self.name = "On Error"
        self.node_type = "OnErrorNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_output_port("protected_body", PortType.EXEC_OUTPUT)
        self.add_output_port("on_error", PortType.EXEC_OUTPUT)
        self.add_output_port("finally", PortType.EXEC_OUTPUT)
        self.add_output_port("error_message", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("error_type", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("error_node", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("stack_trace", PortType.OUTPUT, DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Execute global error handler.

        Args:
            context: Execution context

        Returns:
            Result routing to protected body or error handler
        """
        self.status = NodeStatus.RUNNING

        try:
            error_state_key = f"{self.node_id}_error_state"

            if error_state_key not in context.variables:
                # First execution - enter protected block
                context.variables[error_state_key] = {
                    "in_protected_block": True,
                    "error_occurred": False,
                    "finally_executed": False,
                }
                logger.info(f"Entering protected block: {self.node_id}")

                self.status = NodeStatus.SUCCESS
                return {"success": True, "next_nodes": ["protected_body"]}
            else:
                # Returning from protected block
                error_state = context.variables[error_state_key]

                if error_state.get("error_occurred") and not error_state.get(
                    "error_handled"
                ):
                    # Error occurred - route to error handler
                    error_msg = error_state.get("error_message", "Unknown error")
                    error_type = error_state.get("error_type", "Exception")
                    error_node = error_state.get("error_node", "")
                    stack_trace = error_state.get("stack_trace", "")

                    self.set_output_value("error_message", error_msg)
                    self.set_output_value("error_type", error_type)
                    self.set_output_value("error_node", error_node)
                    self.set_output_value("stack_trace", stack_trace)

                    error_state["error_handled"] = True

                    logger.warning(
                        f"Error caught by OnError handler: {error_type}: {error_msg}"
                    )

                    self.status = NodeStatus.SUCCESS
                    return {
                        "success": True,
                        "data": {
                            "error_message": error_msg,
                            "error_type": error_type,
                            "error_node": error_node,
                        },
                        "next_nodes": ["on_error"],
                    }
                elif not error_state.get("finally_executed"):
                    # Execute finally block
                    error_state["finally_executed"] = True

                    logger.info(f"Executing finally block: {self.node_id}")

                    self.status = NodeStatus.SUCCESS
                    return {"success": True, "next_nodes": ["finally"]}
                else:
                    # Cleanup and exit
                    del context.variables[error_state_key]

                    self.status = NodeStatus.SUCCESS
                    return {"success": True, "next_nodes": []}

        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"OnError node execution failed: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}


@node_schema(
    PropertyDef(
        "strategy",
        PropertyType.CHOICE,
        default="stop",
        choices=["stop", "continue", "retry", "restart", "fallback"],
        label="Strategy",
        tooltip="Error recovery strategy",
    ),
    PropertyDef(
        "max_retries",
        PropertyType.INTEGER,
        default=3,
        min_value=0,
        label="Max Retries",
        tooltip="Maximum retries for 'retry' strategy",
    ),
)
@executable_node
class ErrorRecoveryNode(BaseNode):
    """
    Configure error recovery strategy for workflow.

    Sets the recovery behavior when errors occur:
    - stop: Stop workflow execution
    - continue: Skip failed node and continue
    - retry: Retry the failed operation
    - restart: Restart the entire workflow
    - fallback: Execute a fallback path
    """

    def __init__(self, node_id: str, config: Optional[dict] = None) -> None:
        """Initialize ErrorRecovery node."""
        super().__init__(node_id, config)
        self.name = "Error Recovery"
        self.node_type = "ErrorRecoveryNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("strategy", PortType.INPUT, DataType.STRING)
        self.add_input_port("max_retries", PortType.INPUT, DataType.INTEGER)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("fallback", PortType.EXEC_OUTPUT)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Configure error recovery.

        Args:
            context: Execution context

        Returns:
            Result with recovery configuration
        """
        self.status = NodeStatus.RUNNING

        try:
            strategy = self.get_parameter("strategy", "stop")
            max_retries = self.get_parameter("max_retries", 3)

            # Valid strategies
            valid_strategies = ["stop", "continue", "retry", "restart", "fallback"]
            if strategy not in valid_strategies:
                strategy = "stop"

            # Store recovery config in context
            context.variables["_error_recovery_strategy"] = strategy
            context.variables["_error_recovery_max_retries"] = max_retries

            logger.info(
                f"Error recovery configured: strategy={strategy}, max_retries={max_retries}"
            )

            self.status = NodeStatus.SUCCESS
            return {
                "success": True,
                "data": {"strategy": strategy, "max_retries": max_retries},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"ErrorRecovery node failed: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}


@node_schema(
    PropertyDef(
        "level",
        PropertyType.CHOICE,
        default="error",
        choices=["debug", "info", "warning", "error", "critical"],
        label="Log Level",
        tooltip="Logging severity level",
    ),
    PropertyDef(
        "include_stack_trace",
        PropertyType.BOOLEAN,
        default=False,
        label="Include Stack Trace",
        tooltip="Include stack trace in log output",
    ),
)
@executable_node
class LogErrorNode(BaseNode):
    """
    Log error details with structured information.

    Captures error information and logs it with configurable
    severity level and format for debugging and monitoring.
    """

    def __init__(self, node_id: str, config: Optional[dict] = None) -> None:
        """Initialize LogError node."""
        super().__init__(node_id, config)
        self.name = "Log Error"
        self.node_type = "LogErrorNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("error_message", PortType.INPUT, DataType.STRING)
        self.add_input_port("error_type", PortType.INPUT, DataType.STRING)
        self.add_input_port("context", PortType.INPUT, DataType.DICT)
        self.add_output_port("log_entry", PortType.OUTPUT, DataType.DICT)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Log error details.

        Args:
            context: Execution context

        Returns:
            Result with log entry
        """
        self.status = NodeStatus.RUNNING

        try:
            error_message = self.get_input_value("error_message") or "Unknown error"
            error_type = self.get_input_value("error_type") or "Error"
            error_context = self.get_input_value("context") or {}
            level = self.get_parameter("level", "error")
            include_stack = self.get_parameter("include_stack_trace", False)

            # Build log entry
            from datetime import datetime

            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "level": level,
                "error_type": error_type,
                "error_message": error_message,
                "workflow": context.workflow_name,
                "context": error_context,
            }

            if include_stack:
                import traceback

                log_entry["stack_trace"] = traceback.format_exc()

            # Log with appropriate level
            log_message = f"[{error_type}] {error_message}"
            if error_context:
                log_message += f" | Context: {json.dumps(error_context)}"

            if level == "debug":
                logger.debug(log_message)
            elif level == "info":
                logger.info(log_message)
            elif level == "warning":
                logger.warning(log_message)
            elif level == "critical":
                logger.critical(log_message)
            else:
                logger.error(log_message)

            self.set_output_value("log_entry", log_entry)

            self.status = NodeStatus.SUCCESS
            return {
                "success": True,
                "data": {"log_entry": log_entry},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"LogError node failed: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}


@node_schema(
    PropertyDef(
        "condition",
        PropertyType.BOOLEAN,
        default=True,
        label="Condition",
        tooltip="Condition to assert (can be overridden by input port)",
    ),
    PropertyDef(
        "message",
        PropertyType.STRING,
        default="Assertion failed",
        label="Message",
        tooltip="Error message if assertion fails",
        placeholder="Expected value to be greater than 0",
    ),
)
@executable_node
class AssertNode(BaseNode):
    """
    Assert a condition and throw error if false.

    Validates that a condition is true, throwing an error with
    a custom message if the assertion fails. Useful for validation
    and debugging workflows.
    """

    def __init__(self, node_id: str, config: Optional[dict] = None) -> None:
        """Initialize Assert node."""
        super().__init__(node_id, config)
        self.name = "Assert"
        self.node_type = "AssertNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("condition", PortType.INPUT, DataType.BOOLEAN)
        self.add_input_port("message", PortType.INPUT, DataType.STRING)
        self.add_output_port("passed", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Execute assertion.

        Args:
            context: Execution context

        Returns:
            Result - success if assertion passes, error if fails
        """
        self.status = NodeStatus.RUNNING

        try:
            condition = self.get_parameter("condition", True)
            message = self.get_parameter("message", "Assertion failed")

            # Evaluate condition (handle strings)
            if isinstance(condition, str):
                condition = condition.lower() in ("true", "1", "yes")

            self.set_output_value("passed", bool(condition))

            if condition:
                logger.debug(f"Assertion passed: {message}")
                self.status = NodeStatus.SUCCESS
                return {
                    "success": True,
                    "data": {"passed": True},
                    "next_nodes": ["exec_out"],
                }
            else:
                logger.error(f"Assertion failed: {message}")
                self.status = NodeStatus.ERROR
                return {
                    "success": False,
                    "error": f"Assertion failed: {message}",
                    "error_type": "AssertionError",
                    "next_nodes": [],
                }

        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"Assert node failed: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}
