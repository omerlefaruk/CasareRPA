---
description: Protocol for maintaining the .brain knowledge base
---

# Brain Protocol

## Brain Structure

| Directory | Purpose |
|-----------|---------|
| .brain/context/ | Session state tracking |
| .brain/decisions/ | Decision trees for common tasks |
| .brain/plans/ | Implementation plans |
| .brain/docs/ | Long-lived documentation |

## Update Rules

### 1. Context Updates
- Update .brain/context/current.md at the start and end of every session.
- Record: Focus, Status, Key Decisions.
<<<<<<< HEAD
=======
- For multi-phase tasks, update status when a phase completes or when blocking on approval.
- Use `python scripts/phase_report.py` to log phase/progress updates.
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e

### 2. Decision Trees
- If you find yourself making a complex decision, document the logic in a new decision tree.
- Format: Graph-like markdown or simple lists.

### 3. Plans
- Create a plan file BEFORE starting any complex task.
- Update the plan as you make progress.

### 4. System Patterns
- If you discover a reusable pattern, add it to .brain/systemPatterns.md.
<<<<<<< HEAD
=======
- If the pattern changes agent behavior or standards, also update `AGENTS.md` and sync `CLAUDE.md` + `GEMINI.md` in the same change.
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e
