# Qdrant Quick Reference for Agents

## What is Qdrant?

**Semantic code search** for CasareRPA. Instead of keyword matching (grep), Qdrant understands *meaning*.

```
Grep: "browser" → finds only string "browser"
Qdrant: "clicking elements in browser" → finds BrowserClickNode, BrowserTypeNode, etc.
```

## How to Use

### Basic Syntax

```
qdrant-find: "what you're looking for"
```

### Examples

**Exploring patterns:**
```
qdrant-find: "browser automation click pattern"
qdrant-find: "error handling retry mechanism"
qdrant-find: "event publishing workflow"
```

**Understanding concepts:**
```
qdrant-find: "how nodes are registered"
qdrant-find: "workflow execution flow"
qdrant-find: "async task completion"
```

**Finding implementations:**
```
qdrant-find: "Google Drive file listing"
qdrant-find: "WebSocket communication pattern"
qdrant-find: "credential validation"
```

## Search Tips

### Good Queries (Semantic)
- Natural language: "browser automation click element"
- Conceptual: "error recovery pattern"
- Domain terms: "node registration decorator"
- Descriptive: "async workflow with retry logic"

### Bad Queries (Use Grep Instead)
- Class names: "BrowserClickNode" → Use `Grep: "class BrowserClickNode"`
- Exact symbols: "get_event_bus" → Use `Grep: "def get_event_bus"`
- Line numbers: "line 123" → Use `Read: file_path` with offset

## Decision Flow

```
Need to find something?
│
├─ Know the exact class/function name?
│  └─ Use Grep (faster)
│
├─ Know the file path?
│  └─ Use Read (direct)
│
└─ Don't know what to look for?
   └─ Use qdrant-find (semantic search)
```

## What You Get Back

### Response Format

Qdrant returns code chunks with metadata:

```python
[
    {
        "content": "class BrowserClickNode(BrowserBaseNode):\n  ...",
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

### Interpreting Results

- **Top results** = highest semantic similarity
- **metadata.path** = file location for Read/Grep
- **metadata.line_start** = start line for focused reading
- **metadata.is_node** = True if automation node (vs utility)

## Search Layers

Qdrant indexes all DDD layers:

| Layer | What's Indexed | Use for |
|-------|----------------|---------|
| **domain/** | Entities, events, types | Understanding core concepts |
| **application/** | Use cases, services | Finding business logic |
| **infrastructure/** | Adapters, resources | Finding external integrations |
| **presentation/** | UI, controllers | Finding UI patterns |
| **nodes/** | Automation nodes | Finding node implementations |

## Examples in Context

### Scenario 1: "Add browser automation node"

```
1. Explore pattern:
   qdrant-find: "browser node implementation pattern"

2. Understand event flow:
   qdrant-find: "node execution events completion"

3. Find base class:
   Grep: "class BrowserBaseNode"

4. Read implementation:
   Read: /path/to/browser_base.py
```

### Scenario 2: "Debug workflow execution"

```
1. Find execution flow:
   qdrant-find: "workflow execution orchestration"

2. Understand event bus:
   qdrant-find: "event bus domain pattern"

3. Find event definitions:
   Grep: "class WorkflowCompleted"

4. Check implementation:
   Read: src/casare_rpa/domain/events/__init__.py
```

### Scenario 3: "Add credential handling"

```
1. Find credential pattern:
   qdrant-find: "credential validation encryption"

2. Find existing implementation:
   qdrant-find: "OAuth credential storage"

3. Check Vault integration:
   Grep: "VaultManager"

4. Read implementation:
   Read: infrastructure/security/vault.py
```

## Metadata Filters (Advanced)

Results are sorted by similarity, but metadata helps interpretation:

```
Looking for:
- Core logic → Search for metadata.layer = "domain"
- Node implementations → Search for metadata.is_node = True
- Recent code → Check metadata.has_ai_hint = True
- Exported APIs → Use metadata.exported = True
```

## Performance

- **Query time**: ~500ms (from agent docs)
- **Typical results**: 5-10 relevant chunks
- **Result order**: By semantic similarity

## Limitations

- ❌ Cannot search by exact line number
- ❌ Cannot filter by git history
- ❌ Results are snippets, not full files
- ✓ Use `Read` tool after qdrant-find for full context

## When Index is Updated

Qdrant index is updated when:
1. You run: `python scripts/index_codebase_qdrant.py`
2. Agents restart (to load new MCP server)

**After significant code changes, re-index:**
```bash
python scripts/index_codebase_qdrant.py
```

## Troubleshooting

### "No results found"

1. Try broader query: "browser automation" instead of "click XPath selector"
2. Try semantic synonyms: "press button" instead of "click element"
3. Use Grep if you know exact name: `Grep: "ClassName"`

### "Results are irrelevant"

1. Make query more specific with domain terms
2. Include layer: "domain layer event handling"
3. Use Grep for exact matches

### "Search seems slow"

- Normal: 500ms is expected
- Check: Is MCP server running? (from `.mcp.json`)
- Try: Restart Claude Code to reload MCP server

## Files Reference

| What | File | When |
|------|------|------|
| How to use Qdrant | `QDRANT_MCP_ARCHITECTURE.md` | Deep dive |
| Search strategy | `CLAUDE.md` section "Search Strategy" | Quick reference |
| Indexing code | `scripts/index_codebase_qdrant.py` | Maintenance |
| MCP config | `.mcp.json` | Setup |
| Agent rules | `.claude/rules/01-core.md` | Workflows |

## Quick Commands

```bash
# Re-index after code changes
python scripts/index_codebase_qdrant.py

# Check if .qdrant directory exists
ls -la .qdrant/

# Force MCP reload (restart Claude Code)
```

## Summary

- **qdrant-find** = semantic search for understanding code
- **Grep** = exact symbol search for refactoring
- **Read** = get full file content after qdrant-find
- Re-index regularly for best results
