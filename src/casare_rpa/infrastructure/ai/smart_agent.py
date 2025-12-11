"""
CasareRPA - Smart Workflow Agent

Integrates LLM generation with headless validation for reliable workflow generation.
Uses iterative refinement to produce valid workflows from natural language prompts.

Key Features:
    - Generation with retry loop and self-healing
    - Headless validation before returning results
    - Append mode for extending existing workflows
    - Comprehensive error tracking and repair prompts
    - Configurable performance optimization
    - Extensive logging and error handling

Architecture:
    - Uses LLMResourceManager for LLM calls
    - Uses validate_workflow for headless validation
    - WorkflowAISchema for parsing and validation
    - AgentConfig for customizable behavior
"""

from __future__ import annotations

import asyncio
import json
import re
import time
import traceback
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from loguru import logger

from casare_rpa.domain.schemas.workflow_ai import (
    WorkflowAISchema,
    NodeSchema,
    ConnectionSchema,
    PositionSchema,
)
from casare_rpa.domain.validation import (
    ValidationResult,
    validate_workflow,
)
from casare_rpa.domain.services.workflow_validator import (
    WorkflowValidator as QtWorkflowValidator,
    validate_workflow_with_qt,
)
from casare_rpa.infrastructure.ai.registry_dumper import (
    dump_node_manifest,
    manifest_to_compact_markdown,
)

if TYPE_CHECKING:
    from casare_rpa.infrastructure.resources.llm_resource_manager import (
        LLMResourceManager,
    )
    from casare_rpa.domain.ai.config import AgentConfig


# =============================================================================
# CUSTOM EXCEPTIONS
# =============================================================================


class WorkflowGenerationError(Exception):
    """Base exception for workflow generation errors."""

    def __init__(
        self,
        message: str,
        error_type: str = "GENERATION_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.error_type = error_type
        self.details = details or {}
        self.timestamp = time.time()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize exception to dictionary."""
        return {
            "error_type": self.error_type,
            "message": str(self),
            "details": self.details,
            "timestamp": self.timestamp,
        }


class LLMCallError(WorkflowGenerationError):
    """Error during LLM API call."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message, "LLM_CALL_ERROR", details)


class JSONParseError(WorkflowGenerationError):
    """Error parsing JSON from LLM response."""

    def __init__(self, message: str, response_preview: str = "") -> None:
        super().__init__(
            message,
            "JSON_PARSE_ERROR",
            {"response_preview": response_preview[:500]},
        )


class ValidationError(WorkflowGenerationError):
    """Error during workflow validation."""

    def __init__(self, message: str, validation_errors: List[str]) -> None:
        super().__init__(
            message,
            "VALIDATION_ERROR",
            {"validation_errors": validation_errors},
        )


class MaxRetriesExceededError(WorkflowGenerationError):
    """Maximum retry attempts exceeded."""

    def __init__(self, attempts: int, last_error: Optional[str] = None) -> None:
        super().__init__(
            f"Max retries ({attempts}) exceeded",
            "MAX_RETRIES_EXCEEDED",
            {"attempts": attempts, "last_error": last_error},
        )


# =============================================================================
# RESULT DATACLASSES
# =============================================================================


@dataclass
class GenerationAttempt:
    """Record of a single generation attempt."""

    attempt_number: int
    timestamp: float
    success: bool
    temperature: float
    duration_ms: float
    error: Optional[str] = None
    validation_result: Optional[ValidationResult] = None
    token_usage: Optional[Dict[str, int]] = None


@dataclass
class WorkflowGenerationResult:
    """
    Result of a workflow generation attempt.

    Attributes:
        success: Whether generation succeeded
        workflow: Generated workflow dict (if success)
        attempts: Number of generation attempts made
        error: Error message if failed
        validation_history: List of validation results from each attempt
        generation_time_ms: Total time taken for generation
        attempt_history: Detailed history of each attempt
    """

    success: bool
    workflow: Optional[Dict[str, Any]] = None
    attempts: int = 0
    error: Optional[str] = None
    validation_history: List[ValidationResult] = field(default_factory=list)
    generation_time_ms: float = 0.0
    attempt_history: List[GenerationAttempt] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "success": self.success,
            "workflow": self.workflow,
            "attempts": self.attempts,
            "error": self.error,
            "generation_time_ms": self.generation_time_ms,
            "validation_history": [v.to_dict() for v in self.validation_history],
            "attempt_history": [
                {
                    "attempt": a.attempt_number,
                    "success": a.success,
                    "duration_ms": a.duration_ms,
                    "error": a.error,
                }
                for a in self.attempt_history
            ],
        }


# =============================================================================
# HEADLESS WORKFLOW SANDBOX
# =============================================================================


class HeadlessWorkflowSandbox:
    """
    Headless validation sandbox for workflow JSON.

    Validates workflows without requiring the full UI or execution engine.
    Uses domain validation rules AND Qt-based validation to check:
    - Structure, node types, and connections (domain validation)
    - Actual port names against visual node definitions (Qt validation)
    """

    def __init__(self) -> None:
        """Initialize the headless sandbox."""
        self._node_types_cache: Optional[set] = None
        self._qt_validator: Optional[QtWorkflowValidator] = None
        logger.debug("HeadlessWorkflowSandbox initialized")

    def _get_valid_node_types(self) -> set:
        """Get set of valid node types from registry."""
        if self._node_types_cache is not None:
            return self._node_types_cache

        try:
            from casare_rpa.domain.validation.schemas import get_valid_node_types

            self._node_types_cache = get_valid_node_types()
            logger.debug(f"Loaded {len(self._node_types_cache)} valid node types")
        except ImportError as e:
            logger.warning(f"Could not load node types from registry: {e}")
            self._node_types_cache = set()
        except Exception as e:
            logger.error(f"Unexpected error loading node types: {e}")
            self._node_types_cache = set()

        return self._node_types_cache

    def _get_qt_validator(self) -> QtWorkflowValidator:
        """Get or create Qt workflow validator."""
        if self._qt_validator is None:
            self._qt_validator = QtWorkflowValidator()
            logger.debug("Qt WorkflowValidator initialized")
        return self._qt_validator

    def validate_workflow(self, workflow_dict: Dict[str, Any]) -> ValidationResult:
        """
        Validate a workflow dictionary in headless mode.

        This performs both domain validation AND Qt-based validation to ensure:
        1. Workflow structure is valid (domain validation)
        2. All port names match actual visual node definitions (Qt validation)

        Args:
            workflow_dict: Workflow data to validate

        Returns:
            ValidationResult with any issues found
        """
        result = ValidationResult()
        start_time = time.time()

        logger.debug(
            f"Starting headless validation for workflow with "
            f"{len(workflow_dict.get('nodes', {}))} nodes"
        )

        # Run domain validation
        try:
            domain_result = validate_workflow(workflow_dict)
            result.merge(domain_result)
            logger.debug(
                f"Domain validation: {len(domain_result.errors)} errors, "
                f"{len(domain_result.warnings)} warnings"
            )
        except Exception as e:
            logger.error(f"Domain validation threw exception: {e}")
            logger.debug(traceback.format_exc())
            result.add_error(
                "VALIDATION_EXCEPTION",
                f"Validation threw exception: {e}",
                suggestion="Check workflow structure and try again",
            )

        # Run Qt-based validation (validates port names against actual node definitions)
        try:
            qt_validator = self._get_qt_validator()
            qt_result = qt_validator.validate(workflow_dict)

            # Convert Qt validation errors to domain validation format
            for issue in qt_result.errors:
                result.add_error(
                    issue.code,
                    issue.message,
                    location=issue.location,
                    suggestion=issue.suggestion,
                )

            for issue in qt_result.warnings:
                result.add_warning(
                    issue.code,
                    issue.message,
                    location=issue.location,
                    suggestion=issue.suggestion,
                )

            logger.debug(
                f"Qt validation: {len(qt_result.errors)} errors, "
                f"{len(qt_result.warnings)} warnings"
            )
        except Exception as e:
            logger.error(f"Qt validation threw exception: {e}")
            logger.debug(traceback.format_exc())
            result.add_warning(
                "QT_VALIDATION_SKIPPED",
                f"Qt validation skipped due to error: {e}",
                suggestion="Workflow may have port name issues",
            )

        # Additional semantic checks
        try:
            self._validate_node_types(workflow_dict, result)
        except Exception as e:
            logger.error(f"Node type validation failed: {e}")
            result.add_error(
                "NODE_TYPE_VALIDATION_ERROR",
                f"Node type validation failed: {e}",
                suggestion="Ensure all node types are valid",
            )

        try:
            self._validate_connection_ports(workflow_dict, result)
        except Exception as e:
            logger.error(f"Connection port validation failed: {e}")
            result.add_error(
                "CONNECTION_VALIDATION_ERROR",
                f"Connection validation failed: {e}",
                suggestion="Check connection port names",
            )

        duration_ms = (time.time() - start_time) * 1000
        logger.debug(
            f"Headless validation completed in {duration_ms:.2f}ms: "
            f"valid={result.is_valid}, errors={len(result.errors)}"
        )

        return result

    def _validate_node_types(
        self, workflow_dict: Dict[str, Any], result: ValidationResult
    ) -> None:
        """Validate that all node types are registered."""
        valid_types = self._get_valid_node_types()
        if not valid_types:
            logger.warning("Skipping node type validation - no types loaded")
            return

        nodes = workflow_dict.get("nodes", {})
        for node_id, node_data in nodes.items():
            node_type = node_data.get("node_type", "")
            if node_type and node_type not in valid_types:
                logger.warning(f"Unknown node type '{node_type}' in node '{node_id}'")
                result.add_error(
                    "UNKNOWN_NODE_TYPE",
                    f"Node type '{node_type}' is not registered",
                    location=f"node:{node_id}",
                    suggestion="Use a valid node type from the manifest",
                )

    def _validate_connection_ports(
        self, workflow_dict: Dict[str, Any], result: ValidationResult
    ) -> None:
        """Validate connection port names are valid."""
        connections = workflow_dict.get("connections", [])

        for idx, conn in enumerate(connections):
            source_port = conn.get("source_port", "")
            target_port = conn.get("target_port", "")

            # Execution ports should follow naming convention
            if source_port and not self._is_valid_port_name(source_port):
                result.add_warning(
                    "INVALID_PORT_NAME",
                    f"Source port '{source_port}' may be invalid",
                    location=f"connection:{idx}",
                )

            if target_port and not self._is_valid_port_name(target_port):
                result.add_warning(
                    "INVALID_PORT_NAME",
                    f"Target port '{target_port}' may be invalid",
                    location=f"connection:{idx}",
                )

    def _is_valid_port_name(self, port_name: str) -> bool:
        """Check if port name follows valid patterns."""
        if not port_name:
            return False
        # Port names should be snake_case
        return bool(re.match(r"^[a-z][a-z0-9_]*$", port_name))


# =============================================================================
# SYSTEM PROMPTS
# =============================================================================


_GENERATION_SYSTEM_PROMPT = """You are CasareRPA Workflow Architect.

Your task: Generate valid CasareRPA workflow JSON from natural language descriptions.

## CRITICAL RULES
1. Output ONLY valid JSON - no markdown, no explanation, no code blocks
2. Use EXACT node types from the manifest below
3. DO NOT include StartNode or EndNode - they already exist on the canvas
4. Generate ONLY action nodes (the actual work to be done)
5. Node IDs must be snake_case (e.g., "click_login_button")
6. Connect nodes with exec_out -> exec_in for execution flow
7. Use meaningful node IDs that describe the action
8. Position nodes with x starting at 0, incrementing by 400 for each node

## JSON Schema
{{
  "metadata": {{
    "name": "string (required)",
    "description": "string",
    "version": "1.0.0"
  }},
  "nodes": {{
    "<node_id>": {{
      "node_id": "<same as key>",
      "node_type": "<NodeTypeName>",
      "config": {{<node-specific config>}},
      "position": [x, y]
    }}
  }},
  "connections": [
    {{
      "source_node": "<node_id>",
      "source_port": "exec_out",
      "target_node": "<node_id>",
      "target_port": "exec_in"
    }}
  ],
  "variables": {{}},
  "settings": {{
    "stop_on_error": true,
    "timeout": 30,
    "retry_count": 0
  }}
}}

## Available Node Types
{node_manifest}

## Common Node Configs
- GoToURLNode: {{"url": "https://..."}}
- ClickElementNode: {{"selector": "css selector or xpath"}}
- TypeTextNode: {{"selector": "...", "text": "...", "clear_first": true}}
- WaitForElementNode: {{"selector": "...", "timeout": 5000, "state": "visible"}}
- WaitNode: {{"duration_ms": 1000}}
- SetVariableNode: {{"variable_name": "...", "value": "..."}}
- IfNode: {{"condition": "expression"}}
- ForLoopStartNode: {{"items": "{{{{variable}}}}", "index_var": "i"}}
- LaunchApplicationNode: {{"application_path": "notepad.exe", "arguments": ""}}

Output ONLY the JSON object with action nodes. NO StartNode or EndNode."""


_REPAIR_PROMPT_TEMPLATE = """The workflow you generated has validation errors:

{errors}

Original workflow (with issues):
```json
{workflow_json}
```

Please fix these errors and output a corrected workflow JSON.
Remember:
- Use only valid node types from the manifest
- Ensure all node_id fields match their dictionary keys
- Connect nodes properly with exec_out -> exec_in
- DO NOT include StartNode or EndNode

Output ONLY the corrected JSON object, nothing else."""


_EDIT_SYSTEM_PROMPT = """You are CasareRPA Workflow Architect in EDIT mode.

The user wants to MODIFY existing nodes on the canvas, NOT create new ones.

## Current Canvas State
{canvas_state}

## Your Task
Analyze the user's request and determine which existing nodes need to be modified.
Output a JSON object with ONLY the modifications needed.

## Output Format
{{
  "action": "edit",
  "modifications": [
    {{
      "node_id": "<existing node_id to modify>",
      "changes": {{
        "<property_name>": "<new_value>"
      }}
    }}
  ]
}}

## Rules
1. Only modify nodes that exist in the current canvas state
2. Only change the specific properties mentioned in the request
3. Do not create new nodes - this is EDIT mode
4. Output ONLY valid JSON

{base_instructions}"""


_APPEND_SYSTEM_PROMPT = """You are CasareRPA Workflow Architect in APPEND mode.

The user wants to add NEW nodes to the existing workflow.

## Current Canvas State
{canvas_state}

## Instructions
1. Generate ONLY new action nodes (NO StartNode or EndNode)
2. Position new nodes after the last existing node
3. Use node IDs that don't conflict with existing ones
4. The first new node will be connected to the workflow automatically

{base_instructions}"""


# =============================================================================
# SMART WORKFLOW AGENT
# =============================================================================


class SmartWorkflowAgent:
    """
    Smart workflow generation agent with LLM integration and validation.

    Generates workflows from natural language using LLM, then validates
    using headless sandbox. Uses iterative refinement to fix errors.

    Features:
        - Configurable via AgentConfig
        - Comprehensive error handling and logging
        - Performance-optimized prompt generation
        - Retry logic with exponential backoff

    Attributes:
        config: Agent configuration settings
        llm_client: LLM resource manager for API calls
        validator: Headless workflow sandbox for validation
    """

    DEFAULT_MODEL = "gpt-4o-mini"
    DEFAULT_TEMPERATURE = 0.2
    DEFAULT_MAX_TOKENS = 4000
    DEFAULT_MAX_RETRIES = 3

    def __init__(
        self,
        llm_client: Optional[LLMResourceManager] = None,
        max_retries: Optional[int] = None,
        config: Optional[AgentConfig] = None,
    ) -> None:
        """
        Initialize the smart workflow agent.

        Args:
            llm_client: LLM resource manager (creates one if None)
            max_retries: Maximum attempts to generate valid workflow (deprecated, use config)
            config: Agent configuration (optional, uses defaults if None)
        """
        self._llm_client = llm_client
        self._config = config
        self.max_retries = (
            max_retries
            if max_retries is not None
            else (
                config.retry.max_generation_retries
                if config
                else self.DEFAULT_MAX_RETRIES
            )
        )
        self.validator = HeadlessWorkflowSandbox()
        self._system_prompt_cache: Optional[str] = None
        self._manifest_cache: Optional[str] = None

        logger.info(
            f"SmartWorkflowAgent initialized: max_retries={self.max_retries}, "
            f"config={'custom' if config else 'default'}"
        )

    @property
    def config(self) -> Optional[AgentConfig]:
        """Get current configuration."""
        return self._config

    def _get_llm_client(self) -> LLMResourceManager:
        """Get or create LLM resource manager."""
        if self._llm_client is None:
            try:
                from casare_rpa.infrastructure.resources.llm_resource_manager import (
                    LLMResourceManager,
                )

                self._llm_client = LLMResourceManager()
                logger.debug("Created new LLMResourceManager instance")
            except ImportError as e:
                logger.error(f"Failed to import LLMResourceManager: {e}")
                raise LLMCallError(
                    "LLMResourceManager not available",
                    {"import_error": str(e)},
                )
            except Exception as e:
                logger.error(f"Failed to create LLMResourceManager: {e}")
                raise LLMCallError(
                    f"Failed to initialize LLM client: {e}",
                    {"error": str(e)},
                )
        return self._llm_client

    def _get_node_manifest(self) -> str:
        """Get node manifest (cached)."""
        if self._manifest_cache is not None:
            return self._manifest_cache

        try:
            logger.debug("Generating node manifest...")
            manifest = dump_node_manifest()
            self._manifest_cache = manifest_to_compact_markdown(manifest)
            logger.debug(f"Node manifest generated: {len(self._manifest_cache)} chars")
        except Exception as e:
            logger.warning(f"Failed to generate node manifest: {e}")
            logger.debug(traceback.format_exc())
            self._manifest_cache = self._get_fallback_manifest()

        return self._manifest_cache

    def _build_system_prompt(self) -> str:
        """Build system prompt with node manifest and config options."""
        if self._system_prompt_cache is not None:
            return self._system_prompt_cache

        node_manifest = self._get_node_manifest()
        base_prompt = _GENERATION_SYSTEM_PROMPT.format(node_manifest=node_manifest)

        # Add config-based customizations
        additional_sections = []

        if self._config:
            # Add performance optimization rules
            perf_prompt = self._config.build_performance_prompt()
            if perf_prompt:
                additional_sections.append(perf_prompt)

            # Add custom rules
            rules_prompt = self._config.build_rules_prompt()
            if rules_prompt:
                additional_sections.append(rules_prompt)

            # Add error handling instructions
            error_prompt = self._config.build_error_handling_prompt()
            if error_prompt:
                additional_sections.append(error_prompt)

            # Add additional context
            if self._config.additional_context:
                additional_sections.append(
                    f"## Additional Context\n{self._config.additional_context}"
                )

        if additional_sections:
            base_prompt = base_prompt + "\n\n" + "\n\n".join(additional_sections)

        self._system_prompt_cache = base_prompt
        logger.debug(f"System prompt built: {len(self._system_prompt_cache)} chars")
        return self._system_prompt_cache

    def _get_fallback_manifest(self) -> str:
        """Get fallback manifest if registry dump fails."""
        logger.warning("Using fallback node manifest")
        return """## browser
- StartNode(-)->exec_out
- EndNode(exec_in)->-
- GoToURLNode(url)->exec_out,page
- ClickElementNode(selector,page)->exec_out
- TypeTextNode(selector,text,page)->exec_out
- WaitForElementNode(selector,page)->exec_out,element,found

## control_flow
- IfNode(exec_in,condition)->true,false (NOT true_out/false_out!)
- TryNode(exec_in)->exec_out,try_body (NOT try_out!)
- CatchNode(exec_in)->catch_body,error_message,error_type,stack_trace
- FinallyNode(exec_in)->finally_body,had_error
- ForLoopStartNode(exec_in,items)->body,completed,current_item,current_index
- ForLoopEndNode(exec_in)->exec_out
- WhileLoopStartNode(exec_in,condition)->body,completed,current_iteration
- WhileLoopEndNode(exec_in)->exec_out
- WaitNode(duration_ms)->exec_out
- MergeNode(exec_in)->exec_out
- ForkNode(exec_in)->branch_1,branch_2
- JoinNode(exec_in)->exec_out,results

## data
- SetVariableNode(variable_name,value)->exec_out
- GetVariableNode(variable_name)->exec_out,value"""

    def _extract_json_from_response(self, response: str) -> str:
        """
        Extract JSON from LLM response.

        Args:
            response: Raw LLM response text

        Returns:
            Cleaned JSON string

        Raises:
            JSONParseError: If no valid JSON found
        """
        content = response.strip()
        logger.debug(f"Extracting JSON from response ({len(content)} chars)")

        # Try to extract from markdown code block
        try:
            json_block_match = re.search(
                r"```(?:json)?\s*\n?(.*?)\n?```",
                content,
                re.DOTALL | re.IGNORECASE,
            )
            if json_block_match:
                content = json_block_match.group(1).strip()
                logger.debug("Extracted JSON from markdown code block")
        except Exception as e:
            logger.debug(f"Markdown extraction failed: {e}")

        # Find JSON object boundaries
        start_idx = content.find("{")
        if start_idx == -1:
            logger.error("No JSON object found in response")
            raise JSONParseError("No JSON object found in response", content)

        # Find matching closing brace
        depth = 0
        end_idx = -1
        for i, char in enumerate(content[start_idx:], start=start_idx):
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    end_idx = i + 1
                    break

        if end_idx == -1:
            logger.error("Malformed JSON - unmatched braces")
            raise JSONParseError("Malformed JSON - unmatched braces", content)

        json_str = content[start_idx:end_idx]
        logger.debug(f"Extracted JSON: {len(json_str)} chars")
        return json_str

    def _parse_workflow_json(self, json_str: str) -> Dict[str, Any]:
        """
        Parse JSON string and validate against schema.

        Args:
            json_str: JSON string to parse

        Returns:
            Validated workflow dictionary

        Raises:
            JSONParseError: If parsing fails
            ValidationError: If schema validation fails
        """
        logger.debug("Parsing workflow JSON...")

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            raise JSONParseError(f"Invalid JSON: {e}", json_str) from e

        try:
            validated = WorkflowAISchema.model_validate(data)
            result = validated.to_dict()
            logger.debug(
                f"Workflow parsed: {len(result.get('nodes', {}))} nodes, "
                f"{len(result.get('connections', []))} connections"
            )
            return result
        except Exception as e:
            logger.error(f"Schema validation failed: {e}")
            raise ValidationError(
                f"Schema validation failed: {e}",
                [str(e)],
            ) from e

    def _build_repair_prompt(self, workflow_json: str, errors: List[str]) -> str:
        """
        Build repair prompt from validation errors.

        Args:
            workflow_json: Original workflow JSON that had errors
            errors: List of error messages

        Returns:
            Repair prompt for LLM
        """
        errors_text = "\n".join(f"- {err}" for err in errors)
        logger.debug(f"Building repair prompt for {len(errors)} errors")
        return _REPAIR_PROMPT_TEMPLATE.format(
            errors=errors_text,
            workflow_json=workflow_json,
        )

    def _ensure_start_and_end_nodes(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensure workflow has StartNode and EndNode.

        Args:
            workflow: Workflow dictionary

        Returns:
            Workflow with StartNode and EndNode added if missing
        """
        nodes = workflow.get("nodes", {})
        connections = workflow.get("connections", [])

        # Check for StartNode
        has_start = any(n.get("node_type") == "StartNode" for n in nodes.values())

        # Check for EndNode
        has_end = any(n.get("node_type") == "EndNode" for n in nodes.values())

        if has_start and has_end:
            logger.debug("Workflow already has Start and End nodes")
            return workflow

        # Find min/max x positions for placement
        x_positions = []
        for node_data in nodes.values():
            pos = node_data.get("position")
            if pos:
                if isinstance(pos, list) and len(pos) >= 1:
                    x_positions.append(pos[0])
                elif isinstance(pos, dict) and "x" in pos:
                    x_positions.append(pos["x"])

        min_x = min(x_positions) if x_positions else 0
        max_x = max(x_positions) if x_positions else 0

        new_nodes = dict(nodes)
        new_connections = list(connections)

        # Add StartNode if missing
        if not has_start:
            logger.info("Adding missing StartNode")
            start_x = min_x - 400
            new_nodes["start_node"] = {
                "node_id": "start_node",
                "node_type": "StartNode",
                "config": {},
                "position": [start_x, 0],
            }

            # Connect to first non-start node
            first_node_id = None
            for node_id, node_data in nodes.items():
                if node_data.get("node_type") != "StartNode":
                    first_node_id = node_id
                    break

            if first_node_id:
                new_connections.insert(
                    0,
                    {
                        "source_node": "start_node",
                        "source_port": "exec_out",
                        "target_node": first_node_id,
                        "target_port": "exec_in",
                    },
                )

        # Add EndNode if missing
        if not has_end:
            logger.info("Adding missing EndNode")
            end_x = max_x + 400
            new_nodes["end_node"] = {
                "node_id": "end_node",
                "node_type": "EndNode",
                "config": {},
                "position": [end_x, 0],
            }

            # Find terminal nodes (nodes with no outgoing exec connections)
            source_nodes = {c.get("source_node") for c in new_connections}
            terminal_nodes = []
            for node_id, node_data in nodes.items():
                if node_data.get("node_type") == "EndNode":
                    continue
                if node_id not in source_nodes:
                    terminal_nodes.append(node_id)

            # If no terminal nodes, use last node
            if not terminal_nodes and nodes:
                terminal_nodes = [list(nodes.keys())[-1]]

            for terminal_id in terminal_nodes:
                new_connections.append(
                    {
                        "source_node": terminal_id,
                        "source_port": "exec_out",
                        "target_node": "end_node",
                        "target_port": "exec_in",
                    }
                )

        return {
            **workflow,
            "nodes": new_nodes,
            "connections": new_connections,
        }

    def _assign_node_positions(
        self, workflow: Dict[str, Any], spacing_x: float = 400.0
    ) -> Dict[str, Any]:
        """
        Assign positions to nodes that don't have them.

        Args:
            workflow: Workflow dictionary
            spacing_x: Horizontal spacing between nodes

        Returns:
            Workflow with positions assigned
        """
        nodes = workflow.get("nodes", {})
        new_nodes = {}

        x_pos = 0.0
        y_pos = 0.0

        for node_id, node_data in nodes.items():
            pos = node_data.get("position")
            if pos is None:
                node_data = dict(node_data)
                node_data["position"] = [x_pos, y_pos]
                x_pos += spacing_x

            new_nodes[node_id] = node_data

        logger.debug(f"Assigned positions to {len(new_nodes)} nodes")
        return {**workflow, "nodes": new_nodes}

    def _strip_start_end_nodes(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """
        Remove StartNode and EndNode from workflow.

        These nodes already exist on the canvas, so we shouldn't create duplicates.

        Args:
            workflow: Workflow dictionary

        Returns:
            Workflow with Start/End nodes removed
        """
        nodes = workflow.get("nodes", {})
        connections = workflow.get("connections", [])

        # Filter out Start and End nodes
        new_nodes = {}
        removed_node_ids = set()

        for node_id, node_data in nodes.items():
            node_type = node_data.get("node_type", "")
            if node_type in ("StartNode", "EndNode"):
                removed_node_ids.add(node_id)
                logger.debug(f"Stripped {node_type} from AI-generated workflow")
            else:
                new_nodes[node_id] = node_data

        # Filter out connections involving removed nodes
        new_connections = [
            conn
            for conn in connections
            if conn.get("source_node") not in removed_node_ids
            and conn.get("target_node") not in removed_node_ids
        ]

        if removed_node_ids:
            logger.info(
                f"Removed {len(removed_node_ids)} Start/End nodes, "
                f"{len(connections) - len(new_connections)} connections"
            )

        return {
            **workflow,
            "nodes": new_nodes,
            "connections": new_connections,
        }

    def _calculate_append_position(
        self, existing_workflow: Dict[str, Any]
    ) -> tuple[str, float]:
        """
        Calculate append position for extending workflow.

        Args:
            existing_workflow: Existing workflow dictionary

        Returns:
            Tuple of (last_node_id, next_x_position)
        """
        nodes = existing_workflow.get("nodes", {})

        if not nodes:
            return ("", 0.0)

        # Find node with highest x position (excluding EndNode)
        max_x = 0.0
        last_node_id = ""

        for node_id, node_data in nodes.items():
            if node_data.get("node_type") == "EndNode":
                continue

            pos = node_data.get("position")
            if pos:
                x = pos[0] if isinstance(pos, list) else pos.get("x", 0)
                if x >= max_x:
                    max_x = x
                    last_node_id = node_id

        # If no position data, use last node
        if not last_node_id and nodes:
            node_ids = list(nodes.keys())
            for nid in reversed(node_ids):
                if nodes[nid].get("node_type") != "EndNode":
                    last_node_id = nid
                    break

        logger.debug(f"Append position: last_node={last_node_id}, x={max_x + 400}")
        return (last_node_id, max_x + 400.0)

    async def _call_llm_with_retry(
        self,
        prompt: str,
        system_prompt: str,
        model: str,
        temperature: float,
        attempt: int,
    ) -> str:
        """
        Call LLM with error handling and logging.

        Args:
            prompt: User prompt
            system_prompt: System prompt
            model: Model name
            temperature: Sampling temperature
            attempt: Current attempt number

        Returns:
            LLM response content

        Raises:
            LLMCallError: If LLM call fails
        """
        logger.info(
            f"LLM call attempt {attempt + 1}: model={model}, temp={temperature:.2f}"
        )
        start_time = time.time()

        try:
            llm = self._get_llm_client()
            response = await llm.completion(
                prompt=prompt,
                model=model,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=self._config.max_tokens
                if self._config
                else self.DEFAULT_MAX_TOKENS,
            )

            duration_ms = (time.time() - start_time) * 1000
            logger.debug(
                f"LLM response received in {duration_ms:.2f}ms: "
                f"{response.total_tokens} tokens"
            )
            return response.content

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"LLM call failed after {duration_ms:.2f}ms: {e}")
            logger.debug(traceback.format_exc())
            raise LLMCallError(
                f"LLM call failed: {e}",
                {"duration_ms": duration_ms, "attempt": attempt},
            ) from e

    async def generate_workflow(
        self,
        user_prompt: str,
        existing_workflow: Optional[Dict[str, Any]] = None,
        canvas_state: Optional[Dict[str, Any]] = None,
        is_edit: bool = False,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> WorkflowGenerationResult:
        """
        Generate a workflow from natural language prompt.

        Uses iterative refinement with LLM to produce a valid workflow.
        If validation fails, builds repair prompts and retries.

        Args:
            user_prompt: Natural language description of desired workflow
            existing_workflow: Optional workflow to extend (append mode)
            canvas_state: Optional current canvas state for edit mode
            is_edit: If True, generate edits instead of new nodes
            model: LLM model to use (defaults to config or gpt-4o-mini)
            temperature: Sampling temperature

        Returns:
            WorkflowGenerationResult with success/failure and workflow
        """
        generation_start = time.time()
        attempt_history: List[GenerationAttempt] = []
        validation_history: List[ValidationResult] = []

        # Validate input
        if not user_prompt or not user_prompt.strip():
            logger.warning("Empty user prompt provided")
            return WorkflowGenerationResult(
                success=False,
                error="User prompt cannot be empty",
            )

        # Determine parameters from config or defaults
        model_name = model or (
            self._config.model if self._config else self.DEFAULT_MODEL
        )
        base_temp = (
            temperature
            if temperature is not None
            else (
                self._config.temperature if self._config else self.DEFAULT_TEMPERATURE
            )
        )

        logger.info(
            f"Starting workflow generation: prompt='{user_prompt[:100]}...', "
            f"model={model_name}, mode={'edit' if is_edit else 'append' if existing_workflow else 'generate'}"
        )

        # Build appropriate system prompt based on mode
        try:
            if is_edit and canvas_state:
                logger.debug("Using EDIT mode")
                system_prompt = _EDIT_SYSTEM_PROMPT.format(
                    canvas_state=json.dumps(canvas_state, indent=2)[:3000],
                    base_instructions=self._build_system_prompt(),
                )
            elif existing_workflow:
                logger.debug("Using APPEND mode")
                system_prompt = _APPEND_SYSTEM_PROMPT.format(
                    canvas_state=json.dumps(canvas_state, indent=2)[:2000]
                    if canvas_state
                    else "{}",
                    base_instructions=self._build_system_prompt(),
                )
            else:
                logger.debug("Using GENERATE mode")
                system_prompt = self._build_system_prompt()
        except Exception as e:
            logger.error(f"Failed to build system prompt: {e}")
            return WorkflowGenerationResult(
                success=False,
                error=f"Failed to build system prompt: {e}",
            )

        current_prompt = user_prompt
        last_json_str = ""

        # Retry loop
        for attempt in range(self.max_retries):
            attempt_start = time.time()
            temp = (
                self._config.get_effective_temperature(attempt)
                if self._config
                else (base_temp + (attempt * 0.1))
            )

            # Invoke config callbacks
            if self._config and self._config.on_generation_attempt:
                try:
                    self._config.on_generation_attempt(attempt, current_prompt)
                except Exception as e:
                    logger.warning(f"Generation attempt callback failed: {e}")

            attempt_record = GenerationAttempt(
                attempt_number=attempt + 1,
                timestamp=attempt_start,
                success=False,
                temperature=temp,
                duration_ms=0,
            )

            try:
                # Call LLM
                response_content = await self._call_llm_with_retry(
                    prompt=current_prompt,
                    system_prompt=system_prompt,
                    model=model_name,
                    temperature=temp,
                    attempt=attempt,
                )

                # Extract and parse JSON
                json_str = self._extract_json_from_response(response_content)
                last_json_str = json_str
                workflow = self._parse_workflow_json(json_str)

                # Post-process workflow
                if self._config is None or self._config.strip_start_end_nodes:
                    workflow = self._strip_start_end_nodes(workflow)
                workflow = self._assign_node_positions(workflow)

                # Merge with existing workflow if in append mode
                if existing_workflow:
                    workflow = self._merge_workflows(existing_workflow, workflow)

                # Validate
                if self._config is None or self._config.validate_before_return:
                    result = self.validator.validate_workflow(workflow)
                    validation_history.append(result)

                    if not result.is_valid:
                        errors = [
                            f"{issue.code}: {issue.message}" for issue in result.errors
                        ]

                        # Invoke validation error callback
                        if self._config and self._config.on_validation_error:
                            try:
                                self._config.on_validation_error(json_str, errors)
                            except Exception as e:
                                logger.warning(f"Validation error callback failed: {e}")

                        # Build repair prompt
                        current_prompt = self._build_repair_prompt(json_str, errors)

                        attempt_record.error = f"{len(errors)} validation errors"
                        attempt_record.validation_result = result
                        attempt_record.duration_ms = (
                            time.time() - attempt_start
                        ) * 1000
                        attempt_history.append(attempt_record)

                        logger.warning(
                            f"Validation failed on attempt {attempt + 1}: {len(errors)} errors"
                        )

                        # Add delay before retry
                        if self._config and attempt < self.max_retries - 1:
                            delay = self._config.get_retry_delay(attempt)
                            logger.debug(f"Waiting {delay:.2f}s before retry")
                            await asyncio.sleep(delay)

                        continue

                # Success!
                attempt_record.success = True
                attempt_record.duration_ms = (time.time() - attempt_start) * 1000
                attempt_history.append(attempt_record)

                total_time = (time.time() - generation_start) * 1000
                logger.info(
                    f"Workflow generated successfully on attempt {attempt + 1} "
                    f"in {total_time:.2f}ms"
                )

                # Invoke success callback
                if self._config and self._config.on_success:
                    try:
                        self._config.on_success(workflow, attempt + 1)
                    except Exception as e:
                        logger.warning(f"Success callback failed: {e}")

                return WorkflowGenerationResult(
                    success=True,
                    workflow=workflow,
                    attempts=attempt + 1,
                    validation_history=validation_history,
                    generation_time_ms=total_time,
                    attempt_history=attempt_history,
                )

            except JSONParseError as e:
                logger.warning(f"JSON parse error on attempt {attempt + 1}: {e}")
                current_prompt = (
                    f"JSON parse error: {e}. "
                    f"Fix the syntax and output valid JSON only."
                )
                attempt_record.error = str(e)
                attempt_record.duration_ms = (time.time() - attempt_start) * 1000
                attempt_history.append(attempt_record)
                validation_history.append(ValidationResult())

            except ValidationError as e:
                logger.warning(f"Validation error on attempt {attempt + 1}: {e}")
                if last_json_str:
                    current_prompt = self._build_repair_prompt(
                        last_json_str, e.details.get("validation_errors", [str(e)])
                    )
                else:
                    current_prompt = (
                        f"Error: {e}. Please generate a valid workflow JSON."
                    )
                attempt_record.error = str(e)
                attempt_record.duration_ms = (time.time() - attempt_start) * 1000
                attempt_history.append(attempt_record)
                validation_history.append(ValidationResult())

            except LLMCallError as e:
                logger.error(f"LLM call failed on attempt {attempt + 1}: {e}")
                attempt_record.error = str(e)
                attempt_record.duration_ms = (time.time() - attempt_start) * 1000
                attempt_history.append(attempt_record)
                validation_history.append(ValidationResult())

                if attempt >= self.max_retries - 1:
                    total_time = (time.time() - generation_start) * 1000
                    return WorkflowGenerationResult(
                        success=False,
                        error=f"LLM call failed: {e}",
                        attempts=attempt + 1,
                        validation_history=validation_history,
                        generation_time_ms=total_time,
                        attempt_history=attempt_history,
                    )

                # Add delay before retry
                if self._config:
                    delay = self._config.get_retry_delay(attempt)
                    await asyncio.sleep(delay)

            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
                logger.debug(traceback.format_exc())
                attempt_record.error = str(e)
                attempt_record.duration_ms = (time.time() - attempt_start) * 1000
                attempt_history.append(attempt_record)
                validation_history.append(ValidationResult())

                if attempt >= self.max_retries - 1:
                    total_time = (time.time() - generation_start) * 1000
                    return WorkflowGenerationResult(
                        success=False,
                        error=f"Unexpected error: {e}",
                        attempts=attempt + 1,
                        validation_history=validation_history,
                        generation_time_ms=total_time,
                        attempt_history=attempt_history,
                    )

        # All retries exhausted
        total_time = (time.time() - generation_start) * 1000
        logger.error(
            f"Max retries ({self.max_retries}) exceeded after {total_time:.2f}ms"
        )

        return WorkflowGenerationResult(
            success=False,
            error=f"Max retries ({self.max_retries}) exceeded",
            attempts=self.max_retries,
            validation_history=validation_history,
            generation_time_ms=total_time,
            attempt_history=attempt_history,
        )

    def _merge_workflows(
        self,
        existing: Dict[str, Any],
        new: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Merge new workflow nodes into existing workflow.

        Args:
            existing: Existing workflow to extend
            new: New workflow with nodes to add

        Returns:
            Merged workflow
        """
        logger.debug("Merging workflows...")
        merged_nodes = dict(existing.get("nodes", {}))
        merged_connections = list(existing.get("connections", []))

        # Add new nodes (skip duplicates by ID)
        new_nodes_added = 0
        for node_id, node_data in new.get("nodes", {}).items():
            if node_id not in merged_nodes:
                merged_nodes[node_id] = node_data
                new_nodes_added += 1

        # Add new connections (skip duplicates)
        existing_conn_set = {
            (c["source_node"], c["source_port"], c["target_node"], c["target_port"])
            for c in merged_connections
        }

        new_connections_added = 0
        for conn in new.get("connections", []):
            conn_tuple = (
                conn["source_node"],
                conn["source_port"],
                conn["target_node"],
                conn["target_port"],
            )
            if conn_tuple not in existing_conn_set:
                merged_connections.append(conn)
                existing_conn_set.add(conn_tuple)
                new_connections_added += 1

        logger.debug(
            f"Merged: +{new_nodes_added} nodes, +{new_connections_added} connections"
        )

        return {
            "metadata": existing.get("metadata", new.get("metadata", {})),
            "nodes": merged_nodes,
            "connections": merged_connections,
            "variables": {
                **existing.get("variables", {}),
                **new.get("variables", {}),
            },
            "settings": existing.get("settings", new.get("settings", {})),
        }

    def clear_caches(self) -> None:
        """Clear all cached data."""
        self._system_prompt_cache = None
        self._manifest_cache = None
        logger.debug("Agent caches cleared")


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================


async def generate_smart_workflow(
    prompt: str,
    existing_workflow: Optional[Dict[str, Any]] = None,
    max_retries: int = 3,
    model: str = "gpt-4o-mini",
    config: Optional[AgentConfig] = None,
) -> WorkflowGenerationResult:
    """
    Convenience function for generating workflows with smart agent.

    Args:
        prompt: Natural language workflow description
        existing_workflow: Optional workflow to extend
        max_retries: Maximum generation attempts
        model: LLM model to use
        config: Optional agent configuration

    Returns:
        WorkflowGenerationResult
    """
    logger.info(f"generate_smart_workflow called: prompt='{prompt[:50]}...'")

    try:
        agent = SmartWorkflowAgent(max_retries=max_retries, config=config)
        return await agent.generate_workflow(
            user_prompt=prompt,
            existing_workflow=existing_workflow,
            model=model,
        )
    except Exception as e:
        logger.error(f"generate_smart_workflow failed: {e}")
        logger.debug(traceback.format_exc())
        return WorkflowGenerationResult(
            success=False,
            error=f"Generation failed: {e}",
        )


__all__ = [
    "SmartWorkflowAgent",
    "WorkflowGenerationResult",
    "GenerationAttempt",
    "HeadlessWorkflowSandbox",
    "generate_smart_workflow",
    "WorkflowGenerationError",
    "LLMCallError",
    "JSONParseError",
    "ValidationError",
    "MaxRetriesExceededError",
]
