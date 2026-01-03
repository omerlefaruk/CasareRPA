"""
Core implementation of SmartWorkflowAgent.
"""

from __future__ import annotations

import asyncio
import json
import re
import time
import traceback
from typing import TYPE_CHECKING, Any

from loguru import logger

from casare_rpa.domain.schemas.workflow_ai import (
    EditWorkflowSchema,
    WorkflowAISchema,
)
from casare_rpa.domain.validation import (
    ValidationResult,
)
from casare_rpa.infrastructure.ai.agent.exceptions import (
    JSONParseError,
    LLMCallError,
    ValidationError,
)
from casare_rpa.infrastructure.ai.agent.prompts import (
    APPEND_SYSTEM_PROMPT,
    EDIT_SYSTEM_PROMPT,
    GENERATION_SYSTEM_PROMPT,
    MULTI_TURN_SYSTEM_PROMPT,
    PAGE_CONTEXT_TEMPLATE,
    REFINE_SYSTEM_PROMPT,
    REPAIR_PROMPT_TEMPLATE,
)
from casare_rpa.infrastructure.ai.agent.sandbox import HeadlessWorkflowSandbox
from casare_rpa.infrastructure.ai.agent.types import (
    GenerationAttempt,
    WorkflowGenerationResult,
)
from casare_rpa.infrastructure.ai.registry_dumper import (
    NodeManifest,
    dump_node_manifest,
    manifest_to_markdown,
)

if TYPE_CHECKING:
    from casare_rpa.domain.ai.config import AgentConfig
    from casare_rpa.infrastructure.ai.conversation_manager import (
        ConversationManager,
        UserIntent,
    )
    from casare_rpa.infrastructure.ai.page_analyzer import PageContext
    from casare_rpa.infrastructure.resources.llm_resource_manager import (
        LLMResourceManager,
    )


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

    DEFAULT_MODEL = "openrouter/google/gemini-3-flash-preview"
    DEFAULT_TEMPERATURE = 0.2
    DEFAULT_MAX_TOKENS = 4000
    DEFAULT_MAX_RETRIES = 3

    # RAG Configuration
    RAG_TOP_K = 15  # Number of relevant nodes to retrieve
    RAG_COLLECTION = "casare_nodes"  # Vector store collection name
    CORE_NODE_CATEGORIES = frozenset({"control_flow", "data"})  # Always include these

    # URL Detection Pattern
    URL_PATTERN = re.compile(r'https?://[^\s<>"\')\]]+', re.IGNORECASE)
    MAX_URLS_TO_ANALYZE = 3  # Limit URLs to analyze per request

    def __init__(
        self,
        llm_client: LLMResourceManager | None = None,
        max_retries: int | None = None,
        config: AgentConfig | None = None,
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
            else (config.retry.max_generation_retries if config else self.DEFAULT_MAX_RETRIES)
        )
        self.validator = HeadlessWorkflowSandbox()
        self._system_prompt_cache: str | None = None
        self._manifest_cache: str | None = None

        # RAG components (lazy initialized)
        self._vector_store: Any | None = None
        self._embedding_manager: Any | None = None
        self._rag_initialized: bool = False
        self._rag_available: bool = False
        self._nodes_indexed: bool = False

        # Page context (Playwright MCP integration)
        self._page_context_cache: dict[str, PageContext] = {}
        self._mcp_available: bool | None = None  # Lazy check

        logger.debug(
            f"SmartWorkflowAgent initialized: max_retries={self.max_retries}, "
            f"config={'custom' if config else 'default'}"
        )

    @property
    def config(self) -> AgentConfig | None:
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
            # Use verbose markdown so the agent understands what nodes actually do
            self._manifest_cache = manifest_to_markdown(manifest)
            logger.debug(f"Node manifest generated: {len(self._manifest_cache)} chars")
        except Exception as e:
            logger.warning(f"Failed to generate node manifest: {e}")
            logger.debug(traceback.format_exc())
            self._manifest_cache = self._get_fallback_manifest()

        return self._manifest_cache

    async def _ensure_rag_initialized(self) -> bool:
        """Initialize RAG components if available."""
        if self._rag_initialized:
            return self._rag_available

        try:
            from casare_rpa.infrastructure.ai.embedding_manager import (
                get_embedding_manager,
            )
            from casare_rpa.infrastructure.ai.vector_store import get_vector_store

            self._vector_store = get_vector_store()
            self._embedding_manager = get_embedding_manager()

            # Check if nodes are already indexed
            if await self._vector_store.collection_exists(self.RAG_COLLECTION):
                count = await self._vector_store.count_documents(self.RAG_COLLECTION)
                if count == 0:
                    logger.info("RAG index empty. Indexing nodes...")
                    await self._index_nodes()
                else:
                    self._nodes_indexed = True
                    logger.debug(f"RAG index validation: {count} nodes found")
            else:
                logger.info("RAG collection missing. Indexing nodes...")
                await self._index_nodes()

            self._rag_available = True
            logger.debug("RAG components initialized successfully")
        except ImportError:
            logger.warning("RAG dependencies (chromadb/litellm) not found. RAG disabled.")
            self._rag_available = False
        except Exception as e:
            logger.error(f"Failed to initialize RAG: {e}")
            self._rag_available = False

        self._rag_initialized = True
        return self._rag_available

    async def _index_nodes(self) -> None:
        """Index all registered nodes into vector store."""
        if not self._vector_store:
            return

        try:
            from casare_rpa.infrastructure.ai.vector_store import Document

            manifest = dump_node_manifest()
            documents = []

            for node in manifest.nodes:
                # Create rich semantic representation for embedding
                content = (
                    f"Node: {node.type}\n"
                    f"Category: {node.category}\n"
                    f"Description: {node.description}\n"
                    f"Inputs: {', '.join(p.name for p in node.inputs)}\n"
                    f"Outputs: {', '.join(p.name for p in node.outputs)}"
                )

                doc = Document(
                    id=node.type,
                    content=content,
                    metadata={
                        "type": node.type,
                        "category": node.category,
                        "description": node.description,
                    },
                )
                documents.append(doc)

            await self._vector_store.add_documents(documents, collection=self.RAG_COLLECTION)
            self._nodes_indexed = True
            logger.info(f"Indexed {len(documents)} nodes for RAG")

        except Exception as e:
            logger.error(f"Failed to index nodes: {e}")
            self._nodes_indexed = False

    async def _get_relevant_manifest(self, query: str) -> str:
        """Get manifest with only nodes relevant to the query + core nodes."""
        if not await self._ensure_rag_initialized():
            return self._get_node_manifest()

        try:
            # Search for relevant nodes
            results = await self._vector_store.search(
                query=query, collection=self.RAG_COLLECTION, top_k=self.RAG_TOP_K
            )

            relevant_types = {res.metadata["type"] for res in results}
            logger.debug(f"RAG retrieved {len(relevant_types)} nodes for query: '{query}'")

            # Fetch full manifest to filter
            full_manifest = dump_node_manifest()

            filtered_nodes = []
            relevant_categories = set()

            for node in full_manifest.nodes:
                is_core = node.category in self.CORE_NODE_CATEGORIES
                is_relevant = node.type in relevant_types

                if is_core or is_relevant:
                    filtered_nodes.append(node)
                    relevant_categories.add(node.category)

            # Create filtered manifest object
            filtered_manifest = NodeManifest(
                nodes=tuple(filtered_nodes),
                categories=frozenset(relevant_categories),
                total_count=len(filtered_nodes),
                generated_at=full_manifest.generated_at,
            )

            return manifest_to_markdown(filtered_manifest)

        except Exception as e:
            logger.error(f"RAG retrieval failed: {e}. Falling back to full manifest.")
            return self._get_node_manifest()

    def _detect_urls(self, prompt: str) -> list[str]:
        """
        Extract URLs from user prompt.

        Args:
            prompt: User prompt text

        Returns:
            List of detected URLs (limited to MAX_URLS_TO_ANALYZE)
        """
        urls = self.URL_PATTERN.findall(prompt)
        # Clean up URLs (remove trailing punctuation)
        cleaned = []
        for url in urls:
            url = url.rstrip(".,;:!?")
            if url not in cleaned:
                cleaned.append(url)
        return cleaned[: self.MAX_URLS_TO_ANALYZE]

    async def _check_mcp_available(self) -> bool:
        """Check if Playwright MCP is available."""
        if self._mcp_available is not None:
            return self._mcp_available

        try:
            from casare_rpa.infrastructure.ai.playwright_mcp import PlaywrightMCPClient

            # Quick check - can we import and find npx?
            client = PlaywrightMCPClient(headless=True)
            self._mcp_available = client._npx_path is not None
            logger.debug(f"Playwright MCP available: {self._mcp_available}")
        except ImportError:
            logger.debug("Playwright MCP not available (import failed)")
            self._mcp_available = False
        except Exception as e:
            logger.debug(f"Playwright MCP not available: {e}")
            self._mcp_available = False

        return self._mcp_available

    async def _fetch_page_context(self, url: str) -> PageContext | None:
        """
        Fetch page context for a URL using Playwright MCP.

        Args:
            url: URL to analyze

        Returns:
            PageContext with extracted page elements, or None on failure
        """
        # Check cache first
        if url in self._page_context_cache:
            logger.debug(f"Using cached page context for {url}")
            return self._page_context_cache[url]

        # Check if MCP is available
        if not await self._check_mcp_available():
            logger.debug("Skipping page context - MCP not available")
            return None

        try:
            from casare_rpa.infrastructure.ai.page_analyzer import PageAnalyzer
            from casare_rpa.infrastructure.ai.playwright_mcp import PlaywrightMCPClient

            logger.info(f"Fetching page context for: {url}")

            async with PlaywrightMCPClient(headless=True) as client:
                # Navigate to URL
                nav_result = await client.navigate(url)
                if not nav_result.success:
                    logger.warning(f"Failed to navigate to {url}: {nav_result.error}")
                    return None

                # Wait for page to stabilize
                await client.wait_for(time_seconds=2.0)

                # Get accessibility snapshot
                snapshot_result = await client.get_snapshot()
                if not snapshot_result.success:
                    logger.warning(f"Failed to get snapshot: {snapshot_result.error}")
                    return None

                # Get page title
                title_result = await client.evaluate("() => document.title")
                title = title_result.get_text() if title_result.success else ""

                # Analyze snapshot
                analyzer = PageAnalyzer()
                context = analyzer.analyze_snapshot(
                    snapshot=snapshot_result.get_text(),
                    url=url,
                    title=title,
                )

                # Cache result
                self._page_context_cache[url] = context

                logger.info(
                    f"Page context extracted: {len(context.forms)} forms, "
                    f"{len(context.buttons)} buttons, {len(context.inputs)} inputs"
                )
                return context

        except Exception as e:
            logger.error(f"Failed to fetch page context for {url}: {e}")
            logger.debug(traceback.format_exc())
            return None

    async def _fetch_page_contexts(self, urls: list[str]) -> list[PageContext]:
        """
        Fetch page contexts for multiple URLs.

        Args:
            urls: List of URLs to analyze

        Returns:
            List of PageContext objects (may be shorter than input if some fail)
        """
        contexts = []
        for url in urls:
            context = await self._fetch_page_context(url)
            if context and not context.is_empty():
                contexts.append(context)
        return contexts

    def _format_page_contexts(self, contexts: list[PageContext]) -> str:
        """
        Format page contexts for injection into system prompt.

        Args:
            contexts: List of PageContext objects

        Returns:
            Formatted string for prompt injection
        """
        if not contexts:
            return ""

        context_strs = [ctx.to_prompt_context() for ctx in contexts]
        combined = "\n\n---\n\n".join(context_strs)

        return PAGE_CONTEXT_TEMPLATE.format(page_contexts=combined)

    def _build_system_prompt(self, node_manifest: str | None = None) -> str:
        """Build system prompt with node manifest and config options."""
        # Only use cache if no custom manifest provided
        if node_manifest is None and self._system_prompt_cache is not None:
            return self._system_prompt_cache

        manifest_to_use = node_manifest or self._get_node_manifest()
        base_prompt = GENERATION_SYSTEM_PROMPT.format(node_manifest=manifest_to_use)

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

        # Cache only if it's the default manifest
        if node_manifest is None:
            self._system_prompt_cache = base_prompt

        logger.debug(f"System prompt built: {len(base_prompt)} chars")
        return base_prompt

    def _get_fallback_manifest(self) -> str:
        """Get fallback manifest if registry dump fails."""
        logger.warning("Using fallback node manifest")
        return """# CasareRPA Node Reference (Fallback)

## Browser
**GoToURLNode** - Navigate to a specific URL.
  IN: `url:STRING`, `page:PAGE?`
  OUT: `exec_out:EXEC`, `page:PAGE`

**ClickElementNode** - Click an element on the page.
  IN: `selector:STRING`, `page:PAGE?`
  OUT: `exec_out:EXEC`

**TypeTextNode** - Type text into an input field.
  IN: `selector:STRING`, `text:STRING`, `page:PAGE?`
  OUT: `exec_out:EXEC`

## Control Flow
**IfNode** - Conditional branching based on expression.
  IN: `condition:STRING`, `exec_in:EXEC`
  OUT: `true:EXEC`, `false:EXEC`

**ForLoopStartNode** - Iterate over a list of items.
  IN: `items:LIST`, `exec_in:EXEC`
  OUT: `body:EXEC`, `completed:EXEC`, `current_item:ANY`

**WaitNode** - Pause execution for a duration.
  IN: `duration_ms:INT`
  OUT: `exec_out:EXEC`

## Data
**SetVariableNode** - Set a variable value.
  IN: `variable_name:STRING`, `value:ANY`
  OUT: `exec_out:EXEC`
"""

    def _extract_json_from_response(self, response: str) -> str:
        """
        Extract JSON from LLM response.

        Handles new Chain-of-Thought (CoT) format where JSON is inside a code block
        after a <thinking> section.

        Args:
            response: Raw LLM response text

        Returns:
            Cleaned JSON string

        Raises:
            JSONParseError: If no valid JSON found
        """
        content = response.strip()
        logger.debug(f"Extracting JSON from response ({len(content)} chars)")

        # 1. Try to find JSON inside a markdown code block (most reliable for CoT)
        # Look for ```json ... ``` or just ``` ... ```
        json_block_match = re.search(
            r"```(?:json)?\s*\n?(.*?)\n?```",
            content,
            re.DOTALL | re.IGNORECASE,
        )
        if json_block_match:
            json_candidate = json_block_match.group(1).strip()
            # Verify it looks like a JSON object
            if json_candidate.startswith("{") and json_candidate.endswith("}"):
                logger.debug("Extracted JSON from markdown code block")
                return json_candidate

        # 2. Fallback: Find the first outer-most JSON object in the text
        # This handles cases where the model forgets code blocks but outputs JSON
        start_idx = content.find("{")
        if start_idx == -1:
            # Check if this is a chat response (text without JSON)
            # Filter out thinking blocks to get the actual message
            message_content = re.sub(
                r"<thinking>.*?</thinking>", "", content, flags=re.DOTALL
            ).strip()

            if message_content and "Error" not in message_content[:20]:
                logger.debug("No JSON found, treating as chat response")
                return json.dumps({"type": "chat", "message": message_content})

            logger.error("No JSON object found in response")
            # If we have a thinking block but no JSON, capture that context
            thinking_match = re.search(r"<thinking>(.*?)</thinking>", content, re.DOTALL)
            context = ""
            if thinking_match:
                context = f"\nThinking was: {thinking_match.group(1)[:200]}..."

            raise JSONParseError(f"No JSON object found in response.{context}", content)

        # Find matching closing brace using simple counter
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
        logger.debug(f"Extracted JSON by scanning: {len(json_str)} chars")
        return json_str

    def _parse_workflow_json(self, json_str: str) -> dict[str, Any]:
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

        # Check if this is an edit response
        if EditWorkflowSchema.is_edit_response(data):
            try:
                validated = EditWorkflowSchema.model_validate(data)
                result = validated.to_dict()
                logger.debug(
                    f"Edit workflow parsed: {len(result.get('modifications', []))} modifications"
                )
                return result
            except Exception as e:
                logger.error(f"Edit schema validation failed: {e}")
                raise ValidationError(
                    f"Edit schema validation failed: {e}",
                    [str(e)],
                ) from e

        # Check if this is a chat response
        if data.get("type") == "chat":
            return data

        # Fill in default values for missing required fields
        data = self._fill_default_workflow_fields(data)

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

    def _fill_default_workflow_fields(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Fill in default values for missing required workflow fields.

        AI sometimes generates only nodes without metadata, variables, or settings.
        This method fills in sensible defaults to make such workflows valid.

        Args:
            data: Raw workflow dictionary from AI

        Returns:
            Workflow dictionary with defaults filled in
        """
        # Ensure metadata exists with minimum required fields
        if "metadata" not in data:
            logger.debug("Adding default metadata to workflow")
            data["metadata"] = {
                "name": "AI Generated Workflow",
                "description": "Workflow generated by AI assistant",
                "version": "1.0.0",
            }
        elif isinstance(data["metadata"], dict):
            # Ensure name is present (required field)
            if "name" not in data["metadata"]:
                data["metadata"]["name"] = "AI Generated Workflow"
            # Fill other optional fields
            if "version" not in data["metadata"]:
                data["metadata"]["version"] = "1.0.0"

        # Ensure other required sections exist
        if "variables" not in data:
            data["variables"] = {}

        if "settings" not in data:
            data["settings"] = {
                "stop_on_error": True,
                "timeout": 30,
                "retry_count": 0,
            }

        if "connections" not in data:
            data["connections"] = []

        if "nodes" not in data:
            data["nodes"] = {}
        elif not isinstance(data["nodes"], dict):
            raise ValueError("workflow.nodes must be a dictionary")

        return data

    def _build_repair_prompt(self, workflow_json: str, errors: list[str]) -> str:
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
        return REPAIR_PROMPT_TEMPLATE.format(
            errors=errors_text,
            workflow_json=workflow_json,
        )

    def _ensure_start_and_end_nodes(self, workflow: dict[str, Any]) -> dict[str, Any]:
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
        self, workflow: dict[str, Any], spacing_x: float = 400.0
    ) -> dict[str, Any]:
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

    def _strip_start_end_nodes(self, workflow: dict[str, Any]) -> dict[str, Any]:
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

    def _calculate_append_position(self, existing_workflow: dict[str, Any]) -> tuple[str, float]:
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
        logger.debug(f"LLM call attempt {attempt + 1}: model={model}, temp={temperature:.2f}")
        start_time = time.time()

        try:
            llm = self._get_llm_client()
            response = await llm.completion(
                prompt=prompt,
                model=model,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=self._config.max_tokens if self._config else self.DEFAULT_MAX_TOKENS,
            )

            duration_ms = (time.time() - start_time) * 1000
            logger.debug(
                f"LLM response received in {duration_ms:.2f}ms: {response.total_tokens} tokens"
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
        existing_workflow: dict[str, Any] | None = None,
        canvas_state: dict[str, Any] | None = None,
        is_edit: bool = False,
        model: str | None = None,
        temperature: float | None = None,
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
        attempt_history: list[GenerationAttempt] = []
        validation_history: list[ValidationResult] = []

        # Validate input
        if not user_prompt or not user_prompt.strip():
            logger.warning("Empty user prompt provided")
            return WorkflowGenerationResult(
                success=False,
                error="User prompt cannot be empty",
            )

        # Determine parameters from config or defaults
        model_name = model or (self._config.model if self._config else self.DEFAULT_MODEL)
        base_temp = (
            temperature
            if temperature is not None
            else (self._config.temperature if self._config else self.DEFAULT_TEMPERATURE)
        )

        logger.info(
            f"Starting workflow generation: prompt='{user_prompt[:100]}...', "
            f"model={model_name}, mode={'edit' if is_edit else 'append' if existing_workflow else 'generate'}"
        )

        # Build appropriate system prompt based on mode
        try:
            # Get appropriate manifest (RAG-filtered or full)
            # This dynamically selects nodes relevant to the user request
            manifest_context = await self._get_relevant_manifest(user_prompt)
            base_instructions = self._build_system_prompt(manifest_context)

            # Detect URLs and fetch page context for browser workflows
            page_context_str = ""
            detected_urls = self._detect_urls(user_prompt)
            if detected_urls:
                logger.info(f"Detected {len(detected_urls)} URLs in prompt: {detected_urls}")
                try:
                    page_contexts = await self._fetch_page_contexts(detected_urls)
                    if page_contexts:
                        page_context_str = self._format_page_contexts(page_contexts)
                        logger.info(f"Added page context for {len(page_contexts)} URLs")
                except Exception as e:
                    # Page context is optional - continue without it
                    logger.warning(f"Failed to fetch page contexts: {e}")

            # Append page context to base instructions if available
            if page_context_str:
                base_instructions = base_instructions + "\n\n" + page_context_str

            if is_edit and canvas_state:
                logger.debug("Using EDIT mode")
                system_prompt = EDIT_SYSTEM_PROMPT.format(
                    canvas_state=json.dumps(canvas_state, indent=2)[:3000],
                    base_instructions=base_instructions,
                )
            elif existing_workflow:
                logger.debug("Using APPEND mode")
                system_prompt = APPEND_SYSTEM_PROMPT.format(
                    canvas_state=json.dumps(canvas_state, indent=2)[:2000]
                    if canvas_state
                    else "{}",
                    base_instructions=base_instructions,
                )
            else:
                logger.debug("Using GENERATE mode")
                system_prompt = base_instructions
        except Exception as e:
            logger.error(f"Failed to build system prompt: {e}")
            return WorkflowGenerationResult(
                success=False,
                error=f"Failed to build system prompt: {e}",
            )

        current_prompt = user_prompt
        last_json_str = ""
        last_raw_response = ""  # Track raw LLM response for debugging

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
                last_raw_response = response_content  # Store for debugging

                # Extract and parse JSON
                json_str = self._extract_json_from_response(response_content)
                last_json_str = json_str
                workflow = self._parse_workflow_json(json_str)

                # Check if this is an edit response (skip standard workflow processing)
                is_edit_response = workflow.get("action") == "edit" and "modifications" in workflow
                is_chat_response = workflow.get("type") == "chat"

                if not is_edit_response and not is_chat_response:
                    # Post-process workflow (only for new/append workflows)
                    if self._config is None or self._config.strip_start_end_nodes:
                        workflow = self._strip_start_end_nodes(workflow)
                    workflow = self._assign_node_positions(workflow)

                    # Merge with existing workflow if in append mode
                    if existing_workflow:
                        workflow = self._merge_workflows(existing_workflow, workflow)

                # Validate (skip for edit/chat responses - they have different structure)
                if is_edit_response:
                    # Edit responses are pre-validated by schema, add empty validation result
                    validation_history.append(ValidationResult(is_valid=True))
                    logger.debug(
                        f"Edit response validated with {len(workflow.get('modifications', []))} modifications"
                    )
                elif is_chat_response:
                    # Chat responses don't need workflow validation
                    validation_history.append(ValidationResult(is_valid=True))
                    logger.debug(f"Chat response: {workflow.get('message', '')[:100]}...")
                elif self._config is None or self._config.validate_before_return:
                    result = self.validator.validate_workflow(workflow)
                    validation_history.append(result)

                    if not result.is_valid:
                        errors = [f"{issue.code}: {issue.message}" for issue in result.errors]

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
                        attempt_record.duration_ms = (time.time() - attempt_start) * 1000
                        attempt_history.append(attempt_record)

                        logger.debug(
                            f"Validation failed on attempt {attempt + 1}: {len(errors)} errors"
                        )
                        # Log each error for debugging
                        for i, err in enumerate(errors[:10], 1):  # Limit to first 10
                            logger.debug(f"  Error {i}: {err}")

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
                    raw_response=last_raw_response,
                )

            except JSONParseError as e:
                logger.warning(f"JSON parse error on attempt {attempt + 1}: {e}")
                current_prompt = (
                    f"JSON parse error: {e}. Fix the syntax and output valid JSON only."
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
                    current_prompt = f"Error: {e}. Please generate a valid workflow JSON."
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
                        raw_response=last_raw_response,
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
                        raw_response=last_raw_response,
                    )

        # All retries exhausted
        total_time = (time.time() - generation_start) * 1000
        logger.error(f"Max retries ({self.max_retries}) exceeded after {total_time:.2f}ms")

        return WorkflowGenerationResult(
            success=False,
            error=f"Max retries ({self.max_retries}) exceeded",
            attempts=self.max_retries,
            validation_history=validation_history,
            generation_time_ms=total_time,
            attempt_history=attempt_history,
            raw_response=last_raw_response,
        )

    def _merge_workflows(
        self,
        existing: dict[str, Any],
        new: dict[str, Any],
    ) -> dict[str, Any]:
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

        logger.debug(f"Merged: +{new_nodes_added} nodes, +{new_connections_added} connections")

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
        self._page_context_cache.clear()
        logger.debug("Agent caches cleared")

    async def generate_with_conversation(
        self,
        user_prompt: str,
        conversation_manager: ConversationManager,
        detected_intent: UserIntent | None = None,
        model: str | None = None,
        temperature: float | None = None,
    ) -> WorkflowGenerationResult:
        """
        Generate workflow with multi-turn conversation context.

        Uses conversation history and current workflow state to provide
        context-aware generation for iterative workflow refinement.

        Args:
            user_prompt: Current user message
            conversation_manager: Manager with conversation history
            detected_intent: Pre-classified intent (optional)
            model: LLM model to use
            temperature: Sampling temperature

        Returns:
            WorkflowGenerationResult with generated/modified workflow
        """
        from casare_rpa.infrastructure.ai.conversation_manager import UserIntent

        generation_start = time.time()

        # Validate input
        if not user_prompt or not user_prompt.strip():
            logger.warning("Empty user prompt provided")
            return WorkflowGenerationResult(
                success=False,
                error="User prompt cannot be empty",
            )

        # Handle special intents that don't require LLM
        if detected_intent == UserIntent.UNDO:
            workflow = conversation_manager.undo_workflow()
            if workflow:
                return WorkflowGenerationResult(
                    success=True,
                    workflow=workflow,
                    attempts=0,
                    generation_time_ms=(time.time() - generation_start) * 1000,
                )
            return WorkflowGenerationResult(
                success=False,
                error="Nothing to undo",
            )

        if detected_intent == UserIntent.REDO:
            workflow = conversation_manager.redo_workflow()
            if workflow:
                return WorkflowGenerationResult(
                    success=True,
                    workflow=workflow,
                    attempts=0,
                    generation_time_ms=(time.time() - generation_start) * 1000,
                )
            return WorkflowGenerationResult(
                success=False,
                error="Nothing to redo",
            )

        if detected_intent == UserIntent.CLEAR:
            conversation_manager.clear_all()
            return WorkflowGenerationResult(
                success=True,
                workflow=None,
                attempts=0,
                generation_time_ms=(time.time() - generation_start) * 1000,
            )

        # Build conversation context for LLM
        conversation_context = conversation_manager.build_modification_context()
        current_workflow = conversation_manager.current_workflow

        # Build workflow state string
        if current_workflow:
            workflow_state = json.dumps(current_workflow, indent=2)[:3000]
        else:
            workflow_state = "No workflow currently loaded."

        # Determine intent string
        intent_str = detected_intent.value if detected_intent else "unknown"

        # Build system prompt based on intent
        base_instructions = self._build_system_prompt()

        if detected_intent == UserIntent.REFINE and current_workflow:
            REFINE_SYSTEM_PROMPT.format(
                current_workflow=json.dumps(current_workflow, indent=2)[:4000],
                base_instructions=base_instructions,
            )
        else:
            MULTI_TURN_SYSTEM_PROMPT.format(
                conversation_context=conversation_context,
                workflow_state=workflow_state,
                detected_intent=intent_str,
                base_instructions=base_instructions,
            )

        # Determine mode based on intent
        is_modify = detected_intent in (
            UserIntent.MODIFY_WORKFLOW,
            UserIntent.ADD_NODE,
            UserIntent.REMOVE_NODE,
            UserIntent.REFINE,
        )

        logger.info(
            f"Multi-turn generation: intent={intent_str}, "
            f"has_workflow={current_workflow is not None}, "
            f"conversation_messages={conversation_manager.message_count}"
        )

        # Generate using standard flow
        result = await self.generate_workflow(
            user_prompt=user_prompt,
            existing_workflow=current_workflow if is_modify else None,
            canvas_state={"nodes": current_workflow.get("nodes", {})} if current_workflow else None,
            is_edit=is_modify,
            model=model,
            temperature=temperature,
        )

        # Update conversation manager with result
        if result.success and result.workflow:
            description = f"After: {user_prompt[:50]}..."
            conversation_manager.set_workflow(result.workflow, description)

        return result

    def _build_conversation_messages(
        self,
        conversation_manager: ConversationManager,
        system_prompt: str,
        user_prompt: str,
    ) -> list[dict[str, str]]:
        """
        Build message list for LLM with conversation context.

        Args:
            conversation_manager: Manager with conversation history
            system_prompt: System prompt to use
            user_prompt: Current user message

        Returns:
            List of message dicts for LLM API
        """
        messages = [{"role": "system", "content": system_prompt}]

        # Add conversation history
        context_messages = conversation_manager.build_llm_context(
            include_workflow=False,  # Already in system prompt
            max_workflow_chars=2000,
        )
        messages.extend(context_messages)

        # Add current user message
        messages.append({"role": "user", "content": user_prompt})

        return messages


async def generate_smart_workflow(
    prompt: str,
    existing_workflow: dict[str, Any] | None = None,
    max_retries: int = 3,
    model: str = "gpt-4o-mini",
    config: AgentConfig | None = None,
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
