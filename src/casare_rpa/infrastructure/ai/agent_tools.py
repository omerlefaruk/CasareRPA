"""
CasareRPA - Agent Tools Infrastructure

Defines the interface for tools that AI agents can use.
Tools map to actual node types for execution.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from loguru import logger

if TYPE_CHECKING:
    from casare_rpa.infrastructure.execution import ExecutionContext


@dataclass
class ParameterSpec:
    """Specification for a tool parameter."""

    name: str
    type: str  # "string", "number", "boolean", "object", "array"
    description: str
    required: bool = True
    default: Any | None = None
    enum: list[str] | None = None


@dataclass
class AgentTool:
    """
    Defines a tool that an AI agent can use.

    Each tool maps to either:
    - A CasareRPA node type (for workflow integration)
    - A Python callable (for built-in operations)
    """

    name: str
    description: str
    parameters: list[ParameterSpec] = field(default_factory=list)
    node_type: str | None = None  # Maps to CasareRPA node class name
    callable: Callable | None = None  # Direct Python callable
    category: str = "general"
    requires_confirmation: bool = False

    def to_function_schema(self) -> dict[str, Any]:
        """Convert to OpenAI function calling schema format."""
        properties = {}
        required = []

        for param in self.parameters:
            prop: dict[str, Any] = {
                "type": param.type,
                "description": param.description,
            }
            if param.enum:
                prop["enum"] = param.enum
            if param.default is not None:
                prop["default"] = param.default

            properties[param.name] = prop

            if param.required:
                required.append(param.name)

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }

    def to_prompt_description(self) -> str:
        """Convert to human-readable description for prompts."""
        params_desc = []
        for param in self.parameters:
            req_str = "(required)" if param.required else "(optional)"
            params_desc.append(f"  - {param.name} [{param.type}] {req_str}: {param.description}")

        params_str = "\n".join(params_desc) if params_desc else "  (no parameters)"

        return f"""Tool: {self.name}
Description: {self.description}
Parameters:
{params_str}"""


class AgentToolRegistry:
    """
    Registry for agent tools.

    Manages available tools and their execution.
    """

    def __init__(self) -> None:
        self._tools: dict[str, AgentTool] = {}
        self._categories: dict[str, list[str]] = {}

    def register(self, tool: AgentTool) -> None:
        """Register a tool."""
        self._tools[tool.name] = tool

        if tool.category not in self._categories:
            self._categories[tool.category] = []
        if tool.name not in self._categories[tool.category]:
            self._categories[tool.category].append(tool.name)

        logger.debug(f"Registered agent tool: {tool.name} ({tool.category})")

    def unregister(self, name: str) -> bool:
        """Unregister a tool by name."""
        if name in self._tools:
            tool = self._tools[name]
            if tool.category in self._categories:
                self._categories[tool.category] = [
                    t for t in self._categories[tool.category] if t != name
                ]
            del self._tools[name]
            return True
        return False

    def get(self, name: str) -> AgentTool | None:
        """Get a tool by name."""
        return self._tools.get(name)

    def list_tools(self, category: str | None = None) -> list[AgentTool]:
        """List all tools, optionally filtered by category."""
        if category:
            names = self._categories.get(category, [])
            return [self._tools[n] for n in names if n in self._tools]
        return list(self._tools.values())

    def list_categories(self) -> list[str]:
        """List all tool categories."""
        return list(self._categories.keys())

    def get_function_schemas(
        self,
        tool_names: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Get OpenAI function schemas for specified tools."""
        tools = []
        names = tool_names or list(self._tools.keys())

        for name in names:
            tool = self._tools.get(name)
            if tool:
                tools.append(tool.to_function_schema())

        return tools

    def get_prompt_descriptions(
        self,
        tool_names: list[str] | None = None,
    ) -> str:
        """Get human-readable descriptions for prompts."""
        descriptions = []
        names = tool_names or list(self._tools.keys())

        for name in names:
            tool = self._tools.get(name)
            if tool:
                descriptions.append(tool.to_prompt_description())

        return "\n\n".join(descriptions)

    async def execute_tool(
        self,
        name: str,
        parameters: dict[str, Any],
        context: ExecutionContext | None = None,
    ) -> dict[str, Any]:
        """
        Execute a tool by name with given parameters.

        Args:
            name: Tool name
            parameters: Tool parameters
            context: Optional execution context

        Returns:
            Tool execution result
        """
        tool = self._tools.get(name)
        if not tool:
            return {"success": False, "error": f"Unknown tool: {name}"}

        try:
            # Direct callable
            if tool.callable:
                if context:
                    result = await tool.callable(context=context, **parameters)
                else:
                    result = await tool.callable(**parameters)

                if isinstance(result, dict):
                    return result
                return {"success": True, "result": result}

            # Node-based execution
            if tool.node_type and context:
                return await self._execute_node_tool(tool, parameters, context)

            return {"success": False, "error": "Tool has no executable implementation"}

        except Exception as e:
            logger.error(f"Tool execution failed: {name} - {e}")
            return {"success": False, "error": str(e)}

    async def _execute_node_tool(
        self,
        tool: AgentTool,
        parameters: dict[str, Any],
        context: ExecutionContext,
    ) -> dict[str, Any]:
        """Execute a node-based tool."""
        try:
            from casare_rpa.nodes import _lazy_import
            from casare_rpa.utils.id_generator import generate_node_id

            # Import the node class
            node_class = _lazy_import(tool.node_type)

            # Create and configure node
            node_id = generate_node_id(tool.node_type)
            node = node_class(node_id=node_id, config=parameters)

            # Execute node
            result = await node.execute(context)

            return result

        except Exception as e:
            logger.error(f"Node tool execution failed: {tool.node_type} - {e}")
            return {"success": False, "error": str(e)}


# Default tool registry singleton
_default_registry: AgentToolRegistry | None = None


def get_default_tool_registry() -> AgentToolRegistry:
    """Get the default tool registry with built-in tools."""
    global _default_registry

    if _default_registry is None:
        _default_registry = AgentToolRegistry()
        _register_builtin_tools(_default_registry)

    return _default_registry


def _register_builtin_tools(registry: AgentToolRegistry) -> None:
    """Register built-in agent tools."""
    # Web Search Tool
    registry.register(
        AgentTool(
            name="web_search",
            description="Search the web for information",
            parameters=[
                ParameterSpec(
                    name="query",
                    type="string",
                    description="Search query",
                ),
                ParameterSpec(
                    name="max_results",
                    type="number",
                    description="Maximum number of results",
                    required=False,
                    default=5,
                ),
            ],
            node_type="HttpRequestNode",
            category="web",
        )
    )

    # Read File Tool
    registry.register(
        AgentTool(
            name="read_file",
            description="Read contents of a file",
            parameters=[
                ParameterSpec(
                    name="file_path",
                    type="string",
                    description="Path to the file to read",
                ),
                ParameterSpec(
                    name="encoding",
                    type="string",
                    description="File encoding",
                    required=False,
                    default="utf-8",
                ),
            ],
            node_type="ReadFileNode",
            category="file",
        )
    )

    # Write File Tool
    registry.register(
        AgentTool(
            name="write_file",
            description="Write contents to a file",
            parameters=[
                ParameterSpec(
                    name="file_path",
                    type="string",
                    description="Path to the file to write",
                ),
                ParameterSpec(
                    name="content",
                    type="string",
                    description="Content to write",
                ),
                ParameterSpec(
                    name="encoding",
                    type="string",
                    description="File encoding",
                    required=False,
                    default="utf-8",
                ),
            ],
            node_type="WriteFileNode",
            category="file",
        )
    )

    # HTTP Request Tool
    registry.register(
        AgentTool(
            name="http_request",
            description="Make an HTTP request to a URL",
            parameters=[
                ParameterSpec(
                    name="url",
                    type="string",
                    description="URL to request",
                ),
                ParameterSpec(
                    name="method",
                    type="string",
                    description="HTTP method",
                    required=False,
                    default="GET",
                    enum=["GET", "POST", "PUT", "DELETE", "PATCH"],
                ),
                ParameterSpec(
                    name="headers",
                    type="object",
                    description="HTTP headers",
                    required=False,
                ),
                ParameterSpec(
                    name="body",
                    type="string",
                    description="Request body",
                    required=False,
                ),
            ],
            node_type="HttpRequestNode",
            category="web",
        )
    )

    # Calculate Tool (built-in)
    async def calculate(expression: str, **kwargs: Any) -> dict[str, Any]:
        """Safely evaluate a mathematical expression."""
        try:
            # Only allow safe operations
            allowed_names = {
                "abs": abs,
                "round": round,
                "min": min,
                "max": max,
                "sum": sum,
                "len": len,
                "pow": pow,
                "int": int,
                "float": float,
            }
            result = eval(expression, {"__builtins__": {}}, allowed_names)
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    registry.register(
        AgentTool(
            name="calculate",
            description="Perform mathematical calculations",
            parameters=[
                ParameterSpec(
                    name="expression",
                    type="string",
                    description="Mathematical expression to evaluate (e.g., '2 + 2 * 3')",
                ),
            ],
            callable=calculate,
            category="utility",
        )
    )

    # JSON Parse Tool (built-in)
    async def parse_json(json_string: str, **kwargs: Any) -> dict[str, Any]:
        """Parse a JSON string."""
        import json

        try:
            result = json.loads(json_string)
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    registry.register(
        AgentTool(
            name="parse_json",
            description="Parse a JSON string into structured data",
            parameters=[
                ParameterSpec(
                    name="json_string",
                    type="string",
                    description="JSON string to parse",
                ),
            ],
            callable=parse_json,
            category="utility",
        )
    )

    # Think Tool (for chain-of-thought)
    async def think(thought: str, **kwargs: Any) -> dict[str, Any]:
        """Record a thought or reasoning step."""
        return {"success": True, "thought": thought}

    registry.register(
        AgentTool(
            name="think",
            description="Record a thought or reasoning step (for chain-of-thought)",
            parameters=[
                ParameterSpec(
                    name="thought",
                    type="string",
                    description="The thought or reasoning to record",
                ),
            ],
            callable=think,
            category="reasoning",
        )
    )

    # Finish Tool (to signal completion)
    async def finish(result: Any, summary: str = "", **kwargs: Any) -> dict[str, Any]:
        """Signal that the task is complete."""
        return {
            "success": True,
            "finished": True,
            "result": result,
            "summary": summary,
        }

    registry.register(
        AgentTool(
            name="finish",
            description="Signal that the task is complete and provide the final result",
            parameters=[
                ParameterSpec(
                    name="result",
                    type="string",
                    description="The final result or answer",
                ),
                ParameterSpec(
                    name="summary",
                    type="string",
                    description="Summary of what was accomplished",
                    required=False,
                ),
            ],
            callable=finish,
            category="control",
        )
    )


__all__ = [
    "ParameterSpec",
    "AgentTool",
    "AgentToolRegistry",
    "get_default_tool_registry",
]
