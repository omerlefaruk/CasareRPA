"""
CasareRPA - Domain: Prompt Templates

Reusable prompt templates for common AI tasks.
Pure domain logic - no external dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class TemplateCategory(Enum):
    """Categories for prompt templates."""

    EXTRACTION = "extraction"
    CLASSIFICATION = "classification"
    GENERATION = "generation"
    SUMMARIZATION = "summarization"
    TRANSLATION = "translation"
    ANALYSIS = "analysis"
    CONVERSION = "conversion"


@dataclass(frozen=True)
class TemplateVariable:
    """
    Value Object: Template variable definition.

    Defines a placeholder in a prompt template with validation rules.
    """

    name: str
    description: str
    data_type: str = "string"  # string, number, list, dict, boolean
    required: bool = True
    default: Optional[Any] = None
    examples: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Variable name cannot be empty")
        if not self.name.isidentifier():
            raise ValueError(f"Variable name must be a valid identifier: {self.name}")


@dataclass
class FewShotExample:
    """Example input/output pair for few-shot learning."""

    input_text: str
    expected_output: str
    explanation: Optional[str] = None

    def to_prompt_format(self) -> str:
        """Format example for prompt inclusion."""
        result = f"Input: {self.input_text}\nOutput: {self.expected_output}"
        if self.explanation:
            result += f"\nExplanation: {self.explanation}"
        return result


@dataclass
class PromptTemplate:
    """
    Entity: Reusable prompt template for AI tasks.

    Encapsulates a prompt structure with placeholders for variable substitution.
    Supports few-shot examples and validation rules.
    """

    id: str
    name: str
    category: TemplateCategory
    system_prompt: str
    user_prompt_template: str
    variables: List[TemplateVariable] = field(default_factory=list)
    examples: List[FewShotExample] = field(default_factory=list)
    output_format: Optional[str] = None  # json, text, list, etc.
    description: str = ""
    version: str = "1.0"
    tags: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("Template ID cannot be empty")
        if not self.name:
            raise ValueError("Template name cannot be empty")

    def get_variable(self, name: str) -> Optional[TemplateVariable]:
        """Get a variable by name."""
        for var in self.variables:
            if var.name == name:
                return var
        return None

    def validate_inputs(self, inputs: Dict[str, Any]) -> List[str]:
        """
        Validate provided inputs against template variables.

        Returns list of validation errors, empty if valid.
        """
        errors = []

        for var in self.variables:
            if var.required and var.name not in inputs:
                if var.default is None:
                    errors.append(f"Required variable '{var.name}' is missing")

            if var.name in inputs:
                value = inputs[var.name]
                if not self._validate_type(value, var.data_type):
                    errors.append(
                        f"Variable '{var.name}' expected {var.data_type}, "
                        f"got {type(value).__name__}"
                    )

        return errors

    def _validate_type(self, value: Any, expected_type: str) -> bool:
        """Validate value against expected type."""
        type_map = {
            "string": str,
            "number": (int, float),
            "integer": int,
            "float": float,
            "list": list,
            "dict": dict,
            "boolean": bool,
        }
        expected = type_map.get(expected_type)
        if expected is None:
            return True  # Unknown type, allow
        return isinstance(value, expected)

    def render(self, inputs: Dict[str, Any]) -> str:
        """
        Render the user prompt with variable substitution.

        Args:
            inputs: Dictionary mapping variable names to values

        Returns:
            Rendered prompt string

        Raises:
            ValueError: If required variables are missing
        """
        errors = self.validate_inputs(inputs)
        if errors:
            raise ValueError(f"Validation errors: {'; '.join(errors)}")

        # Build full inputs with defaults
        full_inputs = {}
        for var in self.variables:
            if var.name in inputs:
                full_inputs[var.name] = inputs[var.name]
            elif var.default is not None:
                full_inputs[var.name] = var.default

        # Format template
        try:
            rendered = self.user_prompt_template.format(**full_inputs)
        except KeyError as e:
            raise ValueError(f"Missing template variable: {e}")

        # Add examples if present
        if self.examples:
            examples_text = "\n\nExamples:\n"
            for i, example in enumerate(self.examples, 1):
                examples_text += f"\n--- Example {i} ---\n{example.to_prompt_format()}\n"
            rendered = examples_text + "\n" + rendered

        return rendered

    def render_full_prompt(self, inputs: Dict[str, Any]) -> Dict[str, str]:
        """
        Render both system and user prompts.

        Returns dict with 'system' and 'user' keys.
        """
        return {
            "system": self.system_prompt,
            "user": self.render(inputs),
        }


# Built-in template definitions
EXTRACT_ENTITIES_TEMPLATE = PromptTemplate(
    id="extract_entities",
    name="Extract Named Entities",
    category=TemplateCategory.EXTRACTION,
    description="Extract named entities (people, organizations, locations, dates) from text",
    system_prompt=(
        "You are a named entity recognition assistant. Extract entities accurately "
        "and return them in the specified JSON format. Only extract entities that "
        "are explicitly mentioned in the text."
    ),
    user_prompt_template="""Extract all named entities from the following text.

Return a JSON object with these categories:
- persons: List of person names
- organizations: List of organization/company names
- locations: List of locations (cities, countries, addresses)
- dates: List of dates/times mentioned
- other: List of other notable entities

Text:
{text}

Return ONLY valid JSON, no other text.""",
    variables=[
        TemplateVariable(
            name="text",
            description="The text to extract entities from",
            data_type="string",
            required=True,
            examples=["John Smith works at Microsoft in Seattle."],
        ),
    ],
    output_format="json",
    tags=["ner", "extraction", "entities"],
)


CLASSIFY_DOCUMENT_TEMPLATE = PromptTemplate(
    id="classify_document",
    name="Classify Document",
    category=TemplateCategory.CLASSIFICATION,
    description="Classify a document into predefined categories",
    system_prompt=(
        "You are a document classification assistant. Analyze the document content "
        "and classify it into the most appropriate category. Provide confidence scores "
        "for your classification."
    ),
    user_prompt_template="""Classify the following document into one of these categories:
{categories}

Document:
{document}

Return a JSON object with:
- category: The best matching category
- confidence: Confidence score (0.0 to 1.0)
- reasoning: Brief explanation of why this category was chosen

Return ONLY valid JSON, no other text.""",
    variables=[
        TemplateVariable(
            name="document",
            description="The document text to classify",
            data_type="string",
            required=True,
        ),
        TemplateVariable(
            name="categories",
            description="Comma-separated list of possible categories",
            data_type="string",
            required=True,
            examples=["invoice, contract, receipt, memo, report"],
        ),
    ],
    output_format="json",
    tags=["classification", "document"],
)


SUMMARIZE_MEETING_TEMPLATE = PromptTemplate(
    id="summarize_meeting",
    name="Summarize Meeting Notes",
    category=TemplateCategory.SUMMARIZATION,
    description="Create structured meeting summary with action items",
    system_prompt=(
        "You are a professional meeting assistant. Create concise, actionable "
        "summaries that highlight key decisions and next steps."
    ),
    user_prompt_template="""Summarize the following meeting notes.

Meeting Notes:
{notes}

Provide a summary with:
1. **Key Points**: Main topics discussed (3-5 bullet points)
2. **Decisions Made**: Any decisions reached
3. **Action Items**: Tasks assigned with owners if mentioned
4. **Follow-ups**: Items that need future discussion

{additional_instructions}""",
    variables=[
        TemplateVariable(
            name="notes",
            description="The meeting notes or transcript",
            data_type="string",
            required=True,
        ),
        TemplateVariable(
            name="additional_instructions",
            description="Any additional formatting or focus instructions",
            data_type="string",
            required=False,
            default="",
        ),
    ],
    output_format="text",
    tags=["meeting", "summary", "business"],
)


TRANSLATE_FORMAL_TEMPLATE = PromptTemplate(
    id="translate_formal",
    name="Formal Translation",
    category=TemplateCategory.TRANSLATION,
    description="Translate text with formal business tone",
    system_prompt=(
        "You are a professional translator. Translate accurately while maintaining "
        "a formal, business-appropriate tone. Preserve formatting and structure."
    ),
    user_prompt_template="""Translate the following text from {source_language} to {target_language}.
Maintain a formal, professional tone throughout.

Text to translate:
{text}

Return a JSON object with:
- translated_text: The translation
- notes: Any translation notes or cultural considerations (optional)

Return ONLY valid JSON, no other text.""",
    variables=[
        TemplateVariable(
            name="text",
            description="Text to translate",
            data_type="string",
            required=True,
        ),
        TemplateVariable(
            name="source_language",
            description="Source language",
            data_type="string",
            required=False,
            default="auto-detect",
        ),
        TemplateVariable(
            name="target_language",
            description="Target language",
            data_type="string",
            required=True,
            examples=["English", "Spanish", "French", "German"],
        ),
    ],
    output_format="json",
    tags=["translation", "formal", "business"],
)


GENERATE_EMAIL_TEMPLATE = PromptTemplate(
    id="generate_email",
    name="Generate Professional Email",
    category=TemplateCategory.GENERATION,
    description="Generate a professional email based on context",
    system_prompt=(
        "You are a professional email writing assistant. Write clear, concise, "
        "and appropriately toned business emails."
    ),
    user_prompt_template="""Generate a professional email with the following details:

Purpose: {purpose}
Recipient: {recipient}
Key Points: {key_points}
Tone: {tone}

{additional_context}

Format the email with:
- Subject line
- Greeting
- Body
- Closing
- Signature placeholder""",
    variables=[
        TemplateVariable(
            name="purpose",
            description="The main purpose of the email",
            data_type="string",
            required=True,
            examples=["Request meeting", "Follow up on proposal", "Thank you note"],
        ),
        TemplateVariable(
            name="recipient",
            description="Who the email is for (role/relationship)",
            data_type="string",
            required=True,
            examples=["client", "manager", "team member", "vendor"],
        ),
        TemplateVariable(
            name="key_points",
            description="Main points to include",
            data_type="string",
            required=True,
        ),
        TemplateVariable(
            name="tone",
            description="Desired tone",
            data_type="string",
            required=False,
            default="professional",
            examples=["formal", "friendly", "urgent", "apologetic"],
        ),
        TemplateVariable(
            name="additional_context",
            description="Any additional context",
            data_type="string",
            required=False,
            default="",
        ),
    ],
    output_format="text",
    tags=["email", "generation", "business"],
)


ANALYZE_SENTIMENT_TEMPLATE = PromptTemplate(
    id="analyze_sentiment",
    name="Analyze Sentiment",
    category=TemplateCategory.ANALYSIS,
    description="Analyze sentiment and emotional tone of text",
    system_prompt=(
        "You are a sentiment analysis expert. Analyze text for emotional tone, "
        "sentiment polarity, and key emotional indicators."
    ),
    user_prompt_template="""Analyze the sentiment of the following text:

Text:
{text}

Return a JSON object with:
- overall_sentiment: "positive", "negative", "neutral", or "mixed"
- confidence: Confidence score (0.0 to 1.0)
- emotions: List of detected emotions (e.g., joy, anger, sadness, fear, surprise)
- key_phrases: Phrases that indicate the sentiment
- tone: Overall tone description (e.g., formal, casual, aggressive, supportive)

Return ONLY valid JSON, no other text.""",
    variables=[
        TemplateVariable(
            name="text",
            description="Text to analyze",
            data_type="string",
            required=True,
        ),
    ],
    output_format="json",
    tags=["sentiment", "analysis", "emotions"],
)


EXTRACT_INVOICE_TEMPLATE = PromptTemplate(
    id="extract_invoice",
    name="Extract Invoice Data",
    category=TemplateCategory.EXTRACTION,
    description="Extract structured data from invoice text/OCR",
    system_prompt=(
        "You are an invoice processing assistant. Extract all relevant invoice "
        "information accurately. Handle various invoice formats and missing fields."
    ),
    user_prompt_template="""Extract invoice data from the following text:

Invoice Text:
{invoice_text}

Return a JSON object with:
- invoice_number: Invoice/document number
- invoice_date: Date of invoice (ISO format if possible)
- due_date: Payment due date
- vendor: Vendor/supplier information (name, address, tax_id)
- buyer: Buyer information (name, address, tax_id)
- line_items: Array of items with (description, quantity, unit_price, total)
- subtotal: Pre-tax total
- tax_amount: Tax amount
- total_amount: Grand total
- currency: Currency code (USD, EUR, etc.)
- payment_terms: Payment terms if mentioned
- notes: Any additional notes

Use null for missing fields. Return ONLY valid JSON.""",
    variables=[
        TemplateVariable(
            name="invoice_text",
            description="Raw invoice text or OCR output",
            data_type="string",
            required=True,
        ),
    ],
    output_format="json",
    tags=["invoice", "extraction", "finance", "document"],
)


DATA_CONVERSION_TEMPLATE = PromptTemplate(
    id="convert_data_format",
    name="Convert Data Format",
    category=TemplateCategory.CONVERSION,
    description="Convert data between different formats",
    system_prompt=(
        "You are a data conversion specialist. Convert data accurately between "
        "formats while preserving all information and structure."
    ),
    user_prompt_template="""Convert the following data from {source_format} to {target_format}:

Input Data:
{data}

{conversion_rules}

Return the converted data in {target_format} format.""",
    variables=[
        TemplateVariable(
            name="data",
            description="The data to convert",
            data_type="string",
            required=True,
        ),
        TemplateVariable(
            name="source_format",
            description="Source data format",
            data_type="string",
            required=True,
            examples=["JSON", "CSV", "XML", "YAML", "plain text"],
        ),
        TemplateVariable(
            name="target_format",
            description="Target data format",
            data_type="string",
            required=True,
            examples=["JSON", "CSV", "XML", "YAML", "markdown table"],
        ),
        TemplateVariable(
            name="conversion_rules",
            description="Additional conversion rules or mappings",
            data_type="string",
            required=False,
            default="",
        ),
    ],
    output_format="text",
    tags=["conversion", "data", "format"],
)


# Registry of built-in templates
BUILTIN_TEMPLATES: Dict[str, PromptTemplate] = {
    "extract_entities": EXTRACT_ENTITIES_TEMPLATE,
    "classify_document": CLASSIFY_DOCUMENT_TEMPLATE,
    "summarize_meeting": SUMMARIZE_MEETING_TEMPLATE,
    "translate_formal": TRANSLATE_FORMAL_TEMPLATE,
    "generate_email": GENERATE_EMAIL_TEMPLATE,
    "analyze_sentiment": ANALYZE_SENTIMENT_TEMPLATE,
    "extract_invoice": EXTRACT_INVOICE_TEMPLATE,
    "convert_data_format": DATA_CONVERSION_TEMPLATE,
}


def get_builtin_template(template_id: str) -> Optional[PromptTemplate]:
    """Get a built-in template by ID."""
    return BUILTIN_TEMPLATES.get(template_id)


def list_builtin_templates() -> List[Dict[str, Any]]:
    """List all built-in templates with metadata."""
    return [
        {
            "id": t.id,
            "name": t.name,
            "category": t.category.value,
            "description": t.description,
            "variables": [v.name for v in t.variables],
            "tags": t.tags,
        }
        for t in BUILTIN_TEMPLATES.values()
    ]


def list_templates_by_category(category: TemplateCategory) -> List[PromptTemplate]:
    """Get all templates in a category."""
    return [t for t in BUILTIN_TEMPLATES.values() if t.category == category]


__all__ = [
    # Core classes
    "PromptTemplate",
    "TemplateVariable",
    "TemplateCategory",
    "FewShotExample",
    # Built-in templates
    "EXTRACT_ENTITIES_TEMPLATE",
    "CLASSIFY_DOCUMENT_TEMPLATE",
    "SUMMARIZE_MEETING_TEMPLATE",
    "TRANSLATE_FORMAL_TEMPLATE",
    "GENERATE_EMAIL_TEMPLATE",
    "ANALYZE_SENTIMENT_TEMPLATE",
    "EXTRACT_INVOICE_TEMPLATE",
    "DATA_CONVERSION_TEMPLATE",
    "BUILTIN_TEMPLATES",
    # Functions
    "get_builtin_template",
    "list_builtin_templates",
    "list_templates_by_category",
]
