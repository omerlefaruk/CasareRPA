"""
CasareRPA Setup Wizard Package.

Provides first-run setup wizard for configuring orchestrator connection
and robot settings on client installations.
"""

from casare_rpa.presentation.setup.setup_wizard import (
    SetupWizard,
    WelcomePage,
    OrchestratorPage,
    RobotConfigPage,
    CapabilitiesPage,
    SummaryPage,
)
from casare_rpa.presentation.setup.config_manager import (
    ClientConfig,
    ClientConfigManager,
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
