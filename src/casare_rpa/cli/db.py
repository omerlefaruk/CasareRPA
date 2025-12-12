"""
CasareRPA Unified Database Setup.

Handles setup for both local Postgres and Supabase.
"""

import os
import typer
import asyncpg
import asyncio
from pathlib import Path

app = typer.Typer()


async def run_sql_file(conn, file_path: Path):
    """Read and execute SQL file."""
    if not file_path.exists():
        typer.echo(f"Error: SQL file not found: {file_path}", err=True)
        return

    typer.echo(f"Applying {file_path.name}...")
    sql = file_path.read_text()
    try:
        await conn.execute(sql)
        typer.echo("  Success.")
    except Exception as e:
        typer.echo(f"  Error applying SQL: {e}", err=True)


async def _setup_postgres(url: str):
    """Setup standard Postgres database."""
    try:
        conn = await asyncpg.connect(url)

        # Locate schema file - unified logic
        # We prioritize the 'supabase_schema.sql' as the master schema now
        # to ensure parity between local and cloud.
        base_path = Path(__file__).resolve().parents[3]
        schema_path = base_path / "deploy" / "supabase" / "supabase_schema.sql"

        if not schema_path.exists():
            # Fallback to migrations if supabase schema missing (legacy compat)
            schema_path = base_path / "deploy" / "migrations" / "setup_db.sql"

        await run_sql_file(conn, schema_path)
        await conn.close()

    except Exception as e:
        typer.echo(f"Connection failed: {e}", err=True)
        raise typer.Exit(1)


@app.command("setup")
def setup_db(
    url: str = typer.Option(None, "--url", help="Database connection URL"),
    supabase: bool = typer.Option(
        False, "--supabase", help="Use Supabase (requires env vars)"
    ),
):
    """
    Initialize the database schema.

    By default, looks for DATABASE_URL env var.
    If --supabase is set, checks SUPABASE_URL/KEY (though usually Supabase is managed via its own CLI,
    this can apply additional migrations).
    """
    from dotenv import load_dotenv

    load_dotenv()

    if not url:
        url = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")

    if not url:
        typer.echo(
            "Error: No database URL provided and DATABASE_URL not set.", err=True
        )
        raise typer.Exit(1)

    typer.echo(f"Setting up database at {url.split('@')[-1]}...")  # Mask creds

    asyncio.run(_setup_postgres(url))
    typer.echo("Database setup complete.")


if __name__ == "__main__":
    app()
