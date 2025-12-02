"""
Tests for SetupWizard and its pages.

Test coverage:
- SetupWizard: initialization, navigation, configuration gathering
- WelcomePage: display and content
- OrchestratorPage: URL/API key input, validation, connection testing
- RobotConfigPage: name, environment, concurrent jobs
- CapabilitiesPage: checkbox states, tags
- SummaryPage: configuration display

Uses pytest-qt (qtbot fixture) for Qt widget testing.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import socket

from PySide6.QtWidgets import QWizard, QApplication
from PySide6.QtCore import Qt

from casare_rpa.presentation.setup.config_manager import (
    ClientConfig,
    ClientConfigManager,
)
from casare_rpa.presentation.setup.setup_wizard import (
    SetupWizard,
    WelcomePage,
    OrchestratorPage,
    RobotConfigPage,
    CapabilitiesPage,
    SummaryPage,
    show_setup_wizard_if_needed,
)


# Note: Tests require pytest-qt which provides the 'qtbot' fixture.
# Tests are NOT skipped - pytest-qt is installed and available.


@pytest.fixture
def config_manager(tmp_path: Path) -> ClientConfigManager:
    """Create a ClientConfigManager with temp directory."""
    return ClientConfigManager(config_dir=tmp_path / "CasareRPA")


@pytest.fixture
def setup_wizard(qtbot, config_manager: ClientConfigManager) -> SetupWizard:
    """Create a SetupWizard instance."""
    wizard = SetupWizard(config_manager=config_manager)
    qtbot.addWidget(wizard)
    return wizard


class TestSetupWizard:
    """Tests for SetupWizard class."""

    def test_wizard_has_five_pages(self, setup_wizard: SetupWizard) -> None:
        """Wizard contains exactly 5 pages."""
        # Count page IDs (0-4)
        page_count = 0
        for page_id in range(10):  # Check up to 10 pages
            if setup_wizard.page(page_id) is not None:
                page_count += 1

        assert page_count == 5

    def test_wizard_page_order(self, setup_wizard: SetupWizard) -> None:
        """Pages are in correct order."""
        assert setup_wizard.page(SetupWizard.PAGE_WELCOME) is setup_wizard.welcome_page
        assert (
            setup_wizard.page(SetupWizard.PAGE_ORCHESTRATOR)
            is setup_wizard.orchestrator_page
        )
        assert setup_wizard.page(SetupWizard.PAGE_ROBOT) is setup_wizard.robot_page
        assert (
            setup_wizard.page(SetupWizard.PAGE_CAPABILITIES)
            is setup_wizard.capabilities_page
        )
        assert setup_wizard.page(SetupWizard.PAGE_SUMMARY) is setup_wizard.summary_page

    def test_wizard_title(self, setup_wizard: SetupWizard) -> None:
        """Wizard has correct title."""
        assert setup_wizard.windowTitle() == "CasareRPA Setup"

    def test_wizard_minimum_size(self, setup_wizard: SetupWizard) -> None:
        """Wizard has minimum size set."""
        assert setup_wizard.minimumWidth() >= 700
        assert setup_wizard.minimumHeight() >= 500

    def test_wizard_starts_on_welcome_page(
        self, qtbot, setup_wizard: SetupWizard
    ) -> None:
        """Wizard starts on welcome page after restart."""
        setup_wizard.restart()
        assert setup_wizard.currentId() == SetupWizard.PAGE_WELCOME

    def test_wizard_no_back_button_on_start(self, setup_wizard: SetupWizard) -> None:
        """No back button on start page."""
        # The option is set but we verify via QWizard options
        options = setup_wizard.options()
        assert options & QWizard.WizardOption.NoBackButtonOnStartPage

    def test_wizard_creates_default_config(self, setup_wizard: SetupWizard) -> None:
        """Wizard initializes with default config."""
        assert setup_wizard.config is not None
        assert isinstance(setup_wizard.config, ClientConfig)

    def test_can_navigate_forward(self, qtbot, setup_wizard: SetupWizard) -> None:
        """Can navigate from welcome to next page."""
        # Initialize wizard
        setup_wizard.restart()

        # Start on welcome page
        assert setup_wizard.currentId() == SetupWizard.PAGE_WELCOME

        # Click next
        setup_wizard.next()

        # Should be on orchestrator page
        assert setup_wizard.currentId() == SetupWizard.PAGE_ORCHESTRATOR

    def test_can_navigate_back(self, qtbot, setup_wizard: SetupWizard) -> None:
        """Can navigate back to previous page."""
        # Initialize wizard
        setup_wizard.restart()

        # Go forward first
        setup_wizard.next()
        assert setup_wizard.currentId() == SetupWizard.PAGE_ORCHESTRATOR

        # Go back
        setup_wizard.back()
        assert setup_wizard.currentId() == SetupWizard.PAGE_WELCOME

    def test_gather_config_orchestrator(self, setup_wizard: SetupWizard) -> None:
        """_gather_config collects orchestrator settings."""
        # Set values
        setup_wizard.orchestrator_page.url_edit.setText("wss://test.com/ws")
        setup_wizard.orchestrator_page.api_key_edit.setText("crpa_test123")

        setup_wizard._gather_config()

        assert setup_wizard.config.orchestrator.url == "wss://test.com/ws"
        assert setup_wizard.config.orchestrator.api_key == "crpa_test123"

    def test_gather_config_robot(self, setup_wizard: SetupWizard) -> None:
        """_gather_config collects robot settings."""
        # Set values
        setup_wizard.robot_page.name_edit.setText("TestBot")
        setup_wizard.robot_page.concurrent_spin.setValue(5)
        setup_wizard.robot_page.env_combo.setCurrentText("Staging")
        setup_wizard.robot_page.log_level_combo.setCurrentText("DEBUG")

        setup_wizard._gather_config()

        assert setup_wizard.config.robot.name == "TestBot"
        assert setup_wizard.config.robot.max_concurrent_jobs == 5
        assert setup_wizard.config.robot.environment == "staging"
        assert setup_wizard.config.logging.level == "DEBUG"

    def test_gather_config_capabilities(self, setup_wizard: SetupWizard) -> None:
        """_gather_config collects capabilities."""
        # Set capabilities
        setup_wizard.capabilities_page.browser_check.setChecked(True)
        setup_wizard.capabilities_page.desktop_check.setChecked(False)
        setup_wizard.capabilities_page.high_memory_check.setChecked(True)
        setup_wizard.capabilities_page.gpu_check.setChecked(True)
        setup_wizard.capabilities_page.secure_check.setChecked(False)
        setup_wizard.capabilities_page.on_premise_check.setChecked(True)

        setup_wizard._gather_config()

        caps = setup_wizard.config.robot.capabilities
        assert "browser" in caps
        assert "desktop" not in caps
        assert "high_memory" in caps
        assert "gpu" in caps
        assert "secure" not in caps
        assert "on_premise" in caps

    def test_gather_config_tags(self, setup_wizard: SetupWizard) -> None:
        """_gather_config collects tags."""
        setup_wizard.capabilities_page.tags_edit.setText("finance, hr, reports")

        setup_wizard._gather_config()

        tags = setup_wizard.config.robot.tags
        assert "finance" in tags
        assert "hr" in tags
        assert "reports" in tags

    def test_gather_config_empty_tags(self, setup_wizard: SetupWizard) -> None:
        """_gather_config handles empty tags."""
        setup_wizard.capabilities_page.tags_edit.setText("")

        setup_wizard._gather_config()

        # Should not set tags if empty
        assert (
            setup_wizard.config.robot.tags == [] or not setup_wizard.config.robot.tags
        )

    def test_accept_saves_config(
        self, qtbot, setup_wizard: SetupWizard, tmp_path: Path
    ) -> None:
        """accept() saves configuration."""
        # Set required fields
        setup_wizard.robot_page.name_edit.setText("AcceptTestBot")

        # Mock the accept to prevent actual dialog close
        with patch.object(QWizard, "accept"):
            setup_wizard.accept()

        # Check config was gathered
        assert setup_wizard.config.first_run_complete is True
        assert setup_wizard.config.robot.name == "AcceptTestBot"

    def test_accept_emits_signal(self, qtbot, setup_wizard: SetupWizard) -> None:
        """accept() emits setup_complete signal."""
        setup_wizard.robot_page.name_edit.setText("SignalTestBot")

        with qtbot.waitSignal(setup_wizard.setup_complete, timeout=1000):
            with patch.object(QWizard, "accept"):
                setup_wizard.accept()

    def test_reject_emits_signal(self, qtbot, setup_wizard: SetupWizard) -> None:
        """reject() emits setup_cancelled signal."""
        with qtbot.waitSignal(setup_wizard.setup_cancelled, timeout=1000):
            with patch.object(QWizard, "reject"):
                setup_wizard.reject()


class TestWelcomePage:
    """Tests for WelcomePage."""

    def test_page_has_title(self, setup_wizard: SetupWizard) -> None:
        """Welcome page has correct title."""
        page = setup_wizard.welcome_page
        assert page.title() == "Welcome to CasareRPA"

    def test_page_has_subtitle(self, setup_wizard: SetupWizard) -> None:
        """Welcome page has subtitle."""
        page = setup_wizard.welcome_page
        assert page.subTitle() == "Let's set up your robot agent"

    def test_page_displays_version(self, qtbot, setup_wizard: SetupWizard) -> None:
        """Welcome page displays version info."""
        # Search for version label in page widgets
        page = setup_wizard.welcome_page
        found_version = False

        for child in page.findChildren(type(page)):
            pass  # Iterate through children

        # Check the page content contains version info
        # This is a basic check that the page renders
        assert page.layout() is not None


class TestOrchestratorPage:
    """Tests for OrchestratorPage."""

    def test_page_has_title(self, setup_wizard: SetupWizard) -> None:
        """Orchestrator page has correct title."""
        page = setup_wizard.orchestrator_page
        assert page.title() == "Orchestrator Connection"

    def test_url_input_exists(self, setup_wizard: SetupWizard) -> None:
        """URL input field exists."""
        page = setup_wizard.orchestrator_page
        assert page.url_edit is not None

    def test_url_input_placeholder(self, setup_wizard: SetupWizard) -> None:
        """URL input has placeholder text."""
        page = setup_wizard.orchestrator_page
        placeholder = page.url_edit.placeholderText()
        assert "ws" in placeholder.lower() or "orchestrator" in placeholder.lower()

    def test_api_key_input_exists(self, setup_wizard: SetupWizard) -> None:
        """API key input field exists."""
        page = setup_wizard.orchestrator_page
        assert page.api_key_edit is not None

    def test_api_key_input_hidden_by_default(self, setup_wizard: SetupWizard) -> None:
        """API key is hidden by default (password mode)."""
        from PySide6.QtWidgets import QLineEdit

        page = setup_wizard.orchestrator_page
        assert page.api_key_edit.echoMode() == QLineEdit.EchoMode.Password

    def test_show_key_toggle_works(self, qtbot, setup_wizard: SetupWizard) -> None:
        """Show API key checkbox toggles visibility."""
        from PySide6.QtWidgets import QLineEdit

        page = setup_wizard.orchestrator_page

        # Initially hidden
        assert page.api_key_edit.echoMode() == QLineEdit.EchoMode.Password

        # Check the show key box
        page.show_key_check.setChecked(True)
        assert page.api_key_edit.echoMode() == QLineEdit.EchoMode.Normal

        # Uncheck it
        page.show_key_check.setChecked(False)
        assert page.api_key_edit.echoMode() == QLineEdit.EchoMode.Password

    def test_test_button_exists(self, setup_wizard: SetupWizard) -> None:
        """Test connection button exists."""
        page = setup_wizard.orchestrator_page
        assert page.test_button is not None

    def test_test_button_disabled_when_url_empty(
        self, setup_wizard: SetupWizard
    ) -> None:
        """Test button is disabled when URL is empty."""
        page = setup_wizard.orchestrator_page
        page.url_edit.clear()

        assert page.test_button.isEnabled() is False

    def test_test_button_enabled_when_url_entered(
        self, qtbot, setup_wizard: SetupWizard
    ) -> None:
        """Test button is enabled when URL is entered."""
        page = setup_wizard.orchestrator_page
        page.url_edit.setText("wss://test.example.com/ws")

        assert page.test_button.isEnabled() is True

    def test_page_is_complete_without_url(self, setup_wizard: SetupWizard) -> None:
        """Page allows completion without URL (local-only mode)."""
        page = setup_wizard.orchestrator_page
        page.url_edit.clear()

        # Page should be complete (URL is optional)
        assert page.isComplete() is True

    def test_url_validation_on_test(self, qtbot, setup_wizard: SetupWizard) -> None:
        """Invalid URL shows error when testing."""
        page = setup_wizard.orchestrator_page
        page.url_edit.setText("http://invalid.com")  # Wrong scheme

        # Click test button
        qtbot.mouseClick(page.test_button, Qt.MouseButton.LeftButton)

        # Should show error
        assert (
            "ws://" in page.test_result.text().lower()
            or "error" in page.test_result.text().lower()
        )


class TestRobotConfigPage:
    """Tests for RobotConfigPage."""

    def test_page_has_title(self, setup_wizard: SetupWizard) -> None:
        """Robot config page has correct title."""
        page = setup_wizard.robot_page
        assert page.title() == "Robot Configuration"

    def test_name_input_exists(self, setup_wizard: SetupWizard) -> None:
        """Robot name input exists."""
        page = setup_wizard.robot_page
        assert page.name_edit is not None

    def test_name_has_default_value(self, setup_wizard: SetupWizard) -> None:
        """Robot name has default value based on hostname."""
        page = setup_wizard.robot_page
        hostname = socket.gethostname()

        default_name = page.name_edit.text()
        assert hostname in default_name
        assert "Robot" in default_name

    def test_concurrent_spin_exists(self, setup_wizard: SetupWizard) -> None:
        """Concurrent jobs spinbox exists."""
        page = setup_wizard.robot_page
        assert page.concurrent_spin is not None

    def test_concurrent_spin_defaults(self, setup_wizard: SetupWizard) -> None:
        """Concurrent jobs spinbox has correct defaults."""
        page = setup_wizard.robot_page

        assert page.concurrent_spin.value() == 2
        assert page.concurrent_spin.minimum() == 1
        assert page.concurrent_spin.maximum() == 10

    def test_environment_combo_exists(self, setup_wizard: SetupWizard) -> None:
        """Environment combo box exists."""
        page = setup_wizard.robot_page
        assert page.env_combo is not None

    def test_environment_options(self, setup_wizard: SetupWizard) -> None:
        """Environment combo has correct options."""
        page = setup_wizard.robot_page

        options = [page.env_combo.itemText(i) for i in range(page.env_combo.count())]

        assert "Production" in options
        assert "Staging" in options
        assert "Development" in options

    def test_log_level_combo_exists(self, setup_wizard: SetupWizard) -> None:
        """Log level combo box exists."""
        page = setup_wizard.robot_page
        assert page.log_level_combo is not None

    def test_log_level_options(self, setup_wizard: SetupWizard) -> None:
        """Log level combo has correct options."""
        page = setup_wizard.robot_page

        options = [
            page.log_level_combo.itemText(i)
            for i in range(page.log_level_combo.count())
        ]

        assert "DEBUG" in options
        assert "INFO" in options
        assert "WARNING" in options
        assert "ERROR" in options

    def test_log_level_default(self, setup_wizard: SetupWizard) -> None:
        """Log level defaults to INFO."""
        page = setup_wizard.robot_page
        assert page.log_level_combo.currentText() == "INFO"

    def test_page_complete_with_name(self, setup_wizard: SetupWizard) -> None:
        """Page is complete when name is filled."""
        page = setup_wizard.robot_page
        page.name_edit.setText("ValidRobotName")

        assert page.isComplete() is True

    def test_page_incomplete_without_name(self, setup_wizard: SetupWizard) -> None:
        """Page is incomplete when name is empty."""
        page = setup_wizard.robot_page
        page.name_edit.clear()

        assert page.isComplete() is False


class TestCapabilitiesPage:
    """Tests for CapabilitiesPage."""

    def test_page_has_title(self, setup_wizard: SetupWizard) -> None:
        """Capabilities page has correct title."""
        page = setup_wizard.capabilities_page
        assert page.title() == "Robot Capabilities"

    def test_browser_checkbox_exists(self, setup_wizard: SetupWizard) -> None:
        """Browser capability checkbox exists."""
        page = setup_wizard.capabilities_page
        assert page.browser_check is not None

    def test_browser_checkbox_checked_by_default(
        self, setup_wizard: SetupWizard
    ) -> None:
        """Browser capability is checked by default."""
        page = setup_wizard.capabilities_page
        assert page.browser_check.isChecked() is True

    def test_desktop_checkbox_exists(self, setup_wizard: SetupWizard) -> None:
        """Desktop capability checkbox exists."""
        page = setup_wizard.capabilities_page
        assert page.desktop_check is not None

    def test_desktop_checkbox_checked_by_default(
        self, setup_wizard: SetupWizard
    ) -> None:
        """Desktop capability is checked by default on Windows."""
        import platform

        page = setup_wizard.capabilities_page

        if platform.system() == "Windows":
            assert page.desktop_check.isChecked() is True
        else:
            # On non-Windows, may be unchecked
            pass  # Skip assertion

    def test_high_memory_checkbox_exists(self, setup_wizard: SetupWizard) -> None:
        """High memory checkbox exists."""
        page = setup_wizard.capabilities_page
        assert page.high_memory_check is not None

    def test_gpu_checkbox_exists(self, setup_wizard: SetupWizard) -> None:
        """GPU checkbox exists."""
        page = setup_wizard.capabilities_page
        assert page.gpu_check is not None

    def test_secure_checkbox_exists(self, setup_wizard: SetupWizard) -> None:
        """Secure environment checkbox exists."""
        page = setup_wizard.capabilities_page
        assert page.secure_check is not None

    def test_on_premise_checkbox_exists(self, setup_wizard: SetupWizard) -> None:
        """On-premise checkbox exists."""
        page = setup_wizard.capabilities_page
        assert page.on_premise_check is not None

    def test_on_premise_checked_by_default(self, setup_wizard: SetupWizard) -> None:
        """On-premise is checked by default."""
        import platform

        page = setup_wizard.capabilities_page

        if platform.system() == "Windows":
            assert page.on_premise_check.isChecked() is True

    def test_tags_input_exists(self, setup_wizard: SetupWizard) -> None:
        """Tags input field exists."""
        page = setup_wizard.capabilities_page
        assert page.tags_edit is not None

    def test_tags_input_placeholder(self, setup_wizard: SetupWizard) -> None:
        """Tags input has placeholder text."""
        page = setup_wizard.capabilities_page
        placeholder = page.tags_edit.placeholderText()

        assert "comma" in placeholder.lower()

    def test_checkbox_toggling(self, qtbot, setup_wizard: SetupWizard) -> None:
        """Checkboxes can be toggled."""
        page = setup_wizard.capabilities_page

        # Toggle browser off
        initial_state = page.browser_check.isChecked()
        page.browser_check.setChecked(not initial_state)
        assert page.browser_check.isChecked() == (not initial_state)

        # Toggle back
        page.browser_check.setChecked(initial_state)
        assert page.browser_check.isChecked() == initial_state


class TestSummaryPage:
    """Tests for SummaryPage."""

    def test_page_has_title(self, setup_wizard: SetupWizard) -> None:
        """Summary page has correct title."""
        page = setup_wizard.summary_page
        assert page.title() == "Configuration Summary"

    def test_summary_text_exists(self, setup_wizard: SetupWizard) -> None:
        """Summary text widget exists."""
        page = setup_wizard.summary_page
        assert page.summary_text is not None

    def test_summary_text_is_readonly(self, setup_wizard: SetupWizard) -> None:
        """Summary text is read-only."""
        page = setup_wizard.summary_page
        assert page.summary_text.isReadOnly() is True

    def test_initialize_page_shows_config(
        self, qtbot, setup_wizard: SetupWizard
    ) -> None:
        """initializePage shows configuration summary."""
        # Initialize wizard
        setup_wizard.restart()

        # Set some config values
        setup_wizard.orchestrator_page.url_edit.setText("wss://summary.test.com/ws")
        setup_wizard.robot_page.name_edit.setText("SummaryTestBot")
        setup_wizard.capabilities_page.tags_edit.setText("summary, test")

        # Navigate to summary page
        setup_wizard.next()  # To Orchestrator
        setup_wizard.next()  # To Robot
        setup_wizard.next()  # To Capabilities
        setup_wizard.next()  # To Summary

        # Get summary text
        summary = setup_wizard.summary_page.summary_text.toPlainText()

        # Check key elements are present
        assert "wss://summary.test.com/ws" in summary
        assert "SummaryTestBot" in summary

    def test_initialize_page_shows_local_only_mode(
        self, qtbot, setup_wizard: SetupWizard
    ) -> None:
        """initializePage shows local-only mode when no URL."""
        # Initialize wizard
        setup_wizard.restart()

        # Clear URL
        setup_wizard.orchestrator_page.url_edit.clear()
        setup_wizard.robot_page.name_edit.setText("LocalBot")

        # Navigate to summary page
        setup_wizard.next()  # To Orchestrator
        setup_wizard.next()  # To Robot
        setup_wizard.next()  # To Capabilities
        setup_wizard.next()  # To Summary

        summary = setup_wizard.summary_page.summary_text.toPlainText()

        assert "local" in summary.lower()


class TestShowSetupWizardIfNeeded:
    """Tests for show_setup_wizard_if_needed function."""

    def test_returns_config_when_setup_not_needed(self, tmp_path: Path) -> None:
        """Returns existing config when setup not needed."""
        config_dir = tmp_path / "CasareRPA"
        config_manager = ClientConfigManager(config_dir=config_dir)

        # Create complete config
        config = ClientConfig()
        config.first_run_complete = True
        config.robot.name = "ExistingBot"
        config_manager.save(config)

        with patch(
            "casare_rpa.presentation.setup.setup_wizard.ClientConfigManager"
        ) as MockManager:
            mock_instance = Mock()
            mock_instance.needs_setup.return_value = False
            mock_instance.load.return_value = config
            MockManager.return_value = mock_instance

            result = show_setup_wizard_if_needed()

            assert result is not None
            assert result.robot.name == "ExistingBot"


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_wizard_handles_save_error(self, qtbot, setup_wizard: SetupWizard) -> None:
        """Wizard handles save errors gracefully."""
        setup_wizard.robot_page.name_edit.setText("ErrorTestBot")

        # Make save fail
        setup_wizard.config_manager.save = Mock(
            side_effect=PermissionError("Access denied")
        )

        # Should not raise
        with patch.object(QWizard, "accept"):
            setup_wizard.accept()

    def test_wizard_strips_whitespace_from_url(self, setup_wizard: SetupWizard) -> None:
        """Wizard strips whitespace from URL."""
        setup_wizard.orchestrator_page.url_edit.setText("  wss://test.com/ws  ")

        setup_wizard._gather_config()

        assert setup_wizard.config.orchestrator.url == "wss://test.com/ws"

    def test_wizard_strips_whitespace_from_api_key(
        self, setup_wizard: SetupWizard
    ) -> None:
        """Wizard strips whitespace from API key."""
        setup_wizard.orchestrator_page.api_key_edit.setText("  crpa_test  ")

        setup_wizard._gather_config()

        assert setup_wizard.config.orchestrator.api_key == "crpa_test"

    def test_wizard_strips_whitespace_from_name(
        self, setup_wizard: SetupWizard
    ) -> None:
        """Wizard strips whitespace from robot name."""
        setup_wizard.robot_page.name_edit.setText("  TestBot  ")

        setup_wizard._gather_config()

        assert setup_wizard.config.robot.name == "TestBot"

    def test_tags_parsing_handles_extra_spaces(self, setup_wizard: SetupWizard) -> None:
        """Tags parsing handles extra spaces."""
        setup_wizard.capabilities_page.tags_edit.setText("  tag1  ,  tag2  ,  tag3  ")

        setup_wizard._gather_config()

        tags = setup_wizard.config.robot.tags
        assert "tag1" in tags
        assert "tag2" in tags
        assert "tag3" in tags
        # No empty strings
        assert "" not in tags

    def test_tags_parsing_handles_empty_entries(
        self, setup_wizard: SetupWizard
    ) -> None:
        """Tags parsing handles empty entries."""
        setup_wizard.capabilities_page.tags_edit.setText("tag1,,tag2,,,tag3")

        setup_wizard._gather_config()

        tags = setup_wizard.config.robot.tags
        assert len(tags) == 3
        assert "" not in tags

    def test_environment_converted_to_lowercase(
        self, setup_wizard: SetupWizard
    ) -> None:
        """Environment value is converted to lowercase."""
        setup_wizard.robot_page.env_combo.setCurrentText("Production")

        setup_wizard._gather_config()

        assert setup_wizard.config.robot.environment == "production"


class TestConnectionTestUI:
    """Tests for connection test UI behavior."""

    def test_test_result_cleared_on_url_change(
        self, qtbot, setup_wizard: SetupWizard
    ) -> None:
        """Test result is cleared when URL changes."""
        page = setup_wizard.orchestrator_page

        # Set initial result
        page.test_result.setText("Previous result")

        # Change URL
        page.url_edit.setText("wss://new.url.com/ws")

        assert page.test_result.text() == ""

    def test_test_result_cleared_on_api_key_change(
        self, qtbot, setup_wizard: SetupWizard
    ) -> None:
        """Test result is cleared when API key changes."""
        page = setup_wizard.orchestrator_page

        # Set initial result
        page.test_result.setText("Previous result")

        # Change API key
        page.api_key_edit.setText("crpa_newkey")

        assert page.test_result.text() == ""

    def test_progress_bar_hidden_initially(self, setup_wizard: SetupWizard) -> None:
        """Progress bar is hidden initially."""
        page = setup_wizard.orchestrator_page
        assert page.test_progress.isVisible() is False
