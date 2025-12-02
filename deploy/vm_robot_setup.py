#!/usr/bin/env python3
"""
DEPRECATED: This script is deprecated. Use the unified setup instead.

The functionality of this script has been merged into:
    python -m deploy.supabase.setup quickstart

For VM robot setup:
    python -m deploy.supabase.setup init --project-ref REF --service-key KEY
    python -m deploy.supabase.setup all --db-password PASSWORD

CasareRPA VM Robot Setup - Minimal script to deploy robot on VM.

Copy this single file to your VM along with:
1. The CasareRPA source code (or pip install casare-rpa)
2. Your ROBOT_API_KEY from the setup

Usage:
    python vm_robot_setup.py --db-password YOUR_SUPABASE_PASSWORD --api-key crpa_xxxxx

Or create .env first and just run:
    python vm_robot_setup.py
"""

import warnings

warnings.warn(
    "vm_robot_setup.py is deprecated. Use: python -m deploy.supabase.setup quickstart",
    DeprecationWarning,
    stacklevel=2,
)

import argparse
import asyncio
import os
import socket
import subprocess
import sys
from pathlib import Path


# Supabase configuration (your project)
SUPABASE_PROJECT_REF = "znaauaswqmurwfglantv"
SUPABASE_URL = f"https://{SUPABASE_PROJECT_REF}.supabase.co"
# Using Connection Pooler (IPv4) - aws-1-eu-central-1
DATABASE_HOST = "aws-1-eu-central-1.pooler.supabase.com"
DATABASE_USER = f"postgres.{SUPABASE_PROJECT_REF}"


def create_env_file(db_password: str, api_key: str, robot_name: str) -> Path:
    """Create minimal .env file for robot."""
    env_content = f"""# CasareRPA Robot Configuration (Auto-generated)
# Supabase PostgreSQL via Connection Pooler
DATABASE_URL=postgresql://{DATABASE_USER}:{db_password}@{DATABASE_HOST}:5432/postgres
POSTGRES_URL=postgresql://{DATABASE_USER}:{db_password}@{DATABASE_HOST}:5432/postgres
PGQUEUER_DB_URL=postgresql://{DATABASE_USER}:{db_password}@{DATABASE_HOST}:5432/postgres

# Supabase
SUPABASE_URL={SUPABASE_URL}

# Robot
ROBOT_NAME={robot_name}
ROBOT_API_KEY={api_key}
ROBOT_ENVIRONMENT=production

# Logging
LOG_LEVEL=INFO
"""

    env_path = Path(".env")
    env_path.write_text(env_content)
    print(f"[OK] Created {env_path}")
    return env_path


def check_dependencies() -> bool:
    """Check if required packages are installed."""
    required = ["asyncpg", "loguru", "orjson", "typer", "rich"]
    missing = []

    for pkg in required:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)

    if missing:
        print(f"[WARN] Missing packages: {', '.join(missing)}")
        print("Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install"] + missing, check=True)

    return True


def start_robot(robot_name: str):
    """Start the robot agent."""
    print(f"\n{'='*50}")
    print(f" Starting Robot: {robot_name}")
    print(f"{'='*50}\n")

    cmd = [
        sys.executable,
        "-m",
        "casare_rpa.robot.cli",
        "start",
        "--name",
        robot_name,
        "--verbose",
    ]

    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\nRobot stopped.")
    except subprocess.CalledProcessError as e:
        print(f"Robot failed to start: {e}")
        sys.exit(1)


async def test_connection(db_password: str) -> bool:
    """Test database connection."""
    try:
        import asyncpg

        conn_str = f"postgresql://postgres:{db_password}@{DATABASE_HOST}:5432/postgres"
        conn = await asyncpg.connect(conn_str)
        await conn.fetchrow("SELECT 1")
        await conn.close()
        print("[OK] Database connection successful")
        return True
    except Exception as e:
        print(f"[FAIL] Database connection failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="CasareRPA VM Robot Setup")
    parser.add_argument("--db-password", help="Supabase database password")
    parser.add_argument("--api-key", help="Robot API key (crpa_xxxxx)")
    parser.add_argument(
        "--robot-name", help="Robot name", default=f"VM-Robot-{socket.gethostname()}"
    )
    parser.add_argument("--test-only", action="store_true", help="Test connection only")

    args = parser.parse_args()

    print("\n" + "=" * 50)
    print(" CasareRPA VM Robot Setup")
    print("=" * 50)

    # Check for existing .env
    env_path = Path(".env")
    db_password = args.db_password
    api_key = args.api_key

    if env_path.exists() and not db_password:
        print(f"[INFO] Using existing {env_path}")
        # Load from .env
        for line in env_path.read_text().split("\n"):
            if "=" in line and not line.strip().startswith("#"):
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip()
    elif not db_password:
        print("\n[ERROR] Database password required!")
        print("\nUsage:")
        print(
            "  python vm_robot_setup.py --db-password YOUR_PASSWORD --api-key crpa_xxxxx"
        )
        print("\nOr create .env file with DATABASE_URL and ROBOT_API_KEY")
        sys.exit(1)
    else:
        # Create .env
        if not api_key:
            print("\n[WARN] No API key provided. Robot will fail authentication.")
            print("       Get API key from: python deploy/auto_setup.py setup")
            api_key = "REPLACE_WITH_YOUR_API_KEY"

        create_env_file(db_password, api_key, args.robot_name)

    # Check dependencies
    check_dependencies()

    # Test connection
    test_password = (
        db_password or os.getenv("DATABASE_URL", "").split(":")[-1].split("@")[0]
    )
    if test_password and test_password != "REPLACE_WITH_YOUR_API_KEY":
        if not asyncio.run(test_connection(test_password)):
            print("\n[ERROR] Cannot connect to Supabase database")
            print("        Check your password and network connection")
            sys.exit(1)

    if args.test_only:
        print("\n[OK] Connection test passed!")
        return

    # Start robot
    robot_name = args.robot_name or os.getenv(
        "ROBOT_NAME", f"VM-Robot-{socket.gethostname()}"
    )
    start_robot(robot_name)


if __name__ == "__main__":
    main()
