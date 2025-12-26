"""
Expression Editor Popup for CasareRPA.

Provides a popup window for detailed expression editing with syntax highlighting,
variable insertion, and context-aware editing modes.

Design follows node_output_popup.py pattern:
- Tool-style frameless window with shadow
- Draggable header
- Corner resize handles
- Fade-in animation (150ms)
- Keyboard shortcuts (Escape to cancel, Ctrl+Enter to accept)

Features:
- Code editing with syntax highlighting
- Variable insertion via {{}} syntax
- Multiple editor modes (Python, JavaScript, CMD, Markdown, Rich Text)
"""

from loguru import logger
from PySide6.QtCore import (
    QEasingCurve,
    QEvent,
    QObject,
    QPoint,
    QPropertyAnimation,
    Qt,
    Signal,
    Slot,
)
from PySide6.QtGui import QColor, QFont, QKeyEvent
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.managers.popup_manager import PopupManager
from casare_rpa.presentation.canvas.ui.theme import THEME
from casare_rpa.presentation.canvas.ui.widgets.expression_editor.base_editor import (
    BaseExpressionEditor,
    EditorType,
)


class PopupColors:
    """Color constants for the expression editor popup using THEME."""

    BACKGROUND = QColor(THEME.bg_dark)
    HEADER_BG = QColor(THEME.bg_medium)
    BORDER = QColor(THEME.border)
    TEXT = QColor(THEME.text_primary)
    TEXT_SECONDARY = QColor(THEME.text_secondary)
    ACCENT = QColor(THEME.accent)
    ACCENT_HOVER = QColor(THEME.accent_hover)
    SUCCESS = QColor(THEME.success)
    ERROR = QColor(THEME.error)
    TABLE_HOVER = QColor(THEME.hover)
    TABLE_SELECTED = QColor(THEME.selected)


class DraggableHeader(QFrame):
    """
    Header that supports dragging to move the parent window.

    Provides move cursor and drag-to-move functionality.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize draggable header."""
        super().__init__(parent)
        self._drag_pos: QPoint | None = None
        self._parent_window: QWidget | None = None
        self.setCursor(Qt.CursorShape.SizeAllCursor)

    def set_parent_window(self, window: QWidget) -> None:
        """
        Set the window to be moved when dragging.

        Args:
            window: The window widget to move
        """
        self._parent_window = window

    def mousePressEvent(self, event) -> None:
        """Start drag on left click."""
        if event.button() == Qt.MouseButton.LeftButton and self._parent_window:
            self._drag_pos = event.globalPos() - self._parent_window.pos()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        """Move window while dragging."""
        if self._drag_pos is not None and self._parent_window:
            self._parent_window.move(event.globalPos() - self._drag_pos)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        """End drag."""
        self._drag_pos = None
        super().mouseReleaseEvent(event)


class HeaderButton(QPushButton):
    """Compact icon button for popup header."""

    def __init__(self, text: str, tooltip: str, parent: QWidget | None = None) -> None:
        """
        Initialize header button.

        Args:
            text: Button text (usually an icon character)
            tooltip: Tooltip text
            parent: Optional parent widget
        """
        super().__init__(text, parent)
        self.setFixedSize(24, 24)
        self.setToolTip(tooltip)
        self.setFont(QFont("Segoe UI Symbol", 12))
        self.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: 4px;
                color: {PopupColors.TEXT_SECONDARY.name()};
            }}
            QPushButton:hover {{
                background-color: {PopupColors.TABLE_HOVER.name()};
                color: {PopupColors.TEXT.name()};
            }}
            QPushButton:pressed {{
                background-color: {PopupColors.TABLE_SELECTED.name()};
            }}
        """)


class ExpressionEditorPopup(QFrame):
    """
    Popup window for expression editing.

    Provides a modal-like editor popup with:
    - Draggable header with title and mode label
    - Editor content area (injected via set_editor)
    - Accept/Cancel buttons
    - Corner resize handles
    - Fade-in animation

    Signals:
        accepted: Emitted when user confirms changes (str: value)
        cancelled: Emitted when user cancels
        value_changed: Emitted on any content change (str: value)
    """

    accepted = Signal(str)
    cancelled = Signal()
    value_changed = Signal(str)

    DEFAULT_WIDTH = 600
    DEFAULT_HEIGHT = 400
    MIN_WIDTH = 400
    MIN_HEIGHT = 250
    RESIZE_MARGIN = 8

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the expression editor popup."""
        super().__init__(parent)

        self._editor: BaseExpressionEditor | None = None
        self._editor_type: EditorType = EditorType.CODE_PYTHON
        self._initial_value: str = ""

        # Resize state
        self._resize_edge: str | None = None
        self._resize_start_pos: QPoint | None = None
        self._resize_start_geometry = None

        # Enable mouse tracking for cursor changes
        self.setMouseTracking(True)

        # Window setup - Tool window frameless
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, False)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.resize(self.DEFAULT_WIDTH, self.DEFAULT_HEIGHT)
        self.setMinimumSize(self.MIN_WIDTH, self.MIN_HEIGHT)

        # Drop shadow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 100))
        self.setGraphicsEffect(shadow)

        # Setup UI
        self._setup_ui()
        self._apply_styles()

        # Animation
        self._animation: QPropertyAnimation | None = None

        logger.debug("ExpressionEditorPopup initialized")

    def _setup_ui(self) -> None:
        """Setup the popup UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(1, 1, 1, 1)
        main_layout.setSpacing(0)

        # Container for rounded corners
        container = QFrame()
        container.setObjectName("popupContainer")
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # Header
        header = self._create_header()
        container_layout.addWidget(header)

        # Editor container (editor injected later)
        self._editor_container = QFrame()
        self._editor_container.setObjectName("editorContainer")
        self._editor_layout = QVBoxLayout(self._editor_container)
        self._editor_layout.setContentsMargins(0, 0, 0, 0)
        self._editor_layout.setSpacing(0)
        container_layout.addWidget(self._editor_container, 1)

        # Footer with buttons
        footer = self._create_footer()
        container_layout.addWidget(footer)

        main_layout.addWidget(container)

    def _create_header(self) -> DraggableHeader:
        """Create draggable header with title and controls."""
        header = DraggableHeader()
        header.set_parent_window(self)
        header.setObjectName("header")
        header.setFixedHeight(38)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(10, 0, 6, 0)
        layout.setSpacing(4)

        # Title
        self._title_label = QLabel("Expression Editor")
        self._title_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self._title_label.setStyleSheet(f"color: {PopupColors.TEXT.name()};")
        layout.addWidget(self._title_label)

        # Mode label (shows editor type)
        self._mode_label = QLabel("")
        self._mode_label.setFont(QFont("Consolas", 9))
        self._mode_label.setStyleSheet(f"""
            color: {PopupColors.TEXT_SECONDARY.name()};
            background-color: {THEME.bg_darkest};
            border-radius: 3px;
            padding: 2px 6px;
        """)
        layout.addWidget(self._mode_label)

        layout.addStretch()

        # Close button
        self._close_btn = HeaderButton("\u00d7", "Cancel (Escape)")
        self._close_btn.clicked.connect(self._on_cancel)
        layout.addWidget(self._close_btn)

        return header

    def _create_footer(self) -> QFrame:
        """Create footer with accept/cancel buttons."""
        footer = QFrame()
        footer.setObjectName("footer")
        footer.setFixedHeight(50)

        layout = QHBoxLayout(footer)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        # Keyboard hint
        hint_label = QLabel("Ctrl+Enter to accept")
        hint_label.setStyleSheet(f"""
            color: {PopupColors.TEXT_SECONDARY.name()};
            font-size: 10px;
        """)
        layout.addWidget(hint_label)

        layout.addStretch()

        # Cancel button
        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.setFixedHeight(28)
        self._cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME.bg_medium};
                border: 1px solid {THEME.border};
                border-radius: 4px;
                padding: 0 16px;
                color: {THEME.text_primary};
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {THEME.hover};
                border-color: {THEME.border_light};
            }}
        """)
        self._cancel_btn.clicked.connect(self._on_cancel)
        layout.addWidget(self._cancel_btn)

        # Accept button
        self._accept_btn = QPushButton("Accept")
        self._accept_btn.setFixedHeight(28)
        self._accept_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME.accent};
                border: 1px solid {THEME.accent};
                border-radius: 4px;
                padding: 0 16px;
                color: white;
                font-size: 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {THEME.accent_hover};
            }}
        """)
        self._accept_btn.clicked.connect(self._on_accept)
        layout.addWidget(self._accept_btn)

        return footer

    def _apply_styles(self) -> None:
        """Apply dark theme styling."""
        self.setStyleSheet(f"""
            QFrame#popupContainer {{
                background-color: {PopupColors.BACKGROUND.name()};
                border: 1px solid {PopupColors.BORDER.name()};
                border-radius: 8px;
            }}
            QFrame#header {{
                background-color: {PopupColors.HEADER_BG.name()};
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                border-bottom: 1px solid {PopupColors.BORDER.name()};
            }}
            QFrame#editorContainer {{
                background-color: {THEME.bg_darkest};
            }}
            QFrame#footer {{
                background-color: {PopupColors.HEADER_BG.name()};
                border-top: 1px solid {PopupColors.BORDER.name()};
                border-bottom-left-radius: 8px;
                border-bottom-right-radius: 8px;
            }}
        """)

    def set_editor(self, editor: BaseExpressionEditor) -> None:
        """
        Set the editor widget to display.

        Args:
            editor: The editor widget to show in the popup
        """
        # Remove old editor if any
        if self._editor is not None:
            self._editor_layout.removeWidget(self._editor)
            self._editor.value_changed.disconnect(self._on_editor_value_changed)
            self._editor.removeEventFilter(self)  # Remove old event filter
            # QTextEdit-based widgets use viewport for event handling
            if hasattr(self._editor, "viewport"):
                self._editor.viewport().removeEventFilter(self)
            self._editor.setParent(None)

        self._editor = editor
        self._editor_layout.addWidget(editor)
        editor.value_changed.connect(self._on_editor_value_changed)
        # Install event filter to catch Escape key in editor
        editor.installEventFilter(self)
        # QTextEdit-based widgets handle key events through viewport
        if hasattr(editor, "viewport"):
            editor.viewport().installEventFilter(self)

        # Update mode label
        if editor.editor_type:
            self._mode_label.setText(editor.editor_type.value.upper())
            self._mode_label.setVisible(True)
        else:
            self._mode_label.setVisible(False)

    def set_title(self, title: str) -> None:
        """
        Set the popup title.

        Args:
            title: Title text to display
        """
        self._title_label.setText(title)

    def get_value(self) -> str:
        """
        Get the current editor value.

        Returns:
            Current text content
        """
        if self._editor:
            return self._editor.get_value()
        return ""

    def set_value(self, value: str) -> None:
        """
        Set the editor value.

        Args:
            value: Text to set
        """
        self._initial_value = value
        if self._editor:
            self._editor.set_value(value)

    def show_for_widget(
        self,
        widget: QWidget,
        editor_type: EditorType,
        initial_value: str,
        title: str = "Expression Editor",
    ) -> None:
        """
        Show the popup positioned near a widget.

        Args:
            widget: Widget to position near
            editor_type: Type of editor to use
            initial_value: Initial text value
            title: Popup title
        """
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.editor_factory import (
            EditorFactory,
        )

        # Create and set editor
        editor = EditorFactory.create(editor_type)
        self.set_editor(editor)

        # Set initial value and title
        self.set_value(initial_value)
        self.set_title(title)

        # Position near widget
        global_pos = widget.mapToGlobal(widget.rect().bottomLeft())
        self.show_at_position(QPoint(global_pos.x(), global_pos.y() + 5))

        # Focus the editor
        if self._editor:
            self._editor.set_focus()

    def show_at_position(self, pos: QPoint) -> None:
        """
        Show the popup at the specified position.

        Adjusts position to stay within screen bounds.

        Args:
            pos: Global position to show at
        """
        screen = QApplication.primaryScreen().availableGeometry()

        x = pos.x()
        y = pos.y()

        if x + self.width() > screen.right():
            x = screen.right() - self.width() - 10
        if y + self.height() > screen.bottom():
            y = screen.bottom() - self.height() - 10
        if x < screen.left():
            x = screen.left() + 10
        if y < screen.top():
            y = screen.top() + 10

        self.move(x, y)
        self.show()
        self._animate_fade_in()
        # Register with PopupManager for click-outside-to-close handling
        PopupManager.register(self)
        # Activate window and set focus to ensure key events work
        self.activateWindow()
        self.raise_()
        if self._editor:
            self._editor.set_focus()

    def _animate_fade_in(self) -> None:
        """Animate popup fade-in."""
        self.setWindowOpacity(0.0)

        self._animation = QPropertyAnimation(self, b"windowOpacity")
        self._animation.setDuration(150)
        self._animation.setStartValue(0.0)
        self._animation.setEndValue(1.0)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._animation.start()

    @Slot()
    def _on_editor_value_changed(self, value: str) -> None:
        """Handle editor content change."""
        self.value_changed.emit(value)

    @Slot()
    def _on_accept(self) -> None:
        """Handle accept button click."""
        value = self.get_value()
        logger.debug(f"ExpressionEditorPopup accepted with value length: {len(value)}")
        self.accepted.emit(value)
        self.close()

    @Slot()
    def _on_cancel(self) -> None:
        """Handle cancel button click."""
        logger.debug("ExpressionEditorPopup cancelled")
        self.cancelled.emit()
        self.close()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle key press events."""
        # Escape closes popup (cancel)
        if event.key() == Qt.Key.Key_Escape:
            self._on_cancel()
            event.accept()
            return

        # Ctrl+Enter accepts
        if (
            event.modifiers() == Qt.KeyboardModifier.ControlModifier
            and event.key() == Qt.Key.Key_Return
        ):
            self._on_accept()
            event.accept()
            return

        super().keyPressEvent(event)

    # =========================================================================
    # RESIZE HANDLING (same pattern as NodeOutputPopup)
    # =========================================================================

    def _get_resize_edge(self, pos: QPoint) -> str | None:
        """Determine which corner the mouse is near for resizing."""
        m = self.RESIZE_MARGIN
        rect = self.rect()
        x, y = pos.x(), pos.y()
        w, h = rect.width(), rect.height()

        left = x < m
        right = x > w - m
        top = y < m
        bottom = y > h - m

        if top and left:
            return "top-left"
        elif top and right:
            return "top-right"
        elif bottom and left:
            return "bottom-left"
        elif bottom and right:
            return "bottom-right"
        return None

    def _update_cursor_for_edge(self, edge: str | None) -> None:
        """Update cursor based on resize corner."""
        if edge in ("top-left", "bottom-right"):
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        elif edge in ("top-right", "bottom-left"):
            self.setCursor(Qt.CursorShape.SizeBDiagCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def mousePressEvent(self, event) -> None:
        """Start resize on edge click."""
        if event.button() == Qt.MouseButton.LeftButton:
            edge = self._get_resize_edge(event.pos())
            if edge:
                self._resize_edge = edge
                self._resize_start_pos = event.globalPos()
                self._resize_start_geometry = self.geometry()
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        """Handle resize drag or update cursor."""
        if self._resize_edge and self._resize_start_pos:
            delta = event.globalPos() - self._resize_start_pos
            geo = self._resize_start_geometry
            new_geo = geo.__class__(geo)

            edge = self._resize_edge
            if "left" in edge:
                new_geo.setLeft(geo.left() + delta.x())
            if "right" in edge:
                new_geo.setRight(geo.right() + delta.x())
            if "top" in edge:
                new_geo.setTop(geo.top() + delta.y())
            if "bottom" in edge:
                new_geo.setBottom(geo.bottom() + delta.y())

            if new_geo.width() >= self.MIN_WIDTH and new_geo.height() >= self.MIN_HEIGHT:
                try:
                    screen = QApplication.primaryScreen()
                    if screen is not None:
                        avail = screen.availableGeometry()
                        if new_geo.left() < avail.left():
                            new_geo.moveLeft(avail.left())
                        if new_geo.top() < avail.top():
                            new_geo.moveTop(avail.top())
                        if new_geo.right() > avail.right():
                            new_geo.setRight(avail.right())
                        if new_geo.bottom() > avail.bottom():
                            new_geo.setBottom(avail.bottom())
                except Exception:
                    pass

                self.setGeometry(new_geo)
            event.accept()
        else:
            edge = self._get_resize_edge(event.pos())
            self._update_cursor_for_edge(edge)
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        """End resize."""
        self._resize_edge = None
        self._resize_start_pos = None
        self._resize_start_geometry = None
        self.setCursor(Qt.CursorShape.ArrowCursor)
        super().mouseReleaseEvent(event)

    def closeEvent(self, event) -> None:
        """Handle close event."""
        # Unregister from PopupManager
        PopupManager.unregister(self)
        # Clean up event filters from editor
        if self._editor is not None:
            self._editor.removeEventFilter(self)
            if hasattr(self._editor, "viewport"):
                self._editor.viewport().removeEventFilter(self)
        self._resize_edge = None
        self._resize_start_pos = None
        self._resize_start_geometry = None
        super().closeEvent(event)

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """
        Event filter to catch Escape key from editor widget.

        Args:
            obj: The object receiving the event
            event: The event

        Returns:
            False to let event propagate
        """
        # Catch Escape key from editor to close popup
        # Check both KeyPress and ShortcutOverride (text editors consume Escape)
        if event.type() in (QEvent.Type.KeyPress, QEvent.Type.ShortcutOverride):
            key_event = event
            if hasattr(key_event, "key") and key_event.key() == Qt.Key.Key_Escape:
                self._on_cancel()
                return True  # Consume the event

        return False  # Don't consume other events
