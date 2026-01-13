# CasareRPA Agent Guide (Lean)

This file is intentionally **small** to reduce Claude Code startup tokens.

```xml
<casare>
  <quick_commands>
    <cmd>pip install -e ".[dev]"</cmd>
    <cmd>pytest tests/ -v</cmd>
    <cmd>python run.py</cmd>
    <cmd>python manage.py canvas</cmd>
    <cmd>python scripts/create_worktree.py "feature-name"</cmd>
  </quick_commands>

  <start_here>
    <doc>docs/agent/_index.md</doc>
    <brain>.brain/_index.md</brain>
    <rules_core>.claude/rules/01-core.md</rules_core>
  </start_here>

  <indexes>
    <idx>src/casare_rpa/domain/_index.md</idx>
    <idx>src/casare_rpa/nodes/_index.md</idx>
    <idx>src/casare_rpa/application/_index.md</idx>
    <idx>src/casare_rpa/infrastructure/_index.md</idx>
    <idx>src/casare_rpa/presentation/canvas/_index.md</idx>
    <idx>src/casare_rpa/presentation/canvas/visual_nodes/_index.md</idx>
  </indexes>

  <non_negotiable>
    <rule>INDEX-FIRST: read relevant _index.md first</rule>
    <rule>SEARCH BEFORE CREATE</rule>
    <rule>DOMAIN PURITY: domain has no external deps</rule>
    <rule>NO SILENT FAILURES: log external failures</rule>
    <rule>ASYNC FIRST: no blocking I/O in async</rule>
    <rule>HTTP: use UnifiedHttpClient</rule>
    <rule>UI THEME: no hardcoded colors (use THEME)</rule>
    <rule>QT: @Slot required; no lambdas</rule>
    <rule>NODES: schema-driven (@properties + get_parameter)</rule>
    <rule>EVENTS: typed domain events only</rule>
  </non_negotiable>

  <note>
    .claude/rules/* contains small stubs that link to docs/agent/* (on-demand).
  </note>
</casare>
```

--- 
*Last updated: 2025-12-27*
