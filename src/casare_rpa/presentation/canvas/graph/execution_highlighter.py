"""
Execution Highlighter for visual execution trail.

Highlights nodes during workflow execution with status-based colors:
- Running: Yellow animated border
- Success: Green border (fades after 2s)
- Error: Red border (persists)
- Breakpoint: Red border with glow
- Skipped: Gray border

Connects to DebugController signals to update node visual states.
"""

from enum import Enum, auto
from functools import partial
from typing import TYPE_CHECKING, Dict, List, Optional

from loguru import logger
from PySide6.QtCore import QObject, QTimer, Signal

if TYPE_CHECKING:
    from NodeGraphQt import NodeGraph

    from ..debugger.debug_controller import DebugController


class HighlightState(Enum):
    """Node highlight state during execution."""

    IDLE = auto()
    RUNNING = auto()
    SUCCESS = auto()
    ERROR = auto()
    BREAKPOINT = auto()
    SKIPPED = auto()


class ExecutionHighlighter(QObject):
    """
    Manages node highlighting during workflow execution.

    Tracks highlight state for each node and applies visual changes
    through the CasareNodeItem interface.

    Signals:
        path_updated: Emitted when execution path changes
    """

    path_updated = Signal(list)

    def __init__(
        self,
        graph_widget: "NodeGraph",
        debug_controller: Optional["DebugController"] = None,
        parent: QObject | None = None,
    ) -> None:
        """
        Initialize execution highlighter.

        Args:
            graph_widget: NodeGraph instance containing nodes
            debug_controller: Optional debug controller for signal connections
            parent: Optional parent QObject
        """
        super().__init__(parent)
        self._graph = graph_widget
        self._debug_controller = debug_controller
        self._highlights: dict[str, HighlightState] = {}
        self._execution_path: list[str] = []
        self._execution_order: dict[str, int] = {}

        # Timer for fade effects
        self._fade_timers: dict[str, QTimer] = {}
        self._success_fade_duration = 2000  # 2 seconds

        if debug_controller:
            self._connect_debug_signals()

        logger.debug("ExecutionHighlighter initialized")

    def _connect_debug_signals(self) -> None:
        """Connect to debug controller signals."""
        if not self._debug_controller:
            return

        # Breakpoint signals
        self._debug_controller.breakpoint_hit.connect(self._on_breakpoint_hit)
        self._debug_controller.execution_resumed.connect(self._on_execution_resumed)

        # Step signals
        self._debug_controller.step_completed.connect(self._on_step_completed)

        logger.debug("ExecutionHighlighter connected to DebugController")

    def highlight_running(self, node_id: str) -> None:
        """
        Highlight node as currently running.

        Applies yellow animated border to the node.

        Args:
            node_id: ID of the node to highlight
        """
        self._cancel_fade_timer(node_id)
        self._highlights[node_id] = HighlightState.RUNNING
        self._update_node_visual(node_id, HighlightState.RUNNING)

        # Track execution order
        if node_id not in self._execution_order:
            self._execution_order[node_id] = len(self._execution_path)
            self._execution_path.append(node_id)
            self.path_updated.emit(list(self._execution_path))

        logger.debug(f"Node {node_id} highlighted as RUNNING")

    def highlight_success(self, node_id: str, auto_fade: bool = True) -> None:
        """
        Highlight node as successfully completed.

        Applies green border that fades after 2 seconds.

        Args:
            node_id: ID of the node to highlight
            auto_fade: Whether to automatically fade after duration
        """
        self._cancel_fade_timer(node_id)
        self._highlights[node_id] = HighlightState.SUCCESS
        self._update_node_visual(node_id, HighlightState.SUCCESS)

        if auto_fade:
            self._start_fade_timer(node_id)

        logger.debug(f"Node {node_id} highlighted as SUCCESS")

    def highlight_error(self, node_id: str) -> None:
        """
        Highlight node as failed/error.

        Applies red border that persists until cleared.

        Args:
            node_id: ID of the node to highlight
        """
        self._cancel_fade_timer(node_id)
        self._highlights[node_id] = HighlightState.ERROR
        self._update_node_visual(node_id, HighlightState.ERROR)
        logger.debug(f"Node {node_id} highlighted as ERROR")

    def highlight_breakpoint(self, node_id: str) -> None:
        """
        Highlight node as stopped at breakpoint.

        Applies red border with glow effect.

        Args:
            node_id: ID of the node to highlight
        """
        self._cancel_fade_timer(node_id)
        self._highlights[node_id] = HighlightState.BREAKPOINT
        self._update_node_visual(node_id, HighlightState.BREAKPOINT)
        logger.debug(f"Node {node_id} highlighted as BREAKPOINT")

    def highlight_skipped(self, node_id: str) -> None:
        """
        Highlight node as skipped.

        Applies gray border to indicate node was not executed.

        Args:
            node_id: ID of the node to highlight
        """
        self._cancel_fade_timer(node_id)
        self._highlights[node_id] = HighlightState.SKIPPED
        self._update_node_visual(node_id, HighlightState.SKIPPED)
        logger.debug(f"Node {node_id} highlighted as SKIPPED")

    def highlight_path(self, node_ids: list[str]) -> None:
        """
        Highlight execution path (multiple nodes).

        Shows execution order badges on nodes.

        Args:
            node_ids: List of node IDs in execution order
        """
        self._execution_path = list(node_ids)
        self._execution_order = {nid: idx for idx, nid in enumerate(node_ids)}
        self.path_updated.emit(list(self._execution_path))
        logger.debug(f"Execution path highlighted: {len(node_ids)} nodes")

    def clear_highlight(self, node_id: str) -> None:
        """
        Clear highlight from a single node.

        Args:
            node_id: ID of the node to clear
        """
        self._cancel_fade_timer(node_id)
        if node_id in self._highlights:
            del self._highlights[node_id]
        self._update_node_visual(node_id, HighlightState.IDLE)
        logger.debug(f"Node {node_id} highlight cleared")

    def clear_all(self) -> None:
        """Clear all highlights and reset execution path."""
        for node_id in list(self._highlights.keys()):
            self._cancel_fade_timer(node_id)
            self._update_node_visual(node_id, HighlightState.IDLE)

        self._highlights.clear()
        self._execution_path.clear()
        self._execution_order.clear()
        self.path_updated.emit([])
        logger.debug("All highlights cleared")

    def get_state(self, node_id: str) -> HighlightState:
        """
        Get current highlight state for a node.

        Args:
            node_id: ID of the node

        Returns:
            Current HighlightState
        """
        return self._highlights.get(node_id, HighlightState.IDLE)

    def get_execution_path(self) -> list[str]:
        """
        Get the current execution path.

        Returns:
            List of node IDs in execution order
        """
        return list(self._execution_path)

    def get_execution_order(self, node_id: str) -> int | None:
        """
        Get execution order number for a node.

        Args:
            node_id: ID of the node

        Returns:
            Order number (0-based) or None if not in path
        """
        return self._execution_order.get(node_id)

    def _update_node_visual(self, node_id: str, state: HighlightState) -> None:
        """
        Update the visual appearance of a node.

        Args:
            node_id: ID of the node
            state: Target highlight state
        """
        node = self._find_node_by_id(node_id)
        if not node:
            return

        # Get the graphics item
        item = getattr(node, "view", None)
        if not item:
            return

        # Apply state-specific visual changes
        if state == HighlightState.IDLE:
            self._apply_idle_state(item)
        elif state == HighlightState.RUNNING:
            self._apply_running_state(item)
        elif state == HighlightState.SUCCESS:
            self._apply_success_state(item)
        elif state == HighlightState.ERROR:
            self._apply_error_state(item)
        elif state == HighlightState.BREAKPOINT:
            self._apply_breakpoint_state(item)
        elif state == HighlightState.SKIPPED:
            self._apply_skipped_state(item)

    def _apply_idle_state(self, item) -> None:
        """Apply idle (default) state to node item."""
        if hasattr(item, "clear_execution_state"):
            item.clear_execution_state()
        elif hasattr(item, "set_running"):
            item.set_running(False)
            if hasattr(item, "set_completed"):
                item.set_completed(False)
            if hasattr(item, "set_error"):
                item.set_error(False)

    def _apply_running_state(self, item) -> None:
        """Apply running state to node item."""
        if hasattr(item, "set_running"):
            item.set_running(True)
        if hasattr(item, "set_completed"):
            item.set_completed(False)
        if hasattr(item, "set_error"):
            item.set_error(False)

    def _apply_success_state(self, item) -> None:
        """Apply success state to node item."""
        if hasattr(item, "set_running"):
            item.set_running(False)
        if hasattr(item, "set_completed"):
            item.set_completed(True)
        if hasattr(item, "set_error"):
            item.set_error(False)

    def _apply_error_state(self, item) -> None:
        """Apply error state to node item."""
        if hasattr(item, "set_running"):
            item.set_running(False)
        if hasattr(item, "set_completed"):
            item.set_completed(False)
        if hasattr(item, "set_error"):
            item.set_error(True)

    def _apply_breakpoint_state(self, item) -> None:
        """Apply breakpoint hit state to node item."""
        # Breakpoint uses error styling with running animation
        if hasattr(item, "set_running"):
            item.set_running(True)
        if hasattr(item, "set_error"):
            item.set_error(True)

    def _apply_skipped_state(self, item) -> None:
        """Apply skipped state to node item."""
        if hasattr(item, "set_running"):
            item.set_running(False)
        if hasattr(item, "set_skipped"):
            item.set_skipped(True)

    def _find_node_by_id(self, node_id: str):
        """
        Find a node by its node_id property.

        Args:
            node_id: The node_id to search for

        Returns:
            Node object or None
        """
        if not self._graph:
            return None

        try:
            for node in self._graph.all_nodes():
                if hasattr(node, "get_property"):
                    if node.get_property("node_id") == node_id:
                        return node
        except Exception as e:
            logger.warning(f"Error finding node {node_id}: {e}")

        return None

    def _start_fade_timer(self, node_id: str) -> None:
        """Start fade timer for success highlight."""
        timer = QTimer(self)
        timer.setSingleShot(True)
        timer.timeout.connect(partial(self._on_fade_complete, node_id))
        timer.start(self._success_fade_duration)
        self._fade_timers[node_id] = timer

    def _cancel_fade_timer(self, node_id: str) -> None:
        """Cancel active fade timer for a node."""
        if node_id in self._fade_timers:
            self._fade_timers[node_id].stop()
            del self._fade_timers[node_id]

    def _on_fade_complete(self, node_id: str) -> None:
        """Handle fade timer completion."""
        if node_id in self._fade_timers:
            del self._fade_timers[node_id]

        # Only clear if still in success state
        if self._highlights.get(node_id) == HighlightState.SUCCESS:
            self._highlights[node_id] = HighlightState.IDLE
            self._update_node_visual(node_id, HighlightState.IDLE)

    def _on_breakpoint_hit(self, node_id: str) -> None:
        """Handle breakpoint hit signal from debug controller."""
        self.highlight_breakpoint(node_id)

    def _on_execution_resumed(self) -> None:
        """Handle execution resumed signal from debug controller."""
        # Clear breakpoint highlight from current node
        for node_id, state in list(self._highlights.items()):
            if state == HighlightState.BREAKPOINT:
                self._highlights[node_id] = HighlightState.RUNNING
                self._update_node_visual(node_id, HighlightState.RUNNING)

    def _on_step_completed(self, node_id: str) -> None:
        """Handle step completed signal from debug controller."""
        # Previous node becomes success, current becomes breakpoint
        for prev_id, state in list(self._highlights.items()):
            if state in (HighlightState.RUNNING, HighlightState.BREAKPOINT):
                if prev_id != node_id:
                    self.highlight_success(prev_id, auto_fade=False)

        self.highlight_breakpoint(node_id)

    def cleanup(self) -> None:
        """Clean up resources."""
        for timer in self._fade_timers.values():
            timer.stop()
        self._fade_timers.clear()
        self._highlights.clear()
        self._execution_path.clear()
        self._execution_order.clear()
        logger.debug("ExecutionHighlighter cleaned up")
