"""
Custom modernized NodeGraph for CasareRPA.

Provides:
- Fixed QUrl handling during file drops.
- File-to-node creation (drop an Excel file -> create ExcelOpenNode).
- Better telemetry for node creation.
"""

import json
import os
from pathlib import Path
from typing import Any, Iterable, Optional, Union

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
    Provides automatic node creation for dropped files.
    """

    def __init__(self, parent: Optional[Any] = None) -> None:
        """Initialize the custom node graph."""
        super().__init__(parent)

    def _on_node_data_dropped(
        self, data: Union[dict, list, QUrl, QMimeData], pos: Union[list, QPoint]
    ) -> None:
        print(f"DEBUG: START _on_node_data_dropped on {self}")
        """
        Handle data dropped onto the graph.

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
                    # Apply fix to avoid TypeError in base class if we call super() later
                    converted_urls = []
                    for url in urls:
                        converted_urls.append(url.toLocalFile() or url.toString())
                    data._converted_paths = converted_urls

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

    def _offset_drop_pos(self, pos: Union[list, QPoint], index: int) -> list:
        """Normalize and offset the drop position for batch drops."""
        if isinstance(pos, QPoint):
            base_pos = [pos.x(), pos.y()]
        elif isinstance(pos, (list, tuple)) and len(pos) >= 2:
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
                from casare_rpa.presentation.canvas.graph.node_registry import (
                    create_node_from_type,
                )

                print(f"DEBUG: Creating node {node_type} for {file_path}")
                node = create_node_from_type(self, node_type, config=config, position=tuple(pos))
                print(f"DEBUG: Created node: {node}")

                if node:
                    # Ensure properties are correctly set if creation didn't use config
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
            if size > MAX_SESSION_FILE_BYTES:
                return False

            with open(file_path, encoding="utf-8") as handle:
                payload = json.load(handle)

            if not isinstance(payload, dict):
                return False
            return isinstance(payload.get("graph"), dict) and isinstance(payload.get("nodes"), dict)
        except Exception as exc:
            logger.debug(f"Drop file not parseable as NodeGraphQt session: {file_path} ({exc})")
            return False

    def create_node(
        self,
        node_type: str,
        name: Optional[str] = None,
        pos: Optional[list] = None,
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


# Apply global class-level patch to NodeGraph to avoid QUrl TypeError crashes
# This ensures that even if NodeGraph is instantiated directly (e.g. in tests or 3rd party scripts),
# the file drop doesn't crash the application.
try:
    from NodeGraphQt.base.graph import NodeGraph as OriginalNodeGraph

    _original_on_node_data_dropped = OriginalNodeGraph._on_node_data_dropped

    def patched_on_node_data_dropped(self, data, pos):
        """Fixed version of _on_node_data_dropped that handles QUrls."""
        # Check if we are a CasareNodeGraph instance - it already implements this with extra logic
        if isinstance(self, CasareNodeGraph):
            return _original_on_node_data_dropped(self, data, pos)

        # For base NodeGraph, apply the QUrl -> string conversion fix before calling original
        if hasattr(data, "urls") and callable(data.urls):
            urls = data.urls()
            if urls:
                converted_urls = []
                for url in urls:
                    if isinstance(url, QUrl):
                        converted_urls.append(url.toLocalFile() or url.toString())
                    else:
                        converted_urls.append(str(url))
                # Inject converted paths into the mime data object to avoid TypeError downstream
                data._converted_paths = converted_urls

        return _original_on_node_data_dropped(self, data, pos)

    OriginalNodeGraph._on_node_data_dropped = patched_on_node_data_dropped
except Exception as e:
    logger.warning(f"Could not patch NodeGraph._on_node_data_dropped: {e}")
