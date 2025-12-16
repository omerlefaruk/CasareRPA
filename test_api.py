"""Quick test for orchestrator API connection and robot listing."""

import asyncio
import os
from casare_rpa.infrastructure.orchestrator.client import (
    OrchestratorClient,
    OrchestratorConfig,
)


async def main():
    url = os.getenv("CASARE_API_URL") or "https://api.casare.net"
    api_key = os.getenv("ORCHESTRATOR_API_KEY")
    ws_url = url.replace("http://", "ws://").replace("https://", "wss://")

    print(f"URL: {url}")
    print(f"API key set: {bool(api_key)}")

    client = OrchestratorClient(
        OrchestratorConfig(base_url=url, ws_url=ws_url, api_key=api_key)
    )
    try:
        ok = await client.connect()
        print("Health check: OK" if ok else "Health check: FAILED")
        if ok:
            robots = await client.get_robots()
            print(f"Robots found: {len(robots)}")
            for r in robots[:10]:
                print(f"  - {r.id}: {r.name} [{r.status}]")
        else:
            print("Health check failed - cannot list robots")
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
    finally:
        try:
            await client.disconnect()
        except Exception:
            pass


if __name__ == "__main__":
    asyncio.run(main())
