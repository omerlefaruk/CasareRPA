# Claude Context & Subagent Token Optimization (CasareRPA)

**Created**: 2025-12-27
**Status**: In Progress
**Goal**: Reduce baseline context + subagent startup tokens without losing critical guidance.

## Principles (from Claude Code docs)
- Keep always-loaded instructions small and stable (`CLAUDE.md`).
- Use `.claude/rules/*.md` for modular rules; scope with `paths:` so only relevant rules load.
- Keep subagent prompts minimal; avoid duplicating global rules inside each agent file.

## Execution Plan

### 1) Establish the “Always-Loaded Core”
- [x] Keep `CLAUDE.md` as a short repo index + non-negotiables (no deep how-tos).
- [x] Ensure anything not universally applicable moves out of `CLAUDE.md` into:
  - Path-scoped rules (`.claude/rules/*`)
  - On-demand docs (`.brain/docs/*`)
  - Slash commands (`.claude/commands/*`) for procedures

### 2) Path-Scope Rules (Primary Token Lever)
Target: only a handful of rule files load globally; everything else is `paths:` scoped.

- [x] Add/adjust `paths:` frontmatter for “on-demand” rules:
  - `.claude/rules/_index.md`
  - `.claude/rules/01-workflow-default.md`
  - `.claude/rules/04-agents.md`
  - `.claude/rules/05-triggers.md`
  - `.claude/rules/09-brain-protocol.md`
  - `.claude/rules/10-node-workflow.md`
  - `.claude/rules/11-node-templates.md`

- [ ] Decide which rules remain global (no `paths:`), typically:
  - `00-role.md`, `01-core.md`, `06-enforcement.md`, `07-tools.md`, `08-token-optimization.md`
  - (Everything else should be scoped.)

### 3) Normalize Rule Metadata
- [x] Normalize `paths:` YAML formats to lists (avoid comma-separated single lines):
  - `.claude/rules/nodes/node-registration.md`
  - `.claude/rules/ui/theme-rules.md`
  - `.claude/rules/ui/signal-slot-rules.md`

### 4) Slim Subagents (Biggest “Startup Token” Win)
Target: subagent prompt = role + output contract + minimal defaults.

- [x] Trim `.claude/agents/*.md` bodies to remove duplicated global guidance and long checklists:
  - `architect.md`, `builder.md`, `docs.md`, `explore.md`, `integrations.md`
  - `quality.md`, `refactor.md`, `researcher.md`, `reviewer.md`, `ui.md`

### 5) Fix Stale References (Prevent Accidental Token Bombs)
- [x] Update node rule references that still point to deleted/split docs:
  - Replace `.brain/docs/node-templates.md` references with `.brain/docs/node-templates-*.md` (core/data/services).
- [x] Audit `.claude/claude-*.json` configs for non-existent rule files (e.g. `00-minimal.md`, `13-agent-chaining.md`) and either:
  - Create the missing files, or
  - Update configs to match the real set, or
  - Delete configs if unused.

### 6) Validate in Claude Code
- [ ] Run `/memory` from repo root and confirm:
  - Only core files load in “baseline”.
  - Path-scoped rules load only when editing matching files.
- [ ] Spot-check a few tasks:
  - Edit a node file → node rules load.
  - Edit a UI file → UI rules load.
  - Edit docs → brain protocol loads (if desired).

## XML Tags Recommendation
- Keep YAML frontmatter for metadata (`name`, `description`, `paths`, `tools`, etc.)—this is what Claude Code understands.
- Use XML only where it reduces ambiguity (indexes like `CLAUDE.md`, `_index.md`), not everywhere.
- Avoid wrapping every rule/agent in XML: it increases tokens and usually doesn’t improve instruction-following.

## Success Criteria
- [x] Subagent invocation prompts are short (no repeated repo-wide rules).
- [ ] Baseline memory load is “core-only”; specialized rules load only when relevant (verify via `/memory`).
- [x] No broken references to removed docs/rules.
