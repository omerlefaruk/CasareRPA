"""
UI initializers for MainWindow.

This package contains extracted initialization logic from MainWindow
to reduce its size and improve maintainability:

- UIComponentInitializer: Panel, dock, and debug component initialization
- ControllerRegistrar: Controller instantiation and signal wiring
"""

from casare_rpa.presentation.canvas.initializers.controller_registrar import (
    ControllerRegistrar,
)
from casare_rpa.presentation.canvas.initializers.ui_component_initializer import (
    UIComponentInitializer,
)

__all__ = [
    "UIComponentInitializer",
    "ControllerRegistrar",
]
