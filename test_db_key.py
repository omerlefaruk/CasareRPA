import asyncio
import os
import hashlib
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
    pg_url = os.getenv("DATABASE_URL")
    if not pg_url:
        print("❌ No DB URL in .env")
        return

    # 1. Get Key from environment
    key = os.getenv("ORCHESTRATOR_API_KEY")
    if not key:
        print("❌ ORCHESTRATOR_API_KEY missing")
        return

    print(f"Checking Key: '{key}'")
    local_hash = hash_api_key(key)
    print(f"Local Hash:   {local_hash}")

    # 2. Connect to DB
    print(f"Connecting to DB: {pg_url.split('@')[-1]}")  # Hide password
    try:
        conn = await asyncpg.connect(pg_url, statement_cache_size=0)
    except Exception as e:
        print(f"❌ DB Connection Failed: {e}")
        return

    try:
        # 3. Check exact match
        row = await conn.fetchrow(
            "SELECT * FROM robot_api_keys WHERE key_hash = $1", local_hash
        )

        if row:
            print("✅ FOUND MATCH in DB!")
            print(f"   ID: {row['id']}")
            print(f"   Robot: {row['robot_id']}")
            print(f"   Revoked: {row['is_revoked']}")
            print(f"   Expires: {row['expires_at']}")
        else:
            print("❌ NO MATCH FOUND in DB.")

            # 4. Debug: Print all keys
            print("   Listing all available keys:")
            rows = await conn.fetch(
                "SELECT robot_id, key_hash, created_at FROM robot_api_keys ORDER BY created_at DESC"
            )
            for r in rows:
                print(f"   - Robot: {r['robot_id']}, Hash: {r['key_hash'][:10]}...")
                if r["key_hash"] == local_hash:
                    print("     (Wait, this matches?! logic error above?)")
                else:
                    print("     (Mismatch)")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
