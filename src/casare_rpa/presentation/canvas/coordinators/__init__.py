"""
Coordinators for MainWindow.

Coordinators handle signal routing and action coordination,
reducing MainWindow's responsibilities.

Components:
    SignalCoordinator: Routes action signals to appropriate handlers
    QtDomainEventBridge: Bridges typed domain events to Qt signals
"""

from .event_bridge import (
    QtDomainEventBridge,
    get_qt_domain_event_bridge,
    reset_qt_domain_event_bridge,
)
from .signal_coordinator import SignalCoordinator

__all__ = [
    "SignalCoordinator",
    "QtDomainEventBridge",
    "get_qt_domain_event_bridge",
    "reset_qt_domain_event_bridge",
]
