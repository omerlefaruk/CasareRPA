# Archived Analysis (Non-Normative)

This file is archived analysis. Do not treat as current rules. See .agent/, .claude/, and .brain/_index.md for active guidance.

---
# Qdrant System Analysis & Integration Report

**Date:** 2025-12-14
**System:** CasareRPA Semantic Code Search
**Status:** Fully Configured and Operational

## Executive Summary

CasareRPA uses **Qdrant** (vector database) integrated with **MCP** (Model Context Protocol) to provide semantic code search for agents. This enables agents to ask conceptual questions like "browser automation pattern" instead of requiring exact class names.

### Key Facts

- **Indexing:** Automatic via `scripts/index_codebase_qdrant.py`
- **Storage:** Local `.qdrant/` directory (~50-100 MB)
- **Query Time:** ~500ms typical
- **Index Size:** 2000-3000 code chunks
- **Model:** sentence-transformers/all-MiniLM-L6-v2 (384-dim vectors)
- **Status:** Ready for agent use

## System Components

### 1. Indexing Pipeline

**Script:** `c:\Users\Rau\Desktop\CasareRPA\scripts\index_codebase_qdrant.py`

**Process:**
1. Walks `src/` directory for Python files
2. Extracts code chunks (classes, functions, docstrings)
3. Builds rich metadata (layer, category, decorators, base classes)
4. Generates embeddings using sentence-transformers model
5. Upserts to Qdrant in batches

**Output:** 2000+ indexed code chunks in `.qdrant/collections/casare_codebase/`

**When to Run:**
- After significant code changes (>50 files)
- After file reorganization
- Quarterly refresh
- Before intensive agent sessions

**Time:** ~40-60 seconds for full rebuild

### 2. MCP Server Configuration

**File:** `c:\Users\Rau\Desktop\CasareRPA\.mcp.json`

**Configuration:**
```json
{
  "mcpServers": {
    "qdrant": {
      "command": "C:\\Users\\Rau\\AppData\\Local\\Programs\\Python\\Python313\\Scripts\\mcp-server-qdrant.exe",
      "env": {
        "QDRANT_LOCAL_PATH": "C:/Users/Rau/Desktop/CasareRPA/.qdrant",
        "COLLECTION_NAME": "casare_codebase",
        "EMBEDDING_MODEL": "sentence-transformers/all-MiniLM-L6-v2"
      }
    }
  }
}
```

**Responsibilities:**
- Connects agent queries to Qdrant database
- Handles query embedding
- Returns ranked results
- Manages vector naming: `fast-all-minilm-l6-v2`

**Transport:** stdio (standard input/output)

### 3. Vector Database

**Location:** `c:\Users\Rau\Desktop\CasareRPA\.qdrant\`

**Collection:** `casare_codebase`

**Metrics:**
- Vector size: 384 dimensions
- Distance: COSINE
- Points: ~2000-3000 indexed chunks
- Disk size: 50-100 MB

**Point Structure:**
```python
{
    "id": <int>,
    "vector": {"fast-all-minilm-l6-v2": [...]},
    "payload": {
        "document": "<full code chunk>",
        "type": "class|function|module",
        "name": "<symbol name>",
        "path": "<file path>",
        "layer": "domain|application|infrastructure|presentation|nodes",
        "category": "browser|desktop|events|...",
        "base_classes": [...],
        "decorators": [...],
        "is_node": True/False,
        "has_ai_hint": True/False,
        "line_start": <int>,
        "line_end": <int>
    }
}
```

## How Agents Use It

### Query Syntax

```
qdrant-find: "natural language search query"
```

### Examples

```
qdrant-find: "browser automation click element"
→ Returns: BrowserClickNode, BrowserHoverNode, etc.

qdrant-find: "error handling retry pattern"
→ Returns: Retry logic, error handlers, recovery

qdrant-find: "event bus domain pattern"
→ Returns: EventBus, event publishing, subscriptions
```

### Response Format

Agent receives List of entries:
```python
[
    {
        "content": "<full code chunk>",
        "metadata": {
            "type": "class",
            "name": "BrowserClickNode",
            "path": "src/casare_rpa/nodes/browser.py",
            "layer": "nodes",
            "category": "browser",
            "is_node": True,
            "line_start": 120,
            "line_end": 165
        }
    },
    # More results...
]
```

## Performance Characteristics

### Query Performance

| Component | Time | Notes |
|-----------|------|-------|
| Embed query | 100-200ms | First run; 50ms cached |
| Qdrant search | 300-400ms | COSINE distance, K=10 |
| Network roundtrip | ~100ms | stdio communication |
| **Total** | **~500ms** | Typical end-to-end |

### System Resources

| Resource | Usage | Notes |
|----------|-------|-------|
| Disk space | ~50-100 MB | .qdrant/ directory |
| Memory (Qdrant) | 200-300 MB | Vector indexes |
| Memory (Model) | 500 MB | Embedding model (loaded once) |
| **Total** | **700-800 MB** | Typical system footprint |

### Scalability

- **Current index:** 2000-3000 chunks
- **Codebase:** ~280 files in src/
- **Growth:** Linear with file count
- **Sustainable:** Yes, up to 10k+ chunks

## Data Flow

```
Agent Request:
  qdrant-find: "browser automation"
       ↓
  [MCP Protocol - stdio]
       ↓
  MCP Server (.mcp.json configured)
  ├─ Load config: EMBEDDING_MODEL, COLLECTION_NAME
  ├─ Initialize embedding provider
  ├─ Embed query: "browser automation"
  │  → 384-dim vector
       ↓
  Qdrant Query
  ├─ Collection: casare_codebase
  ├─ Vector space: fast-all-minilm-l6-v2
  ├─ Query vector: [...]
  ├─ Metric: COSINE distance
  ├─ Limit: 10 results
       ↓
  Qdrant Results (ranked by similarity)
  ├─ BrowserClickNode (0.92)
  ├─ BrowserHoverNode (0.88)
  ├─ BrowserTypeNode (0.85)
       ↓
  MCP Server Response
  ├─ Extract content + payload
  ├─ Format as List[Entry]
       ↓
  [MCP Protocol - stdio]
       ↓
  Agent receives results
```

## Critical Constraints

### Vector Name Matching (CRITICAL)

The indexer and MCP server MUST use the same embedding model configuration.

**Current Configuration:**

Indexer (`scripts/index_codebase_qdrant.py`):
```python
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
VECTOR_NAME = "fast-all-minilm-l6-v2"  # fastembed naming
```

MCP Server (`.mcp.json`):
```json
"EMBEDDING_MODEL": "sentence-transformers/all-MiniLM-L6-v2"
```

**What Happens If Mismatch:**
- Collection appears empty
- No search results
- No errors (silent failure)
- Fix: Re-run indexer, restart MCP server

### What Not to Do

- ❌ Edit `.qdrant/` directory directly
- ❌ Change vector names without understanding
- ❌ Use different embedding models for index and server
- ❌ Try to manually update points without re-indexing
- ❌ Move `.qdrant/` to different location without updating `.mcp.json`

## Maintenance Procedures

### Regular Index Updates

```bash
# After significant code changes
python scripts/index_codebase_qdrant.py

# Then restart Claude Code (to reload MCP server)
```

**Decision:** When to update?

| Scenario | Action | Time |
|----------|--------|------|
| Added 1-5 files | Optional | ~1 min |
| Added 10+ files | Recommended | ~1 min |
| Major refactor | Required | ~1 min |
| File reorganization | Required | ~1 min |
| Monthly refresh | Optional | ~1 min |

### Health Check

```bash
# Verify index exists
ls .qdrant/collections/casare_codebase/

# Check point count
python -c "
from qdrant_client import QdrantClient
c = QdrantClient(path='.qdrant')
print(f'Total points: {c.count(\"casare_codebase\").count}')
"

# Expected: 2000+ points
```

### Recovery Procedure

If index becomes corrupted:

```bash
# 1. Delete old index
rm -r .qdrant/

# 2. Re-index (this creates fresh index)
python scripts/index_codebase_qdrant.py

# 3. Restart Claude Code
# (To reload MCP server with new index)
```

## Integration Points

### Where Qdrant is Used

1. **Explorer Agent** (`.claude/agents/explore.md`)
   - Explores codebase structure
   - Finds related patterns

2. **Architect Agent** (`.claude/agents/architect.md`)
   - Searches design patterns
   - Finds similar implementations

3. **Builder Agent** (via CLAUDE.md)
   - Discovers existing implementations
   - Avoids re-implementing functionality

4. **Researcher Agent** (`.claude/agents/researcher.md`)
   - Conceptual code search
   - Pattern discovery

### Agent Rules

From `CLAUDE.md` - "Search Strategy" section:

```
Search Strategy (Qdrant vs Grep)

| Use Case | Tool |
|----------|------|
| Explore patterns/architecture | **qdrant-find** |
| Understand how X works | **qdrant-find** |
| Find exact symbol/string | **Grep** |
| Find specific class/function | **Grep** |
```

## Search Quality Factors

### What Affects Results

1. **Query Specificity**
   - ✓ Good: "browser automation click pattern"
   - ✗ Bad: "click"

2. **Domain Terminology**
   - ✓ Good: "node registration decorator"
   - ✗ Bad: "how to add thing"

3. **Semantic Relationships**
   - ✓ Good: "event publishing workflow"
   - ✗ Bad: "BrowserClickNode" (use Grep)

### Query Tips

**Good queries:**
- Use domain-specific terms
- Be descriptive and specific
- Include context (layer, type)
- Use natural language

**Bad queries:**
- Too generic ("click")
- Exact class names ("BrowserClickNode")
- Line numbers/file paths
- Ambiguous requests

## Known Issues & Solutions

### Issue 1: "Collection appears empty"

**Cause:** Vector name mismatch between indexer and server

**Check:**
```bash
grep VECTOR_NAME scripts/index_codebase_qdrant.py
# Should show: VECTOR_NAME = "fast-all-minilm-l6-v2"
```

**Fix:**
- Re-run indexer: `python scripts/index_codebase_qdrant.py`
- Restart Claude Code

### Issue 2: "No results found"

**Cause:** Index missing or outdated

**Check:**
```bash
ls .qdrant/collections/casare_codebase/
# Should contain data
```

**Fix:**
- Re-index: `python scripts/index_codebase_qdrant.py`
- Try broader query terms
- Use Grep if searching for exact symbols

### Issue 3: "Search very slow (>5s)"

**Note:** This is normal
- First query: 1-2s (embedding model load)
- Subsequent queries: ~500ms

**If consistently >5s:**
- Check system resources
- Re-index if code changes were large
- Verify no background indexing running

### Issue 4: "MCP server crashes"

**Cause:** Corrupted `.qdrant/` directory

**Fix:**
```bash
rm -r .qdrant/
python scripts/index_codebase_qdrant.py
# Then restart Claude Code
```

## Technical Details Reference

For complete technical architecture, see:
- `QDRANT_MCP_ARCHITECTURE.md` - Full technical architecture
- `CLAUDE.md` - Search strategy guide
- `.brain/docs/QDRANT_UNDERSTANDING.md` - Overview and concepts
- `.brain/docs/qdrant-quick-reference.md` - Agent usage guide
- `.brain/docs/qdrant-debugging.md` - Troubleshooting guide

## Files Summary

| File | Purpose | Type |
|------|---------|------|
| `scripts/index_codebase_qdrant.py` | Indexing script | Python |
| `.mcp.json` | MCP server config | JSON |
| `.qdrant/` | Vector database | Data |
| `QDRANT_MCP_ARCHITECTURE.md` | Technical details | Docs |
| `.brain/docs/QDRANT_INDEX.md` | Documentation index | Docs |
| `.brain/docs/QDRANT_UNDERSTANDING.md` | Overview | Docs |
| `.brain/docs/qdrant-quick-reference.md` | Agent usage | Docs |
| `.brain/docs/qdrant-debugging.md` | Troubleshooting | Docs |
| `CLAUDE.md` | Search strategy | Docs |

## Recommended Next Steps

### For Agents
1. Read `.brain/docs/qdrant-quick-reference.md`
2. Try: `qdrant-find: "browser automation"`
3. Use results with Grep/Read for details

### For Developers
1. Run: `python scripts/index_codebase_qdrant.py`
2. Verify: Check `.qdrant/` directory exists
3. Test: Use simple query to verify functionality

### For Troubleshooting
1. Check: `.brain/docs/qdrant-debugging.md`
2. Run: Health check script (see debugging docs)
3. Fix: Follow specific issue resolution

## Conclusion

**Qdrant is fully configured and operational** in CasareRPA. The system provides:

- ✓ Semantic code search for agents
- ✓ Local vector database (~50-100 MB)
- ✓ Fast queries (~500ms typical)
- ✓ Easy maintenance (one script)
- ✓ Rich metadata support

**Agents can now:**
- Ask conceptual questions: `qdrant-find: "what you're looking for"`
- Get back ranked code chunks
- Use results for exploration and implementation

**Regular maintenance:**
- Run indexer after significant changes
- Typical indexing time: 40-60 seconds
- Zero maintenance downtime

---

**System Status:** Operational
**Last Updated:** 2025-12-14
**Maintenance:** Monthly or as needed
