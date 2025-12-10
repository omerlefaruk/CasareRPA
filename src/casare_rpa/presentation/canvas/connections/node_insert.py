"""
Node insertion on connection drop.

Allows dragging a node onto an existing connection line to insert it in-between.
Shows visual feedback (orange highlight) when node overlaps a connection.
Automatically spaces nodes apart with 150px gaps when needed.
"""

from typing import Optional, Tuple
import math

from PySide6.QtCore import QObject, Signal, Qt, QRectF, QTimer
from PySide6.QtGui import QPainterPath, QPen, QColor
from NodeGraphQt import NodeGraph, BaseNode

from loguru import logger


# Spacing between nodes after insertion
NODE_GAP = 100


def _get_name(obj) -> str:
    """Get name from object, handling both callable and property."""
    if hasattr(obj, "name"):
        if callable(obj.name):
            return obj.name()
        return str(obj.name)
    return str(obj)


class NodeInsertManager(QObject):
    """
    Manages inserting nodes onto existing connections.

    Features:
    - Detects when a dragged node overlaps an exec connection
    - Highlights the connection with orange color
    - On drop, inserts the node in-between by reconnecting ports
    - Auto-spaces nodes with 150px gaps when too close
    """

    node_inserted = Signal(
        object, object, object
    )  # inserted_node, source_node, target_node

    def __init__(self, graph: NodeGraph, parent: Optional[QObject] = None):
        """Initialize the node insert manager."""
        super().__init__(parent)

        self._graph = graph
        self._active = True
        self._dragging_node: Optional[BaseNode] = None
        self._highlighted_pipe = None
        self._was_dragging = False
        self._original_pen = None  # For restoring PipeItem pen after highlight
        self._drag_start_pos: Optional[Tuple[float, float]] = (
            None  # Track initial position
        )
        self._drag_threshold = 10  # Minimum pixels to move before considering it a drag

        # Use a timer for polling during drag (more reliable than event filters)
        self._drag_timer = QTimer(self)
        self._drag_timer.setInterval(50)  # 20 FPS check
        self._drag_timer.timeout.connect(self._check_drag_state)

        self._setup_event_filters()

    def _setup_event_filters(self):
        """Setup event filters to monitor node dragging."""
        try:
            viewer = self._graph.viewer()
            if viewer:
                # Install on viewport for mouse release detection
                if hasattr(viewer, "viewport"):
                    viewport = viewer.viewport()
                    if viewport:
                        viewport.installEventFilter(self)

            # Timer is NOT started here - only started on demand when dragging begins
            # This saves CPU cycles when idle (was running at 20 FPS continuously)
        except Exception as e:
            logger.warning(f"Could not setup node insert event filters: {e}")

    def set_active(self, active: bool):
        """Enable or disable the node insert feature."""
        self._active = active
        if not active:
            self._clear_highlight()
            self._stop_drag_timer()

    def is_active(self) -> bool:
        """Check if node insert is active."""
        return self._active

    def _start_drag_timer(self):
        """Start the drag monitoring timer (only when needed)."""
        if not self._drag_timer.isActive():
            self._drag_timer.start()

    def _stop_drag_timer(self):
        """Stop the drag monitoring timer to save CPU."""
        if self._drag_timer.isActive():
            self._drag_timer.stop()

    def _check_drag_state(self):
        """Timer callback to check if a node is being dragged over a pipe."""
        if not self._active:
            return

        try:
            # Check if left mouse button is pressed
            from PySide6.QtWidgets import QApplication
            from PySide6.QtCore import Qt

            buttons = QApplication.mouseButtons()
            is_dragging = bool(buttons & Qt.MouseButton.LeftButton)

            selected_nodes = self._graph.selected_nodes()

            if is_dragging and selected_nodes:
                # Check if we're making a connection (not dragging node)
                viewer = self._graph.viewer()
                is_making_connection = (
                    viewer
                    and hasattr(viewer, "_LIVE_PIPE")
                    and viewer._LIVE_PIPE.isVisible()
                )

                if not is_making_connection:
                    node = selected_nodes[0]
                    current_pos = node.pos()

                    # Track initial position when first pressing LMB
                    if self._drag_start_pos is None:
                        self._drag_start_pos = current_pos
                        # Don't highlight yet - wait for actual movement
                    else:
                        # Check if moved beyond threshold (actual drag, not just click)
                        dx = abs(current_pos[0] - self._drag_start_pos[0])
                        dy = abs(current_pos[1] - self._drag_start_pos[1])
                        if dx > self._drag_threshold or dy > self._drag_threshold:
                            self._dragging_node = node
                            self._was_dragging = True
                            self._update_highlight()
                else:
                    # Making connection, clear any highlight
                    if self._highlighted_pipe:
                        self._clear_highlight()
                    self._dragging_node = None
                    self._drag_start_pos = None
            else:
                # Not dragging anymore
                if (
                    self._was_dragging
                    and self._highlighted_pipe
                    and self._dragging_node
                ):
                    # Mouse was released while over a highlighted pipe - INSERT!
                    self._insert_node_on_pipe()

                self._clear_highlight()
                self._dragging_node = None
                self._was_dragging = False
                self._drag_start_pos = None
                # Stop timer when not dragging (saves CPU)
                self._stop_drag_timer()

        except Exception as e:
            logger.error(f"Error in drag state check: {e}")

    def debug_find_pipes(self):
        """Debug method to list all pipes in the scene."""
        pass

    def eventFilter(self, watched, event):
        """Filter events - start timer on mouse press, stop on release."""
        from PySide6.QtCore import QEvent

        if event.type() == QEvent.Type.MouseButtonPress:
            # Start timer when mouse is pressed (potential drag start)
            if self._active:
                self._start_drag_timer()
        elif event.type() == QEvent.Type.MouseButtonRelease:
            # Let timer handle the release logic, it will stop itself
            pass

        return super().eventFilter(watched, event)

    def _update_highlight(self):
        """Update which pipe is highlighted based on dragging node position."""
        if not self._dragging_node:
            return

        try:
            # Get dragging node bounding rect
            node_rect = self._get_node_scene_rect(self._dragging_node)
            if not node_rect:
                logger.debug("Could not get node rect")
                self._clear_highlight()
                return

            # Find intersecting exec pipe
            pipe, distance = self._find_closest_intersecting_exec_pipe(node_rect)

            # Update highlight
            if pipe != self._highlighted_pipe:
                self._clear_highlight()
                if pipe:
                    # Always track the pipe for insertion
                    self._highlighted_pipe = pipe

                    # Try to highlight - CasarePipe has set_insert_highlight method
                    if hasattr(pipe, "set_insert_highlight"):
                        pipe.set_insert_highlight(True)
                    else:
                        # Fallback for regular PipeItem: store original pen and set orange
                        self._original_pen = (
                            pipe.pen() if hasattr(pipe, "pen") else None
                        )
                        if hasattr(pipe, "setPen"):
                            orange_pen = QPen(
                                QColor(255, 140, 0), 4
                            )  # Orange highlight
                            pipe.setPen(orange_pen)
                            pipe.update()

        except Exception as e:
            logger.error(f"Error updating highlight: {e}")
            import traceback

            logger.error(traceback.format_exc())

    def _clear_highlight(self):
        """Clear any highlighted pipe."""
        if self._highlighted_pipe:
            try:
                if hasattr(self._highlighted_pipe, "set_insert_highlight"):
                    self._highlighted_pipe.set_insert_highlight(False)
                elif hasattr(self, "_original_pen") and self._original_pen:
                    # Restore original pen for regular PipeItem
                    if hasattr(self._highlighted_pipe, "setPen"):
                        self._highlighted_pipe.setPen(self._original_pen)
                        self._highlighted_pipe.update()
                    self._original_pen = None
            except Exception:
                pass
            self._highlighted_pipe = None

    def _get_node_scene_rect(self, node: BaseNode) -> Optional[QRectF]:
        """Get the scene bounding rect of a node."""
        try:
            if hasattr(node, "view") and node.view:
                return node.view.sceneBoundingRect()
        except Exception:
            pass
        return None

    def _find_closest_intersecting_exec_pipe(
        self, node_rect: QRectF
    ) -> Tuple[Optional[object], float]:
        """
        Find the exec pipe closest to the node center that intersects with it.

        Returns:
            Tuple of (pipe, distance) or (None, inf) if no intersection
        """
        try:
            viewer = self._graph.viewer()
            if not viewer or not viewer.scene():
                return None, float("inf")

            scene = viewer.scene()
            node_center = node_rect.center()
            closest_pipe = None
            closest_distance = float("inf")

            pipe_count = 0
            exec_pipe_count = 0

            for item in scene.items():
                class_name = item.__class__.__name__

                # Check if this is a pipe
                if "Pipe" not in class_name:
                    continue

                pipe_count += 1

                # Check if it's a complete connection (has both ports)
                if not hasattr(item, "input_port") or not hasattr(item, "output_port"):
                    continue
                if not item.input_port or not item.output_port:
                    continue

                # Check if it's an exec connection
                if not self._is_exec_pipe(item):
                    continue

                exec_pipe_count += 1

                # Check intersection
                if self._node_intersects_pipe(node_rect, item):
                    # Calculate distance to pipe center
                    pipe_center = item.sceneBoundingRect().center()
                    distance = self._calculate_distance(node_center, pipe_center)

                    if distance < closest_distance:
                        closest_distance = distance
                        closest_pipe = item

            return closest_pipe, closest_distance

        except Exception as e:
            logger.error(f"Error finding intersecting pipe: {e}")
            import traceback

            logger.error(traceback.format_exc())
            return None, float("inf")

    def _is_exec_pipe(self, pipe) -> bool:
        """Check if a pipe connects exec ports."""
        try:
            input_port = pipe.input_port
            output_port = pipe.output_port

            # Get port names - handle both callable and property
            in_name = ""
            out_name = ""

            if hasattr(input_port, "name"):
                if callable(input_port.name):
                    in_name = input_port.name().lower()
                else:
                    in_name = str(input_port.name).lower()

            if hasattr(output_port, "name"):
                if callable(output_port.name):
                    out_name = output_port.name().lower()
                else:
                    out_name = str(output_port.name).lower()

            # Check if both are exec ports
            is_exec = "exec" in in_name and "exec" in out_name
            return is_exec

        except Exception:
            return False

    def _node_intersects_pipe(self, node_rect: QRectF, pipe) -> bool:
        """Check if a node bounding rect intersects with a pipe."""
        try:
            # Expand the pipe bounding rect for easier hit detection
            pipe_rect = pipe.sceneBoundingRect()

            # Add padding to make pipes easier to hit (40px each direction)
            expanded_pipe_rect = pipe_rect.adjusted(-40, -40, 40, 40)

            if not node_rect.intersects(expanded_pipe_rect):
                return False

            # For more accurate check, stroke the pipe path to give it width
            if hasattr(pipe, "path") and callable(pipe.path):
                pipe_path = pipe.path()
                if not pipe_path.isEmpty():
                    from PySide6.QtGui import QPainterPathStroker

                    # Create a stroked version of the pipe with 60px width for easy detection
                    stroker = QPainterPathStroker()
                    stroker.setWidth(60)  # Wide hit area
                    stroked_pipe = stroker.createStroke(pipe_path)

                    # Map to scene coordinates
                    scene_pipe_path = pipe.mapToScene(stroked_pipe)

                    # Create a path from the node rect
                    node_path = QPainterPath()
                    node_path.addRect(node_rect)

                    return scene_pipe_path.intersects(node_path)

            # Fallback to expanded bounding rect intersection
            return True

        except Exception as e:
            logger.debug(f"Error checking intersection: {e}")
            return False

    def _calculate_distance(self, p1, p2) -> float:
        """Calculate distance between two points."""
        dx = p1.x() - p2.x()
        dy = p1.y() - p2.y()
        return math.sqrt(dx * dx + dy * dy)

    def _insert_node_on_pipe(self):
        """Insert the dragging node on the highlighted pipe."""
        if not self._dragging_node or not self._highlighted_pipe:
            logger.warning("No dragging node or highlighted pipe")
            return

        try:
            pipe = self._highlighted_pipe
            node = self._dragging_node

            # Get source and target port ITEMS from the pipe (these are view-level)
            source_port_item = pipe.output_port
            target_port_item = pipe.input_port

            if not source_port_item or not target_port_item:
                logger.warning("Pipe missing ports, cannot insert node")
                return

            # Get port names from port items
            source_port_name = _get_name(source_port_item)
            target_port_name = _get_name(target_port_item)

            # Get source and target model nodes from port items
            # Try multiple approaches to get the model node
            source_node = None
            target_node = None

            # Get node items from port items via parentItem()
            # The parentItem of a PortItem is the CasareNodeItem (view)
            # We need to find the model node by ID using graph.all_nodes()
            source_node_item = (
                source_port_item.parentItem()
                if hasattr(source_port_item, "parentItem")
                else None
            )
            target_node_item = (
                target_port_item.parentItem()
                if hasattr(target_port_item, "parentItem")
                else None
            )

            if not source_node_item or not target_node_item:
                logger.warning("Could not get node items from port items")
                return

            # Get node IDs from the view items
            source_node_id = (
                source_node_item.id if hasattr(source_node_item, "id") else None
            )
            target_node_id = (
                target_node_item.id if hasattr(target_node_item, "id") else None
            )

            logger.debug(
                f"Node item IDs: source={source_node_id}, target={target_node_id}"
            )

            if not source_node_id or not target_node_id:
                logger.warning("Could not get node IDs from node items")
                return

            # Find model nodes by ID using graph.all_nodes()
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

            logger.debug(
                f"Found model nodes: source={source_node}, target={target_node}"
            )

            if not source_node or not target_node:
                logger.warning("Could not get source/target model nodes from pipe")
                return

            # Don't insert between the same node or insert onto self
            if source_node == node or target_node == node:
                logger.debug("Cannot insert node onto its own connections")
                return

            # Get the model-level ports using node's get_input/get_output methods
            source_port = source_node.get_output(source_port_name)
            target_port = target_node.get_input(target_port_name)

            if not source_port:
                logger.warning(
                    f"Could not get output port '{source_port_name}' from source node"
                )
                return
            if not target_port:
                logger.warning(
                    f"Could not get input port '{target_port_name}' from target node"
                )
                return

            # Find exec ports on the dragging node
            exec_in, exec_out = self._find_exec_ports(node)

            if not exec_in or not exec_out:
                logger.warning(
                    f"Node {_get_name(node)} has no exec ports, cannot insert"
                )
                return

            # Disconnect existing connection
            disconnected = False
            try:
                source_port.disconnect_from(target_port)
                disconnected = True
            except Exception as e:
                logger.warning(f"Failed to disconnect (trying reverse): {e}")
                # Try reverse
                try:
                    target_port.disconnect_from(source_port)
                    disconnected = True
                except Exception as e2:
                    logger.error(f"Failed reverse disconnect: {e2}")

            if not disconnected:
                logger.error("Could not disconnect original pipe, aborting insert")
                return

            # Connect source -> new node -> target
            connect1_success = False
            connect2_success = False

            logger.info("Port objects before connect:")
            logger.info(
                f"  source_port: {source_port}, type={type(source_port).__name__}"
            )
            logger.info(f"  exec_in: {exec_in}, type={type(exec_in).__name__}")
            logger.info(f"  exec_out: {exec_out}, type={type(exec_out).__name__}")
            logger.info(
                f"  target_port: {target_port}, type={type(target_port).__name__}"
            )

            try:
                source_port.connect_to(exec_in)
                connect1_success = True
                # Verify the connection was made
                connected = source_port.connected_ports()
                logger.info(
                    f"Connected source_port -> exec_in (verified: {exec_in in connected})"
                )
            except Exception as e:
                logger.error(f"Failed to connect source to new node: {e}")
                import traceback

                logger.error(traceback.format_exc())

            try:
                exec_out.connect_to(target_port)
                connect2_success = True
                # Verify the connection was made
                connected = exec_out.connected_ports()
                logger.info(
                    f"Connected exec_out -> target_port (verified: {target_port in connected})"
                )
            except Exception as e:
                logger.error(f"Failed to connect new node to target: {e}")
                import traceback

                logger.error(traceback.format_exc())

            # If connections failed, try to restore original
            if not connect1_success or not connect2_success:
                logger.warning(
                    "Some connections failed, attempting to restore original"
                )
                try:
                    source_port.connect_to(target_port)
                    logger.info("Restored original connection")
                except Exception as e:
                    logger.error(f"Could not restore original connection: {e}")
                return  # Exit early on failure

            # Force visual update - connections are made at model level,
            # but view might need a nudge to create the pipe visuals
            self._force_visual_update()

            # Verify pipe visuals exist after connection
            self._verify_pipe_visuals()

            # Auto-space the nodes
            self._auto_space_nodes(source_node, node, target_node)

            # Force visual update AFTER spacing - pipe paths need to recalculate
            # for new node positions
            self._force_visual_update()

            logger.info(
                f"Successfully inserted {_get_name(node)} between {_get_name(source_node)} and {_get_name(target_node)}"
            )

            # Emit signal
            self.node_inserted.emit(node, source_node, target_node)

        except Exception as e:
            logger.error(f"Error inserting node on pipe: {e}")
            import traceback

            logger.error(traceback.format_exc())

    def _find_exec_ports(
        self, node: BaseNode
    ) -> Tuple[Optional[object], Optional[object]]:
        """Find exec_in and exec_out ports on a node."""
        exec_in = None
        exec_out = None

        try:
            for port in node.input_ports():
                if "exec" in port.name().lower():
                    exec_in = port
                    break

            for port in node.output_ports():
                if "exec" in port.name().lower():
                    exec_out = port
                    break

        except Exception as e:
            logger.debug(f"Error finding exec ports: {e}")

        return exec_in, exec_out

    def _auto_space_nodes(
        self, source_node: BaseNode, new_node: BaseNode, target_node: BaseNode
    ):
        """
        Auto-space nodes to ensure equal 150px gaps between all three.

        Positions: source --150px-- new_node --150px-- target
        Source stays fixed, new_node and target are repositioned.
        """
        try:
            # Get node rects
            source_rect = self._get_node_scene_rect(source_node)
            new_rect = self._get_node_scene_rect(new_node)
            target_rect = self._get_node_scene_rect(target_node)

            if not source_rect or not new_rect or not target_rect:
                return

            # Get current positions
            source_pos = source_node.pos()
            new_pos = new_node.pos()
            target_pos = target_node.pos()

            # Calculate widths
            source_width = source_rect.width()
            new_node_width = new_rect.width()

            # Position new_node: 30px after source's right edge
            # new_node.x = source.x + source_width + NODE_GAP
            new_x = source_pos[0] + source_width + NODE_GAP
            new_node.set_pos(new_x, new_pos[1])

            # Position target: 30px after new_node's right edge
            # target.x = new_node.x + new_node_width + NODE_GAP
            target_x = new_x + new_node_width + NODE_GAP
            target_node.set_pos(target_x, target_pos[1])

            logger.debug(
                f"Spaced nodes: source@{source_pos[0]:.0f}, "
                f"new@{new_x:.0f}, target@{target_x:.0f} (gap={NODE_GAP}px)"
            )

        except Exception as e:
            logger.error(f"Error auto-spacing nodes: {e}")

    def _force_visual_update(self):
        """
        Force the graph view to update and redraw all connections.

        NodeGraphQt sometimes needs a nudge after model-level connections
        to properly render the pipe visuals. We use a small delay to ensure
        the model changes have fully propagated before refreshing the view.
        """
        try:
            # Immediate update
            self._do_visual_update()

            # Schedule another update after a short delay to catch any deferred changes
            QTimer.singleShot(50, self._do_visual_update)
            QTimer.singleShot(100, self._do_visual_update)

        except Exception as e:
            logger.debug(f"Error scheduling visual update: {e}")

    def _do_visual_update(self):
        """Actually perform the visual update."""
        try:
            viewer = self._graph.viewer()
            if not viewer:
                return

            scene = viewer.scene()
            if scene:
                # Force all pipes to recalculate their paths by calling draw_path
                for item in scene.items():
                    class_name = item.__class__.__name__
                    if "Pipe" in class_name:
                        # Trigger path recalculation
                        if hasattr(item, "draw_path"):
                            try:
                                item.draw_path(item.input_port, item.output_port)
                            except Exception:
                                pass
                        # Force the item to update
                        item.update()

                # Invalidate the scene to force a repaint
                scene.invalidate()
                scene.update()

            # Also update the viewport
            if hasattr(viewer, "viewport"):
                viewport = viewer.viewport()
                if viewport:
                    viewport.update()

            # Process pending events to ensure UI updates
            from PySide6.QtWidgets import QApplication

            QApplication.processEvents()

        except Exception as e:
            logger.debug(f"Error in visual update: {e}")

    def _verify_pipe_visuals(self):
        """Verify that pipe visuals exist in the scene after connections."""
        try:
            viewer = self._graph.viewer()
            if not viewer or not viewer.scene():
                return

            scene = viewer.scene()
            pipe_count = 0
            exec_pipe_count = 0

            for item in scene.items():
                class_name = item.__class__.__name__
                if "Pipe" in class_name:
                    pipe_count += 1
                    # Check if it's a complete exec pipe
                    if (
                        hasattr(item, "input_port")
                        and item.input_port
                        and hasattr(item, "output_port")
                        and item.output_port
                    ):
                        if self._is_exec_pipe(item):
                            exec_pipe_count += 1

        except Exception:
            pass
