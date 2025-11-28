"""
Desktop Automation Managers

Modular managers for desktop automation operations.
Each manager handles a specific domain of desktop automation.
"""

from .window_manager import WindowManager
from .mouse_controller import MouseController
from .keyboard_controller import KeyboardController
from .form_interactor import FormInteractor
from .screen_capture import ScreenCapture
from .wait_manager import WaitManager

__all__ = [
    "WindowManager",
    "MouseController",
    "KeyboardController",
    "FormInteractor",
    "ScreenCapture",
    "WaitManager",
]
