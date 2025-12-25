"""Optimize .mcp.json to disable unused servers.

Reduces token usage by loading only essential MCP servers.
"""

import json
from pathlib import Path


def optimize_mcp_json(source_path: Path, keep_servers: list[str], backup: bool = True) -> None:
    """Optimize .mcp.json to keep only specified servers.

    Args:
        source_path: Path to .mcp.json
        keep_servers: List of server names to keep.
        backup: Create backup before modifying.
    """
    if backup:
        backup_path = source_path.parent / f"{source_path.name}.backup"
        backup_path.write_text(source_path.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"Created backup: {backup_path}")

    with open(source_path, encoding="utf-8") as f:
        config = json.load(f)

    if "mcpServers" not in config:
        print("No mcpServers section found")
        return

    servers = config["mcpServers"]

    active_servers = {name: server for name, server in servers.items() if name in keep_servers}

    config["mcpServers"] = active_servers

    with open(source_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

    print("Optimized .mcp.json")
    print(f"  Original: {len(servers)} servers")
    print(f"  Kept: {len(active_servers)} servers")
    print(f"  Removed: {len(servers) - len(active_servers)} servers")


def create_minimal_mcp_json(source_path: Path) -> Path:
    """Create minimal .mcp.json with only essential servers.

    Keeps:
    - codebase: Local code search
    - filesystem: File operations
    - playwright: Browser automation

    Args:
        source_path: Path to .mcp.json

    Returns:
        Path to minimal file.
    """
    minimal_config = {
        "mcpServers": {
            "codebase": {"command": "python", "args": ["scripts/chroma_search_mcp.py"], "env": {}},
            "filesystem": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem", "."],
            },
            "playwright": {"command": "npx", "args": ["-y", "@playwright/mcp@latest"]},
        }
    }

    minimal_path = source_path.parent / ".mcp.minimal.json"
    with open(minimal_path, "w", encoding="utf-8") as f:
        json.dump(minimal_config, f, indent=2)

    return minimal_path


if __name__ == "__main__":
    import sys

    mcp_json = Path(".mcp.json")

    if "--minimal" in sys.argv:
        create_minimal_mcp_json(mcp_json)
        print("Created .mcp.minimal.json")
    elif "--essential" in sys.argv:
        optimize_mcp_json(mcp_json, keep_servers=["codebase", "filesystem", "playwright"])
    else:
        print("Usage:")
        print("  python scripts/optimize_mcp.py --minimal    # Create minimal config")
        print("  python scripts/optimize_mcp.py --essential # Keep only essential servers")
