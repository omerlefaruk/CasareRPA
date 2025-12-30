# Plan Lifecycle Decision

**Date**: 2025-12-29
**Status**: ACTIVE

## Policy

### 1. Plan Location
**Plans MUST NOT be stored in `.brain/`**

- `.brain/` is for **active context** only (current session state, decisions, reference docs)
- Plans live at **project root**: `plans/` directory
- This prevents plans from being auto-loaded into startup context

### 2. Plan Auto-Deletion
**Active plans are auto-deleted after 2 days**

| Plan State | Location | TTL | Action |
|------------|----------|-----|--------|
| Active | `plans/` | 2 days | Delete after TTL |
| Completed | N/A | Immediate | Archive to git |
| Archived | `.brain/context/archive/plans/` | Permanent | Keep for reference |

### 3. Workflow

```
plans/ (root)
├── active-plan-*.md    # Created today, expires in 2 days
└── another-plan-*.md   # Created yesterday, expires tomorrow

# When plan is complete:
# 1. Delete from plans/
# 2. Git commit preserves history if needed
```

### 4. Enforcement

- Claude checks plan dates on startup
- Plans older than 2 days are flagged for deletion
- Completed plans are removed immediately (not archived in .brain)

### 5. Rationale

- `.brain/` is memory (loaded at startup) - keep it lean
- `plans/` is workspace (on-demand) - separate lifecycle
- Old plans create bloat and confusion
- Git history is the archive for completed plans
