"""
Encryptable Line Edit Widget for CasareRPA.

Extends VariableAwareLineEdit with inline encryption capability.
Shows a lock button (🔒) that encrypts the current text and stores it
securely in the credential store.

When encrypted, displays masked text (•••••) and the lock icon changes
to an unlocked state (🔓). Clicking the unlocked icon allows editing.
"""

from __future__ import annotations

import re
from functools import partial
from typing import Any

from loguru import logger
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import QPushButton, QWidget

from casare_rpa.presentation.canvas.theme import THEME_V2 as THEME
from casare_rpa.presentation.canvas.theme.utils import alpha


class EncryptableLineEdit(QWidget):
    """
    Line edit with inline encryption capability.

    Features:
    - Lock button (🔒) to encrypt current text
    - Masked display (•••••) when encrypted
    - Unlock button (🔓) to reveal/edit encrypted value
    - Stores encrypted values in credential store with {{$secret:id}} syntax
    - Inherits variable picker functionality

    Signals:
        text_changed: Emitted when text changes (raw or encrypted reference)
        encryption_state_changed: Emitted when encryption state changes (bool)
    """

    # Signal emitted when text changes (either plaintext or {{$secret:id}})
    text_changed = Signal(str)
    # Signal emitted when encryption state changes
    encryption_state_changed = Signal(bool)

    # Masked display for encrypted values
    MASKED_TEXT = "•••••••••"

    def __init__(
        self,
        parent: QWidget | None = None,
        show_variable_button: bool = True,
        show_expand_button: bool = False,
    ) -> None:
        """
        Initialize the widget.

        Args:
            parent: Parent widget
            show_variable_button: Whether to show the {x} variable picker button
            show_expand_button: Whether to show the ... expand button
        """
        super().__init__(parent)

        self._is_encrypted = False
        self._credential_id: str | None = None
        self._plaintext_cache: str | None = None  # Cached for editing
        self._show_variable_button = show_variable_button
        self._show_expand_button = show_expand_button

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Set up the widget UI."""
        from PySide6.QtWidgets import QHBoxLayout

        from casare_rpa.presentation.canvas.ui.widgets.variable_picker import (
            VariableAwareLineEdit,
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # Main line edit with variable support
        self._line_edit = VariableAwareLineEdit(
            self,
            show_expand_button=self._show_expand_button,
        )
        self._line_edit.setMinimumHeight(24)
        layout.addWidget(self._line_edit, 1)

        # Lock/Unlock button
        c = THEME
        self._lock_button = QPushButton("🔒", self)
        self._lock_button.setFixedSize(24, 24)
        self._lock_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._lock_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._lock_button.setToolTip("Encrypt this value (makes it a secret)")
        self._lock_button.setStyleSheet(f"""
            QPushButton {{
                background: {c.bg_component};
                border: 1px solid {c.border};
                border-radius: 4px;
                font-size: 12px;
                padding: 0px;
            }}
            QPushButton:hover {{
                background: {c.primary};
                border-color: {c.primary};
            }}
            QPushButton:pressed {{
                background: {c.primary_hover};
            }}
        """)
        layout.addWidget(self._lock_button)

        # Apply styling to line edit
        self._apply_normal_style()

    def _connect_signals(self) -> None:
        """Connect internal signals."""
        self._lock_button.clicked.connect(self._on_lock_button_clicked)
        self._line_edit.textChanged.connect(self._on_text_changed)

    def _apply_normal_style(self) -> None:
        """Apply normal (unencrypted) styling to line edit."""
        c = THEME
        # Calculate right padding for buttons
        right_padding = 28  # Variable button
        if self._show_expand_button:
            right_padding += 20

        self._line_edit.setStyleSheet(f"""
            QLineEdit {{
                background: {c.input_bg};
                border: 1px solid {c.border};
                border-radius: 3px;
                color: {c.text_primary};
                padding: 2px {right_padding}px 2px 4px;
                selection-background-color: {c.primary};
                selection-color: {c.text_on_primary};
            }}
            QLineEdit:focus {{
                background: {c.bg_hover};
                border: 1px solid {c.border_focus};
            }}
        """)

    def _apply_encrypted_style(self) -> None:
        """Apply encrypted (masked) styling to line edit."""
        c = THEME
        # Green tint for encrypted state - use success color with transparency
        right_padding = 28
        if self._show_expand_button:
            right_padding += 20

        self._line_edit.setStyleSheet(f"""
            QLineEdit {{
                background: {alpha(c.success, 0.18)};
                border: 1px solid {c.success};
                border-radius: 3px;
                color: {c.text_secondary};
                padding: 2px {right_padding}px 2px 4px;
                font-style: italic;
            }}
            QLineEdit:focus {{
                background: {alpha(c.success, 0.25)};
                border: 1px solid {c.success_hover};
            }}
        """)

    def _apply_editing_style(self) -> None:
        """Apply editing (decrypted temporarily) styling."""
        c = THEME
        # Orange/warning tint for editing encrypted value - matches warning color
        right_padding = 28
        if self._show_expand_button:
            right_padding += 20

        self._line_edit.setStyleSheet(f"""
            QLineEdit {{
                background: {alpha(c.warning, 0.18)};
                border: 1px solid {c.warning};
                border-radius: 3px;
                color: {c.text_primary};
                padding: 2px {right_padding}px 2px 4px;
            }}
            QLineEdit:focus {{
                background: {alpha(c.warning, 0.25)};
                border: 1px solid {c.warning_hover};
            }}
        """)

    @Slot()
    def _on_lock_button_clicked(self) -> None:
        """Handle lock/unlock button click."""
        if self._is_encrypted:
            # Unlock: show plaintext for editing
            self._unlock_for_editing()
        else:
            # Lock: encrypt current text
            self._encrypt_current_text()

    def _encrypt_current_text(self) -> None:
        """Encrypt the current text and store it."""
        text = self._line_edit.text().strip()
        if not text:
            logger.debug("Nothing to encrypt - text is empty")
            return

        # Don't encrypt if already a secret reference
        if text.startswith("{{$secret:") and text.endswith("}}"):
            logger.debug("Text is already a secret reference")
            return

        try:
            from casare_rpa.infrastructure.security.credential_store import (
                get_credential_store,
            )

            store = get_credential_store()
            credential_id = store.encrypt_inline_secret(
                plaintext=text,
                name="inline_secret",
                description="Encrypted from parameter widget",
            )

            self._credential_id = credential_id
            self._is_encrypted = True
            self._plaintext_cache = text

            # Update display
            self._line_edit.blockSignals(True)
            self._line_edit.setText(self.MASKED_TEXT)
            self._line_edit.setReadOnly(True)
            self._line_edit.blockSignals(False)

            # Update button
            self._lock_button.setText("🔓")
            self._lock_button.setToolTip("Click to edit this secret")

            # Update styling
            self._apply_encrypted_style()

            # Emit signals
            self.encryption_state_changed.emit(True)
            self.text_changed.emit(f"{{{{$secret:{credential_id}}}}}")

            logger.debug(f"Encrypted text to credential: {credential_id}")

        except Exception as e:
            logger.error(f"Failed to encrypt text: {e}")

    def _unlock_for_editing(self) -> None:
        """Unlock encrypted value for editing."""
        if not self._credential_id:
            return

        # Basic UI security: verify before revealing secret
        from PySide6.QtWidgets import QMessageBox

        reply = QMessageBox.question(
            self,
            "Reveal Secret",
            "This value is encrypted for security.\n\nAre you sure you want to reveal and edit it?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            # Get the plaintext from cache or decrypt
            plaintext = self._plaintext_cache
            if not plaintext:
                from casare_rpa.infrastructure.security.credential_store import (
                    get_credential_store,
                )

                store = get_credential_store()
                plaintext = store.decrypt_inline_secret(self._credential_id)

            if plaintext:
                self._line_edit.blockSignals(True)
                self._line_edit.setText(plaintext)
                self._line_edit.setReadOnly(False)
                self._line_edit.blockSignals(False)

                # Update button to show "lock" (will re-encrypt on click)
                self._lock_button.setText("🔒")
                self._lock_button.setToolTip("Click to re-encrypt this value")

                # Apply editing style (orange border)
                self._apply_editing_style()

                # Clear encrypted state temporarily
                self._is_encrypted = False
                self.encryption_state_changed.emit(False)

        except Exception as e:
            logger.error(f"Failed to decrypt for editing: {e}")

    @Slot(str)
    def _on_text_changed(self, text: str) -> None:
        """Handle text changes."""
        # Don't emit if showing masked text
        if text == self.MASKED_TEXT:
            return

        # If we were encrypted and user edited, we need to re-encrypt
        if self._credential_id and not self._is_encrypted:
            # User is editing - update cache
            self._plaintext_cache = text

        self.text_changed.emit(text)

    # =========================================================================
    # Public API
    # =========================================================================

    def text(self) -> str:
        """
        Get the current value.

        Returns:
            - If encrypted: {{$secret:credential_id}}
            - If not encrypted: the raw text
        """
        if self._is_encrypted and self._credential_id:
            return f"{{{{$secret:{self._credential_id}}}}}"
        return self._line_edit.text()

    def setText(self, text: str) -> None:
        """
        Set the text value.

        If text is a {{$secret:id}} reference, it will be displayed as masked.

        Args:
            text: The text to set (can be plaintext or secret reference)
        """
        # Check if it's a secret reference
        secret_match = re.match(r"\{\{\$secret:([^}]+)\}\}", text)
        if secret_match:
            self._credential_id = secret_match.group(1)
            self._is_encrypted = True
            self._plaintext_cache = None

            self._line_edit.blockSignals(True)
            self._line_edit.setText(self.MASKED_TEXT)
            self._line_edit.setReadOnly(True)
            self._line_edit.blockSignals(False)

            self._lock_button.setText("🔓")
            self._lock_button.setToolTip("Click to edit this secret")
            self._apply_encrypted_style()
        else:
            self._credential_id = None
            self._is_encrypted = False
            self._plaintext_cache = None

            self._line_edit.blockSignals(True)
            self._line_edit.setText(text)
            self._line_edit.setReadOnly(False)
            self._line_edit.blockSignals(False)

            self._lock_button.setText("🔒")
            self._lock_button.setToolTip("Encrypt this value (makes it a secret)")
            self._apply_normal_style()

    def setPlaceholderText(self, text: str) -> None:
        """Set placeholder text."""
        self._line_edit.setPlaceholderText(text)

    def setReadOnly(self, read_only: bool) -> None:
        """Set read-only state."""
        if not self._is_encrypted:
            self._line_edit.setReadOnly(read_only)

    def isEncrypted(self) -> bool:
        """Check if the current value is encrypted."""
        return self._is_encrypted

    def getCredentialId(self) -> str | None:
        """Get the credential ID if encrypted."""
        return self._credential_id

    def clear(self) -> None:
        """Clear the current value and encryption state."""
        self._credential_id = None
        self._is_encrypted = False
        self._plaintext_cache = None

        self._line_edit.blockSignals(True)
        self._line_edit.clear()
        self._line_edit.setReadOnly(False)
        self._line_edit.blockSignals(False)

        self._lock_button.setText("🔒")
        self._lock_button.setToolTip("Encrypt this value (makes it a secret)")
        self._apply_normal_style()

        self.encryption_state_changed.emit(False)

    def setToolTip(self, text: str) -> None:
        """Set tooltip on the line edit."""
        self._line_edit.setToolTip(text)

    def set_provider(self, provider: Any) -> None:
        """Set the variable provider for the line edit."""
        if hasattr(self._line_edit, "set_provider"):
            self._line_edit.set_provider(provider)

    def set_node_context(self, node_id: str, graph: Any) -> None:
        """Set node context for upstream variable detection."""
        if hasattr(self._line_edit, "set_node_context"):
            self._line_edit.set_node_context(node_id, graph)


# Convenience factory function
def create_encryptable_text_widget(
    name: str,
    label: str,
    text: str = "",
    placeholder_text: str = "",
    tooltip: str = "",
    show_variable_button: bool = True,
) -> Any:
    """
    Factory function to create an encryptable text widget for NodeGraphQt.

    Creates a NodeBaseWidget with EncryptableLineEdit for use in visual nodes.

    Args:
        name: Property name for the node
        label: Label text displayed above the widget
        text: Initial text value
        placeholder_text: Placeholder text when empty
        tooltip: Tooltip text for the widget
        show_variable_button: Whether to show the {x} variable picker

    Returns:
        NodeBaseWidget with EncryptableLineEdit
    """
    try:
        from NodeGraphQt.widgets.node_widgets import NodeBaseWidget
    except ImportError:
        logger.error("NodeGraphQt not available")
        return None

    # Create the encryptable line edit
    line_edit = EncryptableLineEdit(
        show_variable_button=show_variable_button,
        show_expand_button=False,
    )
    line_edit.setText(text)
    line_edit.setPlaceholderText(placeholder_text)

    if tooltip:
        line_edit.setToolTip(tooltip)

    # Create NodeBaseWidget and set up
    widget = NodeBaseWidget(parent=None, name=name, label=label)
    widget.set_custom_widget(line_edit)

    # Connect signals
    line_edit.text_changed.connect(partial(_trigger_widget_value_changed, widget))

    # Store reference
    widget._encryptable_edit = line_edit

    # Override get_value and set_value
    def get_value():
        return line_edit.text()

    def set_value(value):
        line_edit.setText(str(value) if value else "")

    widget.get_value = get_value
    widget.set_value = set_value

    return widget


@Slot()
def _trigger_widget_value_changed(widget: Any, *args) -> None:
    """Trigger value changed on a widget."""
    widget.on_value_changed()


class NodeEncryptableTextWidget:
    """
    Encryptable text widget for NodeGraphQt nodes.

    Usage in visual node:
        from casare_rpa.presentation.canvas.ui.widgets.encryptable_line_edit import (
            NodeEncryptableTextWidget,
        )

        def __init__(self):
            super().__init__()
            widget = NodeEncryptableTextWidget(
                name="api_key",
                label="API Key",
                placeholder="Enter API key...",
            )
            self.add_custom_widget(widget)
    """

    def __new__(
        cls,
        name: str = "",
        label: str = "",
        text: str = "",
        placeholder: str = "",
        tooltip: str = "",
    ) -> Any:
        """Create a new NodeEncryptableTextWidget."""
        return create_encryptable_text_widget(
            name=name,
            label=label,
            text=text,
            placeholder_text=placeholder,
            tooltip=tooltip,
        )


__all__ = [
    "EncryptableLineEdit",
    "NodeEncryptableTextWidget",
    "create_encryptable_text_widget",
]
