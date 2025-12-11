"""Visual nodes for scripts category."""

from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode
from casare_rpa.domain.value_objects.types import DataType

# Import logic layer nodes
from casare_rpa.nodes.script_nodes import (
    RunPythonScriptNode,
    RunPythonFileNode,
    EvalExpressionNode,
    RunBatchScriptNode,
    RunJavaScriptNode,
)


# =============================================================================
# Script Nodes
# =============================================================================


class VisualRunPythonScriptNode(VisualNode):
    """Visual representation of RunPythonScriptNode."""

    __identifier__ = "casare_rpa.scripts"
    NODE_NAME = "Run Python Script"
    NODE_CATEGORY = "scripts"

    def get_node_class(self) -> type:
        return RunPythonScriptNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("code", DataType.STRING)
        self.add_typed_input("variables", DataType.DICT)
        self.add_exec_output("exec_out")
        self.add_typed_output("result", DataType.ANY)
        self.add_typed_output("output", DataType.STRING)
        self.add_typed_output("error", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualRunPythonFileNode(VisualNode):
    """Visual representation of RunPythonFileNode.

    Widgets are auto-generated from RunPythonFileNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.scripts"
    NODE_NAME = "Run Python File"
    NODE_CATEGORY = "scripts"

    def get_node_class(self) -> type:
        return RunPythonFileNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("file_path", DataType.STRING)
        self.add_typed_input("args", DataType.LIST)
        self.add_exec_output("exec_out")
        self.add_typed_output("stdout", DataType.STRING)
        self.add_typed_output("stderr", DataType.STRING)
        self.add_typed_output("return_code", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualEvalExpressionNode(VisualNode):
    """Visual representation of EvalExpressionNode.

    Widgets auto-generated from EvalExpressionNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.scripts"
    NODE_NAME = "Eval Expression"
    NODE_CATEGORY = "scripts"

    def get_node_class(self) -> type:
        return EvalExpressionNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        # expression is now a PropertyDef (auto-generated widget)
        self.add_exec_output("exec_out")
        self.add_typed_output("result", DataType.ANY)
        self.add_typed_output("type", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualRunBatchScriptNode(VisualNode):
    """Visual representation of RunBatchScriptNode.

    Widgets are auto-generated from RunBatchScriptNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.scripts"
    NODE_NAME = "Run Batch Script"
    NODE_CATEGORY = "scripts"

    def get_node_class(self) -> type:
        return RunBatchScriptNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("script", DataType.STRING)
        self.add_typed_input("working_dir", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("stdout", DataType.STRING)
        self.add_typed_output("stderr", DataType.STRING)
        self.add_typed_output("return_code", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualRunJavaScriptNode(VisualNode):
    """Visual representation of RunJavaScriptNode."""

    __identifier__ = "casare_rpa.scripts"
    NODE_NAME = "Run JavaScript"
    NODE_CATEGORY = "scripts"

    def get_node_class(self) -> type:
        return RunJavaScriptNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("code", DataType.STRING)
        self.add_typed_input("variables", DataType.DICT)
        self.add_exec_output("exec_out")
        self.add_typed_output("result", DataType.ANY)
        self.add_typed_output("output", DataType.STRING)
        self.add_typed_output("error", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
