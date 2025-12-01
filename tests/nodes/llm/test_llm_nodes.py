"""Tests for LLM Nodes."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from casare_rpa.nodes.llm.llm_nodes import (
    LLMCompletionNode,
    LLMChatNode,
    LLMExtractDataNode,
    LLMSummarizeNode,
    LLMClassifyNode,
    LLMTranslateNode,
)
from casare_rpa.infrastructure.resources.llm_resource_manager import (
    LLMResourceManager,
    LLMResponse,
)


@pytest.fixture
def mock_execution_context():
    """Create mock execution context."""
    context = MagicMock()
    context.resources = {}
    context.resolve_value = lambda x: x
    context.get_variable = MagicMock(return_value=None)
    return context


@pytest.fixture
def mock_llm_manager():
    """Create mock LLM resource manager."""
    manager = MagicMock(spec=LLMResourceManager)
    manager.metrics = MagicMock()
    manager.metrics.total_tokens = 100
    return manager


@pytest.fixture
def mock_llm_response():
    """Create mock LLM response."""
    return LLMResponse(
        content="Test response",
        model="gpt-4o-mini",
        prompt_tokens=50,
        completion_tokens=20,
        total_tokens=70,
        finish_reason="stop",
    )


class TestLLMCompletionNode:
    """Tests for LLMCompletionNode."""

    def test_init(self):
        """Test node initialization."""
        node = LLMCompletionNode("test-node")
        assert node.name == "LLM Completion"
        assert node.NODE_CATEGORY == "AI/ML"

    def test_has_required_ports(self):
        """Test node has required ports."""
        node = LLMCompletionNode("test-node")

        # Check input ports (dict keyed by name)
        assert "prompt" in node.input_ports
        assert "model" in node.input_ports
        assert "temperature" in node.input_ports

        # Check output ports
        assert "response" in node.output_ports
        assert "tokens_used" in node.output_ports
        assert "success" in node.output_ports

    @pytest.mark.asyncio
    async def test_execute_missing_prompt(self, mock_execution_context):
        """Test execution fails without prompt."""
        node = LLMCompletionNode("test-node", config={"prompt": ""})

        result = await node.execute(mock_execution_context)

        assert result["success"] is False
        assert "required" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_execute_success(
        self, mock_execution_context, mock_llm_manager, mock_llm_response
    ):
        """Test successful completion."""
        node = LLMCompletionNode(
            "test-node",
            config={"prompt": "Say hello", "model": "gpt-4o-mini"},
        )

        mock_llm_manager.completion = AsyncMock(return_value=mock_llm_response)

        with patch.object(node, "_get_llm_manager", return_value=mock_llm_manager):
            result = await node.execute(mock_execution_context)

        assert result["success"] is True
        assert node.get_output_value("response") == "Test response"
        assert node.get_output_value("tokens_used") == 70


class TestLLMChatNode:
    """Tests for LLMChatNode."""

    def test_init(self):
        """Test node initialization."""
        node = LLMChatNode("test-node")
        assert node.name == "LLM Chat"

    def test_has_conversation_port(self):
        """Test node has conversation_id port."""
        node = LLMChatNode("test-node")

        assert "conversation_id" in node.input_ports
        assert "conversation_id" in node.output_ports

    @pytest.mark.asyncio
    async def test_execute_missing_message(self, mock_execution_context):
        """Test execution fails without message."""
        node = LLMChatNode("test-node", config={"message": ""})

        result = await node.execute(mock_execution_context)

        assert result["success"] is False
        assert "required" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_execute_success(
        self, mock_execution_context, mock_llm_manager, mock_llm_response
    ):
        """Test successful chat."""
        node = LLMChatNode("test-node", config={"message": "Hello!"})

        mock_llm_manager.chat = AsyncMock(return_value=(mock_llm_response, "conv-123"))

        with patch.object(node, "_get_llm_manager", return_value=mock_llm_manager):
            result = await node.execute(mock_execution_context)

        assert result["success"] is True
        assert node.get_output_value("conversation_id") == "conv-123"


class TestLLMExtractDataNode:
    """Tests for LLMExtractDataNode."""

    def test_init(self):
        """Test node initialization."""
        node = LLMExtractDataNode("test-node")
        assert node.name == "LLM Extract Data"

    def test_has_required_ports(self):
        """Test node has required ports."""
        node = LLMExtractDataNode("test-node")

        assert "text" in node.input_ports
        assert "schema" in node.input_ports
        assert "extracted_data" in node.output_ports

    @pytest.mark.asyncio
    async def test_execute_missing_text(self, mock_execution_context):
        """Test execution fails without text."""
        node = LLMExtractDataNode(
            "test-node",
            config={"text": "", "schema": {"name": "string"}},
        )

        result = await node.execute(mock_execution_context)

        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_execute_missing_schema(self, mock_execution_context):
        """Test execution fails without schema."""
        node = LLMExtractDataNode(
            "test-node",
            config={"text": "John is 30 years old", "schema": None},
        )

        result = await node.execute(mock_execution_context)

        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_execute_success(self, mock_execution_context, mock_llm_manager):
        """Test successful extraction."""
        node = LLMExtractDataNode(
            "test-node",
            config={
                "text": "John is 30 years old",
                "schema": {"name": "string", "age": "integer"},
            },
        )

        mock_llm_manager.extract_structured = AsyncMock(
            return_value={"name": "John", "age": 30}
        )

        with patch.object(node, "_get_llm_manager", return_value=mock_llm_manager):
            result = await node.execute(mock_execution_context)

        assert result["success"] is True
        assert node.get_output_value("extracted_data") == {"name": "John", "age": 30}


class TestLLMSummarizeNode:
    """Tests for LLMSummarizeNode."""

    def test_init(self):
        """Test node initialization."""
        node = LLMSummarizeNode("test-node")
        assert node.name == "LLM Summarize"

    def test_has_required_ports(self):
        """Test node has required ports."""
        node = LLMSummarizeNode("test-node")

        assert "text" in node.input_ports
        assert "max_length" in node.input_ports
        assert "style" in node.input_ports
        assert "summary" in node.output_ports
        assert "original_length" in node.output_ports

    @pytest.mark.asyncio
    async def test_execute_missing_text(self, mock_execution_context):
        """Test execution fails without text."""
        node = LLMSummarizeNode("test-node", config={"text": ""})

        result = await node.execute(mock_execution_context)

        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_execute_success(
        self, mock_execution_context, mock_llm_manager, mock_llm_response
    ):
        """Test successful summarization."""
        long_text = "This is a very long text " * 100
        node = LLMSummarizeNode(
            "test-node",
            config={"text": long_text, "style": "paragraph"},
        )

        summary_response = LLMResponse(
            content="This is a summary.",
            model="gpt-4o-mini",
            prompt_tokens=200,
            completion_tokens=10,
            total_tokens=210,
            finish_reason="stop",
        )
        mock_llm_manager.completion = AsyncMock(return_value=summary_response)

        with patch.object(node, "_get_llm_manager", return_value=mock_llm_manager):
            result = await node.execute(mock_execution_context)

        assert result["success"] is True
        assert node.get_output_value("summary") == "This is a summary."
        assert node.get_output_value("original_length") == len(long_text)


class TestLLMClassifyNode:
    """Tests for LLMClassifyNode."""

    def test_init(self):
        """Test node initialization."""
        node = LLMClassifyNode("test-node")
        assert node.name == "LLM Classify"

    def test_has_required_ports(self):
        """Test node has required ports."""
        node = LLMClassifyNode("test-node")

        assert "text" in node.input_ports
        assert "categories" in node.input_ports
        assert "multi_label" in node.input_ports
        assert "classification" in node.output_ports
        assert "classifications" in node.output_ports
        assert "confidence" in node.output_ports

    @pytest.mark.asyncio
    async def test_execute_missing_text(self, mock_execution_context):
        """Test execution fails without text."""
        node = LLMClassifyNode(
            "test-node",
            config={"text": "", "categories": ["positive", "negative"]},
        )

        result = await node.execute(mock_execution_context)

        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_execute_missing_categories(self, mock_execution_context):
        """Test execution fails without categories."""
        node = LLMClassifyNode(
            "test-node",
            config={"text": "This is great!", "categories": None},
        )

        result = await node.execute(mock_execution_context)

        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_execute_single_label(self, mock_execution_context, mock_llm_manager):
        """Test single-label classification."""
        node = LLMClassifyNode(
            "test-node",
            config={
                "text": "This is great!",
                "categories": ["positive", "negative", "neutral"],
                "multi_label": False,
            },
        )

        classify_response = LLMResponse(
            content='{"category": "positive", "confidence": 0.95}',
            model="gpt-4o-mini",
            prompt_tokens=50,
            completion_tokens=10,
            total_tokens=60,
            finish_reason="stop",
        )
        mock_llm_manager.completion = AsyncMock(return_value=classify_response)

        with patch.object(node, "_get_llm_manager", return_value=mock_llm_manager):
            result = await node.execute(mock_execution_context)

        assert result["success"] is True
        assert node.get_output_value("classification") == "positive"

    @pytest.mark.asyncio
    async def test_execute_multi_label(self, mock_execution_context, mock_llm_manager):
        """Test multi-label classification."""
        node = LLMClassifyNode(
            "test-node",
            config={
                "text": "This is a great technical document!",
                "categories": ["technical", "positive", "formal"],
                "multi_label": True,
            },
        )

        classify_response = LLMResponse(
            content='{"categories": ["technical", "positive"], "confidence": {"technical": 0.9, "positive": 0.8}}',
            model="gpt-4o-mini",
            prompt_tokens=50,
            completion_tokens=20,
            total_tokens=70,
            finish_reason="stop",
        )
        mock_llm_manager.completion = AsyncMock(return_value=classify_response)

        with patch.object(node, "_get_llm_manager", return_value=mock_llm_manager):
            result = await node.execute(mock_execution_context)

        assert result["success"] is True
        classifications = node.get_output_value("classifications")
        assert "technical" in classifications
        assert "positive" in classifications


class TestLLMTranslateNode:
    """Tests for LLMTranslateNode."""

    def test_init(self):
        """Test node initialization."""
        node = LLMTranslateNode("test-node")
        assert node.name == "LLM Translate"

    def test_has_required_ports(self):
        """Test node has required ports."""
        node = LLMTranslateNode("test-node")

        assert "text" in node.input_ports
        assert "target_language" in node.input_ports
        assert "source_language" in node.input_ports
        assert "translated_text" in node.output_ports
        assert "detected_language" in node.output_ports

    @pytest.mark.asyncio
    async def test_execute_missing_text(self, mock_execution_context):
        """Test execution fails without text."""
        node = LLMTranslateNode(
            "test-node",
            config={"text": "", "target_language": "Spanish"},
        )

        result = await node.execute(mock_execution_context)

        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_execute_missing_target_language(self, mock_execution_context):
        """Test execution fails without target language."""
        node = LLMTranslateNode(
            "test-node",
            config={"text": "Hello world", "target_language": ""},
        )

        result = await node.execute(mock_execution_context)

        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_execute_success(self, mock_execution_context, mock_llm_manager):
        """Test successful translation."""
        node = LLMTranslateNode(
            "test-node",
            config={"text": "Hello world", "target_language": "Spanish"},
        )

        translate_response = LLMResponse(
            content='{"translated_text": "Hola mundo", "detected_language": "English"}',
            model="gpt-4o-mini",
            prompt_tokens=30,
            completion_tokens=15,
            total_tokens=45,
            finish_reason="stop",
        )
        mock_llm_manager.completion = AsyncMock(return_value=translate_response)

        with patch.object(node, "_get_llm_manager", return_value=mock_llm_manager):
            result = await node.execute(mock_execution_context)

        assert result["success"] is True
        assert node.get_output_value("translated_text") == "Hola mundo"
        assert node.get_output_value("detected_language") == "English"

    @pytest.mark.asyncio
    async def test_execute_with_source_language(
        self, mock_execution_context, mock_llm_manager
    ):
        """Test translation with specified source language."""
        node = LLMTranslateNode(
            "test-node",
            config={
                "text": "Bonjour le monde",
                "target_language": "English",
                "source_language": "French",
            },
        )

        translate_response = LLMResponse(
            content='{"translated_text": "Hello world", "detected_language": "French"}',
            model="gpt-4o-mini",
            prompt_tokens=30,
            completion_tokens=15,
            total_tokens=45,
            finish_reason="stop",
        )
        mock_llm_manager.completion = AsyncMock(return_value=translate_response)

        with patch.object(node, "_get_llm_manager", return_value=mock_llm_manager):
            result = await node.execute(mock_execution_context)

        assert result["success"] is True
        assert node.get_output_value("translated_text") == "Hello world"
