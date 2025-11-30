"""
CasareRPA Robot CLI

Command-line interface for managing the Robot Agent.

Commands:
    start   - Start the robot agent with PostgreSQL backend
    stop    - Gracefully stop a running robot by ID
    status  - Show robot status and current jobs

Usage:
    python -m casare_rpa.robot.cli start
    python -m casare_rpa.robot.cli start --verbose
    python -m casare_rpa.robot.cli stop --robot-id worker-01
    python -m casare_rpa.robot.cli status
"""

import asyncio
import os
import signal
import sys
from pathlib import Path
from typing import Optional

# Suppress Qt DPI awareness warning (Playwright sets it first)
os.environ.setdefault("QT_LOGGING_RULES", "qt.qpa.window=false")

import typer
from dotenv import load_dotenv
from loguru import logger
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

# Load environment variables
load_dotenv()


app = typer.Typer(
    name="robot",
    help="CasareRPA Robot Agent CLI - Distributed workflow execution with PostgreSQL",
    add_completion=False,
)

console = Console()


# Global state for signal handling
_shutdown_event: Optional[asyncio.Event] = None
_agent = None


def _get_postgres_url() -> str:
    """
    Build PostgreSQL connection URL from environment variables.

    Returns:
        PostgreSQL connection string.
    """
    # Check for direct URL first
    url = (
        os.getenv("PGQUEUER_DB_URL")
        or os.getenv("DATABASE_URL")
        or os.getenv("POSTGRES_URL")
    )
    if url:
        return url

    # Build from individual components
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    name = os.getenv("DB_NAME", "casare_rpa")
    user = os.getenv("DB_USER", "casare_user")
    password = os.getenv("DB_PASSWORD", "")

    if not password:
        console.print("[yellow]Warning: DB_PASSWORD not set in environment[/yellow]")

    return f"postgresql://{user}:{password}@{host}:{port}/{name}"


def _ensure_playwright_browsers() -> bool:
    """
    Check if Playwright browsers are installed, auto-install if missing.

    Returns:
        True if browsers are available, False if installation failed.
    """
    import subprocess

    try:
        from playwright.sync_api import sync_playwright

        # Try to launch browser to check if binaries exist
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
                # Run playwright install chromium
                result = subprocess.run(
                    [sys.executable, "-m", "playwright", "install", "chromium"],
                    capture_output=True,
                    text=True,
                    timeout=300,  # 5 minute timeout for download
                )
                if result.returncode == 0:
                    console.print(
                        "[green]Playwright browsers installed successfully![/green]"
                    )
                    return True
                else:
                    console.print(
                        f"[red]Failed to install browsers: {result.stderr}[/red]"
                    )
                    return False
            except subprocess.TimeoutExpired:
                console.print("[red]Browser installation timed out[/red]")
                return False
            except Exception as install_error:
                console.print(f"[red]Failed to install browsers: {install_error}[/red]")
                return False
        else:
            # Some other Playwright error
            logger.warning(f"Playwright check failed: {e}")
            return True  # Continue anyway, might work for non-browser workflows


def _write_pid_file(robot_id: str) -> Path:
    """Write PID file for the running robot."""
    pid_dir = Path.home() / ".casare_rpa"
    pid_dir.mkdir(parents=True, exist_ok=True)
    pid_file = pid_dir / f"robot_{robot_id}.pid"
    pid_file.write_text(str(os.getpid()))
    return pid_file


def _remove_pid_file(robot_id: str) -> None:
    """Remove PID file for the robot."""
    pid_file = Path.home() / ".casare_rpa" / f"robot_{robot_id}.pid"
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
    global _shutdown_event
    _shutdown_event = asyncio.Event()

    def signal_handler(signum: int, frame) -> None:
        sig_name = signal.Signals(signum).name
        logger.info(f"Received {sig_name}, initiating graceful shutdown...")
        console.print(f"\n[yellow]Received {sig_name}, shutting down...[/yellow]")

        if _shutdown_event:
            loop.call_soon_threadsafe(_shutdown_event.set)

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    if sys.platform == "win32":
        try:
            signal.signal(signal.SIGBREAK, signal_handler)
        except (AttributeError, ValueError):
            pass


async def _run_agent(
    postgres_url: str,
    robot_id: Optional[str] = None,
    robot_name: Optional[str] = None,
    environment: str = "default",
    max_concurrent_jobs: int = 3,
    poll_interval: float = 1.0,
) -> int:
    """
    Run the distributed robot agent.

    Args:
        postgres_url: PostgreSQL connection string
        robot_id: Optional robot ID override
        robot_name: Optional robot name override
        environment: Environment/pool for job filtering
        max_concurrent_jobs: Maximum concurrent job executions
        poll_interval: Seconds between job polls

    Returns:
        Exit code (0 for success, 1 for error).
    """
    global _agent, _shutdown_event

    from .distributed_agent import DistributedRobotAgent, DistributedRobotConfig

    # Create configuration
    config = DistributedRobotConfig(
        robot_id=robot_id,
        robot_name=robot_name,
        postgres_url=postgres_url,
        environment=environment,
        max_concurrent_jobs=max_concurrent_jobs,
        poll_interval_seconds=poll_interval,
        enable_realtime=False,  # Disable Supabase Realtime
    )

    _agent = DistributedRobotAgent(config)

    # Write PID file
    pid_file = _write_pid_file(config.robot_id)
    logger.debug(f"PID file written: {pid_file}")

    try:
        # Start the agent
        await _agent.start()

        # Wait for shutdown signal
        if _shutdown_event:
            await _shutdown_event.wait()
            console.print("[yellow]Graceful shutdown in progress...[/yellow]")
            await _agent.stop()
            console.print("[green]Robot agent stopped successfully.[/green]")

        return 0

    except asyncio.CancelledError:
        logger.info("Agent task cancelled")
        if _agent:
            await _agent.stop()
        return 0
    except Exception as e:
        logger.exception(f"Agent error: {e}")
        console.print(f"[red]Error:[/red] {e}")
        return 1
    finally:
        _remove_pid_file(config.robot_id)
        _agent = None


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
        3,
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
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose logging",
    ),
) -> None:
    """
    Start the robot agent with PostgreSQL backend.

    The agent connects to PostgreSQL via PgQueuer for job queue management.
    Configure database connection via environment variables:

    - PGQUEUER_DB_URL: Full PostgreSQL URL
    - Or individual: DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

    Supports graceful shutdown via SIGTERM or SIGINT (Ctrl+C).
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

    if not postgres_url or "://:@" in postgres_url:
        console.print("[red]Error: Database connection not configured.[/red]")
        console.print("\nSet environment variables in .env file:")
        console.print("  DB_HOST=localhost")
        console.print("  DB_PORT=5432")
        console.print("  DB_NAME=casare_rpa")
        console.print("  DB_USER=casare_user")
        console.print("  DB_PASSWORD=your_password")
        console.print("\nOr set PGQUEUER_DB_URL directly.")
        raise typer.Exit(code=1)

    # Check and auto-install Playwright browsers if needed
    console.print("[dim]Checking Playwright browsers...[/dim]")
    _ensure_playwright_browsers()

    # Generate robot ID if not provided
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
            f"[bold]Database:[/bold] PostgreSQL (PgQueuer)",
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
) -> None:
    """
    Stop a running robot agent.

    Sends a shutdown signal to the specified robot. The robot will complete
    any currently running jobs before shutting down, unless --force is used.
    """
    console.print(f"[yellow]Requesting shutdown for robot: {robot_id}[/yellow]")

    pid_file = Path.home() / ".casare_rpa" / f"robot_{robot_id}.pid"

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
        if force:
            console.print(f"[yellow]Sending SIGKILL to process {pid}...[/yellow]")
            if sys.platform == "win32":
                import psutil

                try:
                    proc = psutil.Process(pid)
                    proc.kill()
                except psutil.NoSuchProcess:
                    console.print(f"[yellow]Warning:[/yellow] Process {pid} not found.")
                    pid_file.unlink(missing_ok=True)
                    raise typer.Exit(code=0)
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
        try:
            pid_file.unlink()
        except OSError:
            pass
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
) -> None:
    """
    Show robot status and current jobs.

    Displays the current state of the robot agent including connection status,
    running jobs, and resource metrics.
    """
    import orjson
    import socket

    target_robot_id = robot_id or f"robot-{socket.gethostname()}"

    pid_file = Path.home() / ".casare_rpa" / f"robot_{target_robot_id}.pid"
    status_file = Path.home() / ".casare_rpa" / f"robot_{target_robot_id}_status.json"

    status_data = {
        "robot_id": target_robot_id,
        "running": False,
        "pid": None,
        "backend": "PostgreSQL (PgQueuer)",
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
                    }
            except psutil.NoSuchProcess:
                try:
                    pid_file.unlink()
                except OSError:
                    pass
        except (ValueError, OSError):
            pass

    # Load cached status if available
    if status_file.exists():
        try:
            cached = orjson.loads(status_file.read_bytes())
            status_data.update(cached)
        except (OSError, orjson.JSONDecodeError):
            pass

    if json_output:
        console.print(orjson.dumps(status_data, option=orjson.OPT_INDENT_2).decode())
        return

    # Rich formatted output
    running_status = (
        "[green]Running[/green]" if status_data["running"] else "[red]Stopped[/red]"
    )

    console.print(
        Panel(
            f"[bold]Robot ID:[/bold] {status_data['robot_id']}\n"
            f"[bold]Status:[/bold] {running_status}\n"
            f"[bold]PID:[/bold] {status_data.get('pid', 'N/A')}\n"
            f"[bold]Backend:[/bold] {status_data.get('backend', 'PostgreSQL')}",
            title="Robot Status",
            border_style="blue",
        )
    )

    if status_data.get("process"):
        proc = status_data["process"]
        console.print("\n[bold]Resource Usage:[/bold]")
        console.print(f"  CPU: {proc.get('cpu_percent', 0):.1f}%")
        console.print(f"  Memory: {proc.get('memory_mb', 0):.1f} MB")


def main() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
