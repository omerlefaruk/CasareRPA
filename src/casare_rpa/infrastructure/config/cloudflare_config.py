"""Cloudflare Tunnel configuration for remote access."""

import os
from dataclasses import dataclass


@dataclass
class CloudflareConfig:
    """
    URLs for CasareRPA services (local or via Cloudflare Tunnel).

    Environment Variables:
        CASARE_API_URL: FastAPI monitoring API endpoint
        CASARE_WEBHOOK_URL: Webhook receiver endpoint
        CASARE_ROBOT_WS_URL: Robot WebSocket endpoint

    Usage:
        # Local development (default)
        config = CloudflareConfig.from_env()

        # Production with Cloudflare Tunnel
        config = CloudflareConfig.production()
    """

    # FastAPI monitoring API endpoint
    api_url: str

    # Webhook receiver endpoint (for external services to call)
    webhook_url: str

    # Robot WebSocket endpoint
    robot_ws_url: str

    @classmethod
    def from_env(cls) -> "CloudflareConfig":
        """Load configuration from environment variables."""
        return cls(
            api_url=os.getenv("CASARE_API_URL", "http://localhost:8000"),
            webhook_url=os.getenv("CASARE_WEBHOOK_URL", "http://localhost:8766"),
            robot_ws_url=os.getenv("CASARE_ROBOT_WS_URL", "ws://localhost:8765"),
        )

    @classmethod
    def production(cls) -> "CloudflareConfig":
        """Production config using Cloudflare Tunnel for casare.net."""
        return cls(
            api_url="https://api.casare.net",
            webhook_url="https://webhooks.casare.net",
            robot_ws_url="wss://robots.casare.net",
        )

    @classmethod
    def local(cls) -> "CloudflareConfig":
        """Local development config (localhost)."""
        return cls(
            api_url="http://localhost:8000",
            webhook_url="http://localhost:8766",
            robot_ws_url="ws://localhost:8765",
        )

    @property
    def is_production(self) -> bool:
        """Check if using production (tunnel) URLs."""
        return "casare.net" in self.api_url

    @property
    def is_secure(self) -> bool:
        """Check if using HTTPS/WSS."""
        return self.api_url.startswith("https://")
