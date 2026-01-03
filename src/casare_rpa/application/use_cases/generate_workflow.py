"""
CasareRPA - Application Use Case: Generate Workflow from Natural Language

Generates CasareRPA workflows from natural language descriptions using LLM.
Uses the node registry manifest to inform the LLM about available nodes,
and validates output against WorkflowAISchema.

Features:
    - Configurable agent settings via AgentConfig
    - Comprehensive error handling with try-except-catch
    - Extensive logging for debugging
    - Performance-optimized prompt generation
    - No hardcoded wait times (uses smart detection)
    - Retry logic with exponential backoff
"""

from __future__ import annotations

import json
import re
import time
import traceback
from typing import TYPE_CHECKING, Any, cast

from loguru import logger

from casare_rpa.domain.interfaces import ILLMManager, INodeManifestProvider
from casare_rpa.domain.schemas.workflow_ai import (
    ConnectionSchema,
    NodeSchema,
    PositionSchema,
    WorkflowAISchema,
)

if TYPE_CHECKING:
    from casare_rpa.domain.ai.config import AgentConfig


def _resolve_llm_manager(llm_manager: ILLMManager | None) -> ILLMManager:
    if llm_manager is not None:
        return llm_manager

    from casare_rpa.application.dependency_injection.container import DIContainer

    try:
        return cast(ILLMManager, DIContainer.get_instance().resolve("llm_manager"))
    except KeyError:
        from casare_rpa.application.dependency_injection import bootstrap_di

        bootstrap_di(include_presentation=False)
        return cast(ILLMManager, DIContainer.get_instance().resolve("llm_manager"))


def _resolve_node_manifest_provider(
    provider: INodeManifestProvider | None,
) -> INodeManifestProvider:
    if provider is not None:
        return provider

    from casare_rpa.application.dependency_injection.container import DIContainer

    try:
        return cast(
            INodeManifestProvider,
            DIContainer.get_instance().resolve("node_manifest_provider"),
        )
    except KeyError:
        from casare_rpa.application.dependency_injection import bootstrap_di

        bootstrap_di(include_presentation=False)
        return cast(
            INodeManifestProvider,
            DIContainer.get_instance().resolve("node_manifest_provider"),
        )


# =============================================================================
# EXCEPTIONS
# =============================================================================


class WorkflowGenerationError(Exception):
    """Raised when workflow generation fails."""

    def __init__(
        self,
        message: str,
        error_type: str = "GENERATION_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.error_type = error_type
        self.details = details or {}
        self.timestamp = time.time()

    def to_dict(self) -> dict[str, Any]:
        """Serialize exception to dictionary."""
        return {
            "error_type": self.error_type,
            "message": str(self),
            "details": self.details,
            "timestamp": self.timestamp,
        }


class LLMCallError(WorkflowGenerationError):
    """Error during LLM API call."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, "LLM_CALL_ERROR", details)


class JSONParseError(WorkflowGenerationError):
    """Error parsing JSON from LLM response."""

    def __init__(self, message: str, response_preview: str = "") -> None:
        super().__init__(
            message,
            "JSON_PARSE_ERROR",
            {"response_preview": response_preview[:500]},
        )


class SchemaValidationError(WorkflowGenerationError):
    """Error during schema validation."""

    def __init__(self, message: str, validation_errors: list[str]) -> None:
        super().__init__(
            message,
            "SCHEMA_VALIDATION_ERROR",
            {"validation_errors": validation_errors},
        )


# =============================================================================
# SYSTEM PROMPT
# =============================================================================


# System prompt template for workflow generation
_SYSTEM_PROMPT_TEMPLATE = """You are CasareRPA JSON Workflow Architect.

Your task: Generate valid CasareRPA workflow JSON from natural language descriptions.

## CRITICAL RULES
1. Output ONLY valid JSON - no markdown, no explanation, no code blocks
2. Use EXACT node types from the manifest below
3. DO NOT include StartNode or EndNode - they are added automatically by the system
4. Node IDs must be snake_case (e.g., "click_login_button")
5. Connect nodes with exec_out -> exec_in for execution flow
6. Use meaningful node IDs that describe the action
7. Position nodes with x starting at 0, incrementing by 400 for each node

## CRITICAL - Variable Reference Syntax
**ALWAYS use double curly braces: `{{{{node_id.output_port}}}}`**

WRONG ❌: `${{node.output}}`, `$variable`, `${{variable}}`, `{{{{node.result}}}}`
CORRECT ✅: `{{{{node_id.result_value}}}}`, `{{{{variable_name}}}}`

- NEVER use `$` symbol for variables!
- NEVER use `${{}}` syntax - this is shell/JS syntax, NOT CasareRPA!
- EnvironmentVariableNode output port is `result_value`, NOT `result`!

## PERFORMANCE RULES
- NEVER use WaitNode with hardcoded duration_ms values
- ALWAYS use WaitForElementNode with state='visible' before clicking elements
- Use element detection instead of fixed delays
- Prefer data-* selectors over fragile CSS selectors

## JSON Schema
```
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
```

## Available Node Types
{node_manifest}

## Common Node Configs
- GoToURLNode: {{"url": "https://..."}}
- ClickElementNode: {{"selector": "css selector or xpath"}}
- TypeTextNode: {{"selector": "...", "text": "...", "clear_first": true}}
- WaitForElementNode: {{"selector": "...", "timeout": 5000, "state": "visible"}}
- SetVariableNode: {{"variable_name": "...", "value": "..."}}
- IfNode: {{"condition": "expression"}}
- ForLoopStartNode: {{"items": "{{{{variable}}}}", "index_var": "i"}}
- ExtractTextNode: {{"selector": "..."}}
- ScreenshotNode: {{"path": "screenshot.png", "full_page": false}}
- LaunchApplicationNode: {{"application_path": "notepad.exe", "arguments": ""}}
- EnvironmentVariableNode: {{"action": "get", "var_name": "USERPROFILE"}}
- ListDirectoryNode: {{"dir_path": "C:\\path", "pattern": "*", "files_only": false}}

## CRITICAL - Node Output References
When one node's output is needed by another node, use: `{{{{node_id.output_port}}}}`

The manifest shows outputs as `NodeType(inputs)->output1,output2`. Use these output names!

**Example - List Desktop Directory:**
```json
{{
  "nodes": {{
    "get_profile": {{
      "node_id": "get_profile",
      "node_type": "EnvironmentVariableNode",
      "config": {{"action": "get", "var_name": "USERPROFILE"}},
      "position": [0, 0]
    }},
    "list_desktop": {{
      "node_id": "list_desktop",
      "node_type": "ListDirectoryNode",
      "config": {{"dir_path": "{{{{get_profile.result_value}}}}\\Desktop"}},
      "position": [400, 0]
    }}
  }},
  "connections": [
    {{"source_node": "get_profile", "source_port": "exec_out", "target_node": "list_desktop", "target_port": "exec_in"}}
  ]
}}
```

Output ONLY the JSON object with action nodes. NO StartNode or EndNode."""


# =============================================================================
# USE CASE CLASS
# =============================================================================


class GenerateWorkflowUseCase:
    """
    Use case for generating workflows from natural language descriptions.

    Uses LLM to convert natural language into valid CasareRPA workflow JSON,
    then validates the output against WorkflowAISchema.

    Features:
        - Configurable via AgentConfig
        - Comprehensive error handling
        - Extensive logging
        - Retry logic with temperature adjustment

    Example:
        use_case = GenerateWorkflowUseCase()
        workflow = await use_case.execute("Login to example.com")
    """

    DEFAULT_MODEL = "gpt-4o-mini"
    MAX_RETRIES = 2
    DEFAULT_TEMPERATURE = 0.2  # Low temperature for more deterministic output

    def __init__(
        self,
        llm_manager: ILLMManager | None = None,
        node_manifest_provider: INodeManifestProvider | None = None,
        config: AgentConfig | None = None,
    ) -> None:
        """
        Initialize the workflow generation use case.

        Args:
            llm_manager: Optional LLM resource manager. If None, creates one.
            node_manifest_provider: Provides node manifest markdown (DI-resolved if None).
            config: Optional agent configuration for customization.
        """
        self._llm_manager = llm_manager
        self._node_manifest_provider = node_manifest_provider
        self._config = config
        self._system_prompt: str | None = None

        logger.debug(
            f"GenerateWorkflowUseCase initialized: config={'custom' if config else 'default'}"
        )

    def _get_llm_manager(self) -> ILLMManager:
        """
        Get or create LLM resource manager.

        Returns:
            LLMResourceManager instance

        Raises:
            LLMCallError: If manager cannot be created
        """
        if self._llm_manager is None:
            try:
                self._llm_manager = _resolve_llm_manager(None)
                logger.debug("Resolved LLM manager via DI")
            except Exception as e:
                logger.error(f"Failed to resolve LLM manager: {e}")
                raise LLMCallError(
                    f"Failed to initialize LLM manager: {e}",
                    {"error": str(e)},
                ) from e

        return self._llm_manager

    def _build_system_prompt(self) -> str:
        """
        Build the system prompt with node manifest.

        Returns:
            Complete system prompt with node reference
        """
        if self._system_prompt is not None:
            return self._system_prompt

        logger.debug("Building system prompt...")

        try:
            provider = _resolve_node_manifest_provider(self._node_manifest_provider)
            node_manifest = provider.get_compact_markdown()
            logger.debug(f"Node manifest generated: {len(node_manifest)} chars")
        except Exception as e:
            logger.warning(f"Failed to generate node manifest: {e}")
            logger.debug(traceback.format_exc())
            node_manifest = self._get_fallback_manifest()

        # Add config-based customizations to prompt
        base_prompt = _SYSTEM_PROMPT_TEMPLATE.format(node_manifest=node_manifest)

        if self._config:
            try:
                # Add performance rules from config
                perf_prompt = self._config.build_performance_prompt()
                if perf_prompt:
                    base_prompt = f"{base_prompt}\n\n{perf_prompt}"

                # Add custom rules
                rules_prompt = self._config.build_rules_prompt()
                if rules_prompt:
                    base_prompt = f"{base_prompt}\n\n{rules_prompt}"

                # Add error handling instructions
                error_prompt = self._config.build_error_handling_prompt()
                if error_prompt:
                    base_prompt = f"{base_prompt}\n\n{error_prompt}"

                logger.debug("Applied config customizations to system prompt")
            except Exception as e:
                logger.warning(f"Failed to apply config customizations: {e}")

        self._system_prompt = base_prompt
        logger.debug(f"System prompt built: {len(self._system_prompt)} chars")
        return self._system_prompt

    def _get_fallback_manifest(self) -> str:
        """Get fallback manifest if registry dump fails."""
        logger.warning("Using fallback node manifest")
        return """## browser
- GoToURLNode(url)->exec_out
- ClickElementNode(selector)->exec_out
- TypeTextNode(selector,text)->exec_out
- WaitForElementNode(selector)->exec_out
- ExtractTextNode(selector)->exec_out,text
- ScreenshotNode(path)->exec_out

## control_flow
- IfNode(condition)->true_out,false_out
- ForLoopStartNode(items)->exec_out,loop_out
- ForLoopEndNode(exec_in)->exec_out
- TryCatchNode()->try_out,catch_out

## data
- SetVariableNode(variable_name,value)->exec_out
- GetVariableNode(variable_name)->exec_out,value

## file
- ReadFileNode(file_path)->exec_out,content
- WriteFileNode(file_path,content)->exec_out

## desktop
- LaunchApplicationNode(application_path)->exec_out
- SendKeysNode(keys)->exec_out"""

    def _extract_json_from_response(self, response: str) -> str:
        """
        Extract JSON from LLM response, handling potential markdown blocks.

        Args:
            response: Raw LLM response

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

    def _parse_and_validate(self, json_str: str) -> WorkflowAISchema:
        """
        Parse JSON string and validate against schema.

        Args:
            json_str: JSON string to parse

        Returns:
            Validated WorkflowAISchema

        Raises:
            JSONParseError: If JSON parsing fails
            SchemaValidationError: If schema validation fails
        """
        logger.debug("Parsing and validating JSON...")

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            raise JSONParseError(
                f"Invalid JSON: {e}",
                json_str,
            ) from e

        try:
            validated = WorkflowAISchema.model_validate(data)
            logger.debug(
                f"Schema validation passed: {len(validated.nodes)} nodes, "
                f"{len(validated.connections)} connections"
            )
            return validated
        except Exception as e:
            logger.error(f"Schema validation failed: {e}")
            raise SchemaValidationError(
                f"Schema validation failed: {e}",
                [str(e)],
            ) from e

    def _ensure_start_node(self, workflow: WorkflowAISchema) -> WorkflowAISchema:
        """
        Ensure workflow has a StartNode, add one if missing.

        Args:
            workflow: Workflow to check

        Returns:
            Workflow with StartNode
        """
        try:
            has_start = any(node.node_type == "StartNode" for node in workflow.nodes.values())

            if has_start:
                return workflow

            logger.info("Adding missing StartNode to workflow")

            # Create new nodes dict with StartNode
            new_nodes = {
                "start_node": NodeSchema(
                    node_id="start_node",
                    node_type="StartNode",
                    config={},
                    position=PositionSchema(x=-400, y=0),
                ),
                **workflow.nodes,
            }

            # Find first non-start node to connect to
            first_node_id: str | None = None
            for node_id, node in workflow.nodes.items():
                if node.node_type != "StartNode":
                    first_node_id = node_id
                    break

            # Create new connections list
            new_connections = list(workflow.connections)
            if first_node_id:
                new_connections.insert(
                    0,
                    ConnectionSchema(
                        source_node="start_node",
                        source_port="exec_out",
                        target_node=first_node_id,
                        target_port="exec_in",
                    ),
                )

            return WorkflowAISchema(
                metadata=workflow.metadata,
                nodes=new_nodes,
                connections=new_connections,
                variables=workflow.variables,
                settings=workflow.settings,
            )
        except Exception as e:
            logger.warning(f"Failed to ensure StartNode: {e}")
            return workflow

    def _ensure_end_node(self, workflow: WorkflowAISchema) -> WorkflowAISchema:
        """
        Ensure workflow has an EndNode, add one if missing.

        Args:
            workflow: Workflow to check

        Returns:
            Workflow with EndNode
        """
        try:
            has_end = any(node.node_type == "EndNode" for node in workflow.nodes.values())

            if has_end:
                return workflow

            logger.info("Adding missing EndNode to workflow")

            # Find last node (one that has no outgoing connections)
            source_nodes = {conn.source_node for conn in workflow.connections}
            target_nodes = {conn.target_node for conn in workflow.connections}
            terminal_nodes = source_nodes - target_nodes

            # If no terminal nodes found, use last node by dict order
            if not terminal_nodes:
                node_ids = list(workflow.nodes.keys())
                if node_ids:
                    terminal_nodes = {node_ids[-1]}

            # Calculate max x position for EndNode placement
            max_x = 0.0
            for node in workflow.nodes.values():
                if node.position:
                    max_x = max(max_x, node.position.x)

            # Create new nodes dict with EndNode
            new_nodes = {
                **workflow.nodes,
                "end_node": NodeSchema(
                    node_id="end_node",
                    node_type="EndNode",
                    config={},
                    position=PositionSchema(x=max_x + 400, y=0),
                ),
            }

            # Connect terminal nodes to EndNode
            new_connections = list(workflow.connections)
            for terminal_id in terminal_nodes:
                if (
                    terminal_id in workflow.nodes
                    and workflow.nodes[terminal_id].node_type != "EndNode"
                ):
                    new_connections.append(
                        ConnectionSchema(
                            source_node=terminal_id,
                            source_port="exec_out",
                            target_node="end_node",
                            target_port="exec_in",
                        )
                    )

            return WorkflowAISchema(
                metadata=workflow.metadata,
                nodes=new_nodes,
                connections=new_connections,
                variables=workflow.variables,
                settings=workflow.settings,
            )
        except Exception as e:
            logger.warning(f"Failed to ensure EndNode: {e}")
            return workflow

    def _auto_connect_sequential(self, workflow: WorkflowAISchema) -> WorkflowAISchema:
        """
        Auto-connect nodes sequentially if connections list is empty.

        Args:
            workflow: Workflow to process

        Returns:
            Workflow with auto-generated connections
        """
        if workflow.connections:
            return workflow

        try:
            logger.info("Auto-connecting nodes sequentially")

            node_ids = list(workflow.nodes.keys())
            if len(node_ids) < 2:
                return workflow

            new_connections: list[ConnectionSchema] = []
            for i in range(len(node_ids) - 1):
                source_id = node_ids[i]
                target_id = node_ids[i + 1]

                # Skip connecting EndNode as source
                if workflow.nodes[source_id].node_type == "EndNode":
                    continue

                # Skip connecting StartNode as target
                if workflow.nodes[target_id].node_type == "StartNode":
                    continue

                new_connections.append(
                    ConnectionSchema(
                        source_node=source_id,
                        source_port="exec_out",
                        target_node=target_id,
                        target_port="exec_in",
                    )
                )

            return WorkflowAISchema(
                metadata=workflow.metadata,
                nodes=workflow.nodes,
                connections=new_connections,
                variables=workflow.variables,
                settings=workflow.settings,
            )
        except Exception as e:
            logger.warning(f"Failed to auto-connect nodes: {e}")
            return workflow

    def _assign_node_positions(
        self,
        workflow: WorkflowAISchema,
        spacing_x: float = 400.0,
        spacing_y: float = 0.0,
    ) -> WorkflowAISchema:
        """
        Assign canvas positions to nodes to prevent overlap.

        Nodes are laid out horizontally with configurable spacing.
        Default spacing is 400px between nodes.

        Args:
            workflow: Workflow to process
            spacing_x: Horizontal spacing between nodes (default: 400px)
            spacing_y: Vertical offset for each node (default: 0)

        Returns:
            Workflow with positions assigned to all nodes
        """
        try:
            logger.debug(f"Assigning positions: spacing_x={spacing_x}, spacing_y={spacing_y}")

            new_nodes: dict[str, NodeSchema] = {}
            x_pos = 0.0
            y_pos = 0.0

            for node_id, node in workflow.nodes.items():
                # Use existing position if valid, otherwise assign new one
                if node.position and node.position.x is not None:
                    new_nodes[node_id] = node
                else:
                    new_nodes[node_id] = NodeSchema(
                        node_id=node.node_id,
                        node_type=node.node_type,
                        config=node.config,
                        position=PositionSchema(x=x_pos, y=y_pos),
                    )
                x_pos += spacing_x
                y_pos += spacing_y

            return WorkflowAISchema(
                metadata=workflow.metadata,
                nodes=new_nodes,
                connections=workflow.connections,
                variables=workflow.variables,
                settings=workflow.settings,
            )
        except Exception as e:
            logger.warning(f"Failed to assign node positions: {e}")
            return workflow

    def _get_effective_temperature(self, attempt: int) -> float:
        """
        Calculate effective temperature for retry attempt.

        Args:
            attempt: Current attempt number (0-indexed)

        Returns:
            Temperature value to use
        """
        base_temp = self._config.temperature if self._config else self.DEFAULT_TEMPERATURE

        if self._config:
            return self._config.get_effective_temperature(attempt)

        # Default: increase by 0.1 per attempt, max 0.5
        return min(base_temp + (attempt * 0.1), 0.5)

    async def execute(
        self,
        query: str,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int = 4000,
    ) -> WorkflowAISchema:
        """
        Generate a workflow from natural language query.

        Args:
            query: Natural language description of the workflow
            model: LLM model to use (default: config.model or gpt-4o-mini)
            temperature: Sampling temperature (default: config.temperature or 0.2)
            max_tokens: Maximum tokens in response

        Returns:
            Validated WorkflowAISchema

        Raises:
            WorkflowGenerationError: If generation fails after retries
        """
        start_time = time.time()

        # Validate input
        if not query or not query.strip():
            logger.warning("Empty query provided")
            raise WorkflowGenerationError(
                "Query cannot be empty",
                "INVALID_INPUT",
                {"query": query},
            )

        # Determine model from config or default
        model_name = model or (self._config.model if self._config else self.DEFAULT_MODEL)

        max_retries = (
            self._config.retry.max_generation_retries if self._config else self.MAX_RETRIES
        )

        logger.info(
            f"Generating workflow: query='{query[:100]}...', "
            f"model={model_name}, max_retries={max_retries}"
        )

        try:
            llm = self._get_llm_manager()
        except LLMCallError:
            raise
        except Exception as e:
            logger.error(f"Failed to get LLM manager: {e}")
            raise LLMCallError(f"Failed to initialize LLM: {e}") from e

        try:
            system_prompt = self._build_system_prompt()
        except Exception as e:
            logger.error(f"Failed to build system prompt: {e}")
            raise WorkflowGenerationError(
                f"Failed to build system prompt: {e}",
                "PROMPT_ERROR",
            )

        last_error: Exception | None = None

        for attempt in range(max_retries + 1):
            attempt_start = time.time()
            temp = (
                temperature if temperature is not None else self._get_effective_temperature(attempt)
            )

            logger.debug(f"Generation attempt {attempt + 1}/{max_retries + 1}: temp={temp:.2f}")

            try:
                # Call LLM
                response = await llm.completion(
                    prompt=query,
                    model=model_name,
                    system_prompt=system_prompt,
                    temperature=temp,
                    max_tokens=max_tokens,
                )

                attempt_duration = (time.time() - attempt_start) * 1000
                logger.debug(
                    f"LLM response received in {attempt_duration:.2f}ms: "
                    f"{len(response.content)} chars"
                )

                # Extract and parse JSON
                json_str = self._extract_json_from_response(response.content)
                workflow = self._parse_and_validate(json_str)

                # Post-processing
                workflow = self._ensure_start_node(workflow)
                workflow = self._ensure_end_node(workflow)
                workflow = self._auto_connect_sequential(workflow)
                workflow = self._assign_node_positions(workflow)

                total_duration = (time.time() - start_time) * 1000
                logger.info(
                    f"Generated workflow '{workflow.metadata.name}' with "
                    f"{len(workflow.nodes)} nodes, {len(workflow.connections)} connections "
                    f"in {total_duration:.2f}ms (attempt {attempt + 1})"
                )

                return workflow

            except (JSONParseError, SchemaValidationError) as e:
                last_error = e
                logger.warning(f"Generation attempt {attempt + 1} failed: {e.error_type}: {e}")

                if attempt < max_retries:
                    logger.info(
                        f"Retrying with temperature {self._get_effective_temperature(attempt + 1):.2f}"
                    )

            except LLMCallError as e:
                last_error = e
                logger.error(f"LLM call failed on attempt {attempt + 1}: {e}")

                if attempt >= max_retries:
                    break

            except Exception as e:
                last_error = WorkflowGenerationError(
                    f"Unexpected error: {e}",
                    "UNEXPECTED_ERROR",
                    {"error": str(e), "traceback": traceback.format_exc()},
                )
                logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
                logger.debug(traceback.format_exc())

                if attempt >= max_retries:
                    break

        # All retries exhausted
        total_duration = (time.time() - start_time) * 1000
        logger.error(
            f"Workflow generation failed after {max_retries + 1} attempts in {total_duration:.2f}ms"
        )

        raise WorkflowGenerationError(
            f"Workflow generation failed after {max_retries + 1} attempts",
            "MAX_RETRIES_EXCEEDED",
            {"last_error": str(last_error), "attempts": max_retries + 1},
        ) from last_error


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================


async def generate_workflow_from_text(
    query: str,
    model: str = "gpt-4o-mini",
    llm_manager: ILLMManager | None = None,
    config: AgentConfig | None = None,
) -> dict[str, Any]:
    """
    Simple interface for generating workflow from natural language.

    Args:
        query: Natural language description of the workflow
        model: LLM model to use
        llm_manager: Optional LLM resource manager
        config: Optional agent configuration

    Returns:
        Workflow dictionary compatible with WorkflowSchema.from_dict()

    Raises:
        WorkflowGenerationError: If generation fails
    """
    logger.info(f"generate_workflow_from_text called: query='{query[:50]}...'")

    try:
        use_case = GenerateWorkflowUseCase(
            llm_manager=llm_manager,
            node_manifest_provider=None,
            config=config,
        )
        workflow = await use_case.execute(query=query, model=model)
        return workflow.to_dict()
    except WorkflowGenerationError:
        raise
    except Exception as e:
        logger.error(f"generate_workflow_from_text failed: {e}")
        logger.debug(traceback.format_exc())
        raise WorkflowGenerationError(
            f"Generation failed: {e}",
            "GENERATION_FAILED",
        ) from e


__all__ = [
    "GenerateWorkflowUseCase",
    "WorkflowGenerationError",
    "LLMCallError",
    "JSONParseError",
    "SchemaValidationError",
    "generate_workflow_from_text",
]
