"""Tests for AI Prompts."""

import pytest
from casare_rpa.domain.ai.prompts import (
    PromptBuilder,
    GENIUS_SYSTEM_PROMPT,
    CASARE_RPA_SPECIFIC_RULES,
)


class TestPromptBuilder:
    def test_build_system_prompt_structure(self):
        """Test that system prompt includes all required sections."""
        builder = PromptBuilder()
        prompt = builder.build_system_prompt(node_manifest="[]")

        # Core sections
        assert GENIUS_SYSTEM_PROMPT in prompt
        assert "Atomic Workflow Design" in prompt
        assert "Available Nodes" in prompt
        assert "Variable Syntax Rules" in prompt

        # New strict rules section
        assert "CRITICAL: CASARE RPA STRICT RULES" in prompt
        assert "JSON Script Escaping" in prompt
        assert "Retry Logic" in prompt

    def test_casare_rules_content(self):
        """Verify the content of the Casare rules."""
        assert "Use `WhileLoopStartNode`" in CASARE_RPA_SPECIFIC_RULES
        assert (
            "NEVER put actual newlines in the JSON string" in CASARE_RPA_SPECIFIC_RULES
        )
        assert "Visual Node Imports" in CASARE_RPA_SPECIFIC_RULES

    def test_build_generation_prompt(self):
        """Test complete generation prompt assembly."""
        builder = PromptBuilder()
        user_request = "Login to google"
        prompt = builder.build_generation_prompt(user_request, "[]")

        assert user_request in prompt
        assert "Output ONLY the JSON object" in prompt
