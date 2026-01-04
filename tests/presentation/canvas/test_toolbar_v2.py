import os

import pytest
from PySide6.QtWidgets import QMainWindow

from casare_rpa.presentation.canvas.ui.chrome.toolbar_v2 import ToolbarV2

# Ensure Qt headless mode
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.mark.ui
def test_toolbar_hotkey_manager_action_emits_signal(qtbot):
    mw = QMainWindow()
    toolbar = ToolbarV2(mw)
    mw.addToolBar(toolbar)

    assert hasattr(toolbar, "action_keyboard_shortcuts")

    with qtbot.waitSignal(toolbar.keyboard_shortcuts_requested, timeout=1000):
        toolbar.action_keyboard_shortcuts.trigger()
