"""
Desktop Selector System

Provides selector parsing and element finding strategies for desktop automation.
"""

import time
from typing import Any, Dict, List, Optional
from loguru import logger
import uiautomation as auto

from casare_rpa.desktop.element import DesktopElement


def parse_selector(selector: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse and validate a desktop selector.

    Selector format:
    {
        "strategy": "control_type" | "name" | "automation_id" | "class_name",
        "value": <string>,
        "properties": {  # Optional additional filters
            "Name": "...",
            "AutomationId": "...",
            ...
        }
    }

    Args:
        selector: Selector dictionary

    Returns:
        Validated and normalized selector

    Raises:
        ValueError: If selector is invalid
    """
    if not isinstance(selector, dict):
        raise ValueError(f"Selector must be a dictionary, got {type(selector)}")

    # Validate required fields
    if "strategy" not in selector:
        raise ValueError("Selector must have 'strategy' field")

    if "value" not in selector:
        raise ValueError("Selector must have 'value' field")

    strategy = selector["strategy"]
    valid_strategies = ["control_type", "name", "automation_id", "class_name", "xpath"]

    if strategy not in valid_strategies:
        raise ValueError(f"Invalid strategy '{strategy}'. Must be one of: {valid_strategies}")

    # Normalize selector
    normalized = {
        "strategy": strategy,
        "value": str(selector["value"]),
        "properties": selector.get("properties", {}),
    }

    logger.debug(f"Parsed selector: {normalized}")
    return normalized


def find_element(
    parent_control: auto.Control, selector: Dict[str, Any], timeout: float = 5.0
) -> Optional[DesktopElement]:
    """
    Find an element using selector.

    Args:
        parent_control: Parent UI Automation control to search within
        selector: Selector dictionary
        timeout: Maximum time to wait for element (seconds)

    Returns:
        DesktopElement if found, None otherwise

    Raises:
        ValueError: If selector is invalid or element not found
    """
    logger.debug(f"Finding element with selector: {selector}")

    # Parse selector
    parsed = parse_selector(selector)
    strategy = parsed["strategy"]
    value = parsed["value"]
    properties = parsed["properties"]

    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            # Find control based on strategy
            control = None

            if strategy == "control_type":
                # Find by control type (e.g., "Button", "Edit", "Text")
                control_type = value

                # Build search parameters
                search_params = {"searchDepth": 10}

                # Map control type name to method
                control_class = getattr(auto, f"{control_type}Control", None)
                if control_class:
                    # Add additional property filters
                    for prop_name, prop_value in properties.items():
                        if prop_name in ["Name", "AutomationId", "ClassName"]:
                            search_params[prop_name] = prop_value

                    control = control_class(**search_params)
                    if not control.Exists(0, 0):
                        control = None
                else:
                    # Fallback: search by ControlTypeName
                    for child in parent_control.GetChildren():
                        if child.ControlTypeName == f"{control_type}Control":
                            if _matches_properties(child, properties):
                                control = child
                                break

            elif strategy == "name":
                # Find by Name property
                search_params = {"Name": value, "searchDepth": 10}

                # Add additional filters
                for prop_name, prop_value in properties.items():
                    if prop_name in ["AutomationId", "ClassName", "ControlType"]:
                        search_params[prop_name] = prop_value

                control = parent_control.Control(**search_params)
                if not control.Exists(0, 0):
                    control = None

            elif strategy == "automation_id":
                # Find by AutomationId
                search_params = {"AutomationId": value, "searchDepth": 10}

                # Add additional filters
                for prop_name, prop_value in properties.items():
                    if prop_name in ["Name", "ClassName", "ControlType"]:
                        search_params[prop_name] = prop_value

                control = parent_control.Control(**search_params)
                if not control.Exists(0, 0):
                    control = None

            elif strategy == "class_name":
                # Find by ClassName
                search_params = {"ClassName": value, "searchDepth": 10}

                # Add additional filters
                for prop_name, prop_value in properties.items():
                    if prop_name in ["Name", "AutomationId", "ControlType"]:
                        search_params[prop_name] = prop_value

                control = parent_control.Control(**search_params)
                if not control.Exists(0, 0):
                    control = None

            # If control found and matches all properties, return it
            if control and control.Exists(0, 0):
                if _matches_properties(control, properties):
                    logger.info(f"Found element: {control.ControlTypeName} - '{control.Name}'")
                    return DesktopElement(control)

        except Exception as e:
            logger.debug(f"Element search attempt failed: {e}")

        time.sleep(0.1)

    # Timeout
    error_msg = f"Element not found with selector: {selector} (timeout: {timeout}s)"
    logger.error(error_msg)
    raise ValueError(error_msg)


def find_elements(
    parent_control: auto.Control, selector: Dict[str, Any], max_depth: int = 10
) -> List[DesktopElement]:
    """
    Find all elements matching selector.

    Args:
        parent_control: Parent UI Automation control to search within
        selector: Selector dictionary
        max_depth: Maximum search depth

    Returns:
        List of DesktopElement objects (may be empty)
    """
    logger.debug(f"Finding all elements with selector: {selector}")

    # Parse selector
    parsed = parse_selector(selector)
    strategy = parsed["strategy"]
    value = parsed["value"]
    properties = parsed["properties"]

    elements = []

    try:
        # Recursively search children
        def search_children(control, depth=0):
            if depth > max_depth:
                return

            for child in control.GetChildren():
                # Check if child matches selector
                matches = False

                if strategy == "control_type":
                    matches = child.ControlTypeName == f"{value}Control"
                elif strategy == "name":
                    matches = child.Name == value
                elif strategy == "automation_id":
                    matches = child.AutomationId == value
                elif strategy == "class_name":
                    matches = child.ClassName == value

                # Check additional properties
                if matches and properties:
                    matches = _matches_properties(child, properties)

                if matches:
                    elements.append(DesktopElement(child))

                # Recurse
                search_children(child, depth + 1)

        search_children(parent_control)

        logger.info(f"Found {len(elements)} elements matching selector")

    except Exception as e:
        logger.warning(f"Error during element search: {e}")

    return elements


def _matches_properties(control: auto.Control, properties: Dict[str, Any]) -> bool:
    """
    Check if control matches all specified properties.

    Args:
        control: UI Automation control
        properties: Dictionary of property name -> expected value

    Returns:
        True if all properties match
    """
    if not properties:
        return True

    try:
        for prop_name, expected_value in properties.items():
            actual_value = getattr(control, prop_name, None)

            # Handle ControlType specially (might need "Control" suffix)
            if prop_name == "ControlType" and not expected_value.endswith("Control"):
                expected_value = f"{expected_value}Control"

            if actual_value != expected_value:
                return False

        return True

    except Exception as e:
        logger.debug(f"Property matching failed: {e}")
        return False
