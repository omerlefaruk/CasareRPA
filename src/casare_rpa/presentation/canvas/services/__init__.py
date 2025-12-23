"""
Presentation Services for CasareRPA Canvas.

Contains service classes that bridge infrastructure components to the UI layer.
"""

from casare_rpa.presentation.canvas.services.trigger_event_handler import (
    QtTriggerEventHandler,
    create_trigger_event_handler,
)
from casare_rpa.presentation.canvas.services.websocket_bridge import (
    JobStatusUpdate,
    QueueMetricsUpdate,
    RobotStatusUpdate,
    WebSocketBridge,
    get_websocket_bridge,
)

__all__ = [
    # Trigger handling
    "QtTriggerEventHandler",
    "create_trigger_event_handler",
    # WebSocket bridge
    "WebSocketBridge",
    "RobotStatusUpdate",
    "JobStatusUpdate",
    "QueueMetricsUpdate",
    "get_websocket_bridge",
]
