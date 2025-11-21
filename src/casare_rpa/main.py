"""
CasareRPA - Main Entry Point
Launches the application with proper initialization.
"""

import sys
from typing import NoReturn
from loguru import logger


def main() -> NoReturn:
    """
    Main entry point for CasareRPA application.
    Initializes logging and launches the GUI.
    """
    try:
        # Import configuration and setup logging
        from casare_rpa.utils import setup_logging, APP_NAME, APP_VERSION

        setup_logging()
        logger.info("=" * 80)
        logger.info(f"{APP_NAME} v{APP_VERSION} - Starting Application")
        logger.info("=" * 80)

        # Phase 3: GUI initialization will be added here
        # from casare_rpa.gui import MainWindow
        # app = QApplication(sys.argv)
        # window = MainWindow()
        # window.show()
        # sys.exit(app.exec())

        # Temporary placeholder for Phase 1
        logger.info("Phase 1: Foundation setup complete")
        logger.info("GUI will be initialized in Phase 3")
        logger.success("CasareRPA is ready for development!")

        print("\n" + "=" * 80)
        print(f"✅ {APP_NAME} v{APP_VERSION} - Foundation Setup Complete!")
        print("=" * 80)
        print("\n📋 Project Structure Created:")
        print("  ✓ Core package (src/casare_rpa/core)")
        print("  ✓ Nodes package (src/casare_rpa/nodes)")
        print("  ✓ GUI package (src/casare_rpa/gui)")
        print("  ✓ Runner package (src/casare_rpa/runner)")
        print("  ✓ Utils package (src/casare_rpa/utils)")
        print("\n📦 Configuration Files:")
        print("  ✓ requirements.txt")
        print("  ✓ pyproject.toml")
        print("  ✓ README.md")
        print("\n🚀 Ready for Phase 2: Core Architecture Development")
        print("=" * 80 + "\n")

    except Exception as e:
        logger.exception(f"Fatal error during startup: {e}")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
