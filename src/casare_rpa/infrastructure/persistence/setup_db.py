"""
Database setup and migration script for CasareRPA.

Applies SQL migrations to PostgreSQL database for workflow storage.

Usage:
    python -m casare_rpa.infrastructure.persistence.setup_db

Environment variables:
    DB_HOST - PostgreSQL host (default: localhost)
    DB_PORT - PostgreSQL port (default: 5432)
    DB_NAME - Database name (default: casare_rpa)
    DB_USER - Database user (default: casare_user)
    DB_PASSWORD - Database password (required)
"""

import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

# Load environment variables from .env file
load_dotenv()


try:
    import asyncpg
except ImportError:
    logger.error("asyncpg not installed. Run: pip install asyncpg")
    sys.exit(1)


async def get_db_connection():
    """
    Create database connection from environment variables.

    Returns:
        asyncpg.Connection
    """
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = int(os.getenv("DB_PORT", "5432"))
    db_name = os.getenv("DB_NAME", "casare_rpa")
    db_user = os.getenv("DB_USER", "casare_user")
    db_password = os.getenv("DB_PASSWORD")

    if not db_password:
        logger.error("DB_PASSWORD environment variable not set")
        sys.exit(1)

    logger.info(
        "Connecting to PostgreSQL: {}@{}:{}/{}",
        db_user,
        db_host,
        db_port,
        db_name,
    )

    try:
        conn = await asyncpg.connect(
            host=db_host,
            port=db_port,
            database=db_name,
            user=db_user,
            password=db_password,
        )
        logger.info("Database connection established")
        return conn

    except Exception as e:
        logger.error("Failed to connect to database: {}", e)
        logger.error("Ensure PostgreSQL is running and credentials are correct in .env")
        sys.exit(1)


async def apply_migration(conn: asyncpg.Connection, migration_file: Path) -> bool:
    """
    Apply a single migration file.

    Args:
        conn: Database connection
        migration_file: Path to .sql migration file

    Returns:
        True if successful, False otherwise
    """
    logger.info("Applying migration: {}", migration_file.name)

    try:
        sql = migration_file.read_text(encoding="utf-8")
        await conn.execute(sql)
        logger.info("Migration applied successfully: {}", migration_file.name)
        return True

    except Exception as e:
        logger.error("Migration failed: {} - {}", migration_file.name, e)
        return False


async def setup_database():
    """
    Apply all migrations in order.

    Migrations are applied in alphabetical order from the migrations/ directory.
    """
    # Get migrations directory
    migrations_dir = Path(__file__).parent / "migrations"

    if not migrations_dir.exists():
        logger.error("Migrations directory not found: {}", migrations_dir)
        sys.exit(1)

    # Get all .sql migration files
    migration_files = sorted(migrations_dir.glob("*.sql"))

    if not migration_files:
        logger.warning("No migration files found in {}", migrations_dir)
        return

    logger.info("Found {} migration(s)", len(migration_files))

    # Connect to database
    conn = await get_db_connection()

    try:
        # Apply each migration
        for migration_file in migration_files:
            success = await apply_migration(conn, migration_file)
            if not success:
                logger.error("Stopping migration process due to error")
                sys.exit(1)

        logger.info("All migrations applied successfully!")

        # Verify tables created
        tables = await conn.fetch(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
            """
        )

        logger.info("Created tables:")
        for row in tables:
            logger.info("  - {}", row["table_name"])

        # Verify views created
        views = await conn.fetch(
            """
            SELECT table_name
            FROM information_schema.views
            WHERE table_schema = 'public'
            ORDER BY table_name
            """
        )

        if views:
            logger.info("Created views:")
            for row in views:
                logger.info("  - {}", row["table_name"])

    finally:
        await conn.close()
        logger.info("Database connection closed")


async def verify_setup():
    """
    Verify database setup is correct.

    Returns:
        True if all tables exist, False otherwise
    """
    conn = await get_db_connection()

    try:
        # Check required tables
        required_tables = ["workflows", "jobs", "schedules", "workflow_versions"]

        for table_name in required_tables:
            exists = await conn.fetchval(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = $1
                )
                """,
                table_name,
            )

            if exists:
                logger.info("Table exists: {}", table_name)
            else:
                logger.error("Table missing: {}", table_name)
                return False

        logger.info("Database setup verified successfully!")
        return True

    finally:
        await conn.close()


def main():
    """Main entry point."""
    logger.info("CasareRPA Database Setup")
    logger.info("=" * 50)

    # Check environment
    if not os.getenv("DB_PASSWORD"):
        logger.error(
            "DB_PASSWORD not set in environment. Create .env file with database credentials."
        )
        logger.info("\nExample .env file:")
        logger.info("DB_HOST=localhost")
        logger.info("DB_PORT=5432")
        logger.info("DB_NAME=casare_rpa")
        logger.info("DB_USER=casare_user")
        logger.info("DB_PASSWORD=your_password_here")
        sys.exit(1)

    # Run setup
    try:
        asyncio.run(setup_database())

        # Verify setup
        logger.info("\nVerifying database setup...")
        if asyncio.run(verify_setup()):
            logger.info("\nDatabase setup complete! ✓")
            logger.info("\nNext steps:")
            logger.info(
                "1. Start Orchestrator API: uvicorn casare_rpa.infrastructure.orchestrator.api.main:app"
            )
            logger.info("2. Start Robot: python -m casare_rpa.robot.cli start")
            logger.info("3. Start Canvas: python run.py")
        else:
            logger.error("\nDatabase verification failed!")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.warning("\nSetup interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error("Setup failed: {}", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
