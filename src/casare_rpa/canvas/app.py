"""
Main application class with qasync integration.

This module provides the CasareRPAApp class which integrates
PySide6 with asyncio using qasync for async workflow execution.
"""

import sys
import asyncio
from typing import Any, Dict, Optional

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from qasync import QEventLoop

from .main_window import MainWindow
from .node_graph_widget import NodeGraphWidget
from .node_registry import get_node_registry
from .selector_integration import SelectorIntegration
from ..runner.workflow_runner import WorkflowRunner
from ..core.workflow_schema import WorkflowSchema, WorkflowMetadata
from ..core.events import EventType, get_event_bus
from ..core.types import NodeStatus
from ..utils.config import setup_logging, APP_NAME
from ..utils.playwright_setup import ensure_playwright_ready
from loguru import logger


class CasareRPAApp:
    """
    Main application class integrating Qt with asyncio.
    
    Uses qasync to bridge PySide6's event loop with Python's asyncio,
    enabling async workflows with Playwright to run within the Qt application.
    """
    
    def __init__(self) -> None:
        """Initialize the application."""
        # Setup logging
        setup_logging()
        logger.info(f"Initializing {APP_NAME}...")
        
        # Enable high-DPI scaling
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling)
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)
        
        # Create Qt application
        self._app = QApplication(sys.argv)
        self._app.setApplicationName(APP_NAME)

        # Check for Playwright browsers and install if needed
        # This happens early so the user sees the dialog before the main window
        logger.info("Checking Playwright browser installation...")
        ensure_playwright_ready(show_gui=True, parent=None)

        # Create qasync event loop
        self._loop = QEventLoop(self._app)
        asyncio.set_event_loop(self._loop)

        # Create main window
        self._main_window = MainWindow()
        
        # Create node graph widget
        self._node_graph = NodeGraphWidget()
        
        # Register nodes with the graph
        node_registry = get_node_registry()
        node_registry.register_all_nodes(self._node_graph.graph)
        logger.info("Registered all node types with graph")

        # Pre-build node mapping to avoid 500ms delay on first node creation
        from .node_registry import get_casare_node_mapping
        get_casare_node_mapping()
        logger.info("Pre-built CasareRPA node mapping")

        # Set node graph as central widget
        self._main_window.set_central_widget(self._node_graph)

        # Setup drag-drop support for importing workflow JSON files
        self._setup_drag_drop_import()

        # Workflow runner
        self._workflow_runner: Optional[WorkflowRunner] = None
        self._workflow_task: Optional[asyncio.Task] = None
        
        # Selector integration (browser element picker)
        self._selector_integration = SelectorIntegration(self._main_window)
        
        # Event bus for execution feedback
        self._event_bus = get_event_bus()
        self._subscribe_to_events()
        
        # Connect signals
        self._connect_signals()
        
        logger.info("Application initialized successfully")
    
    def _subscribe_to_events(self) -> None:
        """Subscribe to workflow execution events for visual feedback."""
        self._event_bus.subscribe(EventType.NODE_STARTED, self._on_node_started)
        self._event_bus.subscribe(EventType.NODE_COMPLETED, self._on_node_completed)
        self._event_bus.subscribe(EventType.NODE_ERROR, self._on_node_error)
        self._event_bus.subscribe(EventType.WORKFLOW_COMPLETED, self._on_workflow_completed)
        self._event_bus.subscribe(EventType.WORKFLOW_ERROR, self._on_workflow_error)
        self._event_bus.subscribe(EventType.WORKFLOW_STOPPED, self._on_workflow_stopped)
        
        # Subscribe to node completion for browser launch detection
        self._event_bus.subscribe(EventType.NODE_COMPLETED, self._check_browser_launch)
        
        # Subscribe all events to log viewer
        log_viewer = self._main_window.get_log_viewer()
        if log_viewer:
            for event_type in EventType:
                self._event_bus.subscribe(event_type, log_viewer.log_event)
    
    def _connect_signals(self) -> None:
        """Connect window signals to handlers."""
        # File operations
        self._main_window.workflow_new.connect(self._on_new_workflow)
        self._main_window.workflow_new_from_template.connect(self._on_new_from_template)
        self._main_window.workflow_open.connect(self._on_open_workflow)
        self._main_window.workflow_import.connect(self._on_import_workflow)
        self._main_window.workflow_import_json.connect(self._on_import_workflow_json)
        self._main_window.workflow_export_selected.connect(self._on_export_selected)
        self._main_window.workflow_save.connect(self._on_save_workflow)
        self._main_window.workflow_save_as.connect(self._on_save_as_workflow)

        # Workflow execution
        self._main_window.workflow_run.connect(self._on_run_workflow)
        self._main_window.workflow_run_to_node.connect(self._on_run_to_node)
        self._main_window.workflow_run_single_node.connect(self._on_run_single_node)
        self._main_window.workflow_pause.connect(self._on_pause_workflow)
        self._main_window.workflow_resume.connect(self._on_resume_workflow)
        self._main_window.workflow_stop.connect(self._on_stop_workflow)
        
        # Edit operations - connect to NodeGraphQt undo stack
        graph = self._node_graph.graph
        undo_stack = graph.undo_stack()
        
        # Enable undo/redo actions and connect them
        self._main_window.action_undo.setEnabled(True)
        self._main_window.action_redo.setEnabled(True)
        self._main_window.action_undo.triggered.connect(undo_stack.undo)
        self._main_window.action_redo.triggered.connect(undo_stack.redo)
        
        # Connect undo stack signals to update action states
        undo_stack.canUndoChanged.connect(self._main_window.action_undo.setEnabled)
        undo_stack.canRedoChanged.connect(self._main_window.action_redo.setEnabled)
        
        # Other edit operations - delete both nodes and frames
        self._main_window.action_delete.triggered.connect(self._on_delete_selected)
        self._main_window.action_cut.triggered.connect(graph.cut_nodes)
        self._main_window.action_copy.triggered.connect(graph.copy_nodes)
        self._main_window.action_paste.triggered.connect(graph.paste_nodes)
        self._main_window.action_select_all.triggered.connect(graph.select_all)
        self._main_window.action_deselect_all.triggered.connect(graph.clear_selection)
        
        # View operations
        self._main_window.action_zoom_in.triggered.connect(self._node_graph.zoom_in)
        self._main_window.action_zoom_out.triggered.connect(self._node_graph.zoom_out)
        self._main_window.action_zoom_reset.triggered.connect(self._node_graph.reset_zoom)
        self._main_window.action_fit_view.triggered.connect(self._node_graph.center_on_nodes)
        
        # Auto-connect toggle
        self._main_window.action_auto_connect.triggered.connect(
            lambda checked: self._node_graph.set_auto_connect_enabled(checked)
        )
        
        # Debug toolbar connections
        debug_toolbar = self._main_window.get_debug_toolbar()
        if debug_toolbar:
            debug_toolbar.debug_mode_toggled.connect(self._on_debug_mode_toggled)
            debug_toolbar.step_mode_toggled.connect(self._on_step_mode_toggled)
            debug_toolbar.step_requested.connect(self._on_step_requested)
            debug_toolbar.continue_requested.connect(self._on_continue_requested)
            debug_toolbar.stop_requested.connect(self._on_stop_workflow)
            debug_toolbar.clear_breakpoints_requested.connect(self._on_clear_breakpoints)
        
        # Variable inspector connections
        variable_inspector = self._main_window.get_variable_inspector()
        if variable_inspector:
            variable_inspector.refresh_requested.connect(self._on_refresh_variables)
        
        # Execution history connections
        execution_history = self._main_window.get_execution_history_viewer()
        if execution_history:
            execution_history.node_selected.connect(self._on_history_node_selected)
            execution_history.clear_requested.connect(self._on_clear_history)
        
        # Selector integration connections
        self._selector_integration.selector_picked.connect(self._on_selector_picked)
        self._selector_integration.recording_complete.connect(self._on_recording_complete)
        self._main_window.action_pick_selector.triggered.connect(self._on_start_selector_picking)
        self._main_window.action_record_workflow.triggered.connect(self._on_toggle_recording)

        # Set workflow data provider for validation
        self._main_window.set_workflow_data_provider(self._get_serialized_workflow_data)

        # Properties panel - connect to node selection changes
        if hasattr(graph, 'node_selected'):
            graph.node_selected.connect(self._on_node_selected_for_properties)
        # Also connect to selection cleared
        if hasattr(graph, 'node_selection_changed'):
            graph.node_selection_changed.connect(self._on_selection_changed_for_properties)

        # Quick actions connections (node right-click context menu)
        quick_actions = self._node_graph.quick_actions
        quick_actions.run_node_requested.connect(self._on_run_single_node)
        quick_actions.run_to_node_requested.connect(self._on_run_to_node)
        quick_actions.copy_requested.connect(graph.copy_nodes)
        quick_actions.duplicate_requested.connect(self._on_duplicate_nodes)
        quick_actions.delete_requested.connect(self._on_delete_selected)

    def _on_duplicate_nodes(self) -> None:
        """Duplicate the selected nodes."""
        graph = self._node_graph.graph
        graph.copy_nodes()
        graph.paste_nodes()
        logger.debug("Duplicated selected nodes")

    def _on_node_selected_for_properties(self, node) -> None:
        """Update properties panel and breadcrumb when a node is selected."""
        self._main_window.update_properties_panel(node)
        # Update breadcrumb
        if node:
            node_name = node.name() if hasattr(node, 'name') else "Node"
            node_id = node.get_property("node_id") if hasattr(node, 'get_property') else None
            self._main_window.update_breadcrumb_node(node_name, node_id)
        else:
            self._main_window.update_breadcrumb_node(None)

    def _on_selection_changed_for_properties(self, selected, deselected) -> None:
        """Handle selection changes for properties panel and breadcrumb."""
        graph = self._node_graph.graph
        selected_nodes = graph.selected_nodes()
        if selected_nodes:
            node = selected_nodes[0]
            self._main_window.update_properties_panel(node)
            # Update breadcrumb
            node_name = node.name() if hasattr(node, 'name') else "Node"
            node_id = node.get_property("node_id") if hasattr(node, 'get_property') else None
            self._main_window.update_breadcrumb_node(node_name, node_id)
        else:
            self._main_window.update_properties_panel(None)
            self._main_window.update_breadcrumb_node(None)

    def _on_delete_selected(self) -> None:
        """
        Delete selected nodes and frames.

        This handles both NodeGraphQt nodes and NodeFrame graphics items.
        """
        from .node_frame import NodeFrame

        graph = self._node_graph.graph
        viewer = graph.viewer()
        scene = viewer.scene()

        # Delete selected frames first
        frames_deleted = 0
        for item in list(scene.selectedItems()):
            if isinstance(item, NodeFrame):
                logger.info(f"Deleting frame: {item.frame_title}")
                item._delete_frame()
                frames_deleted += 1

        # Delete selected nodes
        selected_nodes = graph.selected_nodes()
        if selected_nodes:
            graph.delete_nodes(selected_nodes)
            logger.info(f"Deleted {len(selected_nodes)} nodes")

        if frames_deleted > 0:
            logger.info(f"Deleted {frames_deleted} frames")

    def _get_serialized_workflow_data(self) -> Optional[dict]:
        """
        Get the current workflow as serialized data for validation.

        Returns:
            Workflow data dictionary suitable for validation
        """
        try:
            # Ensure all nodes are valid
            self._ensure_all_nodes_have_casare_nodes()

            # Create workflow from graph
            workflow = self._create_workflow_from_graph()

            if not workflow:
                return None

            # Build serialized workflow data
            serialized_data = {
                "metadata": workflow.metadata.to_dict() if hasattr(workflow.metadata, 'to_dict') else {},
                "nodes": {},
                "connections": [],
                "variables": getattr(workflow, 'variables', {}),
                "settings": getattr(workflow, 'settings', {}),
            }

            # Serialize nodes
            for node_id, node in workflow.nodes.items():
                try:
                    serialized_node = node.serialize()
                    serialized_data["nodes"][node_id] = serialized_node
                except Exception as e:
                    logger.debug(f"Could not serialize node {node_id}: {e}")

            # Serialize connections
            for conn in workflow.connections:
                serialized_data["connections"].append(conn.to_dict())

            return serialized_data

        except Exception as e:
            logger.debug(f"Could not get workflow data for validation: {e}")
            return None

    def _on_new_workflow(self) -> None:
        """Handle new workflow creation."""
        logger.info("Creating new workflow")
        self._node_graph.clear_graph()
        self._main_window.set_modified(False)
    
    def _on_new_from_template(self, template_info) -> None:
        """
        Handle new workflow from template.
        
        Args:
            template_info: TemplateInfo object
        """
        import asyncio
        from casare_rpa.utils.template_loader import get_template_loader
        from qasync import asyncSlot
        
        logger.info(f"Creating workflow from template: {template_info.name}")
        
        # Use qasync to properly handle async in Qt event loop
        async def load_and_apply_template():
            try:
                # Load the template
                loader = get_template_loader()
                
                # Create workflow from template (async) - returns WorkflowSchema with node instances
                workflow_with_instances = await loader.create_workflow_from_template(template_info)
                
                # Convert to serialized format for GUI
                # WorkflowRunner needs instances, but GUI needs serialized data
                from ..core.workflow_schema import WorkflowSchema
                serialized_workflow = WorkflowSchema(workflow_with_instances.metadata)
                
                # Serialize each node instance to dict
                for node_id, node_instance in workflow_with_instances.nodes.items():
                    serialized_workflow.nodes[node_id] = {
                        "node_id": node_instance.node_id,
                        "node_type": node_instance.node_type,
                        "name": getattr(node_instance, 'name', node_instance.node_type),
                        "config": node_instance.config,
                        "position": {"x": 0, "y": 0}  # Default position
                    }
                
                # Copy connections
                serialized_workflow.connections = workflow_with_instances.connections
                
                # Load workflow into graph
                self._load_workflow_to_graph(serialized_workflow)
                
                self._main_window.set_modified(True)
                self._main_window.statusBar().showMessage(f"Loaded template: {template_info.name}", 5000)
                logger.info(f"Successfully loaded template: {template_info.name}")
                
            except Exception as e:
                logger.error(f"Failed to load template {template_info.name}: {e}")
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.critical(
                    self._main_window,
                    "Template Load Error",
                    f"Failed to load template '{template_info.name}':\n\n{str(e)}"
                )
        
        # Schedule the coroutine in the existing event loop
        asyncio.create_task(load_and_apply_template())
    
    def _load_workflow_to_graph(self, workflow: WorkflowSchema) -> None:
        """
        Load a workflow into the node graph.
        
        Args:
            workflow: WorkflowSchema to load
        """
        from .node_registry import get_node_registry
        
        # Import all node classes
        from ..nodes.basic_nodes import StartNode, EndNode
        from ..nodes.variable_nodes import SetVariableNode, GetVariableNode, IncrementVariableNode
        from ..nodes.control_flow_nodes import IfNode, ForLoopNode, WhileLoopNode
        from ..nodes.error_handling_nodes import TryNode, RetryNode
        from ..nodes.wait_nodes import WaitNode, WaitForElementNode, WaitForNavigationNode
        from ..nodes.browser_nodes import LaunchBrowserNode, CloseBrowserNode
        from ..nodes.navigation_nodes import GoToURLNode, GoBackNode, GoForwardNode, RefreshPageNode
        from ..nodes.interaction_nodes import ClickElementNode, TypeTextNode, SelectDropdownNode
        from ..nodes.data_nodes import ExtractTextNode, GetAttributeNode, ScreenshotNode
        from ..nodes.desktop_nodes import LaunchApplicationNode, CloseApplicationNode, ActivateWindowNode, GetWindowListNode
        
        # Map node types to (class, identifier)
        NODE_TYPE_MAP = {
            "StartNode": (StartNode, "casare_rpa.basic"),
            "EndNode": (EndNode, "casare_rpa.basic"),
            "SetVariableNode": (SetVariableNode, "casare_rpa.variable"),
            "GetVariableNode": (GetVariableNode, "casare_rpa.variable"),
            "IncrementVariableNode": (IncrementVariableNode, "casare_rpa.variable"),
            "IfNode": (IfNode, "casare_rpa.control_flow"),
            "ForLoopNode": (ForLoopNode, "casare_rpa.control_flow"),
            "WhileLoopNode": (WhileLoopNode, "casare_rpa.control_flow"),
            "TryNode": (TryNode, "casare_rpa.error_handling"),
            "RetryNode": (RetryNode, "casare_rpa.error_handling"),
            "WaitNode": (WaitNode, "casare_rpa.wait"),
            "WaitForElementNode": (WaitForElementNode, "casare_rpa.wait"),
            "WaitForNavigationNode": (WaitForNavigationNode, "casare_rpa.wait"),
            "LaunchBrowserNode": (LaunchBrowserNode, "casare_rpa.browser"),
            "CloseBrowserNode": (CloseBrowserNode, "casare_rpa.browser"),
            "GoToURLNode": (GoToURLNode, "casare_rpa.navigation"),
            "GoBackNode": (GoBackNode, "casare_rpa.navigation"),
            "GoForwardNode": (GoForwardNode, "casare_rpa.navigation"),
            "RefreshPageNode": (RefreshPageNode, "casare_rpa.navigation"),
            "ClickElementNode": (ClickElementNode, "casare_rpa.interaction"),
            "TypeTextNode": (TypeTextNode, "casare_rpa.interaction"),
            "SelectDropdownNode": (SelectDropdownNode, "casare_rpa.interaction"),
            "ExtractTextNode": (ExtractTextNode, "casare_rpa.data"),
            "GetAttributeNode": (GetAttributeNode, "casare_rpa.data"),
            "ScreenshotNode": (ScreenshotNode, "casare_rpa.data"),
            "LaunchApplicationNode": (LaunchApplicationNode, "casare_rpa.nodes.desktop"),
            "CloseApplicationNode": (CloseApplicationNode, "casare_rpa.nodes.desktop"),
            "ActivateWindowNode": (ActivateWindowNode, "casare_rpa.nodes.desktop"),
            "GetWindowListNode": (GetWindowListNode, "casare_rpa.nodes.desktop"),
        }
        
        graph = self._node_graph.graph
        registry = get_node_registry()
        
        # Clear existing graph
        graph.clear_session()
        
        # Create visual nodes from workflow nodes
        node_map = {}  # Map node_id to visual node
        
        for node_id, node_data in workflow.nodes.items():
            logger.info(f"Loading node {node_id}: keys={list(node_data.keys())}")
            node_type = node_data.get("node_type")
            
            # Get the node class and identifier from mapping
            if node_type in NODE_TYPE_MAP:
                node_class, identifier = NODE_TYPE_MAP[node_type]
                
                # Get the visual node class name
                visual_class_name = f"Visual{node_type}"
                
                # Create visual node in graph
                visual_node = graph.create_node(
                    f"{identifier}.{visual_class_name}"
                )
                
                if visual_node:
                    # Create the underlying CasareRPA node
                    casare_node = node_class(node_id, node_data.get("config", {}))
                    visual_node.set_casare_node(casare_node)
                    
                    # Restore widget values from saved config
                    config = node_data.get("config", {})
                    widgets = visual_node.widgets()
                    for widget_name, widget in widgets.items():
                        if widget_name in config:
                            try:
                                widget.set_value(config[widget_name])
                                logger.info(f"Restored widget {node_id}.{widget_name} = '{config[widget_name]}'")
                            except Exception as e:
                                logger.warning(f"Failed to restore widget {node_id}.{widget_name}: {e}")
                    
                    # Restore node name if available
                    name = node_data.get("name")
                    if name:
                        visual_node.set_name(name)
                        logger.info(f"Restored name for {node_id}: '{name}'")
                    
                    # Set node position if available
                    pos = node_data.get("position")
                    if pos and "x" in pos and "y" in pos:
                        logger.info(f"Restoring position for {node_id}: ({pos['x']}, {pos['y']})")
                        visual_node.set_pos(pos["x"], pos["y"])
                    else:
                        # Auto-arrange nodes that don't have positions
                        index = len(node_map)
                        x = 100 + (index % 4) * 250
                        y = 100 + (index // 4) * 150
                        logger.info(f"Auto-arranging {node_id} at ({x}, {y})")
                        visual_node.set_pos(x, y)
                    
                    node_map[node_id] = visual_node
        
        # Create connections
        for connection in workflow.connections:
            source_visual = node_map.get(connection.source_node)
            target_visual = node_map.get(connection.target_node)
            
            if source_visual and target_visual:
                # Find ports by name
                source_port = None
                target_port = None
                
                for port in source_visual.output_ports():
                    if port.name() == connection.source_port:
                        source_port = port
                        break
                
                for port in target_visual.input_ports():
                    if port.name() == connection.target_port:
                        target_port = port
                        break
                
                if source_port and target_port:
                    source_port.connect_to(target_port)

        # Deserialize frames
        self._deserialize_frames(workflow.frames, node_map)

        logger.info(f"Loaded workflow '{workflow.metadata.name}' with {len(workflow.nodes)} nodes")
    
    def _on_open_workflow(self, file_path: str) -> None:
        """
        Handle workflow opening.
        
        Args:
            file_path: Path to workflow file
        """
        try:
            logger.info(f"Opening workflow: {file_path}")
            
            from pathlib import Path
            workflow = WorkflowSchema.load_from_file(Path(file_path))
            
            # Load workflow into graph
            self._load_workflow_to_graph(workflow)
            
            self._main_window.set_modified(False)
            self._main_window.statusBar().showMessage(f"Opened: {Path(file_path).name}", 3000)
            
        except Exception as e:
            logger.exception("Failed to open workflow")
            self._main_window.statusBar().showMessage(f"Error opening file: {str(e)}", 5000)

    def _on_import_workflow(self, file_path: str) -> None:
        """
        Handle workflow importing/merging.

        Imports nodes from a workflow file into the current canvas.

        Args:
            file_path: Path to workflow file to import
        """
        try:
            import orjson
            from pathlib import Path
            from .workflow_import import import_workflow_data

            logger.info(f"Importing workflow: {file_path}")

            # Load workflow data
            data = orjson.loads(Path(file_path).read_bytes())

            # Prepare for import (remap IDs and position)
            prepared_data, id_mapping = import_workflow_data(
                self._node_graph.graph,
                get_node_factory(),
                data,
                drop_position=None  # Use default offset
            )

            # Create nodes from prepared data
            self._load_workflow_to_graph_merge(prepared_data)

            self._main_window.set_modified(True)
            self._main_window.statusBar().showMessage(
                f"Imported {len(prepared_data.get('nodes', {}))} nodes from {Path(file_path).name}",
                5000
            )

        except Exception as e:
            logger.exception("Failed to import workflow")
            self._main_window.statusBar().showMessage(f"Error importing file: {str(e)}", 5000)

    def _on_import_workflow_json(self, json_text: str) -> None:
        """
        Handle workflow import from JSON string (clipboard paste).

        Args:
            json_text: JSON string containing workflow data
        """
        try:
            import orjson
            from .workflow_import import import_workflow_data

            logger.info("Importing workflow from clipboard JSON")

            # Parse JSON
            data = orjson.loads(json_text)

            # Prepare for import (remap IDs and position)
            prepared_data, id_mapping = import_workflow_data(
                self._node_graph.graph,
                get_node_factory(),
                data,
                drop_position=None  # Use default offset
            )

            # Create nodes from prepared data
            self._load_workflow_to_graph_merge(prepared_data)

            self._main_window.set_modified(True)
            self._main_window.statusBar().showMessage(
                f"Pasted {len(prepared_data.get('nodes', {}))} nodes from clipboard",
                5000
            )

        except Exception as e:
            logger.exception("Failed to import workflow from JSON")
            self._main_window.statusBar().showMessage(f"Error pasting workflow: {str(e)}", 5000)

    def _on_export_selected(self, file_path: str) -> None:
        """
        Handle export selected nodes to file.

        Creates a minimal workflow JSON containing only the selected nodes
        and their internal connections.

        Args:
            file_path: Destination file path
        """
        try:
            import orjson
            from pathlib import Path
            from datetime import datetime

            graph = self._node_graph.graph
            selected_nodes = graph.selected_nodes()

            if not selected_nodes:
                self._main_window.statusBar().showMessage("No nodes selected", 3000)
                return

            # Collect selected node IDs
            selected_ids = set()
            for visual_node in selected_nodes:
                node_id = visual_node.get_property("node_id")
                if node_id:
                    selected_ids.add(node_id)

            logger.info(f"Exporting {len(selected_ids)} selected nodes")

            # Build export data structure
            export_data = {
                "metadata": {
                    "name": f"Exported Nodes",
                    "description": f"Exported {len(selected_ids)} nodes",
                    "created_at": datetime.now().isoformat(),
                    "schema_version": "1.0.0",
                },
                "nodes": {},
                "connections": [],
                "frames": [],
                "variables": {},
                "settings": {},
            }

            # Export nodes
            for visual_node in selected_nodes:
                node_id = visual_node.get_property("node_id")
                if not node_id:
                    continue

                casare_node = visual_node.get_casare_node() if hasattr(visual_node, 'get_casare_node') else None
                pos = visual_node.pos()

                node_data = {
                    "node_id": node_id,
                    "node_type": casare_node.node_type if casare_node else visual_node.type_,
                    "position": {"x": pos[0], "y": pos[1]},
                    "config": casare_node.config.copy() if casare_node else {},
                }
                export_data["nodes"][node_id] = node_data

            # Export connections between selected nodes only
            for visual_node in selected_nodes:
                node_id = visual_node.get_property("node_id")
                if not node_id:
                    continue

                # Get output ports and their connections
                for port_name, port in visual_node.outputs().items():
                    for connected_port in port.connected_ports():
                        connected_node = connected_port.node()
                        connected_node_id = connected_node.get_property("node_id")

                        # Only include connection if both nodes are selected
                        if connected_node_id in selected_ids:
                            export_data["connections"].append({
                                "source_node": node_id,
                                "source_port": port_name,
                                "target_node": connected_node_id,
                                "target_port": connected_port.name(),
                            })

            # Write to file
            json_bytes = orjson.dumps(
                export_data,
                option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS
            )
            Path(file_path).write_bytes(json_bytes)

            self._main_window.statusBar().showMessage(
                f"Exported {len(selected_ids)} nodes to {Path(file_path).name}",
                5000
            )
            logger.info(f"Exported {len(selected_ids)} nodes to {file_path}")

        except Exception as e:
            logger.exception("Failed to export selected nodes")
            self._main_window.statusBar().showMessage(f"Error exporting nodes: {str(e)}", 5000)

    def _setup_drag_drop_import(self) -> None:
        """
        Setup drag-and-drop support for importing workflow JSON files.

        Allows users to drag .json workflow files directly onto the canvas
        to import nodes at the drop position.
        """
        from .workflow_import import import_workflow_data

        def on_import_file(file_path: str, position: tuple) -> None:
            """Handle file drop."""
            try:
                import orjson
                from pathlib import Path

                logger.info(f"Importing dropped file: {file_path}")

                # Load workflow data
                data = orjson.loads(Path(file_path).read_bytes())

                # Prepare for import (remap IDs and position at drop location)
                prepared_data, id_mapping = import_workflow_data(
                    self._node_graph.graph,
                    get_node_factory(),
                    data,
                    drop_position=position
                )

                # Create nodes from prepared data
                self._load_workflow_to_graph_merge(prepared_data)

                self._main_window.set_modified(True)
                self._main_window.statusBar().showMessage(
                    f"Imported {len(prepared_data.get('nodes', {}))} nodes from {Path(file_path).name}",
                    5000
                )
            except Exception as e:
                logger.exception(f"Failed to import dropped file: {e}")
                self._main_window.statusBar().showMessage(f"Error importing file: {str(e)}", 5000)

        def on_import_data(data: dict, position: tuple) -> None:
            """Handle JSON data drop."""
            try:
                logger.info("Importing dropped JSON data")

                # Prepare for import (remap IDs and position at drop location)
                prepared_data, id_mapping = import_workflow_data(
                    self._node_graph.graph,
                    get_node_factory(),
                    data,
                    drop_position=position
                )

                # Create nodes from prepared data
                self._load_workflow_to_graph_merge(prepared_data)

                self._main_window.set_modified(True)
                self._main_window.statusBar().showMessage(
                    f"Imported {len(prepared_data.get('nodes', {}))} nodes",
                    5000
                )
            except Exception as e:
                logger.exception(f"Failed to import dropped JSON: {e}")
                self._main_window.statusBar().showMessage(f"Error importing JSON: {str(e)}", 5000)

        # Set callbacks and enable drag-drop
        self._node_graph.set_import_file_callback(on_import_file)
        self._node_graph.set_import_callback(on_import_data)
        self._node_graph.setup_drag_drop()

        logger.info("Drag-drop import support configured")

    def _load_workflow_to_graph_merge(self, workflow_data: dict) -> None:
        """
        Load workflow data into graph without clearing existing nodes (merge mode).

        Args:
            workflow_data: Prepared workflow data with remapped IDs
        """
        from .node_registry import get_node_factory

        graph = self._node_graph.graph
        factory = get_node_factory()

        # Create nodes
        for node_id, node_data in workflow_data.get("nodes", {}).items():
            try:
                # Call _load_node_to_graph to reuse existing logic
                # This handles visual node creation and CasareRPA node linking
                visual_node = self._create_visual_node_from_data(graph, node_data, factory)
                if visual_node:
                    logger.debug(f"Created node {node_id} during import")
            except Exception as e:
                logger.error(f"Failed to create node {node_id}: {e}")

        # Restore connections
        node_map = {}
        for visual_node in graph.all_nodes():
            node_id = visual_node.get_property("node_id")
            if node_id:
                node_map[node_id] = visual_node

        for conn in workflow_data.get("connections", []):
            try:
                source_node = node_map.get(conn["source_node"])
                target_node = node_map.get(conn["target_node"])

                if source_node and target_node:
                    source_port = source_node.get_output(conn["source_port"])
                    target_port = target_node.get_input(conn["target_port"])

                    if source_port and target_port:
                        source_port.connect_to(target_port)
            except Exception as e:
                logger.warning(f"Failed to restore connection: {e}")

        logger.debug(f"Imported workflow with {len(workflow_data.get('nodes', {}))} nodes")

    def _create_visual_node_from_data(self, graph, node_data: dict, factory):
        """Create a visual node from workflow data."""
        node_type = node_data.get("node_type")
        node_id = node_data.get("node_id")
        pos = node_data.get("position", {"x": 0, "y": 0})

        # Map node type to identifier (this should match _load_workflow_to_graph)
        # This is a simplified version - actual implementation uses NODE_TYPE_MAP
        identifier = f"casare_rpa.nodes.Visual{node_type}"

        try:
            visual_node = graph.create_node(
                identifier,
                pos=[pos.get("x", 0), pos.get("y", 0)]
            )

            if visual_node:
                # Create CasareRPA node
                casare_node = factory.create_casare_node(visual_node)

                # Override ID if different (from remapping)
                if casare_node and node_id:
                    casare_node.node_id = node_id
                    visual_node.set_property("node_id", node_id)

                # Restore config values
                config = node_data.get("config", {})
                if hasattr(visual_node, '_widgets'):
                    for widget_name, value in config.items():
                        if widget_name in visual_node._widgets:
                            try:
                                visual_node._widgets[widget_name].set_value(value)
                            except Exception as e:
                                logger.debug(f"Could not restore widget {widget_name}: {e}")

                # Restore custom name
                if "name" in node_data:
                    visual_node.set_name(node_data["name"])

                return visual_node
        except Exception as e:
            logger.error(f"Failed to create visual node {node_type}: {e}")
            return None

    def _on_save_workflow(self) -> None:
        """Handle workflow saving."""
        current_file = self._main_window.get_current_file()
        if current_file:
            try:
                logger.info(f"Saving workflow: {current_file}")
                
                # Ensure all nodes are valid before saving
                self._ensure_all_nodes_have_casare_nodes()
                
                # Create workflow from graph
                workflow = self._create_workflow_from_graph()
                
                # Serialize nodes to dict format for saving
                serialized_workflow = WorkflowSchema(workflow.metadata)
                
                # Build a map of visual nodes by their node_id property
                visual_node_map = {}
                for visual_node in self._node_graph.graph.all_nodes():
                    visual_node_id = visual_node.get_property("node_id")
                    if visual_node_id:
                        visual_node_map[visual_node_id] = visual_node
                        logger.info(f"Visual node map: {visual_node_id} -> {visual_node.name()}")
                    else:
                        logger.warning(f"Visual node {visual_node.name()} has no node_id property")
                
                for node_id, node in workflow.nodes.items():
                    serialized_node = node.serialize()
                    
                    # Add node position and name from graph
                    if node_id in visual_node_map:
                        visual_node = visual_node_map[node_id]
                        pos = visual_node.pos()
                        serialized_node["position"] = {"x": pos[0], "y": pos[1]}
                        serialized_node["name"] = visual_node.name()
                        logger.info(f"Saving {node_id}: pos=({pos[0]}, {pos[1]}), name='{visual_node.name()}'")
                    else:
                        logger.warning(f"No visual node found for {node_id}")
                    
                    serialized_workflow.add_node(serialized_node)
                
                # Add connections
                for conn in workflow.connections:
                    serialized_workflow.add_connection(conn)

                # Serialize frames
                serialized_workflow.frames = self._serialize_frames()

                # Save to file
                serialized_workflow.save_to_file(current_file)

                self._main_window.set_modified(False)
                self._main_window.statusBar().showMessage(f"Saved: {current_file.name}", 3000)

            except Exception as e:
                logger.exception("Failed to save workflow")
                self._main_window.statusBar().showMessage(f"Error saving file: {str(e)}", 5000)

    def _serialize_frames(self) -> list:
        """
        Serialize all frames in the scene.

        Returns:
            List of serialized frame dictionaries
        """
        from .node_frame import NodeFrame

        frames = []
        scene = self._node_graph.graph.viewer().scene()

        for item in scene.items():
            if isinstance(item, NodeFrame):
                frames.append(item.serialize())
                logger.debug(f"Serialized frame: {item.frame_title}")

        logger.info(f"Serialized {len(frames)} frames")
        return frames

    def _deserialize_frames(self, frames_data: list, node_map: dict) -> None:
        """
        Deserialize frames and add them to the scene.

        Args:
            frames_data: List of serialized frame dictionaries
            node_map: Mapping of node_id to visual node objects
        """
        from .node_frame import NodeFrame

        if not frames_data:
            return

        scene = self._node_graph.graph.viewer().scene()

        for frame_data in frames_data:
            try:
                frame = NodeFrame.deserialize(frame_data, node_map)
                scene.addItem(frame)
                logger.debug(f"Deserialized frame: {frame.frame_title}")
            except Exception as e:
                logger.warning(f"Failed to deserialize frame: {e}")

        logger.info(f"Deserialized {len(frames_data)} frames")

    def _on_save_as_workflow(self, file_path: str) -> None:
        """
        Handle save as workflow.
        
        Args:
            file_path: Path to save workflow
        """
        try:
            from pathlib import Path
            logger.info(f"Saving workflow as: {file_path}")
            
            # Ensure all nodes are valid before saving
            self._ensure_all_nodes_have_casare_nodes()
            
            # Create workflow from graph
            workflow = self._create_workflow_from_graph()
            
            # Serialize nodes to dict format for saving
            serialized_workflow = WorkflowSchema(workflow.metadata)
            
            # Build a map of visual nodes by their node_id property
            visual_node_map = {}
            for visual_node in self._node_graph.graph.all_nodes():
                visual_node_id = visual_node.get_property("node_id")
                if visual_node_id:
                    visual_node_map[visual_node_id] = visual_node
                    logger.info(f"Visual node map: {visual_node_id} -> {visual_node.name()}")
                else:
                    logger.warning(f"Visual node {visual_node.name()} has no node_id property")
            
            for node_id, node in workflow.nodes.items():
                serialized_node = node.serialize()
                
                # Add node position and name from graph
                if node_id in visual_node_map:
                    visual_node = visual_node_map[node_id]
                    pos = visual_node.pos()
                    serialized_node["position"] = {"x": pos[0], "y": pos[1]}
                    serialized_node["name"] = visual_node.name()
                    logger.info(f"Saving {node_id}: pos=({pos[0]}, {pos[1]}), name='{visual_node.name()}'")
                else:
                    logger.warning(f"No visual node found for {node_id}")
                
                serialized_workflow.add_node(serialized_node)
            
            # Add connections
            for conn in workflow.connections:
                serialized_workflow.add_connection(conn)

            # Serialize frames
            serialized_workflow.frames = self._serialize_frames()

            # Save to file
            serialized_workflow.save_to_file(Path(file_path))

            self._main_window.set_modified(False)
            self._main_window.statusBar().showMessage(f"Saved as: {Path(file_path).name}", 3000)

        except Exception as e:
            logger.exception("Failed to save workflow")
            self._main_window.statusBar().showMessage(f"Error saving file: {str(e)}", 5000)

    def _ensure_all_nodes_have_casare_nodes(self) -> bool:
        """
        Ensure all visual nodes in the graph have CasareRPA nodes.
        Creates missing CasareRPA nodes on demand.
        
        Returns:
            True if all nodes have CasareRPA nodes, False if any failed
        """
        graph = self._node_graph.graph
        all_valid = True
        
        for visual_node in graph.all_nodes():
            if hasattr(visual_node, 'ensure_casare_node'):
                casare_node = visual_node.ensure_casare_node()
                if not casare_node:
                    logger.error(f"Failed to create CasareRPA node for {visual_node.name()}")
                    all_valid = False
            else:
                logger.warning(f"Node {visual_node.name()} doesn't support ensure_casare_node")
        
        return all_valid
    
    def _sync_visual_properties_to_node(self, visual_node, casare_node) -> None:
        """
        Sync widget values from visual node to CasareRPA node config.
        This updates the node's config with current values from the UI widgets.
        
        Args:
            visual_node: Visual node from NodeGraphQt
            casare_node: CasareRPA node instance
        """
        # Get all embedded widgets (text inputs, dropdowns, etc.)
        widgets = visual_node.widgets()
        logger.info(f"Visual node {casare_node.node_type} has widgets: {list(widgets.keys())}")
        
        # Sync widget values to node config
        synced_count = 0
        for widget_name, widget in widgets.items():
            try:
                # Get widget value
                widget_value = widget.get_value()
                logger.info(f"  Widget '{widget_name}' = '{widget_value}' (type: {type(widget_value).__name__})")
                
                # Always sync widget values, including empty strings (to clear previous values)
                if widget_value is not None:
                    casare_node.config[widget_name] = widget_value
                    synced_count += 1
                    logger.info(f"  ✓ Synced {casare_node.node_type}.{widget_name} = '{widget_value}'")
            except Exception as e:
                logger.warning(f"Could not sync widget {widget_name}: {e}")
        
        if synced_count == 0:
            logger.info(f"No widgets synced for {casare_node.node_type}")

    def _get_initial_variables(self) -> Dict[str, Any]:
        """
        Get initial variables from the bottom panel Variables Tab.

        These variables will be loaded into ExecutionContext at workflow start,
        enabling {{variable_name}} substitution in node properties.

        Returns:
            Dict of variable_name -> default_value
        """
        initial_variables = {}

        try:
            # Get bottom panel from main window
            bottom_panel = self._main_window.get_bottom_panel()
            if bottom_panel:
                variables_tab = bottom_panel.get_variables_tab()
                if variables_tab:
                    # Get all variables from the Variables Tab
                    for name, var_def in variables_tab.get_variables().items():
                        # Extract the default value from the variable definition
                        if isinstance(var_def, dict):
                            initial_variables[name] = var_def.get("default_value", "")
                        else:
                            initial_variables[name] = var_def

                    if initial_variables:
                        logger.info(
                            f"Loaded {len(initial_variables)} variables from Variables Tab: "
                            f"{list(initial_variables.keys())}"
                        )
        except Exception as e:
            logger.warning(f"Could not get initial variables from bottom panel: {e}")

        return initial_variables

    def _create_workflow_from_graph(self) -> WorkflowSchema:
        """
        Create a WorkflowSchema from the current node graph.
        WorkflowRunner expects workflow.nodes to be a dict of node instances.
        
        Returns:
            WorkflowSchema instance
        """
        from .node_registry import get_node_registry
        
        graph = self._node_graph.graph
        registry = get_node_registry()
        
        # Ensure all nodes have CasareRPA nodes
        if not self._ensure_all_nodes_have_casare_nodes():
            logger.error("Some nodes don't have CasareRPA nodes - workflow may be incomplete")
        
        # Create workflow metadata
        metadata = WorkflowMetadata(
            name="Current Workflow",
            description="Workflow from visual editor"
        )
        
        # Create workflow schema
        workflow = WorkflowSchema(metadata)
        
        # Build nodes dict with actual node instances (required by WorkflowRunner)
        nodes_dict = {}
        node_id_map = {}  # Map visual_node -> node_id for connections
        
        logger.info(f"Building workflow from {len(graph.all_nodes())} visual nodes")
        for visual_node in graph.all_nodes():
            # Get the underlying CasareRPA node
            casare_node = visual_node.get_casare_node()
            if casare_node:
                # Use the visual node's stored node_id property (set by set_casare_node)
                stored_node_id = visual_node.get_property("node_id")
                if stored_node_id:
                    node_id = stored_node_id
                else:
                    node_id = casare_node.node_id
                
                logger.info(f"Processing visual node: {visual_node.name()} -> {casare_node.node_type} (id={node_id})")
                # Sync visual node properties to CasareRPA node config
                self._sync_visual_properties_to_node(visual_node, casare_node)
                nodes_dict[node_id] = casare_node
                node_id_map[visual_node] = node_id
            else:
                logger.warning(f"Skipping node {visual_node.name()} - no CasareRPA node")
        
        # Auto-create hidden Start node
        from ..nodes.basic_nodes import StartNode
        start_node = StartNode("__auto_start__")
        nodes_dict["__auto_start__"] = start_node
        
        # Find all nodes without exec_in connections (these are entry points)
        entry_nodes = []
        for visual_node in graph.all_nodes():
            casare_node = visual_node.get_casare_node()
            if not casare_node:
                continue
            
            # Check if node has exec_in port
            has_exec_in = "exec_in" in casare_node.input_ports
            if not has_exec_in:
                continue
            
            # Check if exec_in is connected
            exec_in_connected = False
            for input_port in visual_node.input_ports():
                if input_port.name() == "exec_in" and input_port.connected_ports():
                    exec_in_connected = True
                    break
            
            if not exec_in_connected:
                # Use the mapped node_id from node_id_map
                node_id = node_id_map.get(visual_node, casare_node.node_id)
                entry_nodes.append(node_id)
        
        # Set nodes as instances (WorkflowRunner needs this)
        workflow.nodes = nodes_dict
        
        # Add connections from graph
        connections = []
        
        # Auto-connect Start node to entry points
        from ..core.workflow_schema import NodeConnection
        for entry_node_id in entry_nodes:
            connection = NodeConnection(
                source_node="__auto_start__",
                source_port="exec_out",
                target_node=entry_node_id,
                target_port="exec_in"
            )
            connections.append(connection)
            logger.info(f"Auto-connected Start → {entry_node_id}")
        for node in graph.all_nodes():
            # Get the source node ID from our map
            source_node_id = node_id_map.get(node)
            if not source_node_id:
                continue
            
            # Get output connections
            for output_port in node.output_ports():
                for connected_port in output_port.connected_ports():
                    target_visual_node = connected_port.node()
                    target_node_id = node_id_map.get(target_visual_node)
                    if not target_node_id:
                        continue
                    
                    connection = NodeConnection(
                        source_node=source_node_id,
                        source_port=output_port.name(),
                        target_node=target_node_id,
                        target_port=connected_port.name()
                    )
                    connections.append(connection)
        
        workflow.connections = connections
        
        return workflow
    
    def _reset_all_node_visuals(self) -> None:
        """Reset visual state of all nodes before workflow execution."""
        graph = self._node_graph.graph
        for visual_node in graph.all_nodes():
            visual_node.update_status("idle")
            if hasattr(visual_node.view, 'clear_execution_state'):
                visual_node.view.clear_execution_state()

    def _on_run_workflow(self) -> None:
        """Handle workflow execution."""
        try:
            logger.info("Starting workflow execution")

            # Reset all node visuals before starting
            self._reset_all_node_visuals()

            # Create workflow from current graph
            workflow = self._create_workflow_from_graph()

            # Get initial variables from bottom panel Variables Tab
            initial_variables = self._get_initial_variables()

            # Create workflow runner with initial variables
            self._workflow_runner = WorkflowRunner(
                workflow,
                self._event_bus,
                initial_variables=initial_variables
            )
            
            # Apply debug settings from toolbar
            debug_toolbar = self._main_window.get_debug_toolbar()
            if debug_toolbar:
                debug_enabled = debug_toolbar.action_debug_mode.isChecked()
                step_enabled = debug_toolbar.action_step_mode.isChecked()
                
                if debug_enabled:
                    self._workflow_runner.enable_debug_mode(True)
                    logger.info("Debug mode enabled for execution")

                    # Clear debug data (don't change panel visibility)
                    var_inspector = self._main_window.get_variable_inspector()
                    exec_history = self._main_window.get_execution_history_viewer()
                    if var_inspector:
                        var_inspector.clear()
                    if exec_history:
                        exec_history.clear()
                
                if step_enabled:
                    self._workflow_runner.enable_step_mode(True)
                    logger.info("Step mode enabled for execution")
                
                # Update toolbar state
                debug_toolbar.set_execution_state(True)

            # Start debug update timer if in debug mode
            if self._workflow_runner.debug_mode:
                self._start_debug_updates()
            
            # Run workflow asynchronously
            async def run_and_cleanup():
                try:
                    await self._workflow_runner.run()
                finally:
                    # Update debug panels one final time
                    if self._workflow_runner.debug_mode:
                        self._update_debug_panels()
                        self._stop_debug_updates()
                    
                    # Update toolbar state
                    if debug_toolbar:
                        debug_toolbar.set_execution_state(False)
            
            self._workflow_task = asyncio.ensure_future(run_and_cleanup())

        except Exception as e:
            logger.exception("Failed to start workflow execution")
            self._main_window.statusBar().showMessage(f"Error: {str(e)}", 5000)

    def _on_run_to_node(self, target_node_id: str) -> None:
        """
        Handle run-to-node execution (F4).

        Executes the workflow from StartNode to the specified target node,
        then pauses at that node for inspection.

        Can be called multiple times - will stop any existing run and restart.

        Args:
            target_node_id: The node ID to run to
        """
        try:
            logger.info(f"Starting run-to-node execution, target: {target_node_id}")

            # Stop any existing workflow runner first
            if self._workflow_runner is not None:
                if self._workflow_runner.state in ("running", "paused"):
                    logger.info("Stopping existing workflow runner before restart")
                    self._workflow_runner.stop()
                    # Cancel the task if it exists
                    if self._workflow_task and not self._workflow_task.done():
                        self._workflow_task.cancel()
                        self._workflow_task = None
                # Clear reference
                self._workflow_runner = None

            # Reset all node visuals before starting
            self._reset_all_node_visuals()

            # Create workflow from current graph
            workflow = self._create_workflow_from_graph()

            # Get initial variables from bottom panel Variables Tab
            initial_variables = self._get_initial_variables()

            # Create workflow runner with target node and initial variables
            self._workflow_runner = WorkflowRunner(
                workflow,
                self._event_bus,
                target_node_id=target_node_id,
                initial_variables=initial_variables
            )

            # Check if subgraph was successfully calculated
            if not self._workflow_runner.subgraph_valid:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(
                    self._main_window,
                    "Cannot Run To Node",
                    f"Target node is not reachable from StartNode.\n\n"
                    "Make sure the node is connected to the workflow."
                )
                # Re-enable run buttons
                self._main_window.action_run.setEnabled(True)
                self._main_window.action_run_to_node.setEnabled(True)
                self._main_window.action_run_single_node.setEnabled(True)
                self._main_window.action_pause.setEnabled(False)
                self._main_window.action_stop.setEnabled(False)
                return

            # Enable debug mode for inspection after reaching target
            self._workflow_runner.enable_debug_mode(True)
            logger.info("Debug mode enabled for run-to-node (for inspection at target)")

            # Clear debug data (don't change panel visibility)
            var_inspector = self._main_window.get_variable_inspector()
            exec_history = self._main_window.get_execution_history_viewer()
            if var_inspector:
                var_inspector.clear()
            if exec_history:
                exec_history.clear()

            # Update debug toolbar state
            debug_toolbar = self._main_window.get_debug_toolbar()
            if debug_toolbar:
                debug_toolbar.set_execution_state(True)

            # Start debug update timer
            self._start_debug_updates()

            # Run workflow asynchronously
            # Store reference locally to handle case where F4 is pressed again
            runner = self._workflow_runner

            async def run_and_cleanup():
                try:
                    await runner.run()
                finally:
                    # Check if this runner is still the active one
                    # (user may have pressed F4 again, creating a new runner)
                    if self._workflow_runner is not runner:
                        logger.debug("Workflow runner replaced - skipping cleanup")
                        return

                    # Update debug panels one final time
                    if runner.debug_mode:
                        self._update_debug_panels()
                        self._stop_debug_updates()

                    # Update toolbar state
                    if debug_toolbar:
                        debug_toolbar.set_execution_state(False)

                    # Re-enable run buttons when done
                    self._main_window.action_run.setEnabled(True)
                    self._main_window.action_run_to_node.setEnabled(True)
                    self._main_window.action_run_single_node.setEnabled(True)

                    # Show status message based on result
                    if runner.target_reached:
                        self._main_window.statusBar().showMessage(
                            f"Reached target node - paused for inspection. "
                            f"Press F8 to continue or F7 to stop.",
                            0
                        )
                    elif runner.state == "completed":
                        self._main_window.statusBar().showMessage(
                            "Workflow completed (target may not have been on execution path)",
                            5000
                        )

            self._workflow_task = asyncio.ensure_future(run_and_cleanup())

        except Exception as e:
            logger.exception("Failed to start run-to-node execution")
            self._main_window.statusBar().showMessage(f"Error: {str(e)}", 5000)
            # Re-enable run buttons on error
            self._main_window.action_run.setEnabled(True)
            self._main_window.action_run_to_node.setEnabled(True)
            self._main_window.action_run_single_node.setEnabled(True)

    def _on_run_single_node(self, node_id: str) -> None:
        """
        Handle run single node execution (F5).

        Executes only the selected node using existing input data from the
        last execution context. If no previous context exists, the node's
        input ports will be empty.

        Args:
            node_id: The node ID to execute
        """
        try:
            logger.info(f"Starting single node execution: {node_id}")

            # Find the visual node and its CasareRPA node
            visual_node = None
            casare_node = None
            graph = self._node_graph.graph

            for vn in graph.all_nodes():
                if vn.get_property("node_id") == node_id:
                    visual_node = vn
                    casare_node = vn.get_casare_node()
                    break

            if not visual_node or not casare_node:
                logger.error(f"Node not found: {node_id}")
                self._main_window.statusBar().showMessage(f"Node not found", 3000)
                self._main_window.action_run_single_node.setEnabled(True)
                return

            # Clear only this node's visual state
            visual_node.update_status("running")
            if hasattr(visual_node.view, 'set_running'):
                visual_node.view.set_running(True)

            # Sync widget values to node config before execution
            self._sync_visual_properties_to_node(visual_node, casare_node)

            # Get execution context - reuse existing one if available
            if self._workflow_runner and self._workflow_runner.context:
                context = self._workflow_runner.context
                logger.info("Reusing existing execution context with inputs")
            else:
                # Create a minimal context
                from ..core.execution_context import ExecutionContext
                context = ExecutionContext()
                # Load initial variables from panel
                initial_variables = self._get_initial_variables()
                for name, value in initial_variables.items():
                    context.set_variable(name, value)
                logger.info("Created new execution context")

            # Execute the single node
            async def execute_single_node():
                import time
                try:
                    start_time = time.time()

                    # Execute the node
                    result = await casare_node.execute(context)

                    execution_time = time.time() - start_time

                    # Update visual feedback
                    if result.success:
                        visual_node.update_status("success")
                        visual_node.update_execution_time(execution_time)
                        logger.info(f"Node {node_id} completed in {execution_time:.2f}s")
                        self._main_window.statusBar().showMessage(
                            f"Node completed in {execution_time:.2f}s", 3000
                        )
                    else:
                        visual_node.update_status("error")
                        visual_node.update_execution_time(execution_time)
                        error_msg = result.error or "Unknown error"
                        logger.error(f"Node {node_id} failed: {error_msg}")
                        self._main_window.statusBar().showMessage(
                            f"Node failed: {error_msg}", 5000
                        )

                except Exception as e:
                    visual_node.update_status("error")
                    logger.exception(f"Error executing node {node_id}")
                    self._main_window.statusBar().showMessage(f"Error: {str(e)}", 5000)

                finally:
                    # Re-enable the action
                    self._main_window.action_run_single_node.setEnabled(True)
                    if hasattr(visual_node.view, 'set_running'):
                        visual_node.view.set_running(False)

            asyncio.ensure_future(execute_single_node())

        except Exception as e:
            logger.exception("Failed to start single node execution")
            self._main_window.statusBar().showMessage(f"Error: {str(e)}", 5000)
            self._main_window.action_run_single_node.setEnabled(True)

    def _on_pause_workflow(self) -> None:
        """Handle workflow pause."""
        if self._workflow_runner:
            logger.info("Pausing workflow execution")
            self._workflow_runner.pause()
    
    def _on_resume_workflow(self) -> None:
        """Handle workflow resume."""
        if self._workflow_runner:
            logger.info("Resuming workflow execution")
            self._workflow_runner.resume()
    
    def _on_stop_workflow(self) -> None:
        """Handle workflow stop."""
        if self._workflow_runner:
            logger.info("Stopping workflow execution")
            self._workflow_runner.stop()
    
    def _check_browser_launch(self, event) -> None:
        """Check if a browser was launched and initialize selector integration."""
        if not self._workflow_runner:
            return
        
        # Check if execution context has an active page
        context = self._workflow_runner.context
        if context and context.active_page:
            # Check if this is a new page (different from current active page)
            is_new_page = (
                not self._selector_integration._active_page or 
                self._selector_integration._active_page != context.active_page
            )
            
            if is_new_page:
                async def init_selector():
                    try:
                        await self._selector_integration.initialize_for_page(context.active_page)
                        self._main_window.set_browser_running(True)
                        logger.info("Selector integration initialized for browser page")
                    except Exception as e:
                        logger.error(f"Failed to initialize selector integration: {e}")
                
                asyncio.ensure_future(init_selector())
        else:
            # No active page - disable selector buttons
            if self._selector_integration._active_page:
                self._main_window.set_browser_running(False)
                self._selector_integration._active_page = None
                logger.info("Browser closed - selector integration disabled")
    
    def _on_node_started(self, event) -> None:
        """Handle node started event."""
        node_id = event.data.get("node_id")
        if node_id:
            # Find visual node and update status
            graph = self._node_graph.graph
            for visual_node in graph.all_nodes():
                if visual_node.get_property("node_id") == node_id:
                    visual_node.update_status("running")
                    break
    
    def _on_node_completed(self, event) -> None:
        """Handle node completed event."""
        node_id = event.data.get("node_id")
        progress = event.data.get("progress", 0)
        execution_time = event.data.get("execution_time")
        target_reached = event.data.get("target_reached", False)

        if node_id:
            # Find visual node and update status
            graph = self._node_graph.graph
            for visual_node in graph.all_nodes():
                if visual_node.get_property("node_id") == node_id:
                    visual_node.update_status("success")

                    # Update execution time from event data
                    if execution_time is not None:
                        visual_node.update_execution_time(execution_time)
                    break

        # Check if target node was reached (Run-To-Node mode)
        if target_reached:
            # Re-enable run buttons so user can run again
            self._main_window.action_run.setEnabled(True)
            self._main_window.action_run_to_node.setEnabled(True)
            self._main_window.action_run_single_node.setEnabled(True)
            self._main_window.statusBar().showMessage(
                f"Target node reached - paused. Press F4 to re-run, F5 to run this node, F8 to continue, F7 to stop.",
                0
            )
            return

        # Update progress in status bar
        self._main_window.statusBar().showMessage(
            f"Workflow progress: {progress:.1f}%",
            0
        )
    
    def _on_node_error(self, event) -> None:
        """Handle node error event."""
        node_id = event.data.get("node_id")
        error = event.data.get("error", "Unknown error")
        execution_time = event.data.get("execution_time")

        if node_id:
            # Find visual node and update status
            graph = self._node_graph.graph
            for visual_node in graph.all_nodes():
                if visual_node.get_property("node_id") == node_id:
                    visual_node.update_status("error")

                    # Update execution time from event data (even on error)
                    if execution_time is not None:
                        visual_node.update_execution_time(execution_time)
                    break

        logger.error(f"Node error: {node_id} - {error}")
        self._main_window.statusBar().showMessage(f"Error in node: {error}", 5000)
    
    def _on_workflow_completed(self, event) -> None:
        """Handle workflow completed event."""
        duration = event.data.get("duration", 0)
        executed_nodes = event.data.get("executed_nodes", 0)
        total_nodes = event.data.get("total_nodes", 0)

        logger.info(f"Workflow completed in {duration:.2f}s ({executed_nodes}/{total_nodes} nodes)")
        self._main_window.statusBar().showMessage(
            f"Workflow completed! ({executed_nodes}/{total_nodes} nodes in {duration:.2f}s)",
            5000
        )

        # Reset UI - re-enable all run actions
        self._main_window.action_run.setEnabled(True)
        self._main_window.action_run_to_node.setEnabled(True)
        self._main_window.action_run_single_node.setEnabled(True)
        self._main_window.action_pause.setEnabled(False)
        self._main_window.action_pause.setChecked(False)
        self._main_window.action_stop.setEnabled(False)

        # Keep selector buttons enabled if browser is still active
        # They will be disabled when browser is closed or page becomes invalid

    def _on_workflow_error(self, event) -> None:
        """Handle workflow error event."""
        error = event.data.get("error", "Unknown error")
        executed_nodes = event.data.get("executed_nodes", 0)

        logger.error(f"Workflow failed: {error}")
        self._main_window.statusBar().showMessage(f"Workflow failed: {error}", 5000)

        # Reset UI - re-enable all run actions
        self._main_window.action_run.setEnabled(True)
        self._main_window.action_run_to_node.setEnabled(True)
        self._main_window.action_run_single_node.setEnabled(True)
        self._main_window.action_pause.setEnabled(False)
        self._main_window.action_pause.setChecked(False)
        self._main_window.action_stop.setEnabled(False)

        # Keep selector buttons enabled if browser is still active
        # They will be disabled when browser is closed or page becomes invalid

    def _on_debug_mode_toggled(self, enabled: bool) -> None:
        """Handle debug mode toggle."""
        logger.debug(f"Debug mode {'enabled' if enabled else 'disabled'}")
        if self._workflow_runner:
            self._workflow_runner.enable_debug_mode(enabled)
    
    def _on_step_mode_toggled(self, enabled: bool) -> None:
        """Handle step mode toggle."""
        logger.debug(f"Step mode {'enabled' if enabled else 'disabled'}")
        if self._workflow_runner:
            self._workflow_runner.enable_step_mode(enabled)
    
    def _on_step_requested(self) -> None:
        """Handle step execution request."""
        if self._workflow_runner:
            logger.debug("Step execution requested")
            self._workflow_runner.step()
            # Update debug panels after step
            self._update_debug_panels()
    
    def _on_continue_requested(self) -> None:
        """Handle continue execution request."""
        if self._workflow_runner:
            logger.debug("Continue execution requested")
            self._workflow_runner.continue_execution()
    
    def _on_clear_breakpoints(self) -> None:
        """Handle clear all breakpoints request."""
        if self._workflow_runner:
            logger.debug("Clearing all breakpoints")
            self._workflow_runner.clear_all_breakpoints()
            self._main_window.statusBar().showMessage("All breakpoints cleared", 3000)
    
    def _on_refresh_variables(self) -> None:
        """Handle variable refresh request."""
        if self._workflow_runner:
            variables = self._workflow_runner.get_variables()
            var_inspector = self._main_window.get_variable_inspector()
            if var_inspector:
                var_inspector.update_values(variables)
    
    def _on_history_node_selected(self, node_id: str) -> None:
        """
        Handle node selection from execution history.
        
        Args:
            node_id: ID of the selected node
        """
        logger.debug(f"History node selected: {node_id}")
        # Highlight the node in the graph
        graph = self._node_graph.graph
        graph.clear_selection()
        for visual_node in graph.all_nodes():
            if visual_node.get_property("node_id") == node_id:
                visual_node.set_selected(True)
                # Center on the node
                self._node_graph.center_on_nodes([visual_node])
                break
    
    def _on_clear_history(self) -> None:
        """Handle clear execution history request."""
        exec_history = self._main_window.get_execution_history_viewer()
        if exec_history:
            exec_history.clear()
            self._main_window.statusBar().showMessage("Execution history cleared", 3000)
    
    def _on_start_selector_picking(self) -> None:
        """Handle selector picking request."""
        if not self._selector_integration._active_page:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self._main_window,
                "No Browser",
                "Please launch a browser first by running a workflow with a Launch Browser node."
            )
            # Ensure buttons are disabled if page is gone
            self._main_window.set_browser_running(False)
            return
        
        # Check if page is still valid (not closed)
        try:
            if self._selector_integration._active_page.is_closed():
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(
                    self._main_window,
                    "Browser Closed",
                    "The browser page has been closed. Please launch a new browser."
                )
                self._main_window.set_browser_running(False)
                self._selector_integration._active_page = None
                return
        except Exception:
            # If we can't check, assume it's closed
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self._main_window,
                "Browser Unavailable",
                "The browser is no longer available. Please launch a new browser."
            )
            self._main_window.set_browser_running(False)
            self._selector_integration._active_page = None
            return
        
        # Get selected node if any
        selected_nodes = self._node_graph.graph.selected_nodes()
        target_node = None
        target_property = "selector"
        
        if selected_nodes:
            # Get the first selected node with a selector property
            for visual_node in selected_nodes:
                # Check if node has selector widget
                if hasattr(visual_node, 'get_widget'):
                    selector_widget = visual_node.get_widget("selector")
                    if selector_widget:
                        target_node = visual_node
                        break
        
        async def start_picking():
            try:
                await self._selector_integration.start_picking(target_node, target_property)
                self._main_window.statusBar().showMessage("Selector mode active - Click an element in the browser", 0)
                logger.info("Selector picking mode activated")
            except Exception as e:
                logger.error(f"Failed to start selector picking: {e}")
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.critical(
                    self._main_window,
                    "Selector Error",
                    f"Failed to start selector picking:\n\n{str(e)}"
                )
        
        asyncio.ensure_future(start_picking())
    
    def _on_toggle_recording(self, checked: bool) -> None:
        """Handle recording mode toggle."""
        if not self._selector_integration._active_page:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self._main_window,
                "No Browser",
                "Please launch a browser first by running a workflow with a Launch Browser node."
            )
            self._main_window.set_browser_running(False)
            self._main_window.action_record_workflow.setChecked(False)
            return
        
        # Check if page is still valid (not closed)
        try:
            if self._selector_integration._active_page.is_closed():
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(
                    self._main_window,
                    "Browser Closed",
                    "The browser page has been closed. Please launch a new browser."
                )
                self._main_window.set_browser_running(False)
                self._selector_integration._active_page = None
                self._main_window.action_record_workflow.setChecked(False)
                return
        except Exception:
            # If we can't check, assume it's closed
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self._main_window,
                "Browser Unavailable",
                "The browser is no longer available. Please launch a new browser."
            )
            self._main_window.set_browser_running(False)
            self._selector_integration._active_page = None
            self._main_window.action_record_workflow.setChecked(False)
            return
        
        async def toggle_recording():
            try:
                if checked:
                    await self._selector_integration.start_recording()
                    self._main_window.statusBar().showMessage(
                        "🔴 RECORDING - Click elements to capture actions • Type to record text • Press Ctrl+R when done to generate workflow",
                        0
                    )
                    logger.info("Recording mode activated")
                else:
                    await self._selector_integration.stop_selector_mode()
                    self._main_window.statusBar().showMessage("Recording stopped", 3000)
                    logger.info("Recording mode deactivated")
            except Exception as e:
                logger.error(f"Failed to toggle recording: {e}")
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.critical(
                    self._main_window,
                    "Recording Error",
                    f"Failed to toggle recording mode:\n\n{str(e)}"
                )
                self._main_window.action_record_workflow.setChecked(False)
        
        asyncio.ensure_future(toggle_recording())
    
    def _on_selector_picked(self, selector_value: str, selector_type: str) -> None:
        """Handle selector picked event."""
        logger.info(f"Selector picked: {selector_type} = {selector_value}")
        self._main_window.statusBar().showMessage(f"Selector picked: {selector_type}", 3000)
    
    def _on_recording_complete(self, actions: list) -> None:
        """Handle recording complete event - generate workflow nodes."""
        logger.info(f"Recording complete: {len(actions)} actions captured")
        
        # Reset recording button state
        self._main_window.action_record_workflow.setChecked(False)
        
        if not actions:
            self._main_window.statusBar().showMessage("No actions recorded", 3000)
            return
        
        # Show preview dialog
        from .recording_dialog import RecordingPreviewDialog
        
        dialog = RecordingPreviewDialog(actions, self._main_window)
        if dialog.exec():
            # User accepted - generate workflow
            edited_actions = dialog.get_actions()
            self._generate_workflow_from_recording(edited_actions)
            self._main_window.statusBar().showMessage(
                f"Generated workflow from {len(edited_actions)} actions",
                5000
            )
        else:
            logger.info("Recording cancelled by user")
            self._main_window.statusBar().showMessage("Recording cancelled", 3000)
    
    def _generate_workflow_from_recording(self, actions: list) -> None:
        """
        Generate workflow nodes from recorded actions.
        
        Args:
            actions: List of recorded action dictionaries
        """
        from ..recorder import RecordedAction, ActionType, WorkflowGenerator
        from datetime import datetime
        
        # Convert action dicts to RecordedAction objects
        recorded_actions = []
        for action_dict in actions:
            try:
                # Extract element info
                element_info = action_dict.get('element', {})
                
                # Handle both dict and ElementFingerprint objects
                if hasattr(element_info, 'selectors'):
                    # It's an ElementFingerprint object - selectors is a List[SelectorStrategy]
                    # Convert to dict format for compatibility
                    selectors = {}
                    if element_info.selectors:
                        for strat in element_info.selectors:
                            selectors[strat.selector_type.value] = strat.value
                elif isinstance(element_info, dict):
                    # It's a dictionary
                    selectors = element_info.get('selectors', {})
                else:
                    selectors = {}
                
                # Use XPath as primary selector
                selector = selectors.get('xpath', '')
                if not selector and selectors.get('css'):
                    selector = selectors.get('css')
                
                # Map action type
                action_type_str = action_dict.get('action', 'click')
                action_type = ActionType(action_type_str)
                
                # Extract element metadata for better naming
                element_text = None
                element_id = None
                element_tag = None
                element_class = None
                
                if isinstance(element_info, dict):
                    element_text = element_info.get('text', '')
                    element_id = element_info.get('id', '')
                    element_tag = element_info.get('tagName', '')
                    element_class = element_info.get('className', '')
                
                # Create RecordedAction
                recorded_action = RecordedAction(
                    action_type=action_type,
                    selector=selector,
                    value=action_dict.get('value'),
                    timestamp=datetime.fromtimestamp(action_dict.get('timestamp', 0) / 1000),
                    element_info=element_info if isinstance(element_info, dict) else {},
                    url=action_dict.get('url'),
                    element_text=element_text,
                    element_id=element_id,
                    element_tag=element_tag,
                    element_class=element_class,
                )
                recorded_actions.append(recorded_action)
                
            except Exception as e:
                logger.error(f"Failed to convert action: {e}")
                continue
        
        if not recorded_actions:
            logger.warning("No valid actions to generate workflow from")
            return
        
        # Generate workflow
        generator = WorkflowGenerator()
        
        # Get insertion point (below last node in graph)
        graph = self._node_graph.graph
        nodes = graph.all_nodes()
        if nodes:
            # Find bottom-most node (pos() returns [x, y])
            max_y = max(node.pos()[1] for node in nodes)
            start_position = {'x': 200, 'y': max_y + 200}
        else:
            start_position = {'x': 200, 'y': 100}
        
        node_specs = generator.generate_workflow(recorded_actions, start_position)
        
        # Map node types to visual node identifiers
        node_type_to_identifier = {
            'ClickElement': 'casare_rpa.interaction.VisualClickElementNode',
            'TypeText': 'casare_rpa.interaction.VisualTypeTextNode',
            'SelectDropdown': 'casare_rpa.interaction.VisualSelectDropdownNode',
            'GoToURL': 'casare_rpa.navigation.VisualGoToURLNode',
            'WaitForElement': 'casare_rpa.wait.VisualWaitForElementNode',
        }
        
        # Create visual nodes in graph
        created_nodes = []
        for spec in node_specs:
            try:
                node_type = spec['type']
                
                if node_type not in node_type_to_identifier:
                    logger.warning(f"Unknown node type: {node_type}")
                    continue
                
                # Create visual node
                node_identifier = node_type_to_identifier[node_type]
                visual_node = graph.create_node(
                    node_identifier,
                    name=spec.get('name', node_type),
                    pos=[spec['position']['x'], spec['position']['y']]
                )
                
                if visual_node:
                    # Set properties from config
                    for prop_name, prop_value in spec['config'].items():
                        if visual_node.has_property(prop_name):
                            visual_node.set_property(prop_name, prop_value)
                    
                    created_nodes.append(visual_node)
                    logger.debug(f"Created visual node: {spec.get('name', node_type)}")
                    
            except Exception as e:
                logger.error(f"Failed to create node {spec['type']}: {e}")
                continue
        
        # Connect first generated node to last existing node (if workflow exists)
        if created_nodes and nodes:
            try:
                # Find node with highest Y position (bottom-most) that has an exec output
                nodes_with_outputs = [n for n in nodes if n.output_ports()]
                if nodes_with_outputs:
                    last_node = max(nodes_with_outputs, key=lambda n: n.pos()[1])
                    first_new_node = created_nodes[0]
                    
                    # Connect last existing node to first new node
                    exec_out = last_node.output(0)
                    exec_in = first_new_node.input(0)
                    exec_out.connect_to(exec_in)
                    logger.info(f"Connected existing workflow: {last_node.name()} -> {first_new_node.name()}")
            except Exception as e:
                logger.warning(f"Could not connect to existing workflow: {e}")
        
        # Connect generated nodes to each other sequentially
        for i in range(len(created_nodes) - 1):
            try:
                source_node = created_nodes[i]
                target_node = created_nodes[i + 1]
                
                # Find exec output port on source
                exec_out = source_node.output(0)  # Usually first output
                # Find exec input port on target
                exec_in = target_node.input(0)  # Usually first input
                
                # Connect
                exec_out.connect_to(exec_in)
                logger.debug(f"Connected {source_node.name()} -> {target_node.name()}")
                
            except Exception as e:
                logger.error(f"Failed to connect nodes: {e}")
                continue
        
        logger.info(f"Generated workflow with {len(created_nodes)} nodes")
        self._main_window.set_modified(True)
    
    def _update_debug_panels(self) -> None:
        """Update all debug panels with current data."""
        if not self._workflow_runner or not self._workflow_runner.debug_mode:
            return

        # Update variable inspector dock
        var_inspector = self._main_window.get_variable_inspector()
        if var_inspector and var_inspector.isVisible():
            variables = self._workflow_runner.get_variables()
            var_inspector.update_values(variables)

        # Update execution history
        exec_history = self._main_window.get_execution_history_viewer()
        if exec_history and exec_history.isVisible():
            history = self._workflow_runner.get_execution_history()
            exec_history.update_history(history)
            exec_history.scroll_to_bottom()
    
    def _start_debug_updates(self) -> None:
        """Start periodic debug panel updates."""
        from PySide6.QtCore import QTimer
        
        # Create timer if it doesn't exist
        if not hasattr(self, '_debug_update_timer'):
            self._debug_update_timer = QTimer(self._main_window)
            self._debug_update_timer.timeout.connect(self._update_debug_panels)
        
        # Start timer (update every 200ms)
        self._debug_update_timer.start(200)
        logger.debug("Started debug panel updates")
    
    def _stop_debug_updates(self) -> None:
        """Stop periodic debug panel updates."""
        if hasattr(self, '_debug_update_timer'):
            self._debug_update_timer.stop()
            logger.debug("Stopped debug panel updates")
    
    def _on_workflow_stopped(self, event) -> None:
        """Handle workflow stopped event."""
        executed_nodes = event.data.get("executed_nodes", 0)
        total_nodes = event.data.get("total_nodes", 0)

        logger.info(f"Workflow stopped ({executed_nodes}/{total_nodes} nodes executed)")
        self._main_window.statusBar().showMessage(
            f"Workflow stopped ({executed_nodes}/{total_nodes} nodes)",
            5000
        )

        # Reset UI - re-enable all run actions
        self._main_window.action_run.setEnabled(True)
        self._main_window.action_run_to_node.setEnabled(True)
        self._main_window.action_run_single_node.setEnabled(True)
        self._main_window.action_pause.setEnabled(False)
        self._main_window.action_pause.setChecked(False)
        self._main_window.action_stop.setEnabled(False)

    @property
    def main_window(self) -> MainWindow:
        """
        Get the main window instance.
        
        Returns:
            MainWindow instance
        """
        return self._main_window
    
    @property
    def node_graph(self) -> NodeGraphWidget:
        """
        Get the node graph widget.
        
        Returns:
            NodeGraphWidget instance
        """
        return self._node_graph
    
    @property
    def event_loop(self) -> QEventLoop:
        """
        Get the asyncio event loop.
        
        Returns:
            QEventLoop instance
        """
        return self._loop
    
    def run(self) -> int:
        """
        Run the application.
        
        Returns:
            Application exit code
        """
        logger.info("Starting application")
        self._main_window.show()
        
        with self._loop:
            exit_code = self._loop.run_forever()
        
        logger.info(f"Application exited with code {exit_code}")
        return exit_code if isinstance(exit_code, int) else 0
    
    async def run_async(self) -> int:
        """
        Run the application asynchronously.
        
        This method allows the application to be started from
        an async context if needed.
        
        Returns:
            Application exit code
        """
        logger.info("Starting application (async)")
        self._main_window.show()
        return 0


def main() -> int:
    """
    Main entry point for the application.
    
    Returns:
        Application exit code
    """
    app = CasareRPAApp()
    return app.run()


if __name__ == "__main__":
    sys.exit(main())
