"""
Test Gemini AI Studio OAuth direct API call.

This test verifies that the Gemini AI Studio API can be called directly
with OAuth tokens, bypassing LiteLLM for proper OAuth handling.
"""

from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_llm_resource_manager_gemini_oauth():
    """Test LLMResourceManager with Gemini OAuth credential."""
    from casare_rpa.infrastructure.resources.llm_resource_manager import (
        LLMConfig,
        LLMProvider,
        LLMResourceManager,
    )

    # Mock the direct API call function
    async def mock_call_gemini(*args, **kwargs):
        return {
            "candidates": [
                {
                    "content": {"parts": [{"text": "Test response from Gemini"}]},
                    "finishReason": "STOP",
                }
            ],
            "usageMetadata": {
                "promptTokenCount": 5,
                "candidatesTokenCount": 10,
                "totalTokenCount": 15,
            },
        }

    with patch(
        "casare_rpa.infrastructure.resources.llm_resource_manager.call_gemini_api_directly",
        side_effect=mock_call_gemini,
    ):
        # Mock the credential store to return OAuth credential info
        mock_credential_info = {
            "id": "test_gemini_cred",
            "name": "Test Gemini OAuth",
            "type": "google_oauth",
            "category": "google",
            "tags": ["ai_studio", "oauth"],
        }

        mock_store = MagicMock()
        mock_store.get_credential_info = MagicMock(return_value=mock_credential_info)

        with patch(
            "casare_rpa.infrastructure.security.credential_store.get_credential_store",
            return_value=mock_store,
        ):
            # Mock the Gemini OAuth manager to return a fake token
            async def mock_get_token(cred_id):
                return "fake_oauth_token_12345"

            with patch(
                "casare_rpa.infrastructure.security.gemini_oauth.get_gemini_access_token",
                side_effect=mock_get_token,
            ):
                manager = LLMResourceManager()

                # Configure with Gemini AI Studio OAuth credential
                config = LLMConfig(
                    provider=LLMProvider.CUSTOM,
                    model="models/gemini-2.0-flash-exp",
                    credential_id="test_gemini_cred",
                )
                manager.configure(config)

                # The _resolve_api_key should set _using_gemini_studio_oauth
                api_key = await manager._resolve_api_key()
                assert api_key == "fake_oauth_token_12345"
                assert manager._using_gemini_studio_oauth is True

                # Test completion
                response = await manager.completion(
                    prompt="Test prompt",
                    temperature=0.7,
                    max_tokens=1000,
                )

                assert response.content == "Test response from Gemini"
                assert response.total_tokens == 15


@pytest.mark.asyncio
async def test_gemini_model_name_formatting():
    """Test that model names are properly formatted for the Gemini API."""
    from casare_rpa.infrastructure.resources.llm_resource_manager import LLMResourceManager

    # Test model string formatting logic
    test_cases = [
        # (input_model, is_gemini_studio, expected_output)
        ("models/gemini-2.0-flash-exp", True, "gemini/gemini-2.0-flash-exp"),
        ("gemini/gemini-2.0-flash-exp", True, "gemini/gemini-2.0-flash-exp"),
        ("gemini-2.0-flash-exp", True, "gemini/gemini-2.0-flash-exp"),
        ("models/gemini-2.0-flash-exp", False, "vertex_ai/gemini-2.0-flash-exp"),
    ]

    for input_model, is_gemini_studio, expected in test_cases:
        manager = LLMResourceManager()

        # Set the internal flag
        if is_gemini_studio:
            manager._using_gemini_studio_oauth = True
        else:
            manager._using_google_oauth = True

        result = manager._get_model_string(input_model)
        assert result == expected, (
            f"Expected {expected}, got {result} for is_gemini_studio={is_gemini_studio}"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
