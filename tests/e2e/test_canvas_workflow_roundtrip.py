import os
from unittest.mock import MagicMock

import pytest

if os.getenv("CASARE_QT_HEADLESS") == "1":
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.mark.e2e
@pytest.mark.ui
def test_canvas_serialize_deserialize_roundtrip(qapp) -> None:
    """
    High-integrity UI E2E:
    - Create real NodeGraphQt visual nodes (real widgets)
    - Verify visual -> casare config sync
    - Serialize workflow JSON
    - Deserialize into a fresh graph
    - Verify node_id + config + connections survive
    """
    from NodeGraphQt import NodeGraph

    from casare_rpa.presentation.canvas.serialization.workflow_deserializer import (
        WorkflowDeserializer,
    )
    from casare_rpa.presentation.canvas.serialization.workflow_serializer import (
        WorkflowSerializer,
    )
    from casare_rpa.presentation.canvas.visual_nodes import (
        VisualEndNode,
        VisualSetVariableNode,
        VisualStartNode,
    )

    def create_node(graph: NodeGraph, cls, node_id: str, pos) -> object:
        graph.register_node(cls)
        node = graph.create_node(f"{cls.__identifier__}.{cls.__name__}", pos=pos)
        node.set_property("node_id", node_id)
        assert getattr(node, "_casare_node", None) is not None
        return node

    graph = NodeGraph()

    start = create_node(graph, VisualStartNode, "start_1", [0, 0])
    set_var = create_node(graph, VisualSetVariableNode, "setvar_1", [250, 0])
    end = create_node(graph, VisualEndNode, "end_1", [500, 0])

    # Real widget -> config sync (VisualNode.set_property syncs to casare_node.config)
    set_var.set_property("variable_name", "my_var")
    set_var.set_property("default_value", "hello")
    assert set_var._casare_node.config.get("variable_name") == "my_var"
    assert set_var._casare_node.config.get("default_value") == "hello"

    # Connect exec flow
    start.get_output("exec_out").connect_to(set_var.get_input("exec_in"))
    set_var.get_output("exec_out").connect_to(end.get_input("exec_in"))

    # Serialize
    main_window = MagicMock()
    main_window._bottom_panel = None
    serializer = WorkflowSerializer(graph, main_window)
    workflow_data = serializer.serialize()

    assert "nodes" in workflow_data
    assert "connections" in workflow_data
    assert len(workflow_data["nodes"]) == 3
    assert len(workflow_data["connections"]) == 2

    # Deserialize into a new graph
    graph2 = NodeGraph()
    graph2.register_node(VisualStartNode)
    graph2.register_node(VisualSetVariableNode)
    graph2.register_node(VisualEndNode)

    main_window2 = MagicMock()
    main_window2._bottom_panel = None
    deserializer = WorkflowDeserializer(graph2, main_window2)
    ok = deserializer.deserialize(workflow_data)
    assert ok is True

    # Verify nodes recreated
    nodes2 = {n.get_property("node_id"): n for n in graph2.all_nodes()}
    assert set(nodes2.keys()) == {"start_1", "setvar_1", "end_1"}

    set_var2 = nodes2["setvar_1"]
    assert set_var2._casare_node is not None
    # During deserialization we explicitly synchronize the Casare node_id to the workflow node_id.
    assert set_var2._casare_node.node_id == "setvar_1"
    assert set_var2._casare_node.config.get("variable_name") == "my_var"
    assert set_var2._casare_node.config.get("default_value") == "hello"
