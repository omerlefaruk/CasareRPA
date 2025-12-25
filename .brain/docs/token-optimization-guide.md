# Token Usage Optimization Guide

**Date**: 2025-12-25
**Purpose**: Comprehensive token reduction strategies

## Implemented Optimizations

### 1. Prompt Compression ✅
**File**: `scripts/compress_prompts.py`

Features:
- Remove filler phrases and verbose wording
- Compress verbose phrases to concise alternatives
- Truncate long code blocks with summaries
- Model-specific prompt optimization

**Usage**:
```python
from scripts.compress_prompts import compress_prompt, truncate_conversation

compressed = compress_prompt(prompt, aggressive=True)
truncated_messages = truncate_conversation(messages, max_tokens=4000)
```

**Expected Savings**: 15-30% per prompt

---

### 2. Context Window Management ✅
**File**: `src/casare_rpa/utils/llm/context_manager.py`

Features:
- Sliding window (keep N most recent messages)
- Token budget enforcement
- Message deduplication
- Prioritized retention (system prompts always kept)
- Semantic relevance filtering (optional)

**Usage**:
```python
from casare_rpa.utils.llm.context_manager import ConversationSession

session = ConversationSession(max_tokens=4000, system_prompt=system_prompt)
session.user_message("What is X?")
context = session.get_llm_context()
```

**Expected Savings**: 20-40% on long conversations

---

### 3. Lazy Context Loading ✅
**File**: `src/casare_rpa/utils/context/context_loader.py`

Features:
- Load only `context/current.md` by default (25 lines)
- Load `context/recent.md` on demand
- Never load `context/archive/` (reference only)
- Archive management utilities

**Usage**:
```python
from casare_rpa.utils.context.context_loader import load_context_for_agent

context = load_context_for_agent(need_recent=False)  # Default: minimal
context = load_context_for_agent(need_recent=True)  # With recent history
```

**Expected Savings**: ~25,000 tokens per agent invocation

---

### 4. AGENTS.md Trimming ✅
**File**: `scripts/trim_agents_md.py`

Features:
- Trim to essential sections only
- Keep core rules, tech stack, node standard
- Remove verbose examples and tables
- Create minimal version

**Usage**:
```bash
python scripts/trim_agents_md.py --minimal
```

**Expected Savings**: 60-70% (from 1372 lines to ~200 lines)

---

### 5. LLM Response Caching ✅
**Files**:
- `src/casare_rpa/utils/llm/cache.py`
- `src/casare_rpa/utils/llm/cached_clients.py`

Features:
- Disk-based persistence (diskcache)
- Automatic TTL expiration
- Token counting for budgeting
- Cache hit/miss tracking
- Cached clients for OpenAI and Anthropic

**Usage**:
```python
from casare_rpa.utils.llm.cache import LLMResponseCache
from casare_rpa.utils.llm.cached_clients import CachedAnthropicClient

cache = LLMResponseCache()
client = CachedAnthropicClient(api_key=api_key, cache=cache)

response = client.generate(prompt="Hello", model="claude-3-5-sonnet-20241022")
print(f"Cache stats: {client.get_cache_stats()}")
```

**Expected Savings**: 30-50% on repeated queries

---

### 6. ChromaDB RAG Enhanced ✅
**File**: `src/casare_rpa/utils/rag/code_search.py`

Features:
- Semantic search for code (vector embeddings)
- Hybrid search (semantic + keyword)
- Top-K retrieval (fetch only relevant chunks)
- Chunk-level indexing (fine-grained results)
- Context injection based on query relevance

**Usage**:
```python
from casare_rpa.utils.rag.code_search import rag_search_code

results = rag_search_code(query="How to use @properties decorator?")
# Returns only relevant code chunks, not full files
```

**Expected Savings**: 40-60% vs loading full files

---

### 7. MCP Server Optimization ✅
**File**: `scripts/optimize_mcp.py`

Features:
- Disable unused MCP servers
- Keep only essential: codebase, filesystem, playwright
- Create minimal config (3 servers vs 6)
- Backup before modification

**Usage**:
```bash
python scripts/optimize_mcp.py --minimal    # Create .mcp.minimal.json
python scripts/optimize_mcp.py --essential # Keep only essential servers
```

**Expected Savings**: 50% on MCP server startup

---

### 8. Token Usage Tracking ✅
**File**: `scripts/token_tracker.py`

Features:
- Session-based tracking
- Cache hit/miss tracking
- Per-agent statistics
- Trend analysis (matplotlib plots)
- Optimization recommendations
- CSV export for analysis

**Usage**:
```bash
python scripts/token_tracker.py --report 7    # Generate 7-day report
python scripts/token_tracker.py --plot 30       # Plot 30-day trends
python scripts/token_tracker.py --csv           # Export to CSV
```

**Expected Value**: Identify high-usage patterns and optimization opportunities

---

## Maintenance Schedule

### Monthly (Automate with GitHub Actions)
```bash
# Archive old .brain/analysis files
python scripts/archive_brain_analysis.py

# Archive completed plans
python scripts/archive_old_plans.py --days=30

# Trim AGENTS.md
python scripts/trim_agents_md.py

# Rebuild codebase index
python scripts/index_codebase.py
```

### Quarterly
```bash
# Review and disable unused MCP servers
python scripts/optimize_mcp.py

# Check for unused dependencies
python scripts/audit_codebase.py
```

---

## Expected Total Impact

| Optimization | Expected Savings | Priority |
|-------------|------------------|----------|
| Prompt Compression | 15-30% | High |
| Context Window | 20-40% | High |
| Lazy Loading | ~25K per call | High |
| AGENTS.md Trim | 60-70% | Medium |
| Response Caching | 30-50% | High |
| RAG Search | 40-60% | High |
| MCP Optimization | 50% startup | Low |
| Token Tracking | Visibility | Medium |

**Overall Expected Savings**: 40-70% total token usage

---

## Integration Guide

### For AI Agents
Load minimal context by default:
```python
# In agent instructions
from casare_rpa.utils.context.context_loader import load_context_for_agent

context = load_context_for_agent(need_recent=False)  # ~25 lines
```

Use compression before LLM calls:
```python
from scripts.compress_prompts import compress_prompt

compressed_prompt = compress_prompt(user_input, aggressive=True)
response = llm.generate(compressed_prompt)
```

Enable caching for LLM clients:
```python
from casare_rpa.utils.llm.cached_clients import CachedAnthropicClient

client = CachedAnthropicClient(api_key=key)
response = client.generate(prompt)  # Automatic caching
```

### For Manual Use
1. **Before**: `cat AGENTS.md` (1372 lines, ~100K tokens)
2. **After**: `cat AGENTS.minimal.md` (~200 lines, ~15K tokens)

3. **Monitor**: `python scripts/token_tracker.py --report`

---

## Quick Commands

```bash
# Trim AGENTS.md
python scripts/trim_agents_md.py --minimal

# Optimize MCP servers
python scripts/optimize_mcp.py --minimal

# Generate token usage report
python scripts/token_tracker.py --report 7

# Test prompt compression
python -c "from scripts.compress_prompts import *; print(compress_prompt('test'))"
```

---

## Files Created

| File | Purpose | Lines |
|-------|---------|--------|
| `scripts/compress_prompts.py` | Prompt compression | 230 |
| `src/casare_rpa/utils/llm/context_manager.py` | Context management | 300 |
| `src/casare_rpa/utils/context/context_loader.py` | Lazy loading | 320 |
| `scripts/trim_agents_md.py` | AGENTS.md trimming | 160 |
| `src/casare_rpa/utils/llm/cache.py` | LLM caching | 320 |
| `src/casare_rpa/utils/llm/cached_clients.py` | Cached clients | 160 |
| `src/casare_rpa/utils/rag/code_search.py` | RAG search | 410 |
| `scripts/optimize_mcp.py` | MCP optimization | 130 |
| `scripts/token_tracker.py` | Token tracking | 450 |

**Total**: ~2,500 lines of optimization code

---

## Next Steps

1. **Integrate** these utilities into agent workflows
2. **Monitor** token usage with tracker for 2 weeks
3. **Adjust** based on actual savings data
4. **Document** agent-specific optimization patterns

---

*Last Updated*: 2025-12-25 02:21 UTC
