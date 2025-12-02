"""
Canvas (Designer + Robot) PyInstaller Spec Configuration.

Full application build including:
- CasareRPA Designer (GUI workflow editor)
- CasareRPA Robot Agent (headless executor)

Usage:
    pyinstaller deploy/installer/specs/canvas.py
"""

# This file is designed to be executed by PyInstaller as a spec file
# It imports configuration from base.py

import sys
from pathlib import Path

# Add installer directory to path for imports
_spec_dir = Path(globals().get("SPECPATH", Path(__file__).parent))
_installer_dir = _spec_dir.parent if _spec_dir.name == "specs" else _spec_dir
sys.path.insert(0, str(_installer_dir))

from specs.base import (
    APP_ICON,
    INSTALLER_DIR,
    PROJECT_ROOT,
    SRC_DIR,
    check_icon_exists,
    check_version_info_exists,
    get_canvas_analysis_kwargs,
    get_version,
)

# Application metadata
APP_NAME = "CasareRPA"
APP_VERSION = get_version()
APP_DESCRIPTION = "Windows Desktop RPA Platform"

# Entry points
MAIN_SCRIPT = str(PROJECT_ROOT / "run.py")
ROBOT_SCRIPT = str(SRC_DIR / "casare_rpa" / "agent_main.py")

# Build configuration
_analysis_kwargs = get_canvas_analysis_kwargs()

# Main Analysis
a = Analysis(
    [MAIN_SCRIPT],
    **_analysis_kwargs,
)

# Remove duplicates
pyz = PYZ(a.pure)

# Main executable (GUI)
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
    console=False,  # GUI application
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=check_icon_exists(),
    version=check_version_info_exists(),
)

# Robot executable (headless)
robot_analysis = Analysis(
    [ROBOT_SCRIPT],
    **_analysis_kwargs,
)

robot_exe = EXE(
    PYZ(robot_analysis.pure),
    robot_analysis.scripts,
    [],
    exclude_binaries=True,
    name=f"{APP_NAME}-Robot",
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
    icon=check_icon_exists(),
)

# Collect all files into distribution directory
coll = COLLECT(
    exe,
    robot_exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=APP_NAME,
)
