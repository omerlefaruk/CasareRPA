---
description: Optimized MCP config for minimal context loading
---

# Context Optimization Strategy

## Problem
OpenCode auto-loads 7-10% (30k+ tokens) of context on startup.

## Root Cause
1. Large instruction files (AGENTS.md: 18KB)
2. Multiple rule files loaded automatically
3. Filesystem server scanning entire project

## Solutions

### 1. Tiered Instruction Sets

**minimal** (opencode-minimal.json):
- Loads only: `00-minimal.md` (~2KB)
- Token usage: ~1-2k tokens
- Use for: Quick sessions, debugging

**standard** (opencode.json):
- Loads: Core rules + selected topics
- Token usage: ~10-12k tokens
- Use for: Normal development

**full** (opencode-full.json):
- Loads: AGENTS.md + all rules
- Token usage: ~30k+ tokens
- Use for: Deep research, documentation

### 2. Switching Modes

```bash
# Minimal mode (lowest tokens)
mv opencode-minimal.json opencode.json

# Standard mode (balanced)
cp opencode-standard.json opencode.json

# Full mode (maximum context)
cp opencode-full.json opencode.json
```

### 3. Filesystem Server Optimization

Current: `./src` (entire codebase)
Optimized: `./src/casare_rpa/domain` or `./docs` (specific areas)

### 4. Instruction File Strategy

- **Keep 00-minimal.md**: Quick reference, links to details
- **Keep full files intact**: Load on-demand via links
- **Use lazy loading**: Reference files instead of embedding

## Implementation

Files created:
1. `.opencode/rules/00-minimal.md` - Essential rules only
2. `opencode-minimal.json` - Minimal config
3. `.opencode/context-optimization.md` - This file
4. `opencode-standard.json` - Balanced config (create)
5. `opencode-full.json` - Full config (create)

## Usage

Start with `opencode-minimal.json`. OpenCode will load minimal instructions.
When you need more context, switch to `opencode-standard.json` or `opencode-full.json`.
