"""
Desktop Selector Strategy Generator

Auto-generates multiple selector strategies for desktop UI elements
with confidence scoring and validation.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
from loguru import logger
import uiautomation as auto

from ...desktop.element import DesktopElement


class ConfidenceLevel(Enum):
    """Confidence level for selector reliability"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class SelectorStrategy:
    """
    Represents a single selector strategy with metadata
    """
    strategy: str  # "automation_id", "name", "control_type", etc.
    value: str
    properties: Dict[str, Any]  # Additional properties for filtering
    confidence: ConfidenceLevel
    score: float  # 0-100
    is_unique: bool = False
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to selector dictionary format"""
        selector = {
            "strategy": self.strategy,
            "value": self.value
        }
        if self.properties:
            selector["properties"] = self.properties
        return selector


def generate_selectors(element: DesktopElement, parent_control: Optional[auto.Control] = None) -> List[SelectorStrategy]:
    """
    Generate multiple selector strategies for a desktop element.

    Strategies (in priority order):
    1. AutomationId - Most reliable if available
    2. Name - Good for buttons, labels
    3. ControlType + Name - Specific matching
    4. ControlType + Index - Fallback
    5. Path-based - Hierarchical selector

    Args:
        element: DesktopElement to generate selectors for
        parent_control: Optional parent control for relative selectors

    Returns:
        List of SelectorStrategy objects, sorted by confidence/score
    """
    logger.debug(f"Generating selectors for element: {element}")

    strategies = []

    # Get element properties
    automation_id = element.get_property("AutomationId")
    name = element.get_property("Name")
    control_type = element.get_property("ControlTypeName")
    class_name = element.get_property("ClassName")

    # Remove "Control" suffix from control type for cleaner selectors
    if control_type and control_type.endswith("Control"):
        control_type_clean = control_type[:-7]  # Remove "Control"
    else:
        control_type_clean = control_type

    # Strategy 1: AutomationId (highest priority)
    if automation_id:
        strategies.append(SelectorStrategy(
            strategy="automation_id",
            value=automation_id,
            properties={},
            confidence=ConfidenceLevel.HIGH,
            score=95.0,
            description=f"By AutomationId: {automation_id}"
        ))
        logger.debug(f"Generated AutomationId strategy: {automation_id}")

    # Strategy 2: Name (if available and meaningful)
    if name and len(name) > 0 and name.strip():
        # Check if name looks unique (not generic like "OK" or "Button")
        is_generic = name.lower() in ["ok", "cancel", "yes", "no", "button", "text", "edit"]

        strategies.append(SelectorStrategy(
            strategy="name",
            value=name,
            properties={},
            confidence=ConfidenceLevel.MEDIUM if not is_generic else ConfidenceLevel.LOW,
            score=80.0 if not is_generic else 60.0,
            description=f"By Name: {name}"
        ))
        logger.debug(f"Generated Name strategy: {name}")

    # Strategy 3: ControlType + Name (specific combination)
    if control_type and name and name.strip():
        strategies.append(SelectorStrategy(
            strategy="control_type",
            value=control_type_clean,
            properties={"Name": name},
            confidence=ConfidenceLevel.MEDIUM,
            score=75.0,
            description=f"By {control_type_clean} with Name: {name}"
        ))
        logger.debug(f"Generated ControlType+Name strategy: {control_type_clean} / {name}")

    # Strategy 4: ClassName (if available)
    if class_name and class_name.strip():
        strategies.append(SelectorStrategy(
            strategy="class_name",
            value=class_name,
            properties={},
            confidence=ConfidenceLevel.MEDIUM,
            score=70.0,
            description=f"By ClassName: {class_name}"
        ))
        logger.debug(f"Generated ClassName strategy: {class_name}")

    # Strategy 5: ClassName + Name (specific combination)
    if class_name and name and name.strip():
        strategies.append(SelectorStrategy(
            strategy="class_name",
            value=class_name,
            properties={"Name": name},
            confidence=ConfidenceLevel.MEDIUM,
            score=72.0,
            description=f"By {class_name} with Name: {name}"
        ))
        logger.debug(f"Generated ClassName+Name strategy: {class_name} / {name}")

    # Strategy 6: ControlType + AutomationId (very specific)
    if control_type and automation_id:
        strategies.append(SelectorStrategy(
            strategy="control_type",
            value=control_type_clean,
            properties={"AutomationId": automation_id},
            confidence=ConfidenceLevel.HIGH,
            score=98.0,
            description=f"By {control_type_clean} with AutomationId: {automation_id}"
        ))
        logger.debug(f"Generated ControlType+AutomationId strategy")

    # Strategy 7: ControlType + Index (fallback)
    if control_type:
        # Calculate index if parent provided
        index = 0
        if parent_control:
            try:
                index = _calculate_element_index(element, parent_control, control_type_clean)
            except Exception:
                pass

        strategies.append(SelectorStrategy(
            strategy="control_type",
            value=control_type_clean,
            properties={"index": index},
            confidence=ConfidenceLevel.LOW,
            score=40.0,
            description=f"By {control_type_clean} at index {index} (may be fragile)"
        ))
        logger.debug(f"Generated ControlType+Index strategy: {control_type_clean}[{index}]")

    # Strategy 8: Path-based selector (hierarchical)
    if parent_control:
        try:
            path = _generate_path_selector(element)
            if path:
                strategies.append(SelectorStrategy(
                    strategy="xpath",
                    value=path,
                    properties={},
                    confidence=ConfidenceLevel.LOW,
                    score=50.0,
                    description=f"Path-based: {path}"
                ))
                logger.debug(f"Generated path-based strategy: {path}")
        except Exception as e:
            logger.warning(f"Failed to generate path selector: {e}")

    # Sort strategies by score (descending)
    strategies.sort(key=lambda s: s.score, reverse=True)

    logger.info(f"Generated {len(strategies)} selector strategies")
    return strategies


def _calculate_element_index(element: DesktopElement, parent_control: auto.Control, control_type: str) -> int:
    """
    Calculate the index of element among siblings of same control type.

    Args:
        element: Target element
        parent_control: Parent control
        control_type: Control type to match

    Returns:
        Zero-based index
    """
    index = 0
    target_control = element._control

    try:
        for child in parent_control.GetChildren():
            child_type = child.ControlTypeName
            if child_type.endswith("Control"):
                child_type = child_type[:-7]

            if child_type == control_type:
                if child == target_control:
                    return index
                index += 1
    except Exception as e:
        logger.warning(f"Failed to calculate element index: {e}")

    return 0


def _generate_path_selector(element: DesktopElement) -> str:
    """
    Generate a path-based selector (XPath-like).

    Example: "Window[@Name='Calculator']/Pane[@AutomationId='main']/Button[@Name='7']"

    Args:
        element: Target element

    Returns:
        Path string
    """
    try:
        path_parts = []
        current = element._control

        # Walk up to root (max 5 levels)
        for _ in range(5):
            if not current:
                break

            # Get control type
            control_type = current.ControlTypeName
            if control_type.endswith("Control"):
                control_type = control_type[:-7]

            # Build selector for this level
            part = control_type

            # Add identifying attribute
            if current.AutomationId:
                part += f"[@AutomationId='{current.AutomationId}']"
            elif current.Name:
                # Escape single quotes in name
                name = current.Name.replace("'", "\\'")
                part += f"[@Name='{name}']"

            path_parts.insert(0, part)

            # Move to parent
            try:
                parent = current.GetParentControl()
                if not parent or parent == current:
                    break
                current = parent
            except Exception:
                break

        return "/" + "/".join(path_parts) if path_parts else ""

    except Exception as e:
        logger.warning(f"Failed to generate path selector: {e}")
        return ""


def validate_selector_uniqueness(
    selector: SelectorStrategy,
    parent_control: auto.Control,
    timeout: float = 2.0
) -> bool:
    """
    Validate if a selector is unique (finds exactly one element).

    Args:
        selector: SelectorStrategy to validate
        parent_control: Parent control to search within
        timeout: Timeout for search

    Returns:
        True if selector finds exactly one element
    """
    try:
        from ...desktop.selector import find_elements

        # Convert to selector dict
        selector_dict = selector.to_dict()

        # Find all matching elements
        elements = find_elements(parent_control, selector_dict, max_depth=10)

        is_unique = len(elements) == 1
        logger.debug(f"Selector '{selector.description}' found {len(elements)} elements (unique: {is_unique})")

        return is_unique

    except Exception as e:
        logger.warning(f"Failed to validate selector uniqueness: {e}")
        return False


def filter_best_selectors(strategies: List[SelectorStrategy], max_count: int = 5) -> List[SelectorStrategy]:
    """
    Filter to keep only the best selector strategies.

    Args:
        strategies: List of all generated strategies
        max_count: Maximum number to keep

    Returns:
        Filtered list of best strategies
    """
    # Already sorted by score
    # Prefer unique selectors
    unique_strategies = [s for s in strategies if s.is_unique]
    non_unique_strategies = [s for s in strategies if not s.is_unique]

    # Combine: all unique + top non-unique to reach max_count
    result = unique_strategies[:max_count]
    if len(result) < max_count:
        result.extend(non_unique_strategies[:max_count - len(result)])

    logger.debug(f"Filtered to {len(result)} best strategies")
    return result
