"""
CasareRPA - Conversation Manager for Multi-turn AI Interactions.

Provides conversation context management for iterative workflow refinement.
Tracks conversation history, workflow state, and detects user intent for
seamless multi-turn interactions with the AI workflow generator.

Features:
    - Message history with role tracking (user/assistant/system)
    - Workflow state persistence across conversation turns
    - Intent detection for routing (NEW_WORKFLOW, MODIFY, EXPLAIN, UNDO)
    - Context window management (truncation of old messages)
    - Undo/redo support for workflow changes

Architecture:
    - Domain layer: ConversationMessage, ConversationContext (dataclasses)
    - Infrastructure layer: ConversationManager (state management)
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from loguru import logger


class MessageRole(Enum):
    """Role of a message in the conversation."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class UserIntent(Enum):
    """Detected intent from user message."""

    NEW_WORKFLOW = "new_workflow"
    MODIFY_WORKFLOW = "modify_workflow"
    ADD_NODE = "add_node"
    REMOVE_NODE = "remove_node"
    EXPLAIN = "explain"
    UNDO = "undo"
    REDO = "redo"
    CLEAR = "clear"
    HELP = "help"
    TEMPLATE_REQUEST = "template_request"
    REFINE = "refine"
    UNKNOWN = "unknown"


@dataclass
class ConversationMessage:
    """
    A single message in the conversation.

    Attributes:
        role: Who sent the message (user, assistant, system)
        content: The message text content
        timestamp: When the message was created
        message_id: Unique identifier for the message
        metadata: Optional additional data (workflow snapshot, intent, etc.)
    """

    role: MessageRole
    content: str
    timestamp: float = field(default_factory=time.time)
    message_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for LLM API."""
        return {
            "role": self.role.value,
            "content": self.content,
        }

    def to_full_dict(self) -> Dict[str, Any]:
        """Serialize with all fields for persistence."""
        return {
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp,
            "message_id": self.message_id,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationMessage":
        """Create from dictionary."""
        return cls(
            role=MessageRole(data["role"]),
            content=data["content"],
            timestamp=data.get("timestamp", time.time()),
            message_id=data.get("message_id", str(uuid.uuid4())[:8]),
            metadata=data.get("metadata", {}),
        )


@dataclass
class WorkflowSnapshot:
    """
    Snapshot of workflow state at a point in time.

    Used for undo/redo functionality.
    """

    workflow: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    description: str = ""
    message_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "workflow": self.workflow,
            "timestamp": self.timestamp,
            "description": self.description,
            "message_id": self.message_id,
        }


@dataclass
class ConversationContext:
    """
    Complete context for a conversation session.

    Tracks messages, workflow state, and provides methods for
    building LLM context from conversation history.
    """

    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    messages: List[ConversationMessage] = field(default_factory=list)
    current_workflow: Optional[Dict[str, Any]] = None
    workflow_history: List[WorkflowSnapshot] = field(default_factory=list)
    redo_stack: List[WorkflowSnapshot] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    last_intent: Optional[UserIntent] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def message_count(self) -> int:
        """Get total message count."""
        return len(self.messages)

    @property
    def has_workflow(self) -> bool:
        """Check if a workflow is currently loaded."""
        return self.current_workflow is not None

    @property
    def can_undo(self) -> bool:
        """Check if undo is available."""
        return len(self.workflow_history) > 0

    @property
    def can_redo(self) -> bool:
        """Check if redo is available."""
        return len(self.redo_stack) > 0

    def get_last_user_message(self) -> Optional[str]:
        """Get the most recent user message content."""
        for msg in reversed(self.messages):
            if msg.role == MessageRole.USER:
                return msg.content
        return None

    def get_last_assistant_message(self) -> Optional[str]:
        """Get the most recent assistant message content."""
        for msg in reversed(self.messages):
            if msg.role == MessageRole.ASSISTANT:
                return msg.content
        return None


class ConversationManager:
    """
    Manages conversation context for multi-turn AI interactions.

    Provides:
    - Message history tracking with role identification
    - Workflow state management across conversation turns
    - Context window management for LLM token limits
    - Undo/redo support for workflow modifications
    - Intent detection routing

    Example:
        manager = ConversationManager(max_messages=20)
        manager.add_user_message("Create a login workflow")
        context = manager.build_llm_context(include_workflow=True)
        # ... call LLM with context ...
        manager.add_assistant_message("I've created a login workflow...")
        manager.set_workflow(generated_workflow)
    """

    DEFAULT_MAX_MESSAGES = 20
    DEFAULT_MAX_HISTORY = 10
    SYSTEM_MESSAGE_WEIGHT = 2  # System messages count more toward limit

    def __init__(
        self,
        max_messages: int = DEFAULT_MAX_MESSAGES,
        max_workflow_history: int = DEFAULT_MAX_HISTORY,
    ) -> None:
        """
        Initialize conversation manager.

        Args:
            max_messages: Maximum messages to retain in context
            max_workflow_history: Maximum workflow snapshots for undo
        """
        self._max_messages = max_messages
        self._max_workflow_history = max_workflow_history
        self._context = ConversationContext()

        logger.debug(
            f"ConversationManager initialized: max_messages={max_messages}, "
            f"max_history={max_workflow_history}"
        )

    @property
    def context(self) -> ConversationContext:
        """Get current conversation context."""
        return self._context

    @property
    def session_id(self) -> str:
        """Get current session ID."""
        return self._context.session_id

    @property
    def current_workflow(self) -> Optional[Dict[str, Any]]:
        """Get current workflow state."""
        return self._context.current_workflow

    @property
    def message_count(self) -> int:
        """Get total message count."""
        return self._context.message_count

    def add_user_message(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ConversationMessage:
        """
        Add a user message to the conversation.

        Args:
            content: Message text
            metadata: Optional additional data

        Returns:
            The created message
        """
        message = ConversationMessage(
            role=MessageRole.USER,
            content=content,
            metadata=metadata or {},
        )
        self._add_message(message)
        logger.debug(f"User message added: {content[:50]}...")
        return message

    def add_assistant_message(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ConversationMessage:
        """
        Add an assistant message to the conversation.

        Args:
            content: Message text
            metadata: Optional additional data (e.g., workflow generated)

        Returns:
            The created message
        """
        message = ConversationMessage(
            role=MessageRole.ASSISTANT,
            content=content,
            metadata=metadata or {},
        )
        self._add_message(message)
        logger.debug(f"Assistant message added: {content[:50]}...")
        return message

    def add_system_message(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ConversationMessage:
        """
        Add a system message to the conversation.

        Args:
            content: Message text
            metadata: Optional additional data

        Returns:
            The created message
        """
        message = ConversationMessage(
            role=MessageRole.SYSTEM,
            content=content,
            metadata=metadata or {},
        )
        self._add_message(message)
        logger.debug(f"System message added: {content[:50]}...")
        return message

    def _add_message(self, message: ConversationMessage) -> None:
        """Add message and manage context window."""
        self._context.messages.append(message)
        self._truncate_if_needed()

    def _truncate_if_needed(self) -> None:
        """Truncate old messages if over limit."""
        if len(self._context.messages) <= self._max_messages:
            return

        # Keep system messages and recent messages
        system_messages = [m for m in self._context.messages if m.role == MessageRole.SYSTEM]
        non_system = [m for m in self._context.messages if m.role != MessageRole.SYSTEM]

        # Calculate how many non-system messages to keep
        system_weight = len(system_messages) * self.SYSTEM_MESSAGE_WEIGHT
        non_system_limit = max(2, self._max_messages - system_weight)

        # Keep the most recent non-system messages
        truncated_non_system = non_system[-non_system_limit:]

        # Reconstruct messages: system first, then chronological
        self._context.messages = system_messages + truncated_non_system

        logger.debug(
            f"Truncated conversation: {len(non_system)} -> {len(truncated_non_system)} messages"
        )

    def set_workflow(
        self,
        workflow: Dict[str, Any],
        description: str = "",
        create_snapshot: bool = True,
    ) -> None:
        """
        Set current workflow state.

        Args:
            workflow: Workflow dictionary
            description: Description of this workflow version
            create_snapshot: Whether to create undo snapshot
        """
        if create_snapshot and self._context.current_workflow is not None:
            self._create_workflow_snapshot(description or "Previous workflow")
            # Clear redo stack on new change
            self._context.redo_stack.clear()

        self._context.current_workflow = workflow
        logger.debug(
            f"Workflow set: {len(workflow.get('nodes', {}))} nodes, " f"snapshot={create_snapshot}"
        )

    def _create_workflow_snapshot(self, description: str) -> None:
        """Create a snapshot of current workflow for undo."""
        if self._context.current_workflow is None:
            return

        snapshot = WorkflowSnapshot(
            workflow=dict(self._context.current_workflow),
            description=description,
            message_id=self._context.messages[-1].message_id if self._context.messages else "",
        )

        self._context.workflow_history.append(snapshot)

        # Truncate history if needed
        if len(self._context.workflow_history) > self._max_workflow_history:
            self._context.workflow_history = self._context.workflow_history[
                -self._max_workflow_history :
            ]

    def undo_workflow(self) -> Optional[Dict[str, Any]]:
        """
        Undo the last workflow change.

        Returns:
            Previous workflow state, or None if no undo available
        """
        if not self._context.can_undo:
            logger.debug("Undo not available - no history")
            return None

        # Save current to redo stack
        if self._context.current_workflow is not None:
            redo_snapshot = WorkflowSnapshot(
                workflow=dict(self._context.current_workflow),
                description="Redo point",
            )
            self._context.redo_stack.append(redo_snapshot)

        # Restore previous
        snapshot = self._context.workflow_history.pop()
        self._context.current_workflow = snapshot.workflow

        logger.info(f"Workflow undone: {snapshot.description}")
        return snapshot.workflow

    def redo_workflow(self) -> Optional[Dict[str, Any]]:
        """
        Redo a previously undone workflow change.

        Returns:
            Restored workflow state, or None if no redo available
        """
        if not self._context.can_redo:
            logger.debug("Redo not available - no redo stack")
            return None

        # Save current to history
        if self._context.current_workflow is not None:
            self._create_workflow_snapshot("Before redo")

        # Restore from redo stack
        snapshot = self._context.redo_stack.pop()
        self._context.current_workflow = snapshot.workflow

        logger.info("Workflow redone")
        return snapshot.workflow

    def build_llm_context(
        self,
        include_workflow: bool = True,
        max_workflow_chars: int = 3000,
    ) -> List[Dict[str, str]]:
        """
        Build message list for LLM API.

        Args:
            include_workflow: Whether to include current workflow in context
            max_workflow_chars: Maximum chars for workflow JSON in context

        Returns:
            List of message dicts with role and content
        """
        messages = []

        # Add system context about current workflow state
        if include_workflow and self._context.current_workflow is not None:
            import json

            workflow_json = json.dumps(self._context.current_workflow, indent=2)
            if len(workflow_json) > max_workflow_chars:
                # Truncate but keep valid JSON structure info
                node_count = len(self._context.current_workflow.get("nodes", {}))
                conn_count = len(self._context.current_workflow.get("connections", []))
                workflow_summary = (
                    f"[Current workflow: {node_count} nodes, {conn_count} connections. "
                    f"Workflow too large to include full JSON - {len(workflow_json)} chars]"
                )
                messages.append(
                    {
                        "role": "system",
                        "content": f"Current workflow state:\n{workflow_summary}",
                    }
                )
            else:
                messages.append(
                    {
                        "role": "system",
                        "content": f"Current workflow state:\n```json\n{workflow_json}\n```",
                    }
                )

        # Add conversation messages
        for msg in self._context.messages:
            messages.append(msg.to_dict())

        return messages

    def build_modification_context(self) -> str:
        """
        Build context string for workflow modification requests.

        Returns summary of current workflow and recent conversation
        for efficient LLM prompting.
        """
        parts = []

        # Current workflow summary
        if self._context.current_workflow is not None:
            nodes = self._context.current_workflow.get("nodes", {})
            connections = self._context.current_workflow.get("connections", [])

            node_summaries = []
            for node_id, node_data in list(nodes.items())[:10]:  # First 10 nodes
                node_type = node_data.get("node_type", "Unknown")
                node_summaries.append(f"  - {node_id}: {node_type}")

            if len(nodes) > 10:
                node_summaries.append(f"  ... and {len(nodes) - 10} more nodes")

            parts.append(
                f"CURRENT WORKFLOW:\n"
                f"  Nodes: {len(nodes)}\n"
                f"  Connections: {len(connections)}\n"
                f"  Node list:\n" + "\n".join(node_summaries)
            )

        # Recent conversation summary
        recent_messages = self._context.messages[-4:]  # Last 4 messages
        if recent_messages:
            conversation_parts = []
            for msg in recent_messages:
                role = msg.role.value.upper()
                content = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
                conversation_parts.append(f"  [{role}]: {content}")

            parts.append("RECENT CONVERSATION:\n" + "\n".join(conversation_parts))

        return "\n\n".join(parts)

    def clear_conversation(self) -> None:
        """Clear all conversation history but keep workflow."""
        self._context.messages.clear()
        self._context.last_intent = None
        logger.info("Conversation cleared")

    def clear_all(self) -> None:
        """Clear everything and start fresh session."""
        self._context = ConversationContext()
        logger.info(f"New session started: {self._context.session_id}")

    def get_conversation_summary(self) -> Dict[str, Any]:
        """
        Get summary of current conversation state.

        Returns:
            Dictionary with conversation statistics
        """
        return {
            "session_id": self._context.session_id,
            "message_count": self._context.message_count,
            "has_workflow": self._context.has_workflow,
            "workflow_node_count": len(self._context.current_workflow.get("nodes", {}))
            if self._context.current_workflow
            else 0,
            "can_undo": self._context.can_undo,
            "can_redo": self._context.can_redo,
            "undo_stack_size": len(self._context.workflow_history),
            "last_intent": self._context.last_intent.value if self._context.last_intent else None,
        }

    def set_intent(self, intent: UserIntent) -> None:
        """Set the detected intent for the last user message."""
        self._context.last_intent = intent

    def get_last_intent(self) -> Optional[UserIntent]:
        """Get the last detected intent."""
        return self._context.last_intent

    def export_context(self) -> Dict[str, Any]:
        """
        Export full conversation context for persistence.

        Returns:
            Serializable dictionary of full context
        """
        return {
            "session_id": self._context.session_id,
            "messages": [m.to_full_dict() for m in self._context.messages],
            "current_workflow": self._context.current_workflow,
            "workflow_history": [s.to_dict() for s in self._context.workflow_history],
            "created_at": self._context.created_at,
            "last_intent": self._context.last_intent.value if self._context.last_intent else None,
            "metadata": self._context.metadata,
        }

    def import_context(self, data: Dict[str, Any]) -> None:
        """
        Import conversation context from saved data.

        Args:
            data: Previously exported context dictionary
        """
        try:
            self._context.session_id = data.get("session_id", str(uuid.uuid4()))
            self._context.messages = [
                ConversationMessage.from_dict(m) for m in data.get("messages", [])
            ]
            self._context.current_workflow = data.get("current_workflow")
            self._context.workflow_history = [
                WorkflowSnapshot(**s) for s in data.get("workflow_history", [])
            ]
            self._context.created_at = data.get("created_at", time.time())
            intent_str = data.get("last_intent")
            self._context.last_intent = UserIntent(intent_str) if intent_str else None
            self._context.metadata = data.get("metadata", {})

            logger.info(
                f"Context imported: session={self._context.session_id}, "
                f"messages={len(self._context.messages)}"
            )
        except Exception as e:
            logger.error(f"Failed to import context: {e}")
            raise ValueError(f"Invalid context data: {e}") from e


__all__ = [
    "ConversationManager",
    "ConversationContext",
    "ConversationMessage",
    "WorkflowSnapshot",
    "MessageRole",
    "UserIntent",
]
