"""
CasareRPA Rules MCP Server

FastMCP server for serving project rules on-demand.
Reduces startup tokens by ~60-70% through progressive disclosure.
"""

from fastmcp import FastMCP

from .tools.get_rules import get_rules, list_rules

mcp = FastMCP(
    name="casare-rpa-rules",
    instructions="CasareRPA project rules served on-demand. Use get_rules() to retrieve rules by category and context.",
)

# Register tools
mcp.add_tool(get_rules)
mcp.add_tool(list_rules)

if __name__ == "__main__":
    mcp.run()
