# Qdrant Documentation Index

Complete documentation for understanding and using Qdrant semantic search in CasareRPA.

## Quick Navigation

### I'm an Agent - How do I use Qdrant?
**Start here:** `.brain/docs/qdrant-quick-reference.md`

Quick syntax: `qdrant-find: "natural language query"`

Key points:
- Use for semantic/conceptual searches
- Get back code chunks with metadata
- Use Grep for exact symbol matches instead

### I Need to Debug Qdrant
**Start here:** `.brain/docs/qdrant-debugging.md`

Common issues:
- "Collection appears empty" → Vector name mismatch
- "No results found" → Index missing, re-index
- "Search very slow" → Normal (500ms), first query slower
- "MCP server crashes" → Delete .qdrant/ and rebuild

### I Want to Understand How It Works
**Start here:** `.brain/docs/QDRANT_UNDERSTANDING.md`

Complete overview covering:
- What Qdrant does and why
- Architecture overview
- How indexing works
- How search works
- Maintenance procedures

### I Need Technical Architecture Details
**Start here:** `QDRANT_MCP_ARCHITECTURE.md` (root directory)

Deep dive covering:
- Complete system architecture with diagrams
- Indexing pipeline details
- MCP server implementation
- Qdrant connector methods
- Storage structure and schemas
- Data flow examples
- Performance characteristics
- Troubleshooting guide

## Document Organization

### For Different Audiences

#### Agents (Using Qdrant)
1. `.brain/docs/qdrant-quick-reference.md` (5 min read)
   - How to write queries
   - What you get back
   - Search tips and tricks
   - Examples

2. `.brain/docs/QDRANT_UNDERSTANDING.md` → "When to use what" section
   - Decision tree for choosing tools

#### Developers (Maintaining Qdrant)
1. `.brain/docs/QDRANT_UNDERSTANDING.md` (15 min read)
   - Overview and architecture
   - Maintenance procedures
   - When to re-index

2. `.brain/docs/qdrant-debugging.md` (when needed)
   - Health checks
   - Verification procedures
   - Direct Python testing
   - Re-index procedures

#### Architects (System Design)
1. `QDRANT_MCP_ARCHITECTURE.md` (30+ min read)
   - Complete architecture with diagrams
   - Component breakdown
   - Integration points
   - Performance characteristics

### By Task

| Task | Document | Section |
|------|----------|---------|
| Write semantic search query | qdrant-quick-reference.md | "How to Use" + "Examples" |
| Debug search issues | qdrant-debugging.md | Issue-specific section |
| Understand overall system | QDRANT_UNDERSTANDING.md | Full document |
| Deep technical dive | QDRANT_MCP_ARCHITECTURE.md | Full document |
| Learn when to re-index | QDRANT_UNDERSTANDING.md | "Maintenance" |
| Fix empty results | qdrant-debugging.md | "Vector Name Mismatch" |
| Optimize query performance | QDRANT_UNDERSTANDING.md | "Search Quality" section |

## File Structure

```
CasareRPA/
├── scripts/
│   └── index_codebase_qdrant.py          # Indexing script
│
├── .mcp.json                              # MCP server config
├── .qdrant/                               # Database directory
│   └── collections/
│       └── casare_codebase/               # Main collection
│
├── QDRANT_MCP_ARCHITECTURE.md             # Technical details
│
├── .brain/
│   └── docs/
│       ├── QDRANT_INDEX.md               # This file
│       ├── QDRANT_UNDERSTANDING.md       # Overview
│       ├── qdrant-quick-reference.md     # Agent usage
│       └── qdrant-debugging.md           # Troubleshooting
│
└── CLAUDE.md                              # Search strategy guide
```

## Core Concepts

### Three Components

1. **Indexer:** `scripts/index_codebase_qdrant.py`
   - Extracts code chunks from `src/`
   - Generates semantic vectors (384-dim)
   - Stores in Qdrant

2. **MCP Server:** `mcp-server-qdrant` (configured in `.mcp.json`)
   - Connects agent to Qdrant
   - Handles query embedding
   - Returns search results

3. **Qdrant Database:** `.qdrant/` directory
   - Local vector database
   - Stores 2000+ code chunks
   - COSINE distance metric

### Key Terms

| Term | Meaning |
|------|---------|
| Vector | 384-dimensional number representing semantic meaning |
| Embedding | Process of converting text to vector |
| Semantic similarity | How "similar in meaning" two pieces of code are |
| Collection | Named group of vectors (here: `casare_codebase`) |
| Point | Single entry in Qdrant (vector + metadata + content) |
| Payload | Metadata stored with each point |
| COSINE distance | How search similarity is calculated (0.0-1.0) |

## Command Reference

### Running Indexer
```bash
python scripts/index_codebase_qdrant.py
```

### Checking Index Health
```python
python -c "
from qdrant_client import QdrantClient
c = QdrantClient(path='.qdrant')
print(f'Total points: {c.count(\"casare_codebase\").count}')
"
```

### Testing MCP Server
```cmd
# Windows
set QDRANT_LOCAL_PATH=C:/Users/Rau/Desktop/CasareRPA/.qdrant
set COLLECTION_NAME=casare_codebase
set EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
mcp-server-qdrant
```

### Agent Usage
```
qdrant-find: "search query in natural language"
```

## Common Questions Answered

### Q: When should I re-index?
**A:** After significant code changes (>50 files), file moves, or major refactors. Normal: quarterly or as needed.

### Q: Why is search slow?
**A:** Normal (~500ms). First query slower (embedding model load). If >5s, check system resources.

### Q: Why are results irrelevant?
**A:** Try more specific queries with domain terms. If still bad, re-index with latest code.

### Q: Can I search by exact filename?
**A:** No, use Grep instead. Qdrant is for semantic/conceptual search.

### Q: How big is the index?
**A:** ~50-100 MB (vectors + metadata). ~700 MB total memory usage.

### Q: What if the index gets corrupted?
**A:** Delete `.qdrant/` and re-run `python scripts/index_codebase_qdrant.py`.

### Q: How do I verify the index works?
**A:** See `.brain/docs/qdrant-debugging.md` → "Health Check" section.

## Integration with Development Workflow

### Normal Development
```
1. Write code
2. Test locally
3. When done: python scripts/index_codebase_qdrant.py
4. Restart Claude Code
5. Use qdrant-find for next task
```

### Troubleshooting Workflow
```
1. Agent says "no results found"
2. Check: .brain/docs/qdrant-debugging.md
3. Try: Verify index exists
4. If needed: Re-index
5. Restart Claude Code
```

### Architecture Review
```
1. Agent wants to understand pattern
2. Try: qdrant-find: "pattern description"
3. Get: Code chunks + metadata
4. Use: Grep/Read for deep dive
5. Reference: QDRANT_UNDERSTANDING.md for decision trees
```

## Search Strategy Reference

From `CLAUDE.md`:

| Use Case | Tool | Why |
|----------|------|-----|
| Explore patterns/architecture | **qdrant-find** | Semantic, finds related concepts |
| Understand how X works | **qdrant-find** | Returns full context chunks |
| Find exact symbol/string | **Grep** | Faster, precise matches |
| Find specific class/function | **Grep** | Direct name lookup |

Decision flow:
1. Don't know what to look for? → qdrant-find
2. Know exact name/symbol? → Grep
3. Exploring new area? → qdrant-find first, then Grep

## Performance Expectations

| Operation | Time | Notes |
|-----------|------|-------|
| Index rebuild | 40-60s | Full codebase |
| First query | 1-2s | Embedding model load |
| Subsequent query | 500ms | Typical |
| Index size | 50-100 MB | On disk |
| Memory usage | 700-800 MB | Total (Qdrant + model) |

## Help Resources

### If You're Stuck

1. **Quick issue?** → Check `.brain/docs/qdrant-debugging.md`
2. **How do I use it?** → Check `.brain/docs/qdrant-quick-reference.md`
3. **Want to understand?** → Read `.brain/docs/QDRANT_UNDERSTANDING.md`
4. **Technical details?** → Read `QDRANT_MCP_ARCHITECTURE.md`

### Most Common Issues

| Issue | Fix | Docs |
|-------|-----|------|
| "No results" | Re-index | qdrant-debugging.md |
| "Vector mismatch" | Check VECTOR_NAME | qdrant-debugging.md |
| "Search slow" | Normal, expected | qdrant-debugging.md |
| "How to query?" | See examples | qdrant-quick-reference.md |
| "Full architecture?" | Read complete guide | QDRANT_MCP_ARCHITECTURE.md |

## Maintenance Schedule

### After Every Session
- No action needed

### After Code Changes (Weekly)
- Run: `python scripts/index_codebase_qdrant.py`
- Time: ~1 minute

### When Adding Features (Per Feature)
- Recommended: Re-index for better search
- Time: ~1 minute

### Troubleshooting (As Needed)
- Refer: `.brain/docs/qdrant-debugging.md`
- Time: 5-10 minutes typical

## Knowledge Tree

```
QDRANT_INDEX.md (YOU ARE HERE)
│
├─ Quick Start
│  └─ qdrant-quick-reference.md (5 min)
│
├─ Understanding
│  └─ QDRANT_UNDERSTANDING.md (15 min)
│
├─ Debugging
│  └─ qdrant-debugging.md (20 min)
│
└─ Deep Dive
   └─ QDRANT_MCP_ARCHITECTURE.md (30+ min)
```

## What Each Document Contains

### qdrant-quick-reference.md
- Syntax: `qdrant-find: "query"`
- Search examples
- Query tips (good vs bad)
- Metadata interpretation
- Performance info

### QDRANT_UNDERSTANDING.md
- What Qdrant does
- Architecture overview
- How indexing works
- How search works
- Decision trees
- Maintenance procedures

### qdrant-debugging.md
- Health check procedures
- Common issues + fixes
- Direct Python testing
- Verification checklist
- Re-index procedure
- Performance profiling

### QDRANT_MCP_ARCHITECTURE.md
- Complete architecture diagrams
- Indexing pipeline details
- MCP server implementation
- Qdrant connector code
- Storage schema details
- Data flow examples
- Performance characteristics

## Next Steps

**Pick your path:**

1. **Use Qdrant right now**
   → Read: `.brain/docs/qdrant-quick-reference.md` (5 min)

2. **Understand the system**
   → Read: `.brain/docs/QDRANT_UNDERSTANDING.md` (15 min)

3. **Fix a problem**
   → Check: `.brain/docs/qdrant-debugging.md` (find your issue)

4. **Understand architecture**
   → Read: `QDRANT_MCP_ARCHITECTURE.md` (30+ min)

## Summary

CasareRPA uses **Qdrant** (vector database) + **MCP** (Model Context Protocol) to give agents semantic code search capability.

- **Agents ask:** `qdrant-find: "natural language query"`
- **System returns:** Code chunks ranked by semantic similarity
- **Agents benefit:** Can explore, understand, and reference code patterns easily

All documentation is in `.brain/docs/` and organized by audience and task.
