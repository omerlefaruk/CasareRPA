# Token Optimization Plan

**Status**: Planning
**Created**: 2025-12-25
**Target**: 31% token reduction (29,000 → 20,000 tokens)

## Overview

Current token usage across agent configuration:
- Agents: ~11,000 tokens (12 agents)
- Skills: ~6,000 tokens (10 skills)
- Rules: ~5,000 tokens (14 rules)
- Brain: ~7,000 tokens (docs + context)

**Goal**: Reduce to ~20,000 tokens by splitting context, archiving deprecated content, and consolidating redundant instructions.

## Phase 1: Context File Splitting (Save ~2,000 tokens)

### Problem
- `.brain/context/current.md`: 318 lines, grows indefinitely
- All agents load entire history every session

### Solution
1. **Split into active + archive**:
   ```
   .brain/context/current.md          # Active session only (~30 lines)
   .brain/context/archive/2025-12-25.md  # Completed work
   ```

2. **Create rotation script**: `scripts/manage_context.py`
   - Move old content to archive/YYYY-MM-DD.md
   - Keep only current session in current.md
   - Auto-cleanup archives older than 90 days

3. **Update agent loading**:
   - Change: "Read .brain/context/current.md"
   - To: "Read .brain/context/current.md (active only)"

### Files Modified
- `.brain/context/current.md`
- `scripts/manage_context.py` (new)
- All 12 agent guides (loading instructions)

---

## Phase 2: Brain File Consolidation (Save ~4,000 tokens)

### 2.1 Split node-templates.md (1,407 lines → 3 × 400 lines)

**Current**: `.brain/docs/node-templates.md` (1,407 lines)

**Split into**:
```
.brain/docs/node-templates/
├── _index.md           # Category overview (~100 lines)
├── browser.md          # Browser nodes (~400 lines)
├── data-flow.md        # Data/variable/flow nodes (~400 lines)
├── ui-desktop.md       # UI/Desktop nodes (~400 lines)
└── system.md           # System nodes (~200 lines)
```

### 2.2 Reduce projectRules.md (1,371 lines → ~800 lines)

**Actions**:
1. Move historical decisions to `.brain/decisions/archive/`
2. Keep only active rules in projectRules.md
3. Add reference table: "See: decisions/archive/old-pattern.md"

### 2.3 Archive deprecated COMMAND_*.md (1,248 lines)

**Files to archive**:
- `.brain/plans/archive/*` (already deprecated)
- Remove from agent loading instructions

### 2.4 Limit phase reports in current.md

**Rule**: Keep only last 3 phase reports
- Archive older to `.brain/reports/archive/`
- Add cleanup script to manage_context.py

### Files Modified
- `.brain/docs/node-templates.md` (delete, split)
- `.brain/docs/node-templates/*` (new directory)
- `.brain/projectRules.md` (reduce)
- `.brain/context/current.md` (phase report limit)

---

## Phase 3: Skill Simplification (Save ~1,500 tokens)

### 3.1 Deprecate unused skills

**agent-invoker** (unused):
- Functionality: Duplicate of `/chain` command
- Action: Deprecate, remove from skill registry

### 3.2 Split node-template-generator

**Current**: Single skill handles design + generation

**Split into**:
```
node-designer:     # Architecture, property definitions
node-generator:    # Code generation, registration
```

### 3.3 Merge import-fixer

**Current**: Separate skill for import fixing

**Action**: Merge into new `code-quality` skill
```
code-quality:
  - Fix imports
  - Fix type hints
  - Fix formatting
```

### 3.4 Reference brain docs instead of duplicating

**Example**: Instead of repeating node rules in skills:
- Remove duplicated content
- Add: "See: .brain/docs/node-templates/browser.md"

### Files Modified
- `.claude/skills/agent-invoker.md` (deprecate)
- `.claude/skills/node-template-generator.md` (split)
- `.claude/skills/node-designer.md` (new)
- `.claude/skills/node-generator.md` (new)
- `.claude/skills/import-fixer.md` (merge)
- `.claude/skills/code-quality.md` (new)

---

## Phase 4: Agent Consolidation (Save ~500 tokens)

### 4.1 Standardize .brain Protocol sections

**Problem**: Conflicting instructions across 12 agents
- Some say "head ~100 lines"
- Others say "read entire file"

**Solution**: Create unified loading table
```markdown
### Brain Protocol

| File | When | Scope |
|------|------|-------|
| current.md | Session start | Active context only |
| projectRules.md | Implementing | Read all |
| systemPatterns.md | Designing | Read all |
| docs/node-templates/* | Node dev | Category-specific |
```

### 4.2 Remove redundant instructions

**Pattern found**: All agents repeat same rules
- "Follow .claude/rules/01-workflow.md"
- "Use search_codebase() via MCP"

**Action**: Move to base template, reference by name

### 4.3 Add on-demand reference tables

**Instead of**: Embedding full file contents in agents

**Use**: Reference tables with "See: [file]"
```markdown
## Reference Documentation

| Topic | File |
|-------|------|
| Node patterns | .brain/docs/node-templates/ |
| DDD events | src/casare_rpa/domain/_index.md |
| Workflow | .claude/rules/01-workflow.md |
```

### Files Modified
- All 12 agent files in `.claude/agents/`

---

## Implementation Order

### Priority 1: Quick Wins (15 min)
- [ ] Archive deprecated COMMAND_*.md files
- [ ] Deprecate agent-invoker skill
- [ ] Limit phase reports to 3

### Priority 2: Context Splitting (30 min)
- [ ] Create scripts/manage_context.py
- [ ] Split current.md into active + archive
- [ ] Update agent loading instructions

### Priority 3: Agent Instructions (30 min)
- [ ] Standardize .brain Protocol sections
- [ ] Add reference documentation tables
- [ ] Remove redundant rule repetitions

### Priority 4: Brain Consolidation (60 min)
- [ ] Split node-templates.md into 5 files
- [ ] Reduce projectRules.md (archive old decisions)
- [ ] Update all node-development references

### Priority 5: Skills Restructure (30 min)
- [ ] Split node-template-generator
- [ ] Merge import-fixer into code-quality
- [ ] Update skill registry

---

## Testing & Validation

### Baseline Metrics
```bash
# Measure current token usage
python scripts/measure_tokens.py

# Test all agents load correctly
/chain test "verify agent loading"
```

### Validation Steps
1. **Each agent**: Load and verify no errors
2. **Each skill**: Run test case
3. **Token count**: Verify reduction to ~20,000
4. **Functionality**: Run /chain smoke test

### Success Criteria
- [ ] Total tokens ≤ 20,000 (31% reduction)
- [ ] All 12 agents load without errors
- [ ] All skills functional
- [ ] No broken references
- [ ] Context rotation working

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Broken references after split | Update all references in single commit |
| Agents fail to load | Test each agent individually |
| Lost historical context | Archive everything before deletion |
| Token reduction insufficient | Iterative optimization |

---

## Rollback Plan

If critical issues arise:
```bash
# Restore from git
git revert <commit-hash>

# Or restore backup
python scripts/restore_backup.py --before-token-optimization
```

---

## Next Steps

1. **Approve plan**: Review phases and implementation order
2. **Create worktree**: `python scripts/create_worktree.py "token-optimization"`
3. **Execute phases**: Follow implementation order
4. **Measure results**: Run token counting script
5. **Iterate**: Further optimize if needed

---

## References

- Exploration findings: `.brain/analysis/TOKEN_OPTIMIZATION_ANALYSIS.md`
- Current token breakdown: See exploration report
- Agent guides: `.claude/agents/`
- Skills: `.claude/skills/`
