"""
Workflow generator - converts recorded actions into workflow nodes.
"""

from typing import List, Dict, Any, Optional
from loguru import logger

from ..recorder.recording_session import RecordedAction, ActionType
from ..nodes.interaction_nodes import ClickElementNode, TypeTextNode, SelectDropdownNode
from ..nodes.navigation_nodes import GoToURLNode
from ..nodes.wait_nodes import WaitForElementNode


class WorkflowGenerator:
    """Generates workflow nodes from recorded actions."""

    def __init__(self):
        """Initialize workflow generator."""
        self.node_spacing = 150  # Vertical spacing between nodes
        self.start_x = 200
        self.start_y = 100

        logger.info("Workflow generator initialized")

    def generate_workflow(
        self,
        actions: List[RecordedAction],
        start_position: Optional[Dict[str, int]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Generate workflow nodes from recorded actions.

        Args:
            actions: List of recorded actions
            start_position: Optional start position for nodes

        Returns:
            List of node specifications with positions and connections
        """
        if not actions:
            logger.warning("No actions to generate workflow from")
            return []

        start_x = start_position["x"] if start_position else self.start_x
        start_y = start_position["y"] if start_position else self.start_y

        nodes = []
        current_y = start_y

        for i, action in enumerate(actions):
            node_spec = self._action_to_node(action, i, start_x, current_y)
            if node_spec:
                nodes.append(node_spec)
                current_y += self.node_spacing

        # Connect nodes sequentially
        for i in range(len(nodes) - 1):
            nodes[i]["connections"] = [i + 1]

        logger.info(
            f"Generated workflow with {len(nodes)} nodes from {len(actions)} actions"
        )
        return nodes

    def _action_to_node(
        self, action: RecordedAction, index: int, x: int, y: int
    ) -> Optional[Dict[str, Any]]:
        """
        Convert a recorded action to a node specification.

        Args:
            action: Recorded action
            index: Action index
            x: X position
            y: Y position

        Returns:
            Node specification dictionary
        """
        node_spec = {
            "index": index,
            "position": {"x": x, "y": y},
            "connections": [],
            "config": {},
        }

        if action.action_type == ActionType.CLICK:
            node_spec["type"] = "ClickElement"
            node_spec["node_class"] = ClickElementNode
            node_spec["config"] = {
                "selector": action.selector,
            }
            # Create descriptive name from element info
            element_label = self._get_element_label(action)
            node_spec["name"] = f"Click {element_label}"

        elif action.action_type == ActionType.TYPE:
            node_spec["type"] = "TypeText"
            node_spec["node_class"] = TypeTextNode
            node_spec["config"] = {
                "selector": action.selector,
                "text": action.value or "",
            }
            # Create descriptive name showing target and text
            element_label = self._get_element_label(action)
            text_preview = self._truncate_text(action.value)
            node_spec["name"] = f"Type '{text_preview}' in {element_label}"

        elif action.action_type == ActionType.SELECT:
            node_spec["type"] = "SelectDropdown"
            node_spec["node_class"] = SelectDropdownNode
            node_spec["config"] = {
                "selector": action.selector,
                "value": action.value or "",
            }
            node_spec["name"] = f"Select: {action.value}"

        elif action.action_type == ActionType.NAVIGATE:
            node_spec["type"] = "GoToURL"
            node_spec["node_class"] = GoToURLNode
            node_spec["config"] = {
                "url": action.url,
            }
            node_spec["name"] = f"Navigate: {self._truncate_url(action.url)}"

        elif action.action_type == ActionType.WAIT:
            node_spec["type"] = "WaitForElement"
            node_spec["node_class"] = WaitForElementNode
            node_spec["config"] = {
                "selector": action.selector,
                "timeout": 30000,
            }
            node_spec["name"] = f"Wait: {self._truncate_selector(action.selector)}"

        else:
            logger.warning(f"Unknown action type: {action.action_type}")
            return None

        logger.debug(f"Created node spec: {node_spec['type']} at ({x}, {y})")
        return node_spec

    def _truncate_selector(self, selector: str, max_length: int = 30) -> str:
        """Truncate selector for display."""
        if not selector:
            return "..."
        if len(selector) <= max_length:
            return selector
        return selector[:max_length] + "..."

    def _get_element_label(self, action: RecordedAction) -> str:
        """Generate a descriptive label for an element from action metadata."""
        # Try to get element text content first
        if hasattr(action, "element_text") and action.element_text:
            text = action.element_text.strip()
            if text and len(text) < 40:
                return f"'{text}'"

        # Try element ID
        if hasattr(action, "element_id") and action.element_id:
            return f"#{action.element_id}"

        # Try element tag + class
        if hasattr(action, "element_tag"):
            label = action.element_tag
            if hasattr(action, "element_class") and action.element_class:
                label += f".{action.element_class.split()[0]}"
            if label != "div":  # Only return if it's somewhat meaningful
                return label

        # Fallback to truncated selector
        return self._truncate_selector(action.selector, max_length=25)

    def _truncate_text(self, text: Optional[str], max_length: int = 20) -> str:
        """Truncate text for display."""
        if not text:
            return "..."
        if len(text) <= max_length:
            return text
        return text[:max_length] + "..."

    def _truncate_url(self, url: Optional[str], max_length: int = 40) -> str:
        """Truncate URL for display."""
        if not url:
            return "..."
        if len(url) <= max_length:
            return url
        return url[:max_length] + "..."
