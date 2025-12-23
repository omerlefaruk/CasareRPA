<<<<<<< HEAD
=======
# Archived Analysis (Non-Normative)

This file is archived analysis. Do not treat as current rules. See .agent/, .claude/, and .brain/_index.md for active guidance.

---

>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e
# Qdrant MCP Architecture & Integration

## Overview

The CasareRPA codebase uses **Qdrant** (a vector database) with **Model Context Protocol (MCP)** to enable semantic code search across agents. This document explains the complete architecture, data flow, and how agents access `qdrant-find`.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     Claude Code (Agent)                          │
│                                                                   │
│  Uses: qdrant-find: "browser automation pattern"               │
└─────────────────────┬───────────────────────────────────────────┘
                      │ MCP Request
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│           MCP Server (mcp-server-qdrant)                         │
│                                                                   │
│  Entry Point: mcp_server_qdrant.main:main()                     │
│  Transport: stdio (default)                                      │
│  Tools Exposed: search_qdrant, store_qdrant                     │
└─────────────────────┬───────────────────────────────────────────┘
                      │ Vector operations
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│           QdrantConnector (mcp_server_qdrant.qdrant)             │
│                                                                   │
│  Methods:                                                         │
│  - search(query, limit=10, collection_name)                     │
│  - store(content, metadata, collection_name)                    │
│  - get_collection_names()                                        │
└─────────────────────┬───────────────────────────────────────────┘
                      │ Vector embedding & search
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│     Embedding Provider (fastembed + sentence-transformers)       │
│                                                                   │
│  Model: sentence-transformers/all-MiniLM-L6-v2                  │
│  Vector Name: fast-all-minilm-l6-v2 (matching indexer)          │
│  Vector Size: 384-dimensional                                    │
└─────────────────────┬───────────────────────────────────────────┘
                      │ Load vectors & metadata
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│              Qdrant Vector Database (Local)                       │
│                                                                   │
│  Storage: .qdrant/ directory                                     │
│  Collection: casare_codebase                                     │
│  Points: ~2000+ code chunks with metadata                       │
│  Index Type: COSINE distance                                     │
└─────────────────────────────────────────────────────────────────┘
```

## Component Breakdown

### 1. Indexing Pipeline

**Script:** `c:\Users\Rau\Desktop\CasareRPA\scripts\index_codebase_qdrant.py`

#### Workflow:
1. **Collect Python files** from `src/` directory
   - Walk entire source tree
   - Exclude: `__pycache__`, `.git`, `__init__.py`
   - Include: All `*.py` files

2. **Extract code chunks** using AST parsing
   - Module docstrings
   - Class definitions (first 50 lines)
   - Functions (first 30 lines)
   - Skip private methods (except `__init__`, `_define_ports`, `__call__`)

3. **Extract rich metadata** for each chunk:
   ```python
   {
       "type": "class|function|module|file",
       "name": "ClassName",
       "path": "src/casare_rpa/domain/entities/base_node.py",
       "layer": "domain|application|infrastructure|presentation|nodes",
       "category": "browser|desktop|events|visual_nodes|canvas|ui|tests",
       "base_classes": ["BaseNode", "BrowserBaseNode"],
       "decorators": ["@node", "@properties"],
       "is_node": true,
       "is_async": true,
       "has_ai_hint": true,  # Contains AI-HINT/AI-WARNING comment
       "exported": true,     # Not starting with _
       "line_start": 42,
       "line_end": 75
   }
   ```

4. **Generate embeddings** (batch processing):
   - Text composition: `"{type} {name} | in {path} | layer: {layer} | category: {category} | {content[:500]}"`
   - Model: `sentence-transformers/all-MiniLM-L6-v2` (via fastembed)
   - Output: 384-dimensional vectors

5. **Upsert to Qdrant** in batches (100 items):
   - Create points with named vector: `fast-all-minilm-l6-v2`
   - Store payload with rich metadata
   - Collection: `casare_codebase`

#### Key Configuration:
```python
QDRANT_PATH = ".qdrant"
COLLECTION_NAME = "casare_codebase"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
VECTOR_NAME = "fast-all-minilm-l6-v2"  # MUST match MCP server
```

### 2. MCP Server Configuration

**File:** `c:\Users\Rau\Desktop\CasareRPA\.mcp.json`

```json
{
  "mcpServers": {
    "qdrant": {
      "command": "C:\\Users\\Rau\\AppData\\Local\\Programs\\Python\\Python313\\Scripts\\mcp-server-qdrant.exe",
      "args": [],
      "env": {
        "QDRANT_LOCAL_PATH": "C:/Users/Rau/Desktop/CasareRPA/.qdrant",
        "COLLECTION_NAME": "casare_codebase",
        "EMBEDDING_MODEL": "sentence-transformers/all-MiniLM-L6-v2"
      }
    }
  }
}
```

#### Environment Variables:
- `QDRANT_LOCAL_PATH`: Path to `.qdrant/` directory (local storage)
- `COLLECTION_NAME`: Default collection to search in
- `EMBEDDING_MODEL`: Model for query embedding (must match indexer)

### 3. MCP Server Implementation

**Entry Point:** `mcp_server_qdrant.main:main()`

**Process:**
```python
def main():
    parser = argparse.ArgumentParser(description="mcp-server-qdrant")
    parser.add_argument("--transport", choices=["stdio", "sse", "streamable-http"], default="stdio")
    args = parser.parse_args()
    from mcp_server_qdrant.server import mcp
    mcp.run(transport=args.transport)
```

**Transport:** `stdio` (standard input/output - used for agent communication)

**Exposed Tools:**
- `search_qdrant(query: str, collection_name?: str, limit?: int)` → List[Entry]
- `store_qdrant(content: str, metadata?: dict, collection_name?: str)` → void

### 4. Qdrant Connector

**File:** `mcp_server_qdrant.qdrant:QdrantConnector`

#### Key Methods:

**search(query, limit=10, collection_name=None, query_filter=None)**
```python
# Workflow:
1. Embed query using embedding provider
2. Query Qdrant collection with vector
3. Return top K results with metadata
4. Return List[Entry] with content + metadata
```

**store(entry, collection_name=None)**
```python
# Workflow:
1. Embed entry.content
2. Create PointStruct with:
   - id: UUID
   - vector: {vector_name: embedding}
   - payload: {document: content, metadata: {...}}
3. Upsert to collection
```

### 5. Storage Structure

**Directory:** `c:\Users\Rau\Desktop\CasareRPA\.qdrant/`

```
.qdrant/
├── collections/
│   └── casare_codebase/
│       ├── 0/              # Shard 0
│       │   ├── *.bnx       # Binary vector indexes
│       │   ├── *.pnx       # Payload indexes
│       │   └── ...
│       └── snapshots/
└── config.json             # Qdrant configuration
```

**Collection Schema:**
```python
{
    "name": "casare_codebase",
    "vectors_config": {
        "fast-all-minilm-l6-v2": {
            "size": 384,
            "distance": "cosine"
        }
    }
}
```

**Point Structure:**
```python
PointStruct(
    id=<int>,
    vector={"fast-all-minilm-l6-v2": [0.123, -0.456, ...]},
    payload={
        "document": "class MyNode\n\n...",  # Full code chunk
        "type": "class",
        "name": "MyNode",
        "path": "src/casare_rpa/nodes/browser.py",
        "line_start": 42,
        "line_end": 75,
        "layer": "nodes",
        "category": "browser",
        "base_classes": ["BrowserBaseNode"],
        "decorators": ["@node"],
        "is_node": True,
        "has_ai_hint": False,
        "exported": True
    }
)
```

## How Agents Use Qdrant

### Agent-Side Invocation

Agents (Claude Code) access semantic search through MCP:

```python
# Agent makes MCP request
qdrant-find: "browser automation click element"

# Equivalent to MCP call:
search_qdrant(
    query="browser automation click element",
    collection_name="casare_codebase",
    limit=8  # Default limit
)
```

### Response Format

```python
# MCP returns List[Entry]
[
    Entry(
        content="class BrowserClickNode(BrowserBaseNode):\n\n...",
        metadata={
            "type": "class",
            "name": "BrowserClickNode",
            "path": "src/casare_rpa/nodes/browser.py",
            "layer": "nodes",
            "category": "browser",
            "line_start": 120,
            "line_end": 165,
            "is_node": True,
            "has_ai_hint": False
        }
    ),
    Entry(...),
    ...
]
```

### Search Process

1. **Agent → MCP Server:**
   - Sends natural language query: `"browser automation click element"`

2. **MCP Server → Embedding Provider:**
   - Embeds query: `all-MiniLM-L6-v2([query])` → 384-dim vector

3. **Embedding Provider → Qdrant:**
   - Calls `query_points(vector, using="fast-all-minilm-l6-v2", limit=10)`

4. **Qdrant Search:**
   - Computes COSINE distance from query vector to all point vectors
   - Returns top-K points by similarity score
   - Filters if `query_filter` provided

5. **MCP Server → Agent:**
   - Returns List[Entry] with full document + metadata

## Indexing Workflow

### How to Update the Index

```bash
# From CasareRPA root directory:
python scripts/index_codebase_qdrant.py
```

**Process:**
1. Loads embedding model (first run: ~1 GB download)
2. Walks `src/` directory and extracts chunks (5-10 seconds)
3. Generates embeddings for all chunks (~20 seconds)
4. Deletes old `casare_codebase` collection
5. Creates new collection with fresh index
6. Upserts points in batches (5 seconds)

**Output:**
```
Indexing CasareRPA codebase into Qdrant
  Source: src/
  Qdrant path: .qdrant
  Collection: casare_codebase

Loading embedding model...
  Embedding dimension: 384

Initializing Qdrant...
  Deleting existing collection: casare_codebase
  Creating collection: casare_codebase
  Vector name: fast-all-minilm-l6-v2

Extracting code chunks...
  Processing: src/casare_rpa/domain/...
  ...

Found 2156 chunks from 287 files

Generating embeddings and upserting...
  Upserted 100/2156 points
  Upserted 200/2156 points
  ...

Indexing complete!
  Total points: 2156
  Collection: casare_codebase

Restart Claude Code to load the new MCP server.
```

### When to Re-Index

- After significant code changes (new nodes, major refactors)
- After moving/renaming files
- After adding new features
- Before intensive development sessions

**CLAUDE.md Recommendation:**
```bash
python scripts/index_codebase_qdrant.py    # Re-index for semantic search
```

## Matching Embedding Models

**CRITICAL:** The indexer and MCP server must use the SAME embedding model.

### Consistency Check

**Indexer:** `scripts/index_codebase_qdrant.py`
```python
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
VECTOR_NAME = "fast-all-minilm-l6-v2"
```

**MCP Server:** `.mcp.json`
```json
"env": {
  "EMBEDDING_MODEL": "sentence-transformers/all-MiniLM-L6-v2"
}
```

**FastEmbed Naming:** `mcp_server_qdrant.embeddings.fastembed`
- Model: `sentence-transformers/all-MiniLM-L6-v2`
- Vector Name: `fast-all-minilm-l6-v2` (fastembed naming convention)

### If Vector Names Mismatch:
- Indexer creates: `vector={"fast-all-minilm-l6-v2": [...]}`
- Server queries: `using="different-name"`
- Result: Collection appears empty (no matching vector)

## Search Quality Optimization

### How Search Results are Ranked

1. **Semantic Similarity:** COSINE distance between query and chunk vectors
   - 1.0 = identical (same direction)
   - 0.0 = orthogonal (perpendicular)
   - -1.0 = opposite

2. **Metadata Filtering:** Optional filters on payload fields
   ```python
   # Example: Only find "browser" category nodes
   query_filter=models.Filter(
       must=[
           models.FieldCondition(
               key="category",
               match=models.MatchValue(value="browser")
           )
       ]
   )
   ```

### Query Composition Tips

**Good queries (semantic-friendly):**
```
"browser automation click element"
"error handling retry pattern"
"workflow execution context"
"async task completion notification"
```

**Less effective:**
```
"click"                          # Too general
"BrowserClickNode"               # Use Grep instead
"node.py line 123"               # Use Read instead
```

### Metadata-Aware Queries

Queries can benefit from metadata awareness:

```
"browser node extends BrowserBaseNode with click action"
# Finds: Base class + action matches

"async function with AI-HINT for workflow execution"
# Finds: AI-annotated async functions
```

## Data Flow Example

### Request: Find Browser Automation Pattern

```
Agent Query: "browser automation click element"
              ↓
Embed Query: sentence-transformers/all-MiniLM-L6-v2(query)
            → [0.23, -0.45, 0.12, ..., 0.78] (384-dim)
              ↓
Qdrant Search:
  - Query vector: above
  - Collection: casare_codebase
  - Vector space: fast-all-minilm-l6-v2
  - Distance metric: COSINE
  - Limit: 10
              ↓
Search Results (ranked by similarity):
  1. BrowserClickNode (similarity: 0.92)
  2. BrowserHoverNode (similarity: 0.88)
  3. BrowserTypeNode (similarity: 0.85)
  4. BrowserBaseNode (similarity: 0.82)
  5. ...
              ↓
Return to Agent:
  - Full class definitions
  - Metadata (line numbers, decorators, etc.)
  - Similarity scores (if available)
```

## Performance Characteristics

### Indexing Time (Full Rebuild)
- ~40-60 seconds total
- Scales linearly with number of chunks
- 2000+ chunks typical for CasareRPA

### Query Time
- ~500ms typical (from agent docs)
- Embedding: ~100ms
- Qdrant search: ~300-400ms
- Network: ~100ms (stdio communication)

### Memory Usage
- Qdrant instance: ~200-300 MB
- Embedding model: ~500 MB (loaded once)
- Total: ~700-800 MB

### Storage Usage
- `.qdrant/` directory: ~50-100 MB
- Vectors: ~80% of space
- Metadata: ~20% of space

## Troubleshooting

### Issue: "Collection appears empty"

**Cause:** Vector name mismatch

**Check:**
```bash
# Verify indexer vector name
grep "VECTOR_NAME =" scripts/index_codebase_qdrant.py
# Expected: VECTOR_NAME = "fast-all-minilm-l6-v2"

# Verify MCP server embedding model
grep "EMBEDDING_MODEL" .mcp.json
# Expected: "sentence-transformers/all-MiniLM-L6-v2"
```

**Fix:** Re-run indexer, then restart MCP server

### Issue: "Query returns irrelevant results"

**Cause:** Query too vague or metadata mismatch

**Solution:**
- Make query more specific: `"browser click node implementation"`
- Use domain-specific terms: `"selector xpath click"`
- Include layer context: `"domain layer event bus pattern"`

### Issue: "MCP server crashes"

**Cause:** Missing .qdrant directory or corrupted collection

**Fix:**
```bash
# Delete old index
rm -r .qdrant/

# Re-run indexer
python scripts/index_codebase_qdrant.py

# Restart Claude Code
```

## Integration Points

### Where Agents Access Qdrant

1. **Explorer Agent** (`agent-rules/agents/explore.md`)
   - Uses qdrant-find for codebase exploration
   - Understands architecture before making changes

2. **Architect Agent** (`agent-rules/agents/architect.md`)
   - Searches for design patterns
   - Finds similar implementations

3. **Researcher Agent** (`agent-rules/agents/researcher.md`)
   - Semantic search for related concepts
   - Pattern discovery

4. **Builder Agent** (via CLAUDE.md)
   - Quick pattern lookup
   - Existing implementation discovery

### Agent Rules Reference

From `.claude/rules/01-core.md`:
```
1. **INDEX-FIRST**: Read `_index.md` before grep/glob
2. **SEARCH BEFORE CREATE**: Check existing code before writing new
3. Parallel launches in ONE message block
```

From `CLAUDE.md`:
```
## Search Strategy (Qdrant vs Grep)

| Use Case | Tool |
|----------|------|
| Explore patterns/architecture | **qdrant-find** |
| Understand how X works | **qdrant-find** |
| Find exact symbol/string | **Grep** |
| Find specific class/function | **Grep** |
```

## Files Reference Summary

| Component | File Path |
|-----------|-----------|
| Indexer Script | `scripts/index_codebase_qdrant.py` |
| MCP Config | `.mcp.json` |
| MCP Launcher | `scripts/run-qdrant-mcp.cmd` |
| Qdrant Storage | `.qdrant/` |
| Agent Rules | `.claude/rules/01-core.md` |
| Search Docs | `CLAUDE.md` (Search Strategy section) |
| MCP Server Bin | `venv/Scripts/mcp-server-qdrant.exe` |

## Summary

**Qdrant MCP enables semantic search** across the CasareRPA codebase by:

1. **Indexing** Python files into semantic vectors (384-dim)
2. **Storing** chunks with rich metadata in Qdrant
3. **Exposing** search via MCP protocol to agents
4. **Returning** top-K semantically similar code chunks

**For agents:** Use `qdrant-find: "natural language query"` to search code semantically.

**For maintenance:** Run `python scripts/index_codebase_qdrant.py` after significant changes.

**Key insight:** Embedding model must match between indexer and MCP server for correct search results.
