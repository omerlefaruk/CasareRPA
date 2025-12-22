"""
Shake-to-Detach gesture handler for node graph.

Monitors mouse movement while dragging a node and disconnects
all wires when the user rapidly shakes the node left-right.

This provides a fast, playful alternative to right-clicking or
individually deleting connections.
"""

import time
from collections import deque
from typing import Optional, Deque
from dataclasses import dataclass

from PySide6.QtCore import QObject, Signal, Qt, QTimer
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QGraphicsDropShadowEffect
from NodeGraphQt import NodeGraph, BaseNode

from loguru import logger


@dataclass
class MovementSample:
    """A single mouse movement sample."""

    x: float
    y: float
    timestamp: float  # seconds


class ShakeToDetachManager(QObject):
    """
    Detects shake gestures on dragged nodes and disconnects their wires.

    The shake detection algorithm:
    1. Track mouse positions during drag
    2. Detect direction changes (velocity sign flips)
    3. If enough rapid direction changes occur within time window -> SHAKE!
    4. Disconnect all wires from the node

    Configuration:
    - shake_threshold: Minimum direction changes to trigger (default: 4)
    - time_window_ms: Time window for shake detection (default: 400ms)
    - min_movement_px: Minimum horizontal movement per direction change (default: 15px)
    """

    # Emitted when a node is detached via shake gesture
    node_detached = Signal(object)  # node that was detached

    # Emitted when shake is detected (for visual feedback)
    shake_detected = Signal(object)  # node being shaken

    def __init__(self, graph: NodeGraph, parent: Optional[QObject] = None):
        """
        Initialize shake-to-detach manager.

        Args:
            graph: NodeGraph instance to monitor
            parent: Optional parent QObject
        """
        super().__init__(parent)

        self._graph = graph
        self._active = True

        # Shake detection parameters (tunable)
        self._shake_threshold = 3  # Direction changes needed (lower = easier)
        self._time_window_ms = 500  # Window to detect shake (higher = more time)
        self._min_movement_px = (
            12  # Min horizontal movement per swing (lower = smaller shakes work)
        )
        self._cooldown_ms = 500  # Cooldown after shake to prevent re-trigger

        # State tracking
        self._dragging_node: Optional[BaseNode] = None
        self._movement_history: Deque[MovementSample] = deque(maxlen=50)
        self._last_x_direction: Optional[int] = None  # -1 left, +1 right
        self._direction_changes: list[float] = []  # timestamps of direction changes
        self._last_shake_time: float = 0.0

        # Visual feedback
        self._shake_effect: Optional[QGraphicsDropShadowEffect] = None
        self._feedback_timer = QTimer(self)
        self._feedback_timer.setSingleShot(True)
        self._feedback_timer.timeout.connect(self._clear_visual_feedback)

        # Install event filter
        self._setup_event_filters()

    def _setup_event_filters(self):
        """Setup event filters on the graph viewer."""
        try:
            viewer = self._graph.viewer()
            if viewer:
                viewer.installEventFilter(self)
                if hasattr(viewer, "viewport"):
                    viewport = viewer.viewport()
                    if viewport:
                        viewport.installEventFilter(self)
        except Exception as e:
            logger.warning(f"ShakeToDetach: Could not setup event filters: {e}")

    def set_active(self, active: bool):
        """Enable or disable shake-to-detach."""
        self._active = active
        if not active:
            self._reset_state()

    def is_active(self) -> bool:
        """Check if shake-to-detach is active."""
        return self._active

    def set_sensitivity(
        self,
        shake_threshold: int = 4,
        time_window_ms: int = 400,
        min_movement_px: int = 15,
    ):
        """
        Configure shake detection sensitivity.

        Args:
            shake_threshold: Number of direction changes to trigger shake
            time_window_ms: Time window for detecting shake gesture
            min_movement_px: Minimum horizontal pixels per swing
        """
        self._shake_threshold = max(2, shake_threshold)
        self._time_window_ms = max(100, time_window_ms)
        self._min_movement_px = max(5, min_movement_px)

    def eventFilter(self, watched, event) -> bool:
        """Filter events to detect node dragging and shake gesture."""
        if not self._active:
            return super().eventFilter(watched, event)

        try:
            from PySide6.QtCore import QEvent

            # Mouse move during drag
            if event.type() == QEvent.Type.MouseMove:
                if isinstance(event, QMouseEvent):
                    if event.buttons() & Qt.MouseButton.LeftButton:
                        self._handle_mouse_move(event)

            # Detect drag start
            elif event.type() == QEvent.Type.MouseButtonPress:
                if isinstance(event, QMouseEvent) and event.button() == Qt.MouseButton.LeftButton:
                    self._handle_drag_start()

            # Detect drag end
            elif event.type() == QEvent.Type.MouseButtonRelease:
                if isinstance(event, QMouseEvent) and event.button() == Qt.MouseButton.LeftButton:
                    self._handle_drag_end()

        except Exception as e:
            logger.debug(f"ShakeToDetach eventFilter error: {e}")

        return super().eventFilter(watched, event)

    def _handle_drag_start(self):
        """Handle potential drag start."""
        try:
            selected = self._graph.selected_nodes()
            if selected:
                # Check we're not making a connection
                viewer = self._graph.viewer()
                is_connecting = (
                    viewer and hasattr(viewer, "_LIVE_PIPE") and viewer._LIVE_PIPE.isVisible()
                )

                if not is_connecting:
                    self._dragging_node = selected[0]
                    self._movement_history.clear()
                    self._direction_changes.clear()
                    self._last_x_direction = None
        except Exception as e:
            logger.debug(f"ShakeToDetach drag start error: {e}")

    def _handle_drag_end(self):
        """Handle drag end."""
        self._reset_state()

    def _handle_mouse_move(self, event: QMouseEvent):
        """Track mouse movement and detect shake."""
        if not self._dragging_node:
            return

        try:
            # Get current position
            viewer = self._graph.viewer()
            if not viewer:
                return

            view_pos = viewer.mapFromGlobal(event.globalPosition().toPoint())
            scene_pos = viewer.mapToScene(view_pos)
            current_time = time.perf_counter()

            # Add sample
            sample = MovementSample(x=scene_pos.x(), y=scene_pos.y(), timestamp=current_time)
            self._movement_history.append(sample)

            # Need at least 2 samples to detect direction
            if len(self._movement_history) < 2:
                return

            # Calculate horizontal velocity
            prev_sample = self._movement_history[-2]
            dx = sample.x - prev_sample.x
            dt = sample.timestamp - prev_sample.timestamp

            if dt <= 0 or abs(dx) < self._min_movement_px:
                return

            # Determine direction
            current_direction = 1 if dx > 0 else -1

            # Detect direction change
            if self._last_x_direction is not None and current_direction != self._last_x_direction:
                self._direction_changes.append(current_time)
                self._check_for_shake(current_time)

            self._last_x_direction = current_direction

        except Exception as e:
            logger.debug(f"ShakeToDetach mouse move error: {e}")

    def _check_for_shake(self, current_time: float):
        """Check if recent direction changes constitute a shake."""
        # Check cooldown
        if (current_time - self._last_shake_time) < (self._cooldown_ms / 1000.0):
            return

        # Remove old direction changes outside time window
        window_start = current_time - (self._time_window_ms / 1000.0)
        self._direction_changes = [t for t in self._direction_changes if t >= window_start]

        # Check if we have enough direction changes
        if len(self._direction_changes) >= self._shake_threshold:
            self._trigger_shake()
            self._last_shake_time = current_time

    def _trigger_shake(self):
        """Execute the shake action - disconnect all wires."""
        if not self._dragging_node:
            return

        node = self._dragging_node

        try:
            # Show visual feedback first
            self._show_visual_feedback(node)

            # Emit signal for listeners
            self.shake_detected.emit(node)

            # Disconnect all connections
            disconnected_count = self._disconnect_all_wires(node)

            if disconnected_count > 0:
                logger.info(
                    f"ShakeToDetach: Disconnected {disconnected_count} wires from '{node.name()}'"
                )
                self.node_detached.emit(node)

            # Reset direction tracking but keep dragging state
            self._direction_changes.clear()
            self._last_x_direction = None

        except Exception as e:
            logger.error(f"ShakeToDetach trigger error: {e}")

    def _disconnect_all_wires(self, node: BaseNode) -> int:
        """
        Disconnect all wires from a node.

        Args:
            node: The node to disconnect

        Returns:
            Number of connections disconnected
        """
        disconnected = 0

        try:
            # Disconnect input ports
            input_ports = node.inputs()
            if input_ports:
                for port_name, port in input_ports.items():
                    connected = port.connected_ports()
                    for other_port in list(connected):
                        try:
                            port.disconnect_from(other_port)
                            disconnected += 1
                        except Exception:
                            pass

            # Disconnect output ports
            output_ports = node.outputs()
            if output_ports:
                for port_name, port in output_ports.items():
                    connected = port.connected_ports()
                    for other_port in list(connected):
                        try:
                            port.disconnect_from(other_port)
                            disconnected += 1
                        except Exception:
                            pass

        except Exception as e:
            logger.debug(f"ShakeToDetach disconnect error: {e}")

        return disconnected

    def _show_visual_feedback(self, node: BaseNode):
        """Show visual feedback when shake is detected."""
        try:
            # Get the node's graphics item
            view = node.view
            if not view:
                return

            # Create a brief glow/flash effect using drop shadow
            from PySide6.QtGui import QColor

            effect = QGraphicsDropShadowEffect()
            effect.setBlurRadius(30)
            effect.setColor(QColor(255, 100, 100, 200))  # Red glow
            effect.setOffset(0, 0)

            view.setGraphicsEffect(effect)
            self._shake_effect = effect

            # Clear effect after 200ms
            self._feedback_timer.start(200)

        except Exception as e:
            logger.debug(f"ShakeToDetach visual feedback error: {e}")

    def _clear_visual_feedback(self):
        """Clear the visual feedback effect."""
        try:
            if self._dragging_node and hasattr(self._dragging_node, "view"):
                view = self._dragging_node.view
                if view:
                    view.setGraphicsEffect(None)
            self._shake_effect = None
        except Exception:
            pass

    def _reset_state(self):
        """Reset all tracking state."""
        self._clear_visual_feedback()
        self._dragging_node = None
        self._movement_history.clear()
        self._direction_changes.clear()
        self._last_x_direction = None


# Singleton access
_shake_manager: Optional[ShakeToDetachManager] = None


def get_shake_manager() -> Optional[ShakeToDetachManager]:
    """Get the global shake-to-detach manager instance."""
    return _shake_manager


def set_shake_manager(manager: ShakeToDetachManager):
    """Set the global shake-to-detach manager instance."""
    global _shake_manager
    _shake_manager = manager
