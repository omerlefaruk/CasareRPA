"""
CasareRPA - Workflow Call Trigger

Trigger that allows a workflow to be called from another workflow.
Enables sub-workflow and cross-workflow invocation patterns.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from loguru import logger

from casare_rpa.triggers.base import BaseTrigger, TriggerStatus, TriggerType
from casare_rpa.triggers.registry import register_trigger


@register_trigger
class WorkflowCallTrigger(BaseTrigger):
    """
    Trigger that enables workflow-to-workflow calls.

    This trigger allows a workflow to be invoked by other workflows
    using a callable alias. It's useful for:
    - Sub-workflow patterns (modular workflows)
    - Cross-project workflow invocation
    - API-like workflow endpoints

    Configuration options:
        call_alias: Unique alias for invoking this workflow
        synchronous: Wait for completion before returning
        input_schema: Expected input parameters schema
        output_mapping: Mapping of output variables to return
        allowed_callers: List of scenario IDs that can call this (empty = all)

    Payload provided to workflow:
        caller_scenario_id: ID of the calling scenario
        caller_workflow_id: ID of the calling workflow
        input_params: Parameters passed by the caller
        call_id: Unique identifier for this call
    """

    trigger_type = TriggerType.WORKFLOW_CALL
    display_name = "Workflow Call"
    description = "Allow this workflow to be called by other workflows"
    icon = "link"
    category = "Control"

    async def start(self) -> bool:
        """
        Start the workflow call trigger.

        The actual callable is registered with the TriggerManager,
        not handled directly by this trigger.
        """
        config = self.config.config
        call_alias = config.get("call_alias", "")

        if not call_alias:
            self._error_message = "call_alias is required"
            self._status = TriggerStatus.ERROR
            return False

        self._status = TriggerStatus.ACTIVE
        logger.info(f"Workflow call trigger started: {self.config.name} (alias: {call_alias})")
        return True

    async def stop(self) -> bool:
        """Stop the workflow call trigger."""
        self._status = TriggerStatus.INACTIVE
        logger.info(f"Workflow call trigger stopped: {self.config.name}")
        return True

    async def invoke(
        self,
        caller_scenario_id: str,
        caller_workflow_id: str,
        input_params: Optional[Dict[str, Any]] = None,
        call_id: Optional[str] = None,
    ) -> bool:
        """
        Invoke this trigger from another workflow.

        Called by TriggerManager.call_workflow() when a workflow
        uses the CallWorkflowNode to invoke this trigger's workflow.

        Args:
            caller_scenario_id: ID of the calling scenario
            caller_workflow_id: ID of the calling workflow
            input_params: Parameters passed by the caller
            call_id: Unique identifier for this call

        Returns:
            True if trigger was fired successfully
        """
        config = self.config.config

        # Check if caller is allowed
        allowed_callers = config.get("allowed_callers", [])
        if allowed_callers and caller_scenario_id not in allowed_callers:
            logger.warning(
                f"Workflow call from {caller_scenario_id} not allowed by {self.config.id}"
            )
            return False

        # Validate input parameters against schema
        input_schema = config.get("input_schema", {})
        if input_schema and input_params:
            # Basic schema validation (could be expanded)
            required_params = input_schema.get("required", [])
            for param in required_params:
                if param not in input_params:
                    logger.warning(f"Missing required parameter: {param}")
                    return False

        # Build payload
        payload = {
            "caller_scenario_id": caller_scenario_id,
            "caller_workflow_id": caller_workflow_id,
            "input_params": input_params or {},
            "call_id": call_id or f"call_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Also add input params directly to payload for easy variable access
        if input_params:
            payload.update(input_params)

        metadata = {
            "source": "workflow_call",
            "call_alias": config.get("call_alias", ""),
            "synchronous": config.get("synchronous", True),
        }

        return await self.emit(payload, metadata)

    def validate_config(self) -> tuple[bool, Optional[str]]:
        """Validate workflow call trigger configuration."""
        config = self.config.config

        call_alias = config.get("call_alias", "")
        if not call_alias:
            return False, "call_alias is required"

        # Validate alias format (alphanumeric and underscores only)
        import re

        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", call_alias):
            return (
                False,
                "call_alias must be alphanumeric (start with letter or underscore)",
            )

        return True, None

    @classmethod
    def get_config_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for workflow call configuration."""
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
                "call_alias": {
                    "type": "string",
                    "pattern": "^[a-zA-Z_][a-zA-Z0-9_]*$",
                    "description": "Unique alias for calling this workflow",
                },
                "synchronous": {
                    "type": "boolean",
                    "default": True,
                    "description": "Wait for completion before returning",
                },
                "input_schema": {
                    "type": "object",
                    "description": "Schema for expected input parameters",
                    "properties": {
                        "required": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Required parameter names",
                        },
                        "properties": {
                            "type": "object",
                            "description": "Parameter type definitions",
                        },
                    },
                },
                "output_mapping": {
                    "type": "object",
                    "additionalProperties": {"type": "string"},
                    "description": "Map output variables to return values",
                },
                "allowed_callers": {
                    "type": "array",
                    "items": {"type": "string"},
                    "default": [],
                    "description": "Scenario IDs that can call this (empty = all)",
                },
            },
            "required": ["name", "call_alias"],
        }
