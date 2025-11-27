"""
Base widget class for all UI components.

Provides common patterns, stylesheet management, and signal/slot conventions
for all reusable UI widgets in the CasareRPA Canvas application.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

from PySide6.QtCore import Signal, QObject
from PySide6.QtWidgets import QWidget

from loguru import logger


class BaseWidget(QWidget, ABC):
    """
    Abstract base class for all reusable UI widgets.

    Provides:
    - Consistent initialization pattern
    - Stylesheet management
    - Common signals
    - Logging integration

    Signals:
        value_changed: Emitted when widget value changes (object: new_value)
        state_changed: Emitted when widget state changes (str: state_name, Any: state_value)
    """

    value_changed = Signal(object)
    state_changed = Signal(str, object)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the base widget.

        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)

        # Component state
        self._is_initialized = False
        self._state: Dict[str, Any] = {}

        # Initialize component
        try:
            self.setup_ui()
            self.apply_stylesheet()
            self.connect_signals()
            self._is_initialized = True
            logger.debug(f"{self.__class__.__name__} initialized")
        except Exception as e:
            logger.error(f"Failed to initialize {self.__class__.__name__}: {e}")
            raise

    @abstractmethod
    def setup_ui(self) -> None:
        """
        Set up the user interface elements.

        This method must be implemented by subclasses to create
        and arrange all UI widgets.
        """
        pass

    def apply_stylesheet(self) -> None:
        """
        Apply component stylesheet.

        Override this method to customize component appearance.
        Default implementation applies dark theme styles.
        """
        self.setStyleSheet(self._get_default_stylesheet())

    def connect_signals(self) -> None:
        """
        Connect internal signal/slot connections.

        Override this method to set up signal/slot connections
        between child widgets. Default implementation does nothing.
        """
        pass

    def _get_default_stylesheet(self) -> str:
        """
        Get default dark theme stylesheet.

        Returns:
            CSS stylesheet string
        """
        return """
            QWidget {
                background-color: #252525;
                color: #e0e0e0;
                font-family: "Segoe UI", Arial, sans-serif;
                font-size: 9pt;
            }

            QLabel {
                color: #e0e0e0;
                background: transparent;
            }

            QPushButton {
                background-color: #3d3d3d;
                border: 1px solid #4a4a4a;
                border-radius: 3px;
                color: #e0e0e0;
                padding: 5px 15px;
                min-height: 20px;
            }

            QPushButton:hover {
                background-color: #4a4a4a;
                border: 1px solid #5a8a9a;
            }

            QPushButton:pressed {
                background-color: #2d2d2d;
            }

            QPushButton:disabled {
                background-color: #2d2d2d;
                color: #666666;
            }

            QLineEdit, QTextEdit, QPlainTextEdit {
                background-color: #3d3d3d;
                border: 1px solid #4a4a4a;
                border-radius: 3px;
                color: #e0e0e0;
                padding: 4px;
                selection-background-color: #5a8a9a;
            }

            QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
                border: 1px solid #5a8a9a;
            }

            QSpinBox, QDoubleSpinBox {
                background-color: #3d3d3d;
                border: 1px solid #4a4a4a;
                border-radius: 3px;
                color: #e0e0e0;
                padding: 4px;
            }

            QSpinBox:focus, QDoubleSpinBox:focus {
                border: 1px solid #5a8a9a;
            }

            QComboBox {
                background-color: #3d3d3d;
                border: 1px solid #4a4a4a;
                border-radius: 3px;
                color: #e0e0e0;
                padding: 4px;
            }

            QComboBox:focus {
                border: 1px solid #5a8a9a;
            }

            QComboBox::drop-down {
                border: none;
                width: 20px;
            }

            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #e0e0e0;
                margin-right: 5px;
            }

            QCheckBox {
                color: #e0e0e0;
                spacing: 5px;
            }

            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #4a4a4a;
                border-radius: 2px;
                background-color: #3d3d3d;
            }

            QCheckBox::indicator:checked {
                background-color: #5a8a9a;
                border: 1px solid #5a8a9a;
            }

            QScrollBar:vertical {
                background: #2d2d2d;
                width: 12px;
                border-radius: 6px;
            }

            QScrollBar::handle:vertical {
                background: #4a4a4a;
                border-radius: 6px;
                min-height: 20px;
            }

            QScrollBar::handle:vertical:hover {
                background: #5a5a5a;
            }

            QScrollBar:horizontal {
                background: #2d2d2d;
                height: 12px;
                border-radius: 6px;
            }

            QScrollBar::handle:horizontal {
                background: #4a4a4a;
                border-radius: 6px;
                min-width: 20px;
            }

            QScrollBar::handle:horizontal:hover {
                background: #5a5a5a;
            }

            QTableWidget {
                background-color: #2d2d2d;
                alternate-background-color: #323232;
                border: 1px solid #4a4a4a;
                gridline-color: #3d3d3d;
                color: #e0e0e0;
            }

            QTableWidget::item:selected {
                background-color: #5a8a9a;
            }

            QHeaderView::section {
                background-color: #3d3d3d;
                color: #e0e0e0;
                border: none;
                border-right: 1px solid #4a4a4a;
                border-bottom: 1px solid #4a4a4a;
                padding: 4px;
            }
        """

    def set_state(self, key: str, value: Any) -> None:
        """
        Set internal state value.

        Args:
            key: State key
            value: State value
        """
        old_value = self._state.get(key)
        if old_value != value:
            self._state[key] = value
            self.state_changed.emit(key, value)
            logger.debug(f"{self.__class__.__name__} state changed: {key} = {value}")

    def get_state(self, key: str, default: Any = None) -> Any:
        """
        Get internal state value.

        Args:
            key: State key
            default: Default value if key not found

        Returns:
            State value or default
        """
        return self._state.get(key, default)

    def clear_state(self) -> None:
        """Clear all internal state."""
        self._state.clear()
        logger.debug(f"{self.__class__.__name__} state cleared")

    def is_initialized(self) -> bool:
        """
        Check if widget is fully initialized.

        Returns:
            True if initialization completed successfully
        """
        return self._is_initialized


class BaseDockWidget(BaseWidget):
    """
    Base class for dockable panels.

    Extends BaseWidget with dock-specific functionality like
    visibility toggles and position management.

    Signals:
        visibility_changed: Emitted when dock visibility changes (bool: visible)
    """

    visibility_changed = Signal(bool)

    def __init__(self, title: str, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the dock widget.

        Args:
            title: Dock widget title
            parent: Optional parent widget
        """
        self._title = title
        super().__init__(parent)

    def get_title(self) -> str:
        """
        Get dock widget title.

        Returns:
            Dock title
        """
        return self._title

    def set_title(self, title: str) -> None:
        """
        Set dock widget title.

        Args:
            title: New dock title
        """
        self._title = title
        logger.debug(f"{self.__class__.__name__} title changed to: {title}")


class BaseDialog(BaseWidget):
    """
    Base class for dialogs.

    Extends BaseWidget with dialog-specific functionality like
    accept/reject handling and validation.

    Signals:
        accepted: Emitted when dialog is accepted
        rejected: Emitted when dialog is rejected
    """

    accepted = Signal()
    rejected = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the dialog.

        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)
        self._result: Optional[Any] = None

    def validate(self) -> bool:
        """
        Validate dialog input.

        Override this method to implement custom validation logic.

        Returns:
            True if validation passes, False otherwise
        """
        return True

    def get_result(self) -> Optional[Any]:
        """
        Get dialog result.

        Returns:
            Dialog result value
        """
        return self._result

    def set_result(self, result: Any) -> None:
        """
        Set dialog result.

        Args:
            result: Result value
        """
        self._result = result
