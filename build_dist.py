"""
CasareRPA Build Script
Builds all three components: Canvas, Robot, and Orchestrator
"""
import subprocess
import shutil
from pathlib import Path

def clean():
    """Remove previous build artifacts."""
    print("🧹 Cleaning previous builds...")
    shutil.rmtree("dist", ignore_errors=True)
    shutil.rmtree("build", ignore_errors=True)
    for spec in Path(".").glob("*.spec"):
        spec.unlink()
    print("✅ Clean complete\n")

def build_canvas():
    """Build Canvas (Workflow Designer)."""
    print("📦 Building Canvas...")
    subprocess.run([
        "pyinstaller",
        "--name=CasareRPA-Canvas",
        "--windowed",
        "--paths=src",  # Add src to path
        "--add-data=workflows;workflows",
        "--hidden-import=casare_rpa",
        "--hidden-import=casare_rpa.canvas",
        "--hidden-import=casare_rpa.nodes",
        "--hidden-import=playwright",
        "--hidden-import=PySide6",
        "--hidden-import=PySide6.QtSvg",  # Required for NodeGraphQt SVG nodes
        "--hidden-import=qasync",
        "--onedir",
        "--clean",
        "run.py"
    ], check=True)
    print("✅ Canvas built\n")

def build_robot():
    """Build Robot (Execution Agent)."""
    print("📦 Building Robot...")
    subprocess.run([
        "pyinstaller",
        "--name=CasareRPA-Robot",
        "--windowed",
        "--paths=src",  # Add src to path
        "--hidden-import=casare_rpa.robot",
        "--hidden-import=casare_rpa.utils",
        "--hidden-import=playwright",
        "--hidden-import=PySide6",
        "--hidden-import=qasync",
        "--onedir",
        "--clean",
        "src/casare_rpa/robot/tray_icon.py"
    ], check=True)
    print("✅ Robot built\n")

def build_orchestrator():
    """Build Orchestrator (Robot Manager)."""
    print("📦 Building Orchestrator...")
    subprocess.run([
        "pyinstaller",
        "--name=CasareRPA-Orchestrator",
        "--windowed",
        "--paths=src",  # Add src to path
        "--hidden-import=casare_rpa.orchestrator",
        "--hidden-import=supabase",
        "--hidden-import=PySide6",
        "--hidden-import=qasync",
        "--onedir",
        "--clean",
        "src/casare_rpa/orchestrator/main_window.py"
    ], check=True)
    print("✅ Orchestrator built\n")

def main():
    print("🚀 Building CasareRPA Distribution\n")
    print("=" * 50)
    
    clean()
    build_canvas()
    build_robot()
    build_orchestrator()
    
    print("=" * 50)
    print("\n✅ BUILD COMPLETE!\n")
    print("📁 Output location: dist/\n")
    print("Built applications:")
    print("  • Canvas:       dist/CasareRPA-Canvas/CasareRPA-Canvas.exe")
    print("  • Robot:        dist/CasareRPA-Robot/CasareRPA-Robot.exe")
    print("  • Orchestrator: dist/CasareRPA-Orchestrator/CasareRPA-Orchestrator.exe")
    print("\nℹ️  You can copy these folders to any Windows PC and run them directly!")

if __name__ == "__main__":
    main()
