"""Verify PostgreSQL setup for CasareRPA"""

import sys
import asyncio
import psycopg2
from dotenv import load_dotenv
import os

# Fix Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()


def test_connection():
    """Test basic connection to PostgreSQL"""
    print("Testing PostgreSQL connection...")

    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", 5432)),
            database=os.getenv("DB_NAME", "casare_rpa"),
            user=os.getenv("DB_USER", "casare_user"),
            password=os.getenv("DB_PASSWORD", "postgre"),
        )

        cur = conn.cursor()
        cur.execute("SELECT version();")
        version = cur.fetchone()[0]
        print(f"✓ Connected to: {version}")

        # Check tables
        cur.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema='public'
            AND table_type='BASE TABLE'
            ORDER BY table_name
        """)
        tables = [row[0] for row in cur.fetchall()]

        print(f"\n✓ Found {len(tables)} tables:")
        for table in tables:
            print(f"  - {table}")

        # Check views
        cur.execute("""
            SELECT table_name
            FROM information_schema.views
            WHERE table_schema='public'
            ORDER BY table_name
        """)
        views = [row[0] for row in cur.fetchall()]

        if views:
            print(f"\n✓ Found {len(views)} views:")
            for view in views:
                print(f"  - {view}")

        # Test insert/select
        print("\n✓ Testing write permissions...")
        cur.execute("""
            INSERT INTO workflows (workflow_name, workflow_json)
            VALUES ('test_workflow', '{"test": true}'::jsonb)
            RETURNING workflow_id, workflow_name
        """)
        result = cur.fetchone()
        print(f"  Inserted workflow: {result[1]} (ID: {result[0]})")

        # Clean up
        cur.execute("DELETE FROM workflows WHERE workflow_name = 'test_workflow'")
        conn.commit()
        print("  ✓ Cleanup successful")

        cur.close()
        conn.close()

        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        return False


async def test_asyncpg():
    """Test asyncpg connection"""
    print("\n" + "=" * 50)
    print("Testing asyncpg connection...")

    try:
        import asyncpg

        conn = await asyncpg.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", 5432)),
            database=os.getenv("DB_NAME", "casare_rpa"),
            user=os.getenv("DB_USER", "casare_user"),
            password=os.getenv("DB_PASSWORD", "postgre"),
        )

        # Test query
        count = await conn.fetchval("SELECT COUNT(*) FROM workflows")
        print("✓ asyncpg connected successfully")
        print(f"  Current workflow count: {count}")

        await conn.close()
        return True

    except ImportError:
        print("⚠ asyncpg not installed (optional)")
        return True
    except Exception as e:
        print(f"✗ asyncpg error: {e}")
        return False


def test_queue_imports():
    """Test queue module imports"""
    print("\n" + "=" * 50)
    print("Testing queue imports...")

    try:
        from casare_rpa.infrastructure.queue import get_memory_queue

        print("✓ Queue imports successful")
        return True
    except Exception as e:
        print(f"✗ Queue import error: {e}")
        return False


def main():
    """Run all verification tests"""
    print("=" * 50)
    print("CasareRPA PostgreSQL Setup Verification")
    print("=" * 50)
    print()

    # Test 1: Basic connection
    test1 = test_connection()

    # Test 2: asyncpg
    test2 = asyncio.run(test_asyncpg())

    # Test 3: Queue imports
    test3 = test_queue_imports()

    # Summary
    print("\n" + "=" * 50)
    print("Verification Summary")
    print("=" * 50)
    print(f"PostgreSQL Connection: {'✓ PASS' if test1 else '✗ FAIL'}")
    print(f"asyncpg Connection:    {'✓ PASS' if test2 else '✗ FAIL'}")
    print(f"Queue Imports:         {'✓ PASS' if test3 else '✗ FAIL'}")

    if test1 and test2 and test3:
        print("\n✓ All tests passed! PostgreSQL setup is complete.")
        print("\nYou can now:")
        print("  1. Start Orchestrator API: start_platform.bat")
        print("  2. Start Canvas Designer: python run.py")
        print("  3. Start Robot Agent: python -m casare_rpa.robot.cli start")
        return 0
    else:
        print("\n✗ Some tests failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
