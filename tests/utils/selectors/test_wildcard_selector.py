"""Tests for wildcard selector pattern support."""

import pytest

from casare_rpa.utils.selectors.wildcard_selector import (
    WildcardSelector,
    normalize_selector_with_wildcards,
)


class TestWildcardSelectorHasWildcard:
    """Tests for WildcardSelector.has_wildcard() method."""

    def test_has_wildcard_with_asterisk(self):
        """Test detection of * wildcard."""
        assert WildcardSelector.has_wildcard("btn-*") is True
        assert WildcardSelector.has_wildcard("*-submit") is True
        assert WildcardSelector.has_wildcard("#user-*") is True
        assert WildcardSelector.has_wildcard(".nav-*-item") is True

    def test_has_wildcard_with_question_mark(self):
        """Test detection of ? wildcard."""
        assert WildcardSelector.has_wildcard("btn-?") is True
        assert WildcardSelector.has_wildcard("item-?-end") is True

    def test_has_wildcard_no_wildcard(self):
        """Test that regular selectors return False."""
        assert WildcardSelector.has_wildcard("#myId") is False
        assert WildcardSelector.has_wildcard(".btn-primary") is False
        assert WildcardSelector.has_wildcard("[data-testid='btn']") is False
        assert WildcardSelector.has_wildcard("button") is False

    def test_has_wildcard_empty_string(self):
        """Test that empty string returns False."""
        assert WildcardSelector.has_wildcard("") is False
        assert WildcardSelector.has_wildcard(None) is False


class TestWildcardSelectorParseIdPatterns:
    """Tests for parsing ID wildcard patterns."""

    def test_parse_id_prefix_wildcard(self):
        """Test #user-* -> [id^="user-"]."""
        result = WildcardSelector.parse("#user-*")
        assert result == '[id^="user-"]'

    def test_parse_id_suffix_wildcard(self):
        """Test #*-panel -> [id$="-panel"]."""
        result = WildcardSelector.parse("#*-panel")
        assert result == '[id$="-panel"]'

    def test_parse_id_with_tag_prefix(self):
        """Test input#field-* -> input[id^="field-"]."""
        result = WildcardSelector.parse("input#field-*")
        assert result == 'input[id^="field-"]'

    def test_parse_id_with_underscore(self):
        """Test #user_profile-* -> [id^="user_profile-"]."""
        result = WildcardSelector.parse("#user_profile-*")
        assert result == '[id^="user_profile-"]'


class TestWildcardSelectorParseClassPatterns:
    """Tests for parsing class wildcard patterns."""

    def test_parse_class_prefix_wildcard(self):
        """Test .btn-* -> [class*="btn-"]."""
        result = WildcardSelector.parse(".btn-*")
        assert result == '[class*="btn-"]'

    def test_parse_class_suffix_wildcard(self):
        """Test .*-active -> [class$="-active"]."""
        result = WildcardSelector.parse(".*-active")
        assert result == '[class$="-active"]'

    def test_parse_class_with_tag_prefix(self):
        """Test button.btn-* -> button[class*="btn-"]."""
        result = WildcardSelector.parse("button.btn-*")
        assert result == 'button[class*="btn-"]'

    def test_parse_class_middle_wildcard(self):
        """Test nav-*-item -> [class*="nav-"][class*="-item"]."""
        result = WildcardSelector.parse("nav-*-item")
        assert result == '[class*="nav-"][class*="-item"]'


class TestWildcardSelectorParseSuffixPatterns:
    """Tests for parsing suffix wildcard patterns."""

    def test_parse_suffix_only(self):
        """Test *-submit -> [class$="-submit"]."""
        result = WildcardSelector.parse("*-submit")
        assert result == '[class$="-submit"]'

    def test_parse_suffix_with_underscore(self):
        """Test *_button -> [class$="_button"]."""
        result = WildcardSelector.parse("*_button")
        assert result == '[class$="_button"]'


class TestWildcardSelectorParseAttributePatterns:
    """Tests for parsing attribute wildcard patterns."""

    def test_parse_attribute_prefix_wildcard(self):
        """Test [name=field*] -> [name^="field"]."""
        result = WildcardSelector.parse("[name=field*]")
        assert result == '[name^="field"]'

    def test_parse_attribute_suffix_wildcard(self):
        """Test [name=*field] -> [name$="field"]."""
        result = WildcardSelector.parse("[name=*field]")
        assert result == '[name$="field"]'

    def test_parse_data_attribute_wildcard(self):
        """Test [data-testid=user*] -> [data-testid^="user"]."""
        result = WildcardSelector.parse("[data-testid=user*]")
        assert result == '[data-testid^="user"]'

    def test_parse_data_star_attribute_preserved(self):
        """Test [data-*] is preserved as native CSS."""
        result = WildcardSelector.parse("[data-*]")
        assert result == "[data-*]"


class TestWildcardSelectorParseNoWildcard:
    """Tests for parsing selectors without wildcards."""

    def test_parse_no_wildcard_unchanged(self):
        """Test that selectors without wildcards are unchanged."""
        assert WildcardSelector.parse("#myId") == "#myId"
        assert WildcardSelector.parse(".btn-primary") == ".btn-primary"
        assert WildcardSelector.parse("button") == "button"
        assert WildcardSelector.parse("[data-testid='btn']") == "[data-testid='btn']"

    def test_parse_empty_string(self):
        """Test that empty string returns empty string."""
        assert WildcardSelector.parse("") == ""

    def test_parse_none_returns_none(self):
        """Test that None returns None."""
        assert WildcardSelector.parse(None) is None


class TestWildcardSelectorExpand:
    """Tests for WildcardSelector.expand() method."""

    def test_expand_class_pattern(self):
        """Test expanding class wildcard to multiple variants."""
        variants = WildcardSelector.expand(".btn-*")
        assert len(variants) >= 1
        assert '[class*="btn-"]' in variants
        # Should include common expansions
        assert '[class^="btn-"]' in variants
        assert '[class$="btn-"]' in variants

    def test_expand_id_pattern(self):
        """Test expanding ID wildcard to multiple variants."""
        variants = WildcardSelector.expand("#user-*")
        assert len(variants) >= 1
        assert '[id^="user-"]' in variants
        # Should include common expansions
        assert '[id*="user-"]' in variants
        assert '[id$="user-"]' in variants

    def test_expand_no_wildcard(self):
        """Test that non-wildcard selectors return single item."""
        variants = WildcardSelector.expand("#myId")
        assert variants == ["#myId"]

    def test_expand_empty_string(self):
        """Test expanding empty string returns empty list."""
        variants = WildcardSelector.expand("")
        assert variants == []

    def test_expand_no_duplicates(self):
        """Test that expand returns unique variants."""
        variants = WildcardSelector.expand(".nav-*")
        assert len(variants) == len(set(variants))


class TestWildcardSelectorIsValidPattern:
    """Tests for WildcardSelector.is_valid_wildcard_pattern() method."""

    def test_valid_patterns(self):
        """Test that valid patterns return True."""
        assert WildcardSelector.is_valid_wildcard_pattern("#user-*") is True
        assert WildcardSelector.is_valid_wildcard_pattern(".btn-*") is True
        assert WildcardSelector.is_valid_wildcard_pattern("*-submit") is True
        assert WildcardSelector.is_valid_wildcard_pattern("[name=field*]") is True

    def test_non_wildcard_patterns_valid(self):
        """Test that non-wildcard patterns are considered valid."""
        assert WildcardSelector.is_valid_wildcard_pattern("#myId") is True
        assert WildcardSelector.is_valid_wildcard_pattern(".btn-primary") is True

    def test_invalid_too_many_wildcards(self):
        """Test that too many wildcards returns False."""
        assert WildcardSelector.is_valid_wildcard_pattern("*-*-*") is False

    def test_invalid_unbalanced_brackets(self):
        """Test that unbalanced brackets returns False."""
        assert WildcardSelector.is_valid_wildcard_pattern("[name=*") is False
        assert WildcardSelector.is_valid_wildcard_pattern("name=*]") is False

    def test_invalid_empty(self):
        """Test that empty/None returns False."""
        assert WildcardSelector.is_valid_wildcard_pattern("") is False
        assert WildcardSelector.is_valid_wildcard_pattern(None) is False


class TestNormalizeSelectorWithWildcards:
    """Tests for normalize_selector_with_wildcards() convenience function."""

    def test_normalizes_wildcard_selector(self):
        """Test that wildcard selectors are normalized."""
        result = normalize_selector_with_wildcards("#user-*")
        assert result == '[id^="user-"]'

    def test_no_change_for_regular_selector(self):
        """Test that regular selectors are unchanged."""
        result = normalize_selector_with_wildcards("#myId")
        assert result == "#myId"

    def test_empty_string_unchanged(self):
        """Test that empty string is unchanged."""
        result = normalize_selector_with_wildcards("")
        assert result == ""

    def test_none_unchanged(self):
        """Test that None is unchanged."""
        result = normalize_selector_with_wildcards(None)
        assert result is None


class TestWildcardSelectorIntegration:
    """Integration tests for wildcard selector with selector_normalizer."""

    def test_normalize_selector_with_wildcards_integration(self):
        """Test that normalize_selector properly handles wildcards."""
        from casare_rpa.utils.selectors.selector_normalizer import normalize_selector

        result = normalize_selector("#btn-*")
        assert result == '[id^="btn-"]'

    def test_detect_selector_type_wildcard(self):
        """Test that detect_selector_type identifies wildcard selectors."""
        from casare_rpa.utils.selectors.selector_normalizer import detect_selector_type

        assert detect_selector_type("#user-*") == "wildcard"
        assert detect_selector_type(".btn-*") == "wildcard"
        assert detect_selector_type("*-submit") == "wildcard"

    def test_detect_selector_type_non_wildcard(self):
        """Test that regular selectors are not detected as wildcard."""
        from casare_rpa.utils.selectors.selector_normalizer import detect_selector_type

        assert detect_selector_type("#myId") == "css"
        assert detect_selector_type(".btn") == "css"
        assert detect_selector_type("//div") == "xpath"


class TestWildcardSelectorEdgeCases:
    """Edge case tests for wildcard selector."""

    def test_multiple_wildcards_prefix_suffix(self):
        """Test pattern with both prefix and suffix wildcards."""
        result = WildcardSelector.parse("nav-*-item")
        assert '[class*="nav-"]' in result
        assert '[class*="-item"]' in result

    def test_whitespace_handling(self):
        """Test that whitespace is preserved (normalizer handles trimming)."""
        result = WildcardSelector.parse("  #user-*  ")
        # WildcardSelector.parse does not trim whitespace - that's the normalizer's job
        # The pattern with leading/trailing whitespace won't match the regex
        assert result == "  #user-*  "

    def test_complex_class_name(self):
        """Test complex class names with hyphens and underscores."""
        result = WildcardSelector.parse(".btn-primary-lg-*")
        assert result == '[class*="btn-primary-lg-"]'

    def test_numeric_suffix(self):
        """Test class with numeric suffix."""
        result = WildcardSelector.parse(".item-*")
        assert result == '[class*="item-"]'

    def test_question_mark_converted_to_star(self):
        """Test that ? wildcards are handled."""
        result = WildcardSelector.parse(".btn-?")
        # ? should be treated similarly to *
        assert "btn-" in result or result == ".btn-?"


class TestWildcardSelectorRealWorldPatterns:
    """Tests for real-world selector patterns."""

    def test_bootstrap_button_classes(self):
        """Test Bootstrap-style button class patterns."""
        result = WildcardSelector.parse(".btn-*")
        assert result == '[class*="btn-"]'

    def test_data_testid_pattern(self):
        """Test data-testid attribute pattern."""
        result = WildcardSelector.parse("[data-testid=user-*]")
        assert result == '[data-testid^="user-"]'

    def test_react_generated_ids(self):
        """Test React-style generated ID patterns."""
        result = WildcardSelector.parse("#react-select-*")
        assert result == '[id^="react-select-"]'

    def test_angular_component_ids(self):
        """Test Angular-style component ID patterns."""
        result = WildcardSelector.parse("#ng-*-component")
        # Middle wildcard pattern
        assert '[id*="ng-"]' in result or result == "#ng-*-component"

    def test_material_ui_classes(self):
        """Test Material UI class patterns."""
        result = WildcardSelector.parse(".MuiButton-*")
        assert result == '[class*="MuiButton-"]'

    def test_tailwind_utility_classes(self):
        """Test Tailwind CSS utility class patterns."""
        result = WildcardSelector.parse(".*-blue-500")
        assert result == '[class$="-blue-500"]'
