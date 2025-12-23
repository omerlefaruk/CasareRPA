"""
Custom NodeGraph subclass for CasareRPA.

Overrides internal methods of NodeGraphQt.NodeGraph to provide:
- Enhanced drag-drop support (File/URL handling)
- Better node creation telemetry
- Custom signal routing
"""

import json
import os
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from loguru import logger
from NodeGraphQt import NodeGraph
from PySide6.QtCore import QMimeData, QPoint, QUrl

from casare_rpa.nodes.file.super_node import FileSystemAction
from casare_rpa.presentation.canvas.telemetry import log_canvas_event

MAX_SESSION_FILE_BYTES = 5 * 1024 * 1024


class CasareNodeGraph(NodeGraph):
    """
    Enhanced NodeGraph with CasareRPA specific behaviors.

    Modernizes monkey-patches previously applied to NodeGraph class.
    """

    def __init__(self, parent: Any | None = None) -> None:
        """Initialize the custom node graph."""
        super().__init__(parent)

    def _on_node_data_dropped(
        self, data: dict | list | QUrl | QMimeData, pos: list | QPoint
    ) -> None:
        """
        Handle data dropped onto the graph.

        Modernized replacement for CasareNodeDataDropFix.
        Supports:
        - Node type dictionaries (Internal NodeGraphQt format)
        - QMimeData (standard Qt drag payload)
        - QUrl objects (File drag-drop from Explorer)
        - Lists of URLs (Batch drag-drop)
        """
        # 1. Handle standard NodeGraphQt node type data
        if isinstance(data, dict) and "node_type" in data:
            try:
                # Use standard implementation for node types
                super()._on_node_data_dropped(data, pos)
                return
            except Exception as e:
                logger.error(f"Failed to drop node type: {e}")

        # 2. Handle QMimeData drops (standard Qt payload)
        if isinstance(data, QMimeData):
            if data.hasUrls():
                urls = [url for url in data.urls() if url is not None]
                local_urls = [url for url in urls if url.toLocalFile()]
                if local_urls:
                    for index, url in enumerate(local_urls):
                        local_path = url.toLocalFile()
                        if not local_path:
                            continue
                        drop_pos = self._offset_drop_pos(pos, index)
                        self._handle_file_drop(local_path, drop_pos)
                    return

            # Preserve NodeGraphQt's default behavior for non-file drops.
            try:
                super()._on_node_data_dropped(data, pos)
            except Exception as e:
                logger.error(f"Failed to process dropped data: {e}")
            return

        # 3. Handle File/URL drops (CasareRPA specific enhancement)
        urls = []
        if isinstance(data, QUrl):
            urls = [data]
        elif isinstance(data, list):
            urls = [item for item in data if isinstance(item, QUrl)]
        else:
            # Check for generic item list (sometimes passed from viewer)
            try:
                if isinstance(data, Iterable):
                    urls = [item for item in data if hasattr(item, "toLocalFile")]
            except Exception:
                pass

        if not urls:
            logger.debug(f"Unsupported data format dropped: {type(data)}")
            return

        # Process each URL
        for i, url in enumerate(urls):
            local_path = url.toLocalFile()
            if not local_path:
                continue

            # Adjust position for batch drops
            drop_pos = self._offset_drop_pos(pos, i)
            self._handle_file_drop(local_path, drop_pos)

    def _offset_drop_pos(self, pos: list | QPoint, index: int) -> list:
        """Normalize and offset the drop position for batch drops."""
        if isinstance(pos, QPoint):
            base_pos = [pos.x(), pos.y()]
        elif isinstance(pos, list | tuple) and len(pos) >= 2:
            base_pos = [pos[0], pos[1]]
        else:
            base_pos = [0, 0]
        return [base_pos[0] + (index * 40), base_pos[1] + (index * 40)]

    def _handle_file_drop(self, file_path: str, pos: list) -> None:
        """
        Create appropriate node based on dropped file type.

        Args:
            file_path: Absolute path to the dropped file
            pos: [x, y] position in scene
        """
        ext = os.path.splitext(file_path)[1].lower()
        node_type = None
        config: dict[str, object] = {}

        # Determine node type from extension
        if self._is_nodegraph_session_file(file_path, ext):
            try:
                self.import_session(file_path)
                logger.info(f"Imported NodeGraphQt session from drop: {Path(file_path).name}")
                return
            except Exception as e:
                logger.error(f"Failed to import session from {file_path}: {e}")

        if ext in (".xlsx", ".xls"):
            node_type = "ExcelOpenNode"
            config = {"file_path": file_path}
        else:
            node_type = "FileSystemSuperNode"
            config = {
                "action": FileSystemAction.READ.value,
                "file_path": file_path,
            }

        if node_type:
            try:
                # Use CasareRPA's creation helper to link visual and domain nodes
                from casare_rpa.presentation.canvas.graph.node_registry import create_node_from_type

                node = create_node_from_type(self, node_type, config=config, position=tuple(pos))

                if node:
                    if node_type == "FileSystemSuperNode":
                        node.set_property("action", FileSystemAction.READ.value, push_undo=False)
                        node.set_property("file_path", file_path, push_undo=False)
                    else:
                        node.set_property("file_path", file_path, push_undo=False)

                    logger.info(f"Created {node_type} from dropped file: {Path(file_path).name}")
                    log_canvas_event(
                        "file_dropped_create_node",
                        file_ext=ext,
                        node_type=node_type,
                    )
            except Exception as e:
                logger.error(f"Failed to create node from dropped file {file_path}: {e}")
        else:
            logger.debug(f"No node type mapped for extension: {ext}")

    def _is_nodegraph_session_file(self, file_path: str, ext: str) -> bool:
        """Return True if a dropped file looks like a NodeGraphQt session."""
        if ext not in (".json", ".graph"):
            return False
        try:
            size = os.path.getsize(file_path)
        except OSError as exc:
            logger.debug(f"Drop file size unavailable: {file_path} ({exc})")
            return False
        if size > MAX_SESSION_FILE_BYTES:
            logger.debug(f"Drop file too large for session import: {file_path}")
            return False
        try:
            with open(file_path, encoding="utf-8") as handle:
                payload = json.load(handle)
        except Exception as exc:
            logger.debug(f"Drop file not parseable as NodeGraphQt session: {file_path} ({exc})")
            return False
        if not isinstance(payload, dict):
            return False
        return isinstance(payload.get("graph"), dict) and isinstance(payload.get("nodes"), dict)

    def create_node(
        self,
        node_type: str,
        name: str | None = None,
        pos: list | None = None,
        **kwargs,
    ) -> Any:
        """
        Override create_node to add telemetry.
        """
        node = super().create_node(node_type, name=name, pos=pos, **kwargs)
        if node:
            log_canvas_event(
                "node_created_manual",
                node_type=node_type,
                node_id=node.id if hasattr(node, "id") else "unknown",
            )
        return node
