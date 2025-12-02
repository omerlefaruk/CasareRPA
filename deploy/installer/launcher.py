#!/usr/bin/env python3
"""
CasareRPA Launcher with Setup Wizard.

This script serves as the entry point for installed CasareRPA clients.
It checks for first-run setup needs and launches the appropriate mode.

Usage:
    python launcher.py [--robot] [--designer] [--setup]

Options:
    --robot     Launch robot agent only (headless mode)
    --designer  Launch workflow designer only
    --setup     Force show setup wizard
    --config    Path to config file (default: %APPDATA%/CasareRPA/config.yaml)
"""

import argparse
import sys
from pathlib import Path


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="CasareRPA Launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--robot",
        action="store_true",
        help="Launch robot agent only (headless mode)",
    )
    parser.add_argument(
        "--designer",
        action="store_true",
        help="Launch workflow designer only",
    )
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Force show setup wizard",
    )
    parser.add_argument(
        "--config",
        type=str,
        help="Path to config file",
    )

    args = parser.parse_args()

    # Add src to path if running from source
    src_dir = Path(__file__).parent.parent.parent / "src"
    if src_dir.exists():
        sys.path.insert(0, str(src_dir))

    try:
        from casare_rpa.presentation.setup import ClientConfigManager

        # Initialize config manager
        config_manager = ClientConfigManager()
        if args.config:
            config_manager = ClientConfigManager(config_dir=Path(args.config).parent)

        # Check if setup is needed
        needs_setup = args.setup or config_manager.needs_setup()

        if needs_setup and not args.robot:
            # Show setup wizard (requires Qt)
            from PySide6.QtWidgets import QApplication

            app = QApplication.instance() or QApplication(sys.argv)

            from casare_rpa.presentation.setup import SetupWizard

            wizard = SetupWizard(config_manager)
            result = wizard.exec()

            if result != wizard.DialogCode.Accepted:
                print("Setup cancelled. Run with --setup to configure later.")
                if not args.robot:
                    return 0

        # Launch appropriate mode
        if args.robot:
            # Launch robot agent
            from casare_rpa.agent_main import main as robot_main

            return robot_main()

        else:
            # Launch designer (default)
            from casare_rpa.presentation.canvas import main as canvas_main

            return canvas_main()

    except ImportError as e:
        print(f"Error: Missing dependency - {e}")
        print("Run: pip install -e . to install dependencies")
        return 1

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
