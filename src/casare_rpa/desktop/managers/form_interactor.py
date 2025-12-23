"""
Form Interactor - Form control operations for desktop automation

Handles dropdowns, checkboxes, radio buttons, tabs, tree items, and scrolling.
All operations are async-first with proper error handling.
"""

import asyncio
from typing import Union

import uiautomation as auto
from loguru import logger

from casare_rpa.desktop.element import DesktopElement


class FormInteractor:
    """
    Handles form control interactions for desktop automation.

    Provides async methods for interacting with dropdowns, checkboxes,
    radio buttons, tabs, tree items, and scrollable elements.
    Uses asyncio.to_thread() for blocking UIAutomation calls and asyncio.sleep() for delays.
    """

    def __init__(self) -> None:
        """Initialize form interactor."""
        logger.debug("Initializing FormInteractor")

    async def select_from_dropdown(
        self, element: DesktopElement, value: str, by_text: bool = True
    ) -> bool:
        """
        Select an item from a dropdown/combobox.

        Args:
            element: DesktopElement representing the dropdown/combobox
            value: Value to select (text or index)
            by_text: If True, match by text; if False, treat value as index

        Returns:
            True if selection was successful

        Raises:
            ValueError: If item not found or selection fails
        """
        logger.debug(f"Selecting '{value}' from dropdown (by_text={by_text})")

        def _try_expand_and_select_pattern(control: auto.Control) -> bool:
            """Try expand pattern and selection pattern - returns True if successful."""
            try:
                expand_pattern = control.GetExpandCollapsePattern()
                if expand_pattern:
                    expand_state = expand_pattern.ExpandCollapseState
                    if expand_state == auto.ExpandCollapseState.Collapsed:
                        expand_pattern.Expand()
                        return True
            except Exception as e:
                logger.debug(f"Could not expand dropdown: {e}")
            return False

        def _try_selection_pattern(control: auto.Control) -> bool | None:
            """Try selection pattern - returns True if successful, None if not applicable."""
            try:
                selection_pattern = control.GetSelectionPattern()
                if selection_pattern:
                    items = control.GetChildren()
                    for item in items:
                        if item.ControlTypeName == "ListItemControl":
                            if by_text:
                                if item.Name == value or value.lower() in item.Name.lower():
                                    try:
                                        sel_item_pattern = item.GetSelectionItemPattern()
                                        if sel_item_pattern:
                                            sel_item_pattern.Select()
                                            logger.info(f"Selected '{item.Name}' from dropdown")
                                            return True
                                    except Exception as e:
                                        logger.debug(
                                            f"SelectionItemPattern failed, clicking item: {e}"
                                        )
                                        item.Click()
                                        logger.info(f"Clicked '{item.Name}' in dropdown")
                                        return True
            except Exception as e:
                logger.debug(f"SelectionPattern failed: {e}")
            return None

        def _try_value_pattern(control: auto.Control) -> bool | None:
            """Try value pattern - returns True if successful, None if not applicable."""
            try:
                value_pattern = control.GetValuePattern()
                if value_pattern and not value_pattern.IsReadOnly:
                    value_pattern.SetValue(value)
                    logger.info(f"Set dropdown value using ValuePattern: '{value}'")
                    return True
            except Exception as e:
                logger.debug(f"ValuePattern failed: {e}")
            return None

        def _click_and_find_list(control: auto.Control) -> auto.Control | None:
            """Click control and find popup list."""
            control.Click()
            list_control = None
            for child in auto.GetRootControl().GetChildren():
                if child.ControlTypeName in [
                    "ListControl",
                    "MenuControl",
                    "PopupControl",
                ]:
                    if child.BoundingRectangle.width() > 0:
                        list_control = child
                        break
            return list_control

        def _select_from_list(list_control: auto.Control) -> bool:
            """Select item from popup list."""
            for item in list_control.GetChildren():
                item_text = item.Name or ""
                if by_text and (item_text == value or value.lower() in item_text.lower()):
                    item.Click()
                    logger.info(f"Selected '{item_text}' from dropdown list")
                    return True
                elif not by_text:
                    try:
                        idx = int(value)
                        items = list(list_control.GetChildren())
                        if 0 <= idx < len(items):
                            items[idx].Click()
                            logger.info(f"Selected item at index {idx}")
                            return True
                    except ValueError:
                        pass
            return False

        try:
            control = element._control

            expanded = await asyncio.to_thread(_try_expand_and_select_pattern, control)
            if expanded:
                await asyncio.sleep(0.2)

            result = await asyncio.to_thread(_try_selection_pattern, control)
            if result is True:
                return True

            result = await asyncio.to_thread(_try_value_pattern, control)
            if result is True:
                return True

            list_control = await asyncio.to_thread(_click_and_find_list, control)
            await asyncio.sleep(0.3)

            if list_control:
                if await asyncio.to_thread(_select_from_list, list_control):
                    return True

            raise ValueError(f"Could not find item '{value}' in dropdown")

        except Exception as e:
            error_msg = f"Failed to select from dropdown: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    async def check_checkbox(self, element: DesktopElement, check: bool = True) -> bool:
        """
        Check or uncheck a checkbox.

        Args:
            element: DesktopElement representing the checkbox
            check: True to check, False to uncheck

        Returns:
            True if operation was successful

        Raises:
            ValueError: If checkbox cannot be toggled
        """
        logger.debug(f"Setting checkbox to {'checked' if check else 'unchecked'}")

        def _toggle() -> bool:
            control = element._control

            try:
                toggle_pattern = control.GetTogglePattern()
                if toggle_pattern:
                    current_state = toggle_pattern.ToggleState
                    is_checked = current_state == auto.ToggleState.On

                    if check and not is_checked:
                        toggle_pattern.Toggle()
                        if toggle_pattern.ToggleState == auto.ToggleState.Indeterminate:
                            toggle_pattern.Toggle()
                        logger.info("Checkbox checked")
                    elif not check and is_checked:
                        toggle_pattern.Toggle()
                        logger.info("Checkbox unchecked")
                    else:
                        logger.info(f"Checkbox already {'checked' if check else 'unchecked'}")

                    return True
            except Exception as e:
                logger.debug(f"TogglePattern failed: {e}")

            current_text = element.get_text().lower()
            is_checked = "checked" in current_text or "true" in current_text

            if (check and not is_checked) or (not check and is_checked):
                element.click()
                logger.info(f"Clicked checkbox to {'check' if check else 'uncheck'}")

            return True

        try:
            return await asyncio.to_thread(_toggle)
        except Exception as e:
            error_msg = f"Failed to toggle checkbox: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    async def select_radio_button(self, element: DesktopElement) -> bool:
        """
        Select a radio button.

        Args:
            element: DesktopElement representing the radio button

        Returns:
            True if selection was successful

        Raises:
            ValueError: If radio button cannot be selected
        """
        logger.debug("Selecting radio button")

        def _select() -> bool:
            control = element._control

            try:
                sel_item_pattern = control.GetSelectionItemPattern()
                if sel_item_pattern:
                    sel_item_pattern.Select()
                    logger.info(f"Selected radio button: {control.Name}")
                    return True
            except Exception as e:
                logger.debug(f"SelectionItemPattern failed: {e}")

            element.click()
            logger.info(f"Clicked radio button: {control.Name}")
            return True

        try:
            return await asyncio.to_thread(_select)
        except Exception as e:
            error_msg = f"Failed to select radio button: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    async def select_tab(
        self,
        tab_control: DesktopElement,
        tab_name: str = None,
        tab_index: int = None,
    ) -> bool:
        """
        Select a tab in a tab control.

        Args:
            tab_control: DesktopElement representing the tab control
            tab_name: Name of tab to select (partial match supported)
            tab_index: Index of tab to select (0-based)

        Returns:
            True if selection was successful

        Raises:
            ValueError: If tab not found or cannot be selected
        """
        if tab_name is None and tab_index is None:
            raise ValueError("Must provide either tab_name or tab_index")

        logger.debug(f"Selecting tab: name='{tab_name}', index={tab_index}")

        def _select_tab() -> bool:
            control = tab_control._control

            tab_items = []
            for child in control.GetChildren():
                if child.ControlTypeName == "TabItemControl":
                    tab_items.append(child)

            if not tab_items:
                for child in control.GetChildren():
                    for subchild in child.GetChildren():
                        if subchild.ControlTypeName == "TabItemControl":
                            tab_items.append(subchild)

            logger.debug(f"Found {len(tab_items)} tab items")

            target_tab = None

            if tab_index is not None:
                if 0 <= tab_index < len(tab_items):
                    target_tab = tab_items[tab_index]
                else:
                    raise ValueError(f"Tab index {tab_index} out of range (0-{len(tab_items)-1})")

            elif tab_name is not None:
                for tab in tab_items:
                    if tab.Name == tab_name or tab_name.lower() in tab.Name.lower():
                        target_tab = tab
                        break

                if not target_tab:
                    tab_names = [t.Name for t in tab_items]
                    raise ValueError(f"Tab '{tab_name}' not found. Available tabs: {tab_names}")

            try:
                sel_item_pattern = target_tab.GetSelectionItemPattern()
                if sel_item_pattern:
                    sel_item_pattern.Select()
                    logger.info(f"Selected tab: {target_tab.Name}")
                    return True
            except Exception as e:
                logger.debug(f"SelectionItemPattern failed: {e}")

            target_tab.Click()
            logger.info(f"Clicked tab: {target_tab.Name}")
            return True

        try:
            return await asyncio.to_thread(_select_tab)
        except Exception as e:
            error_msg = f"Failed to select tab: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    async def expand_tree_item(self, element: DesktopElement, expand: bool = True) -> bool:
        """
        Expand or collapse a tree item.

        Args:
            element: DesktopElement representing the tree item
            expand: True to expand, False to collapse

        Returns:
            True if operation was successful

        Raises:
            ValueError: If tree item cannot be expanded/collapsed
        """
        action = "expand" if expand else "collapse"
        logger.debug(f"Attempting to {action} tree item")

        def _toggle_expand() -> bool:
            control = element._control

            try:
                expand_pattern = control.GetExpandCollapsePattern()
                if expand_pattern:
                    current_state = expand_pattern.ExpandCollapseState

                    if expand and current_state == auto.ExpandCollapseState.Collapsed:
                        expand_pattern.Expand()
                        logger.info(f"Expanded tree item: {control.Name}")
                    elif not expand and current_state == auto.ExpandCollapseState.Expanded:
                        expand_pattern.Collapse()
                        logger.info(f"Collapsed tree item: {control.Name}")
                    else:
                        state_name = (
                            "expanded"
                            if current_state == auto.ExpandCollapseState.Expanded
                            else "collapsed"
                        )
                        logger.info(f"Tree item already {state_name}")

                    return True
            except Exception as e:
                logger.debug(f"ExpandCollapsePattern failed: {e}")

            rect = control.BoundingRectangle
            center_x = rect.left + rect.width() // 2
            center_y = rect.top + rect.height() // 2
            control.DoubleClick(x=center_x, y=center_y)
            logger.info(f"Double-clicked tree item to {action}: {control.Name}")
            return True

        try:
            return await asyncio.to_thread(_toggle_expand)
        except Exception as e:
            error_msg = f"Failed to {action} tree item: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    async def scroll_element(
        self,
        element: DesktopElement,
        direction: str = "down",
        amount: float | str = 0.5,
    ) -> bool:
        """
        Scroll an element (scrollbar, list, window, etc.).

        Args:
            element: DesktopElement to scroll
            direction: Scroll direction - "up", "down", "left", "right"
            amount: Scroll amount as percentage (0.0 to 1.0) or "page" for page scroll

        Returns:
            True if scroll was successful

        Raises:
            ValueError: If element cannot be scrolled
        """
        logger.debug(f"Scrolling element {direction} by {amount}")

        valid_directions = ["up", "down", "left", "right"]
        if direction.lower() not in valid_directions:
            raise ValueError(f"Invalid direction '{direction}'. Must be one of: {valid_directions}")

        direction = direction.lower()

        def _try_scroll_pattern(control: auto.Control) -> bool | None:
            """Try scroll pattern - returns True if successful, None if not applicable."""
            try:
                scroll_pattern = control.GetScrollPattern()
                if scroll_pattern:
                    h_scroll = scroll_pattern.HorizontalScrollPercent
                    v_scroll = scroll_pattern.VerticalScrollPercent

                    if isinstance(amount, str) and amount.lower() == "page":
                        scroll_amount = 100
                    else:
                        scroll_amount = float(amount) * 100

                    if direction == "down":
                        new_v = min(100, v_scroll + scroll_amount)
                        scroll_pattern.SetScrollPercent(h_scroll, new_v)
                    elif direction == "up":
                        new_v = max(0, v_scroll - scroll_amount)
                        scroll_pattern.SetScrollPercent(h_scroll, new_v)
                    elif direction == "right":
                        new_h = min(100, h_scroll + scroll_amount)
                        scroll_pattern.SetScrollPercent(new_h, v_scroll)
                    elif direction == "left":
                        new_h = max(0, h_scroll - scroll_amount)
                        scroll_pattern.SetScrollPercent(new_h, v_scroll)

                    logger.info(f"Scrolled {direction} by {scroll_amount}%")
                    return True
            except Exception as e:
                logger.debug(f"ScrollPattern failed: {e}")
            return None

        def _set_focus(control: auto.Control) -> None:
            """Set focus on control."""
            control.SetFocus()

        def _scroll_with_wheel(control: auto.Control) -> bool:
            """Scroll using mouse wheel."""
            rect = control.BoundingRectangle
            center_x = rect.left + rect.width() // 2
            center_y = rect.top + rect.height() // 2

            wheel_delta = 3 if isinstance(amount, str) else max(1, int(float(amount) * 5))

            if direction == "down":
                auto.WheelDown(center_x, center_y, wheelTimes=wheel_delta)
            else:
                auto.WheelUp(center_x, center_y, wheelTimes=wheel_delta)

            logger.info(f"Scrolled {direction} using mouse wheel")
            return True

        def _scroll_with_keyboard(control: auto.Control) -> bool:
            """Scroll using keyboard."""
            key = "{Right}" if direction == "right" else "{Left}"
            times = 5 if isinstance(amount, str) else max(1, int(float(amount) * 10))
            for _ in range(times):
                control.SendKeys(key)

            logger.info(f"Scrolled {direction} using keyboard")
            return True

        try:
            control = element._control

            result = await asyncio.to_thread(_try_scroll_pattern, control)
            if result is True:
                return True

            await asyncio.to_thread(_set_focus, control)
            await asyncio.sleep(0.1)

            if direction in ["up", "down"]:
                return await asyncio.to_thread(_scroll_with_wheel, control)
            else:
                return await asyncio.to_thread(_scroll_with_keyboard, control)

        except Exception as e:
            error_msg = f"Failed to scroll element: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg)
