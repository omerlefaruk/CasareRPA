# CasareRPA Startup - Code Snippets & Key Sections

## Canvas Entry Point

### File: `manage.py` (Root)
```python
#!/usr/bin/env python
"""CasareRPA Unified Management Script."""

import sys
from pathlib import Path

# Add src to path to ensure imports work
sys.path.insert(0, str(Path(__file__).parent / "src"))

from casare_rpa.cli.main import app

if __name__ == "__main__":
    app()  # Typer CLI dispatcher
```

### File: `src/casare_rpa/cli/main.py`
```python
# Relevant sections:
# Lines 17-24: Create Typer app and add subcommands
app = typer.Typer(name="casare", help="CasareRPA Unified CLI")
app.add_typer(robot_app, name="robot")
app.add_typer(orchestrator_app, name="orchestrator")

# Lines 66-82: Canvas command
@app.command("canvas")
def start_canvas():
    """Start the Canvas Designer (GUI)."""
    from casare_rpa.presentation.canvas import main
    sys.exit(main())
```

### File: `src/casare_rpa/presentation/canvas/__main__.py`
```python
"""Entry point for running canvas as module."""

import sys

# Apply QFont fix BEFORE any Qt imports
from PySide6.QtGui import QFont

_original_setPointSize = QFont.setPointSize

def _safe_setPointSize(self, size: int) -> None:
    if size <= 0:
        size = 9
    _original_setPointSize(self, size)

QFont.setPointSize = _safe_setPointSize

from casare_rpa.presentation.canvas.app import main

if __name__ == "__main__":
    sys.exit(main())
```

---

## Canvas Main App Class

### File: `src/casare_rpa/presentation/canvas/app.py`

#### Module-Level Setup
```python
# Lines 5-31: Module setup
import sys
import asyncio
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, qInstallMessageHandler, QtMsgType
from qasync import QEventLoop
from loguru import logger

# QFont fix (duplicate of __main__.py - DUPLICATION ISSUE)
_original_setPointSize = QFont.setPointSize
def _safe_setPointSize(self, size: int) -> None:
    if size <= 0:
        size = 9
    _original_setPointSize(self, size)
QFont.setPointSize = _safe_setPointSize

# Lines 34-70: Qt message handler (suppress CSS warnings)
_SUPPRESSED_PATTERNS = (
    "Unknown property box-shadow",
    "Unknown property text-shadow",
)

def _qt_message_handler(msg_type: QtMsgType, context, message: str) -> None:
    """Suppress known harmless warnings."""
    if any(pattern in message for pattern in _SUPPRESSED_PATTERNS):
        return
    # Otherwise log at appropriate level
    if msg_type == QtMsgType.QtDebugMsg:
        logger.debug(f"[Qt] {message}")
    # ... etc
```

#### CasareRPAApp.__init__() - Full Initialization
```python
# Lines 164-200: Full initialization sequence
def __init__(self) -> None:
    """Initialize the application."""
    global _app_instance
    _app_instance = self

    # PHASE 1: Setup logging
    setup_logging()

    # PHASE 2: Setup Qt application
    self._setup_qt_application()

    # PHASE 3: Create UI
    self._create_ui()

    # OPTIMIZATION: Show window BEFORE heavy initialization
    self._main_window.setWindowTitle(f"{APP_NAME} - Loading...")
    self._main_window.show()
    self._app.processEvents()  # Force display

    # PHASE 4: Initialize components
    self._initialize_components()

    # PHASE 5: Connect signals
    self._connect_components()
    self._connect_ui_signals()

    # Restore window title
    self._main_window.setWindowTitle(APP_NAME)
```

#### Phase 2: Qt Setup
```python
# Lines 202-223
def _setup_qt_application(self) -> None:
    """Setup Qt application and event loop."""

    # Install custom message handler
    qInstallMessageHandler(_qt_message_handler)

    # Enable high-DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)

    # Create Qt application
    self._app = QApplication(sys.argv)
    self._app.setApplicationName(APP_NAME)

    # Create qasync event loop
    self._loop = QEventLoop(self._app)
    asyncio.set_event_loop(self._loop)

    # Connect aboutToQuit for async cleanup
    self._app.aboutToQuit.connect(self._on_about_to_quit)
```

#### Phase 3: UI Creation
```python
# Lines 225-261
def _create_ui(self) -> None:
    """Create main window and central widget."""

    # Create main window
    self._main_window = MainWindow()

    # Create node graph widget
    self._node_graph = NodeGraphWidget()

    # Set as central widget
    self._main_window.set_central_widget(self._node_graph)

    # Create serializers (lazy imports inside function)
    from .serialization.workflow_serializer import WorkflowSerializer
    from .serialization.workflow_deserializer import WorkflowDeserializer
    from .execution.canvas_workflow_runner import CanvasWorkflowRunner

    self._serializer = WorkflowSerializer(
        self._node_graph.graph,
        self._main_window,
    )

    self._deserializer = WorkflowDeserializer(
        self._node_graph.graph,
        self._main_window,
    )

    # Set data provider
    self._main_window.set_workflow_data_provider(self._serializer.serialize)

    # Create workflow runner
    from casare_rpa.domain.events import get_event_bus

    self._workflow_runner = CanvasWorkflowRunner(
        self._serializer, get_event_bus(), self._main_window
    )

    logger.debug("Workflow serializer and runner initialized")
```

#### Phase 4: Component Initialization (Two-Phase)
```python
# Lines 263-346
def _initialize_components(self) -> None:
    """Initialize all controllers in dependency order."""
    from PySide6.QtCore import QTimer

    # PHASE 4A: Node registry (essential nodes only)
    self._node_controller = NodeController(self._main_window)
    self._node_controller.initialize()
    logger.debug("Essential nodes registered")

    # Defer icon preloading to background
    QTimer.singleShot(500, self._preload_icons_background)

    # PHASE 4B: All other controllers
    logger.debug("Phase 2: Initializing application controllers...")

    self._workflow_controller = WorkflowController(self._main_window)
    self._execution_controller = ExecutionController(self._main_window)
    self._selector_controller = SelectorController(self._main_window)
    self._preferences_controller = PreferencesController(self._main_window)
    self._autosave_controller = AutosaveController(self._main_window)

    phase_2_controllers = [
        self._workflow_controller,
        self._execution_controller,
        self._selector_controller,
        self._preferences_controller,
        self._autosave_controller,
    ]

    for controller in phase_2_controllers:
        try:
            controller.initialize()
            logger.debug(f"{controller.__class__.__name__} initialized")
        except Exception as e:
            error_msg = f"Failed to initialize {controller.__class__.__name__}: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    # Configure execution controller
    self._execution_controller.set_workflow_runner(self._workflow_runner)

    # Inject controllers into MainWindow
    self._main_window.set_controllers(
        workflow_controller=self._workflow_controller,
        execution_controller=self._execution_controller,
        node_controller=self._node_controller,
        selector_controller=self._selector_controller,
    )

    # Defer full node registration
    QTimer.singleShot(100, self._complete_deferred_initialization)
```

#### Deferred Operations (Background)
```python
# Lines 348-380
def _preload_icons_background(self) -> None:
    """Preload icons in background (non-blocking)."""
    try:
        from casare_rpa.presentation.canvas.graph.icon_atlas import (
            get_icon_atlas,
            preload_node_icons,
        )

        get_icon_atlas().initialize()
        preload_node_icons()
        logger.debug("Icon atlas preloaded in background")
    except Exception as e:
        logger.warning(f"Failed to preload icon atlas: {e}")

def _complete_deferred_initialization(self) -> None:
    """Complete deferred initialization after window is shown."""
    try:
        if hasattr(self._node_controller, "complete_node_registration"):
            self._node_controller.complete_node_registration()
            logger.info("Deferred node registration completed")
    except Exception as e:
        logger.error(f"Failed to complete deferred initialization: {e}")
```

#### Cleanup on Quit
```python
# Lines 1013-1056
def _on_about_to_quit(self) -> None:
    """Handle application quit - cleanup async resources."""
    logger.debug("Application about to quit - running async cleanup")

    try:
        from litellm.llms.custom_httpx.async_client_cleanup import (
            close_litellm_async_clients,
        )

        if self._loop.is_running():
            # Schedule cleanup and wait for it
            future = asyncio.run_coroutine_threadsafe(
                close_litellm_async_clients(), self._loop
            )
            try:
                future.result(timeout=2.0)
                logger.debug("litellm async clients cleaned up")
            except TimeoutError:
                logger.warning("litellm cleanup timed out")
            except Exception as e:
                logger.debug(f"litellm cleanup: {e}")
        else:
            # Event loop not running
            self._loop.run_until_complete(close_litellm_async_clients())
            logger.debug("litellm async clients cleaned up (sync)")

    except ImportError:
        logger.debug("litellm cleanup module not available - skipping")
    except Exception as e:
        logger.debug(f"litellm cleanup error (non-fatal): {e}")
```

#### Entry Point
```python
# Lines 1059-1071
def main() -> int:
    """Main entry point for the application."""
    app = CasareRPAApp()
    return app.run()

if __name__ == "__main__":
    sys.exit(main())
```

---

## Logging Setup

### File: `src/casare_rpa/config/logging_setup.py`
```python
"""CasareRPA Logging Configuration."""

import sys
from pathlib import Path
from typing import Final

from loguru import logger
from casare_rpa.config.paths import APP_NAME, APP_VERSION, LOGS_DIR

LOG_FILE_PATH: Final[Path] = LOGS_DIR / "casare_rpa_{time:YYYY-MM-DD}.log"
LOG_RETENTION: Final[str] = "30 days"
LOG_ROTATION: Final[str] = "500 MB"
LOG_LEVEL: Final[str] = "INFO"
LOG_FORMAT: Final[str] = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<level>{message}</level>"
)

def setup_logging() -> None:
    """Configure loguru logger with file rotation and formatting."""

    # Remove default handler
    logger.remove()

    # Add console handler (if stderr available)
    if sys.stderr:
        logger.add(
            sys.stderr,
            format=LOG_FORMAT,
            level=LOG_LEVEL,
            colorize=True,
            backtrace=True,
            diagnose=True,
        )

    # Add file handler with rotation
    logger.add(
        LOG_FILE_PATH,
        format=LOG_FORMAT,
        level=LOG_LEVEL,
        rotation=LOG_ROTATION,
        retention=LOG_RETENTION,
        compression="zip",
        backtrace=True,
        diagnose=True,
        enqueue=True,  # Thread-safe
    )

    logger.info(f"{APP_NAME} v{APP_VERSION} - Logging initialized")
    logger.info(f"Log file: {LOG_FILE_PATH}")
```

---

## Robot CLI Startup

### File: `src/casare_rpa/robot/__main__.py`
```python
"""Entry point for running robot CLI as a module."""

from casare_rpa.robot.cli import main

if __name__ == "__main__":
    main()
```

### File: `src/casare_rpa/robot/cli.py` (Key Sections)

#### Environment Loading
```python
# Lines 24-66
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Suppress Qt DPI warning - must be before Qt imports
os.environ.setdefault("QT_LOGGING_RULES", "qt.qpa.window=false")

# Load .env files (priority order)
# 1. Frozen app exe directory
if getattr(sys, "frozen", False):
    _exe_dir = Path(sys.executable).parent
    _exe_env = _exe_dir / ".env"
    if _exe_env.exists():
        load_dotenv(_exe_env, override=True)

# 2. AppData/CasareRPA
_appdata = os.getenv("APPDATA")
if _appdata:
    _appdata_env = Path(_appdata) / "CasareRPA" / ".env"
    if _appdata_env.exists():
        load_dotenv(_appdata_env, override=True)

# 3. Current directory (lowest priority)
load_dotenv()
```

#### Signal Handler Setup
```python
# Lines 293-327
def _setup_signal_handlers(loop: asyncio.AbstractEventLoop) -> None:
    """Setup signal handlers for graceful shutdown."""
    import signal

    _cli_state.shutdown_event = asyncio.Event()

    def signal_handler(signum: int, frame) -> None:
        sig_name = signal.Signals(signum).name
        logger.info(f"Received {sig_name}, initiating graceful shutdown...")
        loop.call_soon_threadsafe(_cli_state.trigger_shutdown)

    # Standard signals
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Windows-specific
    if sys.platform == "win32":
        try:
            signal.signal(signal.SIGBREAK, signal_handler)
        except (AttributeError, ValueError):
            pass
```

#### Playwright Browser Check
```python
# Lines 160-253 (PERFORMANCE CONCERN)
def _ensure_playwright_browsers() -> bool:
    """Check if Playwright browsers installed, auto-install if missing."""
    import shutil
    import subprocess

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        console.print("[red]Playwright module not installed[/red]")
        return False

    try:
        # HEAVY OPERATION: Synchronous browser launch
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            browser.close()
        return True

    except Exception as e:
        # Auto-install if missing
        error_msg = str(e)
        if "Executable doesn't exist" in error_msg or "playwright install" in error_msg:
            console.print("[yellow]Installing Playwright browsers automatically...[/yellow]")
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "playwright", "install", "chromium"],
                    capture_output=True,
                    text=True,
                    timeout=300,  # 5-minute timeout
                )
                if result.returncode == 0:
                    console.print("[green]Playwright browsers installed successfully![/green]")
                    return True
                else:
                    console.print(f"[red]Failed to install browsers: {result.stderr}[/red]")
                    return False
            except subprocess.TimeoutExpired:
                console.print("[red]Browser installation timed out[/red]")
                return False
```

#### Start Command
```python
# Lines 402-560
@app.command()
def start(
    robot_id: Optional[str] = typer.Option(...),
    robot_name: Optional[str] = typer.Option(...),
    environment: str = typer.Option("default", ...),
    max_jobs: int = typer.Option(1, ...),
    poll_interval: float = typer.Option(1.0, ...),
    config_file: Optional[Path] = typer.Option(None, ...),
    daemon: bool = typer.Option(False, ...),
    verbose: bool = typer.Option(False, ...),
) -> None:
    """Start the robot agent."""

    # Configure logging
    logger.remove()
    log_level = "DEBUG" if verbose else "INFO"
    logger.add(
        sys.stderr,
        level=log_level,
        format="<green>{time:HH:mm:ss}</green> | <level>{level:<8}</level> | {message}",
    )

    # Get PostgreSQL URL
    postgres_url = _get_postgres_url()

    # Playwright check
    console.print("[dim]Checking Playwright browsers...[/dim]")
    _ensure_playwright_browsers()

    # Generate robot ID if not provided
    import socket, uuid
    actual_robot_id = robot_id or f"robot-{socket.gethostname()}-{uuid.uuid4().hex[:8]}"
    actual_robot_name = robot_name or f"Robot-{socket.gethostname()}"

    # Setup event loop and signal handlers
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    _setup_signal_handlers(loop)

    # Run agent
    try:
        exit_code = loop.run_until_complete(
            _run_agent(
                postgres_url=postgres_url,
                robot_id=actual_robot_id,
                robot_name=actual_robot_name,
                environment=environment,
                max_concurrent_jobs=max_jobs,
                poll_interval=poll_interval,
                config_file=config_file,
                daemon=daemon,
            )
        )
    finally:
        loop.close()

    raise typer.Exit(code=exit_code)
```

---

## Orchestrator API Startup

### File: `src/casare_rpa/infrastructure/orchestrator/api/main.py` (Key Sections)

#### Environment Loading
```python
# Lines 14-29
import os
import time
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
project_root = Path(__file__).resolve().parents[5]
env_path = project_root / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"[API] Loaded .env from: {env_path}")
else:
    load_dotenv()  # Fallback
    print("[API] Using .env from current directory (fallback)")
```

#### Database Pool Initialization
```python
# Lines 79-118
async def _init_database_pool(app: FastAPI) -> Optional[DatabasePoolManager]:
    """Initialize database connection pool during startup."""

    db_enabled = os.getenv("DB_ENABLED", "true").lower() in ("true", "1", "yes")

    if not db_enabled:
        logger.info("Database disabled via DB_ENABLED=false")
        app.state.db_pool = None
        app.state.db_manager = None
        return None

    pool_manager = get_pool_manager()

    try:
        # HEAVY OPERATION: Create connection pool (2-5 seconds)
        pool = await pool_manager.create_pool()
        app.state.db_pool = pool
        app.state.db_manager = pool_manager
        logger.info("Database pool initialized")
        return pool_manager

    except RuntimeError as e:
        # Allows degraded mode
        logger.error(f"Database initialization failed: {e}. API will start in degraded mode.")
        app.state.db_pool = None
        app.state.db_manager = pool_manager
        return None
```

#### Lifespan Hook
```python
# Lines 136-230
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI app."""
    global _startup_time
    _startup_time = time.time()

    logger.info(f"Starting CasareRPA Monitoring API v{API_VERSION}")

    # Startup
    await _init_database_pool(app)

    if app.state.db_pool:
        # Set pool for routers
        from .routers.workflows import set_db_pool as set_workflows_db_pool
        from .routers.schedules import set_db_pool as set_schedules_db_pool
        from .routers.robots import set_db_pool as set_robots_db_pool
        from .routers.jobs import set_db_pool as set_jobs_db_pool

        set_workflows_db_pool(app.state.db_pool)
        set_schedules_db_pool(app.state.db_pool)
        set_robots_db_pool(app.state.db_pool)
        set_jobs_db_pool(app.state.db_pool)

    # Initialize APScheduler
    scheduler_initialized = False
    try:
        from casare_rpa.infrastructure.orchestrator.scheduling import (
            init_global_scheduler,
            shutdown_global_scheduler,
        )
        from .routers.schedules import _execute_scheduled_workflow

        await init_global_scheduler(
            on_schedule_trigger=_execute_scheduled_workflow,
            default_timezone="UTC",
        )
        scheduler_initialized = True
        logger.info("APScheduler initialized for schedule management")
    except Exception as e:
        logger.error(f"Failed to initialize APScheduler: {e}")

    app.state.scheduler_initialized = scheduler_initialized

    # Initialize metrics
    from casare_rpa.infrastructure.observability.metrics import (
        get_metrics_collector as get_rpa_metrics,
    )
    from casare_rpa.infrastructure.analytics.metrics_aggregator import MetricsAggregator

    rpa_metrics = get_rpa_metrics()
    analytics = MetricsAggregator.get_instance()

    # Subscribe event handlers
    event_bus = get_monitoring_event_bus()
    event_bus.subscribe(MonitoringEventType.JOB_STATUS_CHANGED, on_job_status_changed)
    event_bus.subscribe(MonitoringEventType.ROBOT_HEARTBEAT, on_robot_heartbeat)
    event_bus.subscribe(MonitoringEventType.QUEUE_DEPTH_CHANGED, on_queue_depth_changed)

    yield

    # Shutdown
    event_bus.unsubscribe(MonitoringEventType.JOB_STATUS_CHANGED, on_job_status_changed)
    event_bus.unsubscribe(MonitoringEventType.ROBOT_HEARTBEAT, on_robot_heartbeat)
    event_bus.unsubscribe(MonitoringEventType.QUEUE_DEPTH_CHANGED, on_queue_depth_changed)

    if getattr(app.state, "scheduler_initialized", False):
        try:
            from casare_rpa.infrastructure.orchestrator.scheduling import (
                shutdown_global_scheduler,
            )
            await shutdown_global_scheduler()
            logger.info("APScheduler shutdown complete")
        except Exception as e:
            logger.error(f"Error shutting down APScheduler: {e}")

    await _shutdown_database_pool(app)

    logger.info("Shutting down CasareRPA Monitoring API")
```

#### FastAPI App Creation
```python
# Lines 371-379
app = FastAPI(
    title="CasareRPA Monitoring API",
    description="Multi-robot fleet monitoring and analytics API",
    version=API_VERSION,
    lifespan=lifespan,
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    openapi_url="/api/v1/openapi.json",
)
```

#### Middleware Setup
```python
# Lines 381-423
# CORS (outermost)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Api-Key", "X-Request-ID", "X-Tenant-ID"],
    expose_headers=["X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining"],
)

# Request ID middleware
app.add_middleware(RequestIdMiddleware)

# Rate limiting
setup_rate_limiting(app)
```

#### Router Registration
```python
# Lines 440-486
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(metrics.router, prefix="/api/v1", tags=["Metrics"])
app.include_router(robots.router, prefix="/api/v1", tags=["Robots"])
app.include_router(jobs.router, prefix="/api/v1", tags=["Jobs"])
app.include_router(workflows.router, prefix="/api/v1", tags=["Workflows"])
app.include_router(schedules.router, prefix="/api/v1", tags=["Schedules"])
app.include_router(analytics.router, prefix="/api/v1", tags=["Analytics"])
app.include_router(dlq.router, prefix="/api/v1", tags=["Dead Letter Queue"])
app.include_router(websockets.router, prefix="/ws", tags=["WebSockets"])
```

---

## Node Controller Initialization

### File: `src/casare_rpa/presentation/canvas/controllers/node_controller.py`
```python
# Lines 50-79
def initialize(self) -> None:
    """Initialize controller."""
    super().initialize()
    # Initialize node registry
    self._initialize_node_registry()

def _initialize_node_registry(self) -> None:
    """Initialize node registry with essential nodes only."""
    try:
        from ..graph.node_registry import get_node_registry, get_casare_node_mapping

        # Get the graph
        graph = self._get_graph()
        if not graph:
            logger.warning("Graph not available for node registry initialization")
            return

        # Register essential nodes only (fast)
        node_registry = get_node_registry()
        node_registry.register_essential_nodes(graph)  # ~50ms, only ~8 nodes

        # Pre-build node mapping
        get_casare_node_mapping()

    except Exception as e:
        logger.error(f"Failed to initialize node registry: {e}", exc_info=True)
        raise
```

---

## Summary

### Key Performance Points

1. **Window shown early** (app.py:184) - User sees UI immediately at ~400ms
2. **Two-phase node registration** - Essential only at startup, full registry deferred
3. **Deferred imports** - Lazy loading of large modules (playwright, icons, nodes)
4. **Background operations** - QTimer for icon preload and deferred node registration
5. **Signal handling** - Proper cleanup on quit (litellm, event loop)

### Files to Monitor for Optimization

| File | Current Status | Could Improve |
|------|---|---|
| `app.py` | Good | Parallelize controller init |
| `__main__.py` | OK | Consolidate QFont patch |
| `robot/cli.py` | Slow | Async Playwright check |
| `api/main.py` | Good | Already has degraded mode |
| `node_controller.py` | Good | Consider background thread |
