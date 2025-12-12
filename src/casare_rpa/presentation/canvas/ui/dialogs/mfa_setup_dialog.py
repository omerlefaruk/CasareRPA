"""
CasareRPA - MFA Setup Dialog.

Dialog for setting up multi-factor authentication:
- QR code display for authenticator apps
- Secret key manual entry option
- Code verification to confirm setup

Usage:
    from casare_rpa.presentation.canvas.ui.dialogs import MFASetupDialog

    dialog = MFASetupDialog(parent, user_email="user@example.com")
    if dialog.exec() == QDialog.DialogCode.Accepted:
        encrypted_secret = dialog.encrypted_secret
        # Store the secret for the user
"""

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QWidget,
    QStackedWidget,
    QGroupBox,
    QSpacerItem,
    QSizePolicy,
)

from casare_rpa.presentation.canvas.ui.dialogs.dialog_styles import (
    DialogStyles,
    DialogSize,
    DIALOG_DIMENSIONS,
    COLORS,
)


class MFASetupDialog(QDialog):
    """
    Dialog for MFA setup with QR code display.

    Guides user through authenticator app setup process.
    """

    mfa_enabled = Signal(str)  # encrypted_secret
    mfa_cancelled = Signal()

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        user_email: str = "",
        totp_manager=None,
    ) -> None:
        """
        Initialize MFA setup dialog.

        Args:
            parent: Parent widget
            user_email: User's email for provisioning URI
            totp_manager: Optional TOTPManager instance
        """
        super().__init__(parent)
        self._user_email = user_email
        self._totp_manager = totp_manager
        self._secret: Optional[str] = None
        self._encrypted_secret: Optional[str] = None
        self._qr_pixmap: Optional[QPixmap] = None

        self._setup_ui()
        self._connect_signals()

        # Generate secret if manager provided
        if self._totp_manager:
            self._generate_secret()

    @property
    def secret(self) -> Optional[str]:
        """Get the raw TOTP secret."""
        return self._secret

    @property
    def encrypted_secret(self) -> Optional[str]:
        """Get the encrypted secret for storage."""
        return self._encrypted_secret

    def set_totp_manager(self, manager) -> None:
        """
        Set the TOTP manager and generate secret.

        Args:
            manager: TOTPManager instance
        """
        self._totp_manager = manager
        self._generate_secret()

    def _setup_ui(self) -> None:
        """Setup dialog UI components."""
        self.setWindowTitle("Enable Two-Factor Authentication")
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowCloseButtonHint)

        # Set size
        width, height = DIALOG_DIMENSIONS[DialogSize.MD]
        self.setFixedSize(width, height + 50)

        # Apply styling
        self.setStyleSheet(DialogStyles.full_dialog_style())

        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(16)

        # Header
        header = QLabel("Enable Two-Factor Authentication")
        header.setStyleSheet(f"""
            font-size: 18px;
            font-weight: bold;
            color: {COLORS.text_primary};
        """)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        # Stacked widget for setup steps
        self._stack = QStackedWidget()
        layout.addWidget(self._stack)

        # Step 1: QR Code display
        self._qr_widget = self._create_qr_step()
        self._stack.addWidget(self._qr_widget)

        # Step 2: Verification
        self._verify_widget = self._create_verify_step()
        self._stack.addWidget(self._verify_widget)

        # Step 3: Success
        self._success_widget = self._create_success_step()
        self._stack.addWidget(self._success_widget)

        # Error message
        self._error_label = QLabel()
        self._error_label.setStyleSheet(DialogStyles.error_label())
        self._error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._error_label.setWordWrap(True)
        self._error_label.hide()
        layout.addWidget(self._error_label)

        # Spacer
        layout.addSpacerItem(
            QSpacerItem(
                20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
            )
        )

        # Navigation buttons
        self._nav_layout = QHBoxLayout()
        self._nav_layout.setContentsMargins(0, 16, 0, 0)

        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.setStyleSheet(DialogStyles.button_secondary())
        self._cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._nav_layout.addWidget(self._cancel_btn)

        self._nav_layout.addStretch()

        self._next_btn = QPushButton("Continue")
        self._next_btn.setStyleSheet(DialogStyles.button_primary())
        self._next_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._nav_layout.addWidget(self._next_btn)

        layout.addLayout(self._nav_layout)

    def _create_qr_step(self) -> QWidget:
        """Create the QR code display step."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # Instructions
        instructions = QLabel(
            "Scan this QR code with your authenticator app\n"
            "(Google Authenticator, Authy, Microsoft Authenticator, etc.)"
        )
        instructions.setStyleSheet(f"color: {COLORS.text_secondary}; font-size: 12px;")
        instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        # QR code container
        qr_container = QWidget()
        qr_container.setStyleSheet("""
            background: white;
            border-radius: 8px;
            padding: 16px;
        """)
        qr_layout = QVBoxLayout(qr_container)
        qr_layout.setContentsMargins(16, 16, 16, 16)
        qr_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._qr_label = QLabel()
        self._qr_label.setMinimumSize(200, 200)
        self._qr_label.setMaximumSize(200, 200)
        self._qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._qr_label.setStyleSheet("background: white;")
        qr_layout.addWidget(self._qr_label)

        layout.addWidget(qr_container, alignment=Qt.AlignmentFlag.AlignCenter)

        # Manual entry section
        manual_group = QGroupBox("Can't scan? Enter this code manually:")
        manual_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: 11px;
                color: {COLORS.text_muted};
                border: 1px solid {COLORS.border};
                border-radius: 4px;
                margin-top: 8px;
                padding: 8px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px;
            }}
        """)
        manual_layout = QVBoxLayout(manual_group)

        self._secret_display = QLineEdit()
        self._secret_display.setReadOnly(True)
        self._secret_display.setStyleSheet(f"""
            QLineEdit {{
                background: {COLORS.bg_input_readonly};
                border: 1px solid {COLORS.border_input};
                border-radius: 4px;
                padding: 8px;
                color: {COLORS.text_primary};
                font-family: monospace;
                font-size: 12px;
                letter-spacing: 2px;
            }}
        """)
        manual_layout.addWidget(self._secret_display)

        copy_btn = QPushButton("Copy to Clipboard")
        copy_btn.setStyleSheet(DialogStyles.button_inline())
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.clicked.connect(self._copy_secret)
        manual_layout.addWidget(copy_btn)

        layout.addWidget(manual_group)

        return widget

    def _create_verify_step(self) -> QWidget:
        """Create the verification step."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # Instructions
        instructions = QLabel(
            "Enter the 6-digit code from your authenticator app\n"
            "to verify the setup was successful."
        )
        instructions.setStyleSheet(f"color: {COLORS.text_secondary}; font-size: 12px;")
        instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        layout.addSpacing(24)

        # Code input
        code_label = QLabel("Verification Code")
        code_label.setStyleSheet(f"color: {COLORS.text_secondary}; font-size: 12px;")
        code_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(code_label)

        self._verify_input = QLineEdit()
        self._verify_input.setPlaceholderText("000000")
        self._verify_input.setMaxLength(6)
        self._verify_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._verify_input.setStyleSheet(f"""
            QLineEdit {{
                background: {COLORS.bg_input};
                border: 1px solid {COLORS.border_input};
                border-radius: 4px;
                padding: 16px;
                color: {COLORS.text_primary};
                font-size: 28px;
                font-family: monospace;
                letter-spacing: 12px;
                max-width: 250px;
            }}
            QLineEdit:focus {{
                border-color: {COLORS.border_focus};
            }}
        """)
        layout.addWidget(self._verify_input, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addSpacing(16)

        # Hint
        hint = QLabel("The code changes every 30 seconds")
        hint.setStyleSheet(DialogStyles.info_label())
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint)

        return widget

    def _create_success_step(self) -> QWidget:
        """Create the success confirmation step."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Success icon (checkmark)
        success_icon = QLabel()
        success_icon.setStyleSheet(f"""
            background: {COLORS.success};
            border-radius: 40px;
            padding: 20px;
            font-size: 32px;
            color: white;
        """)
        success_icon.setText("OK")  # Simple text instead of icon
        success_icon.setFixedSize(80, 80)
        success_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(success_icon, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addSpacing(16)

        # Success message
        success_title = QLabel("Two-Factor Authentication Enabled")
        success_title.setStyleSheet(f"""
            font-size: 16px;
            font-weight: bold;
            color: {COLORS.success};
        """)
        success_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(success_title)

        success_msg = QLabel(
            "Your account is now protected with an additional\n"
            "layer of security. You'll need to enter a code from\n"
            "your authenticator app when signing in."
        )
        success_msg.setStyleSheet(f"color: {COLORS.text_secondary}; font-size: 12px;")
        success_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(success_msg)

        layout.addSpacing(16)

        # Recovery codes notice
        recovery_notice = QLabel(
            "Important: Save your recovery codes in a safe place.\n"
            "They can be used to access your account if you lose\n"
            "access to your authenticator app."
        )
        recovery_notice.setStyleSheet(f"""
            color: {COLORS.text_warning};
            font-size: 11px;
            background: {COLORS.bg_panel};
            border: 1px solid {COLORS.warning};
            border-radius: 4px;
            padding: 12px;
        """)
        recovery_notice.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(recovery_notice)

        return widget

    def _connect_signals(self) -> None:
        """Connect UI signals."""
        self._cancel_btn.clicked.connect(self._on_cancel)
        self._next_btn.clicked.connect(self._on_next)
        self._verify_input.returnPressed.connect(self._on_next)

    def _generate_secret(self) -> None:
        """Generate TOTP secret and update UI."""
        if not self._totp_manager:
            return

        try:
            self._secret = self._totp_manager.generate_secret()
            self._secret_display.setText(self._format_secret(self._secret))

            # Generate QR code
            uri = self._totp_manager.get_provisioning_uri(
                self._secret,
                self._user_email,
            )
            qr_bytes = self._totp_manager.generate_qr_code(uri)
            self._display_qr_code(qr_bytes)

        except Exception as e:
            self._show_error(f"Failed to generate secret: {e}")

    def _format_secret(self, secret: str) -> str:
        """Format secret into readable groups."""
        # Split into groups of 4 characters
        groups = [secret[i : i + 4] for i in range(0, len(secret), 4)]
        return " ".join(groups)

    def _display_qr_code(self, qr_bytes: bytes) -> None:
        """Display QR code image."""
        try:
            image = QImage.fromData(qr_bytes, "PNG")
            if image.isNull():
                self._qr_label.setText("QR Code\nUnavailable")
                return

            pixmap = QPixmap.fromImage(image)
            scaled = pixmap.scaled(
                180,
                180,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self._qr_label.setPixmap(scaled)
            self._qr_pixmap = scaled

        except Exception as e:
            self._qr_label.setText(f"Error:\n{e}")

    def _copy_secret(self) -> None:
        """Copy secret to clipboard."""
        if self._secret:
            try:
                from PySide6.QtWidgets import QApplication

                clipboard = QApplication.clipboard()
                clipboard.setText(self._secret)
                self._show_success_message("Secret copied to clipboard")
            except Exception:
                pass

    def _show_success_message(self, message: str) -> None:
        """Show temporary success message."""
        self._error_label.setStyleSheet(DialogStyles.success_label())
        self._error_label.setText(message)
        self._error_label.show()

        # Hide after 2 seconds
        from PySide6.QtCore import QTimer

        QTimer.singleShot(2000, self._hide_error)

    def _on_cancel(self) -> None:
        """Handle cancel button click."""
        self.mfa_cancelled.emit()
        self.reject()

    def _on_next(self) -> None:
        """Handle next/continue button click."""
        current_index = self._stack.currentIndex()

        if current_index == 0:  # QR code step -> Verify step
            self._hide_error()
            self._stack.setCurrentIndex(1)
            self._next_btn.setText("Verify")
            self._verify_input.setFocus()

        elif current_index == 1:  # Verify step -> Success/error
            self._verify_code()

        elif current_index == 2:  # Success step -> Close
            self.accept()

    def _verify_code(self) -> None:
        """Verify the entered TOTP code."""
        code = self._verify_input.text().strip()

        if not code or len(code) != 6:
            self._show_error("Please enter a valid 6-digit code")
            return

        if not self._totp_manager or not self._secret:
            self._show_error("Setup error: missing TOTP manager or secret")
            return

        self._hide_error()
        self._next_btn.setEnabled(False)
        self._next_btn.setText("Verifying...")

        try:
            if self._totp_manager.verify_code(self._secret, code):
                # Success - store the secret (would be encrypted in production)
                self._encrypted_secret = self._secret  # In production, encrypt this
                self._show_success()
            else:
                self._show_error("Invalid code. Please try again.")
                self._next_btn.setEnabled(True)
                self._next_btn.setText("Verify")
                self._verify_input.clear()
                self._verify_input.setFocus()

        except Exception as e:
            self._show_error(f"Verification failed: {e}")
            self._next_btn.setEnabled(True)
            self._next_btn.setText("Verify")

    def _show_success(self) -> None:
        """Show success step."""
        self._hide_error()
        self._stack.setCurrentIndex(2)
        self._next_btn.setText("Done")
        self._next_btn.setEnabled(True)
        self._cancel_btn.hide()
        self.mfa_enabled.emit(self._encrypted_secret or "")

    def _show_error(self, message: str) -> None:
        """Show error message."""
        self._error_label.setStyleSheet(DialogStyles.error_label())
        self._error_label.setText(message)
        self._error_label.show()

    def _hide_error(self) -> None:
        """Hide error message."""
        self._error_label.clear()
        self._error_label.hide()

    def keyPressEvent(self, event) -> None:
        """Handle key press events."""
        if event.key() == Qt.Key.Key_Escape:
            if self._stack.currentIndex() == 0:
                self.reject()
            elif self._stack.currentIndex() == 1:
                # Go back to QR step
                self._stack.setCurrentIndex(0)
                self._next_btn.setText("Continue")
            # On success step, Escape does nothing
        else:
            super().keyPressEvent(event)


__all__ = ["MFASetupDialog"]
