# Active Context

**OPTIMIZED**: This file now redirects to the context/ directory for reduced token usage.

## Context Files

| File | Purpose | When to Load |
|------|---------|--------------|
| [context/current.md](context/current.md) | Active session state | Always |
| [context/recent.md](context/recent.md) | Last 3 completed tasks | On demand |
| [context/archive/](context/archive/) | Historical sessions | Never (reference only) |

## Quick Load

For agents, load only `context/current.md` (~25 lines) instead of this file.

**Token savings**: ~25,000 tokens per agent invocation.
