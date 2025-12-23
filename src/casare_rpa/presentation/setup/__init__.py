"""
CasareRPA Setup Wizard Package.

Provides first-run setup wizard for configuring orchestrator connection
and robot settings on client installations.
"""

from casare_rpa.presentation.setup.config_manager import (
    ClientConfig,
    ClientConfigManager,
)
from casare_rpa.presentation.setup.setup_wizard import (
    CapabilitiesPage,
    OrchestratorPage,
    RobotConfigPage,
    SetupWizard,
    SummaryPage,
    WelcomePage,
)

__all__ = [
    "SetupWizard",
    "WelcomePage",
    "OrchestratorPage",
    "RobotConfigPage",
    "CapabilitiesPage",
    "SummaryPage",
    "ClientConfig",
    "ClientConfigManager",
]
