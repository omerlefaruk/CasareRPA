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
