"""
CasareRPA Developer Installer Build Script

This script orchestrates building the developer installer:
1. Builds Canvas, Orchestrator, and Robot executables with PyInstaller
2. Packages them with Inno Setup into a single installer

Usage:
    python build_dev_installer.py [--skip-pyinstaller] [--sign]
"""

import os
import subprocess
import sys
import shutil
from pathlib import Path
from typing import Optional
import argparse
import json
from datetime import datetime

# Paths
ROOT_DIR = Path(__file__).parent.parent
SRC_DIR = ROOT_DIR / "src"
DIST_DIR = ROOT_DIR / "dist"
BUILD_DIR = ROOT_DIR / "build"
INSTALLER_DIR = ROOT_DIR / "installer"
INNO_DIR = INSTALLER_DIR / "inno"
OUTPUT_DIR = INSTALLER_DIR / "output"

# Version info
VERSION_FILE = ROOT_DIR / "src" / "casare_rpa" / "__init__.py"


def get_version() -> str:
    """Extract version from __init__.py or default to 1.0.0."""
    try:
        init_content = VERSION_FILE.read_text()
        for line in init_content.split("\n"):
            if line.startswith("__version__"):
                return line.split("=")[1].strip().strip('"').strip("'")
    except Exception:
        pass
    return "1.0.0"


def run_command(cmd: list[str], cwd: Optional[Path] = None) -> bool:
    """Run a command and return success status."""
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd, cwd=cwd or ROOT_DIR, check=True, capture_output=True, text=True
        )
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}")
        return False


def remove_readonly(func, path, _):
    """Handle read-only files during rmtree."""
    import stat

    os.chmod(path, stat.S_IWRITE)
    func(path)


def clean_build_dirs():
    """Clean previous build artifacts."""
    print("Cleaning build directories...")
    for dir_path in [DIST_DIR, BUILD_DIR]:
        if dir_path.exists():
            try:
                shutil.rmtree(dir_path, onerror=remove_readonly)
            except PermissionError as e:
                print(f"Warning: Could not fully clean {dir_path}: {e}")
                print("Continuing with existing directory...")
    DIST_DIR.mkdir(exist_ok=True)
    BUILD_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)


def build_canvas() -> bool:
    """Build CasareRPA Canvas with PyInstaller."""
    print("\n=== Building Canvas ===")
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconsole",
        "--noconfirm",
        "--name",
        "CasareRPA-Canvas",
        "--distpath",
        str(DIST_DIR / "Canvas"),
        "--workpath",
        str(BUILD_DIR / "canvas"),
        "--add-data",
        f"{SRC_DIR / 'casare_rpa'};casare_rpa",
        "--hidden-import=PySide6.QtSvg",
        "--hidden-import=PySide6.QtWidgets",
        "--hidden-import=PySide6.QtGui",
        "--hidden-import=PySide6.QtCore",
        "--hidden-import=loguru",
        "--hidden-import=psutil",
        "--hidden-import=qasync",
        "--hidden-import=NodeGraphQt",
        "--hidden-import=Qt",
        "--hidden-import=orjson",
        "--hidden-import=playwright",
        "--hidden-import=playwright.async_api",
        "--hidden-import=playwright.sync_api",
        "--hidden-import=uiautomation",
        "--hidden-import=hvac",
        "--clean",
        str(ROOT_DIR / "run.py"),
    ]
    return run_command(cmd)


def build_orchestrator() -> bool:
    """Build CasareRPA Orchestrator with PyInstaller."""
    print("\n=== Building Orchestrator ===")
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconsole",
        "--noconfirm",
        "--name",
        "CasareRPA-Orchestrator",
        "--distpath",
        str(DIST_DIR / "Orchestrator"),
        "--workpath",
        str(BUILD_DIR / "orchestrator"),
        "--paths",
        str(SRC_DIR),
        "--hidden-import=casare_rpa.orchestrator",
        "--hidden-import=casare_rpa.utils",
        "--hidden-import=PySide6",
        "--hidden-import=PySide6.QtWidgets",
        "--hidden-import=PySide6.QtGui",
        "--hidden-import=PySide6.QtCore",
        "--hidden-import=qasync",
        "--hidden-import=loguru",
        "--hidden-import=orjson",
        "--hidden-import=playwright",
        "--hidden-import=supabase",
        "--hidden-import=hvac",
        "--clean",
        str(SRC_DIR / "casare_rpa" / "orchestrator" / "main_window.py"),
    ]
    return run_command(cmd)


def build_robot() -> bool:
    """Build CasareRPA Robot with PyInstaller."""
    print("\n=== Building Robot ===")
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconsole",
        "--noconfirm",
        "--name",
        "CasareRPA-Robot",
        "--distpath",
        str(DIST_DIR / "Robot"),
        "--workpath",
        str(BUILD_DIR / "robot"),
        "--paths",
        str(SRC_DIR),
        "--hidden-import=casare_rpa.robot",
        "--hidden-import=casare_rpa.utils",
        "--hidden-import=playwright",
        "--hidden-import=PySide6",
        "--hidden-import=PySide6.QtWidgets",
        "--hidden-import=PySide6.QtGui",
        "--hidden-import=PySide6.QtCore",
        "--hidden-import=qasync",
        "--hidden-import=loguru",
        "--hidden-import=orjson",
        "--hidden-import=psutil",
        "--hidden-import=supabase",
        "--hidden-import=hvac",
        "--clean",
        str(SRC_DIR / "casare_rpa" / "robot" / "tray_icon.py"),
    ]
    return run_command(cmd)


def create_version_json(version: str):
    """Create version.json for the installer."""
    version_info = {
        "version": version,
        "build_date": datetime.utcnow().isoformat() + "Z",
        "components": {"canvas": version, "orchestrator": version, "robot": version},
    }
    version_file = DIST_DIR / "version.json"
    version_file.write_text(json.dumps(version_info, indent=2))
    print(f"Created {version_file}")


def find_inno_setup() -> Optional[Path]:
    """Find Inno Setup compiler."""
    possible_paths = [
        Path("C:/Program Files (x86)/Inno Setup 6/ISCC.exe"),
        Path("C:/Program Files/Inno Setup 6/ISCC.exe"),
    ]
    for path in possible_paths:
        if path.exists():
            return path
    return None


def build_installer(version: str, sign: bool = False) -> bool:
    """Build the installer with Inno Setup."""
    print("\n=== Building Installer with Inno Setup ===")

    iscc = find_inno_setup()
    if not iscc:
        print("Error: Inno Setup not found. Please install Inno Setup 6.")
        print("Download from: https://jrsoftware.org/isdl.php")
        return False

    iss_file = INNO_DIR / "casarerpa-dev.iss"
    if not iss_file.exists():
        print(f"Error: {iss_file} not found")
        return False

    cmd = [
        str(iscc),
        f"/DAppVersion={version}",
        f"/DSourceDir={DIST_DIR}",
        f"/DOutputDir={OUTPUT_DIR}",
        str(iss_file),
    ]

    if sign:
        cmd.append("/DSignTools=1")

    return run_command(cmd)


def main():
    parser = argparse.ArgumentParser(description="Build CasareRPA Developer Installer")
    parser.add_argument(
        "--skip-pyinstaller",
        action="store_true",
        help="Skip PyInstaller builds (use existing dist)",
    )
    parser.add_argument(
        "--no-clean", action="store_true", help="Skip cleaning build directories"
    )
    parser.add_argument(
        "--sign",
        action="store_true",
        help="Sign executables with code signing certificate",
    )
    parser.add_argument(
        "--version", type=str, default=None, help="Override version number"
    )
    args = parser.parse_args()

    version = args.version or get_version()
    print(f"Building CasareRPA Developer Installer v{version}")
    print("=" * 50)

    if not args.skip_pyinstaller:
        if not args.no_clean:
            clean_build_dirs()
        else:
            print("Skipping clean (--no-clean specified)")
            DIST_DIR.mkdir(exist_ok=True)
            BUILD_DIR.mkdir(exist_ok=True)
            OUTPUT_DIR.mkdir(exist_ok=True)

        # Build all components
        if not build_canvas():
            print("Failed to build Canvas")
            return 1

        if not build_orchestrator():
            print("Failed to build Orchestrator")
            return 1

        if not build_robot():
            print("Failed to build Robot")
            return 1

        create_version_json(version)

    # Build installer
    if not build_installer(version, args.sign):
        print("Failed to build installer")
        return 1

    print("\n" + "=" * 50)
    print("SUCCESS! Installer created at:")
    print(f"  {OUTPUT_DIR / f'CasareRPA-Setup-{version}.exe'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
