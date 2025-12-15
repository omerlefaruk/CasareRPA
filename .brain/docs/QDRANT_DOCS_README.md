# Qdrant Documentation - Complete Guide

All documentation for understanding and using Qdrant semantic search in CasareRPA.

## Quick Start (Pick Your Path)

### 1. I want to USE Qdrant as an agent (5 minutes)
- **Read:** `qdrant-quick-reference.md`
- **Learn:** Syntax, examples, query tips
- **Action:** Start using `qdrant-find: "query"`

### 2. I want to UNDERSTAND the system (15 minutes)
- **Read:** `QDRANT_UNDERSTANDING.md`
- **Learn:** Architecture, how it works, when to update
- **Action:** Make informed decisions about search

### 3. I need to FIX a problem (10-20 minutes)
- **Read:** `qdrant-debugging.md`
- **Learn:** Health checks, common issues, solutions
- **Action:** Resolve specific issues

### 4. I want TECHNICAL DETAILS (30+ minutes)
- **Read:** `QDRANT_MCP_ARCHITECTURE.md` (in root)
- **Learn:** Complete architecture, code flow, implementation
- **Action:** Deep understanding of internals

### 5. I need EXECUTIVE SUMMARY (5 minutes)
- **Read:** `QDRANT_SYSTEM_ANALYSIS.md` (in root)
- **Learn:** Status, components, key facts
- **Action:** Get high-level overview

## Documentation Files

```
Root Directory:
├── QDRANT_MCP_ARCHITECTURE.md        - Technical architecture (30+ pages)
├── QDRANT_SYSTEM_ANALYSIS.md         - Executive summary & status

.brain/docs/:
├── QDRANT_DOCS_README.md            - This file
├── QDRANT_INDEX.md                  - Documentation index & navigation
├── QDRANT_UNDERSTANDING.md          - Complete overview (15 min read)
├── qdrant-quick-reference.md        - Agent usage guide (5 min read)
└── qdrant-debugging.md              - Troubleshooting guide (10+ min)

Key Configuration:
├── .mcp.json                         - MCP server config
├── scripts/index_codebase_qdrant.py - Indexing script
└── .qdrant/                          - Vector database

Project Documentation:
└── CLAUDE.md                         - Search strategy section
```

## Document Purposes

### QDRANT_MCP_ARCHITECTURE.md
**For:** Deep technical understanding
**Contains:**
- Complete architecture diagrams
- Component breakdown (indexer, server, database)
- Data flow examples
- Embedding process details
- Vector storage structure
- Performance metrics
- Troubleshooting guide

**Time:** 30-45 minutes
**Best for:** Architects, maintainers, detailed troubleshooting

### QDRANT_SYSTEM_ANALYSIS.md
**For:** Executive overview and status
**Contains:**
- System status and facts
- Component summary
- How agents use it
- Performance characteristics
- Integration points
- Known issues and solutions
- Next steps

**Time:** 5-10 minutes
**Best for:** Quick overview, status check, decision-makers

### QDRANT_UNDERSTANDING.md
**For:** Complete understanding
**Contains:**
- What Qdrant does and why
- Architecture overview
- Indexing process
- MCP server setup
- Search flow
- Search quality
- Maintenance procedures
- Troubleshooting checklist
- Integration with agents

**Time:** 15-20 minutes
**Best for:** Developers maintaining the system

### qdrant-quick-reference.md
**For:** Agent usage and queries
**Contains:**
- How to use syntax
- Search examples
- Query tips (good vs bad)
- Metadata interpretation
- Performance info
- Limitations
- Troubleshooting tips

**Time:** 5-10 minutes
**Best for:** Agents writing queries

### qdrant-debugging.md
**For:** Troubleshooting and verification
**Contains:**
- Health check procedures
- Indexing troubleshooting
- MCP server troubleshooting
- Direct Python testing
- Verification checklist
- Re-index procedures
- Performance profiling
- Common issues with solutions

**Time:** 10-30 minutes (depends on issue)
**Best for:** Fixing specific problems

### QDRANT_INDEX.md
**For:** Navigation and organization
**Contains:**
- Quick navigation by role
- File structure
- Core concepts
- Command reference
- Common questions
- Knowledge tree
- Next steps

**Time:** 5-10 minutes
**Best for:** Finding the right document

## Recommended Reading Order

### For New Users
1. This file (QDRANT_DOCS_README.md) - 5 min
2. qdrant-quick-reference.md - 5 min
3. QDRANT_UNDERSTANDING.md - 15 min
4. **Total: ~25 minutes**

### For System Maintainers
1. QDRANT_SYSTEM_ANALYSIS.md - 5 min
2. QDRANT_UNDERSTANDING.md - 15 min
3. qdrant-debugging.md (as needed) - 10+ min
4. QDRANT_MCP_ARCHITECTURE.md (optional deep dive) - 30+ min
5. **Total: ~30-60 minutes**

### For Troubleshooting
1. QDRANT_SYSTEM_ANALYSIS.md - Quick status check
2. qdrant-debugging.md - Find your issue
3. Follow specific solution
4. **Total: 10-20 minutes**

## Key Concepts Across Docs

### Qdrant
- Vector database for semantic search
- Local storage in `.qdrant/` directory
- Contains collection: `casare_codebase`
- ~2000-3000 indexed code chunks

### MCP (Model Context Protocol)
- Protocol connecting agents to Qdrant
- Configured in `.mcp.json`
- Handles query embedding
- Returns ranked results

### Indexing
- Process of converting code to vectors
- Script: `scripts/index_codebase_qdrant.py`
- Run after significant code changes
- Takes ~40-60 seconds

### Search
- Agent asks: `qdrant-find: "query"`
- System embeds and searches vectors
- Returns top-K code chunks
- Takes ~500ms typical

### Metadata
- Rich information attached to each code chunk
- Includes: type, name, path, layer, category, etc.
- Helps interpret and filter results

## Command Reference

All documentation commands:

```bash
# Indexing
python scripts/index_codebase_qdrant.py

# Health check
python -c "from qdrant_client import QdrantClient; print(QdrantClient(path='.qdrant').count('casare_codebase').count)"

# Testing embedding
python -c "from fastembed import TextEmbedding; print(len(list(TextEmbedding('sentence-transformers/all-MiniLM-L6-v2').embed(['test']))[0]))"

# Agent usage
qdrant-find: "search query"
```

## Search Strategy Reference

From CLAUDE.md - when to use what:

| Use Case | Tool |
|----------|------|
| Explore patterns/architecture | **qdrant-find** |
| Understand how X works | **qdrant-find** |
| Find exact symbol/string | **Grep** |
| Find specific class/function | **Grep** |

**Decision:**
1. Don't know what to look for? → qdrant-find
2. Know exact name/symbol? → Grep
3. Exploring new area? → qdrant-find first

## Performance Summary

| Metric | Value | Notes |
|--------|-------|-------|
| Query time | ~500ms | Typical |
| First query | 1-2s | Embedding load |
| Indexing time | 40-60s | Full rebuild |
| Index size | 50-100 MB | On disk |
| Memory usage | 700-800 MB | Total system |
| Indexed chunks | 2000-3000 | Points in DB |

## File Quick Links

| Need | File | Time |
|------|------|------|
| How to query | qdrant-quick-reference.md | 5 min |
| Understand system | QDRANT_UNDERSTANDING.md | 15 min |
| Fix problem | qdrant-debugging.md | 10+ min |
| Executive overview | QDRANT_SYSTEM_ANALYSIS.md | 5 min |
| Architecture | QDRANT_MCP_ARCHITECTURE.md | 30+ min |
| Navigate docs | QDRANT_INDEX.md | 5 min |

## Maintenance Checklist

- [ ] Index updated after code changes? (See: QDRANT_UNDERSTANDING.md)
- [ ] Index healthy? (See: qdrant-debugging.md Health Check)
- [ ] Agents can query? (See: qdrant-quick-reference.md)
- [ ] Results relevant? (See: QDRANT_UNDERSTANDING.md Search Quality)
- [ ] System memory OK? (See: QDRANT_SYSTEM_ANALYSIS.md Performance)

## Common Questions

**Q: Where do I start?**
A: Pick your path above based on what you need.

**Q: How do I use Qdrant as an agent?**
A: Read qdrant-quick-reference.md (5 min)

**Q: How do I understand the system?**
A: Read QDRANT_UNDERSTANDING.md (15 min)

**Q: How do I fix search not working?**
A: Read qdrant-debugging.md (find your issue)

**Q: What's the technical architecture?**
A: Read QDRANT_MCP_ARCHITECTURE.md (30+ min)

**Q: What's the current status?**
A: Read QDRANT_SYSTEM_ANALYSIS.md (5 min)

## Next Steps

1. **Choose your path** based on your needs (see above)
2. **Read the appropriate document** (time varies)
3. **Apply the knowledge** (run commands, use qdrant-find, etc.)
4. **Refer back** as needed for specific questions

## Documentation Philosophy

These docs are organized by:
- **Audience:** Agents, developers, architects
- **Task:** Using, understanding, fixing
- **Time:** Quick (5 min) to deep (30+ min)
- **Purpose:** Quick reference to deep understanding

No need to read all docs - pick what you need.

---

**Last Updated:** 2025-12-14
**Status:** Complete
**Maintenance:** Update when system changes
