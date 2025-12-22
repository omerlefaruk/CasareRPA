"""
Setup Wizard for CasareRPA Client.

First-run configuration wizard that guides users through:
1. Welcome and overview
2. Orchestrator connection setup
3. Robot configuration
4. Capability selection
5. Summary and completion

Triggered automatically when config file is missing or first_run_complete is False.
"""

import asyncio
import socket
from typing import Optional

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import (
    QWizard,
    QWizardPage,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QLineEdit,
    QCheckBox,
    QSpinBox,
    QComboBox,
    QGroupBox,
    QPushButton,
    QTextEdit,
    QProgressBar,
    QFrame,
)

from loguru import logger

from casare_rpa.presentation.setup.config_manager import (
    ClientConfig,
    ClientConfigManager,
)


class SetupWizard(QWizard):
    """
    First-run setup wizard for CasareRPA client.

    Guides users through initial configuration of orchestrator connection
    and robot settings. Saves configuration to APPDATA/CasareRPA/config.yaml.

    Signals:
        setup_complete: Emitted when setup finishes successfully (config: ClientConfig)
        setup_cancelled: Emitted when user cancels setup
    """

    setup_complete = Signal(object)  # ClientConfig
    setup_cancelled = Signal()

    PAGE_WELCOME = 0
    PAGE_ORCHESTRATOR = 1
    PAGE_ROBOT = 2
    PAGE_CAPABILITIES = 3
    PAGE_SUMMARY = 4

    def __init__(
        self,
        config_manager: Optional[ClientConfigManager] = None,
        parent=None,
    ) -> None:
        """
        Initialize setup wizard.

        Args:
            config_manager: Configuration manager instance
            parent: Parent widget
        """
        super().__init__(parent)

        self.config_manager = config_manager or ClientConfigManager()
        self.config = self.config_manager.create_default()

        self._setup_wizard()
        self._add_pages()
        self._apply_styles()

        logger.info("Setup wizard initialized")

    def _setup_wizard(self) -> None:
        """Configure wizard appearance and behavior."""
        self.setWindowTitle("CasareRPA Setup")
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.setOption(QWizard.WizardOption.NoBackButtonOnStartPage)
        self.setOption(QWizard.WizardOption.HaveHelpButton, False)

        self.setMinimumSize(700, 500)

        # Set button text
        self.setButtonText(QWizard.WizardButton.NextButton, "Next >")
        self.setButtonText(QWizard.WizardButton.BackButton, "< Back")
        self.setButtonText(QWizard.WizardButton.FinishButton, "Finish")
        self.setButtonText(QWizard.WizardButton.CancelButton, "Cancel")

    def _add_pages(self) -> None:
        """Add wizard pages."""
        self.welcome_page = WelcomePage(self)
        self.orchestrator_page = OrchestratorPage(self.config_manager, self)
        self.robot_page = RobotConfigPage(self)
        self.capabilities_page = CapabilitiesPage(self)
        self.summary_page = SummaryPage(self)

        self.addPage(self.welcome_page)
        self.addPage(self.orchestrator_page)
        self.addPage(self.robot_page)
        self.addPage(self.capabilities_page)
        self.addPage(self.summary_page)

    def _apply_styles(self) -> None:
        """Apply dark theme styling."""
        self.setStyleSheet("""
            QWizard {
                background-color: #1e1e1e;
            }
            QWizardPage {
                background-color: #1e1e1e;
                color: #e0e0e0;
            }
            QLabel {
                color: #e0e0e0;
            }
            QLineEdit, QTextEdit, QSpinBox, QComboBox {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                color: #e0e0e0;
                padding: 6px;
                min-height: 20px;
            }
            QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QComboBox:focus {
                border: 1px solid #5a8a9a;
            }
            QLineEdit:disabled, QTextEdit:disabled {
                background-color: #252525;
                color: #808080;
            }
            QGroupBox {
                border: 1px solid #3d3d3d;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 12px;
                font-weight: bold;
                color: #e0e0e0;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QCheckBox {
                color: #e0e0e0;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 1px solid #4a4a4a;
                border-radius: 3px;
                background-color: #2d2d2d;
            }
            QCheckBox::indicator:checked {
                background-color: #5a8a9a;
                border-color: #5a8a9a;
            }
            QPushButton {
                background-color: #3d3d3d;
                border: 1px solid #4a4a4a;
                border-radius: 4px;
                color: #e0e0e0;
                padding: 8px 16px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
            }
            QPushButton:pressed {
                background-color: #5a8a9a;
            }
            QPushButton:disabled {
                background-color: #2d2d2d;
                color: #606060;
            }
            QProgressBar {
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                text-align: center;
                background-color: #2d2d2d;
            }
            QProgressBar::chunk {
                background-color: #5a8a9a;
                border-radius: 3px;
            }
        """)

    def accept(self) -> None:
        """Handle wizard completion."""
        # Gather configuration from pages
        self._gather_config()

        # Mark setup as complete
        self.config.first_run_complete = True

        # Save configuration
        try:
            self.config_manager.save(self.config)
            logger.info("Setup wizard completed successfully")
            self.setup_complete.emit(self.config)
            super().accept()

        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            # Show error but still accept (user can fix config manually)
            super().accept()

    def reject(self) -> None:
        """Handle wizard cancellation."""
        logger.info("Setup wizard cancelled")
        self.setup_cancelled.emit()
        super().reject()

    def _gather_config(self) -> None:
        """Gather configuration from all pages."""
        # Orchestrator page
        self.config.orchestrator.url = self.orchestrator_page.url_edit.text().strip()
        self.config.orchestrator.api_key = self.orchestrator_page.api_key_edit.text().strip()

        # Robot page
        self.config.robot.name = self.robot_page.name_edit.text().strip()
        self.config.robot.max_concurrent_jobs = self.robot_page.concurrent_spin.value()
        self.config.robot.environment = self.robot_page.env_combo.currentText().lower()
        self.config.logging.level = self.robot_page.log_level_combo.currentText()

        # Capabilities page
        capabilities = []
        if self.capabilities_page.browser_check.isChecked():
            capabilities.append("browser")
        if self.capabilities_page.desktop_check.isChecked():
            capabilities.append("desktop")
        if self.capabilities_page.high_memory_check.isChecked():
            capabilities.append("high_memory")
        if self.capabilities_page.gpu_check.isChecked():
            capabilities.append("gpu")
        if self.capabilities_page.secure_check.isChecked():
            capabilities.append("secure")
        if self.capabilities_page.on_premise_check.isChecked():
            capabilities.append("on_premise")

        self.config.robot.capabilities = capabilities

        # Tags
        tags_text = self.capabilities_page.tags_edit.text().strip()
        if tags_text:
            self.config.robot.tags = [t.strip() for t in tags_text.split(",") if t.strip()]


class WelcomePage(QWizardPage):
    """Welcome page with overview of setup process."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setTitle("Welcome to CasareRPA")
        self.setSubTitle("Let's set up your robot agent")
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # Logo placeholder
        logo_frame = QFrame()
        logo_frame.setFixedSize(120, 120)
        logo_frame.setStyleSheet("""
            QFrame {
                background-color: #2d5a7a;
                border-radius: 60px;
            }
        """)

        logo_layout = QVBoxLayout(logo_frame)
        logo_label = QLabel("RPA")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label.setStyleSheet("font-size: 32px; font-weight: bold; color: white;")
        logo_layout.addWidget(logo_label)

        logo_container = QHBoxLayout()
        logo_container.addStretch()
        logo_container.addWidget(logo_frame)
        logo_container.addStretch()
        layout.addLayout(logo_container)

        # Welcome text
        welcome_text = QLabel(
            "This wizard will help you configure CasareRPA to connect to your "
            "cloud orchestrator and set up the robot agent.\n\n"
            "You will configure:\n"
            "  - Orchestrator connection settings\n"
            "  - Robot name and execution settings\n"
            "  - Capabilities for job matching\n\n"
            "Click 'Next' to begin setup, or 'Cancel' to configure later."
        )
        welcome_text.setWordWrap(True)
        welcome_text.setStyleSheet("font-size: 13px; line-height: 1.5;")
        layout.addWidget(welcome_text)

        # Version info
        version_label = QLabel("CasareRPA v3.0.0")
        version_label.setStyleSheet("color: #808080; font-size: 11px;")
        version_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(version_label)

        layout.addStretch()


class OrchestratorPage(QWizardPage):
    """Orchestrator connection configuration page."""

    def __init__(
        self,
        config_manager: ClientConfigManager,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.config_manager = config_manager
        self.setTitle("Orchestrator Connection")
        self.setSubTitle("Configure connection to CasareRPA Cloud Orchestrator")
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Connection group
        conn_group = QGroupBox("Connection Settings")
        conn_layout = QFormLayout()
        conn_layout.setSpacing(12)

        # URL input
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("wss://orchestrator.example.com/ws/robot")
        self.url_edit.textChanged.connect(self._on_url_changed)
        conn_layout.addRow("Orchestrator URL:", self.url_edit)

        # URL help text
        url_help = QLabel("WebSocket URL provided by your administrator (ws:// or wss://)")
        url_help.setStyleSheet("color: #808080; font-size: 11px;")
        conn_layout.addRow("", url_help)

        # API Key input
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setPlaceholderText("crpa_xxxxxxxxxxxxxxxx")
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_edit.textChanged.connect(self._on_api_key_changed)
        conn_layout.addRow("API Key:", self.api_key_edit)

        # Show/hide API key toggle
        self.show_key_check = QCheckBox("Show API key")
        self.show_key_check.toggled.connect(self._toggle_api_key_visibility)
        conn_layout.addRow("", self.show_key_check)

        conn_group.setLayout(conn_layout)
        layout.addWidget(conn_group)

        # Test connection section
        test_group = QGroupBox("Connection Test")
        test_layout = QVBoxLayout()

        test_row = QHBoxLayout()
        self.test_button = QPushButton("Test Connection")
        self.test_button.clicked.connect(self._test_connection)
        self.test_button.setEnabled(False)
        test_row.addWidget(self.test_button)

        self.test_progress = QProgressBar()
        self.test_progress.setMaximum(0)  # Indeterminate
        self.test_progress.setVisible(False)
        self.test_progress.setFixedWidth(100)
        test_row.addWidget(self.test_progress)

        test_row.addStretch()
        test_layout.addLayout(test_row)

        self.test_result = QLabel("")
        self.test_result.setWordWrap(True)
        test_layout.addWidget(self.test_result)

        test_group.setLayout(test_layout)
        layout.addWidget(test_group)

        # Optional notice
        notice = QLabel(
            "Note: You can skip this step to run in local-only mode. "
            "Configure orchestrator connection later in Settings."
        )
        notice.setWordWrap(True)
        notice.setStyleSheet("color: #5a8a9a; font-size: 11px;")
        layout.addWidget(notice)

        layout.addStretch()

        # Register fields for validation
        self.registerField("orchestrator_url", self.url_edit)
        self.registerField("api_key", self.api_key_edit)

    def _on_url_changed(self, text: str) -> None:
        """Handle URL text changes."""
        self.test_button.setEnabled(bool(text.strip()))
        self.test_result.clear()

    def _on_api_key_changed(self, text: str) -> None:
        """Handle API key text changes."""
        self.test_result.clear()

    def _toggle_api_key_visibility(self, checked: bool) -> None:
        """Toggle API key visibility."""
        mode = QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
        self.api_key_edit.setEchoMode(mode)

    def _test_connection(self) -> None:
        """Test orchestrator connection."""
        url = self.url_edit.text().strip()
        api_key = self.api_key_edit.text().strip()

        # Validate URL format first
        error = self.config_manager.validate_url(url)
        if error:
            self.test_result.setText(f"Error: {error}")
            self.test_result.setStyleSheet("color: #ff6b6b;")
            return

        # Validate API key format
        if api_key:
            error = self.config_manager.validate_api_key(api_key)
            if error:
                self.test_result.setText(f"Error: {error}")
                self.test_result.setStyleSheet("color: #ff6b6b;")
                return

        # Show progress
        self.test_button.setEnabled(False)
        self.test_progress.setVisible(True)
        self.test_result.setText("Testing connection...")
        self.test_result.setStyleSheet("color: #808080;")

        # Run async connection test
        QTimer.singleShot(100, lambda: self._run_connection_test(url, api_key))

    def _run_connection_test(self, url: str, api_key: str) -> None:
        """Run the actual connection test."""
        try:
            loop = asyncio.new_event_loop()
            success, message = loop.run_until_complete(
                self.config_manager.test_connection(url, api_key)
            )
            loop.close()

            if success:
                self.test_result.setText(f"Success: {message}")
                self.test_result.setStyleSheet("color: #4ecdc4;")
            else:
                self.test_result.setText(f"Failed: {message}")
                self.test_result.setStyleSheet("color: #ff6b6b;")

        except Exception as e:
            self.test_result.setText(f"Error: {str(e)}")
            self.test_result.setStyleSheet("color: #ff6b6b;")

        finally:
            self.test_button.setEnabled(True)
            self.test_progress.setVisible(False)

    def isComplete(self) -> bool:
        """Check if page is complete. Allow empty URL for local-only mode."""
        return True  # URL is optional


class RobotConfigPage(QWizardPage):
    """Robot configuration page."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setTitle("Robot Configuration")
        self.setSubTitle("Configure robot identity and execution settings")
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Identity group
        identity_group = QGroupBox("Robot Identity")
        identity_layout = QFormLayout()
        identity_layout.setSpacing(12)

        # Robot name
        self.name_edit = QLineEdit()
        hostname = socket.gethostname()
        self.name_edit.setText(f"{hostname}-Robot")
        self.name_edit.setPlaceholderText("Enter robot name")
        identity_layout.addRow("Robot Name:", self.name_edit)

        name_help = QLabel("Unique name for this robot. Used in orchestrator dashboard.")
        name_help.setStyleSheet("color: #808080; font-size: 11px;")
        identity_layout.addRow("", name_help)

        # Environment
        self.env_combo = QComboBox()
        self.env_combo.addItems(["Production", "Staging", "Development"])
        identity_layout.addRow("Environment:", self.env_combo)

        identity_group.setLayout(identity_layout)
        layout.addWidget(identity_group)

        # Execution group
        exec_group = QGroupBox("Execution Settings")
        exec_layout = QFormLayout()
        exec_layout.setSpacing(12)

        # Max concurrent jobs
        self.concurrent_spin = QSpinBox()
        self.concurrent_spin.setMinimum(1)
        self.concurrent_spin.setMaximum(10)
        self.concurrent_spin.setValue(2)
        exec_layout.addRow("Max Concurrent Jobs:", self.concurrent_spin)

        concurrent_help = QLabel("Number of workflows this robot can execute simultaneously")
        concurrent_help.setStyleSheet("color: #808080; font-size: 11px;")
        exec_layout.addRow("", concurrent_help)

        # Log level
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.log_level_combo.setCurrentText("INFO")
        exec_layout.addRow("Log Level:", self.log_level_combo)

        exec_group.setLayout(exec_layout)
        layout.addWidget(exec_group)

        layout.addStretch()

        # Register fields
        self.registerField("robot_name*", self.name_edit)

    def isComplete(self) -> bool:
        """Check if page is complete."""
        return bool(self.name_edit.text().strip())


class CapabilitiesPage(QWizardPage):
    """Robot capabilities configuration page."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setTitle("Robot Capabilities")
        self.setSubTitle("Select capabilities for job matching")
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Description
        desc = QLabel(
            "Capabilities are used by the orchestrator to match jobs to appropriate robots. "
            "Select the capabilities this robot supports."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #a0a0a0;")
        layout.addWidget(desc)

        # Core capabilities group
        core_group = QGroupBox("Core Capabilities")
        core_layout = QVBoxLayout()

        self.browser_check = QCheckBox("Browser Automation (Playwright)")
        self.browser_check.setChecked(True)
        self.browser_check.setToolTip("Web automation using Playwright")
        core_layout.addWidget(self.browser_check)

        self.desktop_check = QCheckBox("Desktop Automation (UIAutomation)")
        self.desktop_check.setChecked(True)
        self.desktop_check.setToolTip("Windows desktop automation")
        core_layout.addWidget(self.desktop_check)

        core_group.setLayout(core_layout)
        layout.addWidget(core_group)

        # Resource capabilities group
        resource_group = QGroupBox("Resource Capabilities")
        resource_layout = QVBoxLayout()

        self.high_memory_check = QCheckBox("High Memory (8GB+ RAM)")
        self.high_memory_check.setToolTip("Robot has 8GB or more RAM available")
        resource_layout.addWidget(self.high_memory_check)

        self.gpu_check = QCheckBox("GPU Available")
        self.gpu_check.setToolTip("Robot has GPU for accelerated processing")
        resource_layout.addWidget(self.gpu_check)

        resource_group.setLayout(resource_layout)
        layout.addWidget(resource_group)

        # Environment capabilities group
        env_group = QGroupBox("Environment Capabilities")
        env_layout = QVBoxLayout()

        self.secure_check = QCheckBox("Secure Environment")
        self.secure_check.setToolTip("Robot is in a secure/isolated environment")
        env_layout.addWidget(self.secure_check)

        self.on_premise_check = QCheckBox("On-Premise")
        self.on_premise_check.setChecked(True)
        self.on_premise_check.setToolTip("Robot is running on-premise (not cloud)")
        env_layout.addWidget(self.on_premise_check)

        env_group.setLayout(env_layout)
        layout.addWidget(env_group)

        # Tags group
        tags_group = QGroupBox("Tags")
        tags_layout = QVBoxLayout()

        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("finance, hr, reports (comma-separated)")
        tags_layout.addWidget(self.tags_edit)

        tags_help = QLabel("Optional tags for filtering robots in orchestrator")
        tags_help.setStyleSheet("color: #808080; font-size: 11px;")
        tags_layout.addWidget(tags_help)

        tags_group.setLayout(tags_layout)
        layout.addWidget(tags_group)

        layout.addStretch()

        # Auto-detect capabilities
        self._auto_detect_capabilities()

    def _auto_detect_capabilities(self) -> None:
        """Auto-detect system capabilities."""
        import platform

        # Check for high memory
        try:
            import psutil

            mem_gb = psutil.virtual_memory().total / (1024**3)
            self.high_memory_check.setChecked(mem_gb >= 8)
        except ImportError:
            pass

        # Desktop only on Windows
        if platform.system() != "Windows":
            self.desktop_check.setChecked(False)
            self.desktop_check.setEnabled(False)
            self.on_premise_check.setChecked(False)


class SummaryPage(QWizardPage):
    """Summary page showing configuration overview."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setTitle("Configuration Summary")
        self.setSubTitle("Review your settings before completing setup")
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Summary text area
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setStyleSheet("""
            QTextEdit {
                background-color: #252525;
                border: 1px solid #3d3d3d;
                border-radius: 6px;
                font-family: Consolas, monospace;
                font-size: 12px;
                padding: 12px;
            }
        """)
        layout.addWidget(self.summary_text)

        # Config file location
        config_location = QLabel(
            f"Configuration will be saved to:\n"
            f"{ClientConfigManager.DEFAULT_CONFIG_DIR / 'config.yaml'}"
        )
        config_location.setStyleSheet("color: #808080; font-size: 11px;")
        config_location.setWordWrap(True)
        layout.addWidget(config_location)

    def initializePage(self) -> None:
        """Initialize page when shown."""
        wizard = self.wizard()
        if not wizard:
            return

        # Build summary text
        lines = []
        lines.append("ORCHESTRATOR CONNECTION")
        lines.append("-" * 40)

        url = wizard.orchestrator_page.url_edit.text().strip()
        if url:
            lines.append(f"URL: {url}")
            api_key = wizard.orchestrator_page.api_key_edit.text().strip()
            if api_key:
                lines.append(f"API Key: {api_key[:10]}...{api_key[-4:]}")
            else:
                lines.append("API Key: (not set)")
        else:
            lines.append("Mode: Local-only (no orchestrator)")

        lines.append("")
        lines.append("ROBOT CONFIGURATION")
        lines.append("-" * 40)
        lines.append(f"Name: {wizard.robot_page.name_edit.text()}")
        lines.append(f"Environment: {wizard.robot_page.env_combo.currentText()}")
        lines.append(f"Max Concurrent Jobs: {wizard.robot_page.concurrent_spin.value()}")
        lines.append(f"Log Level: {wizard.robot_page.log_level_combo.currentText()}")

        lines.append("")
        lines.append("CAPABILITIES")
        lines.append("-" * 40)
        caps = []
        if wizard.capabilities_page.browser_check.isChecked():
            caps.append("browser")
        if wizard.capabilities_page.desktop_check.isChecked():
            caps.append("desktop")
        if wizard.capabilities_page.high_memory_check.isChecked():
            caps.append("high_memory")
        if wizard.capabilities_page.gpu_check.isChecked():
            caps.append("gpu")
        if wizard.capabilities_page.secure_check.isChecked():
            caps.append("secure")
        if wizard.capabilities_page.on_premise_check.isChecked():
            caps.append("on_premise")

        lines.append(f"Capabilities: {', '.join(caps) if caps else '(none)'}")

        tags = wizard.capabilities_page.tags_edit.text().strip()
        lines.append(f"Tags: {tags if tags else '(none)'}")

        self.summary_text.setPlainText("\n".join(lines))


def show_setup_wizard_if_needed(parent=None) -> Optional[ClientConfig]:
    """
    Show setup wizard if first-run configuration is needed.

    Args:
        parent: Parent widget for the wizard

    Returns:
        ClientConfig if setup completed, None if cancelled or not needed
    """
    config_manager = ClientConfigManager()

    if not config_manager.needs_setup():
        logger.debug("Setup not needed, config exists and is complete")
        return config_manager.load()

    logger.info("First-run setup needed, showing wizard")

    wizard = SetupWizard(config_manager, parent)
    result = wizard.exec()

    if result == QWizard.DialogCode.Accepted:
        return wizard.config
    else:
        return None
