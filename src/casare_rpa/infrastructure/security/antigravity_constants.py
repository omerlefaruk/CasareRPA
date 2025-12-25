"""
Constants for Antigravity OAuth and Cloud Code Assist API integration.

Antigravity is Google's AI IDE platform. This module provides the OAuth credentials,
API endpoints, and headers needed to authenticate and communicate with Antigravity's
API, which provides access to models like Gemini 3 Pro and Claude 4.5.

Based on: https://github.com/NoeFabris/opencode-antigravity-auth
"""

from __future__ import annotations

from enum import Enum
from typing import Final

# =============================================================================
# OAuth Credentials
# =============================================================================

# Antigravity OAuth client credentials (publicly available from Antigravity IDE)
ANTIGRAVITY_CLIENT_ID: Final[str] = (
    "1071006060591-tmhssin2h21lcre235vtolojh4g403ep.apps.googleusercontent.com"
)
ANTIGRAVITY_CLIENT_SECRET: Final[str] = "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"

# OAuth redirect URI for local callback server
ANTIGRAVITY_REDIRECT_URI: Final[str] = "http://localhost:51121/oauth-callback"

# Provider identifier
ANTIGRAVITY_PROVIDER_ID: Final[str] = "antigravity"

# =============================================================================
# OAuth Scopes
# =============================================================================

ANTIGRAVITY_SCOPES: Final[tuple[str, ...]] = (
    "https://www.googleapis.com/auth/cloud-platform",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/cclog",
    "https://www.googleapis.com/auth/experimentsandconfigs",
)

# =============================================================================
# API Endpoints
# =============================================================================

# Root endpoints for the Antigravity API (in fallback order)
ANTIGRAVITY_ENDPOINT_DAILY: Final[str] = "https://daily-cloudcode-pa.sandbox.googleapis.com"
ANTIGRAVITY_ENDPOINT_AUTOPUSH: Final[str] = "https://autopush-cloudcode-pa.sandbox.googleapis.com"
ANTIGRAVITY_ENDPOINT_PROD: Final[str] = "https://cloudcode-pa.googleapis.com"

# Endpoint fallback order (daily -> autopush -> prod)
ANTIGRAVITY_ENDPOINT_FALLBACKS: Final[tuple[str, ...]] = (
    ANTIGRAVITY_ENDPOINT_DAILY,
    ANTIGRAVITY_ENDPOINT_AUTOPUSH,
    ANTIGRAVITY_ENDPOINT_PROD,
)

# Preferred endpoint order for project discovery (prod first)
ANTIGRAVITY_LOAD_ENDPOINTS: Final[tuple[str, ...]] = (
    ANTIGRAVITY_ENDPOINT_PROD,
    ANTIGRAVITY_ENDPOINT_DAILY,
    ANTIGRAVITY_ENDPOINT_AUTOPUSH,
)

# Primary endpoint to use (daily sandbox - same as CLIProxy/Vibeproxy)
ANTIGRAVITY_ENDPOINT: Final[str] = ANTIGRAVITY_ENDPOINT_DAILY

# Hardcoded project ID used when Antigravity does not return one
ANTIGRAVITY_DEFAULT_PROJECT_ID: Final[str] = "rising-fact-p41fc"

# =============================================================================
# HTTP Headers
# =============================================================================


class HeaderStyle(str, Enum):
    """Header style for Antigravity API requests."""

    ANTIGRAVITY = "antigravity"
    GEMINI_CLI = "gemini-cli"


# Antigravity-style headers (matches Antigravity IDE)
ANTIGRAVITY_HEADERS: Final[dict[str, str]] = {
    "User-Agent": "antigravity/1.11.5 windows/amd64",
    "X-Goog-Api-Client": "google-cloud-sdk vscode_cloudshelleditor/0.1",
    "Client-Metadata": '{"ideType":"IDE_UNSPECIFIED","platform":"PLATFORM_UNSPECIFIED","pluginType":"GEMINI"}',
}

# Gemini CLI-style headers (alternative quota pool)
GEMINI_CLI_HEADERS: Final[dict[str, str]] = {
    "User-Agent": "google-api-nodejs-client/9.15.1",
    "X-Goog-Api-Client": "gl-node/22.17.0",
    "Client-Metadata": "ideType=IDE_UNSPECIFIED,platform=PLATFORM_UNSPECIFIED,pluginType=GEMINI",
}

# =============================================================================
# Model Definitions
# =============================================================================


class AntigravityModel(str, Enum):
    """Available models through Antigravity API."""

    # Gemini models
    GEMINI_3_PRO_HIGH = "gemini-3-pro-high"
    GEMINI_3_PRO_LOW = "gemini-3-pro-low"
    GEMINI_3_FLASH = "gemini-3-flash"

    # Claude models (via Antigravity)
    CLAUDE_SONNET_4_5 = "claude-sonnet-4-5"
    CLAUDE_SONNET_4_5_THINKING = "claude-sonnet-4-5-thinking"
    CLAUDE_OPUS_4_5_THINKING = "claude-opus-4-5-thinking"

    # OpenAI models (via Antigravity)
    GPT_OSS_120B_MEDIUM = "gpt-oss-120b-medium"


class ModelFamily(str, Enum):
    """Model family for rate limit tracking."""

    CLAUDE = "claude"
    GEMINI = "gemini"


# Model configurations with context/output limits
ANTIGRAVITY_MODEL_CONFIGS: Final[dict[str, dict]] = {
    AntigravityModel.GEMINI_3_PRO_HIGH.value: {
        "name": "Gemini 3 Pro High (Antigravity)",
        "family": ModelFamily.GEMINI,
        "context_limit": 1048576,
        "output_limit": 65535,
    },
    AntigravityModel.GEMINI_3_PRO_LOW.value: {
        "name": "Gemini 3 Pro Low (Antigravity)",
        "family": ModelFamily.GEMINI,
        "context_limit": 1048576,
        "output_limit": 65535,
    },
    AntigravityModel.GEMINI_3_FLASH.value: {
        "name": "Gemini 3 Flash (Antigravity)",
        "family": ModelFamily.GEMINI,
        "context_limit": 1048576,
        "output_limit": 65536,
    },
    AntigravityModel.CLAUDE_SONNET_4_5.value: {
        "name": "Claude Sonnet 4.5 (Antigravity)",
        "family": ModelFamily.CLAUDE,
        "context_limit": 200000,
        "output_limit": 64000,
    },
    AntigravityModel.CLAUDE_SONNET_4_5_THINKING.value: {
        "name": "Claude Sonnet 4.5 Thinking (Antigravity)",
        "family": ModelFamily.CLAUDE,
        "context_limit": 200000,
        "output_limit": 64000,
        "thinking_capable": True,
    },
    AntigravityModel.CLAUDE_OPUS_4_5_THINKING.value: {
        "name": "Claude Opus 4.5 Thinking (Antigravity)",
        "family": ModelFamily.CLAUDE,
        "context_limit": 200000,
        "output_limit": 64000,
        "thinking_capable": True,
    },
    AntigravityModel.GPT_OSS_120B_MEDIUM.value: {
        "name": "GPT-OSS 120B Medium (Antigravity)",
        "family": ModelFamily.GEMINI,  # Uses Gemini quota
        "context_limit": 131072,
        "output_limit": 32768,
    },
}

# =============================================================================
# Rate Limiting
# =============================================================================


class QuotaKey(str, Enum):
    """Quota keys for rate limit tracking."""

    CLAUDE = "claude"
    GEMINI_ANTIGRAVITY = "gemini-antigravity"
    GEMINI_CLI = "gemini-cli"


# Default thinking budget for Claude thinking models
DEFAULT_THINKING_BUDGET: Final[int] = 10000

# Claude thinking models need sufficient max output tokens
CLAUDE_THINKING_MAX_OUTPUT_TOKENS: Final[int] = 64000

# =============================================================================
# Utility Functions
# =============================================================================


def get_model_family(model: str) -> ModelFamily:
    """Get the model family for a given model ID."""
    model_lower = model.lower()
    if "claude" in model_lower:
        return ModelFamily.CLAUDE
    return ModelFamily.GEMINI


def is_thinking_capable_model(model: str) -> bool:
    """Check if a model supports thinking/reasoning blocks."""
    model_lower = model.lower()
    return "thinking" in model_lower or "claude" in model_lower


def is_claude_model(model: str) -> bool:
    """Check if a model is a Claude model."""
    return "claude" in model.lower()


def get_quota_key(family: ModelFamily, header_style: HeaderStyle) -> QuotaKey:
    """Get the quota key for a model family and header style."""
    if family == ModelFamily.CLAUDE:
        return QuotaKey.CLAUDE
    return (
        QuotaKey.GEMINI_CLI
        if header_style == HeaderStyle.GEMINI_CLI
        else QuotaKey.GEMINI_ANTIGRAVITY
    )


def get_headers_for_style(style: HeaderStyle) -> dict[str, str]:
    """Get the appropriate headers for a header style."""
    if style == HeaderStyle.GEMINI_CLI:
        return dict(GEMINI_CLI_HEADERS)
    return dict(ANTIGRAVITY_HEADERS)


__all__ = [
    # OAuth
    "ANTIGRAVITY_CLIENT_ID",
    "ANTIGRAVITY_CLIENT_SECRET",
    "ANTIGRAVITY_REDIRECT_URI",
    "ANTIGRAVITY_PROVIDER_ID",
    "ANTIGRAVITY_SCOPES",
    # Endpoints
    "ANTIGRAVITY_ENDPOINT",
    "ANTIGRAVITY_ENDPOINT_DAILY",
    "ANTIGRAVITY_ENDPOINT_AUTOPUSH",
    "ANTIGRAVITY_ENDPOINT_PROD",
    "ANTIGRAVITY_ENDPOINT_FALLBACKS",
    "ANTIGRAVITY_LOAD_ENDPOINTS",
    "ANTIGRAVITY_DEFAULT_PROJECT_ID",
    # Headers
    "HeaderStyle",
    "ANTIGRAVITY_HEADERS",
    "GEMINI_CLI_HEADERS",
    "get_headers_for_style",
    # Models
    "AntigravityModel",
    "ModelFamily",
    "ANTIGRAVITY_MODEL_CONFIGS",
    "get_model_family",
    "is_thinking_capable_model",
    "is_claude_model",
    # Rate Limiting
    "QuotaKey",
    "get_quota_key",
    "DEFAULT_THINKING_BUDGET",
    "CLAUDE_THINKING_MAX_OUTPUT_TOKENS",
]
