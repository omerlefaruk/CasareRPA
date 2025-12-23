"""
CasareRPA - Project Settings

Project and scenario execution settings.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class ProjectSettings:
    """
    Project-level execution and behavior settings.

    Domain value object for project configuration.
    """

    default_browser: str = "chromium"
    stop_on_error: bool = True
    timeout_seconds: int = 30
    retry_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "default_browser": self.default_browser,
            "stop_on_error": self.stop_on_error,
            "timeout_seconds": self.timeout_seconds,
            "retry_count": self.retry_count,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProjectSettings":
        """Create from dictionary."""
        return cls(
            default_browser=data.get("default_browser", "chromium"),
            stop_on_error=data.get("stop_on_error", True),
            timeout_seconds=data.get("timeout_seconds", 30),
            retry_count=data.get("retry_count", 0),
        )


@dataclass
class ScenarioExecutionSettings:
    """
    Execution-time overrides for a scenario.

    Domain value object for scenario execution configuration.
    """

    priority: str = "normal"  # low, normal, high, critical
    timeout_override: int | None = None
    environment_override: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "priority": self.priority,
            "timeout_override": self.timeout_override,
            "environment_override": self.environment_override,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ScenarioExecutionSettings":
        """Create from dictionary."""
        return cls(
            priority=data.get("priority", "normal"),
            timeout_override=data.get("timeout_override"),
            environment_override=data.get("environment_override"),
        )
