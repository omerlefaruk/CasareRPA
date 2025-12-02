#!/usr/bin/env python3
"""
NOTE: This script now delegates to the unified setup system.

Prefer using the unified setup CLI:
    python -m deploy.supabase.setup quickstart    # Interactive first-time setup
    python -m deploy.supabase.setup all           # Complete setup
    python -m deploy.supabase.setup verify        # Verify setup

CasareRPA Orchestrator Quick Start Script.

One-click setup for the CasareRPA orchestrator, including:
1. Prerequisites check
2. Supabase setup (optional)
3. Start orchestrator locally or prepare for cloud deployment

Usage:
    python quickstart.py                    # Interactive mode
    python quickstart.py --local            # Start local orchestrator
    python quickstart.py --cloud railway    # Prepare for Railway deployment
    python quickstart.py --check            # Check prerequisites only
"""

import argparse
import asyncio
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
ORCHESTRATOR_DIR = SCRIPT_DIR / "orchestrator"
SUPABASE_DIR = SCRIPT_DIR / "supabase"
SUPABASE_SETUP = SUPABASE_DIR / "setup.py"


@dataclass
class Prerequisite:
    """A prerequisite check."""

    name: str
    command: str
    required: bool
    install_hint: str
    version_flag: str = "--version"


PREREQUISITES = [
    Prerequisite(
        name="Python 3.12+",
        command="python",
        required=True,
        install_hint="https://www.python.org/downloads/",
        version_flag="--version",
    ),
    Prerequisite(
        name="pip",
        command="pip",
        required=True,
        install_hint="python -m ensurepip --upgrade",
        version_flag="--version",
    ),
    Prerequisite(
        name="Git",
        command="git",
        required=False,
        install_hint="https://git-scm.com/downloads",
        version_flag="--version",
    ),
    Prerequisite(
        name="Docker",
        command="docker",
        required=False,
        install_hint="https://www.docker.com/get-started (for local Postgres)",
        version_flag="--version",
    ),
    Prerequisite(
        name="Railway CLI",
        command="railway",
        required=False,
        install_hint="npm install -g @railway/cli",
        version_flag="--version",
    ),
    Prerequisite(
        name="Fly CLI",
        command="fly",
        required=False,
        install_hint="https://fly.io/docs/hands-on/install-flyctl/",
        version_flag="version",
    ),
    Prerequisite(
        name="Supabase CLI",
        command="supabase",
        required=False,
        install_hint="npm install -g supabase",
        version_flag="--version",
    ),
]


def print_header(title: str, char: str = "="):
    """Print a formatted header."""
    width = 60
    print()
    print(char * width)
    print(f" {title}")
    print(char * width)


def print_step(step: str, status: str = "", success: Optional[bool] = None):
    """Print a step with optional status."""
    icon = ""
    if success is True:
        icon = "[OK]"
    elif success is False:
        icon = "[FAIL]"
    elif success is None and status:
        icon = "[INFO]"

    if icon:
        print(f"  {icon} {step}: {status}")
    else:
        print(f"  {step}")


def run_command(
    command: list[str],
    capture: bool = True,
    check: bool = False,
    cwd: Optional[Path] = None,
) -> subprocess.CompletedProcess:
    """Run a command and return result."""
    try:
        result = subprocess.run(
            command,
            capture_output=capture,
            text=True,
            check=check,
            cwd=cwd,
        )
        return result
    except subprocess.CalledProcessError as e:
        return e
    except FileNotFoundError:
        return subprocess.CompletedProcess(command, 1, "", "Command not found")


def check_command_exists(
    command: str, version_flag: str = "--version"
) -> tuple[bool, str]:
    """Check if a command exists and get its version."""
    try:
        result = run_command([command, version_flag])
        if result.returncode == 0:
            version = result.stdout.strip().split("\n")[0]
            return True, version
        return False, ""
    except Exception:
        return False, ""


def check_python_version() -> tuple[bool, str]:
    """Check Python version is 3.12+."""
    version_info = sys.version_info
    version_str = f"{version_info.major}.{version_info.minor}.{version_info.micro}"
    is_valid = version_info >= (3, 12)
    return is_valid, version_str


def check_prerequisites() -> dict[str, dict]:
    """Check all prerequisites and return status."""
    results = {}

    for prereq in PREREQUISITES:
        if prereq.command == "python":
            exists, version = check_python_version()
        else:
            exists, version = check_command_exists(prereq.command, prereq.version_flag)

        results[prereq.name] = {
            "exists": exists,
            "version": version,
            "required": prereq.required,
            "install_hint": prereq.install_hint,
        }

    return results


def print_prerequisites_status(results: dict) -> bool:
    """Print prerequisites status and return if all required are met."""
    print_header("Prerequisites Check")

    all_required_met = True

    for name, status in results.items():
        if status["exists"]:
            print_step(name, status["version"], True)
        else:
            if status["required"]:
                print_step(name, "NOT FOUND - Required!", False)
                print(f"      Install: {status['install_hint']}")
                all_required_met = False
            else:
                print_step(name, "Not found (optional)", None)

    return all_required_met


def check_env_file(env_path: Path) -> dict:
    """Check environment file for required variables."""
    if not env_path.exists():
        return {}

    env_vars = {}
    for line in env_path.read_text().split("\n"):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            env_vars[key.strip()] = value.strip()

    return env_vars


def create_local_env(orchestrator_dir: Path) -> Path:
    """Create local .env file from template."""
    example_path = orchestrator_dir / ".env.example"
    env_path = orchestrator_dir / ".env"

    if env_path.exists():
        return env_path

    if example_path.exists():
        shutil.copy(example_path, env_path)
        print_step(".env file", "Created from template", True)
        return env_path

    # Create minimal .env
    env_content = """# CasareRPA Orchestrator Configuration
HOST=0.0.0.0
PORT=8000
WORKERS=1

# Database (use local Docker or Supabase)
DATABASE_URL=postgresql://casare:localdev@localhost:5433/casare_orchestrator

# Security - CHANGE THIS!
API_SECRET=dev-secret-change-in-production

# CORS
CORS_ORIGINS=*
"""
    env_path.write_text(env_content)
    print_step(".env file", "Created with defaults", True)
    return env_path


def start_local_database() -> bool:
    """Start local PostgreSQL using Docker Compose."""
    compose_file = ORCHESTRATOR_DIR / "docker-compose.yml"

    if not compose_file.exists():
        print_step("Docker Compose", "File not found", False)
        return False

    # Check if Docker is running
    exists, _ = check_command_exists("docker", "--version")
    if not exists:
        print_step("Docker", "Not installed - using Supabase instead", None)
        return False

    # Check if container is already running
    result = run_command(["docker", "ps", "-q", "-f", "name=casare-postgres"])
    if result.returncode == 0 and result.stdout.strip():
        print_step("PostgreSQL", "Already running", True)
        return True

    # Start database
    print_step("PostgreSQL", "Starting with Docker...")
    result = run_command(
        ["docker", "compose", "-f", str(compose_file), "up", "-d", "postgres"],
        capture=False,
        cwd=ORCHESTRATOR_DIR,
    )

    if result.returncode == 0:
        print_step("PostgreSQL", "Started on localhost:5433", True)
        return True
    else:
        print_step("PostgreSQL", "Failed to start", False)
        return False


def run_supabase_setup(project_ref: str, service_key: str) -> bool:
    """Run Supabase setup script."""
    if not SUPABASE_SETUP.exists():
        print_step("Supabase setup", "Script not found", False)
        return False

    result = run_command(
        [
            sys.executable,
            str(SUPABASE_SETUP),
            "--project-ref",
            project_ref,
            "--service-key",
            service_key,
        ],
        capture=False,
    )

    return result.returncode == 0


def install_dependencies() -> bool:
    """Install Python dependencies."""
    print_step("Dependencies", "Installing...")

    # Install main project
    result = run_command(
        [sys.executable, "-m", "pip", "install", "-e", str(PROJECT_ROOT), "-q"],
        capture=False,
    )

    if result.returncode != 0:
        print_step("Dependencies", "Failed to install", False)
        return False

    # Install orchestrator-specific deps
    requirements = ORCHESTRATOR_DIR / "requirements.txt"
    if requirements.exists():
        result = run_command(
            [sys.executable, "-m", "pip", "install", "-r", str(requirements), "-q"],
            capture=False,
        )

    print_step("Dependencies", "Installed", True)
    return True


def start_orchestrator() -> None:
    """Start the orchestrator server."""
    print_header("Starting Orchestrator")

    # Change to project root
    os.chdir(PROJECT_ROOT)

    # Start uvicorn
    print_step("Server", "Starting on http://0.0.0.0:8000")
    print()
    print("  Press Ctrl+C to stop")
    print()

    try:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "casare_rpa.infrastructure.orchestrator.server:app",
                "--host",
                "0.0.0.0",
                "--port",
                "8000",
                "--reload",
            ],
            cwd=PROJECT_ROOT,
        )
    except KeyboardInterrupt:
        print("\n  Orchestrator stopped.")


def prepare_railway_deployment() -> None:
    """Prepare for Railway deployment."""
    print_header("Railway Deployment")

    # Check Railway CLI
    exists, _ = check_command_exists("railway", "--version")
    if not exists:
        print_step("Railway CLI", "Not installed", False)
        print("  Install: npm install -g @railway/cli")
        return

    print("Next steps:")
    print()
    print("  1. Login to Railway:")
    print("     railway login")
    print()
    print("  2. Initialize project:")
    print(f"     cd {ORCHESTRATOR_DIR}")
    print("     railway init")
    print()
    print("  3. Add PostgreSQL:")
    print("     railway add postgres")
    print()
    print("  4. Set secrets:")
    print("     railway variables set API_SECRET=<your-secret>")
    print()
    print("  5. Deploy:")
    print("     railway up")
    print()


def prepare_flyio_deployment() -> None:
    """Prepare for Fly.io deployment."""
    print_header("Fly.io Deployment")

    exists, _ = check_command_exists("fly", "version")
    if not exists:
        print_step("Fly CLI", "Not installed", False)
        print("  Install: https://fly.io/docs/hands-on/install-flyctl/")
        return

    print("Next steps:")
    print()
    print("  1. Login to Fly.io:")
    print("     fly auth login")
    print()
    print("  2. Launch app:")
    print(f"     cd {ORCHESTRATOR_DIR}")
    print("     fly launch")
    print()
    print("  3. Create PostgreSQL:")
    print("     fly pg create")
    print("     fly pg attach")
    print()
    print("  4. Set secrets:")
    print("     fly secrets set API_SECRET=<your-secret>")
    print()
    print("  5. Deploy:")
    print("     fly deploy")
    print()


def interactive_mode() -> None:
    """Run interactive setup wizard."""
    print_header("CasareRPA Quick Start")
    print()
    print("  This script helps you set up the CasareRPA orchestrator.")
    print("  It will check prerequisites and guide you through setup.")
    print()

    # Check prerequisites
    prereqs = check_prerequisites()
    if not print_prerequisites_status(prereqs):
        print("\n  Please install required dependencies first.")
        sys.exit(1)

    # Ask deployment type
    print_header("Deployment Type")
    print()
    print("  1. Local development (with Docker)")
    print("  2. Local development (with Supabase)")
    print("  3. Cloud deployment (Railway)")
    print("  4. Cloud deployment (Fly.io)")
    print("  5. Cloud deployment (Render)")
    print()

    while True:
        choice = input("  Select option [1-5]: ").strip()
        if choice in ["1", "2", "3", "4", "5"]:
            break
        print("  Invalid choice. Please enter 1-5.")

    if choice == "1":
        # Local with Docker
        print_header("Local Setup (Docker)")

        install_dependencies()
        create_local_env(ORCHESTRATOR_DIR)

        if start_local_database():
            print()
            print("  Database ready!")
            print()
            start_now = input("  Start orchestrator now? [Y/n]: ").strip().lower()
            if start_now != "n":
                start_orchestrator()
        else:
            print("\n  Please install Docker or use Supabase option.")

    elif choice == "2":
        # Local with Supabase
        print_header("Local Setup (Supabase)")

        project_ref = input("  Supabase project ref: ").strip()
        service_key = input("  Supabase service key: ").strip()

        if project_ref and service_key:
            run_supabase_setup(project_ref, service_key)

            # Update .env with Supabase URL
            env_path = create_local_env(ORCHESTRATOR_DIR)
            env_content = env_path.read_text()
            env_content += f"\nSUPABASE_URL=https://{project_ref}.supabase.co\n"
            env_content += f"SUPABASE_KEY={service_key}\n"
            env_path.write_text(env_content)

            install_dependencies()

            start_now = input("\n  Start orchestrator now? [Y/n]: ").strip().lower()
            if start_now != "n":
                start_orchestrator()
        else:
            print("  Project ref and service key are required.")

    elif choice == "3":
        prepare_railway_deployment()

    elif choice == "4":
        prepare_flyio_deployment()

    elif choice == "5":
        print_header("Render Deployment")
        print()
        print("  Render deployment uses render.yaml Blueprint.")
        print()
        print("  Steps:")
        print("  1. Push code to GitHub")
        print("  2. Go to https://dashboard.render.com")
        print("  3. Create New > Blueprint Instance")
        print("  4. Connect your repository")
        print(f"  5. Select: {ORCHESTRATOR_DIR / 'render.yaml'}")
        print("  6. Set environment variables in dashboard")
        print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="CasareRPA Orchestrator Quick Start",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--check",
        action="store_true",
        help="Only check prerequisites",
    )
    parser.add_argument(
        "--local",
        action="store_true",
        help="Start local orchestrator (with Docker)",
    )
    parser.add_argument(
        "--cloud",
        choices=["railway", "flyio", "render"],
        help="Prepare cloud deployment",
    )
    parser.add_argument(
        "--supabase-ref",
        help="Supabase project reference",
    )
    parser.add_argument(
        "--supabase-key",
        help="Supabase service key",
    )

    args = parser.parse_args()

    try:
        if args.check:
            prereqs = check_prerequisites()
            success = print_prerequisites_status(prereqs)
            sys.exit(0 if success else 1)

        elif args.local:
            print_header("Local Orchestrator Setup")
            prereqs = check_prerequisites()
            if not print_prerequisites_status(prereqs):
                sys.exit(1)

            install_dependencies()
            create_local_env(ORCHESTRATOR_DIR)

            if args.supabase_ref and args.supabase_key:
                run_supabase_setup(args.supabase_ref, args.supabase_key)
            else:
                start_local_database()

            start_orchestrator()

        elif args.cloud == "railway":
            prepare_railway_deployment()

        elif args.cloud == "flyio":
            prepare_flyio_deployment()

        elif args.cloud == "render":
            print_header("Render Deployment")
            print("  Use render.yaml Blueprint via GitHub.")

        else:
            interactive_mode()

    except KeyboardInterrupt:
        print("\n\nSetup cancelled.")
        sys.exit(130)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
