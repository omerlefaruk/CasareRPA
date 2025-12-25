#!/usr/bin/env python3
"""
MCP Server Test Script for CasareRPA
Tests all configured MCP servers and reports status.
"""

import json
import os
import subprocess
import sys
from pathlib import Path


def print_header(title: str) -> None:
    """Print a section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def print_status(name: str, status: str, details: str = "") -> None:
    """Print a status line."""
    icons = {"OK": "[OK]", "FAIL": "[FAIL]", "WARN": "[WARN]", "INFO": "[INFO]"}
    icon = icons.get(status, "[?]")
    print(f"  {icon} {name}: {status}")
    if details:
        print(f"     {details}")


def test_codebase_server() -> tuple[str, str]:
    """Test the codebase MCP server (ChromaDB semantic search)."""
    # Check if ChromaDB files exist
    chroma_dir = Path(".chroma")
    db_file = chroma_dir / "chroma.sqlite3"

    if not chroma_dir.exists():
        return "FAIL", "ChromaDB directory (.chroma) not found"
    if not db_file.exists():
        return "FAIL", "ChromaDB database not found"

    # Check if index exists
    cache_file = chroma_dir / "index_cache.json"
    if cache_file.exists():
        with open(cache_file) as f:
            cache = json.load(f)
            doc_count = cache.get("total_documents", 0)
            return "OK", f"Indexed {doc_count} documents"

    return "WARN", "ChromaDB exists but may need re-indexing"


def test_filesystem_mcp() -> tuple[str, str]:
    """Test filesystem MCP availability."""
    # Check if filesystem MCP is configured
    mcp_config = Path(".mcp.json")
    if not mcp_config.exists():
        return "FAIL", ".mcp.json not found"

    try:
        with open(mcp_config) as f:
            config = json.load(f)
            if "filesystem" in config.get("mcpServers", {}):
                return "OK", "Filesystem MCP configured in .mcp.json"
    except json.JSONDecodeError:
        pass

    return "WARN", "Filesystem MCP may need configuration"


def test_git_mcp() -> tuple[str, str]:
    """Test git MCP availability."""
    # Verify git is working
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", "-1"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            commit = result.stdout.strip()
            return "OK", f"Working: {commit[:50]}"
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return "WARN", "Git MCP may need configuration"


def test_sequential_thinking() -> tuple[str, str]:
    """Test sequential-thinking MCP availability."""
    mcp_config = Path(".mcp.json")
    if mcp_config.exists():
        try:
            with open(mcp_config) as f:
                config = json.load(f)
                if "sequential-thinking" in config.get("mcpServers", {}):
                    return "OK", "Sequential-thinking MCP configured in .mcp.json"
        except json.JSONDecodeError:
            pass

    return "WARN", "Sequential-thinking MCP may need configuration"


def test_exa_server() -> tuple[str, str]:
    """Test Exa web search MCP."""
    mcp_config = Path(".mcp.json")
    if mcp_config.exists():
        try:
            with open(mcp_config) as f:
                config = json.load(f)
                exa_config = config.get("mcpServers", {}).get("exa", {})
                env = exa_config.get("env", {})
                if "EXA_API_KEY" in env:
                    return "OK", "Exa MCP configured with API key"
        except json.JSONDecodeError:
            pass

    return "WARN", "Exa MCP may need API key configuration"


def test_ref_server() -> tuple[str, str]:
    """Test ref/documentation MCP."""
    mcp_config = Path(".mcp.json")
    if mcp_config.exists():
        try:
            with open(mcp_config) as f:
                config = json.load(f)
                if "ref" in config.get("mcpServers", {}) or "context7" in config.get(
                    "mcpServers", {}
                ):
                    return "OK", "Ref/Context7 MCP configured"
        except json.JSONDecodeError:
            pass

    return "WARN", "Ref MCP may need configuration"


def test_opencode_config() -> tuple[str, str]:
    """Test OpenCode MCP configuration."""
    opencode_config = Path(".opencode/mcp_config.json")
    if not opencode_config.exists():
        return "FAIL", ".opencode/mcp_config.json not found"

    try:
        with open(opencode_config) as f:
            config = json.load(f)
            patterns = config.get("usage_patterns", {})

            checks = []
            for pattern, servers in patterns.items():
                checks.append(f"{pattern}: {', '.join(servers)}")

            return "OK", " | ".join(checks)
    except json.JSONDecodeError:
        return "FAIL", "Invalid JSON in .opencode/mcp_config.json"


def print_mcp_startup_guide() -> None:
    """Print guide for starting MCP servers."""
    print("\n" + "=" * 60)
    print("  MCP Server Startup Guide")
    print("=" * 60)

    servers = [
        ("codebase", "python scripts/chroma_search_mcp.py", "Semantic code search"),
        ("filesystem", "npx -y @modelcontextprotocol/server-filesystem .", "File operations"),
        ("git", "npx -y @modelcontextprotocol/server-git", "Git operations"),
        (
            "sequential-thinking",
            "npx -y @modelcontextprotocol/server-sequential-thinking",
            "Reasoning",
        ),
        ("exa", "npx -y exa-mcp-server", "Web search"),
        ("ref", "npx -y @upstash/context7-mcp", "Documentation lookup"),
    ]

    for name, cmd, desc in servers:
        print(f"\n  [{name.upper()}]")
        print(f"     Command: {cmd}")
        print(f"     Purpose: {desc}")


def main() -> int:
    """Main test function."""
    print("\n" + "=" * 60)
    print("  CasareRPA MCP Server Test")
    print("=" * 60)

    # Test each server
    print_header("MCP Server Status")

    tests = [
        ("OpenCode Config", test_opencode_config),
        ("Codebase (ChromaDB)", test_codebase_server),
        ("Filesystem", test_filesystem_mcp),
        ("Git", test_git_mcp),
        ("Sequential-Thinking", test_sequential_thinking),
        ("Exa (Web Search)", test_exa_server),
        ("Ref (Documentation)", test_ref_server),
    ]

    results = []
    for name, test_func in tests:
        status, details = test_func()
        print_status(name, status, details)
        results.append((name, status, details))

    # Summary
    print_header("Summary")
    ok_count = sum(1 for _, s, _ in results if s == "OK")
    warn_count = sum(1 for _, s, _ in results if s == "WARN")
    fail_count = sum(1 for _, s, _ in results if s == "FAIL")

    print(f"  [OK]: {ok_count}")
    print(f"  [WARN]: {warn_count}")
    print(f"  [FAIL]: {fail_count}")

    # Print startup guide
    print_mcp_startup_guide()

    print("\n" + "=" * 60)
    print("  Test Complete")
    print("=" * 60 + "\n")

    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
