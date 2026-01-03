"""
CasareRPA - Presentation Layer

User interface, visual components, and user interaction handling.

Entry Points:
    - canvas.new_main_window.NewMainWindow: Main application window (workflow editor)
    - canvas.graph.custom_pipe.CustomPipe: Node connection visualization
    - canvas.ui.dialogs: Modal dialogs (preferences, credentials, properties)
    - canvas.coordinators: UI coordination logic (execution, selection)
    - setup.SetupWizard: First-run configuration wizard
    - get_setup_wizard(): Lazy accessor for SetupWizard class

Key Patterns:
    - MVC/MVP: Views (Qt widgets) separated from Controllers (coordinators)
    - Event-Driven: Qt signals/slots for UI events, EventBus for cross-component
    - Lazy Loading: Heavy UI components loaded on demand
    - qasync: Qt event loop integration with asyncio for async operations
    - Theme System: Centralized styling via theme.py
    - Dialog Factory: Consistent dialog creation and styling

Related:
    - Application layer: Invokes use cases for workflow execution
    - Infrastructure layer: Shares event bus, uses HTTP client for API calls
    - Domain layer: Displays domain entities (Workflow, Node) in visual form
    - visual_nodes package: Visual representation of domain nodes

Depends on: Application layer (via use cases)
Independent of: Infrastructure implementation details
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
