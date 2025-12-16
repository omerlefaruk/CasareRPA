import asyncio
import os
import hashlib
import uuid
from dotenv import load_dotenv

load_dotenv()

try:
    import asyncpg
except ImportError:
    print("asyncpg not installed!")
    exit(1)


def hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


async def main():
    pg_url = os.getenv("POSTGRES_URL") or os.getenv("DATABASE_URL")
    if not pg_url:
        print("❌ No DB URL in .env")
        return

    key = os.getenv("ORCHESTRATOR_API_KEY")
    if not key:
        print("❌ ORCHESTRATOR_API_KEY missing")
        return

    print(f"Backfilling Key: '{key}'")
    local_hash = hash_api_key(key)
    print(f"Hash: {local_hash}")

    robot_id = "robot-R-593a1494"  # Hardcoded ID from previous context

    print("Connecting to DB...")
    try:
        conn = await asyncpg.connect(pg_url, statement_cache_size=0)
    except Exception as e:
        print(f"❌ DB Connection Failed: {e}")
        return

    try:
        # 1. Ensure Robot Exists
        print(f"Ensuring robot {robot_id} exists...")
        # Check if exists
        row = await conn.fetchrow("SELECT id FROM robots WHERE id = $1", robot_id)
        if not row:
            print("   Inserting robot...")
            await conn.execute(
                """
                INSERT INTO robots (id, name, status, created_at, updated_at)
                VALUES ($1, $2, $3, NOW(), NOW())
                """,
                robot_id,
                "Local-Robot",
                "offline",
            )
            print("   ✅ Robot inserted.")
        else:
            print("   ✅ Robot already exists.")

        # 2. Insert Key
        print("Inserting API Key...")
        try:
            await conn.execute(
                """
                INSERT INTO robot_api_keys (
                    id, robot_id, key_hash, name, description, is_revoked, created_at
                ) VALUES ($1, $2, $3, $4, $5, FALSE, NOW())
                """,
                str(uuid.uuid4()),
                robot_id,
                local_hash,
                "Restored Key",
                "Backfilled via fix_auth_db.py",
            )
            print("   ✅ Key inserted successfully!")
        except asyncpg.UniqueViolationError:
            print("   ⚠️ Key hash already exists (duplicate?).")
        except Exception as e:
            print(f"   ❌ Failed to insert key: {e}")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
