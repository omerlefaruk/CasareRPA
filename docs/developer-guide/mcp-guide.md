# MCP Guide

Guide for using Model Context Protocol (MCP) servers in CasareRPA.

## Overview

MCP (Model Context Protocol) servers provide specialized capabilities to AI agents. CasareRPA uses an **MCP-first standard**, meaning agents should prioritize MCP servers over other tools when available.

## MCP Server Priority

Always use MCP servers in this order:

| Priority | Server | Purpose | When to Use |
|----------|--------|---------|-------------|
| 1 | `codebase` | Semantic code search | Unknown concepts, finding patterns |
| 2 | `sequential-thinking` | Multi-step reasoning | Complex analysis, planning |
| 3 | `filesystem` | File read/write | Any file operation |
| 4 | `git` | Repository inspection | Git history, diffs, branches |
| 5 | `exa` | Web search | External research, docs |
| 6 | `ref` | Library docs | API lookups |

## Available MCP Servers

### Core MCP Servers

These servers are essential for all agent operations:

#### `filesystem`
- **Purpose**: File reads, writes, and directory operations
- **Tools**: `read_file`, `write`, `list`, `glob`, `edit`
- **Status**: ✓ Working

**Usage:**
```python
# Read a file
read("src/casare_rpa/domain/entities/base_node.py")

# Write a file
write(content="...", filePath="src/new_file.py")

# List directory
list(path="src/casare_rpa/")
```

#### `git`
- **Purpose**: Repository inspection and version control
- **Tools**: `git status`, `git diff`, `git log`, `git branch`
- **Status**: ✓ Working

**Usage:**
```bash
# Check git status
git status

# Show recent commits
git log --oneline -5

# Show unstaged changes
git diff
```

### Semantic Search MCP

#### `codebase`
- **Purpose**: Semantic code search using ChromaDB
- **Tools**: `search_codebase`
- **Status**: ✗ Not available (requires MCP config)
- **Command**: `python scripts/chroma_search_mcp.py`

**Usage:**
```python
# Semantic search
search_codebase("browser automation click", top_k=5)

# Returns relevant code snippets with context
```

**Setup:**
```bash
# Index the codebase first
python scripts/index_codebase.py

# Start the MCP server
python scripts/chroma_search_mcp.py
```

### Reasoning MCP

#### `sequential-thinking`
- **Purpose**: Complex reasoning and multi-step planning
- **Tools**: `sequential-thinking`
- **Status**: ✗ Not available (requires MCP config)

**Usage:**
```python
sequential_thinking(
    problem="Design a scalable RPA architecture",
    steps=[
        "Analyze requirements",
        "Identify patterns",
        "Propose solution"
    ]
)
```

### External Context MCP

#### `exa`
- **Purpose**: Web search and external research
- **Status**: Optional (when configured)
- **Docs**: https://exa.ai/docs

**Usage:**
```python
exa_search(
    query="latest PySide6 performance best practices",
    num_results=5
)
```

#### `ref`
- **Purpose**: API/library documentation lookup
- **Status**: Optional (when configured)
- **Docs**: https://ref.dev/docs

**Usage:**
```python
ref_search(
    query="PySide6 QTimer async",
    source="pyside6"
)
```

#### `playwright`
- **Purpose**: Browser automation investigations
- **Status**: Optional (when configured)
- **Docs**: https://playwright.dev/python/docs

**Usage:**
```python
playwright_screenshot(
    url="https://example.com",
    selector=".login-form"
)
```

## MCP Configuration

### Configuration File

MCP servers are configured in `.mcp.json`:

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "uvx",
      "args": ["mcp-server-filesystem", "/path/to/project"]
    },
    "git": {
      "command": "uvx",
      "args": ["mcp-server-git"]
    },
    "codebase": {
      "command": "python",
      "args": ["scripts/chroma_search_mcp.py"]
    },
    "sequential-thinking": {
      "command": "uvx",
      "args": ["mcp-server-sequential-thinking"]
    }
  }
}
```

### Environment Variables

Some MCP servers require environment variables:

```bash
# ChromaDB path for codebase server
export CHROMA_DB_PATH=".chroma/"

# Exa API key for web search
export EXA_API_KEY="your-api-key"
```

## MCP-First Best Practices

### 1. Use Semantic Search First

When searching for code patterns, use `codebase` (semantic) before `grep` (exact):

```python
# Good: Semantic search first
search_codebase("how to implement browser click", top_k=5)

# Then exact search if needed
rg "def click" src/

# Bad: Skip semantic search
rg "click" src/  # Too broad, misses patterns
```

### 2. Use Reasoning for Complex Tasks

For multi-step analysis, use `sequential-thinking`:

```python
# Good: Reasoning for complex tasks
sequential_thinking(
    problem="Analyze the node execution flow",
    steps=[
        "Trace the execution path",
        "Identify bottlenecks",
        "Propose optimizations"
    ]
)

# Bad: Skip reasoning
# Jumping directly to implementation
```

### 3. Use Git for History Context

Before making changes, check git history:

```bash
# Good: Check history first
git log --oneline -10 --all -- src/casare_rpa/domain/

# Bad: Skip history
# Making changes without context
```

### 4. Parallel MCP Operations

Launch independent MCP operations in parallel:

```python
# Good: Parallel reads
read("src/casare_rpa/domain/entities/base_node.py")
read("src/casare_rpa/domain/events/base_events.py")
git_diff = git("diff HEAD~1")

# Bad: Sequential operations
base = read("src/casare_rpa/domain/entities/base_node.py")
events = read("src/casare_rpa/domain/events/base_events.py")  # Waits for base
```

## Troubleshooting

### Server Not Available

If an MCP server shows "Not available":

1. **Check configuration**: Verify `.mcp.json` is valid
2. **Install dependencies**: Run `pip install -e ".[dev]"`
3. **Start server**: Run `python scripts/chroma_search_mcp.py`
4. **Restart agent**: Reload the agent context

### Slow Responses

Semantic search may be slow on first query:

- **First query**: ~800ms (cold start)
- **Follow-up queries**: <100ms (cached)

### Empty Results

If search returns no results:

- **Index the codebase**: Run `python scripts/index_codebase.py`
- **Check ChromaDB path**: Verify `.chroma/` directory exists
- **Re-index**: Delete `.chroma/` and run index again

## Integration with Agents

All CasareRPA agents are designed to use MCP-first:

```python
# Example: Explorer agent using MCP
Task(
    subagent_type="explorer",
    description="Find browser automation patterns",
    prompt="""
    Use MCP-first approach:
    1. First, search_codebase("browser automation patterns")
    2. Then, explore the relevant files
    3. Report findings with file paths
    """
)
```

## See Also

- [Agent Guide](agent-guide.md) - Agent and skill usage
- [Development Guide](../index.md) - Project development
- [Architecture](../architecture/index.md) - System architecture
- [.mcp.json Config](https://github.com/anthropics/mcp-server)
