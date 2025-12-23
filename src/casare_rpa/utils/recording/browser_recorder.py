"""
CasareRPA - Browser Action Recorder

Records user interactions with web pages via Playwright for workflow generation.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from loguru import logger


class BrowserActionType(Enum):
    """Types of recordable browser actions."""

    NAVIGATE = "navigate"
    CLICK = "click"
    TYPE = "type"
    SELECT = "select"
    CHECK = "check"
    UNCHECK = "uncheck"
    SCROLL = "scroll"
    HOVER = "hover"
    PRESS_KEY = "press_key"
    WAIT = "wait"
    SCREENSHOT = "screenshot"


@dataclass
class ElementInfo:
    """Information about a DOM element."""

    tag_name: str = ""
    id_attr: str = ""
    class_list: list[str] = field(default_factory=list)
    text_content: str = ""
    name_attr: str = ""
    type_attr: str = ""
    placeholder: str = ""
    aria_label: str = ""
    data_testid: str = ""
    role: str = ""
    href: str = ""
    value: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tag_name": self.tag_name,
            "id": self.id_attr,
            "classes": self.class_list,
            "text": self.text_content,
            "name": self.name_attr,
            "type": self.type_attr,
            "placeholder": self.placeholder,
            "aria_label": self.aria_label,
            "data_testid": self.data_testid,
            "role": self.role,
            "href": self.href,
            "value": self.value,
        }


@dataclass
class BrowserRecordedAction:
    """A recorded browser action."""

    action_type: BrowserActionType
    timestamp: datetime = field(default_factory=datetime.now)
    url: str = ""
    selector: str = ""
    value: str | None = None
    coordinates: tuple[int, int] | None = None
    element_info: ElementInfo = field(default_factory=ElementInfo)
    key: str | None = None  # For key press
    modifiers: list[str] = field(default_factory=list)  # Ctrl, Alt, Shift

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "action_type": self.action_type.value,
            "timestamp": self.timestamp.isoformat(),
            "url": self.url,
            "selector": self.selector,
            "value": self.value,
            "coordinates": self.coordinates,
            "element_info": self.element_info.to_dict(),
            "key": self.key,
            "modifiers": self.modifiers,
        }

    def get_description(self) -> str:
        """Get human-readable description of the action."""
        descriptions = {
            BrowserActionType.NAVIGATE: f"Navigate to {self.url}",
            BrowserActionType.CLICK: f"Click on {self._element_desc()}",
            BrowserActionType.TYPE: f"Type '{self._truncate(self.value or '', 30)}'",
            BrowserActionType.SELECT: f"Select '{self.value}' from {self._element_desc()}",
            BrowserActionType.CHECK: f"Check {self._element_desc()}",
            BrowserActionType.UNCHECK: f"Uncheck {self._element_desc()}",
            BrowserActionType.SCROLL: f"Scroll to ({self.coordinates[0]}, {self.coordinates[1]})"
            if self.coordinates
            else "Scroll",
            BrowserActionType.HOVER: f"Hover over {self._element_desc()}",
            BrowserActionType.PRESS_KEY: f"Press {'+'.join(self.modifiers + [self.key or ''])}",
            BrowserActionType.WAIT: f"Wait for {self._element_desc()}",
            BrowserActionType.SCREENSHOT: "Take screenshot",
        }
        return descriptions.get(self.action_type, str(self.action_type))

    def _element_desc(self) -> str:
        """Get short element description."""
        if self.element_info.text_content:
            return f"'{self._truncate(self.element_info.text_content, 20)}'"
        if self.element_info.id_attr:
            return f"#{self.element_info.id_attr}"
        if self.element_info.aria_label:
            return f"[{self.element_info.aria_label}]"
        if self.selector:
            return self._truncate(self.selector, 30)
        return "element"

    @staticmethod
    def _truncate(text: str, max_len: int) -> str:
        """Truncate text with ellipsis."""
        if len(text) <= max_len:
            return text
        return text[: max_len - 3] + "..."


class BrowserRecorder:
    """
    Records browser interactions for workflow generation.

    Uses Playwright page events to capture user actions.
    """

    def __init__(self):
        """Initialize the browser recorder."""
        self._page = None
        self._recording = False
        self._paused = False
        self._actions: list[BrowserRecordedAction] = []
        self._callbacks: dict[str, list[Callable]] = {
            "action_recorded": [],
            "recording_started": [],
            "recording_stopped": [],
            "recording_paused": [],
            "recording_resumed": [],
        }
        self._current_url = ""
        self._js_injected = False

        logger.debug("BrowserRecorder initialized")

    @property
    def is_recording(self) -> bool:
        """Check if recording is active."""
        return self._recording and not self._paused

    @property
    def is_paused(self) -> bool:
        """Check if recording is paused."""
        return self._paused

    @property
    def actions(self) -> list[BrowserRecordedAction]:
        """Get recorded actions."""
        return self._actions.copy()

    @property
    def action_count(self) -> int:
        """Get number of recorded actions."""
        return len(self._actions)

    def on(self, event: str, callback: Callable) -> None:
        """Register event callback."""
        if event in self._callbacks:
            self._callbacks[event].append(callback)

    def _emit(self, event: str, *args) -> None:
        """Emit event to callbacks."""
        for callback in self._callbacks.get(event, []):
            try:
                callback(*args)
            except Exception as e:
                logger.error(f"Callback error for {event}: {e}")

    async def attach(self, page: Any) -> None:
        """
        Attach recorder to a Playwright page.

        Args:
            page: Playwright Page object
        """
        self._page = page
        self._current_url = page.url

        # Register page event handlers
        page.on("load", self._on_page_load)
        page.on("close", self._on_page_close)

        # Inject JavaScript for event capture
        await self._inject_capture_script()

        logger.info(f"Browser recorder attached to page: {self._current_url}")

    async def _inject_capture_script(self) -> None:
        """Inject JavaScript to capture user interactions."""
        if not self._page or self._js_injected:
            return

        capture_script = """
        window.__casareRecorder = {
            recording: false,

            getElementInfo: function(element) {
                if (!element || !element.tagName) return null;

                const rect = element.getBoundingClientRect();
                return {
                    tagName: element.tagName.toLowerCase(),
                    id: element.id || '',
                    classes: Array.from(element.classList || []),
                    text: (element.textContent || '').trim().substring(0, 100),
                    name: element.name || '',
                    type: element.type || '',
                    placeholder: element.placeholder || '',
                    ariaLabel: element.getAttribute('aria-label') || '',
                    dataTestid: element.getAttribute('data-testid') || '',
                    role: element.getAttribute('role') || '',
                    href: element.href || '',
                    value: element.value || '',
                    rect: { x: rect.x, y: rect.y, width: rect.width, height: rect.height }
                };
            },

            generateSelector: function(element) {
                if (!element) return '';

                // Priority: data-testid > id > aria-label > name > CSS path
                if (element.getAttribute('data-testid')) {
                    return `[data-testid="${element.getAttribute('data-testid')}"]`;
                }
                if (element.id) {
                    return `#${element.id}`;
                }
                if (element.getAttribute('aria-label')) {
                    return `[aria-label="${element.getAttribute('aria-label')}"]`;
                }
                if (element.name) {
                    return `[name="${element.name}"]`;
                }

                // Generate CSS selector path
                let path = [];
                let current = element;
                while (current && current !== document.body) {
                    let selector = current.tagName.toLowerCase();
                    if (current.id) {
                        selector = `#${current.id}`;
                        path.unshift(selector);
                        break;
                    }
                    if (current.className) {
                        const classes = Array.from(current.classList).slice(0, 2).join('.');
                        if (classes) selector += `.${classes}`;
                    }

                    // Add nth-child for disambiguation
                    const siblings = current.parentElement ?
                        Array.from(current.parentElement.children).filter(c => c.tagName === current.tagName) : [];
                    if (siblings.length > 1) {
                        const index = siblings.indexOf(current) + 1;
                        selector += `:nth-child(${index})`;
                    }

                    path.unshift(selector);
                    current = current.parentElement;

                    if (path.length > 5) break;  // Limit depth
                }

                return path.join(' > ');
            },

            captureClick: function(event) {
                if (!this.recording) return;

                const target = event.target;
                const info = this.getElementInfo(target);
                const selector = this.generateSelector(target);

                window.__casareRecorderCallback('click', {
                    selector: selector,
                    elementInfo: info,
                    x: event.clientX,
                    y: event.clientY
                });
            },

            captureInput: function(event) {
                if (!this.recording) return;

                const target = event.target;
                if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA') {
                    const info = this.getElementInfo(target);
                    const selector = this.generateSelector(target);

                    window.__casareRecorderCallback('input', {
                        selector: selector,
                        elementInfo: info,
                        value: target.value
                    });
                }
            },

            captureChange: function(event) {
                if (!this.recording) return;

                const target = event.target;
                if (target.tagName === 'SELECT') {
                    const info = this.getElementInfo(target);
                    const selector = this.generateSelector(target);

                    window.__casareRecorderCallback('select', {
                        selector: selector,
                        elementInfo: info,
                        value: target.value
                    });
                } else if (target.type === 'checkbox' || target.type === 'radio') {
                    const info = this.getElementInfo(target);
                    const selector = this.generateSelector(target);

                    window.__casareRecorderCallback(target.checked ? 'check' : 'uncheck', {
                        selector: selector,
                        elementInfo: info
                    });
                }
            },

            init: function() {
                document.addEventListener('click', this.captureClick.bind(this), true);
                document.addEventListener('input', this.captureInput.bind(this), true);
                document.addEventListener('change', this.captureChange.bind(this), true);
            }
        };

        window.__casareRecorder.init();
        """

        try:
            await self._page.evaluate(capture_script)
            await self._page.expose_function("__casareRecorderCallback", self._handle_js_event)
            self._js_injected = True
            logger.debug("Capture script injected successfully")
        except Exception as e:
            logger.error(f"Failed to inject capture script: {e}")

    async def _handle_js_event(self, event_type: str, data: dict) -> None:
        """Handle events from JavaScript."""
        if not self._recording or self._paused:
            return

        try:
            element_info = ElementInfo()
            if "elementInfo" in data and data["elementInfo"]:
                ei = data["elementInfo"]
                element_info = ElementInfo(
                    tag_name=ei.get("tagName", ""),
                    id_attr=ei.get("id", ""),
                    class_list=ei.get("classes", []),
                    text_content=ei.get("text", ""),
                    name_attr=ei.get("name", ""),
                    type_attr=ei.get("type", ""),
                    placeholder=ei.get("placeholder", ""),
                    aria_label=ei.get("ariaLabel", ""),
                    data_testid=ei.get("dataTestid", ""),
                    role=ei.get("role", ""),
                    href=ei.get("href", ""),
                    value=ei.get("value", ""),
                )

            action_map = {
                "click": BrowserActionType.CLICK,
                "input": BrowserActionType.TYPE,
                "select": BrowserActionType.SELECT,
                "check": BrowserActionType.CHECK,
                "uncheck": BrowserActionType.UNCHECK,
            }

            action_type = action_map.get(event_type)
            if not action_type:
                return

            coordinates = None
            if "x" in data and "y" in data:
                coordinates = (data["x"], data["y"])

            action = BrowserRecordedAction(
                action_type=action_type,
                url=self._current_url,
                selector=data.get("selector", ""),
                value=data.get("value"),
                coordinates=coordinates,
                element_info=element_info,
            )

            self._record_action(action)

        except Exception as e:
            logger.error(f"Error handling JS event: {e}")

    def _on_page_load(self, page: Any = None) -> None:
        """Handle page load event."""
        if not self._recording or self._paused:
            return

        new_url = self._page.url if self._page else ""
        if new_url and new_url != self._current_url:
            action = BrowserRecordedAction(
                action_type=BrowserActionType.NAVIGATE,
                url=new_url,
            )
            self._record_action(action)
            self._current_url = new_url

    def _on_page_close(self, page: Any = None) -> None:
        """Handle page close event."""
        if self._recording:
            self.stop()

    def _record_action(self, action: BrowserRecordedAction) -> None:
        """Record an action."""
        self._actions.append(action)
        self._emit("action_recorded", action)
        logger.debug(f"Recorded: {action.get_description()}")

    async def start(self) -> None:
        """Start recording."""
        if self._recording:
            return

        self._recording = True
        self._paused = False
        self._actions.clear()

        if self._page:
            self._current_url = self._page.url
            # Enable recording in JavaScript
            try:
                await self._page.evaluate("window.__casareRecorder.recording = true")
            except Exception as e:
                logger.warning(f"Could not enable JS recording: {e}")

        self._emit("recording_started")
        logger.info("Browser recording started")

    def stop(self) -> list[BrowserRecordedAction]:
        """
        Stop recording and return actions.

        Returns:
            List of recorded actions
        """
        if not self._recording:
            return self._actions.copy()

        self._recording = False
        self._paused = False

        # Disable recording in JavaScript
        if self._page:
            try:
                asyncio.create_task(
                    self._page.evaluate("window.__casareRecorder.recording = false")
                )
            except Exception:
                pass

        self._emit("recording_stopped", self._actions.copy())
        logger.info(f"Browser recording stopped. {len(self._actions)} actions recorded.")

        return self._actions.copy()

    def pause(self) -> None:
        """Pause recording."""
        if self._recording and not self._paused:
            self._paused = True
            self._emit("recording_paused")
            logger.info("Browser recording paused")

    def resume(self) -> None:
        """Resume recording."""
        if self._recording and self._paused:
            self._paused = False
            self._emit("recording_resumed")
            logger.info("Browser recording resumed")

    def clear(self) -> None:
        """Clear recorded actions."""
        self._actions.clear()
        logger.debug("Recorded actions cleared")

    def add_wait_action(self, selector: str = "", timeout_ms: int = 5000) -> None:
        """
        Manually add a wait action.

        Args:
            selector: Element selector to wait for
            timeout_ms: Wait timeout in milliseconds
        """
        if not self._recording:
            return

        action = BrowserRecordedAction(
            action_type=BrowserActionType.WAIT,
            url=self._current_url,
            selector=selector,
            value=str(timeout_ms),
        )
        self._record_action(action)

    def add_screenshot_action(self, filename: str = "") -> None:
        """
        Manually add a screenshot action.

        Args:
            filename: Screenshot filename
        """
        if not self._recording:
            return

        action = BrowserRecordedAction(
            action_type=BrowserActionType.SCREENSHOT,
            url=self._current_url,
            value=filename,
        )
        self._record_action(action)


__all__ = [
    "BrowserRecorder",
    "BrowserRecordedAction",
    "BrowserActionType",
    "ElementInfo",
]
