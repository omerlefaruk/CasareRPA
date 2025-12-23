"""
CasareRPA - Action Processor

Processes and optimizes recorded actions before workflow generation.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import List, Optional

from loguru import logger

from casare_rpa.utils.recording.browser_recorder import (
    BrowserRecordedAction,
    BrowserActionType,
)


@dataclass
class ProcessingConfig:
    """Configuration for action processing."""

    # Merge consecutive type actions into one if within this time window
    merge_type_window_ms: int = 1000

    # Minimum time between clicks to not be considered double-click
    double_click_threshold_ms: int = 300

    # Insert wait before click if previous action was navigation
    auto_wait_after_navigation: bool = True
    navigation_wait_ms: int = 1000

    # Filter out very short scroll actions (accidental)
    min_scroll_distance: int = 50

    # Remove duplicate consecutive navigations to same URL
    dedupe_navigations: bool = True

    # Merge clicks on same element within threshold
    merge_consecutive_clicks: bool = True
    click_merge_threshold_ms: int = 500


class ActionProcessor:
    """
    Processes recorded actions for optimization.

    Operations:
    - Merge consecutive type actions
    - Deduplicate navigations
    - Insert automatic waits
    - Filter accidental actions
    - Optimize for reliable playback
    """

    def __init__(self, config: Optional[ProcessingConfig] = None):
        """
        Initialize action processor.

        Args:
            config: Processing configuration
        """
        self.config = config or ProcessingConfig()

    def process(self, actions: List[BrowserRecordedAction]) -> List[BrowserRecordedAction]:
        """
        Process and optimize a list of recorded actions.

        Args:
            actions: Raw recorded actions

        Returns:
            Processed and optimized actions
        """
        if not actions:
            return []

        processed = actions.copy()

        # Apply processing steps in order
        processed = self._merge_consecutive_types(processed)
        processed = self._deduplicate_navigations(processed)
        processed = self._merge_consecutive_clicks(processed)
        processed = self._insert_auto_waits(processed)
        processed = self._filter_accidental_actions(processed)

        logger.debug(f"Processed {len(actions)} actions -> {len(processed)} optimized actions")

        return processed

    def _merge_consecutive_types(
        self, actions: List[BrowserRecordedAction]
    ) -> List[BrowserRecordedAction]:
        """Merge consecutive TYPE actions on the same element."""
        if len(actions) < 2:
            return actions

        result = []
        i = 0

        while i < len(actions):
            action = actions[i]

            # Check if this is a TYPE action that can be merged
            if action.action_type == BrowserActionType.TYPE:
                merged_value = action.value or ""
                j = i + 1

                # Look for consecutive TYPE actions on same selector
                while j < len(actions):
                    next_action = actions[j]

                    if next_action.action_type != BrowserActionType.TYPE:
                        break

                    if next_action.selector != action.selector:
                        break

                    # Check time window
                    time_diff = (next_action.timestamp - action.timestamp).total_seconds() * 1000
                    if time_diff > self.config.merge_type_window_ms:
                        break

                    # Merge the values
                    merged_value = next_action.value or ""  # Use latest value
                    j += 1

                # Create merged action if any were merged
                if j > i + 1:
                    merged_action = BrowserRecordedAction(
                        action_type=BrowserActionType.TYPE,
                        timestamp=action.timestamp,
                        url=action.url,
                        selector=action.selector,
                        value=merged_value,
                        element_info=action.element_info,
                    )
                    result.append(merged_action)
                    i = j
                else:
                    result.append(action)
                    i += 1
            else:
                result.append(action)
                i += 1

        return result

    def _deduplicate_navigations(
        self, actions: List[BrowserRecordedAction]
    ) -> List[BrowserRecordedAction]:
        """Remove duplicate consecutive navigations to the same URL."""
        if not self.config.dedupe_navigations or len(actions) < 2:
            return actions

        result = []
        last_nav_url = None

        for action in actions:
            if action.action_type == BrowserActionType.NAVIGATE:
                if action.url != last_nav_url:
                    result.append(action)
                    last_nav_url = action.url
                # Skip duplicate navigation
            else:
                result.append(action)
                # Reset last nav URL if we have non-nav action between
                last_nav_url = None

        return result

    def _merge_consecutive_clicks(
        self, actions: List[BrowserRecordedAction]
    ) -> List[BrowserRecordedAction]:
        """Merge rapid clicks on the same element (detect double-click)."""
        if not self.config.merge_consecutive_clicks or len(actions) < 2:
            return actions

        result = []
        i = 0

        while i < len(actions):
            action = actions[i]

            if action.action_type == BrowserActionType.CLICK:
                # Look ahead for another click on same element
                if i + 1 < len(actions):
                    next_action = actions[i + 1]

                    if (
                        next_action.action_type == BrowserActionType.CLICK
                        and next_action.selector == action.selector
                    ):
                        time_diff = (
                            next_action.timestamp - action.timestamp
                        ).total_seconds() * 1000

                        if time_diff <= self.config.double_click_threshold_ms:
                            # This is a double-click - keep only one
                            # (the workflow node can handle double-click separately)
                            result.append(action)
                            i += 2  # Skip both
                            continue

            result.append(action)
            i += 1

        return result

    def _insert_auto_waits(
        self, actions: List[BrowserRecordedAction]
    ) -> List[BrowserRecordedAction]:
        """Insert automatic waits after navigations."""
        if not self.config.auto_wait_after_navigation:
            return actions

        result = []

        for i, action in enumerate(actions):
            result.append(action)

            # Insert wait after navigation if next action is an interaction
            if action.action_type == BrowserActionType.NAVIGATE:
                if i + 1 < len(actions):
                    next_action = actions[i + 1]

                    if next_action.action_type in (
                        BrowserActionType.CLICK,
                        BrowserActionType.TYPE,
                        BrowserActionType.SELECT,
                    ):
                        # Insert a wait action
                        wait_action = BrowserRecordedAction(
                            action_type=BrowserActionType.WAIT,
                            timestamp=action.timestamp + timedelta(milliseconds=1),
                            url=action.url,
                            selector=next_action.selector,
                            value=str(self.config.navigation_wait_ms),
                        )
                        result.append(wait_action)

        return result

    def _filter_accidental_actions(
        self, actions: List[BrowserRecordedAction]
    ) -> List[BrowserRecordedAction]:
        """Filter out actions that appear to be accidental."""
        result = []

        for action in actions:
            # Filter small scrolls
            if action.action_type == BrowserActionType.SCROLL:
                if action.coordinates:
                    # If scroll distance is too small, skip
                    # (coordinates contain scroll delta for scroll actions)
                    x, y = action.coordinates
                    if (
                        abs(x) < self.config.min_scroll_distance
                        and abs(y) < self.config.min_scroll_distance
                    ):
                        continue

            # Keep all other actions
            result.append(action)

        return result

    def add_element_waits(
        self, actions: List[BrowserRecordedAction]
    ) -> List[BrowserRecordedAction]:
        """
        Add wait-for-element actions before each interaction.

        This is more aggressive than auto_wait_after_navigation and
        adds waits before every click/type action.
        """
        result = []

        for action in actions:
            # Add wait before interactions
            if action.action_type in (
                BrowserActionType.CLICK,
                BrowserActionType.TYPE,
                BrowserActionType.SELECT,
            ):
                if action.selector:
                    wait_action = BrowserRecordedAction(
                        action_type=BrowserActionType.WAIT,
                        timestamp=action.timestamp - timedelta(milliseconds=1),
                        url=action.url,
                        selector=action.selector,
                        value="5000",  # 5 second timeout
                    )
                    result.append(wait_action)

            result.append(action)

        return result


__all__ = ["ActionProcessor", "ProcessingConfig"]
