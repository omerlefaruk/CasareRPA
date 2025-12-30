"""
Gemini Subscription Manager - Routes Gemini models to optimal quota pools.

Manages Google OAuth credentials for Gemini models through:
- Google AI Studio (gemini/ prefix) - free tier quota
- Vertex AI (vertex_ai/ prefix) - subscription quota with cloud-platform scope
- Antigravity API - alternative quota pool (gemini-antigravity, gemini-cli)

The system automatically selects the best route based on:
1. Available credentials (Google OAuth vs Antigravity OAuth)
2. Model name format (models/, gemini/, vertex_ai/)
3. Quota pool availability
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from typing import Any


class GeminiRoute(str, Enum):
    """Gemini API routing options."""

    GOOGLE_AI_STUDIO = "google_ai_studio"  # gemini/ prefix, generative-language scope
    VERTEX_AI = "vertex_ai"  # vertex_ai/ prefix, cloud-platform scope
    OPENROUTER = "openrouter"  # OpenRouter fallback





@dataclass
class GeminiRouteConfig:
    """Configuration for a Gemini model route."""

    route: GeminiRoute
    model_prefix: str
    required_scope: str | None = None
    requires_project_id: bool = False


# Gemini model routing table
_GEMINI_ROUTES: dict[str, GeminiRouteConfig] = {
    # Google AI Studio format (models/gemini-*, gemini/*)
    "models/": GeminiRouteConfig(
        route=GeminiRoute.GOOGLE_AI_STUDIO,
        model_prefix="gemini/",
        required_scope="https://www.googleapis.com/auth/generative-language",
    ),
    "gemini/": GeminiRouteConfig(
        route=GeminiRoute.GOOGLE_AI_STUDIO,
        model_prefix="gemini/",
        required_scope="https://www.googleapis.com/auth/generative-language",
    ),
    # Vertex AI format (vertex_ai/*)
    "vertex_ai/": GeminiRouteConfig(
        route=GeminiRoute.VERTEX_AI,
        model_prefix="vertex_ai/",
        required_scope="https://www.googleapis.com/auth/cloud-platform",
        requires_project_id=True,
    ),
}


def detect_gemini_route(model: str, has_oauth: bool, has_antigravity: bool) -> GeminiRouteConfig:
    """
    Detect the optimal route for a Gemini model.

    Priority order:
    1. Vertex AI (with Google OAuth + cloud-platform scope) - subscription quota
    2. Google AI Studio (with Google OAuth + generative-language scope)
    3. OpenRouter (fallback with API key)

    Args:
        model: Model name/identifier.
        has_oauth: Whether Google OAuth credentials are available.

    Returns:
        GeminiRouteConfig with routing information.
    """
    model_lower = model.lower()

    # Check for explicit prefix
    for prefix, config in _GEMINI_ROUTES.items():
        if model_lower.startswith(prefix):
            # Verify we have the required credentials
            if config.route == GeminiRoute.VERTEX_AI and has_oauth:
                return config
            elif config.route == GeminiRoute.GOOGLE_AI_STUDIO and has_oauth:
                return config

    # No explicit prefix - auto-detect based on available credentials
    if has_oauth:
        # Prefer Vertex AI for subscription quota (cloud-platform scope)
        # Falls back to gemini/ prefix if no cloud-platform scope
        return GeminiRouteConfig(
            route=GeminiRoute.VERTEX_AI,
            model_prefix="vertex_ai/",
            required_scope="https://www.googleapis.com/auth/cloud-platform",
            requires_project_id=True,
        )



    # Fallback to OpenRouter
    return GeminiRouteConfig(
        route=GeminiRoute.OPENROUTER,
        model_prefix="openrouter/google/",
    )


def get_vertex_project_id(config_project: str | None = None) -> str:
    """
    Get the Google Cloud project ID for Vertex AI.

    Priority order:
    1. Provided config_project
    2. GOOGLE_CLOUD_PROJECT env var
    3. VERTEXAI_PROJECT env var
    4. DEFAULT_VERTEXAI_PROJECT env var
    5. Default CasareRPA project

    Args:
        config_project: Project ID from configuration.

    Returns:
        Google Cloud project ID.
    """
    return (
        config_project
        or os.environ.get("GOOGLE_CLOUD_PROJECT")
        or os.environ.get("VERTEXAI_PROJECT")
        or os.environ.get("DEFAULT_VERTEXAI_PROJECT")
        or "casare-481714"  # Default CasareRPA project
    )


def get_vertex_location(config_location: str | None = None) -> str:
    """
    Get the Vertex AI location.

    Args:
        config_location: Location from configuration.

    Returns:
        Vertex AI location (default: europe-west1).
    """
    return (
        config_location
        or os.environ.get("VERTEXAI_LOCATION")
        or os.environ.get("DEFAULT_VERTEXAI_LOCATION")
        or "europe-west1"
    )


def normalize_gemini_model_name(
    model: str,
    has_oauth: bool = False,
    using_vertex_ai: bool = False,
) -> str:
    """
    Normalize a Gemini model name for LiteLLM.

    Converts various Gemini model formats to the correct LiteLLM format
    based on available authentication method.

    Args:
        model: Input model name (e.g., "gemini-2.0-flash", "models/gemini-pro").
        has_oauth: Whether Google OAuth credentials are available.
        using_vertex_ai: Whether to force Vertex AI format.

    Returns:
        Normalized model name for LiteLLM.
    """
    model_lower = model.lower()

    # If already properly formatted, return as-is
    if model_lower.startswith(("vertex_ai/", "gemini/", "openrouter/", "ollama/")):
        return model

    # Strip models/ prefix
    if model_lower.startswith("models/"):
        model_name = model[7:]  # Remove "models/"
    else:
        model_name = model

    # Detect route
    route_config = detect_gemini_route(model_name, has_oauth, False)

    match route_config.route:
        case GeminiRoute.VERTEX_AI | GeminiRoute.GOOGLE_AI_STUDIO:
            prefix = (
                "vertex_ai/"
                if using_vertex_ai or route_config.route == GeminiRoute.VERTEX_AI
                else "gemini/"
            )
            return f"{prefix}{model_name}"

        case GeminiRoute.OPENROUTER:
            return f"openrouter/google/{model_name}"
        case _:
            return model_name


def is_gemini_model(model: str) -> bool:
    """
    Check if a model is a Gemini model.

    Args:
        model: Model name to check.

    Returns:
        True if the model is a Gemini model.
    """
    model_lower = model.lower()
    gemini_keywords = [
        "gemini",
        "models/gemini",
        "vertex_ai/gemini",
        "google/gemini",
    ]
    return any(keyword in model_lower for keyword in gemini_keywords)


def get_required_scope_for_model(model: str) -> str | None:
    """
    Get the required OAuth scope for a Gemini model.

    Args:
        model: Model name to check.

    Returns:
        Required OAuth scope URL, or None if not applicable.
    """
    model_lower = model.lower()

    if model_lower.startswith("vertex_ai/"):
        return "https://www.googleapis.com/auth/cloud-platform"
    if model_lower.startswith("gemini/") or model_lower.startswith("models/"):
        return "https://www.googleapis.com/auth/generative-language"
    if "gemini" in model_lower:
        # Default to cloud-platform for unqualified Gemini models
        return "https://www.googleapis.com/auth/cloud-platform"
    return None


@dataclass
class GeminiAuthConfig:
    """Authentication configuration for Gemini models."""

    credential_id: str | None = None
    credential_type: str | None = None  # "google_oauth"
    use_vertex_ai: bool = False
    project_id: str | None = None
    location: str | None = None


    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GeminiAuthConfig:
        """Create from dictionary."""
        return cls(
            credential_id=data.get("credential_id"),
            credential_type=data.get("credential_type"),
            use_vertex_ai=data.get("use_vertex_ai", False),
            project_id=data.get("project_id"),
            location=data.get("location"),

        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "credential_id": self.credential_id,
            "credential_type": self.credential_type,
            "use_vertex_ai": self.use_vertex_ai,
            "project_id": self.project_id,
            "location": self.location,

        }


__all__ = [
    "GeminiRoute",

    "GeminiRouteConfig",
    "GeminiAuthConfig",
    "detect_gemini_route",
    "get_vertex_project_id",
    "get_vertex_location",
    "normalize_gemini_model_name",
    "is_gemini_model",
    "get_required_scope_for_model",
]
