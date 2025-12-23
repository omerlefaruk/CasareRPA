"""
Base Expression Editor for CasareRPA.

Provides the abstract base class and enum for expression editors.
All concrete editor implementations must inherit from BaseExpressionEditor.

Design follows KISS principle - minimal interface with essential methods only.
"""

from abc import ABCMeta, abstractmethod
from enum import Enum

from loguru import logger
from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import QWidget


class EditorType(Enum):
    """
    Editor type enumeration.

    Determines which editor to create for a given property.
    """

    CODE_PYTHON = "python"
    CODE_JAVASCRIPT = "javascript"
    CODE_CMD = "cmd"
    CODE_JSON = "json"
    CODE_YAML = "yaml"
    CODE_MARKDOWN = "markdown"
    RICH_TEXT = "rich_text"
    AUTO = "auto"


# Combined metaclass for Qt + ABC to avoid metaclass conflict with Python 3.13+
class QABCMeta(type(QWidget), ABCMeta):
    """Metaclass combining Qt's metaclass with ABCMeta."""

    pass


class BaseExpressionEditor(QWidget, metaclass=QABCMeta):
    """
    Abstract base class for all expression editors.

    Provides common interface for:
    - Value get/set operations
    - Variable insertion
    - Cursor position tracking
    - Change notifications

    All concrete editors (CodeExpressionEditor, MarkdownEditor, etc.)
    must inherit from this class.

    Signals:
        value_changed: Emitted when editor content changes (str: new_value)
    """

    value_changed = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        """
        Initialize the base expression editor.

        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)
        self._editor_type: EditorType | None = None
        logger.debug("BaseExpressionEditor initialized")

    @property
    def editor_type(self) -> EditorType | None:
        """Get the editor type for this editor."""
        return self._editor_type

    @abstractmethod
    def get_value(self) -> str:
        """
        Get the current editor content.

        Returns:
            Current text content of the editor
        """
        ...

    @abstractmethod
    def set_value(self, value: str) -> None:
        """
        Set the editor content.

        Args:
            value: Text to set in the editor
        """
        ...

    @abstractmethod
    def insert_at_cursor(self, text: str) -> None:
        """
        Insert text at the current cursor position.

        Args:
            text: Text to insert
        """
        ...

    @abstractmethod
    def get_cursor_position(self) -> int:
        """
        Get the current cursor position.

        Returns:
            Character offset of cursor from start of document
        """
        ...

    def insert_variable(self, var_text: str) -> None:
        """
        Insert a variable reference at the cursor position.

        Convenience method that wraps insert_at_cursor for variable insertion.
        Subclasses can override for special handling (e.g., autocomplete popup).

        Args:
            var_text: Variable reference text (e.g., "{{node_id.port_name}}")
        """
        logger.debug(f"Inserting variable: {var_text}")
        self.insert_at_cursor(var_text)

    def set_focus(self) -> None:
        """Set focus to the editor widget."""
        self.setFocus()

    @Slot()
    def _on_content_changed(self) -> None:
        """
        Handle internal content change.

        Subclasses should connect their text widget's change signal to this slot.
        This emits the value_changed signal with the current content.
        """
        self.value_changed.emit(self.get_value())
