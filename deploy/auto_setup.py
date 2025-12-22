#!/usr/bin/env python3
"""
NOTE: Prefer using the unified setup CLI:
    python -m deploy.supabase.setup quickstart    # Interactive first-time setup
    python -m deploy.supabase.setup all           # Complete setup with migration + robot
    python -m deploy.supabase.setup verify        # Verify setup

CasareRPA Automated Setup Script.

One-click setup for:
1. Database migration to Supabase
2. Initial robot and API key creation
3. Start orchestrator (PC)
4. Start robot agent (VM or PC)

Usage:
    # Full setup (first time)
    python deploy/auto_setup.py setup --db-password YOUR_SUPABASE_DB_PASSWORD

    # Start orchestrator only (your PC)
    python deploy/auto_setup.py orchestrator

    # Start robot only (VM or additional machines)
    python deploy/auto_setup.py robot --orchestrator-url http://YOUR_PC_IP:8000

    # Check status
    python deploy/auto_setup.py status
"""

import argparse
import asyncio
import hashlib
import os
import re
import secrets
import socket
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from dotenv import load_dotenv, set_key

    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False


@dataclass
class Config:
    """Configuration loaded from environment."""

    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_key: str = ""
    database_url: str = ""
    api_secret: str = ""
    orchestrator_url: str = "http://localhost:8000"
    robot_name: str = ""
    robot_api_key: str = ""

    @classmethod
    def from_env(cls, env_path: Path) -> "Config":
        """Load from .env file."""
        if DOTENV_AVAILABLE:
            load_dotenv(env_path)

        return cls(
            supabase_url=os.getenv("SUPABASE_URL", ""),
            supabase_anon_key=os.getenv("SUPABASE_ANON_KEY", ""),
            supabase_service_key=os.getenv("SUPABASE_SERVICE_KEY", ""),
            database_url=os.getenv("DATABASE_URL", ""),
            api_secret=os.getenv("API_SECRET", ""),
            orchestrator_url=os.getenv("ORCHESTRATOR_URL", "http://localhost:8000"),
            robot_name=os.getenv("ROBOT_NAME", f"Robot-{socket.gethostname()}"),
            robot_api_key=os.getenv("ROBOT_API_KEY", ""),
        )


def print_header(title: str):
    """Print formatted header."""
    width = 60
    print("\n" + "=" * width)
    print(f" {title}")
    print("=" * width)


def print_step(step: str, status: str = "", success: Optional[bool] = None):
    """Print step with status."""
    icon = ""
    if success is True:
        icon = "[OK] "
    elif success is False:
        icon = "[FAIL] "
    elif status:
        icon = "[...] "
    print(f"  {icon}{step}: {status}" if status else f"  {step}")


def update_env_password(env_path: Path, password: str) -> bool:
    """Update .env file with actual password."""
    if not env_path.exists():
        print_step(".env file", "Not found", False)
        return False

    content = env_path.read_text()

    # Replace placeholder password
    updated = content.replace("[YOUR_PASSWORD]", password)

    if updated == content:
        print_step("Password", "Already set or no placeholder found", True)
        return True

    env_path.write_text(updated)
    print_step("Password", "Updated in .env", True)
    return True


def get_local_ip() -> str:
    """Get local IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "localhost"


async def run_migration(database_url: str) -> bool:
    """Run database migration against Supabase."""
    migration_file = PROJECT_ROOT / "deploy" / "supabase" / "migrations" / "001_initial_schema.sql"

    if not migration_file.exists():
        print_step("Migration file", "Not found", False)
        return False

    print_step("Migration", f"Applying {migration_file.name}...")

    try:
        import asyncpg
    except ImportError:
        print_step("asyncpg", "Not installed. Run: pip install asyncpg", False)
        return False

    try:
        conn = await asyncpg.connect(database_url)

        # Read and execute migration
        sql = migration_file.read_text()

        # Split into statements (handle function definitions)
        statements = []
        current = []
        in_function = False
        in_dollar_quote = False

        for line in sql.split("\n"):
            # Track $$ blocks (function bodies)
            dollar_count = line.count("$$")
            if dollar_count % 2 == 1:
                in_dollar_quote = not in_dollar_quote

            current.append(line)

            # End of statement (not inside function)
            if not in_dollar_quote and line.strip().endswith(";"):
                stmt = "\n".join(current).strip()
                if stmt and not all(
                    line_part.strip().startswith("--") or not line_part.strip()
                    for line_part in stmt.split("\n")
                ):
                    statements.append(stmt)
                current = []

        print_step("Statements", f"Found {len(statements)} SQL statements")

        errors = []
        for i, stmt in enumerate(statements, 1):
            try:
                await conn.execute(stmt)
            except Exception as e:
                error_msg = str(e)
                # Ignore "already exists" errors
                if "already exists" not in error_msg.lower():
                    errors.append(f"Statement {i}: {error_msg[:100]}")

        await conn.close()

        if errors:
            print_step("Migration", f"Completed with {len(errors)} errors", False)
            for err in errors[:3]:
                print(f"      {err}")
            return False

        print_step("Migration", "Applied successfully", True)
        return True

    except Exception as e:
        print_step("Migration", f"Failed: {e}", False)
        return False


async def create_robot_and_key(database_url: str, robot_name: str) -> tuple[str, str]:
    """Create robot and generate API key."""
    try:
        import asyncpg
    except ImportError:
        return "", ""

    try:
        conn = await asyncpg.connect(database_url)

        # Check if robot exists
        existing = await conn.fetchrow(
            "SELECT robot_id FROM robots WHERE name = $1",
            robot_name,
        )

        if existing:
            robot_id = str(existing["robot_id"])
            print_step("Robot", f"Already exists: {robot_name}", True)
        else:
            # Create robot
            hostname = socket.gethostname()
            result = await conn.fetchrow(
                """
                INSERT INTO robots (name, hostname, status, environment, capabilities, max_concurrent_jobs)
                VALUES ($1, $2, 'offline', 'production', '["browser", "desktop"]'::jsonb, 3)
                RETURNING robot_id
                """,
                robot_name,
                hostname,
            )
            robot_id = str(result["robot_id"])
            print_step("Robot", f"Created: {robot_name} ({robot_id[:8]}...)", True)

        # Generate API key
        token = secrets.token_urlsafe(32)
        raw_key = f"crpa_{token}"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        expires_at = datetime.now(timezone.utc) + timedelta(days=365)

        # Check for existing active key
        existing_key = await conn.fetchrow(
            """
            SELECT id FROM robot_api_keys
            WHERE robot_id = $1::uuid AND is_revoked = FALSE
            AND (expires_at IS NULL OR expires_at > NOW())
            LIMIT 1
            """,
            robot_id,
        )

        if existing_key:
            print_step(
                "API Key",
                "Active key exists (generate new one manually if needed)",
                True,
            )
            await conn.close()
            return robot_id, ""

        await conn.execute(
            """
            INSERT INTO robot_api_keys (robot_id, api_key_hash, name, expires_at, created_by)
            VALUES ($1::uuid, $2, 'Auto-generated', $3, 'auto_setup')
            """,
            robot_id,
            key_hash,
            expires_at,
        )

        await conn.close()
        print_step("API Key", f"Generated (expires: {expires_at.date()})", True)
        return robot_id, raw_key

    except Exception as e:
        print_step("Robot/Key", f"Failed: {e}", False)
        return "", ""


def start_orchestrator(env_path: Path) -> subprocess.Popen:
    """Start orchestrator server."""
    print_step("Orchestrator", "Starting on port 8000...")

    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "casare_rpa.infrastructure.orchestrator.server:app",
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
        "--reload",
    ]

    env = os.environ.copy()
    if env_path.exists():
        for line in env_path.read_text().split("\n"):
            if "=" in line and not line.strip().startswith("#"):
                key, value = line.split("=", 1)
                env[key.strip()] = value.strip()

    proc = subprocess.Popen(
        cmd,
        cwd=PROJECT_ROOT,
        env=env,
    )

    print_step("Orchestrator", f"Started (PID: {proc.pid})", True)
    return proc


def start_robot(env_path: Path, robot_name: str) -> subprocess.Popen:
    """Start robot agent."""
    print_step("Robot", f"Starting {robot_name}...")

    cmd = [
        sys.executable,
        "-m",
        "casare_rpa.robot.cli",
        "start",
        "--name",
        robot_name,
        "--verbose",
    ]

    env = os.environ.copy()
    if env_path.exists():
        for line in env_path.read_text().split("\n"):
            if "=" in line and not line.strip().startswith("#"):
                key, value = line.split("=", 1)
                env[key.strip()] = value.strip()

    proc = subprocess.Popen(
        cmd,
        cwd=PROJECT_ROOT,
        env=env,
    )

    print_step("Robot", f"Started (PID: {proc.pid})", True)
    return proc


async def check_status(config: Config) -> dict:
    """Check system status."""
    status = {
        "supabase": False,
        "database": False,
        "orchestrator": False,
        "robots": 0,
    }

    # Check Supabase URL
    if config.supabase_url:
        try:
            import httpx

            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{config.supabase_url}/rest/v1/",
                    headers={"apikey": config.supabase_anon_key},
                    timeout=5,
                )
                status["supabase"] = resp.status_code == 200
        except Exception:
            pass

    # Check database
    if config.database_url and "[YOUR_PASSWORD]" not in config.database_url:
        try:
            import asyncpg

            conn = await asyncpg.connect(config.database_url)
            result = await conn.fetchrow("SELECT COUNT(*) FROM robots")
            status["database"] = True
            status["robots"] = result[0] if result else 0
            await conn.close()
        except Exception:
            pass

    # Check orchestrator
    try:
        import httpx

        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{config.orchestrator_url}/health", timeout=5)
            status["orchestrator"] = resp.status_code == 200
    except Exception:
        pass

    return status


async def main_setup(args):
    """Main setup command."""
    print_header("CasareRPA Automated Setup")

    env_path = PROJECT_ROOT / ".env"
    config = Config.from_env(env_path)

    # Step 1: Update password
    if args.db_password:
        print_header("Step 1: Configure Database Password")
        update_env_password(env_path, args.db_password)
        # Reload config
        config = Config.from_env(env_path)

    # Step 2: Run migration
    print_header("Step 2: Database Migration")
    if "[YOUR_PASSWORD]" in config.database_url:
        print_step("Database URL", "Password not set. Use --db-password", False)
        print("\n  Run: python deploy/auto_setup.py setup --db-password YOUR_PASSWORD")
        return

    await run_migration(config.database_url)

    # Step 3: Create robot and API key
    print_header("Step 3: Create Robot & API Key")
    robot_name = args.robot_name or config.robot_name or f"Robot-{socket.gethostname()}"
    robot_id, api_key = await create_robot_and_key(config.database_url, robot_name)

    if api_key:
        print("\n" + "!" * 60)
        print(" SAVE THIS API KEY - IT WILL NOT BE SHOWN AGAIN!")
        print("!" * 60)
        print(f"\n  ROBOT_API_KEY={api_key}\n")
        print("!" * 60)

        # Update .env with API key
        if env_path.exists():
            content = env_path.read_text()
            if "ROBOT_API_KEY=" not in content:
                with open(env_path, "a") as f:
                    f.write(f"\n# Generated API Key\nROBOT_API_KEY={api_key}\n")
                print_step("API Key", "Saved to .env", True)

    # Step 4: Show next steps
    print_header("Setup Complete!")
    local_ip = get_local_ip()

    print(f"""
  Your PC (Orchestrator):
    Start: python deploy/auto_setup.py orchestrator
    URL:   http://{local_ip}:8000
    Docs:  http://{local_ip}:8000/docs

  Your VM (Robot):
    1. Copy .env to VM (or create minimal one with):
       DATABASE_URL={config.database_url}
       ROBOT_API_KEY={api_key or 'YOUR_KEY'}

    2. Start robot:
       python deploy/auto_setup.py robot

  Or run both on this PC:
    python deploy/auto_setup.py all
""")


async def main_orchestrator(args):
    """Start orchestrator."""
    print_header("Starting Orchestrator")

    env_path = PROJECT_ROOT / ".env"
    config = Config.from_env(env_path)

    if "[YOUR_PASSWORD]" in config.database_url:
        print_step("Error", "Database password not configured", False)
        print("  Run: python deploy/auto_setup.py setup --db-password YOUR_PASSWORD")
        return

    local_ip = get_local_ip()
    print(f"  Local IP: {local_ip}")
    print(f"  API Docs: http://{local_ip}:8000/docs")
    print(f"  Health:   http://{local_ip}:8000/health")
    print("\n  Press Ctrl+C to stop\n")

    try:
        proc = start_orchestrator(env_path)
        proc.wait()
    except KeyboardInterrupt:
        print("\n  Orchestrator stopped.")


async def main_robot(args):
    """Start robot agent."""
    print_header("Starting Robot Agent")

    env_path = PROJECT_ROOT / ".env"
    config = Config.from_env(env_path)

    if "[YOUR_PASSWORD]" in config.database_url:
        print_step("Error", "Database password not configured", False)
        print("  Run: python deploy/auto_setup.py setup --db-password YOUR_PASSWORD")
        return

    robot_name = args.robot_name or config.robot_name or f"Robot-{socket.gethostname()}"
    print(f"  Robot Name: {robot_name}")
    print("  Database:   Supabase PostgreSQL")
    print("\n  Press Ctrl+C to stop\n")

    try:
        proc = start_robot(env_path, robot_name)
        proc.wait()
    except KeyboardInterrupt:
        print("\n  Robot stopped.")


async def main_all(args):
    """Start both orchestrator and robot."""
    print_header("Starting Orchestrator + Robot")

    env_path = PROJECT_ROOT / ".env"
    config = Config.from_env(env_path)

    if "[YOUR_PASSWORD]" in config.database_url:
        print_step("Error", "Database password not configured", False)
        return

    local_ip = get_local_ip()
    robot_name = args.robot_name or config.robot_name or f"Robot-{socket.gethostname()}"

    print(f"  Orchestrator: http://{local_ip}:8000")
    print(f"  Robot:        {robot_name}")
    print("\n  Press Ctrl+C to stop both\n")

    procs = []
    try:
        procs.append(start_orchestrator(env_path))
        await asyncio.sleep(3)  # Wait for orchestrator to start
        procs.append(start_robot(env_path, robot_name))

        # Wait for processes
        while all(p.poll() is None for p in procs):
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\n  Stopping...")
        for p in procs:
            p.terminate()
        print("  Stopped.")


async def main_status(args):
    """Check system status."""
    print_header("System Status")

    env_path = PROJECT_ROOT / ".env"
    config = Config.from_env(env_path)

    status = await check_status(config)

    print_step(
        "Supabase API",
        "Connected" if status["supabase"] else "Not connected",
        status["supabase"],
    )
    print_step(
        "Database",
        "Connected" if status["database"] else "Not connected",
        status["database"],
    )
    print_step(
        "Orchestrator",
        "Running" if status["orchestrator"] else "Not running",
        status["orchestrator"],
    )
    print_step("Robots in DB", str(status["robots"]), status["robots"] > 0)

    if not status["database"]:
        print("\n  Tip: Run 'python deploy/auto_setup.py setup --db-password YOUR_PASSWORD'")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="CasareRPA Automated Setup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Setup command
    setup_parser = subparsers.add_parser("setup", help="Full setup (first time)")
    setup_parser.add_argument("--db-password", required=True, help="Supabase database password")
    setup_parser.add_argument("--robot-name", help="Robot name (default: Robot-HOSTNAME)")

    # Orchestrator command
    orch_parser = subparsers.add_parser("orchestrator", help="Start orchestrator only")

    # Robot command
    robot_parser = subparsers.add_parser("robot", help="Start robot agent only")
    robot_parser.add_argument("--robot-name", help="Robot name")
    robot_parser.add_argument("--orchestrator-url", help="Orchestrator URL (for remote)")

    # All command
    all_parser = subparsers.add_parser("all", help="Start orchestrator + robot")
    all_parser.add_argument("--robot-name", help="Robot name")

    # Status command
    status_parser = subparsers.add_parser("status", help="Check system status")

    args = parser.parse_args()

    if args.command == "setup":
        asyncio.run(main_setup(args))
    elif args.command == "orchestrator":
        asyncio.run(main_orchestrator(args))
    elif args.command == "robot":
        asyncio.run(main_robot(args))
    elif args.command == "all":
        asyncio.run(main_all(args))
    elif args.command == "status":
        asyncio.run(main_status(args))
    else:
        parser.print_help()
        print("\nQuick start:")
        print("  python deploy/auto_setup.py setup --db-password YOUR_SUPABASE_PASSWORD")
        print("  python deploy/auto_setup.py all")


if __name__ == "__main__":
    main()
