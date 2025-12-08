<context>
  <meta>
    <rules>
      1. Be EXTREMELY concise. Sacrifice grammar.
      2. NO estimated effort/time/complexity ratings.
      3. REUSE > CREATION. Extend existing patterns.
      4. ALWAYS use .brain/ for context and plans.
      5. Always Be Swarming - Will your task benefit from parallelization? Deploy sub agents.
    </rules>

    <brain location=".brain/">
      <file name="activeContext.md">Current session state. Update after major tasks.</file>
      <file name="systemPatterns.md">Architecture patterns. Update when discovering new ones.</file>
      <file name="projectRules.md">Coding standards. Source of truth.</file>
      <file name="plans/{feature}.md">Feature plans. ALWAYS create here.</file>
      <file name="docs/node-checklist.md">Node implementation checklist. Read when creating nodes.</file>
      <file name="docs/trigger-checklist.md">Trigger node checklist. Read for trigger nodes.</file>
      <file name="docs/tdd-guide.md">TDD guide. Read when writing tests.</file>
      <file name="docs/ui-standards.md">UI standards. Read when building UI.</file>
      <file name="docs/widget-rules.md">Widget rules. Read for file paths/variable picker.</file>
    </brain>

    <workflow>
      PLAN → IMPLEMENT → TEST → REVIEW → QA → APPROVAL → DOCS
                ↑                    │
                └── (if ISSUES) ─────┘
    </workflow>

    <agents>
      <!-- Core (mandatory chain) -->
      <agent name="explore">Codebase search. Use first.</agent>
      <agent name="architect">Implementation. After: quality → reviewer</agent>
      <agent name="quality">Tests + perf. After: reviewer</agent>
      <agent name="reviewer">Code review gate. MANDATORY. Output: APPROVED | ISSUES</agent>

      <!-- Specialist -->
      <agent name="security">Security audits</agent>
      <agent name="docs">Documentation</agent>
      <agent name="refactor">Code cleanup. After: quality → reviewer</agent>
      <agent name="ui">Canvas UI</agent>
      <agent name="integrations">External APIs</agent>
      <agent name="researcher">Research, migrations</agent>
      <agent name="pm">Product scope</agent>
    </agents>

    <agent_flow>
      implementation: architect → quality → reviewer (loop if ISSUES)
      refactoring: refactor → quality → reviewer (loop if ISSUES)
      research: explore | researcher
    </agent_flow>

    <agent_name_mapping>
      <!-- Custom Name → System subagent_type for Task tool -->
      <map custom="explore" system="Explore" />
      <map custom="plan" system="Plan" />
      <map custom="architect" system="rpa-engine-architect" />
      <map custom="quality" system="chaos-qa-engineer" />
      <map custom="reviewer" system="code-security-auditor" />
      <map custom="security" system="security-architect" />
      <map custom="docs" system="rpa-docs-writer" />
      <map custom="refactor" system="rpa-refactoring-engineer" />
      <map custom="ui" system="rpa-ui-designer" />
      <map custom="integrations" system="rpa-integration-specialist" />
      <map custom="researcher" system="rpa-research-specialist" />
      <map custom="pm" system="mvp-product-manager" />
    </agent_name_mapping>

    <auto_workflow_triggers>
      <!-- Auto-detect and run full workflow for ANY code change -->

      <!-- Node-specific triggers -->
      <trigger pattern="implement.*node|create.*node|add.*node|build.*node">
        <workflow>implement-node</workflow>
        <phases>explore(3) → plan → architect → quality → reviewer(loop) → QA → docs</phases>
      </trigger>

      <!-- Feature implementation -->
      <trigger pattern="implement.*feature|add.*feature|create.*feature">
        <workflow>implement-feature</workflow>
        <phases>explore(3) → plan → architect → quality → reviewer(loop) → QA → docs</phases>
      </trigger>

      <!-- Fix/Debug/Repair -->
      <trigger pattern="fix|repair|debug|resolve|patch">
        <workflow>implement-feature</workflow>
        <phases>explore(3) → plan → architect → quality → reviewer(loop) → QA → docs</phases>
      </trigger>

      <!-- Refactor/Overhaul/Rewrite -->
      <trigger pattern="refactor|overhaul|rewrite|rebuild|restructure|cleanup|clean up">
        <workflow>implement-feature</workflow>
        <phases>explore(3) → plan → refactor → quality → reviewer(loop) → QA → docs</phases>
      </trigger>

      <!-- Update/Modify/Change -->
      <trigger pattern="update|modify|change|improve|enhance|optimize|upgrade">
        <workflow>implement-feature</workflow>
        <phases>explore(3) → plan → architect → quality → reviewer(loop) → QA → docs</phases>
      </trigger>

      <!-- Generic catch-all for code work -->
      <trigger pattern="look at.*and|work on|handle|address|tackle">
        <workflow>implement-feature</workflow>
        <phases>explore(3) → plan → architect → quality → reviewer(loop) → QA → docs</phases>
      </trigger>
    </auto_workflow_triggers>

    <cmds>
      <run>python run.py</run>
      <install>pip install -e .</install>
      <test>pytest tests/ -v</test>
    </cmds>

    <orchestration_changes>
      <!-- IMPORTANT: When modifying robot, orchestrator, or API code -->
      <rule>Always update start_platform_tunnel.bat if changing startup behavior</rule>
      <rule>After code changes, remind user to restart the Orchestrator API to load new code</rule>
      <rule>Test with: python -m casare_rpa.robot.cli start --name "TestRobot" --env development</rule>
      <affected_files>
        - src/casare_rpa/robot/distributed_agent.py
        - src/casare_rpa/infrastructure/orchestrator/api/*.py
        - src/casare_rpa/infrastructure/orchestrator/api/routers/*.py
        - deploy/supabase/migrations/*.sql
      </affected_files>
    </orchestration_changes>

    <node_registration>
      <!-- CRITICAL: New nodes must be registered in ALL places or errors occur -->
      <rule>1. nodes/{category}/__init__.py: Export the node class</rule>
      <rule>2. nodes/__init__.py: Add to _NODE_REGISTRY dict (lazy loading)</rule>
      <rule>3. utils/workflow/workflow_loader.py: Import + add to NODE_TYPE_MAP (validation)</rule>
      <rule>4. visual_nodes/{category}/nodes.py: Create VisualXxxNode class</rule>
      <rule>5. visual_nodes/{category}/__init__.py: Export VisualXxxNode</rule>
      <rule>6. visual_nodes/__init__.py: Add to _VISUAL_NODE_REGISTRY (for tab menu)</rule>
      <affected_files>
        - src/casare_rpa/nodes/__init__.py (_NODE_REGISTRY)
        - src/casare_rpa/utils/workflow/workflow_loader.py (import + NODE_TYPE_MAP)
        - src/casare_rpa/presentation/canvas/visual_nodes/__init__.py (_VISUAL_NODE_REGISTRY)
      </affected_files>
      <error_symptom>UNKNOWN_NODE_TYPE: Unknown node type: XxxNode</error_symptom>
      <error_symptom>Node not in tab menu: Missing from visual_nodes/__init__.py registry</error_symptom>
    </node_registration>
  </meta>

  <project name="CasareRPA">
    <overview>
      Windows Desktop RPA platform with visual node-based workflow editor.
      Enables Web (Playwright) and Desktop (UIAutomation) automation via drag-and-drop.
      Follows Clean Architecture (DDD).
    </overview>

    <stack>
      Python 3.12+, PySide6 (GUI), NodeGraphQt, Playwright, uiautomation,
      qasync (Qt+Asyncio), orjson, loguru, APScheduler, asyncpg/aiomysql.
    </stack>

    <architecture style="Clean DDD">
      <flow>Presentation → Application → Domain ← Infrastructure</flow>
      <layers>
        <layer name="Domain">Pure logic. Entities, VO, Services. NO deps.</layer>
        <layer name="Application">Use Cases. Coordinates Domain + Infra.</layer>
        <layer name="Infrastructure">Impl Domain interfaces. Resources, Persistence, Adapters.</layer>
        <layer name="Presentation">UI. Canvas, Controllers, EventBus. Depends on App.</layer>
      </layers>
      <structure>
        src/casare_rpa/ [domain, application, infrastructure, presentation, nodes, core]
      </structure>
    </architecture>

    <patterns>
      <item>Controller: MainWindow delegates to specialized controllers.</item>
      <item>EventBus: Pub/sub system for loose coupling.</item>
      <item>Async-First: All I/O operations async (Playwright/Qt).</item>
      <item>Trigger System: Registry-based (Manual, Scheduled, Webhook, File, AppEvent, etc).</item>
      <item>Connection Pooling: Browser contexts, DB connections, HTTP sessions.</item>
    </patterns>

    <!-- IMPLEMENTATION GUIDES - Read when needed -->
    <guides>
      <guide name="Node Implementation" file=".brain/docs/node-checklist.md">
        Read when creating new executable nodes. Covers decorators, schemas, visual nodes, exports.
      </guide>
      <guide name="Trigger Implementation" file=".brain/docs/trigger-checklist.md">
        Read when creating trigger nodes. Different from executable nodes.
      </guide>
      <guide name="TDD Guide" file=".brain/docs/tdd-guide.md">
        Read when writing tests. Covers layers, mocking, async testing, coverage targets.
      </guide>
      <guide name="UI Standards" file=".brain/docs/ui-standards.md">
        Read when building UI. Button heights, theme colors, QMessageBox styling.
      </guide>
      <guide name="Widget Rules" file=".brain/docs/widget-rules.md">
        Read for file path widgets and variable picker integration.
      </guide>
    </guides>

    <plans>
      <instruction>At the end of each plan, list unresolved questions to answer. Be extremely concise.</instruction>
      <roadmap>
        Current: Refactoring v2→v3 (Clean Architecture).
        Tasks: Complete trigger system, Project management, Perf optimization, Remove legacy core/ &amp; visual_nodes.
      </roadmap>
    </plans>
  </project>
</context>
