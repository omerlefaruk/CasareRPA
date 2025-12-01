"""Tests for Browser Recorder."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from casare_rpa.utils.recording.browser_recorder import (
    BrowserRecorder,
    BrowserRecordedAction,
    BrowserActionType,
    ElementInfo,
)


class TestElementInfo:
    """Tests for ElementInfo dataclass."""

    def test_create_empty(self):
        """Test creating empty element info."""
        info = ElementInfo()
        assert info.tag_name == ""
        assert info.id_attr == ""
        assert info.class_list == []

    def test_create_with_data(self):
        """Test creating element info with data."""
        info = ElementInfo(
            tag_name="button",
            id_attr="submit-btn",
            class_list=["btn", "primary"],
            text_content="Submit",
        )
        assert info.tag_name == "button"
        assert info.id_attr == "submit-btn"
        assert len(info.class_list) == 2

    def test_to_dict(self):
        """Test converting to dictionary."""
        info = ElementInfo(
            tag_name="input",
            id_attr="email",
            placeholder="Enter email",
        )
        d = info.to_dict()

        assert d["tag_name"] == "input"
        assert d["id"] == "email"
        assert d["placeholder"] == "Enter email"


class TestBrowserRecordedAction:
    """Tests for BrowserRecordedAction dataclass."""

    def test_create_navigate_action(self):
        """Test creating navigation action."""
        action = BrowserRecordedAction(
            action_type=BrowserActionType.NAVIGATE,
            url="https://example.com",
        )
        assert action.action_type == BrowserActionType.NAVIGATE
        assert action.url == "https://example.com"

    def test_create_click_action(self):
        """Test creating click action."""
        action = BrowserRecordedAction(
            action_type=BrowserActionType.CLICK,
            selector="#submit-btn",
            coordinates=(100, 200),
        )
        assert action.action_type == BrowserActionType.CLICK
        assert action.selector == "#submit-btn"
        assert action.coordinates == (100, 200)

    def test_create_type_action(self):
        """Test creating type action."""
        action = BrowserRecordedAction(
            action_type=BrowserActionType.TYPE,
            selector="#email-input",
            value="user@example.com",
        )
        assert action.action_type == BrowserActionType.TYPE
        assert action.value == "user@example.com"

    def test_to_dict(self):
        """Test converting action to dictionary."""
        action = BrowserRecordedAction(
            action_type=BrowserActionType.CLICK,
            url="https://example.com",
            selector="#btn",
        )
        d = action.to_dict()

        assert d["action_type"] == "click"
        assert d["url"] == "https://example.com"
        assert d["selector"] == "#btn"

    def test_get_description_navigate(self):
        """Test description for navigation."""
        action = BrowserRecordedAction(
            action_type=BrowserActionType.NAVIGATE,
            url="https://example.com/page",
        )
        desc = action.get_description()
        assert "Navigate" in desc
        assert "example.com" in desc

    def test_get_description_click(self):
        """Test description for click."""
        action = BrowserRecordedAction(
            action_type=BrowserActionType.CLICK,
            selector="#submit",
            element_info=ElementInfo(text_content="Submit Form"),
        )
        desc = action.get_description()
        assert "Click" in desc
        assert "Submit Form" in desc

    def test_get_description_type(self):
        """Test description for type."""
        action = BrowserRecordedAction(
            action_type=BrowserActionType.TYPE,
            value="Hello World",
        )
        desc = action.get_description()
        assert "Type" in desc
        assert "Hello World" in desc

    def test_get_description_truncates_long_text(self):
        """Test that long text is truncated in description."""
        long_text = "A" * 100
        action = BrowserRecordedAction(
            action_type=BrowserActionType.TYPE,
            value=long_text,
        )
        desc = action.get_description()
        assert len(desc) < 100
        assert "..." in desc


class TestBrowserRecorder:
    """Tests for BrowserRecorder class."""

    def test_init(self):
        """Test recorder initialization."""
        recorder = BrowserRecorder()
        assert recorder.is_recording is False
        assert recorder.is_paused is False
        assert recorder.action_count == 0

    def test_on_callback(self):
        """Test registering callbacks."""
        recorder = BrowserRecorder()
        callback = MagicMock()

        recorder.on("action_recorded", callback)

        # Callback list should have the callback
        assert callback in recorder._callbacks["action_recorded"]

    @pytest.mark.asyncio
    async def test_start_recording(self):
        """Test starting recording."""
        recorder = BrowserRecorder()

        await recorder.start()

        assert recorder.is_recording is True
        assert recorder.is_paused is False

    @pytest.mark.asyncio
    async def test_stop_recording(self):
        """Test stopping recording."""
        recorder = BrowserRecorder()
        await recorder.start()

        actions = recorder.stop()

        assert recorder.is_recording is False
        assert isinstance(actions, list)

    @pytest.mark.asyncio
    async def test_pause_resume(self):
        """Test pausing and resuming recording."""
        recorder = BrowserRecorder()
        await recorder.start()

        recorder.pause()
        assert recorder.is_paused is True
        assert recorder.is_recording is False  # is_recording returns False when paused

        recorder.resume()
        assert recorder.is_paused is False
        assert recorder.is_recording is True

    def test_clear_actions(self):
        """Test clearing recorded actions."""
        recorder = BrowserRecorder()
        # Manually add an action
        recorder._actions.append(
            BrowserRecordedAction(action_type=BrowserActionType.CLICK)
        )
        assert recorder.action_count == 1

        recorder.clear()
        assert recorder.action_count == 0

    @pytest.mark.asyncio
    async def test_add_wait_action(self):
        """Test manually adding wait action."""
        recorder = BrowserRecorder()
        await recorder.start()

        recorder.add_wait_action(selector="#element", timeout_ms=3000)

        assert recorder.action_count == 1
        action = recorder.actions[0]
        assert action.action_type == BrowserActionType.WAIT
        assert action.selector == "#element"
        assert action.value == "3000"

    @pytest.mark.asyncio
    async def test_add_screenshot_action(self):
        """Test manually adding screenshot action."""
        recorder = BrowserRecorder()
        await recorder.start()

        recorder.add_screenshot_action(filename="test.png")

        assert recorder.action_count == 1
        action = recorder.actions[0]
        assert action.action_type == BrowserActionType.SCREENSHOT
        assert action.value == "test.png"

    @pytest.mark.asyncio
    async def test_callbacks_called(self):
        """Test that callbacks are called on events."""
        recorder = BrowserRecorder()
        started_callback = MagicMock()
        stopped_callback = MagicMock()

        recorder.on("recording_started", started_callback)
        recorder.on("recording_stopped", stopped_callback)

        await recorder.start()
        started_callback.assert_called_once()

        recorder.stop()
        stopped_callback.assert_called_once()

    @pytest.mark.asyncio
    async def test_action_recorded_callback(self):
        """Test action recorded callback is called."""
        recorder = BrowserRecorder()
        action_callback = MagicMock()
        recorder.on("action_recorded", action_callback)

        await recorder.start()
        recorder.add_wait_action()

        action_callback.assert_called_once()

    def test_actions_copy_returned(self):
        """Test that actions property returns a copy."""
        recorder = BrowserRecorder()
        recorder._actions.append(
            BrowserRecordedAction(action_type=BrowserActionType.CLICK)
        )

        actions = recorder.actions
        actions.append(BrowserRecordedAction(action_type=BrowserActionType.TYPE))

        # Original should not be modified
        assert recorder.action_count == 1


class TestBrowserActionType:
    """Tests for BrowserActionType enum."""

    def test_all_action_types_exist(self):
        """Test all expected action types exist."""
        expected = [
            "NAVIGATE",
            "CLICK",
            "TYPE",
            "SELECT",
            "CHECK",
            "UNCHECK",
            "SCROLL",
            "HOVER",
            "PRESS_KEY",
            "WAIT",
            "SCREENSHOT",
        ]
        for name in expected:
            assert hasattr(BrowserActionType, name)

    def test_action_type_values(self):
        """Test action type values."""
        assert BrowserActionType.NAVIGATE.value == "navigate"
        assert BrowserActionType.CLICK.value == "click"
        assert BrowserActionType.TYPE.value == "type"
