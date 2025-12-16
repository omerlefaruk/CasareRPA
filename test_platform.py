"""Quick test of new platform features."""

import asyncio
from casare_rpa.infrastructure.services import get_service_registry, ServiceState
from casare_rpa.robot.auto_discovery import get_auto_discovery


async def main():
    print("=" * 60)
    print(" CasareRPA Platform Health Check")
    print("=" * 60)
    print()

    # 1. Test Service Registry
    print("📊 Checking Services...")
    registry = get_service_registry()
    status_map = await registry.check_all_services()

    for name, status in status_map.items():
        symbol = {
            ServiceState.ONLINE: "✓",
            ServiceState.OFFLINE: "○",
            ServiceState.STARTING: "⏳",
            ServiceState.DEGRADED: "⚠️",
            ServiceState.UNKNOWN: "?",
        }.get(status.state, "?")

        latency = f"({status.latency_ms}ms)" if status.latency_ms else ""
        error = f" - {status.error}" if status.error else ""
        required = " [REQUIRED]" if status.required else ""

        print(
            f"   {symbol} {name:15s} {status.state.value:10s} {latency:10s} {required}{error}"
        )

    print()

    # 2. Test Auto-Discovery
    print("🔍 Testing Auto-Discovery...")
    discovery = get_auto_discovery()
    orchestrator_url = await discovery.discover_orchestrator()

    if orchestrator_url:
        print(f"   ✓ Found orchestrator: {orchestrator_url}")
    else:
        print("   ○ No orchestrator discovered")
        print("   > Tip: Start with: python manage.py orchestrator start --dev")

    print()

    # 3. Summary
    online_count = sum(1 for s in status_map.values() if s.state == ServiceState.ONLINE)
    required_count = sum(1 for s in status_map.values() if s.required)
    required_online = sum(
        1 for s in status_map.values() if s.required and s.state == ServiceState.ONLINE
    )

    print("=" * 60)
    if required_online == required_count:
        print(f"✅ Platform Ready! ({online_count}/{len(status_map)} services online)")
        print("   All required services are healthy")
    else:
        print(
            f"⚠️  Platform Incomplete ({online_count}/{len(status_map)} services online)"
        )
        print(f"   {required_online}/{required_count} required services online")
        print("   Use 'launch.bat' to start all services")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nCancelled")
