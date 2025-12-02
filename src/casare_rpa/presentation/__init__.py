"""
CasareRPA Presentation Layer - UI & User Interaction

This layer contains:
- Canvas: Qt-based visual workflow editor
- Views: Pure UI components
- Controllers: UI logic and coordination
- Setup: First-run configuration wizard

Depends on: Application layer (via use cases)
"""


# Setup wizard components (lazy import to avoid Qt initialization on import)
def get_setup_wizard():
    """Get SetupWizard class for first-run configuration."""
    from casare_rpa.presentation.setup import SetupWizard

    return SetupWizard


def get_config_manager():
    """Get ClientConfigManager class for configuration handling."""
    from casare_rpa.presentation.setup import ClientConfigManager

    return ClientConfigManager


def show_setup_if_needed(parent=None):
    """Show setup wizard if configuration is missing or incomplete."""
    from casare_rpa.presentation.setup.setup_wizard import show_setup_wizard_if_needed

    return show_setup_wizard_if_needed(parent)


__all__ = [
    "get_setup_wizard",
    "get_config_manager",
    "show_setup_if_needed",
]
