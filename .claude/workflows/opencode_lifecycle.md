# Opencode Lifecycle Workflow

This document maps the development lifecycle phases to the specific rule files in `../rules/`. **opencode** must follow this mapping to ensure compliance with project standards.

## Phase 1: RESEARCH & UNDERSTAND
*Before any planning or code generation.*

1.  **Understand Role & Scope:**
    *   Read: `../rules/00-role.md` (Core philosophy and behaviors)
    *   Read: `../rules/04-agents.md` (Agent capabilities and limitations)
2.  **Architecture Analysis:**
    *   Read: `../rules/02-architecture.md` (DDD patterns, layers, dependencies)
    *   Read: `../rules/12-ddd-events.md` (Event-driven architecture requirements)
3.  **Context Gathering:**
    *   Read: `.brain/context/current.md` (Current session state)
    *   Read: Relevant `_index.md` files (Use `glob` to find them)

## Phase 2: PLAN
*Developing a strategy before implementation.*

1.  **Workflow Definition:**
    *   Read: `../rules/01-workflow-default.md` (Standard 5-phase workflow)
    *   Tool: Use `todowrite` to create a structured plan.
    *   Review the plan with the user and get approval before EXECUTE.
2.  **Optimization Strategy:**
    *   Read: `../rules/08-token-optimization.md` (Efficient context usage)
3.  **Documentation Planning:**
    *   Check: `.brain/plans/` for existing plans to update or create new ones.

## Phase 3: EXECUTE
*Writing code and configuration.*

1.  **Coding Standards:**
    *   Read: `../rules/02-coding-standards.md` (Python/Qt style, error handling)
2.  **Tests First:**
    *   For feature work, create tests before implementation.
3.  **Specific Domains (Read as needed):**
    *   **Nodes:** Read `../rules/03-nodes.md`, `../rules/10-node-workflow.md`, `../rules/11-node-templates.md`.
    *   **Triggers:** Read `../rules/05-triggers.md`.
    *   **UI/Qt:** Read `../rules/ui/theme-rules.md`, `../rules/ui/signal-slot-rules.md`.
4.  **Tools & Safety:**
    *   Read: `../rules/07-tools.md` (Tool usage guidelines)

## Phase 4: VALIDATE
*Ensuring quality and correctness.*

1.  **Enforcement:**
    *   Read: `../rules/06-enforcement.md` (Strict "Do Not" rules)
2.  **Testing:**
    *   Run: `pytest tests/` (as defined in `07-tools.md`)
    *   Verify: No hardcoded colors, no silent failures, typed events used.
3.  **Self Review:**
    *   Review changes for correctness, consistency, and rule compliance.

## Phase 5: DOCUMENT & INTEGRATE
*Updating the brain and system state.*

1.  **Brain Protocol:**
    *   Read: `../rules/09-brain-protocol.md` (Updating `_index.md`, `.brain/` files)
2.  **Final Polish:**
    *   Update `AGENTS.md` (and sync `CLAUDE.md` + `GEMINI.md`) if new patterns emerge.
    *   Mark tasks as complete in `todowrite`.
