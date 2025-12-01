"""
CasareRPA - Base Visual Trigger Node

Base class for all visual trigger nodes. Provides distinct styling
and behavior for trigger nodes on the canvas.
"""

from typing import Optional
from PySide6.QtGui import QColor

from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode


# Trigger-specific color (distinct from other nodes)
TRIGGER_ACCENT_COLOR = QColor(156, 39, 176)  # Purple - Material Purple 500
TRIGGER_LISTENING_COLOR = QColor(76, 175, 80)  # Green - Material Green 500


class VisualTriggerNode(VisualNode):
    """
    Base class for visual trigger nodes.

    Trigger nodes have distinct visual styling:
    - Purple accent color (triggers are special entry points)
    - No exec_in port (triggers start workflows)
    - Listening badge when active
    """

    __identifier__ = "casare_rpa.triggers"
    NODE_NAME = "Trigger"
    NODE_CATEGORY = "triggers"

    # Trigger-specific flags
    IS_TRIGGER = True

    def __init__(self) -> None:
        """Initialize visual trigger node."""
        super().__init__()

        # Listening state
        self._is_listening: bool = False

        # Apply trigger-specific styling
        self._apply_trigger_styling()

    def _apply_trigger_styling(self) -> None:
        """Apply distinct styling for trigger nodes."""
        # Purple border for trigger nodes
        self.model.border_color = (
            TRIGGER_ACCENT_COLOR.red(),
            TRIGGER_ACCENT_COLOR.green(),
            TRIGGER_ACCENT_COLOR.blue(),
            255,
        )

    def setup_ports(self) -> None:
        """
        Setup trigger node ports.

        Trigger nodes have NO exec_in - they start workflows.
        Override in subclasses to add specific data output ports.
        """
        # Only exec_out, NO exec_in!
        self.add_exec_output("exec_out")

        # Subclasses should call super().setup_ports() then add their ports
        self._setup_payload_ports()

    def _setup_payload_ports(self) -> None:
        """
        Setup output ports for trigger payload data.

        Override in subclasses to define specific output ports.
        """
        pass

    def set_listening(self, listening: bool) -> None:
        """
        Set the listening state and update visual appearance.

        Args:
            listening: True if trigger is actively listening
        """
        self._is_listening = listening

        if listening:
            # Green border when listening
            self.model.border_color = (
                TRIGGER_LISTENING_COLOR.red(),
                TRIGGER_LISTENING_COLOR.green(),
                TRIGGER_LISTENING_COLOR.blue(),
                255,
            )
            # Update view if it supports listening badge
            if hasattr(self.view, "set_listening"):
                self.view.set_listening(True)
        else:
            # Purple border when not listening
            self.model.border_color = (
                TRIGGER_ACCENT_COLOR.red(),
                TRIGGER_ACCENT_COLOR.green(),
                TRIGGER_ACCENT_COLOR.blue(),
                255,
            )
            if hasattr(self.view, "set_listening"):
                self.view.set_listening(False)

    @property
    def is_listening(self) -> bool:
        """Check if this trigger is actively listening."""
        return self._is_listening

    def update_status(self, status: str) -> None:
        """
        Update node visual status.

        Overrides base to maintain trigger-specific colors.

        Args:
            status: Node status (idle, running, success, error, listening)
        """
        if status == "listening":
            self.set_listening(True)
            return

        # For other statuses, use base implementation but restore trigger border
        super().update_status(status)

        # Restore trigger-specific border if not in error state
        if status not in ("error", "running"):
            if self._is_listening:
                self.model.border_color = (
                    TRIGGER_LISTENING_COLOR.red(),
                    TRIGGER_LISTENING_COLOR.green(),
                    TRIGGER_LISTENING_COLOR.blue(),
                    255,
                )
            else:
                self.model.border_color = (
                    TRIGGER_ACCENT_COLOR.red(),
                    TRIGGER_ACCENT_COLOR.green(),
                    TRIGGER_ACCENT_COLOR.blue(),
                    255,
                )
