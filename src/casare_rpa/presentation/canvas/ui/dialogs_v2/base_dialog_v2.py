"""
Base Dialog v2 - Core dialog framework.

Provides:
- ButtonRole enum (PRIMARY, SECONDARY, DESTRUCTIVE, CANCEL)
- DialogSizeV2 enum (SM, MD, LG)
- DialogFooter - Standardized button row
- DialogTitleBar - Optional draggable header
- BaseDialogV2 - Main dialog base class

Key features:
- Uses THEME_V2/TOKENS_V2 only (no hardcoded colors)
- @Slot decorator on all slot methods
- Escape key handling (reject dialog)
- Enter key for primary button (skip if text input focused)
- eventFilter on text widgets for Escape key
- Modal behavior
- Focus management (activateWindow, raise_)

Usage:
    from casare_rpa.presentation.canvas.ui.dialogs_v2 import BaseDialogV2, DialogSizeV2

    class MyDialog(BaseDialogV2):
        def __init__(self, parent=None):
            super().__init__(
                title="My Dialog",
                parent=parent,
                size=DialogSizeV2.MD,
            )
            content = QWidget()
            layout = QVBoxLayout(content)
            layout.addWidget(QLabel("Content here"))
            self.set_body_widget(content)
            self.set_primary_button("Save", self.accept)
            self.set_secondary_button("Cancel", self.reject)
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Callable

from loguru import logger
from PySide6.QtCore import QPoint, Qt, Signal, Slot
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.theme_system import THEME_V2, TOKENS_V2
from casare_rpa.presentation.canvas.ui.widgets.primitives.buttons import PushButton

if TYPE_CHECKING:
    from PySide6.QtGui import QKeyEvent


# =============================================================================
# ENUMS
# =============================================================================


class ButtonRole(Enum):
    """
    Button role for dialog footer buttons.

    Roles determine styling and behavior:
        PRIMARY: Main action (right-aligned), Enter key binding
        SECONDARY: Additional actions
        DESTRUCTIVE: Destructive actions (delete, etc.), uses error color
        CANCEL: Cancel action, Esc key binding
    """

    PRIMARY = "primary"
    SECONDARY = "secondary"
    DESTRUCTIVE = "destructive"
    CANCEL = "cancel"


class DialogSizeV2(Enum):
    """
    Predefined dialog sizes from TOKENS_V2.

        SM: 380x270 - Simple confirmations, single-field forms
        MD: 550x400 - Standard forms, settings panels (default)
        LG: 750x700 - Complex forms, multi-tab dialogs
    """

    SM = "sm"
    MD = "md"
    LG = "lg"


# =============================================================================
# DIALOG FOOTER
# =============================================================================


class DialogFooter(QFrame):
    """
    Standardized dialog footer with button row.

    Features:
    - Right-aligned buttons (standard Qt pattern)
    - Order: Cancel/Secondary (left) -> Primary (right)
    - ButtonRole-based styling (primary, secondary, destructive, cancel)
    - Uses PushButton from primitives v2

    Signals:
        primary_clicked: Emitted when primary button is clicked
        secondary_clicked: Emitted when secondary button is clicked
        cancel_clicked: Emitted when cancel button is clicked

    Example:
        footer = DialogFooter(
            primary_text="Save",
            cancel_text="Cancel",
            parent=dialog
        )
        footer.primary_clicked.connect(dialog.accept)
        footer.cancel_clicked.connect(dialog.reject)
    """

    primary_clicked = Signal()
    secondary_clicked = Signal()
    cancel_clicked = Signal()

    def __init__(
        self,
        primary_text: str = "OK",
        cancel_text: str = "Cancel",
        show_secondary: bool = False,
        secondary_text: str = "",
        destructive_primary: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize dialog footer.

        Args:
            primary_text: Text for primary button
            cancel_text: Text for cancel button
            show_secondary: Whether to show secondary button
            secondary_text: Text for secondary button
            destructive_primary: Whether primary button is destructive
            parent: Optional parent widget
        """
        super().__init__(parent)
        self._primary_text: str = primary_text
        self._cancel_text: str = cancel_text
        self._show_secondary: bool = show_secondary
        self._secondary_text: str = secondary_text or "Apply"
        self._destructive_primary: bool = destructive_primary

        self._primary_btn: PushButton | None = None
        self._secondary_btn: PushButton | None = None
        self._cancel_btn: PushButton | None = None

        self._setup_ui()
        self._apply_styles()

        logger.debug(f"{self.__class__.__name__} created")

    def _setup_ui(self) -> None:
        """Setup footer layout and buttons."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(
            TOKENS_V2.spacing.md,
            TOKENS_V2.spacing.sm,
            TOKENS_V2.spacing.md,
            TOKENS_V2.spacing.sm,
        )
        layout.setSpacing(TOKENS_V2.spacing.xs)

        # Left side spacer (pushes buttons to right)
        layout.addStretch()

        # Cancel button (left of primary)
        self._cancel_btn = PushButton(
            text=self._cancel_text,
            variant="secondary",
            size="md",
        )
        self._cancel_btn.setProperty("role", "cancel")
        self._cancel_btn.clicked.connect(self._on_cancel_clicked)
        layout.addWidget(self._cancel_btn)

        # Secondary button (optional)
        if self._show_secondary:
            self._secondary_btn = PushButton(
                text=self._secondary_text,
                variant="secondary",
                size="md",
            )
            self._secondary_btn.setProperty("role", "secondary")
            self._secondary_btn.clicked.connect(self._on_secondary_clicked)
            layout.addWidget(self._secondary_btn)

        # Primary button (rightmost)
        primary_variant = "danger" if self._destructive_primary else "primary"
        self._primary_btn = PushButton(
            text=self._primary_text,
            variant=primary_variant,
            size="md",
        )
        self._primary_btn.setProperty("role", "primary")
        self._primary_btn.clicked.connect(self._on_primary_clicked)
        layout.addWidget(self._primary_btn)

    def _apply_styles(self) -> None:
        """Apply footer styling using THEME_V2."""
        t = THEME_V2

        stylesheet = f"""
            DialogFooter {{
                background-color: {t.bg_surface};
                border-top: 1px solid {t.border};
            }}
        """
        self.setStyleSheet(stylesheet)

    @Slot()
    def _on_primary_clicked(self) -> None:
        """Handle primary button click."""
        self.primary_clicked.emit()

    @Slot()
    def _on_secondary_clicked(self) -> None:
        """Handle secondary button click."""
        self.secondary_clicked.emit()

    @Slot()
    def _on_cancel_clicked(self) -> None:
        """Handle cancel button click."""
        self.cancel_clicked.emit()

    # ========================================================================
    # PUBLIC API
    # ========================================================================

    def set_primary_enabled(self, enabled: bool) -> None:
        """
        Enable or disable primary button.

        Args:
            enabled: True to enable, False to disable
        """
        if self._primary_btn:
            self._primary_btn.setEnabled(enabled)

    def set_primary_text(self, text: str) -> None:
        """
        Update primary button text.

        Args:
            text: New button text
        """
        if self._primary_btn:
            self._primary_btn.setText(text)

    def set_cancel_text(self, text: str) -> None:
        """
        Update cancel button text.

        Args:
            text: New button text
        """
        if self._cancel_btn:
            self._cancel_btn.setText(text)

    def get_primary_button(self) -> PushButton | None:
        """Get reference to primary button."""
        return self._primary_btn

    def get_cancel_button(self) -> PushButton | None:
        """Get reference to cancel button."""
        return self._cancel_btn

    def get_secondary_button(self) -> PushButton | None:
        """Get reference to secondary button."""
        return self._secondary_btn


# =============================================================================
# DIALOG TITLE BAR
# =============================================================================


class DialogTitleBar(QFrame):
    """
    Optional draggable title bar for dialogs.

    Features:
    - Title label with heading style
    - Optional close button
    - Draggable to move the dialog

    Signals:
        close_requested: Emitted when close button is clicked

    Example:
        title_bar = DialogTitleBar(title="Settings", show_close=True)
        title_bar.close_requested.connect(dialog.close)
    """

    close_requested = Signal()

    def __init__(
        self,
        title: str = "",
        show_close: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize title bar.

        Args:
            title: Title text
            show_close: Whether to show close button
            parent: Optional parent widget
        """
        super().__init__(parent)

        self._title: str = title
        self._show_close: bool = show_close
        self._close_btn: QPushButton | None = None
        self._title_label: QLabel | None = None
        self._drag_pos: QPoint | None = None
        self._parent_dialog: QDialog | None = None

        self._setup_ui()
        self._apply_styles()

        logger.debug(f"{self.__class__.__name__} created: {title}")

    def _setup_ui(self) -> None:
        """Setup title bar layout."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(
            TOKENS_V2.spacing.md,
            TOKENS_V2.spacing.sm,
            TOKENS_V2.spacing.md,
            TOKENS_V2.spacing.sm,
        )
        layout.setSpacing(TOKENS_V2.spacing.xs)

        # Title label
        self._title_label = QLabel(self._title)
        layout.addWidget(self._title_label)

        layout.addStretch()

        # Close button (optional)
        if self._show_close:
            self._close_btn = QPushButton("×")
            self._close_btn.setFixedSize(24, 24)
            self._close_btn.setCursor(Qt.CursorShape.ArrowCursor)
            self._close_btn.clicked.connect(self._on_close_clicked)
            layout.addWidget(self._close_btn)

    def _apply_styles(self) -> None:
        """Apply title bar styling."""
        t = THEME_V2
        tok = TOKENS_V2

        self.setStyleSheet(f"""
            DialogTitleBar {{
                background-color: {t.bg_surface};
                border-bottom: 1px solid {t.border};
            }}
            QLabel {{
                color: {t.text_primary};
                font-family: {tok.typography.family};
                font-size: {tok.typography.heading_md}px;
                font-weight: {tok.typography.weight_semibold};
            }}
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: {tok.radius.xs}px;
                color: {t.text_secondary};
                font-size: 18px;
            }}
            QPushButton:hover {{
                background-color: {t.bg_hover};
                color: {t.text_primary};
            }}
            QPushButton:pressed {{
                background-color: {t.bg_selected};
            }}
        """)

    def set_parent_dialog(self, dialog: QDialog) -> None:
        """
        Set parent dialog for dragging.

        Args:
            dialog: Parent dialog to move when dragging
        """
        self._parent_dialog = dialog

    def set_title(self, title: str) -> None:
        """
        Update title text.

        Args:
            title: New title text
        """
        self._title = title
        if self._title_label:
            self._title_label.setText(title)

    @Slot()
    def _on_close_clicked(self) -> None:
        """Handle close button click."""
        self.close_requested.emit()

    # ========================================================================
    # DRAG HANDLING
    # ========================================================================

    @Slot()
    def mousePressEvent(self, event) -> None:
        """Start drag on left click."""
        if event.button() == Qt.MouseButton.LeftButton and self._parent_dialog:
            self._drag_pos = event.globalPos() - self._parent_dialog.pos()
            event.accept()
        else:
            super().mousePressEvent(event)

    @Slot()
    def mouseMoveEvent(self, event) -> None:
        """Move dialog while dragging."""
        if self._drag_pos is not None and self._parent_dialog:
            self._parent_dialog.move(event.globalPos() - self._drag_pos)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    @Slot()
    def mouseReleaseEvent(self, event) -> None:
        """End drag."""
        self._drag_pos = None
        super().mouseReleaseEvent(event)


# =============================================================================
# BASE DIALOG V2
# =============================================================================


class BaseDialogV2(QDialog):
    """
    Base class for v2 dialogs with standardized layout and behavior.

    Features:
    - Title bar (optional draggable)
    - Body content area with padding
    - Footer with standardized button row
    - Size presets (SM/MD/LG)
    - Keyboard shortcuts (Enter = primary, Esc = cancel)
    - Escape key handling from text widgets via eventFilter
    - Modal behavior
    - Full THEME_V2/TOKENS_V2 styling

    Layout:
        ┌─────────────────────────────────────┐
        │ Title Bar (optional)                │
        ├─────────────────────────────────────┤
        │                                     │
        │ Body Content                        │
        │ (scrollable if needed)              │
        │                                     │
        ├─────────────────────────────────────┤
        │              [Cancel] [Primary]     │
        └─────────────────────────────────────┘

    Signals:
        accepted: Emitted when dialog is accepted (primary action)
        rejected: Emitted when dialog is rejected (cancel/Esc)

    Example:
        class MyDialog(BaseDialogV2):
            def __init__(self, parent=None):
                super().__init__(
                    title="My Dialog",
                    parent=parent,
                    size=DialogSizeV2.MD,
                )

                # Set body content
                content = QWidget()
                layout = QVBoxLayout(content)
                layout.addWidget(QLabel("Enter your name:"))
                self._name_input = QLineEdit()
                layout.addWidget(self._name_input)
                self.set_body_widget(content)

                # Set buttons
                self.set_primary_button("Save", self._on_save)
                self.set_secondary_button("Cancel", self.reject)

            def _on_save(self):
                if self._name_input.text():
                    self.accept()
    """

    # Size specifications from TOKENS_V2
    _SIZES = {
        DialogSizeV2.SM: (
            TOKENS_V2.sizes.dialog_sm_width,
            TOKENS_V2.sizes.dialog_height_sm,
        ),
        DialogSizeV2.MD: (
            TOKENS_V2.sizes.dialog_md_width,
            TOKENS_V2.sizes.dialog_height_md,
        ),
        DialogSizeV2.LG: (
            TOKENS_V2.sizes.dialog_lg_width,
            TOKENS_V2.sizes.dialog_height_lg,
        ),
    }

    def __init__(
        self,
        title: str,
        parent: QWidget | None = None,
        size: DialogSizeV2 = DialogSizeV2.MD,
        resizable: bool = False,
        show_title_bar: bool = False,
        show_close: bool = False,
    ) -> None:
        """
        Initialize base dialog v2.

        Args:
            title: Dialog title text
            parent: Optional parent widget
            size: Dialog size preset (SM/MD/LG)
            resizable: Whether dialog is resizable by user
            show_title_bar: Whether to show title bar
            show_close: Whether to show close button in title bar
        """
        super().__init__(parent)

        self._dialog_title: str = title
        self._size: DialogSizeV2 = size
        self._resizable: bool = resizable
        self._show_title_bar: bool = show_title_bar
        self._show_close: bool = show_close

        # UI components
        self._title_bar: DialogTitleBar | None = None
        self._footer: DialogFooter | None = None
        self._body_widget: QWidget | None = None
        self._primary_button: QPushButton | None = None
        self._cancel_button: QPushButton | None = None

        # Text widgets for escape key filtering
        self._escape_filter_widgets: list[QWidget] = []

        self._setup_window()
        self._setup_ui()

        logger.debug(f"{self.__class__.__name__} created: title={title}, size={size}")

    def _setup_window(self) -> None:
        """Setup window flags and properties."""
        # Modal dialog
        self.setModal(True)

        # Set size
        width, height = self._SIZES[self._size]
        self.resize(width, height)

        # Minimum size
        self.setMinimumSize(
            TOKENS_V2.sizes.dialog_sm_width,
            TOKENS_V2.sizes.dialog_min_height,
        )

        # Resizable
        if not self._resizable:
            # Fixed size for non-resizable dialogs
            self.setSizeGripEnabled(False)

    def _setup_ui(self) -> None:
        """Setup dialog UI layout."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Container for rounded corners
        container = QFrame()
        container.setObjectName("dialogContainer")
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # Title bar (optional)
        if self._show_title_bar:
            self._title_bar = DialogTitleBar(
                title=self._dialog_title,
                show_close=self._show_close,
            )
            self._title_bar.set_parent_dialog(self)
            self._title_bar.close_requested.connect(self.close)
            container_layout.addWidget(self._title_bar)

        # Body area
        self._body_area = QFrame()
        self._body_area.setObjectName("dialogBody")
        body_layout = QVBoxLayout(self._body_area)
        body_layout.setContentsMargins(
            TOKENS_V2.spacing.md,
            TOKENS_V2.spacing.md,
            TOKENS_V2.spacing.md,
            TOKENS_V2.spacing.md,
        )
        container_layout.addWidget(self._body_area)

        # Add stretch to body for content
        body_layout.addStretch()

        # Footer
        self._footer = DialogFooter(parent=self)
        self._footer.primary_clicked.connect(self._on_primary_clicked)
        self._footer.cancel_clicked.connect(self._on_cancel_clicked)
        container_layout.addWidget(self._footer)

        main_layout.addWidget(container)

        # Apply styles
        self._apply_styles()

    def _apply_styles(self) -> None:
        """Apply dialog styling using THEME_V2."""
        t = THEME_V2
        tok = TOKENS_V2

        self.setStyleSheet(f"""
            BaseDialogV2 {{
                background-color: {t.bg_surface};
            }}
            QFrame#dialogContainer {{
                background-color: {t.bg_surface};
                border-radius: {tok.radius.lg}px;
            }}
            QFrame#dialogBody {{
                background-color: {t.bg_surface};
                border-radius: {tok.radius.lg}px;
            }}
        """)

    # ========================================================================
    # PUBLIC API
    # ========================================================================

    def set_body_widget(self, widget: QWidget) -> None:
        """
        Set the main body content widget.

        Args:
            widget: Content widget to display in body area
        """
        # Remove existing body widget
        if self._body_widget:
            self._body_area.layout().removeWidget(self._body_widget)
            self._body_widget.deleteLater()

        # Insert new widget before the stretch
        self._body_widget = widget
        layout = self._body_area.layout()
        layout.insertWidget(layout.count() - 1, widget)

        # Install escape key filter on text widgets
        self._install_escape_filter(widget)

    def set_title(self, title: str) -> None:
        """
        Update dialog title.

        Args:
            title: New title text
        """
        self._dialog_title = title
        if self._title_bar:
            self._title_bar.set_title(title)
        else:
            self.setWindowTitle(title)

    def set_primary_button(
        self,
        text: str,
        slot: Callable[[], None] | None = None,
    ) -> QPushButton:
        """
        Set primary button text and click handler.

        Args:
            text: Button text
            slot: Optional click handler (if None, defaults to accept)

        Returns:
            The primary button instance
        """
        if self._footer:
            self._footer.set_primary_text(text)
            self._primary_button = self._footer.get_primary_button()
            if slot is not None:
                # Disconnect default and connect custom handler
                try:
                    self._footer.primary_clicked.disconnect()
                except RuntimeError:
                    pass
                self._footer.primary_clicked.connect(slot)

        return self._primary_button

    def set_secondary_button(
        self,
        text: str,
        slot: Callable[[], None] | None = None,
    ) -> QPushButton:
        """
        Add or update secondary button.

        Args:
            text: Button text
            slot: Optional click handler

        Returns:
            The secondary button instance
        """
        # For now, update cancel button to act as secondary
        if self._footer:
            self._footer.set_cancel_text(text)
            self._cancel_button = self._footer.get_cancel_button()
            if slot is not None:
                try:
                    self._footer.cancel_clicked.disconnect()
                except RuntimeError:
                    pass
                self._footer.cancel_clicked.connect(slot)

        return self._cancel_button

    def set_footer_visible(self, visible: bool) -> None:
        """
        Show or hide footer.

        Args:
            visible: True to show, False to hide
        """
        if self._footer:
            self._footer.setVisible(visible)

    def validate(self) -> bool:
        """
        Override in subclasses to validate dialog state.

        Returns:
            True if valid, False otherwise
        """
        return True

    def set_validation_error(self, message: str) -> None:
        """
        Display validation error message.

        Args:
            message: Error message to display
        """
        # Default implementation: log warning
        logger.warning(f"Validation error: {message}")

    # ========================================================================
    # EVENT HANDLERS
    # ========================================================================

    @Slot()
    def _on_primary_clicked(self) -> None:
        """Handle primary button click."""
        if self.validate():
            self.accept()

    @Slot()
    def _on_cancel_clicked(self) -> None:
        """Handle cancel button click."""
        self.reject()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """
        Handle key press events.

        - Enter: Trigger primary button (skip if text input focused)
        - Escape: Reject dialog

        Args:
            event: Key event
        """
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
            event.accept()
            return

        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            # Check if focused widget is a text input
            focused = QApplication.focusWidget()
            if focused is None or not isinstance(
                focused,
                QLineEdit | QTextEdit,
            ):
                # Not in text input, trigger primary button
                if self._primary_button and self._primary_button.isEnabled():
                    self._primary_button.click()
                    event.accept()
                    return

        super().keyPressEvent(event)

    def eventFilter(self, obj, event) -> bool:
        """
        Event filter to catch Escape key from child text widgets.

        Args:
            obj: The object receiving the event
            event: The event

        Returns:
            False to let event propagate, True to consume
        """
        if event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key.Key_Escape:
                self.reject()
                return True
        return False

    def _install_escape_filter(self, widget: QWidget) -> None:
        """
        Install event filter on widget for Escape key handling.

        Args:
            widget: Widget to install filter on
        """
        if widget in self._escape_filter_widgets:
            return

        widget.installEventFilter(self)
        self._escape_filter_widgets.append(widget)

        # Also install on viewport for scroll-based widgets
        if hasattr(widget, "viewport"):
            widget.viewport().installEventFilter(self)

        # Recursively install on children
        for child in widget.findChildren(QWidget):
            if child not in self._escape_filter_widgets:
                child.installEventFilter(self)
                self._escape_filter_widgets.append(child)
                if hasattr(child, "viewport"):
                    child.viewport().installEventFilter(self)

    def showEvent(self, event) -> None:
        """Handle show event - bring to front."""
        super().showEvent(event)
        self.activateWindow()
        self.raise_()

    def closeEvent(self, event) -> None:
        """Handle close event - cleanup event filters."""
        # Remove event filters
        for widget in self._escape_filter_widgets:
            try:
                widget.removeEventFilter(self)
                if hasattr(widget, "viewport"):
                    widget.viewport().removeEventFilter(self)
            except RuntimeError:
                pass
        self._escape_filter_widgets.clear()

        super().closeEvent(event)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "BaseDialogV2",
    "ButtonRole",
    "DialogFooter",
    "DialogSizeV2",
    "DialogTitleBar",
]
