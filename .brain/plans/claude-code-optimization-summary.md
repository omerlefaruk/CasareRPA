# Claude Code Optimization - Executive Summary

## Research Complete

Conducted comprehensive research on Claude Code's official standards for:
- CLAUDE.md (project memory)
- Rules Directory (`.claude/rules/`)
- Skills (`.claude/skills/`)
- Agents/Subagents (`.claude/agents/`)
- Commands (`.claude/commands/`)

**Sources:**
- [ClaudeFast - CLAUDE.md Mastery](https://claudefa.st/blog/guide/mechanics/claude-md-mastery)
- [ClaudeFast - Rules Directory](https://claudefa.st/blog/guide/mechanics/rules-directory)
- [Claude Code - Skills Docs](https://code.claude.com/docs/en/skills)
- [Claude Code - Subagents Docs](https://code.claude.com/docs/en/sub-agents)
- [alexop.dev - Customization Guide](https://alexop.dev/posts/claude-code-customization-guide-claudemd-skills-subagents/)

---

## Key Findings

### 1. CLAUDE.md is Overloaded
- **Current**: ~400 lines, ~15KB tokens
- **Recommended**: ~150 lines
- **Issue**: "Priority saturation" - too much high-priority content reduces effectiveness
- **Solution**: Extract domain-specific rules to path-targeted files

### 2. Skills Format Mismatch
- **Current**: Single `.md` files with YAML frontmatter
- **Standard**: Folders with `skill.yaml` + `skill.md`
- **Impact**: May affect auto-discovery reliability
- **Solution**: Migrate to folder structure

### 3. Path-Targeting Underutilized
- **Current**: Rules load for all files
- **Capability**: YAML frontmatter `paths:` field restricts activation
- **Benefit**: ~30-50% context reduction on focused tasks

### 4. Nested CLAUDE.md Pattern Available
- **Feature**: Subdirectory `CLAUDE.md` files auto-load when working in that directory
- **Opportunity**: Directory-specific rules for `tests/`, `domain/`, `nodes/`, etc.

---

## Comparison Table

| Component | Current State | Official Standard | Gap |
|-----------|---------------|-------------------|-----|
| **CLAUDE.md** | 400+ lines | 100-150 lines | ⚠️ Overloaded |
| **Skills** | Single `.md` files | Folders with `skill.yaml` | ⚠️ Format |
| **Rules** | Minimal path targeting | Extensive path targeting | ⚠️ Underutilized |
| **Agents** | YAML frontmatter | Same format | ✅ Aligned |
| **Commands** | YAML frontmatter | Same format | ✅ Aligned |

---

## Priority Recommendations

### P0 - High Impact, Medium Effort
**CLAUDE.md Token Optimization**
- Extract domain sections to path-targeted rules
- Expected: 50% token reduction in session startup
- Files: `CLAUDE.md`, create 4-5 new rule files

### P1 - Medium Impact, Medium Effort
**Skills Format Standardization**
- Migrate 12 skills to folder structure
- Expected: Better compatibility and auto-discovery
- Files: All `.claude/skills/*.md`

**Rules Path-Targeting Expansion**
- Add `paths:` frontmatter to existing rules
- Expected: 30% context reduction on focused tasks
- Files: `.claude/rules/*.md`

### P2 - Low Impact, Low Effort
**Agent Description Refinement**
- Ensure descriptions follow "MUST BE USED for..." pattern
- Expected: Better auto-delegation accuracy
- Files: `.claude/agents/*.md`

**Nested CLAUDE.md Pattern**
- Add directory-specific CLAUDE.md files
- Expected: Context-aware rule loading
- Files: `tests/CLAUDE.md`, `src/*/CLAUDE.md`

---

## Token Efficiency Projection

### Current
```
CLAUDE.md:  ~15,000 tokens (every session)
All rules:   ~8,000 tokens (every session)
────────────────────────────────────────
Total:      ~23,000 tokens per session
```

### After Optimization
```
CLAUDE.md:  ~5,000 tokens (every session)
Active rules: ~3,000 tokens (path-filtered average)
────────────────────────────────────────
Total:       ~8,000 tokens average session
```

**Savings: ~65% reduction in high-priority context**

---

## Next Steps

1. Review plan: `.brain/plans/claude-code-optimization-2025.md`
2. Approve phases for implementation
3. Execute in order: P0 → P1 → P2
4. Test after each phase

---

## Files Created

- `.brain/plans/claude-code-optimization-2025.md` - Detailed plan
- `.brain/plans/claude-code-optimization-summary.md` - This summary
