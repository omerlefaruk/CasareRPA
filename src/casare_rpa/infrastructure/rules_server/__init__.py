"""
CasareRPA Rules MCP Server

Serves project rules on-demand using progressive disclosure.
Reduces startup tokens by loading rules based on task context.

Example:
    get_rules(category="core", urgency="critical")
    get_rules(category="workflow", task_type="implement")
"""

from .server import mcp

__all__ = ["mcp"]
