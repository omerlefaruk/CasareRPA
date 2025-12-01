"""Tests for AI-Powered Selector Healer."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from casare_rpa.utils.selectors.ai_selector_healer import (
    AISelectorHealer,
    AIHealingResult,
    FuzzyMatcher,
    SemanticMatcher,
    RegexPatternMatcher,
    HealingStrategy,
    UI_SYNONYMS,
)


class TestFuzzyMatcher:
    """Tests for FuzzyMatcher class."""

    def test_levenshtein_distance_identical(self):
        """Test Levenshtein distance for identical strings."""
        assert FuzzyMatcher.levenshtein_distance("hello", "hello") == 0

    def test_levenshtein_distance_one_edit(self):
        """Test Levenshtein distance for one character difference."""
        assert FuzzyMatcher.levenshtein_distance("hello", "hallo") == 1
        assert FuzzyMatcher.levenshtein_distance("cat", "cats") == 1

    def test_levenshtein_distance_empty(self):
        """Test Levenshtein distance with empty strings."""
        assert FuzzyMatcher.levenshtein_distance("", "") == 0
        assert FuzzyMatcher.levenshtein_distance("hello", "") == 5
        assert FuzzyMatcher.levenshtein_distance("", "world") == 5

    def test_levenshtein_similarity_identical(self):
        """Test Levenshtein similarity for identical strings."""
        assert FuzzyMatcher.levenshtein_similarity("hello", "hello") == 1.0

    def test_levenshtein_similarity_similar(self):
        """Test Levenshtein similarity for similar strings."""
        sim = FuzzyMatcher.levenshtein_similarity("hello", "hallo")
        assert 0.7 < sim < 0.9

    def test_levenshtein_similarity_different(self):
        """Test Levenshtein similarity for very different strings."""
        sim = FuzzyMatcher.levenshtein_similarity("abc", "xyz")
        assert sim < 0.5

    def test_jaro_similarity_identical(self):
        """Test Jaro similarity for identical strings."""
        assert FuzzyMatcher.jaro_similarity("hello", "hello") == 1.0

    def test_jaro_similarity_similar(self):
        """Test Jaro similarity for similar strings."""
        sim = FuzzyMatcher.jaro_similarity("MARTHA", "MARHTA")
        assert sim > 0.9

    def test_jaro_similarity_empty(self):
        """Test Jaro similarity with empty strings."""
        assert FuzzyMatcher.jaro_similarity("", "") == 1.0
        assert FuzzyMatcher.jaro_similarity("hello", "") == 0.0

    def test_jaro_winkler_similarity_common_prefix(self):
        """Test Jaro-Winkler gives bonus for common prefix."""
        jaro = FuzzyMatcher.jaro_similarity("MARTHA", "MARHTA")
        jaro_winkler = FuzzyMatcher.jaro_winkler_similarity("MARTHA", "MARHTA")
        assert jaro_winkler > jaro

    def test_jaro_winkler_similarity_identical(self):
        """Test Jaro-Winkler for identical strings."""
        assert FuzzyMatcher.jaro_winkler_similarity("hello", "hello") == 1.0

    def test_token_set_ratio_identical(self):
        """Test token set ratio for identical strings."""
        assert FuzzyMatcher.token_set_ratio("hello world", "hello world") == 1.0

    def test_token_set_ratio_reordered(self):
        """Test token set ratio for reordered words."""
        assert FuzzyMatcher.token_set_ratio("hello world", "world hello") == 1.0

    def test_token_set_ratio_partial(self):
        """Test token set ratio for partial match."""
        ratio = FuzzyMatcher.token_set_ratio("hello world", "hello")
        assert 0.4 < ratio < 0.6  # 1 of 2 tokens match

    def test_token_set_ratio_different_separators(self):
        """Test token set ratio handles different separators."""
        assert FuzzyMatcher.token_set_ratio("sign-in", "sign_in") == 1.0
        assert FuzzyMatcher.token_set_ratio("sign in", "sign-in") == 1.0

    def test_sequence_ratio_identical(self):
        """Test sequence ratio for identical strings."""
        assert FuzzyMatcher.sequence_ratio("hello", "hello") == 1.0

    def test_sequence_ratio_similar(self):
        """Test sequence ratio for similar strings."""
        ratio = FuzzyMatcher.sequence_ratio("hello world", "hello worlds")
        assert ratio > 0.9


class TestSemanticMatcher:
    """Tests for SemanticMatcher class."""

    def test_normalize_text_lowercase(self):
        """Test text normalization converts to lowercase."""
        matcher = SemanticMatcher()
        assert matcher.normalize_text("HELLO") == "hello"

    def test_normalize_text_strips_whitespace(self):
        """Test text normalization strips whitespace."""
        matcher = SemanticMatcher()
        assert matcher.normalize_text("  hello  ") == "hello"

    def test_normalize_text_removes_button_prefix(self):
        """Test text normalization removes common prefixes."""
        matcher = SemanticMatcher()
        assert matcher.normalize_text("btn-submit") == "submit"
        assert matcher.normalize_text("button_login") == "login"

    def test_get_canonical_form_known(self):
        """Test getting canonical form for known synonym."""
        matcher = SemanticMatcher()
        assert matcher.get_canonical_form("login") == "sign_in"
        assert matcher.get_canonical_form("log in") == "sign_in"
        assert matcher.get_canonical_form("sign-in") == "sign_in"

    def test_get_canonical_form_unknown(self):
        """Test getting canonical form for unknown term."""
        matcher = SemanticMatcher()
        assert matcher.get_canonical_form("xyzabc") is None

    def test_are_synonyms_true(self):
        """Test synonym detection for related terms."""
        matcher = SemanticMatcher()
        assert matcher.are_synonyms("login", "sign in") is True
        assert matcher.are_synonyms("submit", "send") is True
        assert matcher.are_synonyms("cancel", "close") is True
        assert matcher.are_synonyms("delete", "remove") is True

    def test_are_synonyms_false(self):
        """Test synonym detection for unrelated terms."""
        matcher = SemanticMatcher()
        assert matcher.are_synonyms("login", "logout") is False
        assert matcher.are_synonyms("submit", "cancel") is False

    def test_synonym_similarity_exact_match(self):
        """Test synonym similarity for exact synonyms."""
        matcher = SemanticMatcher()
        assert matcher.synonym_similarity("login", "sign in") == 1.0
        assert matcher.synonym_similarity("submit", "send") == 1.0

    def test_synonym_similarity_no_match(self):
        """Test synonym similarity for unrelated terms."""
        matcher = SemanticMatcher()
        assert matcher.synonym_similarity("hello", "goodbye") == 0.0


class TestRegexPatternMatcher:
    """Tests for RegexPatternMatcher class."""

    def test_extract_pattern_numeric_id(self):
        """Test pattern extraction for numeric IDs."""
        pattern = RegexPatternMatcher.extract_pattern("btn-12345")
        assert pattern is not None
        assert "\\d+" in pattern

    def test_extract_pattern_hex_id(self):
        """Test pattern extraction for hex/UUID IDs."""
        pattern = RegexPatternMatcher.extract_pattern("elem-a1b2c3d4e5f6")
        assert pattern is not None
        assert "[a-f0-9]+" in pattern

    def test_extract_pattern_no_dynamic(self):
        """Test pattern extraction for static IDs."""
        pattern = RegexPatternMatcher.extract_pattern("submit-button")
        assert pattern is None

    def test_matches_pattern_numeric(self):
        """Test pattern matching for numeric patterns."""
        pattern = "btn[-_]?\\d+"
        assert RegexPatternMatcher.matches_pattern(pattern, "btn-123") is True
        assert RegexPatternMatcher.matches_pattern(pattern, "btn456") is True
        assert RegexPatternMatcher.matches_pattern(pattern, "btn-abc") is False

    def test_pattern_similarity_same_pattern(self):
        """Test pattern similarity for same pattern type."""
        sim = RegexPatternMatcher.pattern_similarity("btn-12345", "btn-67890")
        assert sim >= 0.85

    def test_pattern_similarity_no_pattern(self):
        """Test pattern similarity for non-dynamic values."""
        sim = RegexPatternMatcher.pattern_similarity("submit", "cancel")
        assert sim == 0.0


class TestAISelectorHealer:
    """Tests for AISelectorHealer class."""

    def test_init_default(self):
        """Test default initialization."""
        healer = AISelectorHealer()
        assert healer.min_confidence == 0.6
        assert healer.use_llm is False

    def test_init_custom(self):
        """Test custom initialization."""
        healer = AISelectorHealer(min_confidence=0.8, use_llm=True)
        assert healer.min_confidence == 0.8
        assert healer.use_llm is True

    def test_fuzzy_text_match_exact(self):
        """Test fuzzy text match for identical strings."""
        healer = AISelectorHealer()
        score, strategy = healer.fuzzy_text_match("Submit", "submit")
        assert score == 1.0
        assert strategy == "exact"

    def test_fuzzy_text_match_synonym(self):
        """Test fuzzy text match for synonyms."""
        healer = AISelectorHealer()
        score, strategy = healer.fuzzy_text_match("Login", "Sign In")
        assert score >= 0.9
        assert strategy == "synonym"

    def test_fuzzy_text_match_similar(self):
        """Test fuzzy text match for similar strings."""
        healer = AISelectorHealer()
        score, strategy = healer.fuzzy_text_match("Submit Form", "Submit Forms")
        assert score > 0.8
        assert strategy in ["levenshtein", "jaro_winkler", "token_set", "sequence"]

    def test_fuzzy_text_match_empty(self):
        """Test fuzzy text match with empty strings."""
        healer = AISelectorHealer()
        score, strategy = healer.fuzzy_text_match("", "")
        assert score == 0.0
        assert strategy == "empty"

    def test_fuzzy_attribute_match_identical(self):
        """Test fuzzy attribute match for identical fingerprints."""
        healer = AISelectorHealer()
        attrs = {
            "id": "submit-btn",
            "class_list": ["btn", "primary"],
            "text_content": "Submit",
        }
        score, details = healer.fuzzy_attribute_match(attrs, attrs)
        assert score == 1.0
        assert details.get("id") == 1.0
        assert details.get("classes") == 1.0
        assert details.get("text") == 1.0

    def test_fuzzy_attribute_match_similar(self):
        """Test fuzzy attribute match for similar fingerprints."""
        healer = AISelectorHealer()
        attrs1 = {
            "id": "submit-btn-123",
            "class_list": ["btn", "primary"],
            "text_content": "Submit",
        }
        attrs2 = {
            "id": "submit-btn-456",
            "class_list": ["btn", "primary", "active"],
            "text_content": "Submit Form",
        }
        score, details = healer.fuzzy_attribute_match(attrs1, attrs2)
        assert score > 0.7
        assert details.get("id", 0) > 0.8  # Pattern match
        assert details.get("classes", 0) > 0.6
        assert details.get("text", 0) > 0.7

    def test_fuzzy_attribute_match_position(self):
        """Test fuzzy attribute match with position data."""
        healer = AISelectorHealer()
        attrs1 = {
            "text_content": "Button",
            "position": {"x": 100, "y": 200},
        }
        attrs2 = {
            "text_content": "Button",
            "position": {"x": 110, "y": 205},
        }
        score, details = healer.fuzzy_attribute_match(attrs1, attrs2)
        assert details.get("position", 0) > 0.9  # Close position

    def test_fuzzy_attribute_match_far_position(self):
        """Test fuzzy attribute match with distant positions."""
        healer = AISelectorHealer()
        attrs1 = {
            "text_content": "Button",
            "position": {"x": 100, "y": 200},
        }
        attrs2 = {
            "text_content": "Button",
            "position": {"x": 500, "y": 600},
        }
        score, details = healer.fuzzy_attribute_match(attrs1, attrs2)
        assert details.get("position", 1) < 0.5  # Far apart

    @pytest.mark.asyncio
    async def test_find_best_match_success(self):
        """Test finding best match from candidates."""
        healer = AISelectorHealer(min_confidence=0.6)

        original = {
            "selector": "#submit-btn",
            "id": "submit-btn",
            "text_content": "Submit",
            "class_list": ["btn", "primary"],
        }

        candidates = [
            {
                "selector": "#cancel-btn",
                "id": "cancel-btn",
                "text_content": "Cancel",
                "class_list": ["btn", "secondary"],
            },
            {
                "selector": "#submit-btn-new",
                "id": "submit-btn-new",
                "text_content": "Submit Form",
                "class_list": ["btn", "primary"],
            },
        ]

        result = await healer.find_best_match(None, original, candidates)

        assert result.success is True
        assert result.healed_selector == "#submit-btn-new"
        assert result.confidence > 0.7

    @pytest.mark.asyncio
    async def test_find_best_match_no_match(self):
        """Test finding best match with no good candidates."""
        healer = AISelectorHealer(min_confidence=0.8)

        original = {
            "selector": "#submit-btn",
            "id": "submit-btn",
            "text_content": "Submit",
        }

        candidates = [
            {
                "selector": "#header-logo",
                "id": "header-logo",
                "text_content": "Logo",
            },
        ]

        result = await healer.find_best_match(None, original, candidates)

        assert result.success is False
        assert result.confidence < 0.8

    @pytest.mark.asyncio
    async def test_enhance_similarity_score_synonym(self):
        """Test enhancing score with synonym matching."""
        healer = AISelectorHealer()

        enhanced = await healer.enhance_similarity_score("Login", "Sign In", 0.5)
        assert enhanced >= 0.9  # Should detect synonym

    @pytest.mark.asyncio
    async def test_enhance_similarity_score_already_high(self):
        """Test that high scores are not modified."""
        healer = AISelectorHealer()

        enhanced = await healer.enhance_similarity_score("Submit", "Submit", 0.95)
        assert enhanced == 0.95  # No change needed


class TestUISymonyms:
    """Tests for UI_SYNONYMS dictionary."""

    def test_common_synonyms_present(self):
        """Test that common synonym groups are defined."""
        assert "sign_in" in UI_SYNONYMS
        assert "sign_out" in UI_SYNONYMS
        assert "submit" in UI_SYNONYMS
        assert "cancel" in UI_SYNONYMS
        assert "search" in UI_SYNONYMS

    def test_synonym_groups_not_empty(self):
        """Test that synonym groups have multiple entries."""
        for key, synonyms in UI_SYNONYMS.items():
            assert len(synonyms) >= 2, f"{key} should have at least 2 synonyms"

    def test_login_synonyms(self):
        """Test login/sign-in synonyms."""
        login_syns = UI_SYNONYMS["sign_in"]
        assert "login" in login_syns
        assert "log in" in login_syns
        assert "sign in" in login_syns


class TestAIHealingResult:
    """Tests for AIHealingResult dataclass."""

    def test_create_success_result(self):
        """Test creating a successful healing result."""
        result = AIHealingResult(
            success=True,
            original_selector="#old-btn",
            healed_selector="#new-btn",
            confidence=0.92,
            strategy_used="fuzzy_text",
            match_details={"text": 0.95, "id": 0.88},
            alternatives=[("#alt-btn", 0.85)],
        )
        assert result.success is True
        assert result.confidence == 0.92
        assert result.llm_used is False

    def test_create_failure_result(self):
        """Test creating a failed healing result."""
        result = AIHealingResult(
            success=False,
            original_selector="#missing-btn",
            healed_selector="",
            confidence=0.3,
            strategy_used="none",
        )
        assert result.success is False
        assert result.healed_selector == ""


class TestHealingStrategy:
    """Tests for HealingStrategy enum."""

    def test_strategy_values(self):
        """Test that all strategies have correct values."""
        assert HealingStrategy.FUZZY_TEXT.value == "fuzzy_text"
        assert HealingStrategy.FUZZY_ATTRIBUTE.value == "fuzzy_attribute"
        assert HealingStrategy.SEMANTIC.value == "semantic"
        assert HealingStrategy.STRUCTURAL.value == "structural"
        assert HealingStrategy.REGEX_PATTERN.value == "regex_pattern"
        assert HealingStrategy.SYNONYM.value == "synonym"
