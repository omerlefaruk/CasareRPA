"""
CasareRPA - AI-Powered Selector Healer

Enhanced selector healing with fuzzy matching, semantic similarity,
and optional LLM-based element understanding.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from enum import Enum
from typing import Any

from loguru import logger


class HealingStrategy(Enum):
    """Strategies used for healing."""

    FUZZY_TEXT = "fuzzy_text"
    FUZZY_ATTRIBUTE = "fuzzy_attribute"
    SEMANTIC = "semantic"
    STRUCTURAL = "structural"
    REGEX_PATTERN = "regex_pattern"
    SYNONYM = "synonym"


@dataclass
class AIHealingResult:
    """Result of AI-enhanced selector healing."""

    success: bool
    original_selector: str
    healed_selector: str
    confidence: float
    strategy_used: str
    match_details: dict[str, float] = field(default_factory=dict)
    alternatives: list[tuple[str, float]] = field(default_factory=list)
    llm_used: bool = False
    healing_time_ms: float = 0.0


# Common UI term synonyms for semantic matching
UI_SYNONYMS: dict[str, list[str]] = {
    "sign_in": ["login", "log in", "sign in", "signin", "log-in", "sign-in"],
    "sign_out": ["logout", "log out", "sign out", "signout", "log-out", "sign-out"],
    "sign_up": [
        "register",
        "create account",
        "sign up",
        "signup",
        "join",
        "get started",
    ],
    "submit": ["send", "confirm", "ok", "done", "continue", "next", "proceed", "go"],
    "cancel": ["close", "dismiss", "back", "abort", "nevermind", "exit"],
    "search": ["find", "lookup", "query", "filter", "browse"],
    "delete": ["remove", "trash", "discard", "erase", "clear"],
    "edit": ["modify", "change", "update", "revise"],
    "save": ["store", "apply", "keep", "preserve", "commit"],
    "add": ["create", "new", "insert", "plus"],
    "settings": ["preferences", "options", "config", "configuration"],
    "profile": ["account", "user", "my account"],
    "home": ["main", "dashboard", "start"],
    "help": ["support", "faq", "assistance", "info"],
    "menu": ["nav", "navigation", "hamburger"],
    "cart": ["basket", "bag", "shopping cart"],
    "checkout": ["pay", "payment", "purchase", "buy now"],
    "password": ["pass", "pwd", "secret"],
    "email": ["e-mail", "mail", "email address"],
    "username": ["user", "user name", "userid", "user id"],
    "first_name": ["firstname", "first name", "given name", "forename"],
    "last_name": ["lastname", "last name", "surname", "family name"],
    "phone": ["telephone", "tel", "mobile", "cell"],
    "address": ["location", "addr"],
}

# Build reverse lookup for quick synonym checking
_SYNONYM_LOOKUP: dict[str, str] = {}
for canonical, synonyms in UI_SYNONYMS.items():
    for syn in synonyms:
        _SYNONYM_LOOKUP[syn.lower().replace(" ", "").replace("-", "")] = canonical
    _SYNONYM_LOOKUP[canonical.replace("_", "")] = canonical


class FuzzyMatcher:
    """Fuzzy string matching utilities."""

    @staticmethod
    def levenshtein_distance(s1: str, s2: str) -> int:
        """Calculate Levenshtein edit distance between two strings."""
        if len(s1) < len(s2):
            return FuzzyMatcher.levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    @staticmethod
    def levenshtein_similarity(s1: str, s2: str) -> float:
        """Calculate similarity ratio based on Levenshtein distance (0.0-1.0)."""
        if not s1 and not s2:
            return 1.0
        if not s1 or not s2:
            return 0.0

        max_len = max(len(s1), len(s2))
        distance = FuzzyMatcher.levenshtein_distance(s1, s2)
        return 1.0 - (distance / max_len)

    @staticmethod
    def jaro_similarity(s1: str, s2: str) -> float:
        """Calculate Jaro similarity (0.0-1.0)."""
        if s1 == s2:
            return 1.0
        if not s1 or not s2:
            return 0.0

        len1, len2 = len(s1), len(s2)
        match_distance = max(len1, len2) // 2 - 1
        if match_distance < 0:
            match_distance = 0

        s1_matches = [False] * len1
        s2_matches = [False] * len2
        matches = 0
        transpositions = 0

        for i in range(len1):
            start = max(0, i - match_distance)
            end = min(i + match_distance + 1, len2)

            for j in range(start, end):
                if s2_matches[j] or s1[i] != s2[j]:
                    continue
                s1_matches[i] = True
                s2_matches[j] = True
                matches += 1
                break

        if matches == 0:
            return 0.0

        k = 0
        for i in range(len1):
            if not s1_matches[i]:
                continue
            while not s2_matches[k]:
                k += 1
            if s1[i] != s2[k]:
                transpositions += 1
            k += 1

        return (matches / len1 + matches / len2 + (matches - transpositions / 2) / matches) / 3

    @staticmethod
    def jaro_winkler_similarity(s1: str, s2: str, prefix_weight: float = 0.1) -> float:
        """Calculate Jaro-Winkler similarity (0.0-1.0), favoring common prefixes."""
        jaro_sim = FuzzyMatcher.jaro_similarity(s1, s2)

        # Find common prefix length (max 4)
        prefix_len = 0
        for i in range(min(len(s1), len(s2), 4)):
            if s1[i] == s2[i]:
                prefix_len += 1
            else:
                break

        return jaro_sim + prefix_len * prefix_weight * (1 - jaro_sim)

    @staticmethod
    def token_set_ratio(s1: str, s2: str) -> float:
        """
        Calculate similarity based on word tokens (order-independent).
        Handles cases like "Sign In" vs "In Sign" or "Log In Button" vs "Login".
        """
        # Normalize and tokenize
        tokens1 = set(re.split(r"[\s\-_]+", s1.lower().strip()))
        tokens2 = set(re.split(r"[\s\-_]+", s2.lower().strip()))

        # Remove empty tokens
        tokens1.discard("")
        tokens2.discard("")

        if not tokens1 and not tokens2:
            return 1.0
        if not tokens1 or not tokens2:
            return 0.0

        intersection = tokens1 & tokens2
        union = tokens1 | tokens2

        return len(intersection) / len(union)

    @staticmethod
    def sequence_ratio(s1: str, s2: str) -> float:
        """Use Python's SequenceMatcher for similarity."""
        return SequenceMatcher(None, s1.lower(), s2.lower()).ratio()


class SemanticMatcher:
    """Semantic text matching using synonyms and optional LLM."""

    def __init__(self, llm_manager: Any = None):
        """
        Initialize semantic matcher.

        Args:
            llm_manager: Optional LLMResourceManager for advanced matching
        """
        self._llm_manager = llm_manager

    def normalize_text(self, text: str) -> str:
        """Normalize text for matching."""
        # Convert to lowercase, remove extra whitespace
        normalized = text.lower().strip()
        # Remove common prefixes/suffixes
        normalized = re.sub(r"^(btn|button|link|input|text)[-_]?", "", normalized)
        normalized = re.sub(r"[-_]?(btn|button|link|input|text)$", "", normalized)
        # Remove non-alphanumeric except spaces
        normalized = re.sub(r"[^\w\s]", " ", normalized)
        # Collapse whitespace
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return normalized

    def get_canonical_form(self, text: str) -> str | None:
        """Get canonical form if text is a known synonym."""
        normalized = text.lower().replace(" ", "").replace("-", "").replace("_", "")
        return _SYNONYM_LOOKUP.get(normalized)

    def are_synonyms(self, text1: str, text2: str) -> bool:
        """Check if two texts are synonyms of each other."""
        canonical1 = self.get_canonical_form(text1)
        canonical2 = self.get_canonical_form(text2)

        if canonical1 and canonical2:
            return canonical1 == canonical2

        # Direct check in synonym lists
        norm1 = self.normalize_text(text1)
        norm2 = self.normalize_text(text2)

        for synonyms in UI_SYNONYMS.values():
            norm_synonyms = [s.lower() for s in synonyms]
            if norm1 in norm_synonyms and norm2 in norm_synonyms:
                return True

        return False

    def synonym_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity considering synonyms.
        Returns 1.0 for exact synonyms, 0.0 for unrelated.
        """
        if self.are_synonyms(text1, text2):
            return 1.0

        # Check partial synonym matches (one word in text is synonym)
        tokens1 = set(re.split(r"[\s\-_]+", text1.lower()))
        tokens2 = set(re.split(r"[\s\-_]+", text2.lower()))

        for t1 in tokens1:
            for t2 in tokens2:
                if self.are_synonyms(t1, t2):
                    # Partial match based on how much of text is matched
                    match_weight = 1.0 / max(len(tokens1), len(tokens2))
                    return 0.5 + (0.5 * match_weight)

        return 0.0

    async def llm_similarity(self, text1: str, text2: str) -> float | None:
        """
        Use LLM to determine semantic similarity.
        Returns None if LLM is not available.
        """
        if not self._llm_manager:
            return None

        try:
            prompt = f"""Rate the semantic similarity between these two UI element labels on a scale of 0.0 to 1.0.
Consider if they would refer to the same action or element in a user interface.

Label 1: "{text1}"
Label 2: "{text2}"

Return ONLY a number between 0.0 and 1.0, nothing else."""

            response = await self._llm_manager.completion(
                prompt=prompt,
                model="gpt-4o-mini",
                temperature=0.0,
                max_tokens=10,
            )

            # Parse response
            score = float(response.content.strip())
            return max(0.0, min(1.0, score))

        except Exception as e:
            logger.debug(f"LLM similarity failed: {e}")
            return None


class RegexPatternMatcher:
    """Match selectors using regex patterns for dynamic IDs."""

    # Common patterns for dynamic IDs
    # Tuples of (search_pattern, replacement_pattern)
    DYNAMIC_PATTERNS = [
        (r"[-_]?\d{4,}[-_]?", r"[-_]?\d+[-_]?"),  # Long numeric IDs
        (r"[-_][a-f0-9]{8,}[-_]?", r"[-_][a-f0-9]+[-_]?"),  # Hex IDs (UUIDs)
        (r"[-_]\d+$", r"[-_]\d+"),  # Trailing numbers
        (r"^[a-z]+[-_]\d+[-_]", r"[a-z]+[-_]\d+[-_]"),  # Prefix-number patterns
    ]

    @classmethod
    def extract_pattern(cls, value: str) -> str | None:
        """Extract a regex pattern from a value with dynamic parts."""
        result = value
        found_dynamic = False

        for dynamic_re, replacement in cls.DYNAMIC_PATTERNS:
            match = re.search(dynamic_re, value, re.IGNORECASE)
            if match:
                # Replace the dynamic part with the pattern
                result = result.replace(match.group(), replacement, 1)
                found_dynamic = True

        # Return pattern if we found dynamic parts
        if found_dynamic:
            return result
        return None

    @classmethod
    def matches_pattern(cls, pattern: str, value: str) -> bool:
        """Check if value matches a pattern."""
        try:
            return bool(re.match(f"^{pattern}$", value, re.IGNORECASE))
        except re.error:
            return False

    @classmethod
    def pattern_similarity(cls, value1: str, value2: str) -> float:
        """
        Calculate similarity considering dynamic patterns.
        Returns 1.0 if both match the same pattern.
        """
        # Extract patterns from both
        pattern1 = cls.extract_pattern(value1)
        pattern2 = cls.extract_pattern(value2)

        # If both have patterns
        if pattern1 and pattern2:
            # Check if they're the same pattern
            if pattern1 == pattern2:
                return 1.0
            # Check if one matches the other's pattern
            if cls.matches_pattern(pattern1, value2):
                return 0.9
            if cls.matches_pattern(pattern2, value1):
                return 0.9

        # If only one has a pattern, check if the other matches
        if pattern1 and cls.matches_pattern(pattern1, value2):
            return 0.85
        if pattern2 and cls.matches_pattern(pattern2, value1):
            return 0.85

        return 0.0


class AISelectorHealer:
    """
    AI-enhanced selector healer combining fuzzy, semantic, and pattern matching.

    Designed to be used as an enhancement layer on top of the existing
    SelectorHealer, providing higher-quality matching for difficult cases.
    """

    def __init__(
        self,
        min_confidence: float = 0.6,
        use_llm: bool = False,
        llm_manager: Any = None,
    ):
        """
        Initialize the AI selector healer.

        Args:
            min_confidence: Minimum confidence threshold (0.0-1.0)
            use_llm: Whether to use LLM for semantic matching
            llm_manager: LLMResourceManager instance for LLM matching
        """
        self.min_confidence = min_confidence
        self.use_llm = use_llm
        self.semantic_matcher = SemanticMatcher(llm_manager if use_llm else None)

        # Weights for different matching strategies
        self.weights = {
            "text": 0.35,
            "id": 0.25,
            "classes": 0.15,
            "attributes": 0.15,
            "position": 0.10,
        }

        logger.debug(f"AISelectorHealer initialized (min_conf={min_confidence}, llm={use_llm})")

    def fuzzy_text_match(
        self,
        text1: str,
        text2: str,
        use_semantic: bool = True,
    ) -> tuple[float, str]:
        """
        Calculate fuzzy text similarity using multiple algorithms.

        Args:
            text1: First text
            text2: Second text
            use_semantic: Whether to use semantic matching

        Returns:
            Tuple of (similarity_score, strategy_used)
        """
        if not text1 or not text2:
            return (0.0, "empty")

        # Normalize texts
        norm1 = self.semantic_matcher.normalize_text(text1)
        norm2 = self.semantic_matcher.normalize_text(text2)

        # Exact match after normalization
        if norm1 == norm2:
            return (1.0, "exact")

        # Check synonyms first (fast path)
        if use_semantic:
            syn_score = self.semantic_matcher.synonym_similarity(text1, text2)
            if syn_score >= 0.9:
                return (syn_score, "synonym")

        # Try multiple fuzzy algorithms
        scores = {
            "levenshtein": FuzzyMatcher.levenshtein_similarity(norm1, norm2),
            "jaro_winkler": FuzzyMatcher.jaro_winkler_similarity(norm1, norm2),
            "token_set": FuzzyMatcher.token_set_ratio(norm1, norm2),
            "sequence": FuzzyMatcher.sequence_ratio(norm1, norm2),
        }

        # Use maximum score
        best_algo = max(scores, key=scores.get)
        best_score = scores[best_algo]

        # Boost if partial synonym match
        if use_semantic and syn_score > 0:
            best_score = max(best_score, syn_score)
            if syn_score > best_score:
                best_algo = "synonym"

        return (best_score, best_algo)

    def fuzzy_attribute_match(
        self,
        attrs1: dict[str, Any],
        attrs2: dict[str, Any],
    ) -> tuple[float, dict[str, float]]:
        """
        Calculate fuzzy similarity between attribute dictionaries.

        Args:
            attrs1: First attribute dict
            attrs2: Second attribute dict

        Returns:
            Tuple of (overall_score, per_attribute_scores)
        """
        per_attr_scores: dict[str, float] = {}
        total_weight = 0.0
        weighted_sum = 0.0

        # Compare ID attributes
        if "id" in attrs1 or "id" in attrs2:
            id1 = attrs1.get("id", "")
            id2 = attrs2.get("id", "")
            if id1 and id2:
                # Try pattern matching first
                pattern_score = RegexPatternMatcher.pattern_similarity(id1, id2)
                if pattern_score > 0:
                    per_attr_scores["id"] = pattern_score
                else:
                    per_attr_scores["id"] = FuzzyMatcher.levenshtein_similarity(id1, id2)
            elif id1 == id2:  # Both empty
                per_attr_scores["id"] = 1.0
            else:
                per_attr_scores["id"] = 0.0

            weighted_sum += per_attr_scores["id"] * self.weights["id"]
            total_weight += self.weights["id"]

        # Compare class lists
        classes1 = set(attrs1.get("class_list", []))
        classes2 = set(attrs2.get("class_list", []))
        if classes1 or classes2:
            if classes1 and classes2:
                # Fuzzy class matching - check each class pair
                best_matches = []
                for c1 in classes1:
                    best_match = 0.0
                    for c2 in classes2:
                        score = FuzzyMatcher.jaro_winkler_similarity(c1, c2)
                        best_match = max(best_match, score)
                    best_matches.append(best_match)

                if best_matches:
                    per_attr_scores["classes"] = sum(best_matches) / len(best_matches)
                else:
                    per_attr_scores["classes"] = 0.0
            else:
                per_attr_scores["classes"] = 0.0

            weighted_sum += per_attr_scores["classes"] * self.weights["classes"]
            total_weight += self.weights["classes"]

        # Compare text content
        text1 = attrs1.get("text_content", "")
        text2 = attrs2.get("text_content", "")
        if text1 or text2:
            text_score, _ = self.fuzzy_text_match(text1, text2)
            per_attr_scores["text"] = text_score
            weighted_sum += text_score * self.weights["text"]
            total_weight += self.weights["text"]

        # Compare other attributes (name, placeholder, aria-label, etc.)
        other_attrs = [
            "name",
            "placeholder",
            "aria-label",
            "title",
            "data-testid",
            "role",
            "type",
        ]
        attr_scores = []
        for attr in other_attrs:
            v1 = attrs1.get(attr, "")
            v2 = attrs2.get(attr, "")
            if v1 or v2:
                if v1 and v2:
                    score, _ = self.fuzzy_text_match(v1, v2, use_semantic=False)
                    attr_scores.append(score)
                elif v1 == v2:
                    attr_scores.append(1.0)
                else:
                    attr_scores.append(0.0)

        if attr_scores:
            per_attr_scores["attributes"] = sum(attr_scores) / len(attr_scores)
            weighted_sum += per_attr_scores["attributes"] * self.weights["attributes"]
            total_weight += self.weights["attributes"]

        # Compare position (if available)
        pos1 = attrs1.get("position")
        pos2 = attrs2.get("position")
        if pos1 and pos2:
            try:
                x1, y1 = pos1.get("x", 0), pos1.get("y", 0)
                x2, y2 = pos2.get("x", 0), pos2.get("y", 0)
                distance = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
                # Score based on distance (within 50px is good, 200px is threshold)
                if distance <= 50:
                    per_attr_scores["position"] = 1.0
                elif distance <= 200:
                    per_attr_scores["position"] = 1.0 - (distance - 50) / 150
                else:
                    per_attr_scores["position"] = 0.0

                weighted_sum += per_attr_scores["position"] * self.weights["position"]
                total_weight += self.weights["position"]
            except (TypeError, KeyError):
                pass

        overall = weighted_sum / total_weight if total_weight > 0 else 0.0
        return (overall, per_attr_scores)

    async def find_best_match(
        self,
        page: Any,
        original_fingerprint: dict[str, Any],
        candidate_elements: list[dict[str, Any]],
    ) -> AIHealingResult:
        """
        Find the best matching element from candidates.

        Args:
            page: Playwright page
            original_fingerprint: Original element fingerprint
            candidate_elements: List of candidate element fingerprints

        Returns:
            AIHealingResult with best match
        """
        import time

        start_time = time.time()

        best_match = None
        best_score = 0.0
        best_details: dict[str, float] = {}
        best_strategy = "none"
        alternatives: list[tuple[str, float]] = []

        for candidate in candidate_elements:
            # Calculate fuzzy attribute match
            score, details = self.fuzzy_attribute_match(original_fingerprint, candidate)

            # Track alternatives
            selector = candidate.get("selector", "")
            if score >= self.min_confidence:
                alternatives.append((selector, score))

            if score > best_score:
                best_score = score
                best_match = candidate
                best_details = details
                best_strategy = self._determine_strategy(details)

        # Sort alternatives by score
        alternatives.sort(key=lambda x: x[1], reverse=True)
        alternatives = alternatives[:5]  # Keep top 5

        elapsed_ms = (time.time() - start_time) * 1000

        if best_match and best_score >= self.min_confidence:
            return AIHealingResult(
                success=True,
                original_selector=original_fingerprint.get("selector", ""),
                healed_selector=best_match.get("selector", ""),
                confidence=best_score,
                strategy_used=best_strategy,
                match_details=best_details,
                alternatives=alternatives,
                llm_used=False,
                healing_time_ms=elapsed_ms,
            )
        else:
            return AIHealingResult(
                success=False,
                original_selector=original_fingerprint.get("selector", ""),
                healed_selector="",
                confidence=best_score,
                strategy_used="none",
                match_details=best_details,
                alternatives=alternatives,
                llm_used=False,
                healing_time_ms=elapsed_ms,
            )

    def _determine_strategy(self, details: dict[str, float]) -> str:
        """Determine which strategy contributed most to the match."""
        if not details:
            return "unknown"

        best_attr = max(details, key=details.get)
        score = details[best_attr]

        if best_attr == "text" and score > 0.8:
            return HealingStrategy.FUZZY_TEXT.value
        elif best_attr == "id" and score > 0.8:
            return HealingStrategy.REGEX_PATTERN.value
        elif best_attr == "classes":
            return HealingStrategy.FUZZY_ATTRIBUTE.value
        else:
            return HealingStrategy.STRUCTURAL.value

    async def enhance_similarity_score(
        self,
        original_text: str,
        candidate_text: str,
        base_score: float,
    ) -> float:
        """
        Enhance a base similarity score with semantic matching.

        Args:
            original_text: Original element text
            candidate_text: Candidate element text
            base_score: Base similarity score from heuristic matching

        Returns:
            Enhanced similarity score
        """
        # If base score is already high, no need for enhancement
        if base_score >= 0.9:
            return base_score

        # Try synonym matching
        syn_score = self.semantic_matcher.synonym_similarity(original_text, candidate_text)
        if syn_score > base_score:
            return syn_score

        # Try fuzzy text matching
        fuzzy_score, _ = self.fuzzy_text_match(original_text, candidate_text)
        if fuzzy_score > base_score:
            return fuzzy_score

        # Optionally try LLM
        if self.use_llm and base_score < 0.7:
            llm_score = await self.semantic_matcher.llm_similarity(original_text, candidate_text)
            if llm_score and llm_score > base_score:
                return llm_score

        return base_score


__all__ = [
    "AISelectorHealer",
    "AIHealingResult",
    "FuzzyMatcher",
    "SemanticMatcher",
    "RegexPatternMatcher",
    "HealingStrategy",
    "UI_SYNONYMS",
]
