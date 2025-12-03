"""
CasareRPA Database Migrations

Consolidated migration system for PostgreSQL/Supabase.

Usage:
    python -m deploy.migrations.migrate up      # Apply all pending
    python -m deploy.migrations.migrate status  # Show status
    python -m deploy.migrations.migrate down    # Rollback last
    python -m deploy.migrations.migrate verify  # Verify integrity
    python -m deploy.migrations.migrate reset   # Reset all

See README.md for detailed documentation.
"""

__version__ = "1.0.0"
__all__ = ["migrate"]
