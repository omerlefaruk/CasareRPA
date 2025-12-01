"""Tests for Action Processor."""

import pytest
from datetime import datetime, timedelta

from casare_rpa.utils.recording.browser_recorder import (
    BrowserRecordedAction,
    BrowserActionType,
)
from casare_rpa.utils.recording.action_processor import (
    ActionProcessor,
    ProcessingConfig,
)


class TestProcessingConfig:
    """Tests for ProcessingConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = ProcessingConfig()

        assert config.merge_type_window_ms == 1000
        assert config.double_click_threshold_ms == 300
        assert config.auto_wait_after_navigation is True
        assert config.navigation_wait_ms == 1000
        assert config.min_scroll_distance == 50
        assert config.dedupe_navigations is True

    def test_custom_values(self):
        """Test custom configuration values."""
        config = ProcessingConfig(
            merge_type_window_ms=500,
            auto_wait_after_navigation=False,
        )

        assert config.merge_type_window_ms == 500
        assert config.auto_wait_after_navigation is False


class TestActionProcessor:
    """Tests for ActionProcessor class."""

    def test_init_default_config(self):
        """Test initialization with default config."""
        processor = ActionProcessor()
        assert processor.config is not None

    def test_init_custom_config(self):
        """Test initialization with custom config."""
        config = ProcessingConfig(merge_type_window_ms=500)
        processor = ActionProcessor(config)
        assert processor.config.merge_type_window_ms == 500

    def test_process_empty_list(self):
        """Test processing empty action list."""
        processor = ActionProcessor()
        result = processor.process([])
        assert result == []

    def test_process_single_action(self):
        """Test processing single action."""
        processor = ActionProcessor()
        actions = [
            BrowserRecordedAction(
                action_type=BrowserActionType.CLICK,
                selector="#btn",
            )
        ]

        result = processor.process(actions)

        assert len(result) == 1
        assert result[0].action_type == BrowserActionType.CLICK


class TestMergeConsecutiveTypes:
    """Tests for merging consecutive TYPE actions."""

    def test_merge_consecutive_types_same_element(self):
        """Test merging consecutive type actions on same element."""
        processor = ActionProcessor()
        base_time = datetime.now()

        actions = [
            BrowserRecordedAction(
                action_type=BrowserActionType.TYPE,
                selector="#input",
                value="H",
                timestamp=base_time,
            ),
            BrowserRecordedAction(
                action_type=BrowserActionType.TYPE,
                selector="#input",
                value="He",
                timestamp=base_time + timedelta(milliseconds=100),
            ),
            BrowserRecordedAction(
                action_type=BrowserActionType.TYPE,
                selector="#input",
                value="Hello",
                timestamp=base_time + timedelta(milliseconds=200),
            ),
        ]

        result = processor.process(actions)

        # Should merge into one action with final value
        type_actions = [a for a in result if a.action_type == BrowserActionType.TYPE]
        assert len(type_actions) == 1
        assert type_actions[0].value == "Hello"

    def test_no_merge_different_elements(self):
        """Test no merge when typing in different elements."""
        processor = ActionProcessor()
        base_time = datetime.now()

        actions = [
            BrowserRecordedAction(
                action_type=BrowserActionType.TYPE,
                selector="#input1",
                value="Hello",
                timestamp=base_time,
            ),
            BrowserRecordedAction(
                action_type=BrowserActionType.TYPE,
                selector="#input2",
                value="World",
                timestamp=base_time + timedelta(milliseconds=100),
            ),
        ]

        result = processor.process(actions)

        type_actions = [a for a in result if a.action_type == BrowserActionType.TYPE]
        assert len(type_actions) == 2

    def test_no_merge_outside_window(self):
        """Test no merge when time gap is too large."""
        config = ProcessingConfig(merge_type_window_ms=500)
        processor = ActionProcessor(config)
        base_time = datetime.now()

        actions = [
            BrowserRecordedAction(
                action_type=BrowserActionType.TYPE,
                selector="#input",
                value="Hello",
                timestamp=base_time,
            ),
            BrowserRecordedAction(
                action_type=BrowserActionType.TYPE,
                selector="#input",
                value="World",
                timestamp=base_time + timedelta(milliseconds=1000),  # Outside window
            ),
        ]

        result = processor.process(actions)

        type_actions = [a for a in result if a.action_type == BrowserActionType.TYPE]
        assert len(type_actions) == 2


class TestDeduplicateNavigations:
    """Tests for deduplicating navigations."""

    def test_dedupe_same_url(self):
        """Test deduplicating navigations to same URL."""
        processor = ActionProcessor()

        actions = [
            BrowserRecordedAction(
                action_type=BrowserActionType.NAVIGATE,
                url="https://example.com",
            ),
            BrowserRecordedAction(
                action_type=BrowserActionType.NAVIGATE,
                url="https://example.com",
            ),
        ]

        result = processor.process(actions)

        nav_actions = [a for a in result if a.action_type == BrowserActionType.NAVIGATE]
        assert len(nav_actions) == 1

    def test_keep_different_urls(self):
        """Test keeping navigations to different URLs."""
        processor = ActionProcessor()

        actions = [
            BrowserRecordedAction(
                action_type=BrowserActionType.NAVIGATE,
                url="https://example.com/page1",
            ),
            BrowserRecordedAction(
                action_type=BrowserActionType.NAVIGATE,
                url="https://example.com/page2",
            ),
        ]

        result = processor.process(actions)

        nav_actions = [a for a in result if a.action_type == BrowserActionType.NAVIGATE]
        assert len(nav_actions) == 2

    def test_config_disable_dedupe(self):
        """Test disabling deduplication."""
        config = ProcessingConfig(dedupe_navigations=False)
        processor = ActionProcessor(config)

        actions = [
            BrowserRecordedAction(
                action_type=BrowserActionType.NAVIGATE,
                url="https://example.com",
            ),
            BrowserRecordedAction(
                action_type=BrowserActionType.NAVIGATE,
                url="https://example.com",
            ),
        ]

        result = processor.process(actions)

        nav_actions = [a for a in result if a.action_type == BrowserActionType.NAVIGATE]
        assert len(nav_actions) == 2


class TestAutoWaits:
    """Tests for automatic wait insertion."""

    def test_insert_wait_after_navigation(self):
        """Test inserting wait after navigation before click."""
        processor = ActionProcessor()

        actions = [
            BrowserRecordedAction(
                action_type=BrowserActionType.NAVIGATE,
                url="https://example.com",
            ),
            BrowserRecordedAction(
                action_type=BrowserActionType.CLICK,
                selector="#btn",
            ),
        ]

        result = processor.process(actions)

        # Should have: NAVIGATE, WAIT, CLICK
        assert len(result) == 3
        assert result[0].action_type == BrowserActionType.NAVIGATE
        assert result[1].action_type == BrowserActionType.WAIT
        assert result[2].action_type == BrowserActionType.CLICK

    def test_no_wait_between_clicks(self):
        """Test no wait inserted between clicks."""
        processor = ActionProcessor()

        actions = [
            BrowserRecordedAction(
                action_type=BrowserActionType.CLICK,
                selector="#btn1",
            ),
            BrowserRecordedAction(
                action_type=BrowserActionType.CLICK,
                selector="#btn2",
            ),
        ]

        result = processor.process(actions)

        wait_actions = [a for a in result if a.action_type == BrowserActionType.WAIT]
        assert len(wait_actions) == 0

    def test_config_disable_auto_wait(self):
        """Test disabling auto wait insertion."""
        config = ProcessingConfig(auto_wait_after_navigation=False)
        processor = ActionProcessor(config)

        actions = [
            BrowserRecordedAction(
                action_type=BrowserActionType.NAVIGATE,
                url="https://example.com",
            ),
            BrowserRecordedAction(
                action_type=BrowserActionType.CLICK,
                selector="#btn",
            ),
        ]

        result = processor.process(actions)

        wait_actions = [a for a in result if a.action_type == BrowserActionType.WAIT]
        assert len(wait_actions) == 0


class TestAddElementWaits:
    """Tests for add_element_waits method."""

    def test_add_waits_before_interactions(self):
        """Test adding waits before all interactions."""
        processor = ActionProcessor()

        actions = [
            BrowserRecordedAction(
                action_type=BrowserActionType.CLICK,
                selector="#btn",
            ),
            BrowserRecordedAction(
                action_type=BrowserActionType.TYPE,
                selector="#input",
                value="text",
            ),
        ]

        result = processor.add_element_waits(actions)

        # Should have: WAIT, CLICK, WAIT, TYPE
        assert len(result) == 4
        assert result[0].action_type == BrowserActionType.WAIT
        assert result[1].action_type == BrowserActionType.CLICK
        assert result[2].action_type == BrowserActionType.WAIT
        assert result[3].action_type == BrowserActionType.TYPE

    def test_wait_uses_action_selector(self):
        """Test that wait uses the action's selector."""
        processor = ActionProcessor()

        actions = [
            BrowserRecordedAction(
                action_type=BrowserActionType.CLICK,
                selector="#my-button",
            ),
        ]

        result = processor.add_element_waits(actions)

        wait_action = result[0]
        assert wait_action.selector == "#my-button"
