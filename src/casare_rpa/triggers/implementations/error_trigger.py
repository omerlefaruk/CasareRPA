"""
CasareRPA - Error Trigger

Trigger that fires when a workflow fails with an error.
Useful for error handling, notifications, and retry logic.
"""

import asyncio
import re
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional

from loguru import logger

from casare_rpa.triggers.base import (
    BaseTrigger,
    BaseTriggerConfig,
    TriggerStatus,
    TriggerType,
)
from casare_rpa.triggers.registry import register_trigger


@register_trigger
class ErrorTrigger(BaseTrigger):
    """
    Trigger that fires when workflows encounter errors.

    Configuration options:
        source_scenario_ids: List of scenario IDs to monitor (empty = all)
        error_types: Types of errors to catch
        error_pattern: Regex pattern for error messages
        min_severity: Minimum severity level (info, warning, error, critical)
        exclude_self: Don't trigger on errors from this scenario's workflows

    Payload provided to workflow:
        error_message: The error message
        error_type: Type of error
        failed_scenario_id: ID of the scenario that failed
        failed_workflow_id: ID of the workflow that failed
        failed_node_id: ID of the node that failed
        stack_trace: Full stack trace if available
        timestamp: When the error occurred
    """

    trigger_type = TriggerType.ERROR
    display_name = "Error Trigger"
    description = "Trigger when another workflow fails"
    icon = "alert-triangle"
    category = "Control"

    def __init__(self, config: BaseTriggerConfig, event_callback=None):
        super().__init__(config, event_callback)
        self._event_handler: Optional[Callable] = None

    async def start(self) -> bool:
        """Start the error trigger."""
        try:
            from casare_rpa.domain.events import get_event_bus, WorkflowFailed

            event_bus = get_event_bus()

            # Create event handler
            self._event_handler = lambda event: asyncio.create_task(self._on_workflow_error(event))

            # Subscribe to workflow error events
            event_bus.subscribe(WorkflowFailed, self._event_handler)

            self._status = TriggerStatus.ACTIVE
            logger.info(f"Error trigger started: {self.config.name}")
            return True

        except Exception as e:
            self._error_message = f"Failed to start error trigger: {e}"
            self._status = TriggerStatus.ERROR
            logger.error(self._error_message)
            return False

    async def stop(self) -> bool:
        """Stop the error trigger."""
        try:
            from casare_rpa.domain.events import get_event_bus, WorkflowFailed

            if self._event_handler:
                event_bus = get_event_bus()
                event_bus.unsubscribe(WorkflowFailed, self._event_handler)
                self._event_handler = None

        except Exception as e:
            logger.warning(f"Error unsubscribing from events: {e}")

        self._status = TriggerStatus.INACTIVE
        logger.info(f"Error trigger stopped: {self.config.name}")
        return True

    async def _on_workflow_error(self, event) -> None:
        """Handle workflow error event (WorkflowFailed typed event)."""
        config = self.config.config

        # Extract error details from typed WorkflowFailed event
        error_message = getattr(event, "error_message", "Unknown error")
        error_type = "workflow_failed"
        scenario_id = ""  # Not available in typed event
        workflow_id = getattr(event, "workflow_id", "")
        node_id = getattr(event, "failed_node_id", "") or ""
        stack_trace = getattr(event, "stack_trace", "") or ""

        # Check if we should exclude self
        if config.get("exclude_self", True):
            if scenario_id == self.config.scenario_id:
                return

        # Check source scenario filter
        source_scenario_ids = config.get("source_scenario_ids", [])
        if source_scenario_ids and scenario_id not in source_scenario_ids:
            return

        # Check error type filter
        error_types = config.get("error_types", [])
        if error_types and error_type not in error_types:
            return

        # Check error pattern filter
        error_pattern = config.get("error_pattern", "")
        if error_pattern:
            if not re.search(error_pattern, error_message, re.IGNORECASE):
                return

        # Check severity filter
        min_severity = config.get("min_severity", "error")
        severity_levels = {"info": 0, "warning": 1, "error": 2, "critical": 3}
        event_severity = getattr(event, "severity", "error")
<<<<<<< HEAD
        if severity_levels.get(event_severity, 2) < severity_levels.get(
            min_severity, 2
        ):
=======
        if severity_levels.get(event_severity, 2) < severity_levels.get(min_severity, 2):
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e
            return

        # Build payload
        payload = {
            "error_message": error_message,
            "error_type": error_type,
            "failed_scenario_id": scenario_id,
            "failed_workflow_id": workflow_id,
            "failed_node_id": node_id,
            "stack_trace": stack_trace,
            "severity": event_severity,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        metadata = {
            "source": "error",
            "original_event_type": "WORKFLOW_ERROR",
        }

        await self.emit(payload, metadata)

    def validate_config(self) -> tuple[bool, Optional[str]]:
        """Validate error trigger configuration."""
        config = self.config.config

        # Validate min_severity
        min_severity = config.get("min_severity", "error")
        valid_severities = ["info", "warning", "error", "critical"]
        if min_severity not in valid_severities:
            return False, f"Invalid min_severity. Must be one of: {valid_severities}"

        # Validate error_pattern is valid regex
        error_pattern = config.get("error_pattern", "")
        if error_pattern:
            try:
                re.compile(error_pattern)
            except re.error as e:
                return False, f"Invalid error_pattern regex: {e}"

        return True, None

    @classmethod
    def get_config_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for error trigger configuration."""
        return {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Trigger name"},
                "enabled": {"type": "boolean", "default": True},
                "priority": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 3,
                    "default": 2,
                },
                "cooldown_seconds": {"type": "integer", "minimum": 0, "default": 0},
                "source_scenario_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "default": [],
                    "description": "Scenario IDs to monitor (empty = all)",
                },
                "error_types": {
                    "type": "array",
                    "items": {"type": "string"},
                    "default": [],
                    "description": "Error types to catch",
                },
                "error_pattern": {
                    "type": "string",
                    "description": "Regex pattern for error messages",
                },
                "min_severity": {
                    "type": "string",
                    "enum": ["info", "warning", "error", "critical"],
                    "default": "error",
                    "description": "Minimum severity level",
                },
                "exclude_self": {
                    "type": "boolean",
                    "default": True,
                    "description": "Don't trigger on errors from this scenario",
                },
            },
            "required": ["name"],
        }
