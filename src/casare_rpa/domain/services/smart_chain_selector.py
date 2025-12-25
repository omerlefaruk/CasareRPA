"""
Smart Chain Selector - ML-based task classification for agent chaining.

This service provides intelligent task classification using:
- NLP-based intent detection
- Complexity scoring
- Context awareness
- Historical pattern matching
"""

import re
from dataclasses import dataclass
from typing import Any

from loguru import logger

from casare_rpa.domain.entities.chain_types import (
    ClassificationResult,
    ComplexityLevel,
    TaskType,
)


@dataclass
class IntentMatch:
    """Result of intent matching."""

    task_type: TaskType
    confidence: float
    matched_keywords: list[str]
    unmatched_words: list[str]


class IntentClassifier:
    """NLP-based intent classification for task types."""

    # Keyword patterns for each task type
    INTENT_PATTERNS: dict[TaskType, dict[str, list[str]]] = {
        TaskType.IMPLEMENT: {
            "primary": ["create", "add", "implement", "build", "develop", "new", "make"],
            "secondary": ["feature", "component", "function", "class", "module", "endpoint"],
        },
        TaskType.FIX: {
            "primary": [
                "fix",
                "repair",
                "debug",
                "resolve",
                "solve",
                "correct",
                "bug",
                "issue",
                "error",
                "crash",
            ],
            "secondary": ["null", "None", "exception", "fail", "broken", "wrong"],
        },
        TaskType.RESEARCH: {
            "primary": [
                "research",
                "investigate",
                "analyze",
                "explore",
                "understand",
                "study",
                "examine",
            ],
            "secondary": ["pattern", "approach", "strategy", "best practice", "comparison"],
        },
        TaskType.REFACTOR: {
            "primary": [
                "refactor",
                "clean",
                "optimize",
                "improve",
                "modernize",
                "restructure",
                "redesign",
            ],
            "secondary": ["code", "legacy", "technical debt", "DRY", "simplify"],
        },
        TaskType.EXTEND: {
            "primary": ["extend", "enhance", "add to", "augment", "expand", "upgrade"],
            "secondary": ["existing", "current", "capability", "feature", "support"],
        },
        TaskType.CLONE: {
            "primary": ["clone", "duplicate", "copy", "replicate", "mirror"],
            "secondary": ["pattern", "template", "example", "similar"],
        },
        TaskType.TEST: {
            "primary": ["test", "verify", "check", "validate", "ensure", "coverage"],
            "secondary": ["unit", "integration", "e2e", "edge case", "scenario"],
        },
        TaskType.DOCS: {
            "primary": ["document", "write docs", "generate docs", "update docs", "documentate"],
            "secondary": ["API", "reference", "guide", "README", "docstring"],
        },
        TaskType.UI: {
            "primary": ["ui", "widget", "style", "design", "layout", "component", "visual"],
            "secondary": ["PySide6", "Qt", "button", "dialog", "panel", "theme"],
        },
        TaskType.INTEGRATION: {
            "primary": ["integrate", "connect", "api", "service", "external", "third-party"],
            "secondary": ["OAuth", "REST", "GraphQL", "client", "endpoint"],
        },
        TaskType.SECURITY: {
            "primary": ["security", "audit", "review", "scan", "vulnerability", "penetration"],
            "secondary": ["auth", "encryption", "sanitize", "permission", "CORS"],
        },
    }

    # Negation patterns that indicate opposite intent
    NEGATION_PATTERNS = [
        r"\bnot\b",
        r"\bdon't\b",
        r"\bdoesn't\b",
        r"\bdidn't\b",
        r"\bwon't\b",
        r"\bnever\b",
        r"\bnone\b",
    ]

    def classify_intent(self, request: str) -> IntentMatch:
        """
        Classify the intent from a user request.

        Args:
            request: The user's request text

        Returns:
            IntentMatch with classified task type and confidence
        """
        # Normalize request
        normalized = request.lower().strip()
        words = re.findall(r"\b\w+\b", normalized)

        if not words:
            return IntentMatch(
                task_type=TaskType.IMPLEMENT,
                confidence=0.5,
                matched_keywords=[],
                unmatched_words=[],
            )

        # Calculate scores for each task type
        scores: dict[TaskType, float] = {tt: 0.0 for tt in TaskType}
        matched_keywords: dict[TaskType, list[str]] = {tt: [] for tt in TaskType}

        for i, word in enumerate(words):
            for task_type, patterns in self.INTENT_PATTERNS.items():
                # Check primary keywords (higher weight)
                for keyword in patterns["primary"]:
                    if keyword in word or word in keyword:
                        scores[task_type] += 3.0
                        matched_keywords[task_type].append(keyword)
                        break

                # Check secondary keywords (lower weight)
                for keyword in patterns["secondary"]:
                    if keyword in word or word in keyword:
                        scores[task_type] += 1.0
                        matched_keywords[task_type].append(keyword)
                        break

        # Normalize scores
        max_score = max(scores.values()) if scores.values() else 1.0

        # Find best match
        best_task_type = max(scores, key=lambda k: scores[k])
        best_score = scores[best_task_type]

        # Calculate confidence based on score and margin
        if max_score == 0:
            confidence = 0.3  # Low confidence if no matches
        else:
            # Confidence based on relative score
            confidence = min(0.95, best_score / (max_score * 1.5 + 5))

        # Check for negation patterns that might affect intent
        has_negation = any(re.search(pattern, normalized) for pattern in self.NEGATION_PATTERNS)
        if has_negation:
            confidence *= 0.8  # Reduce confidence if negation detected

        # Get unmatched words
        all_matched = set()
        for keywords in matched_keywords.values():
            all_matched.update(keywords)
        unmatched = [w for w in words if w not in all_matched]

        return IntentMatch(
            task_type=best_task_type,
            confidence=round(confidence, 2),
            matched_keywords=list(set(matched_keywords[best_task_type])),
            unmatched_words=unmatched[:10],  # Limit to first 10
        )


class ComplexityScorer:
    """Estimate task complexity based on request characteristics."""

    # Complexity indicators
    COMPLEXITY_INDICATORS: dict[ComplexityLevel, dict[str, list[str]]] = {
        ComplexityLevel.TRIVIAL: {
            "triggers": ["simple", "one line", "minor", "tiny", "quick", "easy fix"],
            "time_estimates": ["< 5 min", "< 10 min", "5 minutes"],
        },
        ComplexityLevel.SIMPLE: {
            "triggers": ["small", "basic", "easy", "straightforward", "simple"],
            "time_estimates": ["< 1 hour", "30 minutes", "1 hour"],
        },
        ComplexityLevel.MODERATE: {
            "triggers": ["feature", "component", "add", "implement", "create"],
            "time_estimates": ["1-2 hours", "2-4 hours", "half day"],
        },
        ComplexityLevel.COMPLEX: {
            "triggers": ["architecture", "refactor", "redesign", "major", "substantial"],
            "time_estimates": ["4-8 hours", "full day", "one day"],
        },
        ComplexityLevel.EPIC: {
            "triggers": ["system", "complete overhaul", "redesign", "foundation", "platform"],
            "time_estimates": ["2-3 days", "week", "sprint"],
        },
    }

    # Task type complexity modifiers
    TASK_COMPLEXITY_MODIFIERS: dict[TaskType, float] = {
        TaskType.IMPLEMENT: 1.0,
        TaskType.FIX: 0.7,  # Fixes are typically simpler
        TaskType.RESEARCH: 0.5,  # Research is quick to start
        TaskType.REFACTOR: 1.2,  # Refactoring is often complex
        TaskType.EXTEND: 0.9,  # Extending is slightly simpler
        TaskType.CLONE: 0.6,  # Cloning is straightforward
        TaskType.TEST: 0.8,  # Testing varies
        TaskType.DOCS: 0.5,  # Documentation is typically simple
        TaskType.UI: 1.1,  # UI can be complex
        TaskType.INTEGRATION: 1.3,  # Integration is often complex
        TaskType.SECURITY: 1.4,  # Security requires careful analysis
    }

    # Component complexity indicators
    COMPONENT_COMPLEXITY: dict[str, float] = {
        "node": 1.0,
        "workflow": 1.2,
        "orchestrator": 1.5,
        "robot": 1.1,
        "canvas": 1.3,
        "domain": 1.0,
        "infrastructure": 1.2,
        "presentation": 1.1,
        "test": 0.8,
        "docs": 0.5,
    }

    def score_complexity(
        self, request: str, task_type: TaskType, context: dict | None = None
    ) -> tuple[ComplexityLevel, float]:
        """
        Score the complexity of a request.

        Args:
            request: The user's request text
            task_type: The classified task type
            context: Optional context information

        Returns:
            Tuple of (ComplexityLevel, confidence)
        """
        normalized = request.lower()

        # Base score from indicators
        scores: dict[ComplexityLevel, float] = {cl: 0.0 for cl in ComplexityLevel}

        for complexity, indicators in self.COMPLEXITY_INDICATORS.items():
            # Check triggers
            for trigger in indicators["triggers"]:
                if trigger in normalized:
                    scores[complexity] += 2.0

            # Check time estimates
            for estimate in indicators["time_estimates"]:
                if estimate in normalized:
                    scores[complexity] += 1.5

        # Check for component mentions
        for component, modifier in self.COMPONENT_COMPLEXITY.items():
            if component in normalized:
                # Add complexity based on component
                base_score = 1.0 * modifier
                for cl in ComplexityLevel:
                    scores[cl] += base_score * (1.0 / cl.value)

        # Apply task type modifier
        task_modifier = self.TASK_COMPLEXITY_MODIFIERS[task_type]
        for cl in ComplexityLevel:
            scores[cl] *= task_modifier

        # Check context for additional complexity hints
        if context:
            if "files_affected" in context:
                file_count = len(context["files_affected"])
                if file_count > 10:
                    scores[ComplexityLevel.COMPLEX] += 2.0
                    scores[ComplexityLevel.EPIC] += 1.0
                elif file_count > 5:
                    scores[ComplexityLevel.MODERATE] += 1.0
                    scores[ComplexityLevel.COMPLEX] += 0.5

            if "breaking_change" in context and context["breaking_change"]:
                scores[ComplexityLevel.COMPLEX] += 2.0
                scores[ComplexityLevel.EPIC] += 1.0

        # Normalize and find best match
        total_score = sum(scores.values())
        if total_score == 0:
            return ComplexityLevel.MODERATE, 0.5

        # Calculate confidence based on score distribution
        max_score = max(scores.values())
        confidence = min(0.95, max_score / (total_score / len(scores) + 1))

        # Find the best matching complexity level
        best_level = max(scores, key=lambda k: scores[k])

        # Adjust based on score thresholds
        normalized_max = max_score / task_modifier
        if normalized_max < 2:
            best_level = ComplexityLevel.TRIVIAL
        elif normalized_max < 5:
            best_level = ComplexityLevel.SIMPLE
        elif normalized_max < 10:
            best_level = ComplexityLevel.MODERATE
        elif normalized_max < 20:
            best_level = ComplexityLevel.COMPLEX
        else:
            best_level = ComplexityLevel.EPIC

        return best_level, round(confidence, 2)


class ContextAwareClassifier:
    """Use context information to improve classification."""

    # Session context keys that affect classification
    CONTEXT_KEYS = [
        "recent_task_type",
        "active_files",
        "component_area",
        "user_expertise",
    ]

    def enhance_classification(
        self, intent_match: IntentMatch, complexity: ComplexityLevel, context: dict | None = None
    ) -> tuple[ClassificationResult, list[str]]:
        """
        Enhance classification with context awareness.

        Args:
            intent_match: The intent classification result
            complexity: The complexity level
            context: Optional session context

        Returns:
            Enhanced ClassificationResult and reasoning
        """
        reasoning = []
        confidence = intent_match.confidence
        suggested_parallel: list[str] = []
        risk_level = "medium"

        if context:
            # Check if this is similar to recent work
            if "recent_task_type" in context:
                recent_type = context["recent_task_type"]
                if recent_type == intent_match.task_type.value:
                    confidence = min(0.95, confidence + 0.1)
                    reasoning.append(
                        f"Same task type as recent work ({recent_type}), increased confidence"
                    )

            # Check for component-specific patterns
            if "component_area" in context:
                area = context["component_area"]
                if self._area_suggests_task_type(area, intent_match.task_type):
                    confidence = min(0.95, confidence + 0.05)
                    reasoning.append(
                        f"Component area ({area}) supports {intent_match.task_type.value}"
                    )

            # Suggest parallel execution based on context
            if "can_run_parallel" in context:
                suggested_parallel = context["can_run_parallel"]

            # Adjust risk based on area
            risk_level = self._calculate_risk_level(intent_match.task_type, context)

        # Calculate estimated duration based on complexity
        estimated_duration = self._estimate_duration(complexity, intent_match.task_type)

        # Build reasoning from intent match
        if intent_match.matched_keywords:
            reasoning.insert(0, f"Matched keywords: {', '.join(intent_match.matched_keywords[:5])}")
        if intent_match.unmatched_words:
            reasoning.append(f"Could not classify: {', '.join(intent_match.unmatched_words[:3])}")

        result = ClassificationResult(
            task_type=intent_match.task_type,
            complexity=complexity,
            confidence=confidence,
            estimated_duration=estimated_duration,
            suggested_parallel=suggested_parallel,
            reasoning=reasoning,
            risk_level=risk_level,
        )

        return result, reasoning

    def _area_suggests_task_type(self, area: str, task_type: TaskType) -> bool:
        """Check if component area suggests a specific task type."""
        area_task_mapping = {
            "presentation": [TaskType.UI, TaskType.IMPLEMENT],
            "domain": [TaskType.REFACTOR, TaskType.IMPLEMENT],
            "infrastructure": [TaskType.INTEGRATION, TaskType.IMPLEMENT],
            "nodes": [TaskType.IMPLEMENT, TaskType.CLONE],
            "tests": [TaskType.TEST, TaskType.IMPLEMENT],
        }

        if area in area_task_mapping:
            return task_type in area_task_mapping[area]
        return False

    def _calculate_risk_level(self, task_type: TaskType, context: dict) -> str:
        """Calculate risk level based on task type and context."""
        base_risk = {
            TaskType.IMPLEMENT: "medium",
            TaskType.FIX: "low",
            TaskType.RESEARCH: "low",
            TaskType.REFACTOR: "high",
            TaskType.EXTEND: "medium",
            TaskType.CLONE: "low",
            TaskType.TEST: "low",
            TaskType.DOCS: "low",
            TaskType.UI: "medium",
            TaskType.INTEGRATION: "high",
            TaskType.SECURITY: "high",
        }

        risk = base_risk.get(task_type, "medium")

        # Increase risk if modifying many files
        if "files_affected" in context:
            file_count = len(context["files_affected"])
            if file_count > 10:
                risk = "critical"
            elif file_count > 5:
                risk = "high"

        # Increase risk if breaking changes
        if context.get("breaking_change", False):
            risk = "critical"

        return risk

    def _estimate_duration(self, complexity: ComplexityLevel, task_type: TaskType) -> int:
        """Estimate duration in minutes based on complexity and task type."""
        # Base duration by complexity (in minutes)
        base_duration = {
            ComplexityLevel.TRIVIAL: 15,
            ComplexityLevel.SIMPLE: 30,
            ComplexityLevel.MODERATE: 60,
            ComplexityLevel.COMPLEX: 120,
            ComplexityLevel.EPIC: 240,
        }

        # Task type modifiers
        task_modifier = {
            TaskType.IMPLEMENT: 1.0,
            TaskType.FIX: 0.7,
            TaskType.RESEARCH: 0.5,
            TaskType.REFACTOR: 1.2,
            TaskType.EXTEND: 0.9,
            TaskType.CLONE: 0.6,
            TaskType.TEST: 0.8,
            TaskType.DOCS: 0.5,
            TaskType.UI: 1.1,
            TaskType.INTEGRATION: 1.3,
            TaskType.SECURITY: 1.4,
        }

        duration = base_duration[complexity] * task_modifier[task_type]
        return int(duration)


class SmartChainSelector:
    """
    Main service for intelligent task classification.

    Orchestrates:
    - Intent classification
    - Complexity scoring
    - Context awareness
    - Historical pattern matching
    """

    def __init__(self):
        self.intent_classifier = IntentClassifier()
        self.complexity_scorer = ComplexityScorer()
        self.context_aware = ContextAwareClassifier()
        logger.info("SmartChainSelector initialized")

    def classify(self, request: str, context: dict | None = None) -> ClassificationResult:
        """
        Classify a user request into task type and complexity.

        Args:
            request: The user's request text
            context: Optional context information

        Returns:
            ClassificationResult with task type, complexity, and metadata
        """
        logger.debug(f"Classifying request: {request[:100]}...")

        # Step 1: Classify intent
        intent_match = self.intent_classifier.classify_intent(request)
        logger.debug(
            f"Intent classified as {intent_match.task_type.value} "
            f"(confidence: {intent_match.confidence})"
        )

        # Step 2: Score complexity
        complexity, complexity_confidence = self.complexity_scorer.score_complexity(
            request, intent_match.task_type, context
        )
        logger.debug(
            f"Complexity scored as {complexity.name} (confidence: {complexity_confidence})"
        )

        # Step 3: Enhance with context
        result, reasoning = self.context_aware.enhance_classification(
            intent_match, complexity, context
        )

        logger.info(
            f"Classification complete: {result.task_type.value} / "
            f"{result.complexity.name} (confidence: {result.confidence})"
        )

        return result

    def classify_with_fallback(
        self,
        request: str,
        context: dict | None = None,
        manual_task_type: TaskType | None = None,
    ) -> ClassificationResult:
        """
        Classify with fallback to manual task type if confidence is low.

        Args:
            request: The user's request text
            context: Optional context information
            manual_task_type: Manual override if confidence is low

        Returns:
            ClassificationResult
        """
        result = self.classify(request, context)

        # If confidence is too low, use manual override or default
        if result.confidence < 0.6:
            logger.warning(f"Low confidence ({result.confidence}), using fallback")

            if manual_task_type:
                result.task_type = manual_task_type
                result.reasoning.append(f"Used manual override: {manual_task_type.value}")
            else:
                # Default to implement with low confidence warning
                result.task_type = TaskType.IMPLEMENT
                result.reasoning.append("Defaulted to IMPLEMENT due to low confidence")

            # Re-estimate duration based on complexity
            result.estimated_duration = self.context_aware._estimate_duration(
                result.complexity, result.task_type
            )

        return result

    def _estimate_duration_for_type(self, complexity: ComplexityLevel, task_type: TaskType) -> int:
        """Estimate duration for a given complexity and task type."""
        return self.context_aware._estimate_duration(complexity, task_type)

    def get_chain_suggestion(self, classification: ClassificationResult) -> dict[str, Any]:
        """
        Get chain execution suggestion based on classification.

        Args:
            classification: The classification result

        Returns:
            Dict with suggested chain configuration
        """
        chain_templates = {
            TaskType.IMPLEMENT: {
                "agents": ["explore", "architect", "builder", "quality", "reviewer"],
                "default_parallel": ["docs", "security"],
            },
            TaskType.FIX: {
                "agents": ["explore", "builder", "quality", "reviewer"],
                "default_parallel": [],
            },
            TaskType.RESEARCH: {
                "agents": ["explore", "researcher"],
                "default_parallel": [],
            },
            TaskType.REFACTOR: {
                "agents": ["explore", "refactor", "quality", "reviewer"],
                "default_parallel": ["docs"],
            },
            TaskType.EXTEND: {
                "agents": ["explore", "architect", "builder", "quality", "reviewer"],
                "default_parallel": ["docs"],
            },
            TaskType.CLONE: {
                "agents": ["explore", "builder", "quality", "reviewer"],
                "default_parallel": [],
            },
            TaskType.TEST: {
                "agents": ["explore", "quality", "reviewer"],
                "default_parallel": [],
            },
            TaskType.DOCS: {
                "agents": ["explore", "docs", "reviewer"],
                "default_parallel": [],
            },
            TaskType.UI: {
                "agents": ["explore", "ui", "quality", "reviewer"],
                "default_parallel": [],
            },
            TaskType.INTEGRATION: {
                "agents": ["explore", "integrations", "quality", "reviewer"],
                "default_parallel": ["security"],
            },
            TaskType.SECURITY: {
                "agents": ["explore", "security", "reviewer"],
                "default_parallel": [],
            },
        }

        template = chain_templates.get(
            classification.task_type, chain_templates[TaskType.IMPLEMENT]
        )

        return {
            "task_type": classification.task_type.value,
            "agents": template["agents"],
            "parallel_agents": template["default_parallel"],
            "estimated_duration": classification.estimated_duration,
            "complexity": classification.complexity.name,
            "risk_level": classification.risk_level,
        }
