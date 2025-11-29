"""
CasareRPA Robot CLI

Command-line interface for managing the Robot Agent.

Commands:
    start   - Start the robot agent with configuration
    stop    - Gracefully stop a running robot by ID
    status  - Show robot status and current jobs

Usage:
    python -m casare_rpa.robot.cli start --config config/robot.yaml
    python -m casare_rpa.robot.cli stop --robot-id worker-01
    python -m casare_rpa.robot.cli status
"""

import asyncio
import os
import signal
import sys
from pathlib import Path
from typing import Optional

import typer
from loguru import logger
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

# Import config directly to avoid circular imports via __init__.py
from casare_rpa.robot.config import RobotConfig, get_persistent_robot_id


app = typer.Typer(
    name="robot",
    help="CasareRPA Robot Agent CLI - Manage distributed workflow execution",
    add_completion=False,
)

console = Console()


# Global state for signal handling
_shutdown_event: Optional[asyncio.Event] = None
_agent = None  # Type: Optional[RobotAgent], but avoid import at module level


def _write_pid_file(robot_id: str) -> Path:
    """
    Write PID file for the running robot.

    Args:
        robot_id: Robot identifier.

    Returns:
        Path to the PID file.
    """
    pid_dir = Path.home() / ".casare_rpa"
    pid_dir.mkdir(parents=True, exist_ok=True)
    pid_file = pid_dir / f"robot_{robot_id}.pid"
    pid_file.write_text(str(os.getpid()))
    return pid_file


def _remove_pid_file(robot_id: str) -> None:
    """
    Remove PID file for the robot.

    Args:
        robot_id: Robot identifier.
    """
    pid_file = Path.home() / ".casare_rpa" / f"robot_{robot_id}.pid"
    try:
        if pid_file.exists():
            pid_file.unlink()
    except OSError as e:
        logger.warning(f"Failed to remove PID file: {e}")


def _write_status_file(robot_id: str, status_data: dict) -> None:
    """
    Write status file for the robot.

    Args:
        robot_id: Robot identifier.
        status_data: Status dictionary to write.
    """
    import orjson

    status_dir = Path.home() / ".casare_rpa"
    status_dir.mkdir(parents=True, exist_ok=True)
    status_file = status_dir / f"robot_{robot_id}_status.json"
    try:
        status_file.write_bytes(orjson.dumps(status_data, option=orjson.OPT_INDENT_2))
    except OSError as e:
        logger.warning(f"Failed to write status file: {e}")


def _setup_signal_handlers(loop: asyncio.AbstractEventLoop) -> None:
    """
    Setup signal handlers for graceful shutdown.

    Args:
        loop: The asyncio event loop.
    """
    global _shutdown_event
    _shutdown_event = asyncio.Event()

    def signal_handler(signum: int, frame) -> None:
        """Handle shutdown signals."""
        sig_name = signal.Signals(signum).name
        logger.info(f"Received {sig_name}, initiating graceful shutdown...")
        console.print(f"\n[yellow]Received {sig_name}, shutting down...[/yellow]")

        if _shutdown_event:
            loop.call_soon_threadsafe(_shutdown_event.set)

    # Register signal handlers
    # SIGTERM for graceful termination (docker stop, systemd, etc.)
    signal.signal(signal.SIGTERM, signal_handler)
    # SIGINT for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)

    # On Windows, also handle SIGBREAK (Ctrl+Break)
    if sys.platform == "win32":
        try:
            signal.signal(signal.SIGBREAK, signal_handler)
        except (AttributeError, ValueError):
            pass


async def _run_agent(config: RobotConfig) -> int:
    """
    Run the robot agent with graceful shutdown support.

    Args:
        config: Robot configuration.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    global _agent, _shutdown_event

    # Lazy import to avoid circular dependencies
    from .agent import RobotAgent

    _agent = RobotAgent(config)

    # Write PID file
    pid_file = _write_pid_file(config.robot_id)
    logger.debug(f"PID file written: {pid_file}")

    try:
        # Start the agent in a task
        agent_task = asyncio.create_task(_agent.start())

        # Periodically update status file
        async def status_updater():
            while True:
                await asyncio.sleep(5)
                try:
                    status = _agent.get_status()
                    _write_status_file(config.robot_id, status)
                except Exception as e:
                    logger.debug(f"Status update failed: {e}")

        status_task = asyncio.create_task(status_updater())

        # Wait for either agent completion or shutdown signal
        if _shutdown_event:
            shutdown_task = asyncio.create_task(_shutdown_event.wait())

            done, pending = await asyncio.wait(
                [agent_task, shutdown_task],
                return_when=asyncio.FIRST_COMPLETED,
            )

            # Cancel status updater
            status_task.cancel()
            try:
                await status_task
            except asyncio.CancelledError:
                pass

            # Cancel pending tasks
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

            # If shutdown was triggered, stop the agent gracefully
            if shutdown_task in done:
                console.print("[yellow]Graceful shutdown in progress...[/yellow]")
                await _agent.stop()
                console.print("[green]Robot agent stopped successfully.[/green]")
                return 0
        else:
            await agent_task

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
    config: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to YAML configuration file",
        exists=False,
    ),
    robot_id: Optional[str] = typer.Option(
        None,
        "--robot-id",
        "-r",
        help="Override robot ID from config",
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

    Loads configuration from the specified YAML file and starts the robot
    agent. The agent will poll for jobs and execute workflows.

    Supports graceful shutdown via SIGTERM or SIGINT (Ctrl+C).
    """
    # Configure logging
    logger.remove()
    if verbose:
        logger.add(
            sys.stderr,
            level="DEBUG",
            format="<green>{time:HH:mm:ss}</green> | <level>{level:<8}</level> | {message}",
        )
    else:
        logger.add(
            sys.stderr,
            level="INFO",
            format="<green>{time:HH:mm:ss}</green> | <level>{level:<8}</level> | {message}",
        )

    # Load configuration
    try:
        if config:
            console.print(f"Loading configuration from: {config}")
            robot_config = RobotConfig.from_yaml(config)
        else:
            console.print("Using default configuration (no config file specified)")
            robot_config = RobotConfig.load()
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]Error:[/red] Failed to load config: {e}")
        raise typer.Exit(code=1)

    # Override robot ID if specified
    if robot_id:
        robot_config.robot_id = robot_id

    # Display startup info
    console.print(
        Panel(
            f"[bold]Robot ID:[/bold] {robot_config.robot_id}\n"
            f"[bold]Name:[/bold] {robot_config.robot_name}\n"
            f"[bold]Max Concurrent Jobs:[/bold] {robot_config.execution.max_concurrent_jobs}\n"
            f"[bold]Poll Interval:[/bold] {robot_config.polling.poll_interval_seconds}s",
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
        exit_code = loop.run_until_complete(_run_agent(robot_config))
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

    Note: This command requires the robot to have a PID file in the standard
    location (~/.casare_rpa/robot_{robot_id}.pid).
    """
    console.print(f"[yellow]Requesting shutdown for robot: {robot_id}[/yellow]")

    # Try to find the robot process
    pid_file = Path.home() / ".casare_rpa" / f"robot_{robot_id}.pid"

    if not pid_file.exists():
        console.print(
            f"[red]Error:[/red] No PID file found for robot '{robot_id}'.\n"
            f"Expected: {pid_file}"
        )
        console.print(
            "\n[dim]The robot may not be running, or was started without "
            "creating a PID file.[/dim]"
        )
        raise typer.Exit(code=1)

    try:
        pid = int(pid_file.read_text().strip())
    except (ValueError, OSError) as e:
        console.print(f"[red]Error:[/red] Invalid PID file: {e}")
        raise typer.Exit(code=1)

    # Send signal to the process
    try:
        if force:
            console.print(f"[yellow]Sending SIGKILL to process {pid}...[/yellow]")
            if sys.platform == "win32":
                # Windows doesn't have SIGKILL, use terminate
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

        if not force:
            console.print(
                "[dim]The robot will complete current jobs before stopping. "
                "Use --force to terminate immediately.[/dim]"
            )

    except ProcessLookupError:
        console.print(
            f"[yellow]Warning:[/yellow] Process {pid} not found. "
            "Robot may have already stopped."
        )
        # Clean up stale PID file
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
        help="Show status for specific robot (default: current machine)",
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

    target_robot_id = robot_id or get_persistent_robot_id()

    # Check for PID file
    pid_file = Path.home() / ".casare_rpa" / f"robot_{target_robot_id}.pid"

    # Try to get status from a running agent
    status_file = Path.home() / ".casare_rpa" / f"robot_{target_robot_id}_status.json"

    status_data = {
        "robot_id": target_robot_id,
        "running": False,
        "pid": None,
        "connection": {"status": "unknown"},
        "jobs": {"running": 0, "pending": 0, "completed": 0},
        "metrics": {},
    }

    # Check if process is running
    if pid_file.exists():
        try:
            pid = int(pid_file.read_text().strip())
            # Check if process exists
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
                        "create_time": process.create_time(),
                    }
            except psutil.NoSuchProcess:
                # Process not found, clean up stale PID file
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

    # Output
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
            f"[bold]PID:[/bold] {status_data.get('pid', 'N/A')}",
            title="Robot Status",
            border_style="blue",
        )
    )

    # Connection info
    conn = status_data.get("connection", {})
    conn_status = conn.get("status", "unknown")
    conn_color = (
        "green"
        if conn_status == "connected"
        else "red"
        if conn_status == "disconnected"
        else "yellow"
    )

    console.print(
        f"\n[bold]Connection:[/bold] [{conn_color}]{conn_status}[/{conn_color}]"
    )

    # Jobs table
    job_executor = status_data.get("job_executor", {})
    running_jobs = job_executor.get("running_jobs", [])

    console.print("\n[bold]Jobs:[/bold]")
    if running_jobs:
        table = Table(box=box.ROUNDED)
        table.add_column("Job ID", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Started", style="dim")

        for job in running_jobs:
            job_id = job.get("job_id", "unknown")
            if len(job_id) > 12:
                job_id = job_id[:12] + "..."
            table.add_row(
                job_id,
                job.get("status", "unknown"),
                job.get("started_at", "N/A"),
            )

        console.print(table)
    else:
        console.print("  [dim]No jobs currently running[/dim]")

    # Metrics
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
