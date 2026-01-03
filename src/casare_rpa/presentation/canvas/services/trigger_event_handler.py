"""
CasareRPA - Qt Trigger Event Handler

Presentation layer implementation of the TriggerEventHandler protocol.
Bridges application-layer trigger events to the Qt UI.

Architecture:
    Application Layer (TriggerEventHandler Protocol)
           ^
           |
    Presentation Layer (QtTriggerEventHandler - implements protocol)
           |
           v
    Qt Components (MainWindow, BottomPanel, etc.)
"""

from loguru import logger
from PySide6.QtCore import QTimer

from casare_rpa.presentation.canvas.interfaces import IMainWindow


class QtTriggerEventHandler:
    """
    Qt-based implementation of TriggerEventHandler protocol.

    Handles trigger events from CanvasTriggerRunner by delegating to
    Qt UI components. All UI operations are marshaled to the main thread
    using Qt's thread-safe mechanisms.

    This class implements the TriggerEventHandler protocol from
    casare_rpa.application.execution.interfaces.
    """

    def __init__(self, main_window: IMainWindow | None) -> None:
        """
        Initialize with the MainWindow reference.

        Args:
            main_window: The main application window
        """
        self._main_window = main_window

    def request_workflow_run(self) -> None:
        """
        Request the application to run the current workflow.

        Uses QMetaObject.invokeMethod to ensure the call happens
        on the Qt main thread, regardless of which thread this
        method is called from.
        """
        try:
            if self._main_window is None:
                logger.warning("No main window for workflow run request")
                return

            # Marshal to main thread. Emitting Qt signals is safe when scheduled
            # onto the main thread event loop.
            QTimer.singleShot(0, self._main_window.trigger_workflow_requested.emit)
            logger.debug("Workflow run request queued to main thread")

        except Exception as e:
            logger.error(f"Error requesting workflow run: {e}")

    def update_trigger_stats(self, trigger_id: str, count: int, last_triggered: str) -> None:
        """
        Update the UI with trigger statistics.

        Uses QTimer.singleShot to ensure the UI update happens
        on the main thread.

        Args:
            trigger_id: The ID of the trigger that fired
            count: The new execution count
            last_triggered: ISO timestamp of when the trigger last fired
        """
        try:
            if self._main_window is None:
                logger.warning("No main window for trigger stats update")
                return

            # Capture values to avoid closure issues
            _trigger_id = trigger_id
            _count = count
            _timestamp = last_triggered

            def do_update() -> None:
                """Perform the UI update on the main thread."""
                try:
                    bottom_panel = self._main_window.get_bottom_panel()
                    if not bottom_panel:
                        logger.warning("No bottom panel for trigger stats update")
                        return

                    triggers_tab = bottom_panel.get_triggers_tab()
                    if not triggers_tab:
                        logger.warning("No triggers tab for trigger stats update")
                        return

                    logger.debug(f"Updating trigger stats: {_trigger_id} -> count={_count}")
                    triggers_tab.update_trigger_stats(_trigger_id, _count, _timestamp)

                except Exception as e:
                    logger.error(f"Error in trigger stats UI update: {e}")

            # Schedule on main thread
            QTimer.singleShot(0, do_update)

        except Exception as e:
            logger.error(f"Error scheduling trigger stats update: {e}")

    def get_trigger_count(self, trigger_id: str) -> int:
        """
        Get the current execution count for a trigger.

        Note: This method may be called from a background thread,
        so we access the UI data carefully.

        Args:
            trigger_id: The ID of the trigger

        Returns:
            Current execution count, or 0 if not found
        """
        try:
            if self._main_window is None:
                return 0

            bottom_panel = self._main_window.get_bottom_panel()
            if not bottom_panel:
                return 0

            triggers_tab = bottom_panel.get_triggers_tab()
            if not triggers_tab:
                return 0

            # Get triggers list and find the matching one
            triggers = triggers_tab.get_triggers()
            for trigger in triggers:
                if trigger.get("id") == trigger_id:
                    return trigger.get("trigger_count", 0)

            return 0

        except Exception as e:
            logger.error(f"Error getting trigger count: {e}")
            return 0


def create_trigger_event_handler(
    main_window: IMainWindow | None = None,
) -> "QtTriggerEventHandler":
    """
    Factory function to create a QtTriggerEventHandler.

    Args:
        main_window: The main window instance. If None, will return
                     a handler that logs warnings when methods are called.

    Returns:
        QtTriggerEventHandler instance
    """
    if main_window is None:
        logger.warning(
            "Creating QtTriggerEventHandler without main window - trigger events will not update UI"
        )

    return QtTriggerEventHandler(main_window)
