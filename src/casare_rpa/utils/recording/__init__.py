"""
CasareRPA - Action Recording Utilities

Browser and desktop action recording, processing, and workflow generation.
"""

from casare_rpa.utils.recording.browser_recorder import (
    BrowserRecorder,
    BrowserRecordedAction,
    BrowserActionType,
)
from casare_rpa.utils.recording.action_processor import ActionProcessor

__all__ = [
    "BrowserRecorder",
    "BrowserRecordedAction",
    "BrowserActionType",
    "ActionProcessor",
]
