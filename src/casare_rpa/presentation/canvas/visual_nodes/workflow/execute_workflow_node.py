"""
VisualExecuteWorkflowNode - Visual representation for ExecuteWorkflowNode.
"""

from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode
from casare_rpa.presentation.canvas.graph.node_widgets import NodeFilePathWidget


def _replace_widget(node: VisualNode, widget) -> None:
    """
    Replace auto-generated widget with custom widget.

    If a property already exists (from @properties auto-generation),
    remove it first to avoid NodePropertyError conflicts.

    Args:
        node: The visual node
        widget: The custom widget to add (NodeFilePathWidget)
    """
    prop_name = widget._name  # NodeBaseWidget stores name as _name
    # Remove existing property if it was auto-generated from schema
    if hasattr(node, "model") and prop_name in node.model.custom_properties:
        del node.model.custom_properties[prop_name]
        # Also remove from widgets dict if present
        if hasattr(node, "_widgets") and prop_name in node._widgets:
            del node._widgets[prop_name]
    # Now safely add our custom widget
    node.add_custom_widget(widget)
    widget.setParentItem(node.view)


class VisualExecuteWorkflowNode(VisualNode):
    """
    Visual node for executing a standard workflow JSON file.
    """

    __identifier__ = "casare_rpa.workflow"
    NODE_NAME = "Execute Workflow"
    NODE_CATEGORY = "Workflow"

    def __init__(self):
        super().__init__()

        # Add file picker for workflow path (using _replace_widget pattern from file_operations)
        _replace_widget(
            self,
            NodeFilePathWidget(
                name="workflow_path",
                label="Workflow File",
                file_filter="Workflow Files (*.json);;All Files (*.*)",
                placeholder="Select workflow file...",
            ),
        )

    def setup_ports(self) -> None:
        """Setup node ports."""
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")
        self.add_exec_output("error")
