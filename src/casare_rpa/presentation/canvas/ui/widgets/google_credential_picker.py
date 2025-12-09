"""
Google Credential Picker Widget for CasareRPA.

Dropdown widget for selecting Google OAuth credentials:
- Shows only Google credentials (filtered)
- Auto-selects first credential if only one exists
- "Add Google Account..." option opens OAuth dialog
- Refresh button to reload credentials

Follows the pattern from variable_picker.py.
"""

from __future__ import annotations

from typing import Optional, List, Tuple

from PySide6.QtCore import Qt, Signal, QEvent
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QComboBox,
    QPushButton,
    QLabel,
)

from loguru import logger

from casare_rpa.presentation.canvas.theme import THEME


class GraphicsSceneComboBox(QComboBox):
    """
    QComboBox subclass that works reliably in QGraphicsProxyWidget.

    Ensures popup window flags are set correctly when shown in graphics scenes.
    """

    def showPopup(self):
        """Override to ensure popup appears on top in graphics scene."""
        try:
            popup = self.view().window()
            popup.setWindowFlags(
                Qt.WindowType.Popup
                | Qt.WindowType.FramelessWindowHint
                | Qt.WindowType.WindowStaysOnTopHint
            )
        except Exception:
            pass
        super().showPopup()


# Styles using THEME constants
PICKER_STYLE = f"""
QComboBox {{
    background: {THEME.bg_light};
    border: 1px solid {THEME.border_light};
    border-radius: 4px;
    padding: 4px 8px;
    padding-right: 24px;
    color: {THEME.text_secondary};
    min-width: 140px;
    min-height: 24px;
}}
QComboBox:hover {{
    border-color: {THEME.accent_primary};
    background: {THEME.bg_hover};
}}
QComboBox:focus {{
    border-color: {THEME.accent_primary};
}}
QComboBox:disabled {{
    background: {THEME.bg_dark};
    color: {THEME.text_disabled};
}}
QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: center right;
    width: 20px;
    border-left: none;
    background: transparent;
}}
QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {THEME.text_secondary};
    margin-right: 4px;
}}
QComboBox::down-arrow:hover {{
    border-top-color: {THEME.text_primary};
}}
QComboBox QAbstractItemView {{
    background: {THEME.bg_dark};
    border: 1px solid {THEME.border};
    selection-background-color: {THEME.accent_secondary};
    outline: none;
    padding: 2px;
}}
QComboBox QAbstractItemView::item {{
    padding: 6px 8px;
    min-height: 22px;
}}
QComboBox QAbstractItemView::item:hover {{
    background: {THEME.bg_hover};
}}
QComboBox QAbstractItemView::item:selected {{
    background: {THEME.accent_secondary};
}}
"""

BUTTON_STYLE = f"""
QPushButton {{
    background: {THEME.bg_light};
    border: 1px solid {THEME.border_light};
    border-radius: 4px;
    padding: 0px;
    color: {THEME.text_secondary};
    font-size: 16px;
    font-weight: bold;
    min-width: 26px;
    min-height: 26px;
}}
QPushButton:hover {{
    background: {THEME.bg_hover};
    border-color: {THEME.accent_primary};
    color: {THEME.text_primary};
}}
QPushButton:pressed {{
    background: {THEME.bg_dark};
}}
QPushButton:disabled {{
    background: {THEME.bg_dark};
    color: {THEME.text_disabled};
}}
"""

ADD_ACCOUNT_ID = "__add_account__"


class GoogleCredentialPicker(QWidget):
    """
    Dropdown widget for selecting Google OAuth credentials.

    Features:
    - Shows only Google credentials (filtered by category)
    - Auto-selects first credential if only one exists
    - "Add Google Account..." option at bottom opens OAuth dialog
    - Refresh button to reload credentials
    - Displays user email when available
    - Optional filtering by required scopes

    Signals:
        credential_changed(str): Emitted when selection changes, passes credential_id
    """

    credential_changed = Signal(str)

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        required_scopes: Optional[List[str]] = None,
    ) -> None:
        super().__init__(parent)

        self._current_credential_id: Optional[str] = None
        self._credentials: List[Tuple[str, str]] = []  # [(id, display_name), ...]
        self._required_scopes: List[str] = required_scopes or []

        self._setup_ui()
        self._apply_styles()
        self._connect_signals()
        self._refresh_credentials()

    def _setup_ui(self) -> None:
        """Set up the widget layout."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # Credential dropdown - using GraphicsSceneComboBox for proper event handling
        self._combo = GraphicsSceneComboBox()
        self._combo.setMinimumWidth(140)
        self._combo.setMinimumHeight(26)
        self._combo.setMaximumHeight(26)
        self._combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self._combo.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        layout.addWidget(self._combo, 1)

        # Refresh button with proper alignment
        self._refresh_btn = QPushButton()
        self._refresh_btn.setToolTip("Refresh credentials")
        self._refresh_btn.setText("\u21bb")  # Unicode refresh symbol
        self._refresh_btn.setFixedSize(26, 26)
        self._refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self._refresh_btn, 0, Qt.AlignmentFlag.AlignVCenter)

        # Set widget height constraints for consistent appearance
        self.setMinimumHeight(28)
        self.setMaximumHeight(28)

    def _apply_styles(self) -> None:
        """Apply dark theme styling."""
        self._combo.setStyleSheet(PICKER_STYLE)
        self._refresh_btn.setStyleSheet(BUTTON_STYLE)

    def _connect_signals(self) -> None:
        """Connect widget signals."""
        self._combo.currentIndexChanged.connect(self._on_selection_changed)
        self._refresh_btn.clicked.connect(self._refresh_credentials)

    def _refresh_credentials(self) -> None:
        """Reload credentials from credential store."""
        try:
            from casare_rpa.infrastructure.security.credential_store import (
                get_credential_store,
            )

            store = get_credential_store()
            self._credentials = store.get_credentials_for_dropdown(category="google")

            # Update combo box
            self._combo.blockSignals(True)
            self._combo.clear()

            if not self._credentials:
                self._combo.addItem("No Google accounts configured", "")
            else:
                for cred_id, display_name in self._credentials:
                    self._combo.addItem(display_name, cred_id)

            # Add "Add Google Account..." option
            self._combo.insertSeparator(self._combo.count())
            self._combo.addItem("+ Add Google Account...", ADD_ACCOUNT_ID)

            # Restore selection or auto-select
            should_emit = False
            if self._current_credential_id:
                index = self._combo.findData(self._current_credential_id)
                if index >= 0:
                    self._combo.setCurrentIndex(index)
            elif len(self._credentials) == 1:
                # Auto-select if only one credential
                self._combo.setCurrentIndex(0)
                self._current_credential_id = self._credentials[0][0]
                should_emit = True  # Notify child widgets of auto-selection

            self._combo.blockSignals(False)

            logger.debug(f"Loaded {len(self._credentials)} Google credentials")

            # Emit signal AFTER unblocking signals for auto-selection
            if should_emit and self._current_credential_id:
                self.credential_changed.emit(self._current_credential_id)

        except Exception as e:
            logger.error(f"Failed to load Google credentials: {e}")
            self._combo.clear()
            self._combo.addItem("Error loading credentials", "")
            self._combo.insertSeparator(self._combo.count())
            self._combo.addItem("+ Add Google Account...", ADD_ACCOUNT_ID)

    def _on_selection_changed(self, index: int) -> None:
        """Handle combo box selection change."""
        if index < 0:
            return

        credential_id = self._combo.itemData(index)

        # Handle "Add Google Account..." selection
        if credential_id == ADD_ACCOUNT_ID:
            self._open_add_account_dialog()
            # Reset to previous selection
            if self._current_credential_id:
                prev_index = self._combo.findData(self._current_credential_id)
                if prev_index >= 0:
                    self._combo.blockSignals(True)
                    self._combo.setCurrentIndex(prev_index)
                    self._combo.blockSignals(False)
            return

        # Skip empty/error items
        if not credential_id:
            return

        self._current_credential_id = credential_id
        self.credential_changed.emit(credential_id)

    def _open_add_account_dialog(self) -> None:
        """Open the Google OAuth dialog to add a new account."""
        try:
            from casare_rpa.presentation.canvas.ui.dialogs.google_oauth_dialog import (
                GoogleOAuthDialog,
            )

            dialog = GoogleOAuthDialog(self.window())
            dialog.credential_created.connect(self._on_credential_created)
            dialog.exec()

        except Exception as e:
            logger.error(f"Failed to open OAuth dialog: {e}")

    def _on_credential_created(self, credential_id: str) -> None:
        """Handle new credential creation."""
        self._current_credential_id = credential_id
        self._refresh_credentials()
        self.credential_changed.emit(credential_id)

    # =========================================================================
    # Public API
    # =========================================================================

    def get_credential_id(self) -> Optional[str]:
        """Get the currently selected credential ID."""
        return self._current_credential_id

    def set_credential_id(self, credential_id: str) -> None:
        """
        Set the selected credential by ID.

        Args:
            credential_id: ID of the credential to select
        """
        index = self._combo.findData(credential_id)
        if index >= 0:
            self._combo.setCurrentIndex(index)
            self._current_credential_id = credential_id
        else:
            # Credential not found, refresh and try again
            self._refresh_credentials()
            index = self._combo.findData(credential_id)
            if index >= 0:
                self._combo.setCurrentIndex(index)
                self._current_credential_id = credential_id

    def refresh(self) -> None:
        """Refresh the credential list."""
        self._refresh_credentials()

    def is_valid(self) -> bool:
        """Check if a valid credential is selected."""
        return (
            self._current_credential_id is not None
            and self._current_credential_id != ""
            and self._current_credential_id != ADD_ACCOUNT_ID
        )

    def get_credential_display_name(self) -> str:
        """Get the display name of the selected credential."""
        return self._combo.currentText()


class GoogleCredentialPickerWithLabel(QWidget):
    """
    Google credential picker with label.

    Convenience widget that combines a label with the credential picker.
    """

    credential_changed = Signal(str)

    def __init__(
        self,
        label: str = "Google Account:",
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self._label = QLabel(label)
        self._label.setStyleSheet(f"color: {THEME.text_secondary};")
        layout.addWidget(self._label)

        self._picker = GoogleCredentialPicker()
        self._picker.credential_changed.connect(self.credential_changed.emit)
        layout.addWidget(self._picker, 1)

    def get_credential_id(self) -> Optional[str]:
        """Get the currently selected credential ID."""
        return self._picker.get_credential_id()

    def set_credential_id(self, credential_id: str) -> None:
        """Set the selected credential by ID."""
        self._picker.set_credential_id(credential_id)

    def refresh(self) -> None:
        """Refresh the credential list."""
        self._picker.refresh()

    def is_valid(self) -> bool:
        """Check if a valid credential is selected."""
        return self._picker.is_valid()


__all__ = [
    "GoogleCredentialPicker",
    "GoogleCredentialPickerWithLabel",
]
