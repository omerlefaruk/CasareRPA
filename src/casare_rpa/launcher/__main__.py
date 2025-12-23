"""
Smart launcher for CasareRPA platform.

Handles intelligent startup of all services with health checking and auto-recovery.
"""

import asyncio
import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from casare_rpa.infrastructure.services import ServiceState, get_service_registry


class PlatformLauncher:
    """Smart launcher for CasareRPA platform."""

    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root or Path.cwd()
        self.registry = get_service_registry()
        self._processes: list[subprocess.Popen] = []

    async def launch(
        self,
        start_orchestrator: bool = True,
        start_robot: bool = True,
        start_canvas: bool = True,
        start_tunnel: bool = False,
    ):
        """
        Launch the CasareRPA platform with smart service management.

        Args:
            start_orchestrator: Start local orchestrator API
            start_robot: Start robot agent
            start_canvas: Start Canvas UI
            start_tunnel: Start Cloudflare tunnel (optional)
        """
        print("🚀 Starting CasareRPA Platform...\n")

        # 1. Check prerequisites
        if not await self._check_prerequisites():
            print("\n❌ Prerequisites check failed")
            return False

        # 2. Start database (check only, assume external)
        print("📊 Checking database...")
        db_status = await self.registry.check_service("database")
        if db_status.state == ServiceState.ONLINE:
            print(f"   ✓ Database connected ({db_status.latency_ms}ms)")
        else:
            print(f"   ⚠️  Database not available: {db_status.error}")
            print("   Continuing anyway (orchestrator will handle retries)")

        # 3. Start orchestrator
        if start_orchestrator:
            if not await self._start_orchestrator():
                print("\n❌ Failed to start orchestrator")
                return False

        # 4. Start Cloudflare tunnel (optional)
        if start_tunnel:
            await self._start_tunnel()

        # 5. Start robot
        if start_robot:
            await self._start_robot()

        # 6. Start Canvas
        if start_canvas:
            await self._start_canvas()

        print("\n✅ CasareRPA Platform Ready!")
        print("   - Canvas: Open automatically or visit the window")
        print("   - Orchestrator: http://localhost:8000")
        print("   - Fleet Dashboard: Available in Canvas → Fleet")
        print("\n⚡ Press Ctrl+C to stop all services\n")

        return True

    async def _check_prerequisites(self) -> bool:
        """Check that required tools are available."""
        print("🔍 Checking prerequisites...")

        # Check Python
        python_version = (
            f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        )
        print(f"   ✓ Python {python_version}")

        # Check venv
        venv_path = self.project_root / ".venv"
        if venv_path.exists():
            print("   ✓ Virtual environment found")
        else:
            print("   ⚠️  No .venv found (using system Python)")

        return True

    async def _start_orchestrator(self) -> bool:
        """Start the orchestrator API server."""
        print("\n🎯 Starting Orchestrator...")

        # Check if already running
        if self.registry.is_port_in_use(8000):
            print("   ℹ️  Orchestrator already running on port 8000")

            # Verify it's healthy
            status = await self.registry.check_service("orchestrator")
            if status.state == ServiceState.ONLINE:
                print(f"   ✓ Orchestrator healthy ({status.latency_ms}ms)")
                return True
            else:
                print(f"   ⚠️  Port in use but unhealthy: {status.error}")
                print("   You may need to manually stop the existing process")
                return False

        # Start orchestrator
        try:
            python_exe = sys.executable
            cmd = [python_exe, "manage.py", "orchestrator", "start", "--dev"]

            process = subprocess.Popen(
                cmd,
                cwd=str(self.project_root),
                creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0,
            )

            self._processes.append(process)

            # Wait for orchestrator to become healthy
            print("   ⏳ Waiting for orchestrator to start...")
            healthy = await self.registry.wait_for_service("orchestrator", timeout=30)

            if healthy:
                print("   ✓ Orchestrator started successfully")
                return True
            else:
                print("   ❌ Orchestrator failed to start within 30s")
                return False

        except Exception as e:
            print(f"   ❌ Failed to start orchestrator: {e}")
            return False

    async def _start_tunnel(self):
        """Start Cloudflare tunnel (optional)."""
        print("\n🌐 Starting Cloudflare Tunnel...")

        try:
            tunnel_name = os.getenv("CASARE_CLOUDFLARE_TUNNEL_NAME", "casare-rpa")
            cmd = ["cloudflared", "tunnel", "run", tunnel_name]

            process = subprocess.Popen(
                cmd,
                cwd=str(self.project_root),
                creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0,
            )

            self._processes.append(process)
            print(f"   ✓ Tunnel started: {tunnel_name}")

        except FileNotFoundError:
            print("   ⚠️  cloudflared not found in PATH")
            print("   Tunnel disabled (local only mode)")
        except Exception as e:
            print(f"   ⚠️  Failed to start tunnel: {e}")

    async def _start_robot(self):
        """Start robot agent."""
        print("\n🤖 Starting Robot Agent...")

        try:
            python_exe = sys.executable
            cmd = [python_exe, "-m", "casare_rpa.robot.tray_icon"]

            process = subprocess.Popen(
                cmd,
                cwd=str(self.project_root),
                creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0,
            )

            self._processes.append(process)
            print("   ✓ Robot agent started")

            # Give it a moment to initialize
            await asyncio.sleep(2)

        except Exception as e:
            print(f"   ⚠️  Failed to start robot: {e}")

    async def _start_canvas(self):
        """Start Canvas UI."""
        print("\n🎨 Starting Canvas...")

        try:
            python_exe = sys.executable
            cmd = [python_exe, "manage.py", "canvas"]

            process = subprocess.Popen(
                cmd,
                cwd=str(self.project_root),
                creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0,
            )

            self._processes.append(process)
            print("   ✓ Canvas started")

        except Exception as e:
            print(f"   ⚠️  Failed to start Canvas: {e}")

    def cleanup(self):
        """Stop all started processes."""
        print("\n🛑 Stopping services...")

        for process in self._processes:
            try:
                process.terminate()
                process.wait(timeout=5)
            except Exception:
                try:
                    process.kill()
                except Exception:
                    pass

        print("   ✓ All services stopped")


async def main():
    """Main launcher entry point."""
    launcher = PlatformLauncher()

    try:
        success = await launcher.launch(
            start_orchestrator=os.getenv("CASARE_START_ORCHESTRATOR", "1") == "1",
            start_robot=True,
            start_canvas=True,
            start_tunnel=os.getenv("CASARE_START_TUNNEL", "0") == "1",
        )

        if success:
            # Keep running until Ctrl+C
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                print("\n\nReceived shutdown signal...")

    finally:
        launcher.cleanup()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutdown complete!")
