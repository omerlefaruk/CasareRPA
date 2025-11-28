<context>
  <meta>
    <rules>
      1. Be EXTREMELY concise. Sacrifice grammar.
      2. NO estimated effort/time/complexity ratings.
    </rules>
    <cmds>
      <run>python run.py</run>
      <install>pip install -e .</install>
      <test>pytest tests/ -v</test>
    </cmds>
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

    <plans>
      <instruction>At the end of each plan, list unresolved questions to answer. Be extremely concise.</instruction>
      <roadmap>
        Current: Refactoring v2→v3 (Clean Architecture).
        Tasks: Complete trigger system, Project management, Perf optimization, Remove legacy `core/` & `visual_nodes`.
      </roadmap>
    </plans>
  </project>
</context>
