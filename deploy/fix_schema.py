#!/usr/bin/env python3
"""
DEPRECATED: This script is deprecated. Use the unified setup instead.

The functionality of this script has been merged into:
    python -m deploy.supabase.setup migrate

For migration purposes:
    python -m deploy.supabase.setup all --db-password YOUR_PASSWORD

Quick fix for missing database columns.

Run this to add missing columns to existing Supabase tables.

Usage:
    python deploy/fix_schema.py
"""

import warnings

warnings.warn(
    "fix_schema.py is deprecated. Use: python -m deploy.supabase.setup migrate",
    DeprecationWarning,
    stacklevel=2,
)

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    import asyncpg
except ImportError:
    print("Installing asyncpg...")
    import subprocess

    subprocess.run([sys.executable, "-m", "pip", "install", "asyncpg"], check=True)
    import asyncpg

from dotenv import load_dotenv

# Load .env
load_dotenv(Path(__file__).parent.parent / ".env")

DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")


async def main():
    print("=" * 60)
    print(" CasareRPA Database Schema Fix")
    print("=" * 60)

    if not DATABASE_URL:
        print("ERROR: DATABASE_URL not set in .env")
        return

    print("\nConnecting to database...")
    print(f"  URL: {DATABASE_URL[:50]}...")

    try:
        conn = await asyncpg.connect(DATABASE_URL)
        print("  [OK] Connected")
    except Exception as e:
        print(f"  [FAIL] {e}")
        return

    try:
        # Fix 1: Add registered_at to robots table
        print("\n[1/4] Checking robots.registered_at column...")
        try:
            result = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'robots' AND column_name = 'registered_at'
                )
            """)
            if result:
                print("  [OK] Column exists")
            else:
                print("  Adding column...")
                await conn.execute("""
                    ALTER TABLE robots
                    ADD COLUMN registered_at TIMESTAMPTZ DEFAULT NOW()
                """)
                print("  [OK] Added registered_at")
        except Exception as e:
            print(f"  [WARN] {e}")

        # Fix 2: Check job_queue table exists
        print("\n[2/4] Checking job_queue table...")
        try:
            result = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_name = 'job_queue'
                )
            """)
            if result:
                print("  [OK] Table exists")
            else:
                print("  Creating job_queue table...")
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS job_queue (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        workflow_id VARCHAR(255) NOT NULL,
                        workflow_name VARCHAR(255) NOT NULL,
                        workflow_json TEXT NOT NULL,
                        priority INTEGER DEFAULT 1,
                        status VARCHAR(50) DEFAULT 'pending' NOT NULL,
                        robot_id VARCHAR(255),
                        environment VARCHAR(100) DEFAULT 'default' NOT NULL,
                        visible_after TIMESTAMPTZ DEFAULT NOW() NOT NULL,
                        created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
                        started_at TIMESTAMPTZ,
                        completed_at TIMESTAMPTZ,
                        error_message TEXT,
                        result JSONB DEFAULT '{}'::jsonb,
                        retry_count INTEGER DEFAULT 0 NOT NULL,
                        max_retries INTEGER DEFAULT 3 NOT NULL,
                        variables JSONB DEFAULT '{}'::jsonb,
                        metadata JSONB DEFAULT '{}'::jsonb
                    )
                """)
                print("  [OK] Created job_queue table")
        except Exception as e:
            print(f"  [WARN] {e}")

        # Fix 3: Add visible_after to job_queue if missing
        print("\n[3/4] Checking job_queue.visible_after column...")
        try:
            result = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'job_queue' AND column_name = 'visible_after'
                )
            """)
            if result:
                print("  [OK] Column exists")
            else:
                print("  Adding column...")
                await conn.execute("""
                    ALTER TABLE job_queue
                    ADD COLUMN visible_after TIMESTAMPTZ DEFAULT NOW() NOT NULL
                """)
                print("  [OK] Added visible_after")
        except Exception as e:
            print(f"  [WARN] {e}")

        # Fix 4: Create claim_jobs function
        print("\n[4/4] Creating claim_jobs function...")
        try:
            await conn.execute("""
                CREATE OR REPLACE FUNCTION claim_jobs(
                    p_environment VARCHAR(100),
                    p_robot_id VARCHAR(255),
                    p_batch_size INTEGER,
                    p_visibility_timeout_seconds INTEGER
                )
                RETURNS SETOF job_queue AS $$
                BEGIN
                    RETURN QUERY
                    WITH claimed AS (
                        SELECT id
                        FROM job_queue
                        WHERE status = 'pending'
                          AND visible_after <= NOW()
                          AND (environment = p_environment OR environment = 'default' OR p_environment = 'default')
                        ORDER BY priority DESC, created_at ASC
                        LIMIT p_batch_size
                        FOR UPDATE SKIP LOCKED
                    )
                    UPDATE job_queue jq
                    SET status = 'running',
                        robot_id = p_robot_id,
                        started_at = NOW(),
                        visible_after = NOW() + (p_visibility_timeout_seconds || ' seconds')::INTERVAL
                    FROM claimed
                    WHERE jq.id = claimed.id
                    RETURNING jq.*;
                END;
                $$ LANGUAGE plpgsql
            """)
            print("  [OK] Created claim_jobs function")
        except Exception as e:
            print(f"  [WARN] {e}")

        # Verify schema
        print("\n" + "=" * 60)
        print(" Schema Verification")
        print("=" * 60)

        # Check robots columns
        print("\nRobots table columns:")
        rows = await conn.fetch("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'robots'
            ORDER BY ordinal_position
        """)
        for row in rows:
            print(f"  - {row['column_name']}: {row['data_type']}")

        # Check job_queue columns
        print("\nJob_queue table columns:")
        rows = await conn.fetch("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'job_queue'
            ORDER BY ordinal_position
        """)
        for row in rows:
            print(f"  - {row['column_name']}: {row['data_type']}")

        print("\n[DONE] Schema fixes applied!")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
