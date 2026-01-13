"""
MCP tools for serving CasareRPA rules on-demand.

Tools:
- get_rules: Retrieve rules by category, task type, and urgency
- list_rules: Discover available rules
"""

import asyncio
from pathlib import Path
from typing import Literal

from fastmcp import Context

from ..resources.metadata import (
    RULE_CATALOG,
    TRIGGER_KEYWORDS,
    detect_context,
    get_rules_for_category,
)

# Base path for rule files
RULES_BASE_PATH = Path(__file__).parent.parent.parent.parent.parent.parent / ".claude" / "rules_mcp"


def _read_rule_file(file_path: str) -> str:
    """Read a rule file from the rules_mcp directory.

    Args:
        file_path: Relative path within rules_mcp/

    Returns:
        File contents as string
    """
    full_path = RULES_BASE_PATH / file_path
    if full_path.exists():
        return full_path.read_text(encoding="utf-8")
    return f"<error>Rule file not found: {file_path}</error>"


def _format_rules_response(
    category: str,
    rule_files: list[str],
    include_refs: bool = False
) -> str:
    """Format rules response with optional references.

    Args:
        category: Rule category
        rule_files: List of rule file paths
        include_refs: Whether to include reference links

    Returns:
        Formatted XML rules string
    """
    lines = [f'<rules category="{category}">']

    for file_path in rule_files:
        content = _read_rule_file(file_path)
        lines.append(content)

    if include_refs:
        lines.append("<references>")
        lines.append('  <ref path="docs/agent/_index.md">Full agent documentation</ref>')
        lines.append('  <ref path=".brain/decisions/">Decision trees</ref>')
        lines.append('  <ref path=".claude/skills/">Project skills</ref>')
        lines.append("</references>")

    lines.append("</rules>")
    return "\n".join(lines)


async def get_rules(
    category: str = "core",
    task_type: str | None = None,
    urgency: Literal["critical", "normal", "optional"] = "normal",
    user_prompt: str | None = None,
    ctx: Context | None = None,
) -> str:
    """Get CasareRPA rules for current context.

    Use this tool at the START of any task to get relevant rules.
    Rules are served in XML format for 30-40% token savings.

    Args:
        category: Rule category (core, workflow, nodes, ui, testing, http, database, events)
        task_type: Type of task (create, fix, refactor, test) - optional filtering
        urgency: Return depth
            - "critical": Non-negotiable rules only (~300 tokens)
            - "normal": Standard rules for the category (~800 tokens)
            - "optional": Full rules with references (~2000 tokens)
        user_prompt: Your current task description for auto-detection (optional)
        ctx: FastMCP context for logging

    Returns:
        XML-formatted rules for the requested category

    Examples:
        # Get core non-negotiables
        get_rules(category="core", urgency="critical")

        # Auto-detect category from task
        get_rules(user_prompt="Implement a new browser automation node")

        # Get full workflow rules
        get_rules(category="workflow", urgency="optional")
    """
    if ctx:
        await ctx.info(f"Fetching rules: category={category}, urgency={urgency}")

    # Auto-detect category if user_prompt provided
    if user_prompt:
        detected_category, _ = detect_context(user_prompt)
        if detected_category != "core":
            category = detected_category
            if ctx:
                await ctx.info(f"Auto-detected category: {category}")

    # Get rule files for category
    rule_files = get_rules_for_category(category, urgency)

    # Include refs for optional urgency
    include_refs = urgency == "optional"

    return _format_rules_response(category, rule_files, include_refs)


async def list_rules(
    category: str | None = None,
    ctx: Context | None = None,
) -> str:
    """List available CasareRPA rules.

    Use this to discover what rules exist before requesting them.

    Args:
        category: Filter by category (omit for all)
        ctx: FastMCP context for logging

    Returns:
        Formatted list of available rules

    Examples:
        # List all rules
        list_rules()

        # List workflow rules only
        list_rules(category="workflow")
    """
    if ctx:
        await ctx.info(f"Listing rules: category={category or 'all'}")

    lines = ["<rules_catalog>"]

    for rule_id, meta in RULE_CATALOG.items():
        if category and meta["category"] != category:
            continue

        lines.append(f'  <rule id="{rule_id}">')
        lines.append(f'    <category>{meta["category"]}</category>')
        lines.append(f'    <priority>{meta["priority"]}</priority>')
        lines.append(f'    <tokens>{meta["tokens"]}</tokens>')
        lines.append(f'    <file>{meta["file"]}</file>')
        lines.append("  </rule>")

    lines.append("</rules_catalog>")
    lines.append("")
    lines.append("<!-- Usage: get_rules(category='<category>', urgency='<priority>') -->")

    return "\n".join(lines)
