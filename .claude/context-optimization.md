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

**minimal** (`.claude/claude-minimal.json`):
- Loads only: `.claude/rules/00-minimal.md`
- Token usage: ~1-2k tokens
- Use for: Quick sessions, debugging

**standard** (`.claude/claude-standard.json`):
- Loads: core rules + selected topics
- Token usage: ~10-12k tokens
- Use for: Normal development

**full** (`.claude/claude-full.json`):
- Loads: `CLAUDE.md` + additional rules
- Token usage: ~30k+ tokens
- Use for: Deep research, documentation

### 2. Switching Modes

```bash
# Choose the config file you pass to Claude Code (or copy to your active config).
```

### 3. Filesystem Server Optimization

Current: `./src` (entire codebase)
Optimized: `./src/casare_rpa/domain` or `./docs` (specific areas)

### 4. Instruction File Strategy

- **Keep 00-minimal.md**: Quick reference, links to details
- **Keep full files intact**: Load on-demand via links
- **Use lazy loading**: Reference files instead of embedding

## Implementation

Files:
1. `.claude/rules/00-minimal.md` - Essential rules only
2. `.claude/claude-minimal.json` - Minimal config
3. `.claude/claude-standard.json` - Balanced config
4. `.claude/claude-full.json` - Full config

## Usage

Start with `opencode-minimal.json`. OpenCode will load minimal instructions.
When you need more context, switch to `opencode-standard.json` or `opencode-full.json`.
