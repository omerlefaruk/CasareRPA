# Archived Analysis (Non-Normative)

This file is archived analysis. Do not treat as current rules. See .agent/, .claude/, and .brain/_index.md for active guidance.

---
# CasareRPA Startup - Quick Reference

## Three Applications

### Canvas (GUI) - Main Designer
```
manage.py → cli/main.py (canvas cmd) → presentation/canvas/__main__.py → app.py:main()
```
**Startup time**: ~800ms
**Heavy ops**: Node registration (deferred), icon preloading, Qt setup

### Robot (Agent) - Workflow Executor
```
manage.py → cli/main.py (robot start) → robot/__main__.py → cli.py:main()
```
**Startup time**: ~7-10s
**Heavy ops**: Playwright browser check (5-10s), database connection

### Orchestrator (API) - Fleet Manager
```
manage.py → cli/main.py (orchestrator start) → uvicorn main.py
```
**Startup time**: ~3.75s
**Heavy ops**: Database pool (~2-5s), APScheduler, metrics init

---

## Canvas Initialization (Detailed)

### Quick Summary
```python
# app.py CasareRPAApp.__init__()
1. setup_logging()                           # 10ms
2. _setup_qt_application()                   # 100ms (Qt + qasync)
3. _create_ui()                              # 200ms (windows, serializers)
4. WINDOW.show()                             # ← SHOWN HERE (400ms)
5. _initialize_components()                  # 300ms (controllers)
   - Phase 4a: NodeController (8 nodes)     # 50ms
   - Phase 4b: 5 other controllers          # 200ms
6. QTimer.singleShot(500, _preload_icons)   # Background
7. QTimer.singleShot(100, _complete_dereg)  # 100-200ms (400+ nodes)
```

### Critical Files

| File | What | When | Speed |
|------|------|------|-------|
| `presentation/canvas/__main__.py` | QFont patch + entry | Before Qt | ~1ms |
| `presentation/canvas/app.py` | Main class | At startup | ~800ms |
| `config/logging_setup.py` | Logger setup | Phase 1 | ~10ms |
| `presentation/canvas/main_window.py` | UI creation | Phase 3 | ~50-100ms |
| `presentation/canvas/graph/node_graph_widget.py` | Graph widget | Phase 3 | ~20-50ms |
| `presentation/canvas/controllers/node_controller.py` | Node registry | Phase 4a/6 | ~250ms |
| `presentation/canvas/graph/node_registry.py` | Essential nodes (fast) | Phase 4a | ~50ms |

### Initialization Phases

**Phase 1: Logging** (app.py:170)
```python
setup_logging()  # From config/logging_setup.py
```

**Phase 2: Qt Setup** (app.py:202-223)
```python
qInstallMessageHandler(_qt_message_handler)  # Suppress CSS warnings
QApplication.setHighDpiScaleFactorRoundingPolicy(...)
self._app = QApplication(sys.argv)
self._loop = QEventLoop(self._app)  # qasync integration
asyncio.set_event_loop(self._loop)
self._app.aboutToQuit.connect(self._on_about_to_quit)  # Cleanup hook
```

**Phase 3: UI Creation** (app.py:225-261)
```python
self._main_window = MainWindow()
self._node_graph = NodeGraphWidget()
self._main_window.set_central_widget(self._node_graph)
# Create serializers (deferred import)
self._serializer = WorkflowSerializer(...)
self._deserializer = WorkflowDeserializer(...)
self._workflow_runner = CanvasWorkflowRunner(...)
```

**WINDOW SHOWN HERE** (app.py:184-188)
```python
self._main_window.setWindowTitle(f"{APP_NAME} - Loading...")
self._main_window.show()
self._app.processEvents()  # ← Force display to user
```

**Phase 4a: Essential Nodes** (app.py:287-289)
```python
self._node_controller = NodeController(self._main_window)
self._node_controller.initialize()  # Only 8 essential nodes
logger.debug("Essential nodes registered")

# Deferred: Icon preloading at +500ms
QTimer.singleShot(500, self._preload_icons_background)
```

**Phase 4b: Other Controllers** (app.py:296-343)
```python
self._workflow_controller = WorkflowController(...)
self._execution_controller = ExecutionController(...)
self._selector_controller = SelectorController(...)
self._preferences_controller = PreferencesController(...)
self._autosave_controller = AutosaveController(...)

for controller in [workflow, execution, selector, preferences, autosave]:
    controller.initialize()

# Inject controllers into MainWindow
self._main_window.set_controllers(...)
```

**Phase 5: Signal Connections** (app.py:193-197)
```python
self._connect_components()   # Cross-controller signals
self._connect_ui_signals()   # Edit actions, undo/redo
```

**Phase 6: Deferred** (app.py:346)
```python
# At +100ms (before icon preload):
QTimer.singleShot(100, self._complete_deferred_initialization)
    # Calls: self._node_controller.complete_node_registration()
    # Registers remaining 390+ nodes (takes 100-200ms but deferred)
```

---

## Robot Startup (Detailed)

### Quick Summary
```python
# robot/cli.py start() command
1. Load .env files (exe → AppData → cwd)           # 10ms
2. setup_signal_handlers(loop)                      # 10ms
3. _ensure_playwright_browsers()                    # 5-10s ← SLOW!
4. RobotConfig.from_env() or from_file()          # 20ms
5. RobotAgent(config)                              # 100ms
6. loop.run_until_complete(_run_agent(...))        # 2-5s (DB connection)
```

### Heavy Operations

**Playwright Check** (cli.py:160-253)
```python
# Synchronous, blocks startup
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    browser.close()

# If missing, auto-installs (subprocess, ~300s timeout)
```
**Cost**: 5-10 seconds (browser launch + optional install)
**Fix**: Make async or defer to first browser node use

**Database Connection** (agent.py initialization)
```python
# RobotAgent.__init__() connects to PostgreSQL
postgres_url = _get_postgres_url()
agent = RobotAgent(config)
await agent.start()
```
**Cost**: 2-5 seconds (connection pool creation)
**Status**: Has fallback, but blocking

### Environment Variables (Priority)

1. Frozen app (PyInstaller exe):
   - `.env` in exe directory (highest priority)
2. Windows AppData:
   - `%APPDATA%\CasareRPA\.env`
3. Current working directory:
   - `.env` (fallback)

---

## Orchestrator API Startup (Detailed)

### Quick Summary
```python
# infrastructure/orchestrator/api/main.py
1. FastAPI app creation                           # 30ms
2. Middleware setup (CORS, RequestId, RateLimit)  # 50ms
3. Router registration (8 routers)                # 50ms
4. lifespan startup hook:
   a) _init_database_pool(app)                    # 2-5s ← HEAVY!
   b) set_db_pool_for_routers(...)                # 10ms
   c) init_global_scheduler(...)                  # 500ms
   d) metrics collectors                          # 100ms
   e) event_bus subscriptions                     # 50ms
```

### Lifespan Hook (main.py:136-230)

**On Startup** (yield before):
```python
await _init_database_pool(app)          # Connect to PostgreSQL
set_db_pool_for_routers(app.state.db_pool)
await init_global_scheduler(...)        # APScheduler
get_rpa_metrics()
MetricsAggregator.get_instance()
event_bus.subscribe(MonitoringEventType.*, handlers)
```

**On Shutdown** (after yield):
```python
event_bus.unsubscribe(...)
await shutdown_global_scheduler()
await _shutdown_database_pool(app)
```

### Database Pool Init (main.py:79-118)

```python
db_enabled = os.getenv("DB_ENABLED", "true")
if db_enabled:
    pool_manager = get_pool_manager()
    pool = await pool_manager.create_pool()  # ← 2-5 seconds
    app.state.db_pool = pool
else:
    # Degraded mode (no database)
    app.state.db_pool = None
```

### Health Checks
- `/health` - Basic (no dependencies)
- `/health/detailed` - DB + scheduler status
- `/health/ready` - Kubernetes readiness probe
- `/health/live` - Kubernetes liveness probe

---

## Import Chain (Critical Paths)

### Canvas Cold Imports
```
PySide6.QtGui                   → QFont patch
PySide6.QtWidgets               → QApplication, MainWindow
qasync                          → QEventLoop integration
loguru                          → Logger
casare_rpa.config               → setup_logging()
casare_rpa.presentation.canvas  → app.py, main_window.py, node_graph_widget.py
```

### Canvas Lazy Imports (After window shows)
```
casare_rpa.presentation.canvas.graph.node_registry   → register_essential_nodes()
casare_rpa.presentation.canvas.graph.icon_atlas      → preload icons (background)
casare_rpa.presentation.canvas.serialization.*       → Serializers
casare_rpa.presentation.canvas.execution.*           → Workflow runner
casare_rpa.utils.playwright_setup                    → On first browser node use
```

### Heavy Imports (Deferred)
```
playwright              → ~50MB (first browser node)
litellm                 → ~10MB (first AI node)
google-auth             → ~5MB (first Google node)
All 400 visual nodes    → ~50MB (Phase 6 deferred)
```

---

## Performance Concerns Summary

| Issue | Location | Impact | Status |
|-------|----------|--------|--------|
| QFont monkeypatch (duplicate) | __main__.py + app.py lines 6-26 | Fragile pattern | ⚠️ Consider consolidating |
| Playwright sync check (Robot) | robot/cli.py:160-253 | 5-10s startup | ⚠️ Make async |
| Window shown before init | app.py:184 | Positive | ✅ Already optimized |
| Node registry Phase 6 | app.py:346 | 100-200ms deferred | ✅ OK (deferred) |
| Icon preloading | app.py:293 | Non-blocking | ✅ Background thread |
| Database pool (Orchestrator) | api/main.py:104 | 2-5s | ✅ Degraded mode fallback |
| Sequential controller init | app.py:316-331 | ~250ms | ⚠️ Could parallelize |

---

## Startup Timeline (Canvas)

```
0ms    ├─ manage.py
       ├─ cli/main.py
20ms   ├─ canvas/__main__.py
30ms   ├─ QFont patch
70ms   ├─ setup_logging()
100ms  ├─ Qt: QApplication
       ├─ Qt: qasync QEventLoop
180ms  ├─ MainWindow creation
       ├─ NodeGraphWidget
300ms  ├─ Serializer creation
400ms  ├─ WINDOW DISPLAYED ← User sees this
       ├─ NodeController (8 essential nodes)
480ms  ├─ Other controllers (workflow, execution, selector, prefs, autosave)
500ms  ├─ Icon preload starts (background)
580ms  ├─ Complete node registration (100ms timer)
700ms  ├─ Signal connections
800ms  └─ Application fully ready

Perceived wait: 400ms (window shown)
Full ready: 800ms
```

---

## Quick Performance Tweaks

### Easy (< 30 min)
1. Consolidate QFont patch to one location
2. Move icon preloading to thread pool
3. Add startup progress logging

### Medium (1-2 hours)
1. Convert Playwright check to async for Robot
2. Parallelize controller initialization
3. Lazy-load large node categories (desktop, browser, google)

### Hard (2-4 hours)
1. Split visual nodes by category (load on demand)
2. Use background thread for Phase 6 node registration
3. Implement incremental graph loading
4. Add progress bar with estimated completion
