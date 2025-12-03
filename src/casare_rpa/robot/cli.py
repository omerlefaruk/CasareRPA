"""
CasareRPA Robot CLI

Command-line interface for managing the Robot Agent.

Commands:
    start   - Start the robot agent
    stop    - Gracefully stop a running robot by ID
    status  - Show robot status and current jobs
    logs    - View robot logs
    config  - Show or generate configuration

Usage:
    python -m casare_rpa.robot.cli start
    python -m casare_rpa.robot.cli start --name "Production-Bot" --env production
    python -m casare_rpa.robot.cli stop --robot-id worker-01
    python -m casare_rpa.robot.cli stop --robot-id worker-01 --force
    python -m casare_rpa.robot.cli status
    python -m casare_rpa.robot.cli status --json
    python -m casare_rpa.robot.cli logs --robot-id worker-01 --tail 50
    python -m casare_rpa.robot.cli config --generate > config.yaml
"""

from __future__ import annotations

import asyncio
import os
import signal
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

# Suppress Qt DPI awareness warning - must be set before Qt imports.
os.environ.setdefault("QT_LOGGING_RULES", "qt.qpa.window=false")

import typer
from dotenv import load_dotenv
from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.text import Text

# Load environment variables from multiple locations
# Priority (highest to lowest):
# 1. Install directory (.env next to executable) - for frozen apps
# 2. AppData/CasareRPA/.env (Windows installer location)
# 3. Current working directory (.env)

# For frozen apps (PyInstaller exe), load from exe directory FIRST with override=True
if getattr(sys, "frozen", False):
    _exe_dir = Path(sys.executable).parent
    _exe_env = _exe_dir / ".env"
    if _exe_env.exists():
        load_dotenv(_exe_env, override=True)  # Override any system env vars

# Try AppData location (Windows installer) - override=True for installed robots
_appdata = os.getenv("APPDATA")
if _appdata:
    _appdata_env = Path(_appdata) / "CasareRPA" / ".env"
    if _appdata_env.exists():
        load_dotenv(_appdata_env, override=True)  # Override system env vars

# Development: current directory (won't override if already set)
load_dotenv()  # Current directory last, won't override


app = typer.Typer(
    name="robot",
    help="CasareRPA Robot Agent CLI - Distributed workflow execution",
    add_completion=False,
    no_args_is_help=True,
)

console = Console()


class RobotCLIState:
    """
    Thread-safe state management for robot CLI.

    Encapsulates the shutdown event and agent reference
    that were previously global variables.
    """

    def __init__(self) -> None:
        """Initialize CLI state."""
        import threading

        self._shutdown_event: Optional[asyncio.Event] = None
        self._agent: Optional[Any] = None
        self._lock = threading.Lock()

    @property
    def shutdown_event(self) -> Optional[asyncio.Event]:
        """Get the shutdown event."""
        return self._shutdown_event

    @shutdown_event.setter
    def shutdown_event(self, event: Optional[asyncio.Event]) -> None:
        """Set the shutdown event."""
        with self._lock:
            self._shutdown_event = event

    @property
    def agent(self) -> Optional[Any]:
        """Get the robot agent."""
        return self._agent

    @agent.setter
    def agent(self, agent: Optional[Any]) -> None:
        """Set the robot agent."""
        with self._lock:
            self._agent = agent

    def trigger_shutdown(self) -> None:
        """Trigger the shutdown event if set."""
        event = self._shutdown_event
        if event:
            event.set()


# Module-level CLI state singleton
_cli_state = RobotCLIState()


def _get_postgres_url() -> str:
    """
    Build PostgreSQL connection URL from environment variables.

    For frozen apps (installed exe), returns empty string and the
    RobotAgent will fetch credentials from Supabase Vault at runtime.
    """
    url = (
        os.getenv("PGQUEUER_DB_URL")
        or os.getenv("DATABASE_URL")
        or os.getenv("POSTGRES_URL")
    )
    if url:
        return url

    # For frozen apps, return empty - agent.py will fetch from Vault
    if getattr(sys, "frozen", False):
        return ""

    # Development mode: build from individual env vars
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    name = os.getenv("DB_NAME", "casare_rpa")
    user = os.getenv("DB_USER", "casare_user")
    password = os.getenv("DB_PASSWORD", "")

    if not password:
        console.print("[yellow]Warning: DB_PASSWORD not set in environment[/yellow]")

    return f"postgresql://{user}:{password}@{host}:{port}/{name}"


def _ensure_playwright_browsers() -> bool:
    """Check if Playwright browsers are installed, auto-install if missing."""
    import shutil
    import subprocess

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        console.print(
            "[red]Playwright module not installed. Run: pip install playwright[/red]"
        )
        return False

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            browser.close()
        return True

    except Exception as e:
        error_msg = str(e)
        if "Executable doesn't exist" in error_msg or "playwright install" in error_msg:
            console.print(
                "[yellow]Playwright browsers not found. Installing automatically...[/yellow]"
            )
            try:
                is_frozen = getattr(sys, "frozen", False)

                if is_frozen:
                    playwright_cli = shutil.which("playwright")
                    if playwright_cli:
                        result = subprocess.run(
                            [playwright_cli, "install", "chromium"],
                            capture_output=True,
                            text=True,
                            timeout=300,
                        )
                    else:
                        for py_path in ["python", "python3", "py"]:
                            if shutil.which(py_path):
                                result = subprocess.run(
                                    [
                                        py_path,
                                        "-m",
                                        "playwright",
                                        "install",
                                        "chromium",
                                    ],
                                    capture_output=True,
                                    text=True,
                                    timeout=300,
                                )
                                break
                        else:
                            console.print(
                                "[yellow]Cannot auto-install browsers in packaged mode.[/yellow]"
                            )
                            console.print(
                                "[yellow]Please run: playwright install chromium[/yellow]"
                            )
                            return False
                else:
                    result = subprocess.run(
                        [sys.executable, "-m", "playwright", "install", "chromium"],
                        capture_output=True,
                        text=True,
                        timeout=300,
                    )

                if result.returncode == 0:
                    console.print(
                        "[green]Playwright browsers installed successfully![/green]"
                    )
                    return True
                else:
                    stderr_preview = (
                        result.stderr[:200] + "..."
                        if len(result.stderr) > 200
                        else result.stderr
                    )
                    console.print(
                        f"[red]Failed to install browsers: {stderr_preview}[/red]"
                    )
                    logger.error(f"Full Playwright install error: {result.stderr}")
                    return False
            except subprocess.TimeoutExpired:
                console.print("[red]Browser installation timed out[/red]")
                return False
            except Exception as install_error:
                console.print(f"[red]Failed to install browsers: {install_error}[/red]")
                return False
        else:
            logger.warning(f"Playwright check failed: {e}")
            return True  # Continue anyway


def _get_pid_file(robot_id: str) -> Path:
    """Get PID file path for robot."""
    pid_dir = Path.home() / ".casare_rpa"
    pid_dir.mkdir(parents=True, exist_ok=True)
    return pid_dir / f"robot_{robot_id}.pid"


def _write_pid_file(robot_id: str) -> Path:
    """Write PID file for the running robot."""
    pid_file = _get_pid_file(robot_id)
    pid_file.write_text(str(os.getpid()))
    return pid_file


def _remove_pid_file(robot_id: str) -> None:
    """Remove PID file for the robot."""
    pid_file = _get_pid_file(robot_id)
    try:
        if pid_file.exists():
            pid_file.unlink()
    except OSError as e:
        logger.warning(f"Failed to remove PID file: {e}")


def _write_status_file(robot_id: str, status_data: dict) -> None:
    """Write status file for the robot."""
    import orjson

    status_dir = Path.home() / ".casare_rpa"
    status_dir.mkdir(parents=True, exist_ok=True)
    status_file = status_dir / f"robot_{robot_id}_status.json"
    try:
        status_file.write_bytes(orjson.dumps(status_data, option=orjson.OPT_INDENT_2))
    except OSError as e:
        logger.warning(f"Failed to write status file: {e}")


def _setup_signal_handlers(loop: asyncio.AbstractEventLoop) -> None:
    """Setup signal handlers for graceful shutdown."""
    _cli_state.shutdown_event = asyncio.Event()

    def signal_handler(signum: int, frame) -> None:
        sig_name = signal.Signals(signum).name
        logger.info(f"Received {sig_name}, initiating graceful shutdown...")
        console.print(f"\n[yellow]Received {sig_name}, shutting down...[/yellow]")

        loop.call_soon_threadsafe(_cli_state.trigger_shutdown)

    # Standard signals
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Windows-specific: CTRL+C and CTRL+BREAK
    if sys.platform == "win32":
        try:
            signal.signal(signal.SIGBREAK, signal_handler)
        except (AttributeError, ValueError):
            pass

        # Also register with Windows console
        try:
            import win32api

            def win32_handler(ctrl_type):
                if ctrl_type in (0, 1):  # CTRL+C or CTRL+BREAK
                    loop.call_soon_threadsafe(_cli_state.trigger_shutdown)
                    return True
                return False

            win32api.SetConsoleCtrlHandler(win32_handler, True)
        except ImportError:
            pass


async def _run_agent(
    postgres_url: str,
    robot_id: Optional[str] = None,
    robot_name: Optional[str] = None,
    environment: str = "default",
    max_concurrent_jobs: int = 1,
    poll_interval: float = 1.0,
    config_file: Optional[Path] = None,
    daemon: bool = False,
) -> int:
    """Run the unified robot agent."""

    from casare_rpa.robot.agent import RobotAgent, RobotConfig

    # Load config from file or build from args
    if config_file and config_file.exists():
        try:
            import yaml

            config_data = yaml.safe_load(config_file.read_text())
            config = RobotConfig.from_dict(config_data)
        except Exception as e:
            logger.error(f"Failed to load config file: {e}")
            config = RobotConfig.from_env()
    else:
        config = RobotConfig(
            robot_id=robot_id,
            robot_name=robot_name,
            postgres_url=postgres_url,
            environment=environment,
            max_concurrent_jobs=max_concurrent_jobs,
            poll_interval_seconds=poll_interval,
        )

    agent = RobotAgent(config)
    _cli_state.agent = agent

    # Write PID file
    pid_file = _write_pid_file(config.robot_id)
    logger.debug(f"PID file written: {pid_file}")

    try:
        await agent.start()

        # Update status file
        _write_status_file(config.robot_id, agent.get_status())

        # Wait for shutdown signal
        shutdown_event = _cli_state.shutdown_event
        if shutdown_event:
            await shutdown_event.wait()
            console.print("[yellow]Graceful shutdown in progress...[/yellow]")
            await agent.stop()
            console.print("[green]Robot agent stopped successfully.[/green]")

        return 0

    except asyncio.CancelledError:
        logger.info("Agent task cancelled")
        current_agent = _cli_state.agent
        if current_agent:
            await current_agent.stop()
        return 0
    except Exception as e:
        logger.exception(f"Agent error: {e}")
        console.print(f"[red]Error:[/red] {e}")
        return 1
    finally:
        _remove_pid_file(config.robot_id)
        _cli_state.agent = None


@app.command()
def start(
    robot_id: Optional[str] = typer.Option(
        None,
        "--robot-id",
        "-r",
        help="Robot ID (auto-generated if not specified)",
    ),
    robot_name: Optional[str] = typer.Option(
        None,
        "--name",
        "-n",
        help="Human-readable robot name",
    ),
    environment: str = typer.Option(
        "default",
        "--env",
        "-e",
        help="Environment/pool for job filtering (e.g., 'production', 'staging')",
    ),
    max_jobs: int = typer.Option(
        1,
        "--max-jobs",
        "-j",
        help="Maximum concurrent jobs",
    ),
    poll_interval: float = typer.Option(
        1.0,
        "--poll-interval",
        "-p",
        help="Seconds between job polls",
    ),
    config_file: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to configuration file (YAML)",
        exists=True,
        dir_okay=False,
    ),
    daemon: bool = typer.Option(
        False,
        "--daemon",
        "-d",
        help="Run in background (daemon mode)",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose logging",
    ),
) -> None:
    """
    Start the robot agent.

    The agent connects to PostgreSQL and processes jobs from the queue.
    Configure database connection via environment variables:

    - POSTGRES_URL or DATABASE_URL: Full PostgreSQL URL
    - Or individual: DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

    Supports graceful shutdown via SIGTERM, SIGINT (Ctrl+C), or CTRL+BREAK.

    Examples:
        casare robot start
        casare robot start --name "Prod-Bot-01" --env production --max-jobs 3
        casare robot start --config robot_config.yaml
        casare robot start --daemon
    """
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

    # For frozen apps, empty URL is OK - agent.py will build from DB_PASSWORD
    is_frozen = getattr(sys, "frozen", False)

    if not is_frozen and (not postgres_url or "://:@" in postgres_url):
        console.print("[red]Error: Database connection not configured.[/red]")
        console.print("\nSet environment variables in .env file:")
        console.print("  DB_HOST=localhost")
        console.print("  DB_PORT=5432")
        console.print("  DB_NAME=casare_rpa")
        console.print("  DB_USER=casare_user")
        console.print("  DB_PASSWORD=your_password")
        console.print("\nOr set POSTGRES_URL/DATABASE_URL directly.")
        raise typer.Exit(code=1)

    if is_frozen and not postgres_url:
        console.print(
            "[dim]Frozen app: Database URL will be built from DB_PASSWORD[/dim]"
        )

    # Daemon mode
    if daemon:
        console.print(
            "[yellow]Daemon mode not yet implemented on this platform.[/yellow]"
        )
        console.print("Use a process manager like nssm or start as Windows Service.")
        raise typer.Exit(code=1)

    # Check Playwright
    console.print("[dim]Checking Playwright browsers...[/dim]")
    _ensure_playwright_browsers()

    # Generate robot ID/name if not provided
    import socket
    import uuid

    actual_robot_id = robot_id or f"robot-{socket.gethostname()}-{uuid.uuid4().hex[:8]}"
    actual_robot_name = robot_name or f"Robot-{socket.gethostname()}"

    # Display startup info
    console.print(
        Panel(
            f"[bold]Robot ID:[/bold] {actual_robot_id}\n"
            f"[bold]Name:[/bold] {actual_robot_name}\n"
            f"[bold]Environment:[/bold] {environment}\n"
            f"[bold]Max Concurrent Jobs:[/bold] {max_jobs}\n"
            f"[bold]Poll Interval:[/bold] {poll_interval}s\n"
            f"[bold]Config File:[/bold] {config_file or 'N/A'}",
            title="CasareRPA Robot Agent",
            border_style="blue",
        )
    )

    # Setup event loop and signal handlers
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    _setup_signal_handlers(loop)

    console.print("[green]Starting robot agent...[/green]")
    console.print("[dim]Press Ctrl+C to stop[/dim]\n")

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


@app.command()
def stop(
    robot_id: str = typer.Option(
        ...,
        "--robot-id",
        "-r",
        help="Robot ID to stop",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force immediate shutdown (skip grace period)",
    ),
    timeout: int = typer.Option(
        60,
        "--timeout",
        "-t",
        help="Seconds to wait for graceful shutdown",
    ),
) -> None:
    """
    Stop a running robot agent.

    Sends a shutdown signal to the specified robot. The robot will complete
    any currently running jobs before shutting down, unless --force is used.

    Examples:
        casare robot stop --robot-id robot-hostname-abc12345
        casare robot stop --robot-id robot-hostname-abc12345 --force
        casare robot stop -r robot-hostname-abc12345 --timeout 120
    """
    console.print(f"[yellow]Requesting shutdown for robot: {robot_id}[/yellow]")

    pid_file = _get_pid_file(robot_id)

    if not pid_file.exists():
        console.print(
            f"[red]Error:[/red] No PID file found for robot '{robot_id}'.\n"
            f"Expected: {pid_file}"
        )
        raise typer.Exit(code=1)

    try:
        pid = int(pid_file.read_text().strip())
    except (ValueError, OSError) as e:
        console.print(f"[red]Error:[/red] Invalid PID file: {e}")
        raise typer.Exit(code=1)

    try:
        import psutil

        try:
            process = psutil.Process(pid)
        except psutil.NoSuchProcess:
            console.print(f"[yellow]Warning:[/yellow] Process {pid} not found.")
            pid_file.unlink(missing_ok=True)
            raise typer.Exit(code=0)

        if force:
            console.print(f"[yellow]Force killing process {pid}...[/yellow]")
            process.kill()
        else:
            console.print(
                f"[yellow]Sending terminate signal to process {pid}...[/yellow]"
            )
            process.terminate()

            # Wait for graceful shutdown
            try:
                process.wait(timeout=timeout)
                console.print(
                    f"[green]Robot '{robot_id}' stopped successfully.[/green]"
                )
            except psutil.TimeoutExpired:
                console.print("[yellow]Timeout waiting for graceful shutdown.[/yellow]")
                if typer.confirm("Force kill the process?"):
                    process.kill()
                    console.print(f"[green]Robot '{robot_id}' killed.[/green]")
                else:
                    console.print("[yellow]Process still running.[/yellow]")
                    raise typer.Exit(code=1)

    except ImportError:
        # Fallback without psutil
        if force:
            console.print(f"[yellow]Sending SIGKILL to process {pid}...[/yellow]")
            if sys.platform == "win32":
                os.kill(pid, signal.SIGTERM)
            else:
                os.kill(pid, signal.SIGKILL)
        else:
            console.print(f"[yellow]Sending SIGTERM to process {pid}...[/yellow]")
            os.kill(pid, signal.SIGTERM)

        console.print(
            f"[green]Shutdown signal sent to robot '{robot_id}' (PID: {pid})[/green]"
        )

    except ProcessLookupError:
        console.print(
            f"[yellow]Warning:[/yellow] Process {pid} not found. "
            "Robot may have already stopped."
        )
        pid_file.unlink(missing_ok=True)
        raise typer.Exit(code=0)
    except PermissionError:
        console.print(
            f"[red]Error:[/red] Permission denied when sending signal to process {pid}."
        )
        raise typer.Exit(code=1)


@app.command()
def status(
    robot_id: Optional[str] = typer.Option(
        None,
        "--robot-id",
        "-r",
        help="Show status for specific robot",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output status as JSON",
    ),
    watch: bool = typer.Option(
        False,
        "--watch",
        "-w",
        help="Continuously watch status updates",
    ),
) -> None:
    """
    Show robot status and current jobs.

    Displays the current state of the robot agent including connection status,
    running jobs, and resource metrics.

    Examples:
        casare robot status
        casare robot status --robot-id worker-01
        casare robot status --json
        casare robot status --watch
    """
    import orjson
    import socket

    target_robot_id = robot_id or f"robot-{socket.gethostname()}"

    def get_status_data() -> dict:
        pid_file = _get_pid_file(target_robot_id)
        status_file = (
            Path.home() / ".casare_rpa" / f"robot_{target_robot_id}_status.json"
        )

        status_data = {
            "robot_id": target_robot_id,
            "running": False,
            "pid": None,
            "state": "stopped",
            "environment": "unknown",
            "jobs": {"running": 0, "completed": 0, "failed": 0},
        }

        # Check if process is running
        if pid_file.exists():
            try:
                pid = int(pid_file.read_text().strip())
                import psutil

                try:
                    process = psutil.Process(pid)
                    if process.is_running():
                        status_data["running"] = True
                        status_data["pid"] = pid
                        status_data["process"] = {
                            "cpu_percent": process.cpu_percent(),
                            "memory_mb": round(
                                process.memory_info().rss / (1024 * 1024), 2
                            ),
                            "uptime_seconds": int(
                                (
                                    datetime.now(timezone.utc)
                                    - datetime.fromtimestamp(
                                        process.create_time(), timezone.utc
                                    )
                                ).total_seconds()
                            ),
                        }
                except psutil.NoSuchProcess:
                    pid_file.unlink(missing_ok=True)
            except (ValueError, OSError, ImportError):
                pass

        # Load cached status
        if status_file.exists():
            try:
                cached = orjson.loads(status_file.read_bytes())
                status_data.update(cached)
            except (OSError, orjson.JSONDecodeError):
                pass

        return status_data

    if json_output:
        status_data = get_status_data()
        console.print(orjson.dumps(status_data, option=orjson.OPT_INDENT_2).decode())
        return

    def render_status():
        status_data = get_status_data()

        running_status = (
            "[green]Running[/green]" if status_data["running"] else "[red]Stopped[/red]"
        )

        table = Table(
            title=f"Robot Status: {status_data['robot_id']}", border_style="blue"
        )
        table.add_column("Property", style="bold")
        table.add_column("Value")

        table.add_row("Status", running_status)
        table.add_row("State", status_data.get("state", "unknown"))
        table.add_row("PID", str(status_data.get("pid", "N/A")))
        table.add_row("Environment", status_data.get("environment", "unknown"))

        if status_data.get("process"):
            proc = status_data["process"]
            table.add_row("CPU", f"{proc.get('cpu_percent', 0):.1f}%")
            table.add_row("Memory", f"{proc.get('memory_mb', 0):.1f} MB")
            uptime = proc.get("uptime_seconds", 0)
            table.add_row("Uptime", str(timedelta(seconds=uptime)))

        if status_data.get("stats"):
            stats = status_data["stats"]
            table.add_row("Jobs Completed", str(stats.get("jobs_completed", 0)))
            table.add_row("Jobs Failed", str(stats.get("jobs_failed", 0)))

        return table

    if watch:
        try:
            with Live(render_status(), refresh_per_second=1, console=console) as live:
                while True:
                    live.update(render_status())
                    import time

                    time.sleep(1)
        except KeyboardInterrupt:
            pass
    else:
        console.print(render_status())


@app.command()
def logs(
    robot_id: Optional[str] = typer.Option(
        None,
        "--robot-id",
        "-r",
        help="Robot ID to view logs for",
    ),
    tail: int = typer.Option(
        50,
        "--tail",
        "-n",
        help="Number of lines to show",
    ),
    follow: bool = typer.Option(
        False,
        "--follow",
        "-f",
        help="Follow log output (like tail -f)",
    ),
    level: str = typer.Option(
        "INFO",
        "--level",
        "-l",
        help="Minimum log level to show (DEBUG, INFO, WARNING, ERROR)",
    ),
    audit: bool = typer.Option(
        False,
        "--audit",
        "-a",
        help="Show audit logs instead of standard logs",
    ),
) -> None:
    """
    View robot logs.

    Shows recent log entries for the specified robot. Can follow logs
    in real-time or show audit trail.

    Examples:
        casare robot logs --tail 100
        casare robot logs --follow
        casare robot logs --audit --tail 50
        casare robot logs --level ERROR
    """
    import socket

    target_robot_id = robot_id or f"robot-{socket.gethostname()}"
    log_dir = Path.home() / ".casare_rpa" / "logs"

    if audit:
        log_dir = log_dir / "audit"
        pattern = "audit_*.jsonl"
    else:
        pattern = "robot_*.log"

    if not log_dir.exists():
        console.print(f"[yellow]No log directory found at {log_dir}[/yellow]")
        raise typer.Exit(code=0)

    # Find most recent log file
    log_files = sorted(
        log_dir.glob(pattern), key=lambda f: f.stat().st_mtime, reverse=True
    )

    if not log_files:
        console.print(f"[yellow]No log files found in {log_dir}[/yellow]")
        raise typer.Exit(code=0)

    log_file = log_files[0]
    console.print(f"[dim]Reading from: {log_file}[/dim]\n")

    level_priority = {"DEBUG": 0, "INFO": 1, "WARNING": 2, "ERROR": 3, "CRITICAL": 4}
    min_level = level_priority.get(level.upper(), 1)

    def should_show_line(line: str) -> bool:
        """Check if log line meets minimum level."""
        for lvl, priority in level_priority.items():
            if lvl in line and priority >= min_level:
                return True
        return min_level == 0  # Show all if DEBUG

    if follow:
        import time

        try:
            with open(log_file, "r") as f:
                # Show last N lines first
                lines = f.readlines()
                for line in lines[-tail:]:
                    if should_show_line(line):
                        console.print(line.rstrip())

                # Follow new lines
                console.print("\n[dim]Following log output (Ctrl+C to stop)...[/dim]\n")
                while True:
                    line = f.readline()
                    if line:
                        if should_show_line(line):
                            console.print(line.rstrip())
                    else:
                        time.sleep(0.1)
        except KeyboardInterrupt:
            pass
    else:
        try:
            with open(log_file, "r") as f:
                lines = f.readlines()
                for line in lines[-tail:]:
                    if should_show_line(line):
                        console.print(line.rstrip())
        except Exception as e:
            console.print(f"[red]Error reading log file: {e}[/red]")
            raise typer.Exit(code=1)


@app.command()
def config(
    generate: bool = typer.Option(
        False,
        "--generate",
        "-g",
        help="Generate sample configuration file",
    ),
    show: bool = typer.Option(
        False,
        "--show",
        "-s",
        help="Show current configuration (from env)",
    ),
) -> None:
    """
    Show or generate robot configuration.

    Examples:
        casare robot config --generate > robot_config.yaml
        casare robot config --show
    """
    import yaml

    if generate:
        sample_config = {
            "robot_id": None,  # Auto-generated
            "robot_name": "My-Robot",
            "environment": "production",
            "max_concurrent_jobs": 1,
            "poll_interval_seconds": 1.0,
            "heartbeat_interval_seconds": 10.0,
            "graceful_shutdown_seconds": 60,
            "enable_checkpointing": True,
            "enable_circuit_breaker": True,
            "enable_audit_logging": True,
            "browser_pool_size": 5,
            "db_pool_size": 10,
            "http_pool_size": 20,
            "circuit_breaker": {
                "failure_threshold": 5,
                "success_threshold": 2,
                "timeout": 60.0,
                "half_open_max_calls": 3,
            },
            "tags": ["windows", "browser", "desktop"],
        }
        print(yaml.dump(sample_config, default_flow_style=False, sort_keys=False))

    elif show:
        from casare_rpa.robot.agent import RobotConfig

        config = RobotConfig.from_env()
        console.print(
            Panel(
                yaml.dump(config.to_dict(), default_flow_style=False),
                title="Current Configuration",
                border_style="blue",
            )
        )
    else:
        console.print(
            "Use --generate to create sample config or --show to view current."
        )


def main() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
