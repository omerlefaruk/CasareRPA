"""
Toolbar Widget for Element Selector Dialog.

Contains Pick/Stop buttons, mode selection, settings, and history dropdown.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QToolButton,
    QWidget)

from casare_rpa.presentation.canvas.selectors.state.selector_state import PickingMode


class ModeButton(QToolButton):
    """
    Styled toolbar button for mode selection.

    Visual states:
    - Default: Dark background, muted text
    - Hover: Lighter background, brighter text
    - Checked: Blue accent background, white text
    """

    def __init__(
        self,
        icon_text: str,
        tooltip: str,
        parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setText(icon_text)
        self.setToolTip(tooltip)
        self.setCheckable(True)
        self.setFixedSize(40, 40)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self.setStyleSheet("""
            QToolButton {
                background: #2a2a2a;
                border: 1px solid #3a3a3a;
                border-radius: 6px;
                font-size: 16px;
                color: #888888;
            }
            QToolButton:hover {
                background: #333333;
                border-color: #4a4a4a;
                color: #e0e0e0;
            }
            QToolButton:checked {
                background: #3b82f6;
                border-color: #2563eb;
                color: white;
            }
            QToolButton:disabled {
                background: #1a1a1a;
                color: #555555;
            }
        """)


class ToolbarWidget(QWidget):
    """
    Top toolbar for Element Selector Dialog.

    Layout:
    [Pick Element][Stop] | [Auto v][Browser][Desktop][OCR][Image] | [Settings][History]

    Signals:
        pick_requested: User clicked Pick Element button
        stop_requested: User clicked Stop button
        mode_changed: User selected different mode
        settings_requested: User clicked settings
        history_selected: User selected from history (selector string)
    """

    pick_requested = Signal()
    stop_requested = Signal()
    mode_changed = Signal(PickingMode)
    settings_requested = Signal()
    history_selected = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._is_picking = False
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Build toolbar UI."""
        self.setFixedHeight(56)
        self.setStyleSheet("""
            QWidget {
                background: #252525;
                border-bottom: 1px solid #3a3a3a;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        # Pick Element button (primary action)
        self._pick_btn = QPushButton("Pick Element")
        self._pick_btn.setFixedHeight(40)
        self._pick_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._pick_btn.clicked.connect(self._on_pick_clicked)
        self._pick_btn.setStyleSheet("""
            QPushButton {
                background: #3b82f6;
                border: 1px solid #2563eb;
                border-radius: 6px;
                padding: 8px 20px;
                color: white;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background: #2563eb;
            }
            QPushButton:pressed {
                background: #1d4ed8;
            }
            QPushButton:disabled {
                background: #1e3a5f;
                border-color: #1e3a5f;
                color: #888;
            }
        """)
        layout.addWidget(self._pick_btn)

        # Stop button (shown during picking)
        self._stop_btn = QPushButton("Stop")
        self._stop_btn.setFixedHeight(40)
        self._stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._stop_btn.clicked.connect(self._on_stop_clicked)
        self._stop_btn.setVisible(False)
        self._stop_btn.setStyleSheet("""
            QPushButton {
                background: #ef4444;
                border: 1px solid #dc2626;
                border-radius: 6px;
                padding: 8px 16px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #dc2626;
            }
        """)
        layout.addWidget(self._stop_btn)

        layout.addSpacing(12)

        # Mode dropdown
        self._mode_combo = QComboBox()
        self._mode_combo.addItem("Auto", PickingMode.AUTO)
        self._mode_combo.addItem("Browser", PickingMode.BROWSER)
        self._mode_combo.addItem("Desktop", PickingMode.DESKTOP)
        self._mode_combo.addItem("OCR", PickingMode.OCR)
        self._mode_combo.addItem("Image", PickingMode.IMAGE)
        self._mode_combo.setFixedHeight(36)
        self._mode_combo.setMinimumWidth(100)
        self._mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        self._mode_combo.setStyleSheet("""
            QComboBox {
                background: #3a3a3a;
                border: 1px solid #4a4a4a;
                border-radius: 4px;
                padding: 6px 28px 6px 12px;
                color: #e0e0e0;
                font-size: 12px;
            }
            QComboBox::drop-down {
                border: none;
                width: 24px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #888;
                margin-right: 8px;
            }
            QComboBox QAbstractItemView {
                background: #2a2a2a;
                border: 1px solid #4a4a4a;
                selection-background-color: #3b82f6;
                color: #e0e0e0;
            }
        """)
        layout.addWidget(self._mode_combo)

        # Mode quick-access buttons
        self._mode_group = QButtonGroup(self)
        self._mode_group.setExclusive(True)

        self._browser_btn = ModeButton("G", "Browser mode (Ctrl+B)")
        self._mode_group.addButton(self._browser_btn, PickingMode.BROWSER.value)
        layout.addWidget(self._browser_btn)

        self._desktop_btn = ModeButton("D", "Desktop mode (Ctrl+D)")
        self._mode_group.addButton(self._desktop_btn, PickingMode.DESKTOP.value)
        layout.addWidget(self._desktop_btn)

        self._ocr_btn = ModeButton("T", "OCR mode (Ctrl+T)")
        self._mode_group.addButton(self._ocr_btn, PickingMode.OCR.value)
        layout.addWidget(self._ocr_btn)

        self._image_btn = ModeButton("I", "Image mode (Ctrl+I)")
        self._mode_group.addButton(self._image_btn, PickingMode.IMAGE.value)
        layout.addWidget(self._image_btn)

        self._mode_group.idClicked.connect(self._on_mode_button_clicked)

        layout.addStretch()

        # Settings button
        self._settings_btn = QToolButton()
        self._settings_btn.setText("S")
        self._settings_btn.setToolTip("Settings")
        self._settings_btn.setFixedSize(36, 36)
        self._settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._settings_btn.clicked.connect(self.settings_requested.emit)
        self._settings_btn.setStyleSheet("""
            QToolButton {
                background: #2a2a2a;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                color: #888;
                font-size: 14px;
            }
            QToolButton:hover {
                background: #3a3a3a;
                color: #e0e0e0;
            }
        """)
        layout.addWidget(self._settings_btn)

        # History button with dropdown
        self._history_btn = QToolButton()
        self._history_btn.setText("H")
        self._history_btn.setToolTip("History (recent selectors)")
        self._history_btn.setFixedSize(36, 36)
        self._history_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._history_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self._history_btn.setStyleSheet("""
            QToolButton {
                background: #2a2a2a;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                color: #888;
                font-size: 14px;
            }
            QToolButton:hover {
                background: #3a3a3a;
                color: #e0e0e0;
            }
            QToolButton::menu-indicator {
                image: none;
            }
        """)
        self._history_menu = QMenu(self._history_btn)
        self._history_menu.setStyleSheet("""
            QMenu {
                background: #2a2a2a;
                border: 1px solid #4a4a4a;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 12px;
                color: #e0e0e0;
                font-family: Consolas, monospace;
                font-size: 11px;
            }
            QMenu::item:selected {
                background: #3b82f6;
            }
        """)
        self._history_btn.setMenu(self._history_menu)
        self._update_history_menu([])
        layout.addWidget(self._history_btn)

        # Status label
        self._status_label = QLabel("Ready")
        self._status_label.setStyleSheet("color: #888; font-size: 11px; margin-left: 8px;")
        layout.addWidget(self._status_label)

    def _on_pick_clicked(self) -> None:
        """Handle pick button click."""
        self.pick_requested.emit()

    def _on_stop_clicked(self) -> None:
        """Handle stop button click."""
        self.stop_requested.emit()

    def _on_mode_changed(self, index: int) -> None:
        """Handle mode dropdown change."""
        mode = self._mode_combo.currentData()
        if mode:
            self.mode_changed.emit(mode)
            # Update mode buttons to match
            self._update_mode_buttons(mode)

    def _on_mode_button_clicked(self, button_id: int) -> None:
        """Handle mode button click."""
        try:
            mode = PickingMode(button_id)
            # Update dropdown to match
            for i in range(self._mode_combo.count()):
                if self._mode_combo.itemData(i) == mode:
                    self._mode_combo.blockSignals(True)
                    self._mode_combo.setCurrentIndex(i)
                    self._mode_combo.blockSignals(False)
                    break
            self.mode_changed.emit(mode)
        except ValueError:
            pass

    def _update_mode_buttons(self, mode: PickingMode) -> None:
        """Update mode buttons to reflect current mode."""
        # Only check specific mode buttons, not auto
        if mode == PickingMode.BROWSER:
            self._browser_btn.setChecked(True)
        elif mode == PickingMode.DESKTOP:
            self._desktop_btn.setChecked(True)
        elif mode == PickingMode.OCR:
            self._ocr_btn.setChecked(True)
        elif mode == PickingMode.IMAGE:
            self._image_btn.setChecked(True)
        else:
            # Auto mode - uncheck all
            self._mode_group.setExclusive(False)
            self._browser_btn.setChecked(False)
            self._desktop_btn.setChecked(False)
            self._ocr_btn.setChecked(False)
            self._image_btn.setChecked(False)
            self._mode_group.setExclusive(True)

    def _update_history_menu(self, history: list[str]) -> None:
        """Update history dropdown menu."""
        self._history_menu.clear()

        if not history:
            action = self._history_menu.addAction("(no recent selectors)")
            action.setEnabled(False)
            return

        for selector in history[:10]:
            # Truncate long selectors
            display = selector[:50] + "..." if len(selector) > 50 else selector
            action = self._history_menu.addAction(display)
            action.setData(selector)
            action.triggered.connect(lambda checked, s=selector: self.history_selected.emit(s))

    # Public API

    def set_picking(self, is_picking: bool) -> None:
        """Update UI for picking state."""
        self._is_picking = is_picking
        self._pick_btn.setVisible(not is_picking)
        self._stop_btn.setVisible(is_picking)
        self._mode_combo.setEnabled(not is_picking)

        # Disable mode buttons during picking
        self._browser_btn.setEnabled(not is_picking)
        self._desktop_btn.setEnabled(not is_picking)
        self._ocr_btn.setEnabled(not is_picking)
        self._image_btn.setEnabled(not is_picking)

    def set_mode(self, mode: PickingMode) -> None:
        """Set current mode."""
        for i in range(self._mode_combo.count()):
            if self._mode_combo.itemData(i) == mode:
                self._mode_combo.setCurrentIndex(i)
                break
        self._update_mode_buttons(mode)

    def set_status(self, message: str, color: str = "#888") -> None:
        """Set status message."""
        self._status_label.setText(message)
        self._status_label.setStyleSheet(f"color: {color}; font-size: 11px; margin-left: 8px;")

    def set_history(self, history: list[str]) -> None:
        """Update history dropdown."""
        self._update_history_menu(history)

    def get_mode(self) -> PickingMode:
        """Get current mode."""
        return self._mode_combo.currentData() or PickingMode.AUTO


__all__ = ["ToolbarWidget", "ModeButton"]
