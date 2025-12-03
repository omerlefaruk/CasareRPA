"""
Desktop Automation Managers

Modular managers for desktop automation operations.
Each manager handles a specific domain of desktop automation.
"""

from casare_rpa.desktop.managers.form_interactor import FormInteractor
from casare_rpa.desktop.managers.keyboard_controller import KeyboardController
from casare_rpa.desktop.managers.mouse_controller import MouseController
from casare_rpa.desktop.managers.screen_capture import ScreenCapture
from casare_rpa.desktop.managers.wait_manager import WaitManager
from casare_rpa.desktop.managers.window_manager import WindowManager

__all__ = [
    "WindowManager",
    "MouseController",
    "KeyboardController",
    "FormInteractor",
    "ScreenCapture",
    "WaitManager",
]
