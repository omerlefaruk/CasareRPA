#!/usr/bin/env python3
"""
CasareRPA Migration Runner

A comprehensive database migration tool for PostgreSQL.

Usage:
    python -m deploy.migrations.migrate up                    # Apply all pending migrations
    python -m deploy.migrations.migrate down                  # Rollback last migration
    python -m deploy.migrations.migrate down --steps 3        # Rollback last 3 migrations
    python -m deploy.migrations.migrate status                # Show applied/pending migrations
    python -m deploy.migrations.migrate reset                 # Rollback all migrations
    python -m deploy.migrations.migrate verify                # Verify migration checksums
    python -m deploy.migrations.migrate --dry-run up          # Preview without executing

Environment Variables:
    DATABASE_URL            PostgreSQL connection string
    SUPABASE_DB_URL         Alternative: Supabase database URL

Example:
    DATABASE_URL="postgresql://user:pass@localhost/casare_rpa" python -m deploy.migrations.migrate up
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import asyncpg
except ImportError:
    print("ERROR: asyncpg is required. Install with: pip install asyncpg")
    sys.exit(1)


# =============================================================================
# Configuration
# =============================================================================

MIGRATIONS_DIR = Path(__file__).parent / "versions"
DOWN_MIGRATIONS_DIR = Path(__file__).parent / "down"
MIGRATIONS_TABLE = "_migrations"


@dataclass
class MigrationFile:
    """Represents a migration file."""

    version: str
    name: str
    path: Path
    checksum: str

    @classmethod
    def from_path(cls, path: Path) -> "MigrationFile":
        """Create MigrationFile from a path."""
        # Extract version from filename (e.g., "001_initial_schema.sql" -> "001")
        match = re.match(r"^(\d+)_(.+)\.sql$", path.name)
        if not match:
            raise ValueError(f"Invalid migration filename: {path.name}")

        version = match.group(1)
        name = match.group(2)

        # Calculate checksum
        content = path.read_text(encoding="utf-8")
        checksum = hashlib.sha256(content.encode()).hexdigest()[:16]

        return cls(version=version, name=name, path=path, checksum=checksum)


@dataclass
class AppliedMigration:
    """Represents an applied migration from the database."""

    id: int
    version: str
    name: str
    checksum: str
    applied_at: datetime
    execution_time_ms: int


# =============================================================================
# Database Operations
# =============================================================================


async def get_connection(database_url: str) -> asyncpg.Connection:
    """Get a database connection."""
    return await asyncpg.connect(database_url)


async def ensure_migrations_table(conn: asyncpg.Connection) -> None:
    """Create the migrations tracking table if it doesn't exist."""
    await conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {MIGRATIONS_TABLE} (
            id SERIAL PRIMARY KEY,
            version VARCHAR(10) NOT NULL UNIQUE,
            name VARCHAR(255) NOT NULL,
            checksum VARCHAR(32) NOT NULL,
            applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            execution_time_ms INTEGER NOT NULL DEFAULT 0,
            git_commit VARCHAR(40)
        );

        CREATE INDEX IF NOT EXISTS idx_migrations_version
            ON {MIGRATIONS_TABLE}(version);

        COMMENT ON TABLE {MIGRATIONS_TABLE} IS 'Tracks applied database migrations';
    """)


async def get_applied_migrations(conn: asyncpg.Connection) -> list[AppliedMigration]:
    """Get list of applied migrations from database."""
    rows = await conn.fetch(f"""
        SELECT id, version, name, checksum, applied_at, execution_time_ms
        FROM {MIGRATIONS_TABLE}
        ORDER BY version ASC
    """)
    return [
        AppliedMigration(
            id=row["id"],
            version=row["version"],
            name=row["name"],
            checksum=row["checksum"],
            applied_at=row["applied_at"],
            execution_time_ms=row["execution_time_ms"],
        )
        for row in rows
    ]


async def record_migration(
    conn: asyncpg.Connection,
    migration: MigrationFile,
    execution_time_ms: int,
    git_commit: str | None = None,
) -> None:
    """Record a migration as applied."""
    await conn.execute(
        f"""
        INSERT INTO {MIGRATIONS_TABLE} (version, name, checksum, execution_time_ms, git_commit)
        VALUES ($1, $2, $3, $4, $5)
        """,
        migration.version,
        migration.name,
        migration.checksum,
        execution_time_ms,
        git_commit,
    )


async def remove_migration_record(conn: asyncpg.Connection, version: str) -> None:
    """Remove a migration record (for rollback)."""
    await conn.execute(
        f"DELETE FROM {MIGRATIONS_TABLE} WHERE version = $1",
        version,
    )


# =============================================================================
# Migration Discovery
# =============================================================================


def discover_migrations() -> list[MigrationFile]:
    """Discover all migration files in the versions directory."""
    if not MIGRATIONS_DIR.exists():
        raise FileNotFoundError(f"Migrations directory not found: {MIGRATIONS_DIR}")

    migrations = []
    for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
        try:
            migrations.append(MigrationFile.from_path(path))
        except ValueError as e:
            print(f"WARNING: Skipping invalid migration file: {e}")

    return migrations


def get_down_migration_path(migration: MigrationFile) -> Path | None:
    """Get the rollback script path for a migration."""
    down_path = DOWN_MIGRATIONS_DIR / f"{migration.version}_{migration.name}_down.sql"
    if down_path.exists():
        return down_path
    return None


# =============================================================================
# Migration Commands
# =============================================================================


async def cmd_up(
    conn: asyncpg.Connection,
    migrations: list[MigrationFile],
    applied: list[AppliedMigration],
    dry_run: bool = False,
) -> int:
    """Apply pending migrations."""
    applied_versions = {m.version for m in applied}
    pending = [m for m in migrations if m.version not in applied_versions]

    if not pending:
        print("No pending migrations.")
        return 0

    print(f"Found {len(pending)} pending migration(s):\n")

    git_commit = get_git_commit()
    applied_count = 0

    for migration in pending:
        print(f"  [{migration.version}] {migration.name}")

        if dry_run:
            print(f"      (dry-run) Would apply: {migration.path}")
            continue

        # Read and execute migration
        sql = migration.path.read_text(encoding="utf-8")
        start_time = datetime.now(timezone.utc)

        try:
            async with conn.transaction():
                await conn.execute(sql)
                execution_time_ms = int(
                    (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
                )
                await record_migration(conn, migration, execution_time_ms, git_commit)
                print(f"      Applied in {execution_time_ms}ms")
                applied_count += 1
        except Exception as e:
            print(f"      ERROR: {e}")
            return 1

    print(f"\nApplied {applied_count} migration(s).")
    return 0


async def cmd_down(
    conn: asyncpg.Connection,
    migrations: list[MigrationFile],
    applied: list[AppliedMigration],
    steps: int = 1,
    dry_run: bool = False,
) -> int:
    """Rollback migrations."""
    if not applied:
        print("No migrations to rollback.")
        return 0

    # Get migrations to rollback (in reverse order)
    to_rollback = list(reversed(applied[-steps:]))

    print(f"Rolling back {len(to_rollback)} migration(s):\n")

    for applied_migration in to_rollback:
        # Find corresponding migration file
        migration = next(
            (m for m in migrations if m.version == applied_migration.version),
            None,
        )

        down_path = None
        if migration:
            down_path = get_down_migration_path(migration)

        print(f"  [{applied_migration.version}] {applied_migration.name}")

        if down_path is None:
            print(f"      WARNING: No rollback script found for {applied_migration.version}")
            print(
                f"      Expected: {DOWN_MIGRATIONS_DIR}/{applied_migration.version}_{applied_migration.name}_down.sql"
            )
            continue

        if dry_run:
            print(f"      (dry-run) Would rollback: {down_path}")
            continue

        # Read and execute rollback
        sql = down_path.read_text(encoding="utf-8")
        start_time = datetime.now(timezone.utc)

        try:
            async with conn.transaction():
                await conn.execute(sql)
                await remove_migration_record(conn, applied_migration.version)
                execution_time_ms = int(
                    (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
                )
                print(f"      Rolled back in {execution_time_ms}ms")
        except Exception as e:
            print(f"      ERROR: {e}")
            return 1

    print(f"\nRolled back {len(to_rollback)} migration(s).")
    return 0


async def cmd_status(
    migrations: list[MigrationFile],
    applied: list[AppliedMigration],
) -> int:
    """Show migration status."""
    applied_map = {m.version: m for m in applied}

    print("Migration Status:\n")
    print(f"{'Version':<10} {'Name':<40} {'Status':<12} {'Applied At':<24} {'Checksum'}")
    print("-" * 110)

    for migration in migrations:
        applied_m = applied_map.get(migration.version)
        if applied_m:
            status = "APPLIED"
            applied_at = applied_m.applied_at.strftime("%Y-%m-%d %H:%M:%S")
            checksum_match = "OK" if applied_m.checksum == migration.checksum else "MISMATCH!"
        else:
            status = "PENDING"
            applied_at = "-"
            checksum_match = "-"

        print(
            f"{migration.version:<10} {migration.name:<40} {status:<12} {applied_at:<24} {checksum_match}"
        )

    # Summary
    applied_count = len(applied)
    pending_count = len(migrations) - applied_count
    print(f"\nTotal: {len(migrations)} | Applied: {applied_count} | Pending: {pending_count}")

    return 0


async def cmd_verify(
    migrations: list[MigrationFile],
    applied: list[AppliedMigration],
) -> int:
    """Verify migration checksums."""
    applied_map = {m.version: m for m in applied}
    issues = []

    print("Verifying migration checksums...\n")

    for migration in migrations:
        applied_m = applied_map.get(migration.version)
        if applied_m and applied_m.checksum != migration.checksum:
            issues.append(
                {
                    "version": migration.version,
                    "name": migration.name,
                    "expected": applied_m.checksum,
                    "actual": migration.checksum,
                }
            )
            print(f"  [{migration.version}] {migration.name}: CHECKSUM MISMATCH")
            print(f"      Database: {applied_m.checksum}")
            print(f"      File:     {migration.checksum}")
        elif applied_m:
            print(f"  [{migration.version}] {migration.name}: OK")

    if issues:
        print(f"\nWARNING: {len(issues)} migration(s) have been modified after being applied!")
        print("This could indicate tampering or accidental changes.")
        return 1

    print("\nAll checksums verified successfully.")
    return 0


async def cmd_reset(
    conn: asyncpg.Connection,
    migrations: list[MigrationFile],
    applied: list[AppliedMigration],
    dry_run: bool = False,
) -> int:
    """Rollback all migrations."""
    if not applied:
        print("No migrations to reset.")
        return 0

    print(f"WARNING: This will rollback ALL {len(applied)} applied migrations!\n")

    if not dry_run:
        confirm = input("Type 'RESET' to confirm: ")
        if confirm != "RESET":
            print("Reset cancelled.")
            return 1

    return await cmd_down(conn, migrations, applied, steps=len(applied), dry_run=dry_run)


# =============================================================================
# Utilities
# =============================================================================


def get_database_url() -> str:
    """Get database URL from environment."""
    url = os.environ.get("DATABASE_URL") or os.environ.get("SUPABASE_DB_URL")
    if not url:
        raise ValueError(
            "No database URL found. Set DATABASE_URL or SUPABASE_DB_URL environment variable."
        )
    return url


def get_git_commit() -> str | None:
    """Get current git commit hash if available."""
    try:
        import subprocess

        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()[:40]
    except Exception:
        pass
    return None


# =============================================================================
# Main
# =============================================================================


async def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="CasareRPA Database Migration Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "command",
        choices=["up", "down", "status", "verify", "reset"],
        help="Migration command to run",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without executing",
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=1,
        help="Number of migrations to rollback (for 'down' command)",
    )
    parser.add_argument(
        "--database",
        type=str,
        help="Override database URL",
    )

    args = parser.parse_args()

    # Get database URL
    try:
        database_url = args.database or get_database_url()
    except ValueError as e:
        print(f"ERROR: {e}")
        return 1

    # Discover migrations
    try:
        migrations = discover_migrations()
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        return 1

    if not migrations:
        print("No migration files found.")
        return 1

    # Connect to database
    try:
        conn = await get_connection(database_url)
    except Exception as e:
        print(f"ERROR: Failed to connect to database: {e}")
        return 1

    try:
        # Ensure migrations table exists
        await ensure_migrations_table(conn)

        # Get applied migrations
        applied = await get_applied_migrations(conn)

        # Execute command
        if args.command == "up":
            return await cmd_up(conn, migrations, applied, args.dry_run)
        elif args.command == "down":
            return await cmd_down(conn, migrations, applied, args.steps, args.dry_run)
        elif args.command == "status":
            return await cmd_status(migrations, applied)
        elif args.command == "verify":
            return await cmd_verify(migrations, applied)
        elif args.command == "reset":
            return await cmd_reset(conn, migrations, applied, args.dry_run)
        else:
            print(f"Unknown command: {args.command}")
            return 1

    finally:
        await conn.close()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
