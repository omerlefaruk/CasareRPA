"""
Main application class with qasync integration.

This module provides the CasareRPAApp class which integrates
PySide6 with asyncio using qasync for async workflow execution.
"""

import sys
import asyncio
from typing import Optional

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from qasync import QEventLoop

from .main_window import MainWindow
from .node_graph_widget import NodeGraphWidget
from .node_registry import get_node_registry
from ..runner.workflow_runner import WorkflowRunner
from ..core.workflow_schema import WorkflowSchema, WorkflowMetadata
from ..core.events import EventType, get_event_bus
from ..core.types import NodeStatus
from ..utils.config import setup_logging, APP_NAME
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
        
        # Set node graph as central widget
        self._main_window.set_central_widget(self._node_graph)
        
        # Workflow runner
        self._workflow_runner: Optional[WorkflowRunner] = None
        
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
        
        # Subscribe all events to log viewer
        log_viewer = self._main_window.get_log_viewer()
        if log_viewer:
            for event_type in EventType:
                self._event_bus.subscribe(event_type, log_viewer.log_event)
    
    def _connect_signals(self) -> None:
        """Connect window signals to handlers."""
        # File operations
        self._main_window.workflow_new.connect(self._on_new_workflow)
        self._main_window.workflow_open.connect(self._on_open_workflow)
        self._main_window.workflow_save.connect(self._on_save_workflow)
        self._main_window.workflow_save_as.connect(self._on_save_as_workflow)
        
        # Workflow execution
        self._main_window.workflow_run.connect(self._on_run_workflow)
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
        
        # Other edit operations
        self._main_window.action_delete.triggered.connect(lambda: graph.delete_nodes(graph.selected_nodes()))
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
    
    def _on_new_workflow(self) -> None:
        """Handle new workflow creation."""
        logger.info("Creating new workflow")
        self._node_graph.clear_graph()
        self._main_window.set_modified(False)
    
    def _load_workflow_to_graph(self, workflow: WorkflowSchema) -> None:
        """
        Load a workflow into the node graph.
        
        Args:
            workflow: WorkflowSchema to load
        """
        from .node_registry import get_node_registry
        from ..nodes import NODE_REGISTRY
        
        graph = self._node_graph.graph
        registry = get_node_registry()
        
        # Clear existing graph
        graph.clear_session()
        
        # Create visual nodes from workflow nodes
        node_map = {}  # Map node_id to visual node
        
        for node_id, node_data in workflow.nodes.items():
            node_type = node_data.get("node_type")
            
            # Get the node class from registry
            if node_type in NODE_REGISTRY:
                node_class = NODE_REGISTRY[node_type]
                
                # Get the visual node class name
                visual_class_name = f"Visual{node_type}"
                
                # Create visual node in graph
                visual_node = graph.create_node(
                    f"casare_rpa.{node_class.CATEGORY}.{visual_class_name}"
                )
                
                if visual_node:
                    # Create the underlying CasareRPA node
                    casare_node = node_class(node_id, node_data.get("config", {}))
                    visual_node.set_casare_node(casare_node)
                    
                    # Set node position if available
                    pos = node_data.get("position", {})
                    if pos:
                        visual_node.set_pos(pos.get("x", 0), pos.get("y", 0))
                    
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
                
                # Add node positions to serialization
                graph = self._node_graph.graph
                for visual_node in graph.all_nodes():
                    node_id = visual_node.get_property("node_id")
                    if node_id in workflow.nodes:
                        pos = visual_node.pos()
                        workflow.nodes[node_id]["position"] = {"x": pos[0], "y": pos[1]}
                
                # Save to file
                workflow.save_to_file(current_file)
                
                self._main_window.set_modified(False)
                self._main_window.statusBar().showMessage(f"Saved: {current_file.name}", 3000)
                
            except Exception as e:
                logger.exception("Failed to save workflow")
                self._main_window.statusBar().showMessage(f"Error saving file: {str(e)}", 5000)
    
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
            
            # Add node positions to serialization
            graph = self._node_graph.graph
            for visual_node in graph.all_nodes():
                node_id = visual_node.get_property("node_id")
                if node_id in workflow.nodes:
                    pos = visual_node.pos()
                    workflow.nodes[node_id]["position"] = {"x": pos[0], "y": pos[1]}
            
            # Save to file
            workflow.save_to_file(Path(file_path))
            
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
                
                if widget_value is not None and widget_value != "":
                    casare_node.config[widget_name] = widget_value
                    synced_count += 1
                    logger.info(f"  ✓ Synced {casare_node.node_type}.{widget_name} = '{widget_value}'")
            except Exception as e:
                logger.warning(f"Could not sync widget {widget_name}: {e}")
        
        if synced_count == 0:
            logger.info(f"No widgets synced for {casare_node.node_type}")
    
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
        logger.info(f"Building workflow from {len(graph.all_nodes())} visual nodes")
        for visual_node in graph.all_nodes():
            # Get the underlying CasareRPA node
            casare_node = visual_node.get_casare_node()
            if casare_node:
                logger.info(f"Processing visual node: {visual_node.name()} -> {casare_node.node_type}")
                # Sync visual node properties to CasareRPA node config
                self._sync_visual_properties_to_node(visual_node, casare_node)
                nodes_dict[casare_node.node_id] = casare_node
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
                entry_nodes.append(casare_node.node_id)
        
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
            # Get the CasareRPA node to access node_id
            source_casare_node = node.get_casare_node()
            if not source_casare_node:
                continue
            
            # Get output connections
            for output_port in node.output_ports():
                for connected_port in output_port.connected_ports():
                    target_casare_node = connected_port.node().get_casare_node()
                    if not target_casare_node:
                        continue
                    
                    connection = NodeConnection(
                        source_node=source_casare_node.node_id,
                        source_port=output_port.name(),
                        target_node=target_casare_node.node_id,
                        target_port=connected_port.name()
                    )
                    connections.append(connection)
        
        workflow.connections = connections
        
        return workflow
    
    def _on_run_workflow(self) -> None:
        """Handle workflow execution."""
        try:
            logger.info("Starting workflow execution")
            
            # Create workflow from current graph
            workflow = self._create_workflow_from_graph()
            
            # Create workflow runner
            self._workflow_runner = WorkflowRunner(workflow, self._event_bus)
            
            # Show log viewer
            self._main_window.show_log_viewer()
            self._main_window.action_toggle_log.setChecked(True)
            
            # Run workflow asynchronously
            asyncio.ensure_future(self._workflow_runner.run())
            
        except Exception as e:
            logger.exception("Failed to start workflow execution")
            self._main_window.statusBar().showMessage(f"Error: {str(e)}", 5000)
    
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
        
        if node_id:
            # Find visual node and update status
            graph = self._node_graph.graph
            for visual_node in graph.all_nodes():
                if visual_node.get_property("node_id") == node_id:
                    visual_node.update_status("success")
                    break
        
        # Update progress in status bar
        self._main_window.statusBar().showMessage(
            f"Workflow progress: {progress:.1f}%",
            0
        )
    
    def _on_node_error(self, event) -> None:
        """Handle node error event."""
        node_id = event.data.get("node_id")
        error = event.data.get("error", "Unknown error")
        
        if node_id:
            # Find visual node and update status
            graph = self._node_graph.graph
            for visual_node in graph.all_nodes():
                if visual_node.get_property("node_id") == node_id:
                    visual_node.update_status("error")
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
        
        # Reset UI
        self._main_window.action_run.setEnabled(True)
        self._main_window.action_pause.setEnabled(False)
        self._main_window.action_pause.setChecked(False)
        self._main_window.action_stop.setEnabled(False)
    
    def _on_workflow_error(self, event) -> None:
        """Handle workflow error event."""
        error = event.data.get("error", "Unknown error")
        executed_nodes = event.data.get("executed_nodes", 0)
        
        logger.error(f"Workflow failed: {error}")
        self._main_window.statusBar().showMessage(f"Workflow failed: {error}", 5000)
        
        # Reset UI
        self._main_window.action_run.setEnabled(True)
        self._main_window.action_pause.setEnabled(False)
        self._main_window.action_pause.setChecked(False)
        self._main_window.action_stop.setEnabled(False)
    
    def _on_workflow_stopped(self, event) -> None:
        """Handle workflow stopped event."""
        executed_nodes = event.data.get("executed_nodes", 0)
        total_nodes = event.data.get("total_nodes", 0)
        
        logger.info(f"Workflow stopped ({executed_nodes}/{total_nodes} nodes executed)")
        self._main_window.statusBar().showMessage(
            f"Workflow stopped ({executed_nodes}/{total_nodes} nodes)",
            5000
        )
        
        # Reset UI
        self._main_window.action_run.setEnabled(True)
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
