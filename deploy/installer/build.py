#!/usr/bin/env python3
"""
Unified Installer Build Script for CasareRPA.

Consolidates build process for Canvas (Designer) and Robot installers.
Supports PyInstaller builds and NSIS installer creation.

Usage:
    python -m deploy.installer.build           # Build both
    python -m deploy.installer.build --canvas  # Canvas only
    python -m deploy.installer.build --robot   # Robot only
    python -m deploy.installer.build --sign    # Code sign
    python -m deploy.installer.build --clean   # Clean build

Requirements:
    - Python 3.12+
    - PyInstaller
    - NSIS (optional, for installer creation)
    - Windows SDK (optional, for code signing)
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class BuildTarget(Enum):
    """Build target types."""

    CANVAS = "canvas"
    ROBOT = "robot"
    BOTH = "both"


class BuildFormat(Enum):
    """Installer output format."""

    NSIS = "nsis"
    MSI = "msi"
    PORTABLE = "portable"


@dataclass
class BuildConfig:
    """Build configuration."""

    target: BuildTarget
    format: BuildFormat
    clean: bool
    skip_tests: bool
    sign: bool
    include_browsers: bool
    debug: bool
    verbose: bool


class BuildStep:
    """Represents a build step with status tracking."""

    def __init__(self, name: str, action: Callable[[], bool]):
        self.name = name
        self.action = action
        self.success = False
        self.skipped = False

    def run(self) -> bool:
        """Execute the build step."""
        self.success = self.action()
        return self.success


class InstallerBuilder:
    """Unified installer builder for CasareRPA."""

    def __init__(self, config: BuildConfig):
        self.config = config
        self.installer_dir = Path(__file__).parent.resolve()
        self.project_root = self.installer_dir.parent.parent
        self.dist_dir = self.project_root / "dist"
        self.build_dir = self.project_root / "build"
        self.src_dir = self.project_root / "src"

        # Import version utilities
        sys.path.insert(0, str(self.installer_dir))
        from version import get_version, inject_all_versions

        self.version = get_version()
        self._inject_versions = inject_all_versions

    def _print_header(self) -> None:
        """Print build header."""
        print("=" * 60)
        print("CasareRPA Installer Build")
        print("=" * 60)
        print(f"Version:    {self.version.string}")
        print(f"Target:     {self.config.target.value}")
        print(f"Format:     {self.config.format.value}")
        print(f"Debug:      {self.config.debug}")
        print(f"Sign:       {self.config.sign}")
        print("=" * 60)
        print()

    def _print_step(self, message: str) -> None:
        """Print step message."""
        print()
        print(f"[STEP] {message}")
        print("-" * 50)

    def _print_info(self, message: str) -> None:
        """Print info message."""
        if self.config.verbose:
            print(f"       {message}")

    def _print_warning(self, message: str) -> None:
        """Print warning message."""
        print(f"[WARN] {message}")

    def _print_error(self, message: str) -> None:
        """Print error message."""
        print(f"[ERROR] {message}")

    def _run_command(
        self, cmd: list[str], cwd: Path | None = None, env: dict | None = None
    ) -> tuple[int, str, str]:
        """Run a command and return exit code, stdout, stderr."""
        full_env = os.environ.copy()
        if env:
            full_env.update(env)

        result = subprocess.run(
            cmd,
            cwd=cwd or self.project_root,
            capture_output=True,
            text=True,
            env=full_env,
        )

        if self.config.verbose:
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr)

        return result.returncode, result.stdout, result.stderr

    def check_prerequisites(self) -> bool:
        """Check build prerequisites."""
        self._print_step("Checking Prerequisites")

        # Python version
        py_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        if sys.version_info < (3, 12):
            self._print_error(f"Python 3.12+ required (found {py_version})")
            return False
        self._print_info(f"Python: {py_version}")

        # PyInstaller
        if not shutil.which("pyinstaller"):
            self._print_warning("PyInstaller not found, installing...")
            code, _, _ = self._run_command([sys.executable, "-m", "pip", "install", "pyinstaller"])
            if code != 0:
                self._print_error("Failed to install PyInstaller")
                return False

        code, stdout, _ = self._run_command(["pyinstaller", "--version"])
        if code == 0:
            self._print_info(f"PyInstaller: {stdout.strip()}")
        else:
            self._print_error("PyInstaller not working")
            return False

        # NSIS (optional)
        self.nsis_path = self._find_nsis()
        if self.nsis_path:
            self._print_info(f"NSIS: {self.nsis_path}")
        else:
            self._print_warning("NSIS not found - installer will not be built")

        return True

    def _find_nsis(self) -> Path | None:
        """Find NSIS makensis executable."""
        # Check PATH
        makensis = shutil.which("makensis")
        if makensis:
            return Path(makensis)

        # Check common locations
        common_paths = [
            Path(r"C:\Program Files (x86)\NSIS\makensis.exe"),
            Path(r"C:\Program Files\NSIS\makensis.exe"),
        ]

        for path in common_paths:
            if path.exists():
                return path

        return None

    def clean(self) -> bool:
        """Clean build directories."""
        self._print_step("Cleaning Build Directories")

        dirs_to_clean = [self.dist_dir, self.build_dir]
        for dir_path in dirs_to_clean:
            if dir_path.exists():
                self._print_info(f"Removing {dir_path}")
                shutil.rmtree(dir_path)

        return True

    def prepare_directories(self) -> bool:
        """Create build directories."""
        self._print_step("Preparing Build Directories")

        self.dist_dir.mkdir(parents=True, exist_ok=True)
        self.build_dir.mkdir(parents=True, exist_ok=True)

        self._print_info(f"Created: {self.dist_dir}")
        self._print_info(f"Created: {self.build_dir}")
        return True

    def inject_version(self) -> bool:
        """Inject version into all installer files."""
        self._print_step("Injecting Version")

        try:
            self._inject_versions()
            self._print_info(f"Version {self.version.string} injected")
            return True
        except Exception as e:
            self._print_error(f"Version injection failed: {e}")
            return False

    def install_dependencies(self) -> bool:
        """Install project dependencies."""
        self._print_step("Installing Dependencies")

        code, _, stderr = self._run_command(
            [sys.executable, "-m", "pip", "install", "-e", ".", "--quiet"],
        )

        if code != 0:
            self._print_error(f"Dependency installation failed: {stderr}")
            return False

        self._print_info("Dependencies installed")
        return True

    def run_tests(self) -> bool:
        """Run test suite."""
        if self.config.skip_tests:
            self._print_info("Tests skipped")
            return True

        self._print_step("Running Tests")

        code, stdout, stderr = self._run_command(
            [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short", "-q"],
        )

        if code != 0:
            self._print_warning("Some tests failed")
            # Save test output
            test_log = self.build_dir / "test-results.log"
            test_log.write_text(stdout + "\n" + stderr)
            self._print_info(f"Test output saved to: {test_log}")
            # Continue anyway
        else:
            self._print_info("All tests passed")

        return True

    def build_canvas(self) -> bool:
        """Build Canvas (Designer + Robot) executable."""
        self._print_step("Building Canvas Executable")

        spec_file = self.installer_dir / "specs" / "canvas.py"
        if not spec_file.exists():
            # Fall back to legacy spec
            spec_file = self.installer_dir / "casarerpa.spec"

        if not spec_file.exists():
            self._print_error(f"Spec file not found: {spec_file}")
            return False

        env = {}
        if self.config.include_browsers:
            env["CASARE_INCLUDE_BROWSERS"] = "1"

        cmd = [
            "pyinstaller",
            str(spec_file),
            "--distpath",
            str(self.dist_dir),
            "--workpath",
            str(self.build_dir),
            "--noconfirm",
        ]

        if self.config.debug:
            cmd.append("--debug=all")

        self._print_info(f"Running: {' '.join(cmd)}")
        code, _, stderr = self._run_command(cmd, env=env)

        if code != 0:
            self._print_error(f"PyInstaller build failed: {stderr}")
            return False

        # Verify output
        app_dir = self.dist_dir / "CasareRPA"
        exe_path = app_dir / "CasareRPA.exe"

        if not exe_path.exists():
            self._print_error(f"Executable not found: {exe_path}")
            return False

        exe_size_mb = exe_path.stat().st_size / (1024 * 1024)
        self._print_info(f"Executable: {exe_path} ({exe_size_mb:.2f} MB)")
        return True

    def build_robot(self) -> bool:
        """Build Robot-only executable."""
        self._print_step("Building Robot Executable")

        spec_file = self.installer_dir / "specs" / "robot.py"
        if not spec_file.exists():
            # Fall back to legacy spec
            spec_file = self.installer_dir / "casarerpa_robot.spec"

        if not spec_file.exists():
            self._print_error(f"Spec file not found: {spec_file}")
            return False

        cmd = [
            "pyinstaller",
            str(spec_file),
            "--distpath",
            str(self.dist_dir),
            "--workpath",
            str(self.build_dir),
            "--noconfirm",
        ]

        self._print_info(f"Running: {' '.join(cmd)}")
        code, _, stderr = self._run_command(cmd)

        if code != 0:
            self._print_error(f"PyInstaller build failed: {stderr}")
            return False

        # Verify output
        app_dir = self.dist_dir / "CasareRPA-Robot"
        exe_path = app_dir / "CasareRPA-Robot.exe"

        if not exe_path.exists():
            self._print_error(f"Executable not found: {exe_path}")
            return False

        exe_size_mb = exe_path.stat().st_size / (1024 * 1024)
        self._print_info(f"Executable: {exe_path} ({exe_size_mb:.2f} MB)")
        return True

    def sign_executables(self) -> bool:
        """Sign built executables."""
        if not self.config.sign:
            return True

        self._print_step("Signing Executables")

        try:
            from signing import can_sign, sign_all_executables

            if not can_sign():
                self._print_warning("Code signing not configured - skipping")
                return True

            if self.config.target in (BuildTarget.CANVAS, BuildTarget.BOTH):
                results = sign_all_executables(self.dist_dir / "CasareRPA")
                success = all(results.values()) if results else True
                if not success:
                    self._print_warning("Some executables failed to sign")

            if self.config.target in (BuildTarget.ROBOT, BuildTarget.BOTH):
                results = sign_all_executables(self.dist_dir / "CasareRPA-Robot")
                success = all(results.values()) if results else True
                if not success:
                    self._print_warning("Some executables failed to sign")

            return True

        except ImportError:
            self._print_warning("Signing module not available")
            return True

    def build_nsis_installer(self) -> bool:
        """Build NSIS installer."""
        if not self.nsis_path:
            self._print_warning("NSIS not available - skipping installer build")
            return True

        if self.config.format != BuildFormat.NSIS:
            return True

        self._print_step("Building NSIS Installer")

        # Build Canvas installer
        if self.config.target in (BuildTarget.CANVAS, BuildTarget.BOTH):
            nsi_file = self.installer_dir / "casarerpa.nsi"
            dist_dir = self.dist_dir / "CasareRPA"

            if nsi_file.exists() and dist_dir.exists():
                cmd = [
                    str(self.nsis_path),
                    f"/DDIST_DIR={dist_dir}",
                    f"/DPRODUCT_VERSION={self.version.string}",
                    "/V3",
                    str(nsi_file),
                ]

                self._print_info("Building Canvas installer...")
                code, _, stderr = self._run_command(cmd, cwd=self.installer_dir)

                if code != 0:
                    self._print_warning(f"NSIS Canvas build failed: {stderr}")
                else:
                    self._print_info("Canvas installer built")

        # Build Robot installer
        if self.config.target in (BuildTarget.ROBOT, BuildTarget.BOTH):
            nsi_file = self.installer_dir / "casarerpa_robot.nsi"
            dist_dir = self.dist_dir / "CasareRPA-Robot"

            if nsi_file.exists() and dist_dir.exists():
                cmd = [
                    str(self.nsis_path),
                    f"/DDIST_DIR={dist_dir}",
                    f"/DPRODUCT_VERSION={self.version.string}",
                    "/V3",
                    str(nsi_file),
                ]

                self._print_info("Building Robot installer...")
                code, _, stderr = self._run_command(cmd, cwd=self.installer_dir)

                if code != 0:
                    self._print_warning(f"NSIS Robot build failed: {stderr}")
                else:
                    self._print_info("Robot installer built")

        return True

    def print_summary(self) -> None:
        """Print build summary."""
        print()
        print("=" * 60)
        print("BUILD COMPLETE")
        print("=" * 60)
        print()

        print("Output files:")

        # Canvas
        if self.config.target in (BuildTarget.CANVAS, BuildTarget.BOTH):
            canvas_dir = self.dist_dir / "CasareRPA"
            if canvas_dir.exists():
                print(f"  Canvas App:    {canvas_dir}")

            installer = self.dist_dir / f"CasareRPA-{self.version.string}-Setup.exe"
            if installer.exists():
                size_mb = installer.stat().st_size / (1024 * 1024)
                print(f"  Canvas Setup:  {installer} ({size_mb:.2f} MB)")

        # Robot
        if self.config.target in (BuildTarget.ROBOT, BuildTarget.BOTH):
            robot_dir = self.dist_dir / "CasareRPA-Robot"
            if robot_dir.exists():
                print(f"  Robot App:     {robot_dir}")

            installer = self.dist_dir / f"CasareRPA-Robot-{self.version.string}-Setup.exe"
            if installer.exists():
                size_mb = installer.stat().st_size / (1024 * 1024)
                print(f"  Robot Setup:   {installer} ({size_mb:.2f} MB)")

        print()
        print("Next steps:")
        print("  1. Test the application(s)")
        print("  2. Run installer to verify installation")
        if not self.config.sign:
            print("  3. Sign executables before distribution (--sign)")
        print()

    def build(self) -> bool:
        """Execute full build process."""
        self._print_header()

        steps = [
            ("Check prerequisites", self.check_prerequisites),
            ("Inject version", self.inject_version),
        ]

        if self.config.clean:
            steps.append(("Clean", self.clean))

        steps.extend(
            [
                ("Prepare directories", self.prepare_directories),
                ("Install dependencies", self.install_dependencies),
                ("Run tests", self.run_tests),
            ]
        )

        # Build targets
        if self.config.target in (BuildTarget.CANVAS, BuildTarget.BOTH):
            steps.append(("Build Canvas", self.build_canvas))

        if self.config.target in (BuildTarget.ROBOT, BuildTarget.BOTH):
            steps.append(("Build Robot", self.build_robot))

        steps.extend(
            [
                ("Sign executables", self.sign_executables),
                ("Build NSIS installer", self.build_nsis_installer),
            ]
        )

        for name, action in steps:
            success = action()
            if not success:
                self._print_error(f"Build failed at: {name}")
                return False

        self.print_summary()
        return True


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="CasareRPA Unified Installer Builder",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m deploy.installer.build              Build both Canvas and Robot
  python -m deploy.installer.build --canvas     Build Canvas only
  python -m deploy.installer.build --robot      Build Robot only
  python -m deploy.installer.build --clean      Clean build
  python -m deploy.installer.build --sign       Build with code signing
        """,
    )

    # Target selection
    target_group = parser.add_mutually_exclusive_group()
    target_group.add_argument(
        "--canvas",
        action="store_true",
        help="Build Canvas (Designer + Robot) only",
    )
    target_group.add_argument(
        "--robot",
        action="store_true",
        help="Build Robot agent only",
    )

    # Build options
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean build directories before building",
    )
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Skip running tests",
    )
    parser.add_argument(
        "--sign",
        action="store_true",
        help="Sign executables (requires certificate configuration)",
    )
    parser.add_argument(
        "--include-browsers",
        action="store_true",
        help="Include Playwright browsers in Canvas build (~200MB)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Build with debug information",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Verbose output",
    )

    # Output format
    parser.add_argument(
        "--format",
        choices=["nsis", "msi", "portable"],
        default="nsis",
        help="Installer format (default: nsis)",
    )

    args = parser.parse_args()

    # Determine target
    if args.canvas:
        target = BuildTarget.CANVAS
    elif args.robot:
        target = BuildTarget.ROBOT
    else:
        target = BuildTarget.BOTH

    # Create config
    config = BuildConfig(
        target=target,
        format=BuildFormat(args.format),
        clean=args.clean,
        skip_tests=args.skip_tests,
        sign=args.sign,
        include_browsers=args.include_browsers,
        debug=args.debug,
        verbose=args.verbose,
    )

    # Build
    builder = InstallerBuilder(config)
    success = builder.build()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
