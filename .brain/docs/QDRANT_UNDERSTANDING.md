# Understanding Qdrant: Complete Overview

This document provides a complete understanding of how Qdrant semantic search is integrated into CasareRPA for agent use.

## Quick Start

### For Agents (Using Qdrant)

```
qdrant-find: "what you're looking for as natural language"
```

Example:
```
qdrant-find: "browser automation click element"
qdrant-find: "error handling retry pattern"
qdrant-find: "event bus domain pattern"
```

**Gets back:** Code chunks with metadata, ranked by semantic similarity.

### For Developers (Maintaining Qdrant)

```bash
# Update index after code changes
python scripts/index_codebase_qdrant.py

# Verify index health
python -c "from qdrant_client import QdrantClient; c = QdrantClient(path='.qdrant'); print(c.count('casare_codebase').count)"
```

## What Qdrant Does

### Problem It Solves

**Without Qdrant:**
- Grep: `"BrowserClickNode"` → Only finds literal text match
- Agents have to guess exact class names
- No way to ask "what's the pattern for browser automation?"

**With Qdrant:**
- `qdrant-find: "browser automation click"` → Finds BrowserClickNode + related classes
- Agents can ask conceptual questions
- Semantic understanding of code

### How It Works (High Level)

1. **Index Creation:** Convert code → semantic vectors
2. **Storage:** Store vectors + metadata in Qdrant
3. **Search:** Convert query → vector → find similar code
4. **Return:** Send matching code chunks back to agent

## Architecture Overview

### Three Main Components

```
┌──────────────────────────────────────────────────────┐
│ Agent (Claude Code)                                  │
│ Asks: qdrant-find: "search query"                   │
└─────────────────────┬────────────────────────────────┘
                      │
┌─────────────────────▼────────────────────────────────┐
│ MCP Server (mcp-server-qdrant)                       │
│ Configures: .mcp.json environment variables          │
│ Exposes: search_qdrant, store_qdrant tools          │
└─────────────────────┬────────────────────────────────┘
                      │
┌─────────────────────▼────────────────────────────────┐
│ Qdrant Database                                      │
│ Location: .qdrant/ directory (local storage)        │
│ Collection: casare_codebase (2000+ chunks)          │
│ Index: COSINE distance on 384-dim vectors           │
└──────────────────────────────────────────────────────┘
```

## Key Files

| File | Purpose | When to Use |
|------|---------|-----------|
| `scripts/index_codebase_qdrant.py` | Creates/updates index | After code changes |
| `.mcp.json` | Configures MCP server | Setup, troubleshooting |
| `.qdrant/` | Database storage | Never edit directly |
| `CLAUDE.md` | Search strategy guide | Quick reference |
| `QDRANT_MCP_ARCHITECTURE.md` | Complete technical details | Deep dive |
| `.brain/docs/qdrant-quick-reference.md` | Agent usage guide | Writing agent prompts |
| `.brain/docs/qdrant-debugging.md` | Troubleshooting guide | Fixing issues |

## The Indexing Process

### What Gets Indexed

From `src/` directory:
- Classes (with first 50 lines)
- Functions (with first 30 lines)
- Module docstrings
- All metadata (layer, category, decorators, base classes)

### Metadata Extracted

```python
{
    "type": "class",              # class|function|module|file
    "name": "BrowserClickNode",
    "path": "src/casare_rpa/nodes/browser.py",
    "layer": "nodes",             # domain|application|infrastructure|presentation|nodes
    "category": "browser",        # browser|desktop|events|visual_nodes|canvas|ui|tests
    "base_classes": ["BrowserBaseNode"],
    "decorators": ["@node"],
    "is_node": True,              # Automation node?
    "has_ai_hint": False,         # Contains AI-HINT comment?
    "line_start": 120,
    "line_end": 165
}
```

### How Metadata Helps

- **layer:** Find code in specific DDD layer
- **category:** Find related node types
- **is_node:** Filter for automation vs utility
- **has_ai_hint:** Find documented patterns
- **base_classes:** Find implementations of same base

### Vector Embedding

Text composition before embedding:
```
"{type} {name} | in {path} | layer: {layer} | category: {category} | {content[:500]}"

Example:
"class BrowserClickNode | in src/casare_rpa/nodes/browser.py | layer: nodes | category: browser | extends: BrowserBaseNode | decorators: @node | class BrowserClickNode(...) ..."
```

Model used: `sentence-transformers/all-MiniLM-L6-v2`
- Output: 384-dimensional vector
- Captures semantic meaning of code
- Enables similarity search

## MCP Server Setup

### Configuration (.mcp.json)

```json
{
  "mcpServers": {
    "qdrant": {
      "command": "mcp-server-qdrant.exe",
      "env": {
        "QDRANT_LOCAL_PATH": "C:/Users/Rau/Desktop/CasareRPA/.qdrant",
        "COLLECTION_NAME": "casare_codebase",
        "EMBEDDING_MODEL": "sentence-transformers/all-MiniLM-L6-v2"
      }
    }
  }
}
```

### What MCP Server Does

1. Reads environment variables from `.mcp.json`
2. Connects to Qdrant at `QDRANT_LOCAL_PATH`
3. Loads embedding model: `EMBEDDING_MODEL`
4. Exposes tools to agent:
   - `search_qdrant(query, limit=10, collection_name)`
   - `store_qdrant(content, metadata, collection_name)`

### Transport Protocol

- **Transport:** stdio (standard input/output)
- **Communication:** Agent ↔ MCP Server ↔ Qdrant
- **All requests go through MCP for security**

## Search Flow

### Step-by-Step

```
Agent writes: qdrant-find: "browser automation click"
              ↓
MCP server receives query
              ↓
Embedding provider:
  - Load sentence-transformers/all-MiniLM-L6-v2
  - Embed query → 384-dim vector
              ↓
Qdrant searches:
  - Collection: casare_codebase
  - Vector space: fast-all-minilm-l6-v2
  - Distance metric: COSINE
  - Returns: Top-K similar points
              ↓
MCP server formats:
  - Extract content + metadata from points
  - Return as List[Entry]
              ↓
Agent receives:
  - Code chunks ranked by similarity
  - Full metadata for each chunk
  - Line numbers for further reading
```

### Time Breakdown

- Embedding query: 100-200ms (first time), 50ms (cached)
- Qdrant search: 300-400ms
- Network roundtrip: 100ms
- **Total: ~500ms typical**

## Search Quality

### What Affects Results

1. **Query specificity:** More specific = better results
2. **Domain terminology:** Use real domain terms
3. **Semantic relationships:** Similar concepts cluster together
4. **Index freshness:** Outdated index = stale results

### Good vs Bad Queries

**Good:**
- "browser automation click pattern" (specific, domain terms)
- "async error recovery mechanism" (conceptual, clear intent)
- "event publishing workflow orchestration" (descriptive)

**Bad:**
- "click" (too generic, use grep)
- "BrowserClickNode" (use grep for exact names)
- "line 123" (use read for specific lines)

## Important: Vector Name Matching

### Critical Constraint

The indexer and MCP server MUST use the same embedding model and vector naming.

**Indexer:**
```python
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
VECTOR_NAME = "fast-all-minilm-l6-v2"  # fastembed naming convention
```

**MCP Server:**
```json
"EMBEDDING_MODEL": "sentence-transformers/all-MiniLM-L6-v2"
```

### What Happens If They Differ

- Indexer creates: `vector={"fast-all-minilm-l6-v2": [...]}`
- Server queries: `using="different-name"`
- Result: Collection appears empty (no matching vector)

### How to Verify

```bash
# Check indexer
grep "VECTOR_NAME" scripts/index_codebase_qdrant.py
# Should output: VECTOR_NAME = "fast-all-minilm-l6-v2"

# Check server config
cat .mcp.json | grep -i embedding
# Should show: "sentence-transformers/all-MiniLM-L6-v2"
```

## Data Organization

### DDD Layers Indexed

| Layer | Path | What's There |
|-------|------|-------------|
| Domain | `src/casare_rpa/domain/` | Core entities, events, types |
| Application | `src/casare_rpa/application/` | Use cases, services |
| Infrastructure | `src/casare_rpa/infrastructure/` | External adapters, resources |
| Presentation | `src/casare_rpa/presentation/` | UI, controllers, visual nodes |
| Nodes | `src/casare_rpa/nodes/` | Automation node implementations |

### Search by Layer

Agent can search conceptually:
```
qdrant-find: "domain layer event pattern"
# Returns: Events, aggregates from domain/

qdrant-find: "infrastructure HTTP client pattern"
# Returns: HTTP adapter implementations

qdrant-find: "browser node implementation"
# Returns: Browser node classes from nodes/
```

## Maintenance

### When to Re-Index

- **After significant changes:** >50 new/modified files
- **After file moves:** Renaming/reorganizing code
- **After major refactors:** Large structural changes
- **Quarterly:** Just to keep index fresh

### How to Re-Index

```bash
# 1. Delete old index (optional but recommended)
rm -r .qdrant/

# 2. Run indexer
python scripts/index_codebase_qdrant.py

# 3. Restart Claude Code
# (To reload MCP server with new index)
```

### Indexing Time

- Typical: 40-60 seconds
- Scales linearly with code size
- No impact on system during indexing

## Troubleshooting Guide

### Quick Checklist

- [ ] `.qdrant/` directory exists
- [ ] `.qdrant/collections/casare_codebase/` has data
- [ ] `.mcp.json` configuration looks correct
- [ ] Embedding model installed: `pip list | grep sentence-transformers`
- [ ] MCP server runs without errors: `mcp-server-qdrant`
- [ ] Test search returns results

### Common Issues

**"No results found"**
1. Try broader query terms
2. Verify index exists: `ls .qdrant/`
3. Re-index: `python scripts/index_codebase_qdrant.py`

**"Collection appears empty"**
1. Check vector name matches (see above)
2. Re-index: `python scripts/index_codebase_qdrant.py`
3. Restart Claude Code

**"Search very slow (>5s)"**
1. Normal for first query (embedding model load)
2. Subsequent queries should be <1s
3. Check system resources

**"MCP server crashes"**
1. Check `.qdrant/` directory corruption
2. Delete and re-index: `rm -r .qdrant/ && python scripts/index_codebase_qdrant.py`
3. Verify `.mcp.json` syntax

## Performance Characteristics

### Index Statistics

- **Size:** ~50-100 MB
- **Points:** ~2000-3000 code chunks
- **Vector size:** 384 dimensions
- **Distance metric:** COSINE

### Query Performance

- **Embedding:** 100-200ms (first), 50ms (cached)
- **Search:** 300-400ms
- **Total:** ~500ms typical

### Memory Usage

- **Qdrant instance:** ~200-300 MB
- **Embedding model:** ~500 MB (loaded once)
- **Total:** ~700-800 MB

## Decision Tree: When to Use What

```
Need to find code?
│
├─ Know exact class/function name?
│  └─ Use Grep (faster, precise)
│     Example: Grep: "class BrowserClickNode"
│
├─ Know file path?
│  └─ Use Read (direct access)
│     Example: Read: /path/to/file.py
│
├─ Exploring patterns/architecture?
│  └─ Use Qdrant (semantic search)
│     Example: qdrant-find: "browser automation"
│
└─ Understanding "how does X work?"
   └─ Use Qdrant (conceptual search)
      Example: qdrant-find: "event bus pattern"
```

## Integration with Agents

### Where Agents Use Qdrant

1. **Explorer Agent:** Understand codebase layout
2. **Architect Agent:** Find design patterns
3. **Builder Agent:** Discover existing implementations
4. **Researcher Agent:** Find related concepts

### Agent Workflow Example

```
Task: "Implement Google Sheets node"

1. Explore existing patterns:
   qdrant-find: "Google Sheets API integration"

2. Understand node structure:
   qdrant-find: "node implementation pattern"

3. Check existing nodes:
   qdrant-find: "Google Drive nodes implementation"

4. Find base classes:
   Grep: "class.*Node.*:"

5. Read specific implementations:
   Read: /path/to/reference_node.py
```

## Files Quick Reference

| Need | File | Command |
|------|------|---------|
| Detailed architecture | `QDRANT_MCP_ARCHITECTURE.md` | Read this file |
| Agent quick start | `.brain/docs/qdrant-quick-reference.md` | Start here for usage |
| Debugging help | `.brain/docs/qdrant-debugging.md` | Troubleshoot issues |
| Index code | `scripts/index_codebase_qdrant.py` | `python scripts/index_codebase_qdrant.py` |
| Server config | `.mcp.json` | Check configuration |
| Search strategy | `CLAUDE.md` | Read "Search Strategy" section |

## Summary

- **Qdrant** = semantic vector database for code search
- **MCP** = protocol that exposes Qdrant to agents
- **Indexer** = `scripts/index_codebase_qdrant.py` creates vectors
- **Server** = `mcp-server-qdrant` serves search requests
- **Storage** = `.qdrant/` directory (local, ~50-100 MB)
- **Usage:** `qdrant-find: "natural language query"`
- **Performance:** ~500ms typical query time
- **Maintenance:** Re-index after significant code changes

## Next Steps

1. **For agents:** Read `.brain/docs/qdrant-quick-reference.md`
2. **For troubleshooting:** Check `.brain/docs/qdrant-debugging.md`
3. **For deep dive:** Read `QDRANT_MCP_ARCHITECTURE.md`
4. **For maintenance:** Run `python scripts/index_codebase_qdrant.py`
