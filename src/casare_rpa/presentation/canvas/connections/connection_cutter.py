"""
Connection cutter for node graph.

Provides Houdini-style connection cutting: hold Y and drag LMB
to slice through connection lines and disconnect them.
"""

from loguru import logger
from NodeGraphQt import NodeGraph
from PySide6.QtCore import QLineF, QObject, QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainterPath, QPen
from PySide6.QtWidgets import QGraphicsItem, QGraphicsPathItem

from casare_rpa.presentation.canvas.ui.theme import Theme


class ConnectionCutter(QObject):
    """
    Manages connection cutting via Y + LMB drag.

    Hold Y key and drag with left mouse button to draw a cutting line.
    Any connections that intersect with the cutting line will be disconnected
    when the mouse is released.
    """

    def __init__(self, graph: NodeGraph, parent: QObject | None = None):
        """
        Initialize the connection cutter.

        Args:
            graph: NodeGraph instance to manage
            parent: Optional parent QObject
        """
        super().__init__(parent)

        self._graph = graph
        self._active = True
        self._cutting = False
        self._y_pressed = False
        self._cut_start: QPointF | None = None
        self._cut_path: list[QPointF] = []
        self._path_item: QGraphicsPathItem | None = None

        # Setup event filters
        self._setup_event_filters()

    def _setup_event_filters(self):
        """Setup event filters to monitor Y key + mouse drag."""
        try:
            viewer = self._graph.viewer()
            if viewer:
                # Install on viewer for key events and mouse events
                viewer.installEventFilter(self)

                # Install on viewport for mouse events (viewport gets raw mouse events)
                # Note: Key events go to viewer, not viewport
                if hasattr(viewer, "viewport"):
                    viewport = viewer.viewport()
                    if viewport:
                        viewport.installEventFilter(self)
        except Exception as e:
            logger.warning(f"Could not setup connection cutter event filters: {e}")

    def set_active(self, active: bool):
        """Enable or disable the connection cutter."""
        self._active = active
        if not active:
            self._cancel_cut()

    def is_active(self) -> bool:
        """Check if connection cutter is active."""
        return self._active

    def eventFilter(self, watched, event):
        """Filter events to detect Y + LMB drag for cutting."""
        if not self._active:
            return super().eventFilter(watched, event)

        try:
            from PySide6.QtCore import QEvent
            from PySide6.QtGui import QKeyEvent, QMouseEvent

            # Track Y key state (only process key events from viewer, not viewport)
            # This prevents duplicate processing since filter is installed on both
            viewer = self._graph.viewer()
            is_viewer_event = watched == viewer

            if event.type() == QEvent.Type.KeyPress:
                # Only handle key events from the viewer
                if is_viewer_event and isinstance(event, QKeyEvent) and event.key() == Qt.Key.Key_Y:
                    self._y_pressed = True
                    self._set_cut_cursor(True)
                    # Don't consume - let other handlers see it too
                    return False

            elif event.type() == QEvent.Type.KeyRelease:
                # Only handle key events from the viewer
                if is_viewer_event and isinstance(event, QKeyEvent) and event.key() == Qt.Key.Key_Y:
                    # Don't finish cut on Y release - let mouse release finish it
                    # Just clear the Y flag so new cuts can't start without re-pressing Y
                    self._y_pressed = False
                    self._set_cut_cursor(False)
                    return False

            # Handle mouse events for cutting (from both viewer and viewport)
            elif event.type() == QEvent.Type.MouseButtonPress:
                if isinstance(event, QMouseEvent):
                    if event.button() == Qt.MouseButton.LeftButton and self._y_pressed:
                        self._start_cut(event.position())
                        return True  # Consume mouse press to prevent node selection

            elif event.type() == QEvent.Type.MouseMove:
                # Continue cutting even if Y was released (only require mouse to be down)
                if isinstance(event, QMouseEvent):
                    if self._cutting:
                        self._update_cut(event.position())
                        return True  # Consume mouse move during cutting

            elif event.type() == QEvent.Type.MouseButtonRelease:
                if isinstance(event, QMouseEvent):
                    if event.button() == Qt.MouseButton.LeftButton and self._cutting:
                        self._finish_cut()
                        return True  # Consume mouse release

        except Exception as e:
            logger.error(f"Error in connection cutter event filter: {e}")

        return super().eventFilter(watched, event)

    def _set_cut_cursor(self, cutting: bool):
        """Set cursor to indicate cut mode."""
        try:
            viewer = self._graph.viewer()
            if viewer:
                if cutting:
                    viewer.setCursor(Qt.CursorShape.CrossCursor)
                else:
                    viewer.setCursor(Qt.CursorShape.ArrowCursor)
        except Exception:
            pass

    def _start_cut(self, pos):
        """Start a new cut operation."""
        try:
            viewer = self._graph.viewer()
            if not viewer:
                return

            scene_pos = viewer.mapToScene(pos.toPoint())

            self._cutting = True
            self._cut_start = scene_pos
            self._cut_path = [scene_pos]

            self._create_cut_visual(scene_pos)
            logger.debug(f"Started cutting at {scene_pos.x():.0f}, {scene_pos.y():.0f}")

        except Exception as e:
            logger.error(f"Error starting cut: {e}")

    def _update_cut(self, pos):
        """Update the cut line as mouse moves."""
        try:
            viewer = self._graph.viewer()
            if not viewer or not self._cutting:
                return

            scene_pos = viewer.mapToScene(pos.toPoint())
            self._cut_path.append(scene_pos)
            self._update_cut_visual(scene_pos)

        except Exception as e:
            logger.error(f"Error updating cut: {e}")

    def _finish_cut(self):
        """Finish cutting and disconnect intersecting connections."""
        try:
            if not self._cutting:
                return

            cut_count = self._cut_intersecting_connections()

            if cut_count > 0:
                logger.info(f"Cut {cut_count} connection(s)")

            self._cancel_cut()

        except Exception as e:
            logger.error(f"Error finishing cut: {e}")
            self._cancel_cut()

    def _cancel_cut(self):
        """Cancel current cut operation and clean up."""
        self._cutting = False
        self._cut_start = None
        self._cut_path = []
        self._remove_cut_visual()

    def _create_cut_visual(self, start_pos: QPointF):
        """Create the visual cutting line/path."""
        try:
            viewer = self._graph.viewer()
            if not viewer or not viewer.scene():
                return

            scene = viewer.scene()

            self._path_item = QGraphicsPathItem()

            cut_color = QColor(Theme.get_colors().error)
            cut_color.setAlpha(220)
            pen = QPen(cut_color)
            pen.setWidth(3)
            pen.setStyle(Qt.PenStyle.SolidLine)
            self._path_item.setPen(pen)

            path = QPainterPath()
            path.moveTo(start_pos)
            self._path_item.setPath(path)

            self._path_item.setZValue(10000)
            scene.addItem(self._path_item)

        except Exception as e:
            logger.error(f"Error creating cut visual: {e}")

    def _update_cut_visual(self, current_pos: QPointF):
        """Update the visual cutting path."""
        try:
            if not self._path_item or not self._cut_path:
                return

            path = QPainterPath()
            path.moveTo(self._cut_path[0])

            for point in self._cut_path[1:]:
                path.lineTo(point)

            path.lineTo(current_pos)
            self._path_item.setPath(path)

        except Exception as e:
            logger.error(f"Error updating cut visual: {e}")

    def _remove_cut_visual(self):
        """Remove the visual cutting elements."""
        try:
            viewer = self._graph.viewer()
            if viewer and viewer.scene() and self._path_item:
                viewer.scene().removeItem(self._path_item)
            self._path_item = None
        except Exception:
            pass

    def _cut_intersecting_connections(self) -> int:
        """
        Find and disconnect all connections that intersect with the cut path.

        Returns:
            Number of connections cut
        """
        cut_count = 0

        try:
            if len(self._cut_path) < 2:
                logger.debug("Cut path too short")
                return 0

            viewer = self._graph.viewer()
            if not viewer or not viewer.scene():
                logger.debug("No viewer or scene")
                return 0

            scene = viewer.scene()

            # Build cut line segments
            cut_segments = []
            for i in range(len(self._cut_path) - 1):
                cut_segments.append(QLineF(self._cut_path[i], self._cut_path[i + 1]))

            logger.debug(f"Cut path has {len(cut_segments)} segments")

            # Find all pipe-like items in the scene
            pipes_to_cut: list[tuple] = []
            # Deduplication set: (source_node_id, source_port, target_node_id, target_port)
            connections_seen: set[tuple] = set()
            pipe_classes_found = set()

            for item in scene.items():
                class_name = item.__class__.__name__
                module_name = item.__class__.__module__

                # Collect all unique class names for debugging
                if "pipe" in class_name.lower() or "Pipe" in class_name:
                    pipe_classes_found.add(f"{module_name}.{class_name}")

                # Check if this is a pipe/connection item (various naming conventions)
                is_pipe = (
                    "Pipe" in class_name
                    or "pipe" in class_name.lower()
                    or "Connection" in class_name
                    or "Edge" in class_name
                )

                if is_pipe:
                    # Check if cut path intersects this pipe
                    intersects = self._item_intersects_cut(item, cut_segments)

                    if intersects:
                        # Get view-level port items from pipe
                        input_port_item = None
                        output_port_item = None

                        if hasattr(item, "input_port"):
                            input_port_item = item.input_port
                        if hasattr(item, "output_port"):
                            output_port_item = item.output_port

                        if input_port_item and output_port_item:
                            # Get port names for deduplication
                            out_name = self._get_port_name(output_port_item)
                            in_name = self._get_port_name(input_port_item)

                            # Get node IDs for deduplication
                            source_node_item = (
                                output_port_item.parentItem()
                                if hasattr(output_port_item, "parentItem")
                                else None
                            )
                            target_node_item = (
                                input_port_item.parentItem()
                                if hasattr(input_port_item, "parentItem")
                                else None
                            )

                            if source_node_item and target_node_item:
                                source_node_id = (
                                    source_node_item.id if hasattr(source_node_item, "id") else None
                                )
                                target_node_id = (
                                    target_node_item.id if hasattr(target_node_item, "id") else None
                                )

                                # Create deduplication key
                                conn_key = (source_node_id, out_name, target_node_id, in_name)

                                if conn_key not in connections_seen:
                                    connections_seen.add(conn_key)
                                    pipes_to_cut.append((output_port_item, input_port_item, item))
                                    logger.info(f"Found pipe to cut: {class_name}")
                                else:
                                    logger.debug(f"Skipping duplicate connection: {conn_key}")
                            else:
                                logger.warning(
                                    f"Pipe {class_name} has no node items: "
                                    f"source={source_node_item}, target={target_node_item}"
                                )
                        else:
                            logger.warning(
                                f"Pipe {class_name} has no ports: "
                                f"in={input_port_item}, out={output_port_item}"
                            )

            if pipe_classes_found:
                logger.debug(f"Pipe classes in scene: {pipe_classes_found}")

            logger.info(f"Found {len(pipes_to_cut)} pipes to cut")

            # Disconnect the pipes using MODEL-LEVEL ports (not view-level)
            # This is critical - view-level disconnect doesn't update model state
            for output_port_item, input_port_item, _pipe_item in pipes_to_cut:
                try:
                    # Get port names from view-level port items
                    out_name = self._get_port_name(output_port_item)
                    in_name = self._get_port_name(input_port_item)

                    if not out_name or not in_name:
                        logger.warning(f"Could not get port names: out={out_name}, in={in_name}")
                        continue

                    # Get node items from port items via parentItem()
                    source_node_item = (
                        output_port_item.parentItem()
                        if hasattr(output_port_item, "parentItem")
                        else None
                    )
                    target_node_item = (
                        input_port_item.parentItem()
                        if hasattr(input_port_item, "parentItem")
                        else None
                    )

                    if not source_node_item or not target_node_item:
                        logger.warning("Could not get node items from port items")
                        continue

                    # Get node IDs from the view items
                    source_node_id = (
                        source_node_item.id if hasattr(source_node_item, "id") else None
                    )
                    target_node_id = (
                        target_node_item.id if hasattr(target_node_item, "id") else None
                    )

                    if not source_node_id or not target_node_id:
                        logger.warning("Could not get node IDs from node items")
                        continue

                    # Find MODEL-level nodes by ID using graph.all_nodes()
                    source_node = None
                    target_node = None

                    for model_node in self._graph.all_nodes():
                        node_id = model_node.id() if callable(model_node.id) else model_node.id
                        if node_id == source_node_id:
                            source_node = model_node
                        elif node_id == target_node_id:
                            target_node = model_node

                        if source_node and target_node:
                            break

                    if not source_node or not target_node:
                        logger.warning(
                            f"Could not find model nodes: "
                            f"source={source_node_id}, target={target_node_id}"
                        )
                        continue

                    # Get MODEL-level ports using node's get_input/get_output methods
                    source_port = source_node.get_output(out_name)
                    target_port = target_node.get_input(in_name)

                    if not source_port:
                        logger.warning(f"Could not get output port '{out_name}' from source node")
                        continue
                    if not target_port:
                        logger.warning(f"Could not get input port '{in_name}' from target node")
                        continue

                    # Disconnect using MODEL-level ports
                    source_port.disconnect_from(target_port)
                    cut_count += 1
                    logger.info(f"Cut connection: {out_name} -> {in_name}")

                except Exception as e:
                    logger.error(f"Failed to disconnect: {e}")
                    import traceback

                    logger.debug(traceback.format_exc())

            # If no pipes found via scene items, try iterating through nodes
            if len(pipes_to_cut) == 0:
                logger.debug("No pipes found in scene, trying node iteration method")
                cut_count = self._cut_via_node_iteration(cut_segments)

        except Exception as e:
            logger.error(f"Error cutting connections: {e}")
            import traceback

            logger.error(traceback.format_exc())

        return cut_count

    def _get_port_name(self, port_item) -> str | None:
        """Get the name of a port from a port view item."""
        if port_item is None:
            return None

        # Method 1: name() method (most common)
        if hasattr(port_item, "name"):
            if callable(port_item.name):
                return port_item.name()
            return str(port_item.name)

        # Method 2: _name attribute
        if hasattr(port_item, "_name"):
            return str(port_item._name)

        return None

    def _cut_via_node_iteration(self, cut_segments: list[QLineF]) -> int:
        """
        Alternative method: iterate through all nodes and check their connections.

        This is a fallback if scene item detection doesn't work.
        """
        cut_count = 0

        try:
            connections_to_cut = []

            # Iterate through all nodes
            for node in self._graph.all_nodes():
                # Check output ports
                for out_port in node.output_ports():
                    connected_ports = out_port.connected_ports()

                    for in_port in connected_ports:
                        # Get positions of both ports
                        out_pos = self._get_port_position(out_port)
                        in_pos = self._get_port_position(in_port)

                        if out_pos and in_pos:
                            # Check if cut line intersects this connection
                            conn_line = QLineF(out_pos, in_pos)

                            for cut_seg in cut_segments:
                                # PySide6 intersects() returns tuple: (IntersectionType, QPointF)
                                result = cut_seg.intersects(conn_line)
                                if isinstance(result, tuple):
                                    intersect_type, _ = result
                                else:
                                    intersect_type = result

                                if intersect_type == QLineF.IntersectionType.BoundedIntersection:
                                    connections_to_cut.append((out_port, in_port))
                                    logger.info(
                                        f"Found connection to cut via iteration: {out_port.name()} -> {in_port.name()}"
                                    )
                                    break

            logger.info(f"Node iteration found {len(connections_to_cut)} connections to cut")

            # Disconnect
            for out_port, in_port in connections_to_cut:
                try:
                    out_port.disconnect_from(in_port)
                    cut_count += 1
                    logger.info(f"Cut connection: {out_port.name()} -> {in_port.name()}")
                except Exception as e:
                    logger.error(f"Failed to disconnect: {e}")

        except Exception as e:
            logger.error(f"Error in node iteration cut: {e}")
            import traceback

            logger.error(traceback.format_exc())

        return cut_count

    def _get_port_position(self, port) -> QPointF | None:
        """Get the scene position of a port."""
        try:
            if hasattr(port, "view") and port.view:
                rect = port.view.boundingRect()
                center = rect.center()
                return port.view.mapToScene(center)

            # Alternative: get from node position
            if hasattr(port, "node") and callable(port.node):
                node = port.node()
                if node and hasattr(node, "view") and node.view:
                    # Estimate port position from node
                    node_rect = node.view.sceneBoundingRect()
                    # Output ports are on right, input on left
                    if hasattr(port, "port_type"):
                        port_type = port.port_type()
                        if port_type == 0:  # Input
                            return QPointF(node_rect.left(), node_rect.center().y())
                        else:  # Output
                            return QPointF(node_rect.right(), node_rect.center().y())
                    return node_rect.center()
        except Exception as e:
            logger.debug(f"Error getting port position: {e}")

        return None

    def _item_intersects_cut(self, item: QGraphicsItem, cut_segments: list[QLineF]) -> bool:
        """
        Check if a graphics item intersects with the cut path.

        Uses multiple methods for robust intersection detection.
        """
        try:
            # Method 1: Use bounding rect intersection (fast check)
            item_rect = item.sceneBoundingRect()

            # Quick rejection: check if any cut segment is near the bounding rect
            rect_intersects = False
            for seg in cut_segments:
                if self._line_intersects_rect(seg, item_rect):
                    rect_intersects = True
                    break

            if not rect_intersects:
                return False

            # Method 2: Use path intersection for accuracy
            # Get the pipe's path if available
            if hasattr(item, "path") and callable(item.path):
                pipe_path = item.path()
                if not pipe_path.isEmpty():
                    # Create a stroked path from cut segments
                    from PySide6.QtGui import QPainterPathStroker

                    cut_path = QPainterPath()
                    if cut_segments:
                        cut_path.moveTo(cut_segments[0].p1())
                        for seg in cut_segments:
                            cut_path.lineTo(seg.p2())

                    # Stroke the cut path to give it width
                    stroker = QPainterPathStroker()
                    stroker.setWidth(8)  # Wider for easier cutting
                    stroked_cut = stroker.createStroke(cut_path)

                    # Map pipe path to scene coordinates
                    scene_pipe_path = item.mapToScene(pipe_path)

                    if scene_pipe_path.intersects(stroked_cut):
                        return True

            # Method 3: Check shape intersection
            item_shape = item.shape()
            if not item_shape.isEmpty():
                scene_shape = item.mapToScene(item_shape)

                for seg in cut_segments:
                    cut_path = QPainterPath()
                    cut_path.moveTo(seg.p1())
                    cut_path.lineTo(seg.p2())

                    from PySide6.QtGui import QPainterPathStroker

                    stroker = QPainterPathStroker()
                    stroker.setWidth(10)
                    stroked = stroker.createStroke(cut_path)

                    if scene_shape.intersects(stroked):
                        return True

            # Fallback: bounding rect intersection is enough
            return rect_intersects

        except Exception as e:
            logger.debug(f"Error checking intersection: {e}")
            # On error, use bounding rect as fallback
            try:
                item_rect = item.sceneBoundingRect()
                for seg in cut_segments:
                    if self._line_intersects_rect(seg, item_rect):
                        return True
            except Exception:
                pass
            return False

    def _line_intersects_rect(self, line: QLineF, rect: QRectF) -> bool:
        """Check if a line segment intersects a rectangle."""
        try:
            # Check all four edges of the rectangle
            edges = [
                QLineF(rect.topLeft(), rect.topRight()),
                QLineF(rect.topRight(), rect.bottomRight()),
                QLineF(rect.bottomRight(), rect.bottomLeft()),
                QLineF(rect.bottomLeft(), rect.topLeft()),
            ]

            for edge in edges:
                # PySide6 intersects() returns tuple: (IntersectionType, QPointF)
                result = line.intersects(edge)
                if isinstance(result, tuple):
                    intersect_type, _ = result
                else:
                    intersect_type = result

                if intersect_type == QLineF.IntersectionType.BoundedIntersection:
                    return True

            # Also check if line is entirely inside rect
            if rect.contains(line.p1()) or rect.contains(line.p2()):
                return True

            return False
        except Exception:
            return False
