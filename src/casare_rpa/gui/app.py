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
        
        # Connect signals
        self._connect_signals()
        
        logger.info("Application initialized successfully")
    
    def _connect_signals(self) -> None:
        """Connect window signals to handlers."""
        # File operations
        self._main_window.workflow_new.connect(self._on_new_workflow)
        self._main_window.workflow_open.connect(self._on_open_workflow)
        self._main_window.workflow_save.connect(self._on_save_workflow)
        self._main_window.workflow_save_as.connect(self._on_save_as_workflow)
        
        # Workflow execution
        self._main_window.workflow_run.connect(self._on_run_workflow)
        self._main_window.workflow_stop.connect(self._on_stop_workflow)
        
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
    
    def _on_open_workflow(self, file_path: str) -> None:
        """
        Handle workflow opening.
        
        Args:
            file_path: Path to workflow file
        """
        logger.info(f"Opening workflow: {file_path}")
        # TODO: Implement workflow loading in Phase 4
        self._main_window.set_modified(False)
    
    def _on_save_workflow(self) -> None:
        """Handle workflow saving."""
        current_file = self._main_window.get_current_file()
        if current_file:
            logger.info(f"Saving workflow: {current_file}")
            # TODO: Implement workflow saving in Phase 4
            self._main_window.set_modified(False)
    
    def _on_save_as_workflow(self, file_path: str) -> None:
        """
        Handle save as workflow.
        
        Args:
            file_path: Path to save workflow
        """
        logger.info(f"Saving workflow as: {file_path}")
        # TODO: Implement workflow saving in Phase 4
        self._main_window.set_modified(False)
    
    def _on_run_workflow(self) -> None:
        """Handle workflow execution."""
        logger.info("Starting workflow execution")
        # TODO: Implement workflow execution in Phase 4
        # This will use asyncio to run Playwright automation
    
    def _on_stop_workflow(self) -> None:
        """Handle workflow stop."""
        logger.info("Stopping workflow execution")
        # TODO: Implement workflow stopping in Phase 4
    
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
