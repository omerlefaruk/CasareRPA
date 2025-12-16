import asyncio
import asyncpg
import os
from dotenv import load_dotenv


async def test_connection():
    load_dotenv()

    # Test with DATABASE_URL (port 5432)
    db_url = os.getenv("DATABASE_URL")
    print(f"DATABASE_URL: {db_url[:50]}...{db_url[-50:]}")
    print(f"URL Length: {len(db_url)}")

    try:
        conn = await asyncpg.connect(db_url)
        print("✅ Connection successful!")
        version = await conn.fetchval("SELECT version()")
        print(f"PostgreSQL version: {version[:100]}")
        await conn.close()
    except Exception as e:
        print(f"❌ Connection failed: {e}")

        # Try parsing the URL manually
        print("\nTrying to parse URL...")
        if "postgresql://" in db_url:
            parts = db_url.replace("postgresql://", "").split("@")
            if len(parts) == 2:
                user_pass, host_db = parts
                if ":" in user_pass:
                    user, password = user_pass.split(":", 1)
                    print(f"User: {user}")
                    print(f"Password length: {len(password)}")
                    print(f"Password first 10 chars: {password[:10]}")
                    print(f"Password last 10 chars: {password[-10:]}")


if __name__ == "__main__":
    asyncio.run(test_connection())
