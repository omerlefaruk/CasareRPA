"""
Base widget class for all UI components.

Provides common patterns, stylesheet management, and signal/slot conventions
for all reusable UI widgets in the CasareRPA Canvas application.
"""

from abc import ABCMeta, abstractmethod
from typing import Any

from loguru import logger
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget

from casare_rpa.presentation.canvas.theme import TOKENS_V2 as TOKENS


# Create combined metaclass for Qt + ABC to avoid metaclass conflict
class QABCMeta(type(QWidget), ABCMeta):
    """Metaclass combining Qt's metaclass with ABCMeta."""

    pass


class BaseWidget(QWidget, metaclass=QABCMeta):
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

    def __init__(self, parent: QWidget | None = None) -> None:
        """
        Initialize the base widget.

        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)

        # Component state
        self._is_initialized = False
        self._state: dict[str, Any] = {}

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
        # Use theme tokens for colors and sizes
        bg_dark = "#27272a"  # TOKENS would require full theme import
        bg_medium = "#3f3f46"
        text_primary = "#f4f4f5"
        text_secondary = "#a1a1aa"
        border_color = "#52525b"
        accent = "#6366f1"
        disabled = "#52525b"

        return f"""
            QWidget {{
                background-color: {bg_dark};
                color: {text_primary};
                font-family: {TOKENS.typography.ui};
                font-size: {TOKENS.typography.body}pt;
            }}

            QLabel {{
                color: {text_primary};
                background: transparent;
            }}

            QPushButton {{
                background-color: {bg_medium};
                border: 1px solid {border_color};
                border-radius: {TOKENS.radius.md}px;
                color: {text_primary};
                padding: {TOKENS.spacing.xxs}px {TOKENS.spacing.md}px;
                min-height: {TOKENS.sizes.button_sm}px;
            }}

            QPushButton:hover {{
                background-color: {border_color};
                border: 1px solid {accent};
            }}

            QPushButton:pressed {{
                background-color: {bg_dark};
            }}

            QPushButton:disabled {{
                background-color: {bg_dark};
                color: {disabled};
            }}

            QLineEdit, QTextEdit, QPlainTextEdit {{
                background-color: {bg_medium};
                border: 1px solid {border_color};
                border-radius: {TOKENS.radius.md}px;
                color: {text_primary};
                padding: {TOKENS.spacing.sm}px;
                selection-background-color: {accent};
            }}

            QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
                border: 1px solid {accent};
            }}

            QSpinBox, QDoubleSpinBox {{
                background-color: {bg_medium};
                border: 1px solid {border_color};
                border-radius: {TOKENS.radius.md}px;
                color: {text_primary};
                padding: {TOKENS.spacing.sm}px;
            }}

            QSpinBox:focus, QDoubleSpinBox:focus {{
                border: 1px solid {accent};
            }}

            QComboBox {{
                background-color: {bg_medium};
                border: 1px solid {border_color};
                border-radius: {TOKENS.radius.md}px;
                color: {text_primary};
                padding: {TOKENS.spacing.sm}px;
            }}

            QComboBox:focus {{
                border: 1px solid {accent};
            }}

            QComboBox::drop-down {{
                border: none;
                width: {TOKENS.sizes.combo_dropdown_width}px;
            }}

            QComboBox::down-arrow {{
                image: none;
                border-left: {TOKENS.spacing.sm}px solid transparent;
                border-right: {TOKENS.spacing.sm}px solid transparent;
                border-top: {TOKENS.spacing.sm}px solid {text_primary};
                margin-right: {TOKENS.spacing.sm}px;
            }}

            QCheckBox {{
                color: {text_primary};
                spacing: {TOKENS.spacing.sm}px;
            }}

            QCheckBox::indicator {{
                width: {TOKENS.sizes.checkbox_size}px;
                height: {TOKENS.sizes.checkbox_size}px;
                border: 1px solid {border_color};
                border-radius: {TOKENS.radius.sm}px;
                background-color: {bg_medium};
            }}

            QCheckBox::indicator:checked {{
                background-color: {accent};
                border: 1px solid {accent};
            }}

            QScrollBar:vertical {{
                background: {bg_dark};
                width: {TOKENS.sizes.scrollbar_width}px;
                border-radius: {TOKENS.radius.sm}px;
            }}

            QScrollBar::handle:vertical {{
                background: {border_color};
                border-radius: {TOKENS.radius.sm}px;
                min-height: {TOKENS.sizes.scrollbar_min_height}px;
            }}

            QScrollBar::handle:vertical:hover {{
                background: {text_secondary};
            }}

            QScrollBar:horizontal {{
                background: {bg_dark};
                height: {TOKENS.sizes.scrollbar_width}px;
                border-radius: {TOKENS.radius.sm}px;
            }}

            QScrollBar::handle:horizontal {{
                background: {border_color};
                border-radius: {TOKENS.radius.sm}px;
                min-width: {TOKENS.sizes.scrollbar_min_height}px;
            }}

            QScrollBar::handle:horizontal:hover {{
                background: {text_secondary};
            }}

            QTableWidget {{
                background-color: {bg_dark};
                alternate-background-color: {bg_medium};
                border: 1px solid {border_color};
                gridline-color: {bg_medium};
                color: {text_primary};
            }}

            QTableWidget::item:selected {{
                background-color: {accent};
            }}

            QHeaderView::section {{
                background-color: {bg_medium};
                color: {text_primary};
                border: none;
                border-right: 1px solid {border_color};
                border-bottom: 1px solid {border_color};
                padding: {TOKENS.spacing.sm}px;
            }}
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

    def __init__(self, title: str, parent: QWidget | None = None) -> None:
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

    def __init__(self, parent: QWidget | None = None) -> None:
        """
        Initialize the dialog.

        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)
        self._result: Any | None = None

    def validate(self) -> bool:
        """
        Validate dialog input.

        Override this method to implement custom validation logic.

        Returns:
            True if validation passes, False otherwise
        """
        return True

    def get_result(self) -> Any | None:
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
