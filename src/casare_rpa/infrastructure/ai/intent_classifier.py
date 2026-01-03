"""
CasareRPA - Intent Classification for AI Workflow Requests.

Provides fast, pattern-based intent classification to route user requests
before making expensive LLM calls. Supports both regex-based pattern matching
and optional LLM fallback for ambiguous requests.

Features:
    - Pattern-based fast classification (regex)
    - Confidence scoring (0-1)
    - LLM fallback for low-confidence cases
    - Template matching for common workflow patterns
    - Context-aware classification (considers current workflow state)

Intent Types:
    - CREATE_WORKFLOW: New workflow from scratch
    - MODIFY_WORKFLOW: Change existing workflow structure
    - ADD_NODE: Add specific nodes to workflow
    - REMOVE_NODE: Remove nodes from workflow
    - EXPLAIN: Explain current workflow or concepts
    - HELP: General help requests
    - TEMPLATE_REQUEST: Request a predefined template
    - UNDO/REDO: Navigation through workflow history
    - REFINE: Improve or optimize existing workflow
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from loguru import logger

from casare_rpa.infrastructure.ai.conversation_manager import UserIntent

if TYPE_CHECKING:
    from casare_rpa.infrastructure.resources.llm_resource_manager import (
        LLMResourceManager,
    )


@dataclass
class IntentClassification:
    """
    Result of intent classification.

    Attributes:
        intent: Detected user intent
        confidence: Confidence score (0.0 to 1.0)
        matched_patterns: List of patterns that matched
        extracted_entities: Extracted entities (node types, selectors, etc.)
        suggested_template: Template ID if template request detected
        requires_llm_fallback: Whether LLM should be consulted
    """

    intent: UserIntent
    confidence: float
    matched_patterns: list[str] = field(default_factory=list)
    extracted_entities: dict[str, Any] = field(default_factory=dict)
    suggested_template: str | None = None
    requires_llm_fallback: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "intent": self.intent.value,
            "confidence": self.confidence,
            "matched_patterns": self.matched_patterns,
            "extracted_entities": self.extracted_entities,
            "suggested_template": self.suggested_template,
            "requires_llm_fallback": self.requires_llm_fallback,
        }


@dataclass
class PatternRule:
    """
    Rule for pattern-based intent detection.

    Attributes:
        intent: Intent this pattern indicates
        patterns: List of regex patterns
        weight: Weight for this rule (higher = more confident)
        extract_entities: Whether to extract entities from matches
        entity_groups: Named groups to extract from regex
    """

    intent: UserIntent
    patterns: list[str]
    weight: float = 1.0
    extract_entities: bool = False
    entity_groups: list[str] = field(default_factory=list)


class IntentClassifier:
    """
    Fast intent classification for AI workflow requests.

    Uses pattern-based matching for common intents and provides
    confidence scoring to determine when LLM fallback is needed.

    Example:
        classifier = IntentClassifier()
        result = classifier.classify("Create a login workflow for example.com")
        if result.confidence < 0.7:
            # Fall back to LLM classification
            result = await classifier.classify_with_llm(message, llm_client)
        # Use result
    """

    DEFAULT_CONFIDENCE_THRESHOLD = 0.7
    MIN_PATTERN_CONFIDENCE = 0.4
    MAX_PATTERN_CONFIDENCE = 0.95

    # Pattern rules organized by intent
    _PATTERN_RULES: list[PatternRule] = [
        # CREATE_WORKFLOW patterns
        PatternRule(
            intent=UserIntent.NEW_WORKFLOW,
            patterns=[
                r"\b(create|build|make|generate|design)\b.*\b(workflow|automation|bot|process)\b",
                r"\bI (want|need) (a|to)\b.*\b(workflow|automation)\b",
                r"\b(new|fresh|blank)\b.*\bworkflow\b",
                r"\bautomate\b.*\b(task|process|steps)\b",
                r"\bstart\b.*\bfrom scratch\b",
                r"^(create|build|make)\b",
            ],
            weight=1.5,
        ),
        # MODIFY_WORKFLOW patterns
        PatternRule(
            intent=UserIntent.MODIFY_WORKFLOW,
            patterns=[
                r"\b(change|modify|update|edit|alter|adjust)\b.*\b(workflow|node|step)\b",
                r"\b(instead of|rather than|replace)\b",
                r"\bmake (it|the|this)\b.*\b(different|better|faster)\b",
                r"\bswap\b.*\b(node|step|action)\b",
                r"\buse\b.*\binstead\b",
                r"\b(fix|correct)\b.*\b(workflow|node)\b",
            ],
            weight=1.1,
        ),
        # ADD_NODE patterns
        PatternRule(
            intent=UserIntent.ADD_NODE,
            patterns=[
                r"\badd\b.*\b(node|step|action|click|type|wait|navigate)\b",
                r"\binsert\b.*\b(before|after|between)\b",
                r"\binclude\b.*\b(step|action)\b",
                r"\balso\b.*\b(click|type|wait|navigate|extract)\b",
                r"\bthen\b.*\b(click|type|wait|navigate)\b",
                r"\bafter that\b.*\b(click|type|wait)\b",
            ],
            weight=1.0,
            extract_entities=True,
            entity_groups=["node_type", "selector"],
        ),
        # REMOVE_NODE patterns
        PatternRule(
            intent=UserIntent.REMOVE_NODE,
            patterns=[
                r"\b(remove|delete|drop|get rid of)\b.*\b(node|step|action)\b",
                r"\bdon'?t\b.*\b(need|want)\b.*\b(step|node)\b",
                r"\b(skip|omit)\b.*\b(step|action)\b",
                r"\bno\b.*\b(wait|click|step)\b.*\bneeded\b",
            ],
            weight=1.0,
        ),
        # EXPLAIN patterns
        PatternRule(
            intent=UserIntent.EXPLAIN,
            patterns=[
                r"\b(explain|describe|what (is|does)|how (does|do))\b",
                r"\btell me (about|more)\b",
                r"\bwhat'?s\b.*\b(this|that|the)\b.*\b(for|do)\b",
                r"\bhow\b.*\bwork(s)?\b",
                r"\bwhy\b.*\b(this|that|the)\b",
                r"^(what|how|why)\b",
            ],
            weight=0.9,
        ),
        # HELP patterns
        PatternRule(
            intent=UserIntent.HELP,
            patterns=[
                r"\b(help|assist|support)\b",
                r"\bwhat can (you|I)\b",
                r"\bhow (do I|to)\b.*\buse\b",
                r"\bshow me\b.*\b(how|examples)\b",
                r"\bgetting started\b",
                r"\btutorial\b",
            ],
            weight=0.8,
        ),
        # UNDO patterns
        PatternRule(
            intent=UserIntent.UNDO,
            patterns=[
                r"\bundo\b",
                r"\bgo back\b",
                r"\brevert\b",
                r"\bprevious (version|state)\b",
                r"\bcancel (that|last)\b",
                r"\btake (that|it) back\b",
            ],
            weight=1.5,  # High weight for explicit commands
        ),
        # REDO patterns
        PatternRule(
            intent=UserIntent.REDO,
            patterns=[
                r"\bredo\b",
                r"\bgo forward\b",
                r"\brestore\b",
                r"\bput (that|it) back\b",
            ],
            weight=1.5,
        ),
        # CLEAR patterns
        PatternRule(
            intent=UserIntent.CLEAR,
            patterns=[
                r"\bclear\b\s+\b(all|everything|workflow|conversation|chat|history)\b",
                r"\bstart\b\s+\bover\b",
                r"\bfresh\b\s+\bstart\b",
                r"\bfrom\b\s+\bscratch\b",
            ],
            weight=1.0,
        ),
        # TEMPLATE_REQUEST patterns
        PatternRule(
            intent=UserIntent.TEMPLATE_REQUEST,
            patterns=[
                r"\b(template|example|sample)\b.*\b(for|of)\b",
                r"\b(login|scraping|form|download)\b.*\btemplate\b",
                r"\bpredefined\b.*\bworkflow\b",
                r"\bcommon\b.*\b(workflow|pattern)\b",
                r"\buse.*template\b",
            ],
            weight=1.1,
            extract_entities=True,
            entity_groups=["template_type"],
        ),
        # REFINE patterns
        PatternRule(
            intent=UserIntent.REFINE,
            patterns=[
                r"\b(improve|optimize|enhance|refine|polish)\b",
                r"\bmake (it )?(better|faster|cleaner|more robust)\b",
                r"\boptimize\b.*\b(performance|speed)\b",
                r"\badd error handling\b",
                r"\bmake (it )?more (reliable|stable)\b",
            ],
            weight=1.0,
        ),
    ]

    # Template keyword mappings
    _TEMPLATE_KEYWORDS: dict[str, str] = {
        "login": "web_login",
        "authentication": "web_login",
        "sign in": "web_login",
        "scrape": "web_scraping",
        "scraping": "web_scraping",
        "extract data": "web_scraping",
        "form": "form_filling",
        "fill form": "form_filling",
        "form filling": "form_filling",
        "download": "file_download",
        "file download": "file_download",
        "upload": "file_upload",
        "excel": "excel_processing",
        "spreadsheet": "excel_processing",
        "email": "email_automation",
        "send email": "email_automation",
        "api": "api_call",
        "rest api": "api_call",
        "http": "api_call",
        "desktop": "desktop_automation",
        "click button": "desktop_automation",
    }

    # Node type patterns for entity extraction
    _NODE_TYPE_PATTERNS: dict[str, str] = {
        r"\bclick\b": "ClickElementNode",
        r"\btype\b|\benter\b|\binput\b": "TypeTextNode",
        r"\bwait\b": "WaitForElementNode",
        r"\bnavigate\b|\bgo to\b|\bopen\b": "GoToURLNode",
        r"\bextract\b|\bget text\b": "ExtractTextNode",
        r"\bscreenshot\b": "ScreenshotNode",
        r"\bloop\b|\bfor each\b": "ForLoopStartNode",
        r"\bif\b|\bcondition\b": "IfNode",
        r"\bvariable\b|\bset\b": "SetVariableNode",
    }

    def __init__(
        self,
        confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
        llm_client: LLMResourceManager | None = None,
    ) -> None:
        """
        Initialize intent classifier.

        Args:
            confidence_threshold: Threshold below which LLM fallback is recommended
            llm_client: Optional LLM client for fallback classification
        """
        self._confidence_threshold = confidence_threshold
        self._llm_client = llm_client
        self._compiled_patterns: dict[UserIntent, list[tuple[re.Pattern, float]]] = {}

        # Compile all patterns
        self._compile_patterns()

        logger.debug(
            f"IntentClassifier initialized: threshold={confidence_threshold}, "
            f"rules={len(self._PATTERN_RULES)}"
        )

    def _compile_patterns(self) -> None:
        """Pre-compile regex patterns for performance."""
        for rule in self._PATTERN_RULES:
            if rule.intent not in self._compiled_patterns:
                self._compiled_patterns[rule.intent] = []

            for pattern in rule.patterns:
                try:
                    compiled = re.compile(pattern, re.IGNORECASE)
                    self._compiled_patterns[rule.intent].append((compiled, rule.weight))
                except re.error as e:
                    logger.warning(f"Invalid pattern '{pattern}': {e}")

    def classify(
        self,
        message: str,
        has_workflow: bool = False,
        context: str | None = None,
    ) -> IntentClassification:
        """
        Classify user intent from message text.

        Args:
            message: User message to classify
            has_workflow: Whether a workflow is currently loaded
            context: Optional conversation context for better classification

        Returns:
            IntentClassification with detected intent and confidence
        """
        if not message or not message.strip():
            return IntentClassification(
                intent=UserIntent.UNKNOWN,
                confidence=0.0,
            )

        message_lower = message.lower().strip()

        # Score each intent
        intent_scores: dict[UserIntent, float] = {}
        matched_patterns: dict[UserIntent, list[str]] = {}

        for intent, patterns in self._compiled_patterns.items():
            score = 0.0
            matches = []

            for pattern, weight in patterns:
                if pattern.search(message_lower):
                    score += weight
                    matches.append(pattern.pattern)

            if score > 0:
                intent_scores[intent] = score
                matched_patterns[intent] = matches

        # Find best intent
        if not intent_scores:
            # No patterns matched - check for implicit create request
            if self._looks_like_workflow_description(message_lower):
                return IntentClassification(
                    intent=UserIntent.NEW_WORKFLOW,
                    confidence=0.5,
                    requires_llm_fallback=True,
                )
            return IntentClassification(
                intent=UserIntent.UNKNOWN,
                confidence=0.0,
                requires_llm_fallback=True,
            )

        best_intent = max(intent_scores, key=intent_scores.get)
        best_score = intent_scores[best_intent]

        # Normalize score to confidence (0-1)
        # Multiple matches increase confidence
        max_possible_score = max(
            sum(w for _, w in patterns) for patterns in self._compiled_patterns.values()
        )
        confidence = min(
            self.MAX_PATTERN_CONFIDENCE,
            max(
                self.MIN_PATTERN_CONFIDENCE,
                best_score / max_possible_score * 1.5,
            ),
        )

        # Context-aware adjustments
        if has_workflow:
            # If workflow exists, boost modification intents
            if best_intent in (
                UserIntent.MODIFY_WORKFLOW,
                UserIntent.ADD_NODE,
                UserIntent.REFINE,
            ):
                confidence = min(0.95, confidence * 1.2)
            # Reduce confidence for new workflow if one exists
            elif best_intent == UserIntent.NEW_WORKFLOW:
                confidence *= 0.8
        else:
            # No workflow - boost creation intents
            if best_intent == UserIntent.NEW_WORKFLOW:
                confidence = min(0.95, confidence * 1.2)
            # Reduce confidence for modification if no workflow
            elif best_intent in (UserIntent.MODIFY_WORKFLOW, UserIntent.ADD_NODE):
                confidence *= 0.7

        # Extract entities
        entities = self._extract_entities(message_lower, best_intent)

        # Check for template
        suggested_template = self._detect_template(message_lower)

        result = IntentClassification(
            intent=best_intent,
            confidence=confidence,
            matched_patterns=matched_patterns.get(best_intent, []),
            extracted_entities=entities,
            suggested_template=suggested_template,
            requires_llm_fallback=confidence < self._confidence_threshold,
        )

        logger.debug(
            f"Classified: '{message[:50]}...' -> {best_intent.value} (confidence={confidence:.2f})"
        )

        return result

    def _looks_like_workflow_description(self, message: str) -> bool:
        """Check if message looks like a workflow description without explicit keywords."""
        # Check for action verbs that suggest automation
        action_patterns = [
            r"\b(open|go to|click|type|enter|fill|submit|download|upload|send)\b",
            r"\b(first|then|after|next|finally)\b",
            r"\b(website|page|form|button|field|input)\b",
        ]

        matches = 0
        for pattern in action_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                matches += 1

        return matches >= 2

    def _extract_entities(
        self,
        message: str,
        intent: UserIntent,
    ) -> dict[str, Any]:
        """Extract relevant entities from message based on intent."""
        entities: dict[str, Any] = {}

        # Extract URLs
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, message)
        if urls:
            entities["urls"] = urls

        # Extract selectors (CSS/XPath)
        selector_patterns = [
            (r"#[\w-]+", "id"),
            (r"\.[\w-]+", "class"),
            (r'\[[\w-]+=["\']?[^"\']+["\']?\]', "attribute"),
            (r'//[\w/\[\]@="\']+', "xpath"),
        ]
        selectors = []
        for pattern, sel_type in selector_patterns:
            matches = re.findall(pattern, message)
            selectors.extend([(m, sel_type) for m in matches])
        if selectors:
            entities["selectors"] = selectors

        # Extract node types
        if intent in (
            UserIntent.ADD_NODE,
            UserIntent.REMOVE_NODE,
            UserIntent.MODIFY_WORKFLOW,
        ):
            node_types = []
            for pattern, node_type in self._NODE_TYPE_PATTERNS.items():
                if re.search(pattern, message, re.IGNORECASE):
                    node_types.append(node_type)
            if node_types:
                entities["node_types"] = list(set(node_types))

        # Extract numbers (for timeouts, counts, etc.)
        numbers = re.findall(r"\b\d+\b", message)
        if numbers:
            entities["numbers"] = [int(n) for n in numbers]

        return entities

    def _detect_template(self, message: str) -> str | None:
        """Detect if user is requesting a known template."""
        for keyword, template_id in self._TEMPLATE_KEYWORDS.items():
            if keyword in message:
                return template_id
        return None

    async def classify_with_llm(
        self,
        message: str,
        has_workflow: bool = False,
        context: str | None = None,
    ) -> IntentClassification:
        """
        Classify intent using LLM for ambiguous cases.

        Args:
            message: User message to classify
            has_workflow: Whether a workflow is currently loaded
            context: Optional conversation context

        Returns:
            IntentClassification with LLM-determined intent
        """
        if self._llm_client is None:
            logger.warning("LLM client not available for fallback classification")
            return self.classify(message, has_workflow, context)

        prompt = self._build_classification_prompt(message, has_workflow, context)

        try:
            response = await self._llm_client.completion(
                prompt=prompt,
                model="gpt-4o-mini",  # Use fast model for classification
                temperature=0.1,
                max_tokens=100,
            )

            intent_str = self._parse_llm_intent(response.content)
            intent = self._string_to_intent(intent_str)

            return IntentClassification(
                intent=intent,
                confidence=0.85,  # LLM classifications get good confidence
                matched_patterns=["llm_classification"],
                requires_llm_fallback=False,
            )
        except Exception as e:
            logger.error(f"LLM classification failed: {e}")
            return self.classify(message, has_workflow, context)

    def _build_classification_prompt(
        self,
        message: str,
        has_workflow: bool,
        context: str | None,
    ) -> str:
        """Build prompt for LLM intent classification."""
        intent_descriptions = "\n".join(
            f"- {intent.value}: {self._get_intent_description(intent)}"
            for intent in UserIntent
            if intent != UserIntent.UNKNOWN
        )

        context_info = ""
        if context:
            context_info = f"\nConversation context:\n{context[:500]}"

        workflow_info = "has an existing workflow" if has_workflow else "no workflow loaded"

        return f"""Classify the user's intent. User currently {workflow_info}.

Available intents:
{intent_descriptions}

User message: "{message}"
{context_info}

Respond with ONLY the intent name (e.g., "new_workflow" or "modify_workflow")."""

    def _get_intent_description(self, intent: UserIntent) -> str:
        """Get human-readable description of intent."""
        descriptions = {
            UserIntent.NEW_WORKFLOW: "Create a new workflow from scratch",
            UserIntent.MODIFY_WORKFLOW: "Modify existing workflow structure",
            UserIntent.ADD_NODE: "Add specific nodes to current workflow",
            UserIntent.REMOVE_NODE: "Remove nodes from current workflow",
            UserIntent.EXPLAIN: "Explain workflow, nodes, or concepts",
            UserIntent.UNDO: "Undo the last workflow change",
            UserIntent.REDO: "Redo a previously undone change",
            UserIntent.CLEAR: "Clear conversation or workflow",
            UserIntent.HELP: "Request help or guidance",
            UserIntent.TEMPLATE_REQUEST: "Request a predefined workflow template",
            UserIntent.REFINE: "Improve or optimize existing workflow",
            UserIntent.UNKNOWN: "Intent cannot be determined",
        }
        return descriptions.get(intent, "Unknown intent")

    def _parse_llm_intent(self, response: str) -> str:
        """Parse intent string from LLM response."""
        response_lower = response.lower().strip()

        # Handle common LLM response formats
        for intent in UserIntent:
            if intent.value in response_lower:
                return intent.value

        # Fallback: first word might be the intent
        first_word = response_lower.split()[0] if response_lower else ""
        return first_word

    def _string_to_intent(self, intent_str: str) -> UserIntent:
        """Convert string to UserIntent enum."""
        try:
            return UserIntent(intent_str.lower())
        except ValueError:
            return UserIntent.UNKNOWN

    def get_confidence_threshold(self) -> float:
        """Get current confidence threshold."""
        return self._confidence_threshold

    def set_confidence_threshold(self, threshold: float) -> None:
        """Set confidence threshold for LLM fallback."""
        self._confidence_threshold = max(0.0, min(1.0, threshold))


__all__ = [
    "IntentClassifier",
    "IntentClassification",
    "PatternRule",
    "UserIntent",
]
