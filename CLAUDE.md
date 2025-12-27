# CasareRPA Agent Guide

```xml
<casare>
  <!-- Windows RPA | Python 3.12 | PySide6 | Playwright | DDD 2025 -->
  <!-- INDEX-FIRST: Always read _index.md files first -->

  <quick_commands>
    <cmd>pip install -e ".[dev]"</cmd>
    <cmd>pytest tests/ -v</cmd>
    <cmd>python run.py</cmd>
    <cmd>python manage.py canvas</cmd>
    <cmd>python scripts/create_worktree.py "feature-name"</cmd>
  </quick_commands>

  <indexes>
    <!-- Always read these _index.md files first -->
    <idx name="rules">.claude/rules/_index.md</idx>
      <desc>All 21 rule files</desc>
    <idx name="agents">.claude/agents/_index.md</idx>
      <desc>10 agent specifications</desc>
    <idx name="skills">.claude/skills/_index.md</idx>
      <desc>15 skills for Claude Code</desc>
    <idx name="brain">.brain/_index.md</idx>
      <desc>Knowledge base, decisions, plans</desc>
    <idx name="domain">src/casare_rpa/domain/_index.md</idx>
      <desc>Entities, events, schemas, protocols</desc>
    <idx name="nodes">src/casare_rpa/nodes/_index.md</idx>
      <desc>430+ automation nodes</desc>
    <idx name="app">src/casare_rpa/application/_index.md</idx>
      <desc>Use cases, orchestrators</desc>
    <idx name="infra">src/casare_rpa/infrastructure/_index.md</idx>
      <desc>Adapters, persistence, resources</desc>
    <idx name="canvas">src/casare_rpa/presentation/canvas/_index.md</idx>
      <desc>Qt UI, Canvas, graph</desc>
    <idx name="vnodes">src/casare_rpa/presentation/canvas/visual_nodes/_index.md</idx>
      <desc>Visual node widgets</desc>
  </indexes>

  <agents>
    <!-- Use Task(subagent_type="name") with these agents -->
    <agent name="explore">
      <chain>false</chain>
      <purpose>Codebase navigation, file search</purpose>
    </agent>
    <agent name="architect">
      <chain>true</chain>
      <purpose>Plan & implement (full auto-chain)</purpose>
    </agent>
    <agent name="builder">
      <chain>true</chain>
      <purpose>Code writing (auto test+review)</purpose>
    </agent>
    <agent name="quality">
      <chain>false</chain>
      <purpose>Testing, QA, performance</purpose>
    </agent>
    <agent name="reviewer">
      <chain>false</chain>
      <purpose>Code review gate (MANDATORY)</purpose>
    </agent>
    <agent name="refactor">
      <chain>true</chain>
      <purpose>Code cleanup (full auto-chain)</purpose>
    </agent>
    <agent name="researcher">
      <chain>false</chain>
      <purpose>Research, library comparison</purpose>
    </agent>
    <agent name="docs">
      <chain>false</chain>
      <purpose>Documentation, guides</purpose>
    </agent>
    <agent name="ui">
      <chain>true</chain>
      <purpose>Canvas UI design (full auto-chain)</purpose>
    </agent>
    <agent name="integrations">
      <chain>true</chain>
      <purpose>External APIs (full auto-chain)</purpose>
    </agent>
  </agents>

  <search_strategy>
    <step>1. Read _index.md in relevant directory</step>
    <step>2. Use Serena MCP: find_symbol, search_for_pattern, read_file</step>
    <step>3. Use grep only for known symbol names</step>
  </search_strategy>

  <mcp_servers>
    <server name="serena">
      <use>Semantic search, find_symbol, read_file</use>
    </server>
    <server name="filesystem">
      <use>File read/write operations</use>
    </server>
    <server name="git">
      <use>Repository inspection/operations</use>
    </server>
    <server name="playwright">
      <use>Browser automation testing</use>
    </server>
    <server name="web-search">
      <use>Web research</use>
    </server>
    <server name="exa">
      <use>Code context search</use>
    </server>
    <server name="ref">
      <use>API documentation lookup</use>
    </server>
  </mcp_servers>

  <rules dir=".claude/rules/">
    <!-- 21 rule files - see _index.md for complete list -->
    <rule file="00-role.md">Role and philosophy</rule>
    <rule file="01-core.md">Core workflow & standards</rule>
    <rule file="01-workflow-default.md">5-phase workflow</rule>
    <rule file="02-architecture.md">DDD 2025 architecture</rule>
    <rule file="02-coding-standards.md">Coding standards</rule>
    <rule file="03-nodes.md">Node development</rule>
    <rule file="04-agents.md">Agent registry</rule>
    <rule file="05-triggers.md">Workflow triggers</rule>
    <rule file="06-enforcement.md">Hard constraints</rule>
    <rule file="07-tools.md">Tooling rules</rule>
    <rule file="08-token-optimization.md">Token efficiency</rule>
    <rule file="09-brain-protocol.md">Brain protocol</rule>
    <rule file="10-node-workflow.md">Node lifecycle</rule>
    <rule file="11-node-templates.md">Node templates</rule>
    <rule file="12-ddd-events.md">Typed events</rule>
    <rule file="testing-standards.md">Testing standards</rule>
    <rule file="nodes/node-registration.md">Node registration</rule>
    <rule file="ui/theme-rules.md">Theme rules</rule>
    <rule file="ui/popup-rules.md">Popup rules</rule>
    <rule file="ui/signal-slot-rules.md">Signal/slot rules</rule>
  </rules>

  <non_negotiable>
    <rule name="INDEX-FIRST">.claude/rules/01-core.md</rule>
    <rule name="DOMAIN PURITY">.claude/rules/06-enforcement.md</rule>
    <rule name="ASYNC FIRST">.claude/rules/06-enforcement.md</rule>
    <rule name="HTTP (UnifiedHttpClient)">.claude/rules/01-core.md</rule>
    <rule name="THEME ONLY">.claude/rules/ui/theme-rules.md</rule>
    <rule name="POPUP (PopupManager)">.claude/rules/ui/popup-rules.md</rule>
    <rule name="SIGNAL/SLOT (@Slot)">.claude/rules/ui/signal-slot-rules.md</rule>
    <rule name="NODES (@properties)">.claude/rules/03-nodes.md</rule>
    <rule name="EVENTS (Typed)">.claude/rules/12-ddd-events.md</rule>
    <rule name="TESTING (pytest)">.claude/rules/testing-standards.md</rule>
  </non_negotiable>

  <reference_index>
    <category name="rules">.claude/rules/_index.md</category>
    <category name="agents">.claude/agents/_index.md</category>
    <category name="skills">.claude/skills/_index.md</category>
    <category name="brain">.brain/_index.md</category>
    <category name="decisions">.brain/decisions/_index.md</category>
    <category name="docs">.brain/docs/_index.md</category>
    <category name="context">.brain/context/current.md</category>
  </reference_index>

  <structure>
    <dir name="src/casare_rpa/domain">Pure logic (no deps) → _index.md</dir>
    <dir name="src/casare_rpa/application">Use cases → _index.md</dir>
    <dir name="src/casare_rpa/infrastructure">Adapters → _index.md</dir>
    <dir name="src/casare_rpa/presentation">Qt UI → _index.md</dir>
    <dir name="src/casare_rpa/nodes">430+ nodes → _index.md</dir>
    <dir name=".claude/rules">21 files → _index.md</dir>
    <dir name=".claude/agents">11 specs → _index.md</dir>
    <dir name=".claude/skills">15 skills → _index.md</dir>
    <dir name=".brain">Knowledge base → _index.md</dir>
  </structure>
</casare>
```

---

*Last updated: 2025-12-27*
