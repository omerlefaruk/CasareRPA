"""
Browser Recorder for CasareRPA.

Records user actions in the browser via Playwright's event interception.
Captures clicks, text input, navigation, selections, and other interactions.
Converts recorded actions into workflow node configurations.
"""

import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from loguru import logger

if TYPE_CHECKING:
    from playwright.async_api import Page


class BrowserActionType(Enum):
    """Types of browser actions that can be recorded."""

    CLICK = "click"
    TYPE = "type"
    NAVIGATE = "navigate"
    SELECT = "select"
    CHECK = "check"
    SCROLL = "scroll"
    HOVER = "hover"
    SUBMIT = "submit"
    FOCUS = "focus"
    DRAG = "drag"
    FILE_UPLOAD = "file_upload"
    KEYBOARD = "keyboard"


@dataclass
class BrowserRecordedAction:
    """Represents a single recorded browser action."""

    action_type: BrowserActionType
    timestamp: float = field(default_factory=time.time)
    selector: str = ""
    element_info: dict[str, Any] = field(default_factory=dict)
    value: str | None = None
    coordinates: tuple[int, int] | None = None
    url: str | None = None
    page_title: str | None = None
    keys: list[str] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert action to dictionary."""
        return {
            "action_type": self.action_type.value,
            "timestamp": self.timestamp,
            "selector": self.selector,
            "element_info": self.element_info,
            "value": self.value,
            "coordinates": self.coordinates,
            "url": self.url,
            "page_title": self.page_title,
            "keys": self.keys,
        }

    def get_description(self) -> str:
        """Get human-readable description of the action."""
        element_name = self.element_info.get("text", "")[:30] or self.selector[:30]

        if self.action_type == BrowserActionType.CLICK:
            return f"Click on {element_name}"
        elif self.action_type == BrowserActionType.TYPE:
            text_preview = (self.value or "")[:20]
            return (
                f"Type '{text_preview}...' into {element_name}"
                if len(self.value or "") > 20
                else f"Type '{self.value}' into {element_name}"
            )
        elif self.action_type == BrowserActionType.NAVIGATE:
            return f"Navigate to {self.url}"
        elif self.action_type == BrowserActionType.SELECT:
            return f"Select '{self.value}' in {element_name}"
        elif self.action_type == BrowserActionType.CHECK:
            return f"Check/Uncheck {element_name}"
        elif self.action_type == BrowserActionType.HOVER:
            return f"Hover over {element_name}"
        elif self.action_type == BrowserActionType.SCROLL:
            return "Scroll page"
        elif self.action_type == BrowserActionType.SUBMIT:
            return "Submit form"
        elif self.action_type == BrowserActionType.FOCUS:
            return f"Focus on {element_name}"
        elif self.action_type == BrowserActionType.KEYBOARD:
            keys_str = "+".join(self.keys or [])
            return f"Press {keys_str}"
        elif self.action_type == BrowserActionType.FILE_UPLOAD:
            return f"Upload file to {element_name}"
        elif self.action_type == BrowserActionType.DRAG:
            return (
                f"Drag from ({self.coordinates[0]}, {self.coordinates[1]})"
                if self.coordinates
                else "Drag"
            )
        return f"Unknown action on {element_name}"


RECORDING_SCRIPT = """
(function() {
    if (window.__casareRecorder) return;

    // Create recording UI with glowing red corners
    const createRecordingUI = function() {
        // Corner glow elements
        const corners = document.createElement('div');
        corners.id = '__casare_corners';
        corners.innerHTML = `
            <div class="__casare_corner __casare_tl"></div>
            <div class="__casare_corner __casare_tr"></div>
            <div class="__casare_corner __casare_bl"></div>
            <div class="__casare_corner __casare_br"></div>
        `;
        corners.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;pointer-events:none;z-index:2147483646;';
        document.body.appendChild(corners);

        // Status panel
        const panel = document.createElement('div');
        panel.id = '__casare_panel';
        panel.innerHTML = `
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;">
                <span class="__casare_dot"></span>
                <span style="font-weight:700;color:#ef4444;">RECORDING</span>
            </div>
            <div style="display:flex;gap:20px;margin-bottom:8px;">
                <div><span style="color:#888;">Clicks:</span> <span id="__casare_clicks" style="color:#3b82f6;font-weight:700;">0</span></div>
                <div><span style="color:#888;">Inputs:</span> <span id="__casare_inputs" style="color:#10b981;font-weight:700;">0</span></div>
            </div>
            <div id="__casare_status" style="font-size:11px;color:#666;margin-bottom:10px;">Ctrl+Click to select</div>
            <div style="border-top:1px solid #333;padding-top:8px;font-size:11px;color:#888;">
                <div><b style="color:#3b82f6;">Ctrl+Click</b> Select element</div>
                <div><b style="color:#10b981;">Type</b> Auto-captured</div>
                <div><b style="color:#ef4444;">Escape</b> Stop recording</div>
            </div>
        `;
        panel.style.cssText = `
            position:fixed;bottom:20px;right:20px;background:#1a1a1a;color:#e0e0e0;
            padding:14px 18px;border-radius:10px;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
            font-size:13px;z-index:2147483647;box-shadow:0 4px 24px rgba(0,0,0,0.6),0 0 0 2px rgba(239,68,68,0.4);
            min-width:200px;
        `;
        document.body.appendChild(panel);

        // Styles
        const style = document.createElement('style');
        style.id = '__casare_styles';
        style.textContent = `
            @keyframes __casare_glow {
                0%,100% { box-shadow:0 0 30px 8px rgba(239,68,68,0.7),0 0 60px 15px rgba(239,68,68,0.4); }
                50% { box-shadow:0 0 50px 15px rgba(239,68,68,0.9),0 0 80px 25px rgba(239,68,68,0.5); }
            }
            @keyframes __casare_pulse {
                0%,100% { opacity:1; }
                50% { opacity:0.3; }
            }
            .__casare_corner {
                position:fixed;width:100px;height:100px;pointer-events:none;
                animation:__casare_glow 1.5s ease-in-out infinite;
            }
            .__casare_tl { top:0;left:0;border-top:4px solid #ef4444;border-left:4px solid #ef4444;border-radius:12px 0 0 0; }
            .__casare_tr { top:0;right:0;border-top:4px solid #ef4444;border-right:4px solid #ef4444;border-radius:0 12px 0 0; }
            .__casare_bl { bottom:0;left:0;border-bottom:4px solid #ef4444;border-left:4px solid #ef4444;border-radius:0 0 0 12px; }
            .__casare_br { bottom:0;right:0;border-bottom:4px solid #ef4444;border-right:4px solid #ef4444;border-radius:0 0 12px 0; }
            .__casare_dot {
                display:inline-block;width:10px;height:10px;background:#ef4444;border-radius:50%;
                animation:__casare_pulse 1s infinite;
            }
            .__casare_hover {
                outline:3px dashed #3b82f6 !important;
                outline-offset:2px !important;
                background:rgba(59,130,246,0.1) !important;
            }
            .__casare_selected {
                outline:3px solid #10b981 !important;
                outline-offset:2px !important;
                background:rgba(16,185,129,0.15) !important;
            }
            .__casare_typing {
                outline:3px solid #f59e0b !important;
                outline-offset:2px !important;
                background:rgba(245,158,11,0.15) !important;
            }
            @keyframes __casare_flash {
                0% { transform:scale(1.05);background:rgba(16,185,129,0.3); }
                100% { transform:scale(1);background:rgba(16,185,129,0.15); }
            }
        `;
        document.head.appendChild(style);
    };

    const updateClicks = (n) => { const e=document.getElementById('__casare_clicks'); if(e) e.textContent=n; };
    const updateInputs = (n) => { const e=document.getElementById('__casare_inputs'); if(e) e.textContent=n; };
    const updateStatus = (t,c) => {
        const e=document.getElementById('__casare_status');
        if(e) { e.textContent=t; e.style.color=c||'#10b981'; }
    };

    const removeUI = function() {
        ['__casare_corners','__casare_panel','__casare_styles'].forEach(id => {
            const el=document.getElementById(id); if(el) el.remove();
        });
        document.querySelectorAll('.__casare_hover,.__casare_selected,.__casare_typing').forEach(el => {
            el.classList.remove('__casare_hover','__casare_selected','__casare_typing');
        });
    };

    window.__casareRecorder = {
        actions: [],
        inputTimer: null,
        lastInput: null,
        lastInputValue: '',
        enabled: true,
        clickCount: 0,
        inputCount: 0,
        lastHovered: null,

        getSelector: function(el) {
            if (!el || !el.tagName) return '';

            // Priority 1: ID
            if (el.id && !el.id.includes(':') && !el.id.match(/^\\d/)) {
                return '#' + CSS.escape(el.id);
            }

            // Priority 2: data-testid
            if (el.dataset && el.dataset.testid) {
                return '[data-testid="' + el.dataset.testid + '"]';
            }

            // Priority 3: data-cy (Cypress)
            if (el.dataset && el.dataset.cy) {
                return '[data-cy="' + el.dataset.cy + '"]';
            }

            // Priority 4: name attribute
            if (el.name && el.tagName.toLowerCase() !== 'meta') {
                return el.tagName.toLowerCase() + '[name="' + el.name + '"]';
            }

            // Priority 5: aria-label
            if (el.getAttribute && el.getAttribute('aria-label')) {
                return '[aria-label="' + el.getAttribute('aria-label') + '"]';
            }

            // Priority 6: Unique class combination
            if (el.className && typeof el.className === 'string') {
                const classes = el.className.split(' ')
                    .filter(c => c && !c.includes('hover') && !c.includes('focus') && !c.includes('active'))
                    .slice(0, 2);
                if (classes.length > 0) {
                    const selector = el.tagName.toLowerCase() + '.' + classes.join('.');
                    try {
                        if (document.querySelectorAll(selector).length === 1) {
                            return selector;
                        }
                    } catch (e) {}
                }
            }

            // Priority 7: Text content for buttons/links
            if ((el.tagName === 'BUTTON' || el.tagName === 'A') && el.innerText) {
                const text = el.innerText.trim().substring(0, 30);
                if (text && !text.includes('\\n')) {
                    return el.tagName.toLowerCase() + ':has-text("' + text + '")';
                }
            }

            // Priority 8: nth-child path (last resort)
            const path = [];
            let current = el;
            while (current && current !== document.body && path.length < 5) {
                let selector = current.tagName.toLowerCase();
                if (current.parentElement) {
                    const siblings = Array.from(current.parentElement.children)
                        .filter(child => child.tagName === current.tagName);
                    if (siblings.length > 1) {
                        const index = siblings.indexOf(current) + 1;
                        selector += ':nth-of-type(' + index + ')';
                    }
                }
                path.unshift(selector);
                current = current.parentElement;
            }
            return path.join(' > ');
        },

        getElementInfo: function(el) {
            if (!el || !el.tagName) return {};

            const rect = el.getBoundingClientRect();
            return {
                tag: el.tagName.toLowerCase(),
                id: el.id || null,
                classes: el.className && typeof el.className === 'string' ? el.className.split(' ').filter(c => c) : [],
                text: (el.innerText || el.textContent || '').substring(0, 100).trim(),
                type: el.type || null,
                name: el.name || null,
                href: el.href || null,
                value: el.value || null,
                placeholder: el.placeholder || null,
                ariaLabel: el.getAttribute ? el.getAttribute('aria-label') : null,
                role: el.getAttribute ? el.getAttribute('role') : null,
                rect: {
                    x: Math.round(rect.x),
                    y: Math.round(rect.y),
                    width: Math.round(rect.width),
                    height: Math.round(rect.height)
                }
            };
        },

        record: function(type, el, extra) {
            if (!this.enabled) return;

            extra = extra || {};
            const action = {
                type: type,
                selector: this.getSelector(el),
                element: this.getElementInfo(el),
                coords: extra.coords || null,
                value: extra.value || null,
                url: extra.url || window.location.href,
                pageTitle: document.title,
                timestamp: Date.now(),
                keys: extra.keys || null
            };

            if (window.__casareRecordAction) {
                window.__casareRecordAction(action);
            } else {
                this.actions.push(action);
            }
        },

        recordClick: function(el, coords) {
            this.clickCount++;
            updateClicks(this.clickCount);
            el.classList.add('__casare_selected');
            const tag = el.tagName.toLowerCase();
            const id = el.id ? '#'+el.id : '';
            updateStatus('Selected: ' + tag + id, '#10b981');
            this.record('click', el, {coords: coords});
        },

        recordInput: function(el, value) {
            this.inputCount++;
            updateInputs(this.inputCount);
            el.classList.remove('__casare_typing');
            el.classList.add('__casare_selected');
            updateStatus('Typed: "' + value.substring(0,20) + (value.length>20?'...':'') + '"', '#10b981');
            this.record('type', el, {value: value});
        },

        flush: function() {
            if (this.inputTimer) {
                clearTimeout(this.inputTimer);
                this.inputTimer = null;
                if (this.lastInput && this.lastInputValue) {
                    this.recordInput(this.lastInput, this.lastInputValue);
                }
                this.lastInput = null;
                this.lastInputValue = '';
            }
            const actions = this.actions;
            this.actions = [];
            return actions;
        },

        stop: function() {
            this.enabled = false;
            removeUI();
            return this.flush();
        }
    };

    // Initialize UI
    createRecordingUI();

    // Ctrl+Click handler for selection
    document.addEventListener('click', function(e) {
        if (!window.__casareRecorder.enabled) return;
        const el = e.target;
        if (!el || !el.tagName) return;
        if (el.closest('#__casare_panel')) return;

        // Only record on Ctrl+Click
        if (e.ctrlKey) {
            e.preventDefault();
            e.stopPropagation();
            window.__casareRecorder.flush();
            window.__casareRecorder.recordClick(el, [e.clientX, e.clientY]);
        }
    }, true);

    // Hover highlight when holding Ctrl
    document.addEventListener('mousemove', function(e) {
        if (!window.__casareRecorder || !window.__casareRecorder.enabled) return;
        const el = document.elementFromPoint(e.clientX, e.clientY);
        if (!el || el.closest('#__casare_panel') || el.closest('#__casare_corners')) return;

        // Clear previous hover
        document.querySelectorAll('.__casare_hover').forEach(prev => {
            if (prev !== el) prev.classList.remove('__casare_hover');
        });

        // Add hover if Ctrl held
        if (e.ctrlKey && !el.classList.contains('__casare_selected')) {
            el.classList.add('__casare_hover');
        }
    }, true);

    // Clear hover when Ctrl released
    document.addEventListener('keyup', function(e) {
        if (e.key === 'Control') {
            document.querySelectorAll('.__casare_hover').forEach(el => {
                el.classList.remove('__casare_hover');
            });
        }
    }, true);

    // Input handler with visual feedback
    document.addEventListener('input', function(e) {
        if (!window.__casareRecorder.enabled) return;
        const el = e.target;
        if (!el || !el.tagName) return;

        // Show typing indicator
        el.classList.add('__casare_typing');
        updateStatus('Typing...', '#f59e0b');

        clearTimeout(window.__casareRecorder.inputTimer);
        window.__casareRecorder.lastInput = el;
        window.__casareRecorder.lastInputValue = el.value;

        // Debounce: record after 800ms of no typing
        window.__casareRecorder.inputTimer = setTimeout(function() {
            if (window.__casareRecorder.lastInput && window.__casareRecorder.lastInputValue) {
                window.__casareRecorder.recordInput(
                    window.__casareRecorder.lastInput,
                    window.__casareRecorder.lastInputValue
                );
            }
            window.__casareRecorder.lastInput = null;
            window.__casareRecorder.lastInputValue = '';
        }, 800);
    }, true);

    // Select/checkbox change handler
    document.addEventListener('change', function(e) {
        if (!window.__casareRecorder.enabled) return;
        const el = e.target;
        if (!el || !el.tagName) return;

        if (el.tagName === 'SELECT') {
            window.__casareRecorder.clickCount++;
            updateClicks(window.__casareRecorder.clickCount);
            el.classList.add('__casare_selected');
            updateStatus('Selected option: ' + el.value, '#10b981');
            window.__casareRecorder.record('select', el, {value: el.value});
        } else if (el.type === 'checkbox' || el.type === 'radio') {
            window.__casareRecorder.clickCount++;
            updateClicks(window.__casareRecorder.clickCount);
            el.classList.add('__casare_selected');
            updateStatus((el.checked ? 'Checked' : 'Unchecked') + ' ' + (el.name||el.id||'input'), '#10b981');
            window.__casareRecorder.record('check', el, {value: el.checked ? 'true' : 'false'});
        }
    }, true);

    // Escape to stop recording, Enter to record key press
    document.addEventListener('keydown', function(e) {
        if (!window.__casareRecorder.enabled) return;

        if (e.key === 'Escape') {
            e.preventDefault();
            e.stopPropagation();
            updateStatus('Stopping...', '#ef4444');
            if (window.__casareStopRecording) {
                window.__casareStopRecording();
            }
            return;
        }

        // Record Enter key as action
        if (e.key === 'Enter') {
            // Flush any pending input first
            window.__casareRecorder.flush();
            // Record Enter as keyboard action
            window.__casareRecorder.clickCount++;
            updateClicks(window.__casareRecorder.clickCount);
            updateStatus('Pressed Enter', '#10b981');
            window.__casareRecorder.record('keyboard', e.target, {keys: ['Enter']});
        }
    }, true);

    console.log('[CasareRPA] Recording active - Ctrl+Click to select, Escape to stop');
})();
"""


class BrowserRecorder:
    """
    Records user actions in browser via Playwright.

    Injects a JavaScript recording script that captures:
    - Mouse clicks with element selectors
    - Text input with debouncing
    - Select/dropdown changes
    - Checkbox/radio changes
    - Form submissions
    - Keyboard shortcuts

    Example:
        recorder = BrowserRecorder(page)
        await recorder.start_recording()
        # ... user performs actions ...
        actions = await recorder.stop_recording()
        workflow_nodes = recorder.to_workflow_nodes()
    """

    def __init__(self, page: "Page") -> None:
        """
        Initialize the browser recorder.

        Args:
            page: Playwright Page instance to record from.
        """
        self._page = page
        self._actions: list[BrowserRecordedAction] = []
        self._recording = False
        self._start_time = 0.0
        self._start_datetime: datetime | None = None
        self._stop_requested = False

        # Callbacks for real-time notification
        self._on_action_recorded: Callable[[BrowserRecordedAction], None] | None = None
        self._on_recording_started: Callable[[], None] | None = None
        self._on_recording_stopped: Callable[[], None] | None = None

        logger.info("BrowserRecorder initialized")

    def set_callbacks(
        self,
        on_action_recorded: Callable[[BrowserRecordedAction], None] | None = None,
        on_recording_started: Callable[[], None] | None = None,
        on_recording_stopped: Callable[[], None] | None = None,
    ) -> None:
        """
        Set callback functions for recording events.

        Args:
            on_action_recorded: Called when each action is recorded.
            on_recording_started: Called when recording starts.
            on_recording_stopped: Called when recording stops.
        """
        self._on_action_recorded = on_action_recorded
        self._on_recording_started = on_recording_started
        self._on_recording_stopped = on_recording_stopped

    @property
    def is_recording(self) -> bool:
        """Check if recording is active."""
        return self._recording

    @property
    def action_count(self) -> int:
        """Get the number of recorded actions."""
        return len(self._actions)

    @property
    def start_time(self) -> datetime | None:
        """Get the recording start time."""
        return self._start_datetime

    async def start_recording(self) -> None:
        """
        Start recording browser actions.

        Injects the recording script into the page and sets up
        the callback function to receive recorded actions.

        Raises:
            RuntimeError: If recording is already in progress.
        """
        if self._recording:
            logger.warning("Recording already in progress")
            raise RuntimeError("Recording already in progress")

        self._recording = True
        self._start_time = time.time()
        self._start_datetime = datetime.now()
        self._actions.clear()

        try:
            # Expose callback function to receive actions from JavaScript
            await self._page.expose_function("__casareRecordAction", self._on_action_from_browser)
        except Exception as e:
            # Function might already be exposed from a previous recording session
            if "has been already registered" not in str(e):
                logger.warning(f"Could not expose recording function: {e}")

        try:
            # Expose stop callback for Escape key
            await self._page.expose_function("__casareStopRecording", self._on_stop_requested)
        except Exception as e:
            if "has been already registered" not in str(e):
                logger.warning(f"Could not expose stop function: {e}")

        # Inject the recording script
        await self._page.evaluate(RECORDING_SCRIPT)

        # Record initial navigation
        current_url = self._page.url
        if current_url and current_url != "about:blank":
            initial_action = BrowserRecordedAction(
                action_type=BrowserActionType.NAVIGATE,
                timestamp=0.0,
                url=current_url,
                page_title=await self._page.title(),
            )
            self._actions.append(initial_action)
            if self._on_action_recorded:
                self._on_action_recorded(initial_action)

        logger.info("Browser recording started")

        if self._on_recording_started:
            self._on_recording_started()

    async def stop_recording(self) -> list[BrowserRecordedAction]:
        """
        Stop recording and return all recorded actions.

        Returns:
            List of recorded browser actions.
        """
        if not self._recording:
            logger.warning("No recording in progress")
            return []

        self._recording = False

        try:
            # Flush any pending actions from the browser
            pending = await self._page.evaluate("window.__casareRecorder?.stop()")
            if pending and isinstance(pending, list):
                for action_data in pending:
                    self._process_action_data(action_data)
        except Exception as e:
            logger.warning(f"Could not flush pending actions: {e}")

        duration = time.time() - self._start_time
        logger.info(
            f"Browser recording stopped. Duration: {duration:.2f}s, Actions: {len(self._actions)}"
        )

        if self._on_recording_stopped:
            self._on_recording_stopped()

        return self._actions.copy()

    def _on_action_from_browser(self, data: dict) -> None:
        """
        Handle recorded action from browser JavaScript.

        Args:
            data: Action data from the recording script.
        """
        if not self._recording:
            return

        self._process_action_data(data)

    def _on_stop_requested(self) -> None:
        """Handle stop request from browser (Escape key pressed)."""
        logger.info("Stop recording requested from browser (Escape pressed)")
        self._stop_requested = True
        if self._on_recording_stopped:
            self._on_recording_stopped()

    @property
    def stop_requested(self) -> bool:
        """Check if stop was requested via Escape key."""
        return getattr(self, "_stop_requested", False)

    def _process_action_data(self, data: dict) -> None:
        """
        Process action data and create a BrowserRecordedAction.

        Args:
            data: Raw action data from the recording script.
        """
        try:
            action_type_str = data.get("type", "click")
            try:
                action_type = BrowserActionType(action_type_str)
            except ValueError:
                logger.warning(f"Unknown action type: {action_type_str}")
                return

            # Calculate relative timestamp
            browser_timestamp = data.get("timestamp", 0)
            if browser_timestamp and self._start_time:
                relative_time = (browser_timestamp / 1000) - self._start_time
            else:
                relative_time = time.time() - self._start_time

            action = BrowserRecordedAction(
                action_type=action_type,
                timestamp=relative_time,
                selector=data.get("selector", ""),
                element_info=data.get("element", {}),
                value=data.get("value"),
                coordinates=tuple(data["coords"]) if data.get("coords") else None,
                url=data.get("url"),
                page_title=data.get("pageTitle"),
                keys=data.get("keys"),
            )

            self._actions.append(action)
            logger.debug(f"Recorded: {action.get_description()}")

            if self._on_action_recorded:
                self._on_action_recorded(action)

        except Exception as e:
            logger.error(f"Failed to process action data: {e}")

    def get_actions(self) -> list[BrowserRecordedAction]:
        """
        Get all recorded actions.

        Returns:
            Copy of the recorded actions list.
        """
        return self._actions.copy()

    def clear(self) -> None:
        """Clear all recorded actions."""
        self._actions.clear()
        logger.info("Recording cleared")

    def to_workflow_nodes(self) -> list[dict[str, Any]]:
        """
        Convert recorded actions to workflow node configurations.

        Returns:
            List of node configuration dictionaries ready for
            workflow generation.
        """
        nodes = []
        for i, action in enumerate(self._actions):
            node = self._action_to_node(action, f"action_{i+1}")
            if node:
                nodes.append(node)
        return nodes

    def _action_to_node(self, action: BrowserRecordedAction, node_id: str) -> dict[str, Any] | None:
        """
        Convert a single action to a node configuration.

        Args:
            action: The recorded browser action.

        Returns:
            Node configuration dictionary or None if not convertible.
        """
        # Mapping of action types to node types and their configs
        mapping: dict[BrowserActionType, tuple[str, dict[str, Any]]] = {
            BrowserActionType.CLICK: (
                "ClickElementNode",
                {
                    "selector": action.selector,
                    "timeout": 30000,
                },
            ),
            BrowserActionType.TYPE: (
                "TypeTextNode",
                {
                    "selector": action.selector,
                    "text": action.value or "",
                    "clear_before": False,
                    "timeout": 30000,
                },
            ),
            BrowserActionType.NAVIGATE: (
                "NavigateNode",
                {
                    "url": action.url or "",
                    "wait_until": "load",
                },
            ),
            BrowserActionType.SELECT: (
                "SelectOptionNode",
                {
                    "selector": action.selector,
                    "value": action.value or "",
                    "timeout": 30000,
                },
            ),
            BrowserActionType.CHECK: (
                "CheckboxNode",
                {
                    "selector": action.selector,
                    "checked": action.value == "true",
                    "timeout": 30000,
                },
            ),
            BrowserActionType.HOVER: (
                "HoverElementNode",
                {
                    "selector": action.selector,
                    "timeout": 30000,
                },
            ),
            BrowserActionType.KEYBOARD: (
                "SendHotKeyNode",
                {
                    "keys": action.keys or [],
                },
            ),
            BrowserActionType.SUBMIT: (
                "ClickElementNode",  # Submit is usually a click on submit button
                {
                    "selector": action.selector or "form button[type='submit']",
                    "timeout": 30000,
                },
            ),
        }

        if action.action_type in mapping:
            node_type, config = mapping[action.action_type]
            return {
                "node_id": node_id,
                "node_type": node_type,
                "config": config,
                "name": action.get_description(),
            }

        return None


class BrowserWorkflowGenerator:
    """Generates workflow data from recorded browser actions."""

    @staticmethod
    def generate_workflow_data(
        actions: list[BrowserRecordedAction],
        workflow_name: str | None = None,
    ) -> dict[str, Any]:
        """
        Generate workflow nodes from recorded actions (user actions only).

        Only includes actual user interactions (Click, Type, Select, etc).
        Does NOT include scaffolding (Start, End, LaunchBrowser, CloseBrowser, Navigate).

        Args:
            actions: List of recorded browser actions.
            workflow_name: Optional workflow name.

        Returns:
            Workflow data dictionary with only user action nodes.
        """
        nodes: dict[str, dict[str, Any]] = {}
        connections: list[dict[str, Any]] = []

        # Generate workflow name if not provided
        if not workflow_name:
            workflow_name = f"Recorded Browser Workflow {datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Filter out Navigate actions (page load events, not user actions)
        user_actions = [a for a in actions if a.action_type != BrowserActionType.NAVIGATE]

        prev_node_id = None
        x_offset = 100
        HORIZONTAL_SPACING = 350  # Node width (~300) + 50px gap

        for i, action in enumerate(user_actions):
            node_data = BrowserWorkflowGenerator._action_to_node(action, f"action_{i+1}", 100)

            if node_data:
                # Position side-by-side horizontally
                node_data["position"] = [x_offset, 100]
                nodes[node_data["node_id"]] = node_data

                # Connect to previous node (exec only, no page connections)
                if prev_node_id:
                    connections.append(
                        {
                            "source_node": prev_node_id,
                            "source_port": "exec_out",
                            "target_node": node_data["node_id"],
                            "target_port": "exec_in",
                        }
                    )

                prev_node_id = node_data["node_id"]
                x_offset += HORIZONTAL_SPACING

        return {
            "metadata": {
                "name": workflow_name,
                "description": f"Recorded {len(nodes)} user actions",
                "version": "1.0.0",
            },
            "nodes": nodes,
            "connections": connections,
        }

    @staticmethod
    def _action_to_node(
        action: BrowserRecordedAction,
        node_id: str,
        y_pos: int,
    ) -> dict[str, Any] | None:
        """Convert a recorded action to a workflow node."""

        if action.action_type == BrowserActionType.CLICK:
            return {
                "node_id": node_id,
                "node_type": "ClickElementNode",
                "name": f"Click {action.element_info.get('text', '')[:20] or action.selector[:20]}",
                "position": [100, y_pos],
                "config": {
                    "selector": action.selector,
                    "timeout": 30000,
                },
            }

        elif action.action_type == BrowserActionType.TYPE:
            text_preview = (action.value or "")[:15]
            return {
                "node_id": node_id,
                "node_type": "TypeTextNode",
                "name": f"Type: {text_preview}...",
                "position": [100, y_pos],
                "config": {
                    "selector": action.selector,
                    "text": action.value or "",
                    "clear_before": False,
                    "timeout": 30000,
                },
            }

        elif action.action_type == BrowserActionType.NAVIGATE:
            url_preview = (action.url or "")[:30]
            return {
                "node_id": node_id,
                "node_type": "NavigateNode",
                "name": f"Navigate: {url_preview}",
                "position": [100, y_pos],
                "config": {
                    "url": action.url or "",
                    "wait_until": "load",
                },
            }

        elif action.action_type == BrowserActionType.SELECT:
            return {
                "node_id": node_id,
                "node_type": "SelectOptionNode",
                "name": f"Select: {action.value}",
                "position": [100, y_pos],
                "config": {
                    "selector": action.selector,
                    "value": action.value or "",
                },
            }

        elif action.action_type == BrowserActionType.CHECK:
            return {
                "node_id": node_id,
                "node_type": "CheckboxNode",
                "name": f"Check: {action.element_info.get('name', 'checkbox')}",
                "position": [100, y_pos],
                "config": {
                    "selector": action.selector,
                    "checked": action.value == "true",
                },
            }

        elif action.action_type == BrowserActionType.KEYBOARD:
            keys = action.keys or []
            # For Enter key, use TypeTextNode with press_enter_after
            if keys == ["Enter"]:
                return {
                    "node_id": node_id,
                    "node_type": "PressEnterNode",
                    "name": "Press Enter",
                    "position": [100, y_pos],
                    "config": {
                        "selector": action.selector,
                    },
                }
            # Other keys use SendHotKeyNode
            keys_str = "+".join(keys)
            return {
                "node_id": node_id,
                "node_type": "SendHotKeyNode",
                "name": f"Press: {keys_str}",
                "position": [100, y_pos],
                "config": {
                    "keys": keys,
                },
            }

        elif action.action_type == BrowserActionType.HOVER:
            return {
                "node_id": node_id,
                "node_type": "HoverElementNode",
                "name": f"Hover: {action.selector[:20]}",
                "position": [100, y_pos],
                "config": {
                    "selector": action.selector,
                },
            }

        elif action.action_type == BrowserActionType.SUBMIT:
            return {
                "node_id": node_id,
                "node_type": "SubmitFormNode",
                "name": "Submit Form",
                "position": [100, y_pos],
                "config": {
                    "selector": action.selector,
                },
            }

        return None


__all__ = [
    "BrowserActionType",
    "BrowserRecordedAction",
    "BrowserRecorder",
    "BrowserWorkflowGenerator",
]
