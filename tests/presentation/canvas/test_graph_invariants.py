import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from typing import Any, Dict, List

import pytest
from PySide6.QtCore import QPointF
from NodeGraphQt.qgraphics.pipe import PipeItem

from casare_rpa.presentation.canvas.graph.node_graph_widget import NodeGraphWidget
from casare_rpa.presentation.canvas.graph.node_registry import get_node_registry
from casare_rpa.presentation.canvas.serialization.workflow_serializer import (
    WorkflowSerializer,
)
from casare_rpa.presentation.canvas.serialization.workflow_deserializer import (
    WorkflowDeserializer,
)


class _MainWindowStub:
    def __init__(self) -> None:
        self._current_file = None
        self._bottom_panel = None

    def get_preferences(self) -> Dict[str, object]:
        return {}


def _make_graph_widget(qtbot: Any) -> NodeGraphWidget:
    widget = NodeGraphWidget()
    qtbot.addWidget(widget)
    registry = get_node_registry()
    registry.register_essential_nodes(widget.graph)
    return widget


def _find_identifier(graph: Any, suffix: str) -> str:
    for identifier in graph.registered_nodes():
        if identifier.endswith(suffix):
            return identifier
    raise AssertionError(f"Node identifier not found for suffix: {suffix}")


def _center_on_node(widget: NodeGraphWidget, node: Any, qtbot: Any) -> None:
    viewer = widget.graph.viewer()
    rect = node.view.sceneBoundingRect()
    viewer.centerOn(QPointF(rect.center().x(), rect.center().y()))
    qtbot.wait(30)


def _assert_no_pipes_for_node(scene: Any, node_id: str) -> None:
    for item in scene.items():
        if not isinstance(item, PipeItem):
            continue
        input_port = item.input_port
        output_port = item.output_port
        if input_port and input_port.node and input_port.node.id == node_id:
            raise AssertionError(f"Pipe still references deleted node {node_id}")
        if output_port and output_port.node and output_port.node.id == node_id:
            raise AssertionError(f"Pipe still references deleted node {node_id}")


def test_pan_zoom_does_not_lose_nodes(qtbot: Any) -> None:
    widget = _make_graph_widget(qtbot)
    graph = widget.graph

    start_id = _find_identifier(graph, "VisualStartNode")
    message_id = _find_identifier(graph, "VisualMessageBoxNode")
    end_id = _find_identifier(graph, "VisualEndNode")

    nodes = [
        graph.create_node(start_id, pos=[0, 0]),
        graph.create_node(message_id, pos=[1200, 0]),
        graph.create_node(end_id, pos=[2400, 0]),
        graph.create_node(message_id, pos=[-1200, -800]),
        graph.create_node(message_id, pos=[-2400, 900]),
    ]

    nodes[0].set_output(0, nodes[1].input(0))
    nodes[1].set_output(0, nodes[2].input(0))

    node_ids = [n.id for n in nodes]

    viewer = graph.viewer()
    for _ in range(20):
        viewer.set_zoom(0.2)
        qtbot.wait(20)
        viewer.centerOn(QPointF(2000, 2000))
        qtbot.wait(20)
        viewer.set_zoom(1.0)
        qtbot.wait(20)
        viewer.centerOn(QPointF(0, 0))
        qtbot.wait(20)

    # Model invariant: node ids still exist.
    for node_id in node_ids:
        assert graph.get_node_by_id(node_id) is not None

    # Visibility invariant: return to each node and ensure it becomes visible.
    for node in nodes:
        _center_on_node(widget, node, qtbot)
        assert node.view.isVisible() is True


def test_delete_node_removes_connections_and_undo_redo(qtbot: Any) -> None:
    widget = _make_graph_widget(qtbot)
    graph = widget.graph

    start_id = _find_identifier(graph, "VisualStartNode")
    message_id = _find_identifier(graph, "VisualMessageBoxNode")
    end_id = _find_identifier(graph, "VisualEndNode")

    node_a = graph.create_node(start_id, pos=[0, 0])
    node_b = graph.create_node(message_id, pos=[400, 0])
    node_c = graph.create_node(end_id, pos=[800, 0])

    node_a.set_output(0, node_b.input(0))
    node_b.set_output(0, node_c.input(0))

    viewer = graph.viewer()
    if viewer and viewer.scene():
        viewer.scene().clearSelection()
    if node_b.view:
        node_b.view.setSelected(True)
    qtbot.wait(20)
    assert widget._selection_handler.delete_selected_nodes() is True
    qtbot.wait(50)

    assert graph.get_node_by_id(node_b.id) is None
    assert graph.get_node_by_id(node_c.id) is not None

    scene = graph.viewer().scene()
    _assert_no_pipes_for_node(scene, node_b.id)

    # Undo should restore without phantom pipes.
    graph.undo_stack().undo()
    qtbot.wait(50)
    restored = graph.get_node_by_id(node_b.id)
    assert restored is not None

    # Redo should delete again and keep graph clean.
    graph.undo_stack().redo()
    qtbot.wait(50)
    assert graph.get_node_by_id(node_b.id) is None
    _assert_no_pipes_for_node(scene, node_b.id)


def test_node_titles_stable_across_view_and_roundtrip(qtbot: Any) -> None:
    widget = _make_graph_widget(qtbot)
    graph = widget.graph

    message_id = _find_identifier(graph, "VisualMessageBoxNode")
    node_a = graph.create_node(message_id, pos=[0, 0])
    node_b = graph.create_node(message_id, pos=[600, 0])

    node_a.set_name("Alpha")
    node_b.set_name("Beta")

    viewer = graph.viewer()
    viewer.set_zoom(1.0)
    qtbot.wait(20)

    # Pan/zoom cycles.
    for _ in range(10):
        viewer.set_zoom(0.3)
        qtbot.wait(20)
        viewer.set_zoom(1.0)
        qtbot.wait(20)

    node_a.set_selected(True)
    node_a.set_selected(False)
    node_b.set_name("Gamma")

    assert node_a.view.name == node_a.name()
    assert node_b.view.name == node_b.name()
    assert node_a.view.name
    assert node_b.view.name

    serializer = WorkflowSerializer(graph, _MainWindowStub())
    workflow = serializer.serialize()

    deserializer = WorkflowDeserializer(graph, _MainWindowStub())
    assert deserializer.deserialize(workflow) is True

    names = {n.get_property("node_id"): n.name() for n in graph.all_nodes()}
    assert "Alpha" in names.values()
    assert "Gamma" in names.values()
