"""
Coordinators for MainWindow.

Coordinators handle signal routing and action coordination,
reducing MainWindow's responsibilities.
"""

from .signal_coordinator import SignalCoordinator

__all__ = ["SignalCoordinator"]
