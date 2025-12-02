"""
Presentation Services for CasareRPA Canvas.

Contains service classes that bridge infrastructure components to the UI layer.
"""

from .websocket_bridge import (
    WebSocketBridge,
    RobotStatusUpdate,
    JobStatusUpdate,
    QueueMetricsUpdate,
    get_websocket_bridge,
)

__all__ = [
    "WebSocketBridge",
    "RobotStatusUpdate",
    "JobStatusUpdate",
    "QueueMetricsUpdate",
    "get_websocket_bridge",
]
