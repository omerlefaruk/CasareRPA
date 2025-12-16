import os
import asyncio
from dotenv import load_dotenv
from casare_rpa.infrastructure.auth.robot_api_keys import hash_api_key
from casare_rpa.infrastructure.services.registry import get_db_pool

load_dotenv()


async def check_key():
    key = os.getenv("ORCHESTRATOR_API_KEY")
    if not key:
        print("❌ ORCHESTRATOR_API_KEY not found in .env")
        return

    print(f"Checking Key: {key}")

    # 1. Local Hash
    local_hash = hash_api_key(key)
    print(f"Local Computed Hash: {local_hash}")

    # 2. Check DB
    pool = get_db_pool()
    if not pool:
        print("❌ Could not connect to DB")
        return

    async with pool.acquire() as conn:
        # Find by hash
        row = await conn.fetchrow(
            "SELECT robot_id, key_hash, is_revoked FROM robot_api_keys WHERE key_hash = $1",
            local_hash,
        )
        if row:
            print(f"✅ Found key in DB for Robot: {row['robot_id']}")
            print(f"   Revoked: {row['is_revoked']}")
        else:
            print("❌ Key NOT found in DB by hash.")

            # Debug: List all keys
            rows = await conn.fetch("SELECT robot_id, key_hash FROM robot_api_keys")
            print(f"   Dumping {len(rows)} existing keys in DB:")
            for r in rows:
                print(f"   - Robot: {r['robot_id']}, Hash: {r['key_hash']}")


if __name__ == "__main__":
    # Mock settings for DB connection
    # registry.py uses os.getenv internally
    asyncio.run(check_key())
