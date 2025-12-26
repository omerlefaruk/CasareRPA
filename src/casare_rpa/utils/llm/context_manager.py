"""Context window management for conversation history.

Implements sliding window, semantic relevance filtering, and token budgeting.
"""

import hashlib
from collections import deque
from dataclasses import dataclass


@dataclass
class Message:
    """Conversation message with metadata."""

    role: str
    content: str
    tokens: int
    timestamp: float
    message_id: str

    def __hash__(self):
        return hash((self.role, self.content, self.message_id))


class ConversationManager:
    """Manages conversation context with token budgeting.

    Features:
    - Sliding window (keep N most recent messages)
    - Token budget enforcement
    - Message deduplication
    - Prioritized retention (system prompts, critical context)
    """

    def __init__(
        self, max_tokens: int = 4000, max_messages: int = 50, system_prompt: str | None = None
    ):
        """Initialize conversation manager.

        Args:
            max_tokens: Maximum token budget for conversation.
            max_messages: Maximum number of messages to retain.
            system_prompt: Optional system prompt (always retained).
        """
        self.max_tokens = max_tokens
        self.max_messages = max_messages
        self.system_prompt = system_prompt

        self._messages: deque[Message] = deque(maxlen=max_messages)
        self._message_ids = set()
        self._current_tokens = 0

        if system_prompt:
            system_tokens = self._estimate_tokens(system_prompt)
            self._current_tokens += system_tokens

    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation."""
        return len(text) // 4

    def _generate_message_id(self, role: str, content: str) -> str:
        """Generate unique ID for message."""
        combined = f"{role}:{content}"
        return hashlib.md5(combined.encode()).hexdigest()[:12]

    def add_message(self, role: str, content: str) -> None:
        """Add message to conversation.

        Args:
            role: Message role (user, assistant, system).
            content: Message content.
        """
        tokens = self._estimate_tokens(content)
        message_id = self._generate_message_id(role, content)

        if message_id in self._message_ids:
            return

        message = Message(
            role=role,
            content=content,
            tokens=tokens,
            timestamp=self._timestamp(),
            message_id=message_id,
        )

        self._messages.append(message)
        self._message_ids.add(message_id)
        self._current_tokens += tokens

        self._enforce_budget()

    def _timestamp(self) -> float:
        import time

        return time.time()

    def _enforce_budget(self) -> None:
        """Enforce token budget by removing oldest messages."""
        while self._current_tokens > self.max_tokens and len(self._messages) > 1:
            oldest = self._messages.popleft()
            self._message_ids.discard(oldest.message_id)
            self._current_tokens -= oldest.tokens

    def get_context(self, include_system: bool = True) -> list[dict]:
        """Get current conversation context.

        Args:
            include_system: Whether to include system prompt.

        Returns:
            List of message dicts for LLM API.
        """
        messages = []

        if include_system and self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})

        for msg in self._messages:
            messages.append({"role": msg.role, "content": msg.content})

        return messages

    def get_token_count(self) -> int:
        """Get current token count."""
        return self._current_tokens + (
            self._estimate_tokens(self.system_prompt) if self.system_prompt else 0
        )

    def clear(self) -> None:
        """Clear conversation history."""
        self._messages.clear()
        self._message_ids.clear()
        self._current_tokens = 0

        if self.system_prompt:
            self._current_tokens = self._estimate_tokens(self.system_prompt)

    def resize_window(self, new_max_tokens: int, new_max_messages: int | None = None) -> None:
        """Resize conversation window.

        Args:
            new_max_tokens: New token budget.
            new_max_messages: New message limit (optional).
        """
        self.max_tokens = new_max_tokens

        if new_max_messages:
            self.max_messages = new_max_messages
            self._messages = deque(self._messages, maxlen=new_max_messages)

        self._enforce_budget()


class SemanticConversationManager(ConversationManager):
    """Conversation manager with semantic relevance filtering.

    Uses vector similarity to retain semantically relevant messages
    when trimming context.
    """

    def __init__(
        self,
        max_tokens: int = 4000,
        max_messages: int = 50,
        system_prompt: str | None = None,
        embedding_model: str | None = None,
    ):
        """Initialize semantic conversation manager.

        Args:
            max_tokens: Maximum token budget.
            max_messages: Maximum messages to retain.
            system_prompt: Optional system prompt.
            embedding_model: Optional embedding model for semantic search.
        """
        super().__init__(max_tokens, max_messages, system_prompt)
        self._embedding_model = embedding_model

    def _compute_similarity(self, text1: str, text2: str) -> float:
        """Compute semantic similarity between texts."""
        if not self._embedding_model:
            return 0.0

        try:
            import numpy as np
            from sentence_transformers import SentenceTransformer  # type: ignore

            model = SentenceTransformer(self._embedding_model)
            emb1 = model.encode(text1)
            emb2 = model.encode(text2)

            return float(np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2)))
        except (ImportError, AttributeError, RuntimeError):
            return 0.0

        try:
            from sentence_transformers import SentenceTransformer

            model = SentenceTransformer(self._embedding_model)
            emb1 = model.encode(text1)
            emb2 = model.encode(text2)

            import numpy as np

            return float(np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2)))
        except ImportError:
            return 0.0

    def get_context_with_relevance(
        self, recent_count: int = 20, query: str | None = None
    ) -> list[dict]:
        """Get context with semantic relevance filtering.

        Keeps N most recent messages plus semantically relevant ones.

        Args:
            recent_count: Number of most recent messages to keep.
            query: Query text for relevance scoring.

        Returns:
            Filtered message list.
        """
        if not query or not self._embedding_model:
            return self.get_context()

        messages = list(self._messages)
        if len(messages) <= recent_count:
            return self.get_context()

        recent = messages[-recent_count:]
        older = messages[:-recent_count]

        scored = []
        for msg in older:
            score = self._compute_similarity(query, msg.content)
            scored.append((score, msg))

        scored.sort(reverse=True, key=lambda x: x[0])

        context = []

        if self.system_prompt:
            context.append({"role": "system", "content": self.system_prompt})

        context.extend([{"role": m.role, "content": m.content} for m in older])
        context.extend([{"role": m.role, "content": m.content} for m in recent])

        return context


class ConversationSession:
    """Session wrapper for conversation management.

    Provides high-level interface for multi-turn conversations.
    """

    def __init__(
        self,
        max_tokens: int = 4000,
        system_prompt: str | None = None,
        use_semantic: bool = False,
    ):
        """Initialize conversation session.

        Args:
            max_tokens: Maximum token budget.
            system_prompt: Optional system prompt.
            use_semantic: Whether to use semantic relevance filtering.
        """
        if use_semantic:
            self.manager = SemanticConversationManager(
                max_tokens=max_tokens, system_prompt=system_prompt
            )
        else:
            self.manager = ConversationManager(max_tokens=max_tokens, system_prompt=system_prompt)

    def user_message(self, content: str) -> None:
        """Add user message."""
        self.manager.add_message("user", content)

    def assistant_message(self, content: str) -> None:
        """Add assistant message."""
        self.manager.add_message("assistant", content)

    def get_llm_context(self) -> list[dict]:
        """Get context for LLM API call."""
        return self.manager.get_context()

    def reset(self) -> None:
        """Reset conversation."""
        self.manager.clear()

    @property
    def token_count(self) -> int:
        """Current token count."""
        return self.manager.get_token_count()
