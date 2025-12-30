"""
CasareRPA - MFA Setup Dialog.

Dialog for setting up multi-factor authentication:
- QR code display for authenticator apps
- Secret key manual entry option
- Code verification to confirm setup

MIGRATION(Epic 7.4): Migrated from dialog_styles to THEME_V2/TOKENS_V2.
TODO: Replace with dialogs_v2 components (BaseDialogV2) for full migration.

Usage:
    from casare_rpa.presentation.canvas.ui.dialogs import MFASetupDialog

    dialog = MFASetupDialog(parent, user_email="user@example.com")
    if dialog.exec() == QDialog.DialogCode.Accepted:
        encrypted_secret = dialog.encrypted_secret
        # Store the secret for the user
"""


from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.theme_system import THEME_V2, TOKENS_V2
from casare_rpa.presentation.canvas.ui.dialogs_v2 import BaseDialogV2, DialogSizeV2


class MFASetupDialog(BaseDialogV2):
    """
    Dialog for MFA setup with QR code display.

    Guides user through authenticator app setup process.
    """

    mfa_enabled = Signal(str)  # encrypted_secret
    mfa_cancelled = Signal()

    def __init__(
        self,
        parent: QWidget | None = None,
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
        super().__init__(
            title="Enable Two-Factor Authentication",
            parent=parent,
            size=DialogSizeV2.MD,
        )

        self._user_email = user_email
        self._totp_manager = totp_manager
        self._secret: str | None = None
        self._encrypted_secret: str | None = None
        self._qr_pixmap: QPixmap | None = None

        # Set initial buttons
        self.set_primary_button("Continue", self._on_next)
        self.set_secondary_button("Cancel", self._on_cancel)

        # Content setup
        content = QWidget()
        self._setup_ui(content)
        self.set_body_widget(content)
        self._apply_styles()

        # Connect verification input
        self._verify_input.returnPressed.connect(self._on_next)

        # Generate secret if manager provided
        if self._totp_manager:
            self._generate_secret()

    @property
    def secret(self) -> str | None:
        """Get the raw TOTP secret."""
        return self._secret

    @property
    def encrypted_secret(self) -> str | None:
        """Get the encrypted secret for storage."""
        return self._encrypted_secret

    def set_totp_manager(self, manager) -> None:
        """Set the TOTP manager and generate secret."""
        self._totp_manager = manager
        self._generate_secret()

    def _setup_ui(self, content: QWidget) -> None:
        """Setup dialog UI components."""
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(TOKENS_V2.spacing.lg)

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

        # Error message (bottom of content)
        self._error_label = QLabel()
        self._error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._error_label.setWordWrap(True)
        self._error_label.hide()
        layout.addWidget(self._error_label)

    def _apply_styles(self) -> None:
        """Apply v2 styles to components."""
        t = THEME_V2
        tok = TOKENS_V2

        style = f"""
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {t.border};
                border-radius: {tok.radius.md}px;
                margin-top: {tok.spacing.sm}px;
                padding-top: {tok.spacing.sm}px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: {tok.spacing.sm}px;
                padding: 0 {tok.spacing.xs}px;
            }}
            QLineEdit {{
                background-color: {t.input_bg};
                border: 1px solid {t.border};
                border-radius: {tok.radius.sm}px;
                padding: {tok.spacing.sm}px;
                color: {t.text_primary};
            }}
            QLineEdit:focus {{
                border: 1px solid {t.border_focus};
            }}
            QPushButton#copyButton {{
                background: transparent;
                border: none;
                color: {t.primary};
                text-align: left;
                padding: {tok.spacing.xs}px;
            }}
            QPushButton#copyButton:hover {{
                text-decoration: underline;
                color: {t.primary_hover};
            }}
        """
        self.setStyleSheet(style)

    def _create_qr_step(self) -> QWidget:
        """Create the QR code display step."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(TOKENS_V2.spacing.md)

        # Instructions
        instructions = QLabel(
            "Scan this QR code with your authenticator app\n"
            "(Google Authenticator, Authy, Microsoft Authenticator, etc.)"
        )
        instructions.setStyleSheet(f"color: {THEME_V2.text_secondary};")
        instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        # QR code container
        qr_container = QWidget()
        qr_container.setStyleSheet(f"""
            background: white;
            border-radius: {TOKENS_V2.radius.md}px;
            padding: {TOKENS_V2.spacing.md}px;
        """)
        qr_layout = QVBoxLayout(qr_container)
        qr_layout.setContentsMargins(16, 16, 16, 16)
        qr_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._qr_label = QLabel()
        self._qr_label.setMinimumSize(200, 200)
        self._qr_label.setMaximumSize(200, 200)
        self._qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._qr_label.setStyleSheet("background: white; color: black;")
        qr_layout.addWidget(self._qr_label)

        layout.addWidget(qr_container, alignment=Qt.AlignmentFlag.AlignCenter)

        # Manual entry section
        manual_group = QGroupBox("Can't scan? Enter this code manually:")
        manual_layout = QVBoxLayout(manual_group)

        self._secret_display = QLineEdit()
        self._secret_display.setReadOnly(True)
        self._secret_display.setStyleSheet(f"""
            font-family: {TOKENS_V2.typography.mono};
            font-size: {TOKENS_V2.typography.body}px;
            letter-spacing: 2px;
            background: {THEME_V2.bg_component};
        """)
        manual_layout.addWidget(self._secret_display)

        copy_btn = QPushButton("Copy to Clipboard")
        copy_btn.setObjectName("copyButton")
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
        layout.setSpacing(TOKENS_V2.spacing.lg)

        # Instructions
        instructions = QLabel(
            "Enter the 6-digit code from your authenticator app\n"
            "to verify the setup was successful."
        )
        instructions.setStyleSheet(f"color: {THEME_V2.text_secondary};")
        instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        # Code input
        input_container = QWidget()
        input_layout = QVBoxLayout(input_container)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(TOKENS_V2.spacing.xs)

        code_label = QLabel("Verification Code")
        code_label.setStyleSheet(f"color: {THEME_V2.text_secondary}; font-size: {TOKENS_V2.typography.body_sm}px;")
        code_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        input_layout.addWidget(code_label)

        self._verify_input = QLineEdit()
        self._verify_input.setPlaceholderText("000000")
        self._verify_input.setMaxLength(6)
        self._verify_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Specific styling for the big verification input
        self._verify_input.setStyleSheet(f"""
            QLineEdit {{
                background: {THEME_V2.bg_elevated};
                border: 1px solid {THEME_V2.border};
                border-radius: {TOKENS_V2.radius.md}px;
                padding: {TOKENS_V2.spacing.md}px;
                color: {THEME_V2.text_primary};
                font-size: 28px;
                font-family: {TOKENS_V2.typography.mono};
                letter-spacing: 12px;
                max-width: 250px;
            }}
            QLineEdit:focus {{
                border: 1px solid {THEME_V2.border_focus};
            }}
        """)
        input_layout.addWidget(self._verify_input, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(input_container)

        # Hint
        hint = QLabel("The code changes every 30 seconds")
        hint.setStyleSheet(f"color: {THEME_V2.text_muted}; font-size: {TOKENS_V2.typography.caption}px;")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint)

        return widget

    def _create_success_step(self) -> QWidget:
        """Create the success confirmation step."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(TOKENS_V2.spacing.lg)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Success icon
        success_icon = QLabel("OK")
        success_icon.setStyleSheet(f"""
            background: {THEME_V2.success};
            border-radius: 40px;
            padding: 20px;
            font-size: 24px;
            font-weight: bold;
            color: {THEME_V2.text_on_success};
        """)
        success_icon.setFixedSize(80, 80)
        success_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(success_icon, alignment=Qt.AlignmentFlag.AlignCenter)

        # Success message
        msg_container = QWidget()
        msg_layout = QVBoxLayout(msg_container)
        msg_layout.setContentsMargins(0, 0, 0, 0)
        msg_layout.setSpacing(TOKENS_V2.spacing.sm)

        success_title = QLabel("Two-Factor Authentication Enabled")
        success_title.setStyleSheet(f"""
            font-size: {TOKENS_V2.typography.display_sm}px;
            font-weight: {TOKENS_V2.typography.weight_semibold};
            color: {THEME_V2.success};
        """)
        success_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg_layout.addWidget(success_title)

        success_msg = QLabel(
            "Your account is now protected with an additional\n"
            "layer of security. You'll need to enter a code from\n"
            "your authenticator app when signing in."
        )
        success_msg.setStyleSheet(f"color: {THEME_V2.text_secondary};")
        success_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg_layout.addWidget(success_msg)

        layout.addWidget(msg_container)

        # Recovery codes notice
        recovery_notice = QLabel(
            "Important: Save your recovery codes in a safe place.\n"
            "They can be used to access your account if you lose\n"
            "access to your authenticator app."
        )
        recovery_notice.setStyleSheet(f"""
            color: {THEME_V2.warning};
            background: {THEME_V2.bg_surface};
            border: 1px solid {THEME_V2.warning};
            border-radius: {TOKENS_V2.radius.sm}px;
            padding: {TOKENS_V2.spacing.sm}px;
        """)
        recovery_notice.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(recovery_notice)

        return widget

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
                clipboard = QApplication.clipboard()
                clipboard.setText(self._secret)
                self._show_success_message("Secret copied to clipboard")
            except Exception:
                pass

    def _show_success_message(self, message: str) -> None:
        """Show temporary success message."""
        self._error_label.setStyleSheet(f"color: {THEME_V2.success};")
        self._error_label.setText(message)
        self._error_label.show()
        QTimer.singleShot(2000, self._hide_error)

    def _on_cancel(self) -> None:
        """Handle cancel button click."""
        self.mfa_cancelled.emit()
        self.reject()

    def _on_next(self) -> None:
        """Handle next/continue button click."""
        current_index = self._stack.currentIndex()

        if current_index == 0:  # QR code -> Verify
            self._hide_error()
            self._stack.setCurrentIndex(1)
            self.set_primary_button("Verify", self._on_next)
            self._verify_input.setFocus()

        elif current_index == 1:  # Verify -> Success
            self._verify_code()

        elif current_index == 2:  # Success -> Close
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
        btn = self._footer_buttons.get("primary")
        if btn:
            btn.setEnabled(False)
            btn.setText("Verifying...")

        try:
            if self._totp_manager.verify_code(self._secret, code):
                self._encrypted_secret = self._secret
                self._show_success()
            else:
                self._show_error("Invalid code. Please try again.")
                if btn:
                    btn.setEnabled(True)
                    btn.setText("Verify")
                self._verify_input.clear()
                self._verify_input.setFocus()

        except Exception as e:
            self._show_error(f"Verification failed: {e}")
            if btn:
                btn.setEnabled(True)
                btn.setText("Verify")

    def _show_success(self) -> None:
        """Show success step."""
        self._hide_error()
        self._stack.setCurrentIndex(2)
        self.set_primary_button("Done", self.accept)
        self.set_secondary_button_visible(False)
        self.mfa_enabled.emit(self._encrypted_secret or "")

    def _show_error(self, message: str) -> None:
        """Show error message."""
        self._error_label.setStyleSheet(f"color: {THEME_V2.error};")
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
                self.set_primary_button("Continue", self._on_next)
                self._hide_error()
        else:
            super().keyPressEvent(event)


__all__ = ["MFASetupDialog"]
