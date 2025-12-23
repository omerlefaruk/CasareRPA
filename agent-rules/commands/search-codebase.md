---
description: How to use the semantic codebase search
---

# Semantic Codebase Search Workflow

This workflow describes how to use the ChromaDB-based semantic search to find relevant code in the CasareRPA codebase.

## When to Use

Use semantic search when:
- Looking for implementation patterns (e.g., "how do browser nodes work")
- Finding classes/functions by *meaning*, not exact keywords
- Discovering how existing features are implemented
- Exploring unfamiliar parts of the codebase

## MCP Tool

The `codebase` MCP server exposes the `search_codebase` tool.

### Usage

```
search_codebase("browser automation click element", top_k=5)
```

**Arguments:**
- `query` (str): Natural language search query
- `top_k` (int): Number of results to return (default: 5)

### Response

Returns ranked results with:
- File path
- Code type (class, function, module)
- Name
- Relevance score
- Code snippet

## Performance

| Scenario | Latency |
|:---|:---|
| First query (cold start) | ~800ms |
| Subsequent queries (warm) | 4-150ms |
| Incremental index | ~3 seconds |
| Full re-index | ~2.5 minutes |

## Maintenance

### Re-index After Major Changes

```bash
python scripts/index_codebase.py
```

The indexer is **incremental** - it only processes files that have changed since the last run.

<<<<<<< HEAD
=======
### Start MCP Server Locally

```bash
python scripts/chroma_search_mcp.py
```

>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e
### Force Full Re-index

```bash
Remove-Item -Recurse -Force .chroma; python scripts/index_codebase.py
```

## Example Queries

| Query | Finds |
|:---|:---|
| "BaseNode implementation" | Core node base class |
| "HTTP POST request" | HTTP nodes and client |
| "browser automation click" | Browser click nodes |
| "workflow execution" | Execution controller |
| "how to create a node" | Node creation patterns |

## Related Files

- `scripts/index_codebase.py` - Indexing script
- `scripts/chroma_search_mcp.py` - MCP server
- `scripts/benchmark_search.py` - Performance testing
- `.chroma/` - Vector store data
- `.chroma/index_cache.json` - File hash cache
