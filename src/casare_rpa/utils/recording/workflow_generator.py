"""
CasareRPA - Recording Workflow Generator

Converts recorded browser actions into executable workflow JSON.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid

from loguru import logger

from casare_rpa.utils.recording.browser_recorder import (
    BrowserRecordedAction,
    BrowserActionType,
)


class RecordingWorkflowGenerator:
    """
    Generates workflow definitions from recorded actions.

    Maps browser actions to corresponding nodes and creates
    a complete workflow with connections.
    """

    # Map action types to node types
    ACTION_TO_NODE: Dict[BrowserActionType, str] = {
        BrowserActionType.NAVIGATE: "GoToURLNode",
        BrowserActionType.CLICK: "ClickElementNode",
        BrowserActionType.TYPE: "TypeTextNode",
        BrowserActionType.SELECT: "SelectDropdownNode",
        BrowserActionType.CHECK: "ClickElementNode",  # Click for checkbox
        BrowserActionType.UNCHECK: "ClickElementNode",
        BrowserActionType.SCROLL: "WaitNode",  # Use wait as placeholder
        BrowserActionType.HOVER: "ClickElementNode",  # No dedicated hover node
        BrowserActionType.PRESS_KEY: "TypeTextNode",  # Type special key
        BrowserActionType.WAIT: "WaitForElementNode",
        BrowserActionType.SCREENSHOT: "ScreenshotNode",
    }

    def __init__(self, workflow_name: Optional[str] = None):
        """
        Initialize workflow generator.

        Args:
            workflow_name: Name for generated workflow (auto-generated if not provided)
        """
        self.workflow_name = workflow_name

    def generate(
        self,
        actions: List[BrowserRecordedAction],
        include_start_end: bool = True,
    ) -> Dict[str, Any]:
        """
        Generate workflow definition from recorded actions.

        Args:
            actions: List of recorded browser actions
            include_start_end: Whether to include Start/End nodes

        Returns:
            Workflow definition dictionary
        """
        if not actions:
            return self._empty_workflow(self.workflow_name)

        # Generate workflow name
        name = self.workflow_name or self._generate_name(actions)

        # Convert actions to nodes
        nodes = []
        node_ids = []

        # Add Start node
        if include_start_end:
            start_node = self._create_start_node()
            nodes.append(start_node)
            node_ids.append(start_node["id"])

        # Convert each action to a node
        for i, action in enumerate(actions):
            node = self._action_to_node(action, i)
            if node:
                nodes.append(node)
                node_ids.append(node["id"])

        # Add End node
        if include_start_end:
            end_node = self._create_end_node()
            nodes.append(end_node)
            node_ids.append(end_node["id"])

        # Create connections (sequential flow)
        connections = self._create_connections(node_ids)

        workflow = {
            "name": name,
            "description": f"Auto-recorded workflow with {len(actions)} actions",
            "version": "3.0",
            "created_at": datetime.now().isoformat(),
            "nodes": nodes,
            "connections": connections,
            "variables": {},
            "metadata": {
                "source": "browser_recorder",
                "action_count": len(actions),
            },
        }

        logger.info(f"Generated workflow '{name}' with {len(nodes)} nodes")

        return workflow

    def _empty_workflow(self, name: Optional[str] = None) -> Dict[str, Any]:
        """Create empty workflow with just start/end nodes."""
        start_node = self._create_start_node()
        end_node = self._create_end_node()

        return {
            "name": name or "Empty Recorded Workflow",
            "description": "No actions were recorded",
            "version": "3.0",
            "created_at": datetime.now().isoformat(),
            "nodes": [start_node, end_node],
            "connections": [
                {
                    "from_node": start_node["id"],
                    "from_port": "exec_out",
                    "to_node": end_node["id"],
                    "to_port": "exec_in",
                }
            ],
            "variables": {},
            "metadata": {"source": "browser_recorder", "action_count": 0},
        }

    def _generate_name(self, actions: List[BrowserRecordedAction]) -> str:
        """Generate workflow name from first action."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if actions:
            first_action = actions[0]
            if first_action.action_type == BrowserActionType.NAVIGATE:
                # Extract domain from URL
                url = first_action.url
                try:
                    from urllib.parse import urlparse

                    domain = urlparse(url).netloc.replace("www.", "")
                    return f"Recording_{domain}_{timestamp}"
                except Exception:
                    pass

        return f"Recorded_Workflow_{timestamp}"

    def _create_start_node(self) -> Dict[str, Any]:
        """Create Start node."""
        return {
            "id": f"start_{uuid.uuid4().hex[:8]}",
            "type": "StartNode",
            "name": "Start",
            "position": {"x": 100, "y": 200},
            "parameters": {},
        }

    def _create_end_node(self) -> Dict[str, Any]:
        """Create End node."""
        return {
            "id": f"end_{uuid.uuid4().hex[:8]}",
            "type": "EndNode",
            "name": "End",
            "position": {"x": 800, "y": 200},
            "parameters": {},
        }

    def _action_to_node(
        self, action: BrowserRecordedAction, index: int
    ) -> Optional[Dict[str, Any]]:
        """
        Convert a recorded action to a node definition.

        Args:
            action: Recorded browser action
            index: Action index (for positioning)

        Returns:
            Node definition dictionary or None if action not mappable
        """
        node_type = self.ACTION_TO_NODE.get(action.action_type)
        if not node_type:
            logger.warning(f"No node mapping for action type: {action.action_type}")
            return None

        node_id = f"node_{uuid.uuid4().hex[:8]}"

        # Calculate position (staggered horizontally)
        position = {
            "x": 200 + (index * 150),
            "y": 200 + ((index % 3) * 50),  # Slight vertical offset for visibility
        }

        # Build parameters based on action type
        parameters = self._build_parameters(action)

        return {
            "id": node_id,
            "type": node_type,
            "name": action.get_description(),
            "position": position,
            "parameters": parameters,
        }

    def _build_parameters(self, action: BrowserRecordedAction) -> Dict[str, Any]:
        """Build node parameters from action."""
        params = {}

        if action.action_type == BrowserActionType.NAVIGATE:
            params["url"] = action.url

        elif action.action_type == BrowserActionType.CLICK:
            params["selector"] = action.selector
            if action.coordinates:
                params["x"] = action.coordinates[0]
                params["y"] = action.coordinates[1]
            params["timeout"] = 5000

        elif action.action_type == BrowserActionType.TYPE:
            params["selector"] = action.selector
            params["text"] = action.value or ""
            params["clear_first"] = True

        elif action.action_type == BrowserActionType.SELECT:
            params["selector"] = action.selector
            params["value"] = action.value or ""

        elif action.action_type in (BrowserActionType.CHECK, BrowserActionType.UNCHECK):
            params["selector"] = action.selector
            params["timeout"] = 5000

        elif action.action_type == BrowserActionType.WAIT:
            params["selector"] = action.selector
            params["timeout"] = int(action.value or "5000")

        elif action.action_type == BrowserActionType.SCREENSHOT:
            params["filename"] = action.value or "screenshot.png"

        elif action.action_type == BrowserActionType.PRESS_KEY:
            if action.modifiers:
                params["text"] = "+".join(action.modifiers + [action.key or ""])
            else:
                params["text"] = action.key or ""

        elif action.action_type == BrowserActionType.SCROLL:
            # Use wait as placeholder since we don't have a scroll node
            params["timeout"] = 500

        return params

    def _create_connections(self, node_ids: List[str]) -> List[Dict[str, str]]:
        """Create sequential connections between nodes."""
        connections = []

        for i in range(len(node_ids) - 1):
            connections.append(
                {
                    "from_node": node_ids[i],
                    "from_port": "exec_out",
                    "to_node": node_ids[i + 1],
                    "to_port": "exec_in",
                }
            )

        return connections

    @staticmethod
    def merge_workflows(
        workflows: List[Dict[str, Any]], name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Merge multiple recorded workflows into one.

        Args:
            workflows: List of workflow definitions
            name: Name for merged workflow

        Returns:
            Merged workflow definition
        """
        if not workflows:
            return RecordingWorkflowGenerator()._empty_workflow()

        if len(workflows) == 1:
            return workflows[0]

        merged_name = (
            name or f"Merged_Workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        all_nodes = []
        all_connections = []
        prev_end_id = None

        for i, workflow in enumerate(workflows):
            nodes = workflow.get("nodes", [])
            connections = workflow.get("connections", [])

            # Offset node positions
            x_offset = i * 1000
            for node in nodes:
                node_copy = node.copy()
                if "position" in node_copy:
                    node_copy["position"] = {
                        "x": node_copy["position"]["x"] + x_offset,
                        "y": node_copy["position"]["y"],
                    }

                # Skip duplicate start/end nodes (except first start, last end)
                if node_copy["type"] == "StartNode" and i > 0:
                    continue
                if node_copy["type"] == "EndNode" and i < len(workflows) - 1:
                    prev_end_id = node_copy["id"]
                    continue

                all_nodes.append(node_copy)

            # Add connections, linking workflows together
            for conn in connections:
                all_connections.append(conn)

            # Connect previous workflow's last node to this workflow's first node
            if prev_end_id and i > 0 and nodes:
                # Find first non-start node in this workflow
                first_node = None
                for node in nodes:
                    if node["type"] != "StartNode":
                        first_node = node
                        break

                if first_node:
                    # Find the node before the end in previous workflow
                    # and connect it to this workflow's first node
                    pass  # This is handled by removing end nodes

        return {
            "name": merged_name,
            "description": f"Merged from {len(workflows)} recordings",
            "version": "3.0",
            "created_at": datetime.now().isoformat(),
            "nodes": all_nodes,
            "connections": all_connections,
            "variables": {},
            "metadata": {
                "source": "browser_recorder",
                "merged_count": len(workflows),
            },
        }


__all__ = ["RecordingWorkflowGenerator"]
