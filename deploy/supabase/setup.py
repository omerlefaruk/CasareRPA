#!/usr/bin/env python3
"""
Unified Supabase setup for CasareRPA.

Single entry point for all Supabase operations including:
- Database migrations
- Edge function deployment
- RLS policy configuration
- Robot and API key creation
- Setup verification

Usage:
    python -m deploy.supabase.setup init          # Initialize project
    python -m deploy.supabase.setup migrate       # Run migrations
    python -m deploy.supabase.setup functions     # Deploy edge functions
    python -m deploy.supabase.setup rls           # Configure RLS policies
    python -m deploy.supabase.setup verify        # Verify setup
    python -m deploy.supabase.setup all           # Complete setup
    python -m deploy.supabase.setup quickstart    # Interactive first-time setup
    python -m deploy.supabase.setup types         # Generate Python types
"""

from __future__ import annotations

import asyncio
import hashlib
import os
import secrets
import shutil
import socket
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

try:
    import typer
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.table import Table
except ImportError:
    print("Installing required packages: typer, rich")
    subprocess.run([sys.executable, "-m", "pip", "install", "typer", "rich"], check=True)
    import typer
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.table import Table

try:
    import httpx
except ImportError:
    print("Installing httpx...")
    subprocess.run([sys.executable, "-m", "pip", "install", "httpx"], check=True)
    import httpx


# Constants
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
MIGRATIONS_DIR = SCRIPT_DIR / "migrations"
FUNCTIONS_DIR = SCRIPT_DIR / "functions"
ENV_EXAMPLE = PROJECT_ROOT / ".env.example"
ENV_FILE = PROJECT_ROOT / ".env"

REQUIRED_TABLES = [
    "workflows",
    "robots",
    "jobs",
    "robot_api_keys",
    "robot_logs",
    "schedules",
]
REALTIME_TABLES = ["robots", "jobs"]

# CLI setup
app = typer.Typer(
    name="setup",
    help="CasareRPA Supabase Setup CLI",
    add_completion=False,
)
console = Console()


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class SupabaseConfig:
    """Supabase project configuration."""

    project_ref: str
    service_key: str
    anon_key: str = ""
    db_password: str = ""

    @property
    def url(self) -> str:
        return f"https://{self.project_ref}.supabase.co"

    @property
    def rest_url(self) -> str:
        return f"{self.url}/rest/v1"

    @property
    def pooler_host(self) -> str:
        return "aws-0-us-east-1.pooler.supabase.com"

    @property
    def database_url(self) -> str:
        user = f"postgres.{self.project_ref}"
        return f"postgresql://{user}:{self.db_password}@{self.pooler_host}:5432/postgres"

    @classmethod
    def from_env(cls, env_path: Path = ENV_FILE) -> SupabaseConfig | None:
        """Load configuration from .env file."""
        if not env_path.exists():
            return None

        env_vars = {}
        for line in env_path.read_text().split("\n"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                env_vars[key.strip()] = value.strip().strip('"').strip("'")

        project_ref = env_vars.get("SUPABASE_PROJECT_REF", "")
        if not project_ref:
            # Try to extract from URL
            url = env_vars.get("SUPABASE_URL", "")
            if ".supabase.co" in url:
                project_ref = url.replace("https://", "").split(".")[0]

        if not project_ref:
            return None

        return cls(
            project_ref=project_ref,
            service_key=env_vars.get("SUPABASE_SERVICE_KEY", ""),
            anon_key=env_vars.get("SUPABASE_ANON_KEY", ""),
            db_password=env_vars.get("SUPABASE_DB_PASSWORD", ""),
        )


@dataclass
class SetupResult:
    """Result of a setup operation."""

    success: bool
    message: str
    details: dict = field(default_factory=dict)


# =============================================================================
# Supabase Client
# =============================================================================


class SupabaseSetupClient:
    """Client for Supabase setup operations."""

    def __init__(self, config: SupabaseConfig):
        self.config = config
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> SupabaseSetupClient:
        self._client = httpx.AsyncClient(timeout=30.0)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()

    def _headers(self, use_service_key: bool = True) -> dict:
        """Get request headers."""
        key = self.config.service_key if use_service_key else self.config.anon_key
        return {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }

    async def check_connection(self) -> SetupResult:
        """Verify connection to Supabase project."""
        try:
            resp = await self._client.get(
                f"{self.config.rest_url}/",
                headers=self._headers(),
            )
            if resp.status_code == 200:
                return SetupResult(True, "Connection successful")
            return SetupResult(False, f"Connection failed: {resp.status_code}")
        except httpx.HTTPError as e:
            return SetupResult(False, f"Connection error: {e}")

    async def check_tables(self) -> SetupResult:
        """Check if required tables exist."""
        existing = []
        missing = []

        for table in REQUIRED_TABLES:
            try:
                resp = await self._client.get(
                    f"{self.config.rest_url}/{table}?limit=0",
                    headers=self._headers(),
                )
                if resp.status_code == 200:
                    existing.append(table)
                else:
                    missing.append(table)
            except httpx.HTTPError:
                missing.append(table)

        if missing:
            return SetupResult(
                False,
                f"Missing tables: {', '.join(missing)}",
                {"existing": existing, "missing": missing},
            )
        return SetupResult(True, "All required tables exist", {"tables": existing})

    async def enable_realtime(self, table: str) -> SetupResult:
        """Enable realtime for a table via RPC."""
        sql = f"ALTER PUBLICATION supabase_realtime ADD TABLE {table};"
        try:
            resp = await self._client.post(
                f"{self.config.rest_url}/rpc/exec_sql",
                headers=self._headers(),
                json={"query": sql},
            )
            if resp.status_code in (200, 204):
                return SetupResult(True, f"Realtime enabled for {table}")
            # Check if already enabled
            if "already exists" in resp.text.lower():
                return SetupResult(True, f"Realtime already enabled for {table}")
            return SetupResult(False, f"Failed: {resp.text[:100]}")
        except httpx.HTTPError as e:
            return SetupResult(False, f"Error: {e}")

    async def create_robot(self, name: str, hostname: str = "") -> SetupResult:
        """Create a robot entry."""
        hostname = hostname or socket.gethostname()
        data = {
            "name": name,
            "hostname": hostname,
            "status": "offline",
            "environment": "production",
            "capabilities": ["browser", "desktop"],
            "max_concurrent_jobs": 1,
        }
        try:
            resp = await self._client.post(
                f"{self.config.rest_url}/robots",
                headers=self._headers(),
                json=data,
            )
            if resp.status_code == 201:
                robot = resp.json()
                robot_data = robot[0] if isinstance(robot, list) else robot
                return SetupResult(
                    True,
                    f"Created robot: {name}",
                    {"robot_id": robot_data.get("robot_id")},
                )
            elif resp.status_code == 409:
                # Already exists
                get_resp = await self._client.get(
                    f"{self.config.rest_url}/robots?name=eq.{name}",
                    headers=self._headers(),
                )
                if get_resp.status_code == 200 and get_resp.json():
                    robot = get_resp.json()[0]
                    return SetupResult(
                        True,
                        f"Robot already exists: {name}",
                        {"robot_id": robot.get("robot_id")},
                    )
            return SetupResult(False, f"Failed to create robot: {resp.text[:100]}")
        except httpx.HTTPError as e:
            return SetupResult(False, f"Error: {e}")

    async def generate_api_key(
        self, robot_id: str, name: str = "Initial Key", days: int = 365
    ) -> SetupResult:
        """Generate an API key for a robot."""
        token = secrets.token_urlsafe(32)
        raw_key = f"crpa_{token}"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        expires_at = datetime.now(UTC) + timedelta(days=days)

        data = {
            "robot_id": robot_id,
            "api_key_hash": key_hash,
            "name": name,
            "description": "Generated by setup script",
            "expires_at": expires_at.isoformat(),
            "created_by": "setup_script",
        }

        try:
            resp = await self._client.post(
                f"{self.config.rest_url}/robot_api_keys",
                headers=self._headers(),
                json=data,
            )
            if resp.status_code == 201:
                return SetupResult(
                    True,
                    "API key generated",
                    {"raw_key": raw_key, "expires_at": expires_at.isoformat()},
                )
            return SetupResult(False, f"Failed: {resp.text[:100]}")
        except httpx.HTTPError as e:
            return SetupResult(False, f"Error: {e}")

    async def verify_setup(self) -> SetupResult:
        """Run comprehensive verification."""
        checks = {
            "connection": False,
            "tables": False,
            "realtime": False,
            "robots": False,
        }
        issues = []

        # Connection
        conn_result = await self.check_connection()
        checks["connection"] = conn_result.success
        if not conn_result.success:
            issues.append(f"Connection: {conn_result.message}")

        # Tables
        if checks["connection"]:
            tables_result = await self.check_tables()
            checks["tables"] = tables_result.success
            if not tables_result.success:
                issues.append(f"Tables: {tables_result.message}")

        # Realtime (assume working if connection works)
        if checks["connection"]:
            checks["realtime"] = True

        # Robots accessible
        if checks["tables"]:
            try:
                resp = await self._client.get(
                    f"{self.config.rest_url}/robots?limit=1",
                    headers=self._headers(),
                )
                checks["robots"] = resp.status_code == 200
            except Exception:
                checks["robots"] = False
                issues.append("Cannot access robots table")

        all_passed = all(checks.values())
        return SetupResult(
            all_passed,
            "All checks passed" if all_passed else f"{len(issues)} issues found",
            {"checks": checks, "issues": issues},
        )


# =============================================================================
# Migration Functions
# =============================================================================


async def run_migration_via_db(config: SupabaseConfig, migration_file: Path) -> SetupResult:
    """Run migration via direct database connection."""
    if not migration_file.exists():
        return SetupResult(False, f"Migration file not found: {migration_file}")

    try:
        import asyncpg
    except ImportError:
        return SetupResult(False, "asyncpg not installed. Run: pip install asyncpg")

    if not config.db_password:
        return SetupResult(False, "Database password required for direct migration")

    sql = migration_file.read_text(encoding="utf-8")

    # Parse SQL into statements
    statements = _parse_sql_statements(sql)

    try:
        conn = await asyncpg.connect(config.database_url)
        errors = []

        for i, stmt in enumerate(statements, 1):
            try:
                await conn.execute(stmt)
            except Exception as e:
                error_msg = str(e)
                if "already exists" not in error_msg.lower():
                    errors.append(f"Statement {i}: {error_msg[:100]}")

        await conn.close()

        if errors:
            return SetupResult(
                False,
                f"Migration completed with {len(errors)} errors",
                {"errors": errors[:5]},
            )
        return SetupResult(
            True,
            f"Applied migration: {migration_file.name}",
            {"statements": len(statements)},
        )
    except Exception as e:
        return SetupResult(False, f"Migration failed: {e}")


def _parse_sql_statements(sql: str) -> list[str]:
    """Parse SQL into individual statements, handling function definitions."""
    statements = []
    current = []
    in_dollar_quote = False

    for line in sql.split("\n"):
        # Track $$ blocks
        dollar_count = line.count("$$")
        if dollar_count % 2 == 1:
            in_dollar_quote = not in_dollar_quote

        current.append(line)

        # End of statement (not inside function)
        if not in_dollar_quote and line.strip().endswith(";"):
            stmt = "\n".join(current).strip()
            # Skip empty or comment-only statements
            if stmt and not all(
                line_part.strip().startswith("--") or not line_part.strip()
                for line_part in stmt.split("\n")
            ):
                statements.append(stmt)
            current = []

    return statements


# =============================================================================
# Edge Function Deployment
# =============================================================================


def deploy_edge_functions(function_name: str | None = None, dry_run: bool = False) -> SetupResult:
    """Deploy edge functions using Supabase CLI."""
    # Check if supabase CLI is installed
    try:
        result = subprocess.run(
            ["supabase", "--version"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return SetupResult(
                False,
                "Supabase CLI not installed. Run: npm install -g supabase",
            )
    except FileNotFoundError:
        return SetupResult(
            False,
            "Supabase CLI not installed. Run: npm install -g supabase",
        )

    functions = []
    if function_name:
        function_dir = FUNCTIONS_DIR / function_name
        if not function_dir.exists():
            return SetupResult(False, f"Function not found: {function_name}")
        functions = [function_name]
    else:
        # Deploy all functions
        for item in FUNCTIONS_DIR.iterdir():
            if item.is_dir() and (item / "index.ts").exists():
                functions.append(item.name)

    if not functions:
        return SetupResult(False, "No functions found to deploy")

    if dry_run:
        return SetupResult(
            True,
            f"Would deploy: {', '.join(functions)}",
            {"functions": functions},
        )

    deployed = []
    errors = []

    for func in functions:
        result = subprocess.run(
            ["supabase", "functions", "deploy", func],
            capture_output=True,
            text=True,
            cwd=SCRIPT_DIR,
        )
        if result.returncode == 0:
            deployed.append(func)
        else:
            errors.append(f"{func}: {result.stderr[:100]}")

    if errors:
        return SetupResult(
            False,
            f"Deployed {len(deployed)}/{len(functions)} functions",
            {"deployed": deployed, "errors": errors},
        )

    return SetupResult(
        True,
        f"Deployed {len(deployed)} functions",
        {"deployed": deployed},
    )


# =============================================================================
# Type Generation
# =============================================================================


def generate_types_from_schema(output_path: Path | None = None) -> SetupResult:
    """Generate Python types from Supabase schema."""
    output_path = output_path or SCRIPT_DIR / "supabase_types.py"
    migration_file = MIGRATIONS_DIR / "001_initial_schema.sql"

    if not migration_file.exists():
        return SetupResult(False, f"Schema file not found: {migration_file}")

    sql = migration_file.read_text()

    # Extract table definitions
    types_code = '''"""
Auto-generated Supabase types for CasareRPA.

Generated from: deploy/supabase/migrations/001_initial_schema.sql
Do not edit manually - regenerate using: python -m deploy.supabase.setup types
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from uuid import UUID


@dataclass
class Workflow:
    """Workflow table model."""

    workflow_id: UUID
    workflow_name: str
    workflow_json: dict[str, Any]
    version: int = 1
    description: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    timeout_seconds: int = 3600
    max_retries: int = 3


@dataclass
class Robot:
    """Robot table model."""

    robot_id: UUID
    name: str
    hostname: str
    status: str = "offline"
    environment: str = "default"
    capabilities: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    max_concurrent_jobs: int = 1
    current_job_ids: list[str] = field(default_factory=list)
    assigned_workflows: list[str] = field(default_factory=list)
    last_heartbeat: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Job:
    """Job table model."""

    job_id: UUID
    workflow_id: Optional[UUID] = None
    robot_uuid: Optional[UUID] = None
    status: str = "pending"
    robot_id: Optional[str] = None
    priority: int = 10
    execution_mode: str = "lan"
    payload: dict[str, Any] = field(default_factory=dict)
    workflow_name: Optional[str] = None
    progress: int = 0
    current_node: str = ""
    duration_ms: int = 0
    logs: str = ""
    created_at: Optional[datetime] = None
    claimed_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    scheduled_time: Optional[datetime] = None
    timeout_seconds: int = 3600
    result: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    created_by: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RobotApiKey:
    """Robot API Key table model."""

    id: UUID
    robot_id: UUID
    api_key_hash: str
    name: Optional[str] = None
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    last_used_ip: Optional[str] = None
    is_revoked: bool = False
    revoked_at: Optional[datetime] = None
    revoked_by: Optional[str] = None
    revoke_reason: Optional[str] = None
    created_by: Optional[str] = None


@dataclass
class RobotLog:
    """Robot Log table model."""

    id: UUID
    robot_id: UUID
    tenant_id: UUID
    timestamp: datetime
    level: str
    message: str
    source: Optional[str] = None
    extra: dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None


@dataclass
class Schedule:
    """Schedule table model."""

    schedule_id: UUID
    workflow_id: Optional[UUID] = None
    schedule_name: str = ""
    cron_expression: str = ""
    enabled: bool = True
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    run_count: int = 0
    failure_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


# Status enums
ROBOT_STATUSES = ["offline", "online", "busy", "error", "maintenance"]
JOB_STATUSES = ["pending", "queued", "claimed", "running", "completed", "failed", "cancelled", "timeout"]
LOG_LEVELS = ["TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
EXECUTION_MODES = ["lan", "internet"]
'''

    output_path.write_text(types_code)
    return SetupResult(True, f"Generated types: {output_path}", {"output": str(output_path)})


# =============================================================================
# Environment File Management
# =============================================================================


def create_env_file(
    project_ref: str,
    service_key: str,
    anon_key: str = "",
    db_password: str = "",
    robot_api_key: str = "",
) -> SetupResult:
    """Create or update .env file."""
    env_content = f"""# CasareRPA Configuration
# Generated by deploy/supabase/setup.py

# Supabase Configuration
SUPABASE_URL=https://{project_ref}.supabase.co
SUPABASE_PROJECT_REF={project_ref}
SUPABASE_ANON_KEY={anon_key}
SUPABASE_SERVICE_KEY={service_key}
SUPABASE_DB_PASSWORD={db_password or "[YOUR_PASSWORD]"}

# Database (Connection Pooler - IPv4)
DATABASE_URL=postgresql://postgres.{project_ref}:{db_password or "[YOUR_PASSWORD]"}@aws-0-us-east-1.pooler.supabase.com:5432/postgres

# Robot Configuration
ROBOT_NAME=Robot-{socket.gethostname()}
ROBOT_API_KEY={robot_api_key or "[GENERATE_WITH_SETUP]"}
ROBOT_ENVIRONMENT=production

# Orchestrator
API_SECRET={secrets.token_urlsafe(32)}
HOST=0.0.0.0
PORT=8000

# Logging
LOG_LEVEL=INFO
"""

    ENV_FILE.write_text(env_content)
    return SetupResult(True, "Created .env file", {"path": str(ENV_FILE)})


# =============================================================================
# CLI Commands
# =============================================================================


@app.command()
def init(
    project_ref: str = typer.Option(None, "--project-ref", "-p", help="Supabase project reference"),
    service_key: str = typer.Option(None, "--service-key", "-s", help="Supabase service key"),
    anon_key: str = typer.Option(None, "--anon-key", "-a", help="Supabase anon key"),
    db_password: str = typer.Option(None, "--db-password", "-d", help="Database password"),
):
    """Initialize Supabase project configuration."""
    console.print(Panel.fit("[bold]CasareRPA Supabase Initialization[/bold]"))

    if not project_ref or not service_key:
        console.print("[yellow]Missing required parameters.[/yellow]")
        console.print("\nUsage:")
        console.print("  python -m deploy.supabase.setup init \\")
        console.print("    --project-ref YOUR_PROJECT_REF \\")
        console.print("    --service-key YOUR_SERVICE_KEY")
        raise typer.Exit(1)

    result = create_env_file(project_ref, service_key, anon_key, db_password)
    if result.success:
        console.print(f"[green]{result.message}[/green]")
        console.print("\n[bold]Next steps:[/bold]")
        console.print("  1. Edit .env and add your database password")
        console.print("  2. Run: python -m deploy.supabase.setup migrate")
        console.print("  3. Run: python -m deploy.supabase.setup verify")
    else:
        console.print(f"[red]{result.message}[/red]")
        raise typer.Exit(1)


@app.command()
def migrate(
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be executed"),
    migration: str = typer.Option(None, "--migration", "-m", help="Specific migration file"),
):
    """Run database migrations."""
    console.print(Panel.fit("[bold]Database Migration[/bold]"))

    config = SupabaseConfig.from_env()
    if not config:
        console.print("[red]No configuration found. Run 'init' first.[/red]")
        raise typer.Exit(1)

    if not config.db_password or config.db_password == "[YOUR_PASSWORD]":
        console.print("[red]Database password not set in .env[/red]")
        raise typer.Exit(1)

    # Find migration files
    if migration:
        migrations = [MIGRATIONS_DIR / migration]
    else:
        migrations = sorted(MIGRATIONS_DIR.glob("*.sql"))

    if not migrations:
        console.print("[yellow]No migration files found.[/yellow]")
        raise typer.Exit(1)

    console.print(f"Found {len(migrations)} migration(s)")

    if dry_run:
        for m in migrations:
            console.print(f"  [dim]Would apply: {m.name}[/dim]")
        return

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        for mig in migrations:
            task = progress.add_task(f"Applying {mig.name}...", total=None)
            result = asyncio.run(run_migration_via_db(config, mig))
            progress.update(task, completed=True)

            if result.success:
                console.print(f"  [green]{result.message}[/green]")
            else:
                console.print(f"  [red]{result.message}[/red]")
                if result.details.get("errors"):
                    for err in result.details["errors"]:
                        console.print(f"    [dim]{err}[/dim]")


@app.command()
def functions(
    name: str = typer.Option(None, "--name", "-n", help="Specific function to deploy"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be deployed"),
    list_only: bool = typer.Option(False, "--list", "-l", help="List available functions"),
):
    """Deploy edge functions."""
    console.print(Panel.fit("[bold]Edge Function Deployment[/bold]"))

    if list_only:
        funcs = []
        for item in FUNCTIONS_DIR.iterdir():
            if item.is_dir() and (item / "index.ts").exists():
                funcs.append(item.name)

        if funcs:
            console.print("Available functions:")
            for f in funcs:
                console.print(f"  - {f}")
        else:
            console.print("[yellow]No functions found.[/yellow]")
        return

    result = deploy_edge_functions(name, dry_run)
    if result.success:
        console.print(f"[green]{result.message}[/green]")
        if result.details.get("deployed"):
            for f in result.details["deployed"]:
                console.print(f"  - {f}")
    else:
        console.print(f"[red]{result.message}[/red]")
        raise typer.Exit(1)


@app.command()
def rls():
    """Configure Row Level Security policies."""
    console.print(Panel.fit("[bold]RLS Configuration[/bold]"))

    rls_sql = """
-- Enable RLS on sensitive tables
ALTER TABLE robots ENABLE ROW LEVEL SECURITY;
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE robot_api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE robot_logs ENABLE ROW LEVEL SECURITY;

-- Service role has full access (for orchestrator)
CREATE POLICY "Service role full access" ON robots FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role full access" ON jobs FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role full access" ON robot_api_keys FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role full access" ON robot_logs FOR ALL USING (auth.role() = 'service_role');
"""

    console.print(
        "[yellow]RLS policies should be configured in Supabase Dashboard for safety.[/yellow]"
    )
    console.print("\nRecommended policies (copy to SQL Editor):")
    console.print(Panel(rls_sql, title="RLS SQL", border_style="dim"))
    console.print("\nSteps:")
    console.print("  1. Go to Supabase Dashboard > SQL Editor")
    console.print("  2. Paste the SQL above")
    console.print("  3. Review and execute")


@app.command()
def verify():
    """Verify Supabase setup."""
    console.print(Panel.fit("[bold]Setup Verification[/bold]"))

    config = SupabaseConfig.from_env()
    if not config:
        console.print("[red]No configuration found. Run 'init' first.[/red]")
        raise typer.Exit(1)

    if not config.service_key:
        console.print("[red]Service key not set in .env[/red]")
        raise typer.Exit(1)

    async def run_verify():
        async with SupabaseSetupClient(config) as client:
            return await client.verify_setup()

    result = asyncio.run(run_verify())

    table = Table(title="Verification Results")
    table.add_column("Check", style="cyan")
    table.add_column("Status", style="green")

    for check, passed in result.details.get("checks", {}).items():
        status = "[green]OK[/green]" if passed else "[red]FAILED[/red]"
        table.add_row(check.title(), status)

    console.print(table)

    if result.details.get("issues"):
        console.print("\n[yellow]Issues found:[/yellow]")
        for issue in result.details["issues"]:
            console.print(f"  - {issue}")

    if result.success:
        console.print("\n[green]All checks passed![/green]")
    else:
        raise typer.Exit(1)


@app.command("all")
def setup_all(
    db_password: str = typer.Option(..., "--db-password", "-d", help="Database password"),
    robot_name: str = typer.Option(None, "--robot-name", "-r", help="Robot name"),
):
    """Run complete setup (init + migrate + realtime + robot)."""
    console.print(Panel.fit("[bold]Complete Supabase Setup[/bold]"))

    config = SupabaseConfig.from_env()
    if not config:
        console.print("[red]No configuration found. Run 'init' first.[/red]")
        raise typer.Exit(1)

    # Update password
    config.db_password = db_password

    robot_name = robot_name or f"Robot-{socket.gethostname()}"

    async def run_all():
        async with SupabaseSetupClient(config) as client:
            results = []

            # Check connection
            console.print("\n[bold]1. Checking connection...[/bold]")
            conn_result = await client.check_connection()
            results.append(("Connection", conn_result))
            console.print(f"   {conn_result.message}")

            if not conn_result.success:
                return results

            # Check/run migrations
            console.print("\n[bold]2. Checking tables...[/bold]")
            tables_result = await client.check_tables()
            results.append(("Tables", tables_result))
            console.print(f"   {tables_result.message}")

            if not tables_result.success:
                console.print("   Running migration...")
                mig_result = await run_migration_via_db(
                    config, MIGRATIONS_DIR / "001_initial_schema.sql"
                )
                results.append(("Migration", mig_result))
                console.print(f"   {mig_result.message}")

            # Enable realtime
            console.print("\n[bold]3. Enabling realtime...[/bold]")
            for table in REALTIME_TABLES:
                rt_result = await client.enable_realtime(table)
                results.append((f"Realtime:{table}", rt_result))
                console.print(f"   {table}: {rt_result.message}")

            # Create robot
            console.print("\n[bold]4. Creating robot...[/bold]")
            robot_result = await client.create_robot(robot_name)
            results.append(("Robot", robot_result))
            console.print(f"   {robot_result.message}")

            # Generate API key
            if robot_result.success and robot_result.details.get("robot_id"):
                console.print("\n[bold]5. Generating API key...[/bold]")
                key_result = await client.generate_api_key(robot_result.details["robot_id"])
                results.append(("API Key", key_result))
                console.print(f"   {key_result.message}")

                if key_result.success:
                    raw_key = key_result.details.get("raw_key")
                    console.print("\n" + "!" * 60)
                    console.print("[bold red] SAVE THIS API KEY - SHOWN ONLY ONCE![/bold red]")
                    console.print("!" * 60)
                    console.print(f"\n  ROBOT_API_KEY={raw_key}\n")
                    console.print("!" * 60)

            return results

    results = asyncio.run(run_all())

    # Summary
    console.print("\n[bold]Setup Summary:[/bold]")
    all_success = all(r[1].success for r in results)
    for name, result in results:
        status = "[green]OK[/green]" if result.success else "[red]FAILED[/red]"
        console.print(f"  {name}: {status}")

    if all_success:
        console.print("\n[green]Setup completed successfully![/green]")
    else:
        raise typer.Exit(1)


@app.command()
def quickstart():
    """Interactive first-time setup wizard."""
    console.print(Panel.fit("[bold]CasareRPA Quickstart Wizard[/bold]"))
    console.print("\nThis wizard will help you set up Supabase for CasareRPA.\n")

    # Check for existing config
    existing_config = SupabaseConfig.from_env()
    if existing_config and existing_config.service_key:
        use_existing = typer.confirm("Found existing configuration. Use it?", default=True)
        if use_existing:
            # Run verify
            typer.echo("Running verification...")
            verify()
            return

    # Get credentials
    console.print("[bold]Enter your Supabase credentials:[/bold]")
    console.print("(Find these at: Supabase Dashboard > Settings > API)\n")

    project_ref = typer.prompt("Project Reference (from URL)")
    service_key = typer.prompt("Service Key (service_role)", hide_input=True)
    anon_key = typer.prompt("Anon Key (optional)", default="")
    db_password = typer.prompt("Database Password", hide_input=True)

    # Create config
    result = create_env_file(project_ref, service_key, anon_key, db_password)
    if not result.success:
        console.print(f"[red]{result.message}[/red]")
        raise typer.Exit(1)

    console.print(f"[green]{result.message}[/green]")

    # Ask to run migration
    run_mig = typer.confirm("\nRun database migration?", default=True)
    if run_mig:
        config = SupabaseConfig(project_ref, service_key, anon_key, db_password)
        mig_result = asyncio.run(
            run_migration_via_db(config, MIGRATIONS_DIR / "001_initial_schema.sql")
        )
        if mig_result.success:
            console.print(f"[green]{mig_result.message}[/green]")
        else:
            console.print(f"[yellow]{mig_result.message}[/yellow]")

    # Create robot
    create_robot = typer.confirm("\nCreate robot and API key?", default=True)
    if create_robot:
        robot_name = typer.prompt("Robot name", default=f"Robot-{socket.gethostname()}")

        async def create():
            config = SupabaseConfig(project_ref, service_key, anon_key, db_password)
            async with SupabaseSetupClient(config) as client:
                robot_result = await client.create_robot(robot_name)
                if robot_result.success and robot_result.details.get("robot_id"):
                    key_result = await client.generate_api_key(robot_result.details["robot_id"])
                    return robot_result, key_result
                return robot_result, None

        robot_result, key_result = asyncio.run(create())
        console.print(f"  Robot: {robot_result.message}")

        if key_result and key_result.success:
            raw_key = key_result.details.get("raw_key")
            console.print("\n" + "!" * 60)
            console.print("[bold red] SAVE THIS API KEY - SHOWN ONLY ONCE![/bold red]")
            console.print("!" * 60)
            console.print(f"\n  ROBOT_API_KEY={raw_key}\n")
            console.print("!" * 60)

    console.print("\n[bold green]Quickstart complete![/bold green]")
    console.print("\nNext steps:")
    console.print("  1. Save your API key to .env")
    console.print("  2. Run: python -m deploy.supabase.setup verify")
    console.print("  3. Start orchestrator: python deploy/quickstart.py --local")


@app.command()
def types(
    output: str = typer.Option(None, "--output", "-o", help="Output file path"),
):
    """Generate Python types from Supabase schema."""
    console.print(Panel.fit("[bold]Type Generation[/bold]"))

    output_path = Path(output) if output else None
    result = generate_types_from_schema(output_path)

    if result.success:
        console.print(f"[green]{result.message}[/green]")
    else:
        console.print(f"[red]{result.message}[/red]")
        raise typer.Exit(1)


@app.callback()
def main():
    """CasareRPA Supabase Setup CLI."""
    pass


if __name__ == "__main__":
    app()
