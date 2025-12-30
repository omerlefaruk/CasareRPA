import os
import shutil
import subprocess
import sys
from pathlib import Path

import typer

# Import robot CLI if available
try:
    from casare_rpa.robot.cli import app as robot_app
except ImportError:
    robot_app = typer.Typer(name="robot", help="Robot CLI not available (dependencies missing)")

app = typer.Typer(name="casare", help="CasareRPA Unified CLI")

# Mount Robot CLI
app.add_typer(robot_app, name="robot", help="Manage Robot Agent")

# Orchestrator CLI Group
orchestrator_app = typer.Typer(name="orchestrator", help="Manage Orchestrator")
app.add_typer(orchestrator_app, name="orchestrator")


@orchestrator_app.command("start")
def start_orchestrator(
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="Bind host"),
    port: int = typer.Option(8000, "--port", "-p", help="Bind port"),
    workers: int = typer.Option(1, "--workers", "-w", help="Number of workers"),
    reload: bool = typer.Option(False, "--reload", "-r", help="Enable auto-reload"),
    dev: bool = typer.Option(False, "--dev", "-d", help="Enable dev mode (bypass JWT auth)"),
):
    """Start the Orchestrator API locally (development)."""
    env = os.environ.copy()
    if dev:
        env["JWT_DEV_MODE"] = "true"
        typer.echo("⚠️  Dev mode enabled - JWT authentication bypassed")

    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "casare_rpa.infrastructure.orchestrator.server:app",
        "--host",
        host,
        "--port",
        str(port),
        "--workers",
        str(workers),
    ]
    if reload:
        cmd.append("--reload")

    typer.echo(f"Starting Orchestrator on {host}:{port}...")
    typer.echo(
        f"To expose this via Cloudflare, run in another terminal: python manage.py tunnel start --port {port}"
    )
    subprocess.run(cmd, env=env)


# Canvas Command
@app.command("canvas")
def start_canvas(
    v1: bool = typer.Option(False, "--v1", "--legacy", help="Launch legacy V1 UI"),
):
    """Start the Canvas Designer (GUI)."""
    src_path = Path(__file__).parent.parent.parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    if v1:
        os.environ["CASARE_UI_V1"] = "1"
        typer.echo("🚀 Launching legacy V1 UI...")

    try:
        from casare_rpa.presentation.canvas import main

        sys.exit(main())
    except ImportError as e:
        typer.echo(f"Error starting Canvas: {e}", err=True)
        typer.echo("Ensure dependencies are installed (PySide6, NodeGraphQt, etc.)", err=True)
        raise typer.Exit(1)


# Cloudflare Tunnel CLI Group
tunnel_app = typer.Typer(name="tunnel", help="Manage Cloudflare Tunnels")
app.add_typer(tunnel_app, name="tunnel")

# Cache CLI Group
cache_app = typer.Typer(name="cache", help="Manage Caching System")
app.add_typer(cache_app, name="cache")


@cache_app.command("clear")
def cache_clear():
    """Clear all cache tiers (Memory and Disk)."""
    import asyncio

    from casare_rpa.infrastructure.cache.manager import TieredCacheManager

    async def _clear():
        manager = TieredCacheManager()
        await manager.clear()
        typer.echo("Cache cleared successfully.")

    asyncio.run(_clear())


@tunnel_app.command("start")
def tunnel_start(
    port: int = typer.Option(8000, "--port", "-p", help="Port to expose"),
    hostname: str | None = typer.Option(
        None, "--hostname", "-n", help="Custom hostname (if configured)"
    ),
):
    """Start a Cloudflare Tunnel to expose the Orchestrator."""
    typer.echo(f"Starting Cloudflare Tunnel for port {port}...")

    # Check for cloudflared
    if shutil.which("cloudflared") is None:
        typer.echo("Error: 'cloudflared' not found in PATH.", err=True)
        typer.echo(
            "Please install it: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation",
            err=True,
        )
        raise typer.Exit(1)

    cmd = ["cloudflared", "tunnel", "--url", f"http://localhost:{port}"]
    if hostname:
        cmd.extend(["--hostname", hostname])

    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        typer.echo("\nTunnel stopped.")


# Database CLI Group
from casare_rpa.cli.db import app as db_app

app.add_typer(db_app, name="db", help="Database management")

# Deploy CLI Group (Legacy/Scripts)
deploy_app = typer.Typer(name="deploy", help="Deployment tools")
app.add_typer(deploy_app, name="deploy")


@deploy_app.command("setup")
def run_auto_setup():
    """Run the auto_setup.py script for initial environment setup."""
    setup_script = Path(__file__).resolve().parents[3] / "deploy" / "auto_setup.py"
    if not setup_script.exists():
        typer.echo(f"Setup script not found at {setup_script}", err=True)
        raise typer.Exit(1)

    typer.echo(f"Running setup script: {setup_script}")
    subprocess.run([sys.executable, str(setup_script)])


if __name__ == "__main__":
    app()
