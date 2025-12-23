"""
CasareRPA - System Events

Typed domain events for system-level operations.
Includes variable changes, browser events, and log messages.
Replaces EventType.VARIABLE_SET, BROWSER_PAGE_READY, LOG_MESSAGE enum values.
"""

from dataclasses import dataclass
from typing import Any

from casare_rpa.domain.events.base import DomainEvent
from casare_rpa.domain.value_objects.log_entry import LogLevel


@dataclass(frozen=True)
class VariableSet(DomainEvent):
    """
    Event raised when a variable is set in the execution context.

    Attributes:
        variable_name: Name of the variable
        variable_value: New value (may be None)
        workflow_id: ID of the workflow context
        source_node_id: ID of the node that set the variable (if any)
    """

    variable_name: str = ""
    variable_value: Any = None
    workflow_id: str = ""
    source_node_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        result = super().to_dict()
        result.update(
            {
                "variable_name": self.variable_name,
                "variable_value": self.variable_value,
                "workflow_id": self.workflow_id,
                "source_node_id": self.source_node_id,
            }
        )
        return result


@dataclass(frozen=True)
class BrowserPageReady(DomainEvent):
    """
    Event raised when a browser page is ready for selector/recording.

    Attributes:
        page_id: Unique identifier for the page
        url: Current URL of the page
        title: Page title
        browser_type: Browser type (chromium, firefox, webkit)
    """

    page_id: str = ""
    url: str = ""
    title: str = ""
    browser_type: str = "chromium"

    def to_dict(self) -> dict[str, Any]:
        result = super().to_dict()
        result.update(
            {
                "page_id": self.page_id,
                "url": self.url,
                "title": self.title,
                "browser_type": self.browser_type,
            }
        )
        return result


@dataclass(frozen=True)
class LogMessage(DomainEvent):
    """
    Event raised when a log message is emitted.

    Attributes:
        level: Log severity level
        message: Log message content
        source: Source of the log (module, node type, etc.)
        node_id: ID of the node that logged (if any)
        workflow_id: ID of the workflow context (if any)
        extra_data: Additional structured data
    """

    level: LogLevel = LogLevel.INFO
    message: str = ""
    source: str | None = None
    node_id: str | None = None
    workflow_id: str | None = None
    extra_data: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        result = super().to_dict()
        result.update(
            {
                "level": self.level.value,
                "message": self.message,
                "source": self.source,
                "node_id": self.node_id,
                "workflow_id": self.workflow_id,
                "extra_data": self.extra_data,
            }
        )
        return result


@dataclass(frozen=True)
class DebugBreakpointHit(DomainEvent):
    """
    Event raised when execution hits a breakpoint in debug mode.

    Attributes:
        node_id: ID of the node with the breakpoint
        workflow_id: ID of the workflow
        variables: Current variable state snapshot
    """

    node_id: str = ""
    workflow_id: str = ""
    variables: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        result = super().to_dict()
        result.update(
            {
                "node_id": self.node_id,
                "workflow_id": self.workflow_id,
                "variables": self.variables,
            }
        )
        return result


@dataclass(frozen=True)
class ResourceAcquired(DomainEvent):
    """
    Event raised when a shared resource is acquired.

    Attributes:
        resource_type: Type of resource (browser, database, file, etc.)
        resource_id: Unique identifier for the resource
        workflow_id: ID of the workflow that acquired the resource
    """

    resource_type: str = ""
    resource_id: str = ""
    workflow_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        result = super().to_dict()
        result.update(
            {
                "resource_type": self.resource_type,
                "resource_id": self.resource_id,
                "workflow_id": self.workflow_id,
            }
        )
        return result


@dataclass(frozen=True)
class ResourceReleased(DomainEvent):
    """
    Event raised when a shared resource is released.

    Attributes:
        resource_type: Type of resource
        resource_id: Unique identifier for the resource
        workflow_id: ID of the workflow that released the resource
    """

    resource_type: str = ""
    resource_id: str = ""
    workflow_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        result = super().to_dict()
        result.update(
            {
                "resource_type": self.resource_type,
                "resource_id": self.resource_id,
                "workflow_id": self.workflow_id,
            }
        )
        return result


__all__ = [
    "VariableSet",
    "BrowserPageReady",
    "LogMessage",
    "DebugBreakpointHit",
    "ResourceAcquired",
    "ResourceReleased",
]
