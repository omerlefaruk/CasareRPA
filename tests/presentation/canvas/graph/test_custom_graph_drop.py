import os
from pathlib import Path
from typing import Any

import pytest
from PySide6.QtCore import QMimeData, QPoint, QUrl

from casare_rpa.presentation.canvas.graph.node_graph_widget import NodeGraphWidget
from casare_rpa.presentation.canvas.graph.node_registry import get_node_registry
from casare_rpa.presentation.canvas.visual_nodes.file_operations.super_nodes import (
    VisualFileSystemSuperNode,
)
from casare_rpa.presentation.canvas.visual_nodes.office_automation.nodes import (
    VisualExcelOpenNode,
)


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def _make_graph(qtbot: Any):
    widget = NodeGraphWidget()
    qtbot.addWidget(widget)
    graph = widget.graph
    registry = get_node_registry()
    registry.register_node(VisualExcelOpenNode, graph)
    registry.register_node(VisualFileSystemSuperNode, graph)
    return graph, widget


def _make_drop_mime(path: Path) -> QMimeData:
    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile(str(path))])
    return mime


@pytest.mark.parametrize("ext", [".xlsx", ".xls"])
def test_drop_excel_creates_excel_open(qtbot: Any, tmp_path: Path, ext: str) -> None:
    graph, _widget = _make_graph(qtbot)
    file_path = tmp_path / f"book{ext}"
    file_path.write_text("dummy")

    graph._on_node_data_dropped(_make_drop_mime(file_path), QPoint(120, 240))

    excel_nodes = [node for node in graph.all_nodes() if isinstance(node, VisualExcelOpenNode)]
    assert len(excel_nodes) == 1
    assert Path(excel_nodes[0].get_property("file_path")) == file_path


@pytest.mark.parametrize("ext", [".json", ".xml", ".txt"])
def test_drop_file_creates_file_system_read(qtbot: Any, tmp_path: Path, ext: str) -> None:
    graph, _widget = _make_graph(qtbot)
    file_path = tmp_path / f"data{ext}"
    file_path.write_text("dummy")

    graph._on_node_data_dropped(_make_drop_mime(file_path), QPoint(80, 160))

    file_nodes = [node for node in graph.all_nodes() if isinstance(node, VisualFileSystemSuperNode)]
    assert len(file_nodes) == 1
    assert file_nodes[0].get_property("action") == "Read File"
    assert Path(file_nodes[0].get_property("file_path")) == file_path
