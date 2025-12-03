"""Protocol definitions for orchestrator domain."""

from casare_rpa.domain.orchestrator.protocols.robot_protocol import (
    Message,
    MessageBuilder,
    MessageType,
)

__all__ = ["Message", "MessageType", "MessageBuilder"]
