"""Tests for LLM Resource Manager."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from casare_rpa.infrastructure.resources.llm_resource_manager import (
    LLMResourceManager,
    LLMConfig,
    LLMProvider,
    LLMResponse,
    LLMUsageMetrics,
    ChatMessage,
    ConversationHistory,
)


class TestLLMConfig:
    """Tests for LLMConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = LLMConfig()
        assert config.provider == LLMProvider.OPENAI
        assert config.model == "gpt-4o-mini"
        assert config.api_key is None
        assert config.timeout == 60.0
        assert config.max_retries == 3

    def test_custom_config(self):
        """Test custom configuration."""
        config = LLMConfig(
            provider=LLMProvider.ANTHROPIC,
            model="claude-3-5-sonnet-latest",
            api_key="test-key",
            timeout=30.0,
        )
        assert config.provider == LLMProvider.ANTHROPIC
        assert config.model == "claude-3-5-sonnet-latest"
        assert config.api_key == "test-key"
        assert config.timeout == 30.0


class TestLLMUsageMetrics:
    """Tests for LLMUsageMetrics."""

    def test_initial_metrics(self):
        """Test initial metric values."""
        metrics = LLMUsageMetrics()
        assert metrics.prompt_tokens == 0
        assert metrics.completion_tokens == 0
        assert metrics.total_tokens == 0
        assert metrics.total_requests == 0
        assert metrics.total_errors == 0
        assert metrics.total_cost_usd == 0.0

    def test_add_usage(self):
        """Test adding usage metrics."""
        metrics = LLMUsageMetrics()
        metrics.add_usage(100, 50, 0.01)

        assert metrics.prompt_tokens == 100
        assert metrics.completion_tokens == 50
        assert metrics.total_tokens == 150
        assert metrics.total_requests == 1
        assert metrics.total_cost_usd == 0.01
        assert metrics.last_request_time is not None

    def test_add_multiple_usages(self):
        """Test accumulating multiple usages."""
        metrics = LLMUsageMetrics()
        metrics.add_usage(100, 50, 0.01)
        metrics.add_usage(200, 100, 0.02)

        assert metrics.prompt_tokens == 300
        assert metrics.completion_tokens == 150
        assert metrics.total_tokens == 450
        assert metrics.total_requests == 2
        assert metrics.total_cost_usd == 0.03

    def test_record_error(self):
        """Test recording errors."""
        metrics = LLMUsageMetrics()
        metrics.record_error()
        metrics.record_error()

        assert metrics.total_errors == 2
        assert metrics.last_request_time is not None


class TestChatMessage:
    """Tests for ChatMessage."""

    def test_create_message(self):
        """Test creating a chat message."""
        msg = ChatMessage(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.name is None

    def test_to_dict(self):
        """Test converting to dictionary."""
        msg = ChatMessage(role="assistant", content="Hi there!")
        result = msg.to_dict()

        assert result == {"role": "assistant", "content": "Hi there!"}

    def test_to_dict_with_name(self):
        """Test converting to dictionary with name."""
        msg = ChatMessage(role="user", content="Hello", name="Alice")
        result = msg.to_dict()

        assert result == {"role": "user", "content": "Hello", "name": "Alice"}


class TestConversationHistory:
    """Tests for ConversationHistory."""

    def test_create_conversation(self):
        """Test creating a conversation."""
        conv = ConversationHistory(conversation_id="test-123")
        assert conv.conversation_id == "test-123"
        assert len(conv.messages) == 0
        assert conv.system_prompt is None

    def test_add_message(self):
        """Test adding messages."""
        conv = ConversationHistory(conversation_id="test")
        conv.add_message("user", "Hello")
        conv.add_message("assistant", "Hi!")

        assert len(conv.messages) == 2
        assert conv.messages[0].role == "user"
        assert conv.messages[1].role == "assistant"

    def test_get_messages_without_system(self):
        """Test getting messages without system prompt."""
        conv = ConversationHistory(conversation_id="test")
        conv.add_message("user", "Hello")

        msgs = conv.get_messages()
        assert len(msgs) == 1
        assert msgs[0]["role"] == "user"

    def test_get_messages_with_system(self):
        """Test getting messages with system prompt."""
        conv = ConversationHistory(
            conversation_id="test",
            system_prompt="You are a helpful assistant.",
        )
        conv.add_message("user", "Hello")

        msgs = conv.get_messages()
        assert len(msgs) == 2
        assert msgs[0]["role"] == "system"
        assert msgs[1]["role"] == "user"

    def test_clear(self):
        """Test clearing conversation."""
        conv = ConversationHistory(
            conversation_id="test",
            system_prompt="System prompt",
        )
        conv.add_message("user", "Hello")
        conv.clear()

        assert len(conv.messages) == 0
        assert conv.system_prompt == "System prompt"  # System prompt preserved


class TestLLMResourceManager:
    """Tests for LLMResourceManager."""

    def test_init(self):
        """Test initialization."""
        manager = LLMResourceManager()
        assert manager.config is None
        assert manager.metrics.total_requests == 0
        assert len(manager._conversations) == 0

    def test_configure(self):
        """Test configuration."""
        manager = LLMResourceManager()
        config = LLMConfig(
            provider=LLMProvider.OPENAI,
            model="gpt-4o",
            api_key="test-key",
        )
        manager.configure(config)

        assert manager.config == config
        assert manager.config.model == "gpt-4o"

    def test_get_model_string_openai(self):
        """Test model string for OpenAI."""
        manager = LLMResourceManager()
        config = LLMConfig(provider=LLMProvider.OPENAI, model="gpt-4o")
        manager.configure(config)

        model_str = manager._get_model_string()
        assert model_str == "gpt-4o"

    def test_get_model_string_azure(self):
        """Test model string for Azure."""
        manager = LLMResourceManager()
        config = LLMConfig(provider=LLMProvider.AZURE, model="my-deployment")
        manager.configure(config)

        model_str = manager._get_model_string()
        assert model_str == "azure/my-deployment"

    def test_get_model_string_ollama(self):
        """Test model string for Ollama."""
        manager = LLMResourceManager()
        config = LLMConfig(provider=LLMProvider.OLLAMA, model="llama3")
        manager.configure(config)

        model_str = manager._get_model_string()
        assert model_str == "ollama/llama3"

    def test_calculate_cost(self):
        """Test cost calculation."""
        manager = LLMResourceManager()

        # GPT-4o pricing
        cost = manager._calculate_cost("gpt-4o", 1000, 500)
        assert cost > 0

        # Unknown model (zero cost)
        cost = manager._calculate_cost("unknown-model", 1000, 500)
        assert cost == 0

    def test_get_conversation_not_found(self):
        """Test getting non-existent conversation."""
        manager = LLMResourceManager()
        result = manager.get_conversation("nonexistent")
        assert result is None

    def test_clear_conversation(self):
        """Test clearing a conversation."""
        manager = LLMResourceManager()
        conv = ConversationHistory(conversation_id="test-123")
        conv.add_message("user", "Hello")
        manager._conversations["test-123"] = conv

        result = manager.clear_conversation("test-123")
        assert result is True
        assert len(manager._conversations["test-123"].messages) == 0

    def test_delete_conversation(self):
        """Test deleting a conversation."""
        manager = LLMResourceManager()
        conv = ConversationHistory(conversation_id="test-123")
        manager._conversations["test-123"] = conv

        result = manager.delete_conversation("test-123")
        assert result is True
        assert "test-123" not in manager._conversations

    def test_delete_nonexistent_conversation(self):
        """Test deleting non-existent conversation."""
        manager = LLMResourceManager()
        result = manager.delete_conversation("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_completion_success(self):
        """Test successful completion."""
        manager = LLMResourceManager()
        config = LLMConfig(provider=LLMProvider.OPENAI, api_key="test")
        manager.configure(config)

        # Mock litellm
        mock_response = {
            "choices": [{"message": {"content": "Hello!"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        }

        with patch.object(manager, "_ensure_initialized") as mock_init:
            mock_litellm = MagicMock()
            mock_litellm.acompletion = AsyncMock(return_value=mock_response)
            mock_init.return_value = mock_litellm

            response = await manager.completion(
                prompt="Say hello",
                model="gpt-4o-mini",
                temperature=0.7,
            )

            assert response.content == "Hello!"
            assert response.total_tokens == 15
            assert manager.metrics.total_requests == 1

    @pytest.mark.asyncio
    async def test_chat_creates_conversation(self):
        """Test chat creates new conversation."""
        manager = LLMResourceManager()
        config = LLMConfig(provider=LLMProvider.OPENAI, api_key="test")
        manager.configure(config)

        mock_response = {
            "choices": [{"message": {"content": "Hi!"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        }

        with patch.object(manager, "_ensure_initialized") as mock_init:
            mock_litellm = MagicMock()
            mock_litellm.acompletion = AsyncMock(return_value=mock_response)
            mock_init.return_value = mock_litellm

            response, conv_id = await manager.chat(
                message="Hello",
                system_prompt="You are helpful.",
            )

            assert response.content == "Hi!"
            assert conv_id is not None
            assert conv_id in manager._conversations
            assert (
                len(manager._conversations[conv_id].messages) == 2
            )  # user + assistant

    @pytest.mark.asyncio
    async def test_chat_maintains_history(self):
        """Test chat maintains conversation history."""
        manager = LLMResourceManager()
        config = LLMConfig(provider=LLMProvider.OPENAI, api_key="test")
        manager.configure(config)

        mock_response = {
            "choices": [{"message": {"content": "Response"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        }

        with patch.object(manager, "_ensure_initialized") as mock_init:
            mock_litellm = MagicMock()
            mock_litellm.acompletion = AsyncMock(return_value=mock_response)
            mock_init.return_value = mock_litellm

            # First message
            _, conv_id = await manager.chat(message="First")
            # Second message in same conversation
            _, _ = await manager.chat(message="Second", conversation_id=conv_id)

            conv = manager.get_conversation(conv_id)
            assert len(conv.messages) == 4  # 2 user + 2 assistant

    @pytest.mark.asyncio
    async def test_extract_structured(self):
        """Test structured data extraction."""
        manager = LLMResourceManager()
        config = LLMConfig(provider=LLMProvider.OPENAI, api_key="test")
        manager.configure(config)

        mock_response = {
            "choices": [
                {
                    "message": {"content": '{"name": "John", "age": 30}'},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 50, "completion_tokens": 10, "total_tokens": 60},
        }

        with patch.object(manager, "_ensure_initialized") as mock_init:
            mock_litellm = MagicMock()
            mock_litellm.acompletion = AsyncMock(return_value=mock_response)
            mock_init.return_value = mock_litellm

            result = await manager.extract_structured(
                text="My name is John and I am 30 years old.",
                schema={"name": "string", "age": "integer"},
            )

            assert result["name"] == "John"
            assert result["age"] == 30

    @pytest.mark.asyncio
    async def test_cleanup(self):
        """Test cleanup."""
        manager = LLMResourceManager()
        manager._conversations["test"] = ConversationHistory(conversation_id="test")

        await manager.cleanup()

        assert len(manager._conversations) == 0

    def test_repr(self):
        """Test string representation."""
        manager = LLMResourceManager()
        repr_str = repr(manager)

        assert "LLMResourceManager" in repr_str
        assert "not configured" in repr_str

        manager.configure(LLMConfig(provider=LLMProvider.ANTHROPIC, model="claude"))
        repr_str = repr(manager)

        assert "anthropic" in repr_str
        assert "claude" in repr_str
