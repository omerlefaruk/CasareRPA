"""
Entry point for running the canvas application as a module.
"""

import sys

# Apply QFont fix BEFORE any Qt imports to prevent "Point size <= 0" warnings
from PySide6.QtGui import QFont

_original_setPointSize = QFont.setPointSize


def _safe_setPointSize(self, size: int) -> None:
    if size <= 0:
        size = 9
    _original_setPointSize(self, size)


QFont.setPointSize = _safe_setPointSize

from casare_rpa.presentation.canvas.app import main

if __name__ == "__main__":
    sys.exit(main())
