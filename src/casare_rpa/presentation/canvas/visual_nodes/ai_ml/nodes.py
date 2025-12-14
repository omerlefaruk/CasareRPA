"""Visual nodes for AI/ML category.

Provides visual node wrappers for LLM operations including:
- Text completion
- Multi-turn chat
- Data extraction
- Summarization
- Classification
- Translation

Features:
- Dynamic model filtering based on selected credential provider
- Live model fetching from provider APIs (cached)
"""

from typing import Any, List, Tuple

from loguru import logger

from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode


def get_llm_credentials() -> List[Tuple[str, str]]:
    """Get available LLM credentials for dropdown.

    Returns:
        List of (id, display_name) tuples, with "Auto-detect" as first option.
    """
    credentials = [("auto", "Auto-detect from model")]

    try:
        from casare_rpa.infrastructure.security.credential_store import (
            get_credential_store,
        )

        store = get_credential_store()
        for cred in store.list_credentials(category="llm"):
            credentials.append((cred["id"], cred["name"]))
    except ImportError:
        pass

    return credentials


def get_models_for_credential(credential_name: str) -> List[str]:
    """Get models filtered by the credential's provider.

    Args:
        credential_name: The selected credential name

    Returns:
        List of model IDs for that provider, or all models if auto-detect
    """
    try:
        from casare_rpa.infrastructure.resources.llm_model_provider import (
            get_models_for_credential as _get_models,
        )

        return _get_models(credential_name)
    except ImportError:
        # Fallback to all models
        all_models = []
        for models in LLM_MODELS.values():
            all_models.extend(models)
        return all_models


# Available models organized by provider (fallback defaults)
LLM_MODELS = {
    "OpenAI": [
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4-turbo",
        "gpt-4",
        "gpt-3.5-turbo",
        "o1-preview",
        "o1-mini",
    ],
    "Anthropic": [
        "claude-3-5-sonnet-latest",
        "claude-3-5-haiku-latest",
        "claude-3-opus-latest",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307",
    ],
    "Google": [
        "gemini-1.5-pro",
        "gemini-1.5-flash",
        "gemini-2.0-flash-exp",
    ],
    "Mistral": [
        "mistral-large-latest",
        "mistral-medium-latest",
        "mistral-small-latest",
        "codestral-latest",
    ],
    "Groq": [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "mixtral-8x7b-32768",
    ],
    "DeepSeek": [
        "deepseek-chat",
        "deepseek-coder",
    ],
    "Local (Ollama)": [
        "ollama/llama3.2",
        "ollama/mistral",
        "ollama/codellama",
        "ollama/phi3",
    ],
}

# Flat list of all models for dropdown
ALL_MODELS = []
for provider, models in LLM_MODELS.items():
    ALL_MODELS.extend(models)


class LLMVisualNodeMixin:
    """Mixin for LLM visual nodes with credential-model linking.

    When credential selection changes, the model dropdown is automatically
    filtered to show only models from that provider.
    """

    _model_widget: Any = None
    _credential_widget: Any = None

    def _setup_credential_model_link(self) -> None:
        """Setup the link between credential and model dropdowns."""
        try:
            cred_widget = self.get_widget("credential")
            model_widget = self.get_widget("model")

            if cred_widget and model_widget:
                self._credential_widget = cred_widget
                self._model_widget = model_widget

                # Connect credential change to model update
                if hasattr(cred_widget, "value_changed"):
                    cred_widget.value_changed.connect(self._on_credential_changed)
                elif hasattr(cred_widget, "currentTextChanged"):
                    cred_widget.currentTextChanged.connect(self._on_credential_changed)

        except Exception as e:
            logger.debug(f"Could not setup credential-model link: {e}")

    def _on_credential_changed(self, property_name: str, credential_name: str) -> None:
        """Handle credential selection change - update model dropdown.

        Note: NodeGraphQt's value_changed signal emits (property_name, value).
        """
        try:
            if not self._model_widget:
                return

            # Get models for this credential's provider
            models = get_models_for_credential(credential_name)

            # Update model dropdown using NodeGraphQt widget API
            # NodeComboBox has: clear(), add_items(), get_value(), set_value()
            if hasattr(self._model_widget, "clear") and hasattr(
                self._model_widget, "add_items"
            ):
                current = self._model_widget.get_value()
                self._model_widget.clear()
                self._model_widget.add_items(models)

                # Restore selection if model exists in new list
                if current in models:
                    self._model_widget.set_value(current)
                elif models:
                    self._model_widget.set_value(models[0])

            logger.debug(
                f"Updated model dropdown for '{credential_name}': {len(models)} models"
            )

        except Exception as e:
            logger.warning(f"Failed to update model dropdown: {e}")


class VisualLLMCompletionNode(VisualNode, LLMVisualNodeMixin):
    """Visual representation of LLMCompletionNode.

    Generate text completion from a prompt using LLM.
    """

    __identifier__ = "casare_rpa.ai_ml"
    NODE_NAME = "LLM Completion"
    NODE_CATEGORY = "ai_ml"

    def __init__(self) -> None:
        """Initialize LLM completion node."""
        super().__init__()
        self._create_widgets()
        self._setup_credential_model_link()

    def _create_widgets(self) -> None:
        """Create node widgets for configuration."""
        # Credential selector - changing this filters the model dropdown
        cred_items = [name for _, name in get_llm_credentials()]
        self.add_combo_menu("credential", "API Key", items=cred_items)

        self.add_text_input("prompt", "Prompt", placeholder_text="Enter your prompt...")
        self.add_combo_menu("model", "Model", items=ALL_MODELS)
        self.set_property("model", "gpt-4o-mini")
        self.add_text_input(
            "system_prompt",
            "System Prompt",
            placeholder_text="Optional system prompt...",
        )
        self.add_text_input("temperature", "Temperature", text="0.7")
        self.add_text_input("max_tokens", "Max Tokens", text="1000")

    def setup_ports(self) -> None:
        """Setup ports."""
        # Execution flow
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")

        # Data inputs
        self.add_typed_input("prompt", DataType.STRING)
        self.add_typed_input("model", DataType.STRING)
        self.add_typed_input("system_prompt", DataType.STRING)
        self.add_typed_input("temperature", DataType.FLOAT)
        self.add_typed_input("max_tokens", DataType.INTEGER)

        # Data outputs
        self.add_typed_output("response", DataType.STRING)
        self.add_typed_output("tokens_used", DataType.INTEGER)
        self.add_typed_output("model_used", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualLLMChatNode(VisualNode, LLMVisualNodeMixin):
    """Visual representation of LLMChatNode.

    Multi-turn chat conversation with an LLM.
    """

    __identifier__ = "casare_rpa.ai_ml"
    NODE_NAME = "LLM Chat"
    NODE_CATEGORY = "ai_ml"

    def __init__(self) -> None:
        """Initialize LLM chat node."""
        super().__init__()
        self._create_widgets()
        self._setup_credential_model_link()

    def _create_widgets(self) -> None:
        """Create node widgets for configuration."""
        # Credential selector - changing this filters the model dropdown
        cred_items = [name for _, name in get_llm_credentials()]
        self.add_combo_menu("credential", "API Key", items=cred_items)

        self.add_text_input(
            "message", "Message", placeholder_text="Enter your message..."
        )
        self.add_text_input(
            "conversation_id",
            "Conversation ID",
            placeholder_text="Optional - for continuing chat",
        )
        self.add_combo_menu("model", "Model", items=ALL_MODELS)
        self.set_property("model", "gpt-4o-mini")
        self.add_text_input(
            "system_prompt",
            "System Prompt",
            placeholder_text="Optional system prompt...",
        )
        self.add_text_input("temperature", "Temperature", text="0.7")
        self.add_text_input("max_tokens", "Max Tokens", text="1000")

    def setup_ports(self) -> None:
        """Setup ports."""
        # Execution flow
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")

        # Data inputs
        self.add_typed_input("message", DataType.STRING)
        self.add_typed_input("conversation_id", DataType.STRING)
        self.add_typed_input("model", DataType.STRING)
        self.add_typed_input("system_prompt", DataType.STRING)
        self.add_typed_input("temperature", DataType.FLOAT)
        self.add_typed_input("max_tokens", DataType.INTEGER)

        # Data outputs
        self.add_typed_output("response", DataType.STRING)
        self.add_typed_output("conversation_id", DataType.STRING)
        self.add_typed_output("tokens_used", DataType.INTEGER)
        self.add_typed_output("model_used", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualLLMExtractDataNode(VisualNode, LLMVisualNodeMixin):
    """Visual representation of LLMExtractDataNode.

    Extract structured data from text using JSON schema.
    """

    __identifier__ = "casare_rpa.ai_ml"
    NODE_NAME = "LLM Extract Data"
    NODE_CATEGORY = "ai_ml"

    def __init__(self) -> None:
        """Initialize LLM extract data node."""
        super().__init__()
        self._create_widgets()
        self._setup_credential_model_link()

    def _create_widgets(self) -> None:
        """Create node widgets for configuration."""
        # Credential selector - changing this filters the model dropdown
        cred_items = [name for _, name in get_llm_credentials()]
        self.add_combo_menu("credential", "API Key", items=cred_items)

        self.add_text_input(
            "text", "Text", placeholder_text="Text to extract data from..."
        )
        self.add_text_input(
            "schema",
            "JSON Schema",
            placeholder_text='{"name": "string", "age": "integer"}',
        )
        self.add_combo_menu("model", "Model", items=ALL_MODELS)
        self.set_property("model", "gpt-4o-mini")
        self.add_text_input("temperature", "Temperature", text="0.0")

    def setup_ports(self) -> None:
        """Setup ports."""
        # Execution flow
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")

        # Data inputs
        self.add_typed_input("text", DataType.STRING)
        self.add_typed_input("schema", DataType.DICT)
        self.add_typed_input("model", DataType.STRING)
        self.add_typed_input("temperature", DataType.FLOAT)

        # Data outputs
        self.add_typed_output("extracted_data", DataType.DICT)
        self.add_typed_output("raw_response", DataType.STRING)
        self.add_typed_output("tokens_used", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualLLMSummarizeNode(VisualNode, LLMVisualNodeMixin):
    """Visual representation of LLMSummarizeNode.

    Summarize text using an LLM.
    """

    __identifier__ = "casare_rpa.ai_ml"
    NODE_NAME = "LLM Summarize"
    NODE_CATEGORY = "ai_ml"

    def __init__(self) -> None:
        """Initialize LLM summarize node."""
        super().__init__()
        self._create_widgets()
        self._setup_credential_model_link()

    def _create_widgets(self) -> None:
        """Create node widgets for configuration."""
        # Credential selector - changing this filters the model dropdown
        cred_items = [name for _, name in get_llm_credentials()]
        self.add_combo_menu("credential", "API Key", items=cred_items)

        self.add_text_input("text", "Text", placeholder_text="Text to summarize...")
        self.add_text_input("max_length", "Max Length (words)", text="200")
        self.add_combo_menu(
            "style", "Style", items=["paragraph", "bullet_points", "key_points"]
        )
        self.add_combo_menu("model", "Model", items=ALL_MODELS)
        self.set_property("model", "gpt-4o-mini")
        self.add_text_input("temperature", "Temperature", text="0.5")

    def setup_ports(self) -> None:
        """Setup ports."""
        # Execution flow
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")

        # Data inputs
        self.add_typed_input("text", DataType.STRING)
        self.add_typed_input("max_length", DataType.INTEGER)
        self.add_typed_input("style", DataType.STRING)
        self.add_typed_input("model", DataType.STRING)
        self.add_typed_input("temperature", DataType.FLOAT)

        # Data outputs
        self.add_typed_output("summary", DataType.STRING)
        self.add_typed_output("original_length", DataType.INTEGER)
        self.add_typed_output("summary_length", DataType.INTEGER)
        self.add_typed_output("tokens_used", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualLLMClassifyNode(VisualNode, LLMVisualNodeMixin):
    """Visual representation of LLMClassifyNode.

    Classify text into categories using an LLM.
    """

    __identifier__ = "casare_rpa.ai_ml"
    NODE_NAME = "LLM Classify"
    NODE_CATEGORY = "ai_ml"

    def __init__(self) -> None:
        """Initialize LLM classify node."""
        super().__init__()
        self._create_widgets()
        self._setup_credential_model_link()

    def _create_widgets(self) -> None:
        """Create node widgets for configuration."""
        # Credential selector - changing this filters the model dropdown
        cred_items = [name for _, name in get_llm_credentials()]
        self.add_combo_menu("credential", "API Key", items=cred_items)

        self.add_text_input("text", "Text", placeholder_text="Text to classify...")
        self.add_text_input(
            "categories", "Categories", placeholder_text="positive, negative, neutral"
        )
        self.add_checkbox("multi_label", label="", text="Multi-label", state=False)
        self.add_combo_menu("model", "Model", items=ALL_MODELS)
        self.set_property("model", "gpt-4o-mini")
        self.add_text_input("temperature", "Temperature", text="0.0")

    def setup_ports(self) -> None:
        """Setup ports."""
        # Execution flow
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")

        # Data inputs
        self.add_typed_input("text", DataType.STRING)
        self.add_typed_input("categories", DataType.LIST)
        self.add_typed_input("multi_label", DataType.BOOLEAN)
        self.add_typed_input("model", DataType.STRING)
        self.add_typed_input("temperature", DataType.FLOAT)

        # Data outputs
        self.add_typed_output("classification", DataType.STRING)
        self.add_typed_output("classifications", DataType.LIST)
        self.add_typed_output("confidence", DataType.DICT)
        self.add_typed_output("tokens_used", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualLLMTranslateNode(VisualNode, LLMVisualNodeMixin):
    """Visual representation of LLMTranslateNode.

    Translate text to another language using an LLM.
    """

    __identifier__ = "casare_rpa.ai_ml"
    NODE_NAME = "LLM Translate"
    NODE_CATEGORY = "ai_ml"

    def __init__(self) -> None:
        """Initialize LLM translate node."""
        super().__init__()
        self._create_widgets()
        self._setup_credential_model_link()

    def _create_widgets(self) -> None:
        """Create node widgets for configuration."""
        # Credential selector - changing this filters the model dropdown
        cred_items = [name for _, name in get_llm_credentials()]
        self.add_combo_menu("credential", "API Key", items=cred_items)

        self.add_text_input("text", "Text", placeholder_text="Text to translate...")
        self.add_text_input(
            "target_language",
            "Target Language",
            placeholder_text="Spanish, French, German...",
        )
        self.add_text_input(
            "source_language",
            "Source Language",
            placeholder_text="Optional - auto-detect if empty",
        )
        self.add_combo_menu("model", "Model", items=ALL_MODELS)
        self.set_property("model", "gpt-4o-mini")
        self.add_text_input("temperature", "Temperature", text="0.3")

    def setup_ports(self) -> None:
        """Setup ports."""
        # Execution flow
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")

        # Data inputs
        self.add_typed_input("text", DataType.STRING)
        self.add_typed_input("target_language", DataType.STRING)
        self.add_typed_input("source_language", DataType.STRING)
        self.add_typed_input("model", DataType.STRING)
        self.add_typed_input("temperature", DataType.FLOAT)

        # Data outputs
        self.add_typed_output("translated_text", DataType.STRING)
        self.add_typed_output("detected_language", DataType.STRING)
        self.add_typed_output("tokens_used", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualAIConditionNode(VisualNode, LLMVisualNodeMixin):
    """Visual representation of AIConditionNode.

    Evaluate natural language conditions using AI.
    Returns true/false with confidence score.
    """

    __identifier__ = "casare_rpa.ai_ml"
    NODE_NAME = "AI Condition"
    NODE_CATEGORY = "ai_ml"

    def __init__(self) -> None:
        """Initialize AI condition node."""
        super().__init__()
        self._create_widgets()
        self._setup_credential_model_link()

    def _create_widgets(self) -> None:
        """Create node widgets for configuration."""
        cred_items = [name for _, name in get_llm_credentials()]
        self.add_combo_menu("credential", "API Key", items=cred_items)

        self.add_text_input(
            "condition",
            "Condition",
            placeholder_text="Is the email about a complaint?",
        )
        self.add_text_input(
            "context",
            "Context",
            placeholder_text="Data to evaluate against...",
        )
        self.add_combo_menu("model", "Model", items=ALL_MODELS)
        self.set_property("model", "gpt-4o-mini")
        self.add_text_input("temperature", "Temperature", text="0.0")

    def setup_ports(self) -> None:
        """Setup ports."""
        # Execution flow - branching outputs
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_true")
        self.add_exec_output("exec_false")

        # Data inputs
        self.add_typed_input("condition", DataType.STRING)
        self.add_typed_input("context", DataType.ANY)
        self.add_typed_input("model", DataType.STRING)
        self.add_typed_input("temperature", DataType.FLOAT)

        # Data outputs
        self.add_typed_output("result", DataType.BOOLEAN)
        self.add_typed_output("confidence", DataType.FLOAT)
        self.add_typed_output("reasoning", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualAISwitchNode(VisualNode, LLMVisualNodeMixin):
    """Visual representation of AISwitchNode.

    Multi-way branching using AI classification.
    Routes to one of multiple output paths.
    """

    __identifier__ = "casare_rpa.ai_ml"
    NODE_NAME = "AI Switch"
    NODE_CATEGORY = "ai_ml"

    def __init__(self) -> None:
        """Initialize AI switch node."""
        super().__init__()
        self._create_widgets()
        self._setup_credential_model_link()

    def _create_widgets(self) -> None:
        """Create node widgets for configuration."""
        cred_items = [name for _, name in get_llm_credentials()]
        self.add_combo_menu("credential", "API Key", items=cred_items)

        self.add_text_input(
            "question",
            "Question",
            placeholder_text="What type of document is this?",
        )
        self.add_text_input(
            "options",
            "Options",
            placeholder_text="invoice, receipt, contract, other",
        )
        self.add_text_input(
            "context",
            "Context",
            placeholder_text="Data to classify...",
        )
        self.add_combo_menu("model", "Model", items=ALL_MODELS)
        self.set_property("model", "gpt-4o-mini")
        self.add_text_input("temperature", "Temperature", text="0.0")

    def setup_ports(self) -> None:
        """Setup ports."""
        # Execution flow
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_default")

        # Data inputs
        self.add_typed_input("question", DataType.STRING)
        self.add_typed_input("options", DataType.LIST)
        self.add_typed_input("context", DataType.ANY)
        self.add_typed_input("model", DataType.STRING)
        self.add_typed_input("temperature", DataType.FLOAT)

        # Data outputs
        self.add_typed_output("selected_option", DataType.STRING)
        self.add_typed_output("confidence", DataType.FLOAT)
        self.add_typed_output("reasoning", DataType.STRING)
        self.add_typed_output("all_scores", DataType.DICT)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualAIDecisionTableNode(VisualNode, LLMVisualNodeMixin):
    """Visual representation of AIDecisionTableNode.

    Evaluate decision table with AI fuzzy matching.
    """

    __identifier__ = "casare_rpa.ai_ml"
    NODE_NAME = "AI Decision Table"
    NODE_CATEGORY = "ai_ml"

    def __init__(self) -> None:
        """Initialize AI decision table node."""
        super().__init__()
        self._create_widgets()
        self._setup_credential_model_link()

    def _create_widgets(self) -> None:
        """Create node widgets for configuration."""
        cred_items = [name for _, name in get_llm_credentials()]
        self.add_combo_menu("credential", "API Key", items=cred_items)

        self.add_text_input(
            "decision_table",
            "Decision Table",
            placeholder_text='{"rules": [...], "default_action": "..."}',
        )
        self.add_text_input(
            "context",
            "Context",
            placeholder_text="Data to evaluate...",
        )
        self.add_combo_menu("model", "Model", items=ALL_MODELS)
        self.set_property("model", "gpt-4o-mini")
        self.add_text_input("temperature", "Temperature", text="0.0")

    def setup_ports(self) -> None:
        """Setup ports."""
        # Execution flow
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")

        # Data inputs
        self.add_typed_input("decision_table", DataType.DICT)
        self.add_typed_input("context", DataType.ANY)
        self.add_typed_input("model", DataType.STRING)
        self.add_typed_input("temperature", DataType.FLOAT)

        # Data outputs
        self.add_typed_output("matched_action", DataType.STRING)
        self.add_typed_output("matched_rule_index", DataType.INTEGER)
        self.add_typed_output("confidence", DataType.FLOAT)
        self.add_typed_output("reasoning", DataType.STRING)
        self.add_typed_output("all_matches", DataType.LIST)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualAIAgentNode(VisualNode, LLMVisualNodeMixin):
    """Visual representation of AIAgentNode.

    Autonomous AI agent with multi-step reasoning and tool use.
    """

    __identifier__ = "casare_rpa.ai_ml"
    NODE_NAME = "AI Agent"
    NODE_CATEGORY = "ai_ml"

    def __init__(self) -> None:
        """Initialize AI agent node."""
        super().__init__()
        self._create_widgets()
        self._setup_credential_model_link()

    def _create_widgets(self) -> None:
        """Create node widgets for configuration."""
        cred_items = [name for _, name in get_llm_credentials()]
        self.add_combo_menu("credential", "API Key", items=cred_items)

        self.add_text_input(
            "goal",
            "Goal",
            placeholder_text="Find the order status for customer 12345...",
        )
        self.add_text_input(
            "context",
            "Context",
            placeholder_text="Additional context for the agent...",
        )
        self.add_text_input(
            "available_tools",
            "Available Tools",
            placeholder_text="read_file, http_request, calculate (comma-separated)",
        )
        self.add_combo_menu("model", "Model", items=ALL_MODELS)
        self.set_property("model", "gpt-4o-mini")
        self.add_text_input("max_steps", "Max Steps", text="10")
        self.add_text_input("timeout", "Timeout (sec)", text="300")

    def setup_ports(self) -> None:
        """Setup ports."""
        # Execution flow
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")
        self.add_exec_output("exec_error")

        # Data inputs
        self.add_typed_input("goal", DataType.STRING)
        self.add_typed_input("context", DataType.ANY)
        self.add_typed_input("available_tools", DataType.LIST)
        self.add_typed_input("max_steps", DataType.INTEGER)
        self.add_typed_input("timeout", DataType.FLOAT)
        self.add_typed_input("model", DataType.STRING)

        # Data outputs
        self.add_typed_output("result", DataType.ANY)
        self.add_typed_output("steps_taken", DataType.LIST)
        self.add_typed_output("step_count", DataType.INTEGER)
        self.add_typed_output("total_tokens", DataType.INTEGER)
        self.add_typed_output("execution_time", DataType.FLOAT)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualEmbeddingNode(VisualNode):
    """Visual representation of EmbeddingNode.

    Generate text embeddings for semantic operations.
    """

    __identifier__ = "casare_rpa.ai_ml"
    NODE_NAME = "Embedding"
    NODE_CATEGORY = "ai_ml"

    def __init__(self) -> None:
        """Initialize embedding node."""
        super().__init__()
        self._create_widgets()

    def _create_widgets(self) -> None:
        """Create node widgets for configuration."""
        self.add_text_input("text", "Text", placeholder_text="Text to embed...")
        self.add_combo_menu(
            "model",
            "Model",
            items=[
                "text-embedding-3-small",
                "text-embedding-3-large",
                "text-embedding-ada-002",
            ],
        )
        self.set_property("model", "text-embedding-3-small")

    def setup_ports(self) -> None:
        """Setup ports."""
        # Execution flow
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")

        # Data inputs
        self.add_typed_input("text", DataType.STRING)
        self.add_typed_input("model", DataType.STRING)
        self.add_typed_input("api_key", DataType.STRING)

        # Data outputs
        self.add_typed_output("embedding", DataType.LIST)
        self.add_typed_output("dimensions", DataType.INTEGER)
        self.add_typed_output("tokens_used", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualVectorStoreAddNode(VisualNode):
    """Visual representation of VectorStoreAddNode.

    Add documents to vector store for semantic search.
    """

    __identifier__ = "casare_rpa.ai_ml"
    NODE_NAME = "Vector Store Add"
    NODE_CATEGORY = "ai_ml"

    def __init__(self) -> None:
        """Initialize vector store add node."""
        super().__init__()
        self._create_widgets()

    def _create_widgets(self) -> None:
        """Create node widgets for configuration."""
        self.add_text_input("collection", "Collection", placeholder_text="default")
        self.set_property("collection", "default")

    def setup_ports(self) -> None:
        """Setup ports."""
        # Execution flow
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")

        # Data inputs
        self.add_typed_input("documents", DataType.LIST)
        self.add_typed_input("collection", DataType.STRING)
        self.add_typed_input("embeddings", DataType.LIST)

        # Data outputs
        self.add_typed_output("count", DataType.INTEGER)
        self.add_typed_output("collection_name", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualVectorSearchNode(VisualNode):
    """Visual representation of VectorSearchNode.

    Semantic search in vector store.
    """

    __identifier__ = "casare_rpa.ai_ml"
    NODE_NAME = "Vector Search"
    NODE_CATEGORY = "ai_ml"

    def __init__(self) -> None:
        """Initialize vector search node."""
        super().__init__()
        self._create_widgets()

    def _create_widgets(self) -> None:
        """Create node widgets for configuration."""
        self.add_text_input("query", "Query", placeholder_text="Search query...")
        self.add_text_input("collection", "Collection", placeholder_text="default")
        self.set_property("collection", "default")
        self.add_text_input("top_k", "Top K", text="5")

    def setup_ports(self) -> None:
        """Setup ports."""
        # Execution flow
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")

        # Data inputs
        self.add_typed_input("query", DataType.STRING)
        self.add_typed_input("collection", DataType.STRING)
        self.add_typed_input("top_k", DataType.INTEGER)
        self.add_typed_input("filter", DataType.DICT)
        self.add_typed_input("query_embedding", DataType.LIST)

        # Data outputs
        self.add_typed_output("results", DataType.LIST)
        self.add_typed_output("top_result", DataType.DICT)
        self.add_typed_output("result_count", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualRAGNode(VisualNode, LLMVisualNodeMixin):
    """Visual representation of RAGNode.

    Retrieval-Augmented Generation: search context then generate.
    """

    __identifier__ = "casare_rpa.ai_ml"
    NODE_NAME = "RAG"
    NODE_CATEGORY = "ai_ml"

    def __init__(self) -> None:
        """Initialize RAG node."""
        super().__init__()
        self._create_widgets()
        self._setup_credential_model_link()

    def _create_widgets(self) -> None:
        """Create node widgets for configuration."""
        cred_items = [name for _, name in get_llm_credentials()]
        self.add_combo_menu("credential", "API Key", items=cred_items)

        self.add_text_input(
            "question", "Question", placeholder_text="Ask a question..."
        )
        self.add_text_input("collection", "Collection", placeholder_text="default")
        self.set_property("collection", "default")
        self.add_text_input("top_k", "Context Docs", text="3")
        self.add_combo_menu("model", "Model", items=ALL_MODELS)
        self.set_property("model", "gpt-4o-mini")
        self.add_text_input("temperature", "Temperature", text="0.7")
        self.add_text_input("max_tokens", "Max Tokens", text="1000")

    def setup_ports(self) -> None:
        """Setup ports."""
        # Execution flow
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")

        # Data inputs
        self.add_typed_input("question", DataType.STRING)
        self.add_typed_input("collection", DataType.STRING)
        self.add_typed_input("top_k", DataType.INTEGER)
        self.add_typed_input("prompt_template", DataType.STRING)
        self.add_typed_input("model", DataType.STRING)
        self.add_typed_input("system_prompt", DataType.STRING)
        self.add_typed_input("temperature", DataType.FLOAT)
        self.add_typed_input("max_tokens", DataType.INTEGER)

        # Data outputs
        self.add_typed_output("answer", DataType.STRING)
        self.add_typed_output("context", DataType.STRING)
        self.add_typed_output("sources", DataType.LIST)
        self.add_typed_output("tokens_used", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualVectorStoreDeleteNode(VisualNode):
    """Visual representation of VectorStoreDeleteNode.

    Delete documents from vector store.
    """

    __identifier__ = "casare_rpa.ai_ml"
    NODE_NAME = "Vector Store Delete"
    NODE_CATEGORY = "ai_ml"

    def __init__(self) -> None:
        """Initialize vector store delete node."""
        super().__init__()
        self._create_widgets()

    def _create_widgets(self) -> None:
        """Create node widgets for configuration."""
        self.add_text_input("collection", "Collection", placeholder_text="default")
        self.set_property("collection", "default")

    def setup_ports(self) -> None:
        """Setup ports."""
        # Execution flow
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")

        # Data inputs
        self.add_typed_input("document_ids", DataType.LIST)
        self.add_typed_input("collection", DataType.STRING)

        # Data outputs
        self.add_typed_output("deleted_count", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualPromptTemplateNode(VisualNode, LLMVisualNodeMixin):
    """Visual representation of PromptTemplateNode.

    Execute reusable prompt templates for AI tasks.
    """

    __identifier__ = "casare_rpa.ai_ml"
    NODE_NAME = "Prompt Template"
    NODE_CATEGORY = "ai_ml"

    def __init__(self) -> None:
        """Initialize prompt template node."""
        super().__init__()
        self._create_widgets()
        self._setup_credential_model_link()

    def _create_widgets(self) -> None:
        """Create node widgets for configuration."""
        cred_items = [name for _, name in get_llm_credentials()]
        self.add_combo_menu("credential", "API Key", items=cred_items)

        self.add_text_input(
            "template_id", "Template ID", placeholder_text="my_template"
        )
        self.add_checkbox("execute", "Execute with LLM", state=True)
        self.add_combo_menu("model", "Model", items=ALL_MODELS)
        self.set_property("model", "gpt-4o-mini")
        self.add_text_input("temperature", "Temperature", text="0.7")
        self.add_text_input("max_tokens", "Max Tokens", text="1000")

    def setup_ports(self) -> None:
        """Setup ports."""
        # Execution flow
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")

        # Data inputs
        self.add_typed_input("template_id", DataType.STRING)
        self.add_typed_input("variables", DataType.DICT)
        self.add_typed_input("execute", DataType.BOOLEAN)
        self.add_typed_input("model", DataType.STRING)
        self.add_typed_input("temperature", DataType.FLOAT)
        self.add_typed_input("max_tokens", DataType.INTEGER)

        # Data outputs
        self.add_typed_output("rendered_prompt", DataType.STRING)
        self.add_typed_output("system_prompt", DataType.STRING)
        self.add_typed_output("response", DataType.STRING)
        self.add_typed_output("parsed_response", DataType.DICT)
        self.add_typed_output("tokens_used", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualListTemplatesNode(VisualNode):
    """Visual representation of ListTemplatesNode.

    List available prompt templates.
    """

    __identifier__ = "casare_rpa.ai_ml"
    NODE_NAME = "List Templates"
    NODE_CATEGORY = "ai_ml"

    def __init__(self) -> None:
        """Initialize list templates node."""
        super().__init__()
        self._create_widgets()

    def _create_widgets(self) -> None:
        """Create node widgets for configuration."""
        self.add_text_input(
            "category", "Category", placeholder_text="extraction, generation..."
        )
        self.add_text_input("search", "Search", placeholder_text="Search term...")
        self.add_checkbox("include_builtin", "Include Built-in", state=True)

    def setup_ports(self) -> None:
        """Setup ports."""
        # Execution flow
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")

        # Data inputs
        self.add_typed_input("category", DataType.STRING)
        self.add_typed_input("search", DataType.STRING)
        self.add_typed_input("include_builtin", DataType.BOOLEAN)

        # Data outputs
        self.add_typed_output("templates", DataType.LIST)
        self.add_typed_output("count", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualGetTemplateInfoNode(VisualNode):
    """Visual representation of GetTemplateInfoNode.

    Get details about a prompt template.
    """

    __identifier__ = "casare_rpa.ai_ml"
    NODE_NAME = "Get Template Info"
    NODE_CATEGORY = "ai_ml"

    def __init__(self) -> None:
        """Initialize get template info node."""
        super().__init__()
        self._create_widgets()

    def _create_widgets(self) -> None:
        """Create node widgets for configuration."""
        self.add_text_input(
            "template_id", "Template ID", placeholder_text="my_template"
        )

    def setup_ports(self) -> None:
        """Setup ports."""
        # Execution flow
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")

        # Data inputs
        self.add_typed_input("template_id", DataType.STRING)

        # Data outputs
        self.add_typed_output("template_info", DataType.DICT)
        self.add_typed_output("variables", DataType.LIST)
        self.add_typed_output("system_prompt", DataType.STRING)
        self.add_typed_output("found", DataType.BOOLEAN)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)
