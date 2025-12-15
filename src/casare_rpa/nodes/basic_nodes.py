"""
Basic node implementations for CasareRPA.

This module provides fundamental nodes that form the building blocks
of any workflow: StartNode, EndNode, and CommentNode.
"""

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import NodeStatus, ExecutionResult
from casare_rpa.infrastructure.execution import ExecutionContext


@properties()
@node(category="basic")
class StartNode(BaseNode):
    """
    Start node - entry point for workflow execution.

    Every workflow must have exactly one StartNode. This node has no inputs,
    only an execution output to begin the workflow chain.
    """

    # @category: control_flow
    # @requires: none
    # @ports: none -> exec_out

    def __init__(self, node_id: str, name: str = "Start", **kwargs) -> None:
        """
        Initialize start node.

        Args:
            node_id: Unique identifier for this node
            name: Display name for the node
        """
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "StartNode"

    def _define_ports(self) -> None:
        """Define node ports - only execution output."""
        self.add_exec_output("exec_out")

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Execute start node - marks workflow beginning.

        Args:
            context: Execution context for the workflow

        Returns:
            Success result with workflow start message
        """
        self.status = NodeStatus.RUNNING

        try:
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"message": "Workflow started"},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        """
        Validate node configuration.

        Returns:
            Tuple of (is_valid, error_message)
        """
        return True, ""


@properties()
@node(category="basic")
class EndNode(BaseNode):
    """
    End node - exit point for workflow execution.

    Workflows can have multiple EndNodes. This node has only an execution
    input and no outputs. It marks the termination of a workflow branch.
    """

    # @category: control_flow
    # @requires: none
    # @ports: exec_in -> none

    def __init__(self, node_id: str, name: str = "End", **kwargs) -> None:
        """
        Initialize end node.

        Args:
            node_id: Unique identifier for this node
            name: Display name for the node
        """
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "EndNode"

    def _define_ports(self) -> None:
        """Define node ports - only execution input."""
        self.add_exec_input("exec_in")

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Execute end node - marks workflow completion.

        Args:
            context: Execution context for the workflow

        Returns:
            Success result with workflow end message
        """
        self.status = NodeStatus.RUNNING

        try:
            summary = context.get_execution_summary()

            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"message": "Workflow completed", "summary": summary},
                "next_nodes": [],
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        """
        Validate node configuration.

        Returns:
            Tuple of (is_valid, error_message)
        """
        return True, ""


@properties(
    PropertyDef(
        "comment",
        PropertyType.TEXT,
        default="",
        label="Comment",
        tooltip="Documentation or notes for this workflow section",
        placeholder="Enter your comment here...",
    ),
)
@node(category="basic")
class CommentNode(BaseNode):
    """
    Comment node - documentation and annotation for workflows.

    CommentNodes are non-executable nodes used to add documentation,
    notes, or section headers within a workflow. They don't affect
    execution and are skipped during workflow runs.
    """

    # @category: control_flow
    # @requires: none
    # @ports: none -> none

    def __init__(
        self, node_id: str, name: str = "Comment", comment: str = "", **kwargs
    ) -> None:
        """
        Initialize comment node.

        Args:
            node_id: Unique identifier for this node
            name: Display name for the node
            comment: The comment/documentation text
        """
        config = kwargs.get("config", {"comment": comment})
        if "comment" not in config:
            config["comment"] = comment
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "CommentNode"

    def _define_ports(self) -> None:
        """Define node ports - comment nodes have no ports."""
        pass

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Execute comment node - immediately returns success.

        Comment nodes are skipped during execution.

        Args:
            context: Execution context for the workflow

        Returns:
            Success result with comment content
        """
        self.status = NodeStatus.SKIPPED

        return {
            "success": True,
            "data": {"comment": self.get_parameter("comment", ""), "skipped": True},
            "next_nodes": [],
        }

    def _validate_config(self) -> tuple[bool, str]:
        """
        Validate node configuration.

        Returns:
            Tuple of (is_valid, error_message)
        """
        return True, ""

    def set_comment(self, comment: str) -> None:
        """
        Set the comment text.

        Args:
            comment: The comment/documentation text
        """
        self.config["comment"] = comment

    def get_comment(self) -> str:
        """
        Get the comment text.

        Returns:
            The comment text
        """
        return self.get_parameter("comment", "")
