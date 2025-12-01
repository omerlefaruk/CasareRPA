"""
CasareRPA - Icon Provider for Toolbar Actions.

Uses Qt's built-in standard icons for consistent, theme-aware icons
that work on all platforms without external assets.

For custom icons, use ResourceCache.get_icon(path) from resources.py.
"""

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QStyle


class ToolbarIcons:
    """
    Provides icons for toolbar actions using Qt standard icons.

    Qt standard icons are:
    - Always available (no external files needed)
    - Theme-aware (respect system theme on all platforms)
    - Properly scaled for different DPI settings

    Usage:
        icon = ToolbarIcons.get_icon("run")
        action.setIcon(icon)
    """

    # Maps action names to Qt StandardPixmap enum values
    # See: https://doc.qt.io/qt-6/qstyle.html#StandardPixmap-enum
    _ICON_MAP = {
        # File operations
        "new": "SP_FileIcon",
        "open": "SP_DirOpenIcon",
        "save": "SP_DialogSaveButton",
        "save_as": "SP_DialogSaveButton",
        # Edit operations
        "undo": "SP_ArrowBack",
        "redo": "SP_ArrowForward",
        "cut": "SP_FileIcon",  # No standard cut icon
        "copy": "SP_FileDialogContentsView",
        "paste": "SP_FileDialogDetailedView",
        "delete": "SP_TrashIcon",
        "find": "SP_FileDialogContentsView",
        # Execution operations
        "run": "SP_MediaPlay",
        "pause": "SP_MediaPause",
        "resume": "SP_MediaPlay",
        "stop": "SP_MediaStop",
        "step": "SP_MediaSeekForward",
        "continue": "SP_MediaSkipForward",
        # Debug operations
        "debug": "SP_FileDialogInfoView",
        "breakpoint": "SP_DialogCancelButton",
        "clear_breakpoints": "SP_DialogResetButton",
        # View operations
        "zoom_in": "SP_ArrowUp",
        "zoom_out": "SP_ArrowDown",
        "zoom_reset": "SP_BrowserReload",
        "fit_view": "SP_DesktopIcon",
        "save_layout": "SP_DialogApplyButton",
        # Tools
        "record": "SP_DialogApplyButton",
        "pick_selector": "SP_DialogHelpButton",
        "preferences": "SP_FileDialogDetailedView",
        "help": "SP_DialogHelpButton",
        "about": "SP_MessageBoxInformation",
        # Status indicators
        "info": "SP_MessageBoxInformation",
        "warning": "SP_MessageBoxWarning",
        "error": "SP_MessageBoxCritical",
        "success": "SP_DialogApplyButton",
    }

    _style: Optional["QStyle"] = None

    @classmethod
    def _get_style(cls) -> "QStyle":
        """Get the application style (cached)."""
        if cls._style is None:
            from PySide6.QtWidgets import QApplication

            app = QApplication.instance()
            if app:
                cls._style = app.style()
            else:
                # Fallback: create style without app
                from PySide6.QtWidgets import QStyleFactory

                cls._style = QStyleFactory.create("Fusion")
        return cls._style

    @classmethod
    def get_icon(cls, name: str) -> "QIcon":
        """
        Get a toolbar icon by action name.

        Args:
            name: Action name (e.g., "run", "stop", "save")

        Returns:
            QIcon for the action, or empty QIcon if not found
        """
        from PySide6.QtGui import QIcon
        from PySide6.QtWidgets import QStyle

        pixmap_name = cls._ICON_MAP.get(name)
        if not pixmap_name:
            return QIcon()

        style = cls._get_style()
        if not style:
            return QIcon()

        # Get the StandardPixmap enum value
        try:
            pixmap_enum = getattr(QStyle.StandardPixmap, pixmap_name, None)
            if pixmap_enum is None:
                return QIcon()
            return style.standardIcon(pixmap_enum)
        except (AttributeError, TypeError):
            return QIcon()

    @classmethod
    def get_all_icons(cls) -> dict:
        """
        Get all available toolbar icons.

        Returns:
            Dictionary mapping action names to QIcon instances
        """
        return {name: cls.get_icon(name) for name in cls._ICON_MAP.keys()}


def get_toolbar_icon(name: str) -> "QIcon":
    """
    Convenience function to get a toolbar icon.

    Args:
        name: Action name

    Returns:
        QIcon for the action
    """
    return ToolbarIcons.get_icon(name)
