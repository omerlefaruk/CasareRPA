# CasareRPA: GitHub Copilot Operating Guide

GitHub Copilot must mirror the behaviour defined for our in-repo agents. Treat this file as the launch checklist and load the deeper rulebooks it references before editing.

## Canonical Guidance
- Start with [AGENT.md](../AGENT.md) and [.github/copilot/AGENT.md](copilot/AGENT.md) for Copilot-specific expectations, identity, and workflow overview.
- All binding rules live under [.agent/rules](../.agent/rules). Key documents:
  - Role and workflow: [.agent/rules/00-role.md](../.agent/rules/00-role.md), [.agent/rules/01-workflow-default.md](../.agent/rules/01-workflow-default.md)
  - Architecture and coding standards: [.agent/rules/02-architecture.md](../.agent/rules/02-architecture.md), [.agent/rules/02-coding-standards.md](../.agent/rules/02-coding-standards.md)
  - Enforcement and tooling: [.agent/rules/06-enforcement.md](../.agent/rules/06-enforcement.md), [.agent/rules/07-tools.md](../.agent/rules/07-tools.md)
  - Node and trigger playbooks: [.agent/rules/03-nodes.md](../.agent/rules/03-nodes.md), [.agent/rules/05-triggers.md](../.agent/rules/05-triggers.md), [.agent/rules/10-node-workflow.md](../.agent/rules/10-node-workflow.md)
  - Brain protocol and lifecycle: [.agent/workflows/opencode_lifecycle.md](../.agent/workflows/opencode_lifecycle.md), [.agent/rules/09-brain-protocol.md](../.agent/rules/09-brain-protocol.md)
- For task-specific briefs, reference [.agent/agents/_index.md](../.agent/agents/_index.md) and reuse the linked agent guides instead of creating new ones.

## Standard Workflow
1. **Research:** Load the relevant `_index.md` summaries in `.agent/` and `.brain/`. Perform workspace searches before proposing new designs.
2. **Plan:** Follow the five-phase lifecycle (research → plan → execute → validate → document). For substantial work, capture plans in `.brain/plans/` per the brain protocol.
3. **Execute:** Apply Clean Architecture boundaries, strict typing, async patterns, logging, and security guidance exactly as described in the rulebook. Reuse existing patterns.
4. **Validate:** Run or outline the documented tests (pytest suites, targeted checks). Honour enforcement rules: no silent failures, no hardcoded secrets, theme-only colours, typed events, etc.
5. **Document:** Update affected indexes or `.brain` context when mandated. Surface open questions or follow-ups explicitly.

## Quick Operational Facts
- Platform scope: Windows RPA suite (Canvas designer, Robot executor, Orchestrator API, Monitoring dashboard) built with Python 3.12, PySide6, Playwright, qasync, FastAPI.
- **Modern Node Standard (430+ nodes):** All nodes use `@properties()` + `get_parameter()` for dual-source access. NEVER use `self.config.get()`. Audit: `python scripts/audit_node_modernization.py`
- Key commands:
  - Run Canvas Designer: python manage.py canvas
  - Run Robot Agent: python manage.py robot start
  - Run Orchestrator API: python manage.py orchestrator start
  - Start Dashboard Dev Server: python manage.py dashboard
  - Execute full test suite: pytest tests/ -v
  - Build development installer: python installer/build_dev_installer.py
- Test boundaries: domain tests are pure logic, application tests mock infrastructure, infrastructure tests mock externals, presentation tests leverage pytest-qt, node tests use category fixtures.
- UI standards: widgets extend BaseWidget, rely on signal/slot patterns with @Slot decorators, and use theme tokens from THEME (no hardcoded colours).

## Reference Library
- [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md) for Clean Architecture details.
- [tests/integration/README.md](../tests/integration/README.md) for integration patterns.
- [src/casare_rpa/presentation/canvas/ui/README.md](../src/casare_rpa/presentation/canvas/ui/README.md) for UI conventions.
- [monitoring-dashboard/README.md](../monitoring-dashboard/README.md) for dashboard setup.
- [installer/README.md](../installer/README.md) for installer workflow.
- [GEMINI.md](../GEMINI.md) for full agent context and CLI reference.

Always defer to the `.agent` canon when instructions conflict. If ambiguity remains, surface the question and pause for clarification instead of guessing.
