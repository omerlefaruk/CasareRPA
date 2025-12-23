"""
Frame Factory

Factory functions for creating and managing NodeFrames.
Also contains NodeGraphQt-compatible FrameNode class.

Separates creation logic from core frame implementation.
"""

from typing import TYPE_CHECKING, Optional

from NodeGraphQt.base.node import NodeObject
from PySide6.QtCore import QRectF

from casare_rpa.presentation.canvas.graph.style_manager import FRAME_COLORS

if TYPE_CHECKING:
    from casare_rpa.presentation.canvas.graph.node_frame import NodeFrame


class FrameNode(NodeObject):
    """NodeGraphQt-compatible frame node for grouping."""

    __identifier__ = "casare_rpa.frame"
    NODE_NAME = "Frame"

    def __init__(self):
        super().__init__()

        self.create_property("frame_title", "Group", widget_type=0)
        self.create_property("frame_color", "blue", widget_type=3)
        self.create_property("frame_width", 400.0, widget_type=2)
        self.create_property("frame_height", 300.0, widget_type=2)

        self.set_color(0, 0, 0, 0)

    def get_frame_rect(self) -> QRectF:
        """Get the frame's bounding rectangle."""
        width = self.get_property("frame_width")
        height = self.get_property("frame_height")
        pos = self.pos()
        return QRectF(pos[0], pos[1], width, height)


def create_frame(
    graph_view,
    title: str = "Group",
    color_name: str = "blue",
    position: tuple[float, float] = (0, 0),
    size: tuple[float, float] = (400, 300),
    graph=None,
) -> "NodeFrame":
    """
    Create a node frame in the graph view.

    Args:
        graph_view: NodeGraph view to add frame to
        title: Frame title
        color_name: Color theme name from FRAME_COLORS
        position: (x, y) position tuple
        size: (width, height) size tuple
        graph: NodeGraph instance for node lookup (optional)

    Returns:
        Created NodeFrame instance
    """
    from casare_rpa.presentation.canvas.graph.node_frame import NodeFrame

    color = FRAME_COLORS.get(color_name, FRAME_COLORS["gray"])

    if graph is None and hasattr(graph_view, "parent") and graph_view.parent():
        parent = graph_view.parent()
        if hasattr(parent, "graph"):
            graph = parent.graph
        elif hasattr(parent, "_graph"):
            graph = parent._graph

    if graph:
        NodeFrame.set_graph(graph)

    frame = NodeFrame(title=title, color=color, width=size[0], height=size[1])

    scene = graph_view.scene()
    scene.addItem(frame)

    frame.setPos(position[0], position[1])

    return frame


def group_selected_nodes(
    graph_view, title: str = "Group", selected_nodes: list = None
) -> Optional["NodeFrame"]:
    """
    Create a frame around currently selected nodes.

    Args:
        graph_view: NodeGraph viewer
        title: Frame title
        selected_nodes: List of selected nodes (if None, will be fetched)

    Returns:
        Created frame or None if no nodes selected
    """
    if selected_nodes is None:
        if hasattr(graph_view, "selected_nodes"):
            selected_nodes = graph_view.selected_nodes()
        else:
            return None

    if not selected_nodes:
        return None

    min_x = min(node.pos()[0] for node in selected_nodes)
    min_y = min(node.pos()[1] for node in selected_nodes)
    max_x = max(node.pos()[0] + node.view.width for node in selected_nodes)
    max_y = max(node.pos()[1] + node.view.height for node in selected_nodes)

    padding = 30
    padding_top = padding * 3  # Extra space for frame title text
    x = min_x - padding
    y = min_y - padding_top
    width = max_x - min_x + padding * 2
    height = max_y - min_y + padding + padding_top

    frame = create_frame(graph_view, title=title, position=(x, y), size=(width, height))

    for node in selected_nodes:
        frame.add_node(node)

    return frame


def add_frame_menu_actions(graph_menu):
    """
    Add frame-related actions to the graph context menu.

    Args:
        graph_menu: Context menu to add actions to
    """
    from PySide6.QtGui import QAction

    frame_menu = graph_menu.addMenu("Frame")

    group_action = QAction("Group Selected Nodes", graph_menu)
    group_action.triggered.connect(lambda: group_selected_nodes(graph_menu.graph, "Group"))
    frame_menu.addAction(group_action)

    frame_menu.addSeparator()

    for color_name in FRAME_COLORS.keys():
        action = QAction(f"Create {color_name.capitalize()} Frame", graph_menu)
        action.triggered.connect(
            lambda checked, c=color_name: create_frame(
                graph_menu.graph, title="Group", color_name=c, position=(0, 0)
            )
        )
        frame_menu.addAction(action)
