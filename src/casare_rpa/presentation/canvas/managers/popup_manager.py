"""
Popup Manager for CasareRPA.

Centralized manager for popup lifecycle and click-outside-to-close handling.

Provides a single app-level event filter that manages all popup windows,
eliminating the need for each popup to install its own filter.

Features:
- Single app-level event filter for all popups
- Automatic click-outside-to-close handling
- Weak references to avoid memory leaks
- Pin state support (pinned popups don't close on click-outside)
- Simple registration/unregistration API
"""

from typing import TYPE_CHECKING
from weakref import WeakSet

from loguru import logger
from PySide6.QtCore import QEvent, QObject
from PySide6.QtWidgets import QApplication

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget


class PopupManager(QObject):
    """
    Centralized manager for popup lifecycle and click-outside handling.

    Each popup widget registers itself on show and unregisters on close.
    The manager maintains a single app-level event filter that closes
    popups when clicking outside their geometry.

    Usage:
        class MyPopup(QWidget):
            def showEvent(self, event):
                super().showEvent(event)
                PopupManager.register(self)

            def closeEvent(self, event):
                PopupManager.unregister(self)
                super().closeEvent(event)
    """

    _instance: "PopupManager | None" = None

    def __init__(self) -> None:
        """Initialize the popup manager (singleton)."""
        super().__init__()
        self._active_popups: WeakSet[QWidget] = WeakSet()
        self._filter_installed = False

    @classmethod
    def get_instance(cls) -> "PopupManager":
        """Get the singleton PopupManager instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def register(cls, popup: "QWidget", pinned: bool = False) -> None:
        """
        Register a popup for click-outside handling.

        Args:
            popup: The popup widget to register
            pinned: If True, popup won't close on click-outside (default: False)
        """
        manager = cls.get_instance()
        manager._register(popup, pinned)

    @classmethod
    def unregister(cls, popup: "QWidget") -> None:
        """
        Unregister a popup from click-outside handling.

        Args:
            popup: The popup widget to unregister
        """
        manager = cls.get_instance()
        manager._unregister(popup)

    @classmethod
    def install_global_filter(cls, app: QApplication) -> None:
        """
        Install the global event filter on QApplication.

        This should be called once during application initialization.

        Args:
            app: The QApplication instance
        """
        manager = cls.get_instance()
        manager._install_filter(app)

    @classmethod
    def close_popup(cls, popup: "QWidget") -> None:
        """
        Close a specific popup.

        Args:
            popup: The popup to close
        """
        if popup is not None:
            try:
                if popup.isVisible():
                    popup.close()
            except RuntimeError:
                # Widget was already deleted
                cls.get_instance()._unregister(popup)

    @classmethod
    def close_all_popups(cls, exclude_pinned: bool = True) -> None:
        """
        Close all active popups.

        Args:
            exclude_pinned: If True, don't close pinned popups (default: True)
        """
        manager = cls.get_instance()
        for popup in list(manager._active_popups):
            if exclude_pinned and manager._is_pinned(popup):
                continue
            cls.close_popup(popup)

    @classmethod
    def is_any_dragging(cls) -> bool:
        """
        Check if any registered popup is currently being dragged.

        This is used to prevent click-outside-to-close from triggering
        during drag operations.

        Returns:
            True if any popup is currently dragging
        """
        manager = cls.get_instance()
        for popup in manager._active_popups:
            if hasattr(popup, "is_dragging") and popup.is_dragging():
                return True
        return False

    def _register(self, popup: "QWidget", pinned: bool = False) -> None:
        """Register a popup (internal)."""
        self._active_popups.add(popup)
        if pinned:
            # Store pinned state as widget attribute
            popup._popup_manager_pinned = True

    def _unregister(self, popup: "QWidget") -> None:
        """Unregister a popup (internal)."""
        self._active_popups.discard(popup)
        if hasattr(popup, "_popup_manager_pinned"):
            delattr(popup, "_popup_manager_pinned")

    def _is_pinned(self, popup: "QWidget") -> bool:
        """Check if a popup is pinned."""
        return getattr(popup, "_popup_manager_pinned", False)

    def _install_filter(self, app: QApplication) -> None:
        """Install the event filter on QApplication (internal)."""
        if not self._filter_installed:
            app.installEventFilter(self)
            self._filter_installed = True
            logger.debug("PopupManager: Installed global event filter")

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """
        Event filter to close popups when clicking outside.

        This is called by Qt for all events in the application.

        Args:
            obj: The object receiving the event
            event: The event

        Returns:
            False to let the event propagate
        """
        if event.type() == QEvent.Type.MouseButtonPress:
            self._handle_mouse_press(event)

        return False  # Never consume events

    def _handle_mouse_press(self, event: QEvent) -> None:
        """Handle mouse press event for click-outside-to-close."""
        # Get global position of the click
        if hasattr(event, "globalPosition"):
            global_pos = event.globalPosition().toPoint()
        else:
            global_pos = event.globalPos()

        # Check each active popup
        for popup in list(self._active_popups):
            if not popup.isVisible():
                continue

            # Skip pinned popups
            if self._is_pinned(popup):
                continue

            # Check if click is outside popup geometry
            if not popup.geometry().contains(global_pos):
                # Close the popup
                self.close_popup(popup)


# Convenience singleton accessor
get_popup_manager = PopupManager.get_instance
