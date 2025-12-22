"""Tests for AI Prompts."""

import pytest
from casare_rpa.domain.ai.prompts import (
    PromptBuilder,
    GENIUS_SYSTEM_PROMPT,
    ROBUSTNESS_INSTRUCTIONS,
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
        assert "Variable Syntax" in prompt

    def test_robustness_instructions_content(self):
        """Verify the content of the robustness instructions."""
        assert "ERROR HANDLING" in ROBUSTNESS_INSTRUCTIONS
        assert "TryCatchNode" in ROBUSTNESS_INSTRUCTIONS
        assert "DEBUG POINTS" in ROBUSTNESS_INSTRUCTIONS

    def test_build_generation_prompt(self):
        """Test complete generation prompt assembly."""
        builder = PromptBuilder()
        user_request = "Login to google"
        prompt = builder.build_generation_prompt(user_request, "[]")

        assert user_request in prompt
        assert "JSON" in prompt  # Should mention JSON output format
