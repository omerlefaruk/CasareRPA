"""
Robot-Only PyInstaller Spec Configuration.

Lightweight build containing ONLY the robot agent for VM deployment.
Pre-configured for Supabase connection.

Usage:
    pyinstaller deploy/installer/specs/robot.py
"""

import sys
from pathlib import Path

# Add installer directory to path for imports
_spec_dir = Path(globals().get("SPECPATH", Path(__file__).parent))
_installer_dir = _spec_dir.parent if _spec_dir.name == "specs" else _spec_dir
sys.path.insert(0, str(_installer_dir))

from specs.base import (
    SRC_DIR,
    get_robot_analysis_kwargs,
    get_version,
)

# Application metadata
APP_NAME = "CasareRPA-Robot"
APP_VERSION = get_version()
APP_DESCRIPTION = "CasareRPA Robot Agent"

# Entry point
ROBOT_CLI = str(SRC_DIR / "casare_rpa" / "robot" / "cli.py")

# Build configuration
_analysis_kwargs = get_robot_analysis_kwargs()

# Analysis
a = Analysis(
    [ROBOT_CLI],
    **_analysis_kwargs,
)

# Remove duplicates
pyz = PYZ(a.pure)

# Executable
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Robot runs with console for logging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Icon disabled for robot build
)

# Collect all files
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=APP_NAME,
)
