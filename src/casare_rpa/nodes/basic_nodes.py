"""
Basic node implementations for CasareRPA.

This module provides fundamental nodes that form the building blocks
of any workflow: StartNode, EndNode, and CommentNode.
"""

from ..core.base_node import BaseNode
from ..core.types import NodeStatus, PortType, ExecutionResult
from ..core.execution_context import ExecutionContext


class StartNode(BaseNode):
    """
    Start node - entry point for workflow execution.

    Every workflow must have exactly one StartNode. This node has no inputs,
    only an execution output to begin the workflow chain.
    """

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
        # Start node has no inputs, only execution output
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)

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
            # Start nodes simply mark the beginning of execution
            # No actual work to do
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
        # Start node has no configuration requirements
        return True, ""


class EndNode(BaseNode):
    """
    End node - exit point for workflow execution.

    Workflows can have multiple EndNodes. This node has only an execution
    input and no outputs. It marks the termination of a workflow branch.
    """

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
        # End node has no outputs, only execution input
        self.add_input_port("exec_in", PortType.EXEC_INPUT)

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
            # End nodes mark the completion of execution
            # Generate execution summary if desired
            summary = context.get_execution_summary()

            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"message": "Workflow completed", "summary": summary},
                "next_nodes": [],  # No next nodes - this is the end
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
        # End node has no configuration requirements
        return True, ""


class CommentNode(BaseNode):
    """
    Comment node - documentation and annotation for workflows.

    CommentNodes are non-executable nodes used to add documentation,
    notes, or section headers within a workflow. They don't affect
    execution and are skipped during workflow runs.
    """

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
        # Comment nodes have no ports - they're documentation only
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
            "data": {"comment": self.config.get("comment", ""), "skipped": True},
            "next_nodes": [],
        }

    def _validate_config(self) -> tuple[bool, str]:
        """
        Validate node configuration.

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Comment nodes are always valid
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
        return self.config.get("comment", "")
