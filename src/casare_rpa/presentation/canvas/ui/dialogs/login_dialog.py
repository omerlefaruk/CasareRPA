"""
CasareRPA - Login Dialog.

Epic 7.x - Migrated to BaseDialogV2 with THEME_V2/TOKENS_V2.

User authentication dialog with:
- Email/password login
- MFA verification step
- Remember me option
- Password visibility toggle
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
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
from casare_rpa.presentation.canvas.ui.dialogs_v2 import (
    BaseDialogV2,
    DialogSizeV2,
)


class LoginDialog(BaseDialogV2):
    """
    Login dialog for user authentication.

    Migrated to BaseDialogV2 (Epic 7.x).

    Supports two-step authentication with optional MFA.
    """

    login_successful = Signal(object, str)  # (User, token)
    login_failed = Signal(str)  # error message

    def __init__(
        self,
        parent: QWidget | None = None,
        require_mfa: bool = False,
    ) -> None:
        """
        Initialize login dialog.

        Args:
            parent: Parent widget
            require_mfa: Whether MFA is always required
        """
        self._require_mfa = require_mfa
        self._authenticated_user = None
        self._access_token: str | None = None
        self._pending_mfa = False

        super().__init__(
            title="Login - CasareRPA",
            parent=parent,
            size=DialogSizeV2.SM,
        )

        self._setup_content()
        self._connect_signals()

    @property
    def authenticated_user(self):
        """Get the authenticated user after successful login."""
        return self._authenticated_user

    @property
    def access_token(self) -> str | None:
        """Get the access token after successful login."""
        return self._access_token

    def _setup_content(self) -> None:
        """Setup dialog UI components."""
        # Main content widget
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(TOKENS_V2.spacing.md)

        # Header
        header = QLabel("Welcome Back")
        header.setStyleSheet(f"""
            font-size: {TOKENS_V2.typography.heading_xl}px;
            font-weight: {TOKENS_V2.typography.weight_bold};
            color: {THEME_V2.text_primary};
        """)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        subtitle = QLabel("Sign in to CasareRPA")
        subtitle.setStyleSheet(f"""
            color: {THEME_V2.text_muted};
            font-size: {TOKENS_V2.typography.body}px;
        """)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        layout.addSpacing(TOKENS_V2.spacing.md)

        # Stacked widget for login/MFA steps
        self._stack = QStackedWidget()
        layout.addWidget(self._stack)

        # Step 1: Login form
        self._login_widget = self._create_login_form()
        self._stack.addWidget(self._login_widget)

        # Step 2: MFA form
        self._mfa_widget = self._create_mfa_form()
        self._stack.addWidget(self._mfa_widget)

        # Error message
        self._error_label = QLabel()
        self._error_label.setStyleSheet(f"""
            color: {THEME_V2.error};
            font-size: {TOKENS_V2.typography.caption}px;
        """)
        self._error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._error_label.setWordWrap(True)
        self._error_label.hide()
        layout.addWidget(self._error_label)

        # Spacer
        layout.addSpacerItem(
            QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        # Footer links
        footer = QHBoxLayout()
        footer.setContentsMargins(0, TOKENS_V2.spacing.md, 0, 0)

        forgot_link = QLabel('<a href="#">Forgot password?</a>')
        forgot_link.setStyleSheet(
            f"color: {THEME_V2.primary}; font-size: {TOKENS_V2.typography.body}px;"
        )
        forgot_link.setOpenExternalLinks(False)
        footer.addWidget(forgot_link)

        footer.addStretch()

        version_label = QLabel("v3.0.0")
        version_label.setStyleSheet(f"""
            color: {THEME_V2.text_muted};
            font-size: {TOKENS_V2.typography.caption}px;
        """)
        footer.addWidget(version_label)

        layout.addLayout(footer)

        # Set content and buttons (hide default footer for this custom layout)
        self.set_body_widget(content)
        self.set_footer_visible(False)

    def _create_login_form(self) -> QWidget:
        """Create the login form widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(TOKENS_V2.spacing.md)

        # Email field
        email_label = QLabel("Email")
        email_label.setStyleSheet(f"""
            color: {THEME_V2.text_secondary};
            font-size: {TOKENS_V2.typography.body}px;
        """)
        layout.addWidget(email_label)

        self._email_input = QLineEdit()
        self._email_input.setPlaceholderText("Enter your email address")
        self._email_input.setStyleSheet(self._get_input_style())
        layout.addWidget(self._email_input)

        # Password field
        password_label = QLabel("Password")
        password_label.setStyleSheet(f"""
            color: {THEME_V2.text_secondary};
            font-size: {TOKENS_V2.typography.body}px;
        """)
        layout.addWidget(password_label)

        password_container = QHBoxLayout()
        password_container.setSpacing(0)

        self._password_input = QLineEdit()
        self._password_input.setPlaceholderText("Enter your password")
        self._password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._password_input.setStyleSheet(self._get_input_style(border_right=False))
        password_container.addWidget(self._password_input)

        self._show_password_btn = QPushButton("Show")
        self._show_password_btn.setCheckable(True)
        self._show_password_btn.setStyleSheet(f"""
            QPushButton {{
                background: {THEME_V2.bg_input};
                border: 1px solid {THEME_V2.border};
                border-left: none;
                border-top-right-radius: {TOKENS_V2.radius.md}px;
                border-bottom-right-radius: {TOKENS_V2.radius.md}px;
                padding: {TOKENS_V2.spacing.md}px 12px;
                color: {THEME_V2.text_muted};
                font-size: {TOKENS_V2.typography.body}px;
                min-height: {TOKENS_V2.sizes.input_md}px;
            }}
            QPushButton:hover {{
                color: {THEME_V2.text_primary};
            }}
            QPushButton:checked {{
                color: {THEME_V2.primary};
            }}
        """)
        password_container.addWidget(self._show_password_btn)
        layout.addLayout(password_container)

        # Remember me checkbox
        self._remember_checkbox = QCheckBox("Remember me")
        self._remember_checkbox.setStyleSheet(f"""
            QCheckBox {{
                color: {THEME_V2.text_secondary};
                font-size: {TOKENS_V2.typography.body}px;
                spacing: {TOKENS_V2.spacing.sm}px;
            }}
        """)
        layout.addWidget(self._remember_checkbox)

        layout.addSpacing(TOKENS_V2.spacing.sm)

        # Login button
        self._login_btn = QPushButton("Sign In")
        self._login_btn.setStyleSheet(f"""
            QPushButton {{
                background: {THEME_V2.primary};
                border: none;
                border-radius: {TOKENS_V2.radius.md}px;
                padding: 0 20px;
                color: white;
                font-size: {TOKENS_V2.typography.body}px;
                font-weight: {TOKENS_V2.typography.weight_semibold};
                min-height: 36px;
            }}
            QPushButton:hover {{
                background: {THEME_V2.primary_hover};
            }}
            QPushButton:pressed {{
                background: {THEME_V2.primary_active};
            }}
        """)
        self._login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self._login_btn)

        return widget

    def _create_mfa_form(self) -> QWidget:
        """Create the MFA verification form widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(TOKENS_V2.spacing.md)

        # MFA header
        mfa_header = QLabel("Two-Factor Authentication")
        mfa_header.setStyleSheet(f"""
            font-size: {TOKENS_V2.typography.heading_lg}px;
            font-weight: {TOKENS_V2.typography.weight_bold};
            color: {THEME_V2.text_primary};
        """)
        mfa_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(mfa_header)

        mfa_subtitle = QLabel("Enter the 6-digit code from your authenticator app")
        mfa_subtitle.setStyleSheet(f"""
            color: {THEME_V2.text_muted};
            font-size: {TOKENS_V2.typography.body}px;
        """)
        mfa_subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mfa_subtitle.setWordWrap(True)
        layout.addWidget(mfa_subtitle)

        layout.addSpacing(TOKENS_V2.spacing.md)

        # MFA code input
        self._mfa_input = QLineEdit()
        self._mfa_input.setPlaceholderText("000000")
        self._mfa_input.setMaxLength(6)
        self._mfa_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._mfa_input.setStyleSheet(f"""
            QLineEdit {{
                background: {THEME_V2.bg_input};
                border: 1px solid {THEME_V2.border};
                border-radius: {TOKENS_V2.radius.md}px;
                padding: {TOKENS_V2.spacing.lg}px;
                color: {THEME_V2.text_primary};
                font-size: 24px;
                font-family: monospace;
                letter-spacing: 8px;
            }}
            QLineEdit:focus {{
                border-color: {THEME_V2.border_focus};
            }}
        """)
        layout.addWidget(self._mfa_input)

        layout.addSpacing(TOKENS_V2.spacing.md)

        # Verify button
        self._verify_btn = QPushButton("Verify")
        self._verify_btn.setStyleSheet(f"""
            QPushButton {{
                background: {THEME_V2.primary};
                border: none;
                border-radius: {TOKENS_V2.radius.md}px;
                padding: 0 20px;
                color: white;
                font-size: {TOKENS_V2.typography.body}px;
                font-weight: {TOKENS_V2.typography.weight_semibold};
                min-height: 36px;
            }}
            QPushButton:hover {{
                background: {THEME_V2.primary_hover};
            }}
            QPushButton:pressed {{
                background: {THEME_V2.primary_active};
            }}
        """)
        self._verify_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self._verify_btn)

        # Back button
        self._back_btn = QPushButton("Back to Login")
        self._back_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 1px solid {THEME_V2.border};
                border-radius: {TOKENS_V2.radius.md}px;
                padding: 0 20px;
                color: {THEME_V2.text_primary};
                font-size: {TOKENS_V2.typography.body}px;
                font-weight: {TOKENS_V2.typography.weight_medium};
                min-height: 36px;
            }}
            QPushButton:hover {{
                background: {THEME_V2.bg_hover};
                border-color: {THEME_V2.primary};
            }}
        """)
        self._back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self._back_btn)

        return widget

    def _get_input_style(self, border_right: bool = True) -> str:
        """Get input field style."""
        border_radius = (
            f"{TOKENS_V2.radius.md}px"
            if border_right
            else f"{TOKENS_V2.radius.md}px 0 0 {TOKENS_V2.radius.md}px"
        )
        return f"""
            QLineEdit {{
                background: {THEME_V2.bg_input};
                border: 1px solid {THEME_V2.border};
                border-radius: {border_radius};
                padding: {TOKENS_V2.spacing.md}px 12px;
                color: {THEME_V2.text_primary};
                font-size: {TOKENS_V2.typography.body}px;
                min-height: {TOKENS_V2.sizes.input_md}px;
            }}
            QLineEdit:focus {{
                border-color: {THEME_V2.border_focus};
            }}
        """

    def _connect_signals(self) -> None:
        """Connect UI signals."""
        self._login_btn.clicked.connect(self._on_login_clicked)
        self._verify_btn.clicked.connect(self._on_verify_clicked)
        self._back_btn.clicked.connect(self._on_back_clicked)
        self._show_password_btn.toggled.connect(self._on_show_password_toggled)
        self._password_input.returnPressed.connect(self._on_login_clicked)
        self._mfa_input.returnPressed.connect(self._on_verify_clicked)

    def _on_login_clicked(self) -> None:
        """Handle login button click."""
        email = self._email_input.text().strip()
        password = self._password_input.text()

        # Validate inputs
        if not email:
            self._show_error("Please enter your email address")
            self._email_input.setFocus()
            return

        if not password:
            self._show_error("Please enter your password")
            self._password_input.setFocus()
            return

        # Clear previous errors
        self._hide_error()

        # Disable login button during authentication
        self._login_btn.setEnabled(False)
        self._login_btn.setText("Signing in...")

        # Emit credentials for external authentication handling
        # The parent should connect to handle_login and call set_auth_result
        self._current_email = email
        self._current_password = password

        # For now, simulate success (real auth handled by parent)
        # Parent should call: dialog.authenticate(email, password, user_manager, token_manager)
        self._login_btn.setEnabled(True)
        self._login_btn.setText("Sign In")

    def authenticate(
        self,
        user_manager,
        token_manager,
    ) -> None:
        """
        Perform authentication with the provided managers.

        Args:
            user_manager: UserManager instance
            token_manager: TokenManager instance
        """
        import asyncio

        email = self._email_input.text().strip()
        password = self._password_input.text()

        async def do_auth():
            try:
                result = await user_manager.authenticate(email, password)

                if result.success:
                    self._authenticated_user = result.user
                    self._access_token = token_manager.generate_access_token(result.user)
                    self.accept()
                elif result.needs_mfa:
                    self._authenticated_user = result.user
                    self._pending_mfa = True
                    self._show_mfa_step()
                else:
                    self._show_error(result.message or "Authentication failed")

            except Exception as e:
                self._show_error(f"Login error: {e}")

        # Run async authentication
        try:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(do_auth())
        except RuntimeError:
            asyncio.run(do_auth())

    def set_auth_result(
        self,
        success: bool,
        user=None,
        token: str | None = None,
        requires_mfa: bool = False,
        error_message: str | None = None,
    ) -> None:
        """
        Set authentication result from external handler.

        Args:
            success: Whether authentication succeeded
            user: Authenticated user object
            token: Access token
            requires_mfa: Whether MFA step is needed
            error_message: Error message if failed
        """
        self._login_btn.setEnabled(True)
        self._login_btn.setText("Sign In")

        if success and not requires_mfa:
            self._authenticated_user = user
            self._access_token = token
            self.login_successful.emit(user, token)
            self.accept()
        elif requires_mfa:
            self._authenticated_user = user
            self._pending_mfa = True
            self._show_mfa_step()
        else:
            self._show_error(error_message or "Authentication failed")
            self.login_failed.emit(error_message or "Authentication failed")

    def _show_mfa_step(self) -> None:
        """Show MFA verification step."""
        self._hide_error()
        self._mfa_input.clear()
        self._stack.setCurrentWidget(self._mfa_widget)
        self._mfa_input.setFocus()

    def _on_verify_clicked(self) -> None:
        """Handle MFA verify button click."""
        code = self._mfa_input.text().strip()

        if not code or len(code) != 6:
            self._show_error("Please enter a valid 6-digit code")
            return

        self._hide_error()
        self._verify_btn.setEnabled(False)
        self._verify_btn.setText("Verifying...")

        # Emit for external MFA verification
        # Parent should connect and call set_mfa_result

    def verify_mfa(self, totp_manager, token_manager) -> None:
        """
        Verify MFA code with provided managers.

        Args:
            totp_manager: TOTPManager instance
            token_manager: TokenManager instance
        """
        code = self._mfa_input.text().strip()

        if not self._authenticated_user or not self._authenticated_user.mfa_secret:
            self._show_error("MFA verification error")
            return

        # Verify TOTP code
        if totp_manager.verify_code(self._authenticated_user.mfa_secret, code):
            self._access_token = token_manager.generate_access_token(
                self._authenticated_user,
                mfa_verified=True,
            )
            self.accept()
        else:
            self._show_error("Invalid verification code")
            self._verify_btn.setEnabled(True)
            self._verify_btn.setText("Verify")

    def set_mfa_result(
        self,
        success: bool,
        token: str | None = None,
        error_message: str | None = None,
    ) -> None:
        """
        Set MFA verification result from external handler.

        Args:
            success: Whether MFA succeeded
            token: Access token (with MFA verified)
            error_message: Error message if failed
        """
        self._verify_btn.setEnabled(True)
        self._verify_btn.setText("Verify")

        if success:
            self._access_token = token
            self.login_successful.emit(self._authenticated_user, token)
            self.accept()
        else:
            self._show_error(error_message or "Invalid verification code")

    def _on_back_clicked(self) -> None:
        """Handle back button click."""
        self._pending_mfa = False
        self._authenticated_user = None
        self._hide_error()
        self._stack.setCurrentWidget(self._login_widget)
        self._password_input.clear()
        self._email_input.setFocus()

    def _on_show_password_toggled(self, checked: bool) -> None:
        """Toggle password visibility."""
        if checked:
            self._password_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self._show_password_btn.setText("Hide")
        else:
            self._password_input.setEchoMode(QLineEdit.EchoMode.Password)
            self._show_password_btn.setText("Show")

    def _show_error(self, message: str) -> None:
        """Show error message."""
        self._error_label.setText(message)
        self._error_label.show()

    def _hide_error(self) -> None:
        """Hide error message."""
        self._error_label.clear()
        self._error_label.hide()


__all__ = ["LoginDialog"]
