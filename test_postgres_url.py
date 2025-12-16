import asyncio
import asyncpg
from dotenv import load_dotenv
import os


async def test():
    load_dotenv()
    url = os.getenv("POSTGRES_URL")
    print(f"Testing connection to: {url[:50]}...{url[-20:]}")
    print(f"Full URL length: {len(url)}")

    try:
        conn = await asyncpg.connect(url)
        print("✅ CONNECTION SUCCESSFUL!")
        version = await conn.fetchval("SELECT version()")
        print(f"PostgreSQL version: {version[:80]}...")
        await conn.close()
        return True
    except Exception as e:
        print(f"❌ CONNECTION FAILED: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test())
    exit(0 if success else 1)
