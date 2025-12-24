"""
Signal Coordinator for MainWindow.

Extracts signal connection and event handling logic from MainWindow to
reduce its responsibilities. Handles action handlers, recording callbacks,
and project management events.

Usage:
    coordinator = SignalCoordinator(main_window)
    # Actions are connected via ActionManager, handlers route here
"""

import asyncio
from typing import TYPE_CHECKING, Any

from loguru import logger
from PySide6.QtCore import QTimer, Slot
from PySide6.QtWidgets import QApplication, QLineEdit, QTextEdit

if TYPE_CHECKING:
    from ..main_window import MainWindow


class SignalCoordinator:
    """
    Coordinates signal handling and action callbacks for MainWindow.

    Responsibilities:
    - Handle workflow action callbacks (new, open, save, etc.)
    - Handle execution action callbacks (run, pause, stop, etc.)
    - Handle debug action callbacks (step over, step into, etc.)
    - Handle node action callbacks (select, rename, toggle, etc.)
    - Handle recording callbacks (browser recording start/stop)
    - Handle project management callbacks

    Design:
    - Receives MainWindow reference for accessing controllers
    - Methods are called by action triggers from ActionManager
    - Delegates actual work to appropriate controllers
    """

    def __init__(self, main_window: "MainWindow") -> None:
        """
        Initialize the signal coordinator.

        Args:
            main_window: Reference to parent MainWindow
        """
        self._mw = main_window
        self._browser_recorder = None
        self._recording_stop_in_progress = False
        self._connections: list = []  # Track signal connections for cleanup

    def _connect(self, signal, slot, conn_type=None) -> None:
        """
        Connect a signal to a slot and track for cleanup.

        Args:
            signal: Qt signal to connect
            slot: Slot/callback to receive signal
            conn_type: Optional Qt.ConnectionType for cross-thread safety
        """
        if conn_type:
            signal.connect(slot, conn_type)
        else:
            signal.connect(slot)
        self._connections.append((signal, slot))

    def cleanup(self) -> None:
        """
        Disconnect all tracked signals and release resources.

        Called during MainWindow shutdown to prevent dangling connections.
        """
        for signal, slot in self._connections:
            try:
                signal.disconnect(slot)
            except RuntimeError:
                pass  # Already disconnected
        self._connections.clear()
        self._browser_recorder = None
        logger.debug("SignalCoordinator cleanup complete")

    # ==================== Workflow Actions ====================

    @Slot()
    def on_new_workflow(self) -> None:
        """Handle new workflow action."""
        if self._mw._workflow_controller:
            self._mw._workflow_controller.new_workflow()

    @Slot()
    def on_open_workflow(self) -> None:
        """Handle open workflow action."""
        if self._mw._workflow_controller:
            self._mw._workflow_controller.open_workflow()

    @Slot()
    def on_reload_workflow(self) -> None:
        """Handle reload workflow action (Ctrl+Shift+R)."""
        if self._mw._workflow_controller:
            self._mw._workflow_controller.reload_workflow()

    @Slot()
    def on_import_workflow(self) -> None:
        """Handle import workflow action."""
        if self._mw._workflow_controller:
            self._mw._workflow_controller.import_workflow()

    @Slot()
    def on_export_selected(self) -> None:
        """Handle export selected nodes action."""
        if self._mw._workflow_controller:
            self._mw._workflow_controller.export_selected_nodes()

    @Slot()
    def on_paste_workflow(self) -> None:
        """Handle paste workflow action."""
        if self._mw._workflow_controller:
            self._mw._workflow_controller.paste_workflow()

    @Slot()
    def on_save_workflow(self) -> None:
        """Handle save workflow action."""
        if self._mw._workflow_controller:
            self._mw._workflow_controller.save_workflow()
        else:
            logger.warning("Cannot save: workflow controller not initialized")

    @Slot()
    def on_save_as_workflow(self) -> None:
        """Handle save as workflow action."""
        if self._mw._workflow_controller:
            self._mw._workflow_controller.save_workflow_as()

    # ==================== Execution Actions ====================

    @Slot()
    def on_run_workflow(self) -> None:
        """Handle run workflow action."""
        if self._mw._execution_controller:
            self._mw._execution_controller.run_workflow()

    @Slot()
    def on_run_to_node(self) -> None:
        """Handle run to node action."""
        if self._mw._execution_controller:
            self._mw._execution_controller.run_to_node()

    @Slot()
    def on_run_single_node(self) -> None:
        """Handle run single node action."""
        if self._mw._execution_controller:
            self._mw._execution_controller.run_single_node()

    @Slot()
    def on_run_all_workflows(self) -> None:
        """Run all workflows on canvas concurrently (Shift+F3)."""
        if self._mw._execution_controller:
            self._mw._execution_controller.run_all_workflows()

    @Slot()
    def on_run_local(self) -> None:
        """Handle run local action."""
        if self._mw._workflow_controller:
            asyncio.create_task(self._mw._workflow_controller.run_local())

    @Slot()
    def on_run_on_robot(self) -> None:
        """Handle run on robot action."""
        if self._mw._workflow_controller:
            asyncio.create_task(self._mw._workflow_controller.run_on_robot())

    @Slot()
    def on_submit(self) -> None:
        """Handle submit for internet robots action."""
        if self._mw._workflow_controller:
            asyncio.create_task(self._mw._workflow_controller.submit_for_internet_robots())

    @Slot(bool)
    def on_pause_workflow(self, checked: bool) -> None:
        """Handle pause workflow toggle."""
        if self._mw._execution_controller:
            self._mw._execution_controller.toggle_pause(checked)

    @Slot()
    def on_stop_workflow(self) -> None:
        """Handle stop workflow action."""
        if self._mw._execution_controller:
            self._mw._execution_controller.stop_workflow()

    @Slot()
    def on_restart_workflow(self) -> None:
        """Restart workflow - stop, reset, and run fresh (F8)."""
        if self._mw._execution_controller:
            self._mw._execution_controller.restart_workflow()

    @Slot()
    def on_start_listening(self) -> None:
        """Start listening for trigger events (F9)."""
        if self._mw._execution_controller:
            self._mw._execution_controller.start_trigger_listening()
            if hasattr(self._mw, "action_start_listening"):
                self._mw.action_start_listening.setEnabled(False)
            if hasattr(self._mw, "action_stop_listening"):
                self._mw.action_stop_listening.setEnabled(True)

    @Slot()
    def on_stop_listening(self) -> None:
        """Stop listening for trigger events (Shift+F9)."""
        if self._mw._execution_controller:
            self._mw._execution_controller.stop_trigger_listening()
            if hasattr(self._mw, "action_start_listening"):
                self._mw.action_start_listening.setEnabled(True)
            if hasattr(self._mw, "action_stop_listening"):
                self._mw.action_stop_listening.setEnabled(False)

    # ==================== Debug Actions ====================

    @Slot()
    def on_debug_workflow(self) -> None:
        """Handle debug workflow action."""
        if self._mw._execution_controller:
            self._mw._execution_controller.debug_workflow()

    @Slot(bool)
    def on_debug_mode_toggled(self, enabled: bool) -> None:
        """Handle debug mode toggle."""
        if self._mw._execution_controller:
            self._mw._execution_controller.set_debug_mode(enabled)
        if self._mw._debug_panel:
            if enabled:
                self._mw._debug_panel.show()
            else:
                self._mw._debug_panel.hide()
        logger.debug(f"Debug mode {'enabled' if enabled else 'disabled'}")

    @Slot()
    def on_debug_step_over(self) -> None:
        """Handle step over in debug mode."""
        if self._mw._execution_controller:
            self._mw._execution_controller.step_over()

    @Slot()
    def on_debug_step_into(self) -> None:
        """Handle step into in debug mode."""
        if self._mw._execution_controller:
            self._mw._execution_controller.step_into()

    @Slot()
    def on_debug_step_out(self) -> None:
        """Handle step out in debug mode."""
        if self._mw._execution_controller:
            self._mw._execution_controller.step_out()

    @Slot()
    def on_debug_continue(self) -> None:
        """Handle continue in debug mode."""
        if self._mw._execution_controller:
            self._mw._execution_controller.continue_execution()

    @Slot()
    def on_toggle_breakpoint(self) -> None:
        """Handle toggle breakpoint on selected node."""
        if self._mw._node_controller:
            selected = self._mw._node_controller.get_selected_nodes()
            if selected and self._mw._execution_controller:
                self._mw._execution_controller.toggle_breakpoint(selected[0])

    @Slot()
    def on_clear_breakpoints(self) -> None:
        """Handle clear all breakpoints."""
        if self._mw._execution_controller:
            self._mw._execution_controller.clear_breakpoints()

    # ==================== Node Actions ====================

    def _is_text_widget_focused(self) -> bool:
        """Check if text input widget has focus (for hotkey suppression)."""
        focus_widget = QApplication.focusWidget()
        return isinstance(focus_widget, QLineEdit | QTextEdit)

    @Slot()
    def on_select_nearest_node(self) -> None:
        """Select nearest node to cursor."""
        if self._is_text_widget_focused():
            return
        if self._mw._node_controller:
            self._mw._node_controller.select_nearest_node()

    @Slot()
    def on_toggle_collapse_nearest(self) -> None:
        """Toggle collapse/expand on nearest node (hotkey 1)."""
        if self._is_text_widget_focused():
            return
        if self._mw._node_controller:
            self._mw._node_controller.toggle_collapse_nearest_node()

    @Slot()
    def on_toggle_disable_node(self) -> None:
        """Toggle disable state on selected node."""
        if self._is_text_widget_focused():
            return
        if self._mw._node_controller:
            self._mw._node_controller.toggle_disable_node()

    @Slot()
    def on_disable_all_selected(self) -> None:
        """Disable all selected nodes."""
        if self._is_text_widget_focused():
            return
        if self._mw._node_controller:
            self._mw._node_controller.disable_all_selected()

    @Slot()
    def on_toggle_cache_node(self) -> None:
        """Toggle cache state on nearest node (Ctrl+K)."""
        if self._is_text_widget_focused():
            return
        if self._mw._node_controller:
            self._mw._node_controller.toggle_cache_node()

    @Slot()
    def on_rename_node(self) -> None:
        """Rename selected node (F2)."""
        if self._is_text_widget_focused():
            return
        graph = self._mw.graph
        if not graph:
            return
        selected = graph.selected_nodes()
        if not selected:
            self._mw.show_status("No node selected", 2000)
            return
        node = selected[0]
        current_name = node.name() if hasattr(node, "name") else "Node"
        from PySide6.QtWidgets import QInputDialog

        new_name, ok = QInputDialog.getText(
            self._mw, "Rename Node", "Enter new name:", text=current_name
        )
        if ok and new_name and new_name != current_name:
            node.set_name(new_name)
            self._mw.show_status(f"Renamed to: {new_name}", 2000)

    @Slot()
    def on_get_exec_out(self) -> None:
        """Get nearest node's exec_out port (hotkey 3)."""
        if self._is_text_widget_focused():
            return
        if self._mw._node_controller:
            self._mw._node_controller.get_nearest_exec_out()

    @Slot()
    def on_find_node(self) -> None:
        """Open find node dialog."""
        if self._mw._node_controller:
            self._mw._node_controller.find_node()

    # ==================== View/UI Actions ====================

    @Slot()
    def on_focus_view(self) -> None:
        """Focus view: zoom to selected node (F)."""
        if self._is_text_widget_focused():
            return
        if self._mw._viewport_controller:
            self._mw._viewport_controller.focus_view()

    @Slot()
    def on_home_all(self) -> None:
        """Home all: fit all nodes in view (G)."""
        if self._is_text_widget_focused():
            return
        if self._mw._viewport_controller:
            self._mw._viewport_controller.home_all()

    @Slot(bool)
    def on_toggle_minimap(self, checked: bool) -> None:
        """Handle minimap toggle."""
        if self._mw._viewport_controller:
            self._mw._viewport_controller.toggle_minimap(checked)
        elif checked:
            self._mw.show_minimap()
        else:
            self._mw.hide_minimap()

    @Slot()
    def on_create_frame(self) -> None:
        """Create frame around selected nodes."""
        if self._mw._viewport_controller:
            self._mw._viewport_controller.create_frame()

    @Slot()
    def on_save_ui_layout(self) -> None:
        """Save current UI layout."""
        if self._mw._ui_state_controller:
            self._mw._ui_state_controller.save_state()
            self._mw.show_status("UI layout saved", 3000)
        else:
            logger.warning("Cannot save UI layout: controller not initialized")

    # ==================== Mode Toggles ====================

    @Slot(bool)
    def on_toggle_auto_connect(self, checked: bool) -> None:
        """
        Toggle auto-connect mode for node connections.

        When enabled, canvas suggests connections when dragging near
        compatible ports. Right-click confirms suggestions.
        """
        self._mw._auto_connect_enabled = checked

        graph_widget = self._mw._central_widget
        if graph_widget and hasattr(graph_widget, "set_auto_connect_enabled"):
            graph_widget.set_auto_connect_enabled(checked)
            logger.debug(f"Auto-connect set on graph widget: {checked}")

        try:
            from casare_rpa.utils.settings_manager import get_settings_manager

            settings = get_settings_manager()
            settings.set("canvas.auto_connect", checked)
        except Exception as e:
            logger.debug(f"Could not save auto-connect preference: {e}")

        status = "enabled" if checked else "disabled"
        self._mw.show_status(f"Auto-connect {status}", 2000)
        logger.debug(f"Auto-connect mode: {status}")

    @Slot(bool)
    def on_toggle_high_performance_mode(self, checked: bool) -> None:
        """
        Toggle high performance rendering mode.

        Forces simplified LOD rendering at all zoom levels for
        smoother interaction with large workflows (50+ nodes).
        """
        graph_widget = self._mw._central_widget
        if graph_widget and hasattr(graph_widget, "set_high_performance_mode"):
            graph_widget.set_high_performance_mode(checked)

        status = "enabled" if checked else "disabled"
        self._mw.show_status(f"High Performance Mode {status}", 2000)

    @Slot(bool)
    def on_toggle_quick_node_mode(self, checked: bool) -> None:
        """
        Toggle quick node creation mode.

        When enabled, single letter hotkeys create nodes at cursor.
        Example: 'b' creates Launch Browser, 'c' creates Click Element.
        """
        if self._mw._quick_node_manager:
            self._mw._quick_node_manager.set_enabled(checked)

        try:
            from casare_rpa.utils.settings_manager import get_settings_manager

            settings = get_settings_manager()
            settings.set("canvas.quick_node_mode", checked)
        except Exception as e:
            logger.debug(f"Could not save quick node mode preference: {e}")

        status = "enabled" if checked else "disabled"
        self._mw.show_status(f"Quick node mode {status} (press letter keys to create nodes)", 2500)
        logger.debug(f"Quick node mode: {status}")

    # ==================== Menu Actions ====================

    @Slot()
    def on_preferences(self) -> None:
        """Open preferences dialog."""
        if self._mw._menu_controller:
            self._mw._menu_controller.open_preferences()

    @Slot()
    def on_open_hotkey_manager(self) -> None:
        """Open hotkey manager dialog."""
        if self._mw._menu_controller:
            self._mw._menu_controller.open_hotkey_manager()

    @Slot()
    def on_open_performance_dashboard(self) -> None:
        """Open performance dashboard."""
        if self._mw._menu_controller:
            self._mw._menu_controller.open_performance_dashboard()

    @Slot()
    def on_open_command_palette(self) -> None:
        """Open command palette."""
        if self._mw._menu_controller:
            self._mw._menu_controller.open_command_palette()

    @Slot()
    def on_open_quick_node_config(self) -> None:
        """Open Quick Node Hotkey Configuration dialog."""
        from ..ui.dialogs import QuickNodeConfigDialog

        dialog = QuickNodeConfigDialog(self._mw._quick_node_manager, self._mw)
        dialog.exec()

    @Slot(str)
    def on_open_recent_file(self, path: str) -> None:
        """Open a recent file."""
        if self._mw._menu_controller:
            self._mw._menu_controller.open_recent_file(path)

    @Slot()
    def on_clear_recent_files(self) -> None:
        """Clear recent files list."""
        if self._mw._menu_controller:
            self._mw._menu_controller.clear_recent_files()

    @Slot()
    def on_about(self) -> None:
        """Show about dialog."""
        if self._mw._menu_controller:
            self._mw._menu_controller.show_about_dialog()

    @Slot()
    def on_show_documentation(self) -> None:
        """Show documentation."""
        if self._mw._menu_controller:
            self._mw._menu_controller.show_documentation()

    @Slot()
    def on_show_keyboard_shortcuts(self) -> None:
        """Show keyboard shortcuts dialog."""
        if self._mw._menu_controller:
            self._mw._menu_controller.show_keyboard_shortcuts()

    @Slot()
    def on_check_updates(self) -> None:
        """Check for updates."""
        if self._mw._menu_controller:
            self._mw._menu_controller.check_for_updates()

    # ==================== Selector/Picker Actions ====================

    @Slot()
    def on_pick_selector(self) -> None:
        """Legacy handler - delegates to unified picker."""
        self.on_pick_element()

    @Slot()
    def on_pick_element(self) -> None:
        """Show unified element selector (browser mode by default)."""
        if self._mw._selector_controller:
            self._mw._selector_controller.show_unified_selector_dialog(
                target_node=None,
                target_property="selector",
                initial_mode="browser",
            )

    @Slot()
    def on_pick_element_desktop(self) -> None:
        """Show unified element selector with desktop mode."""
        if self._mw._selector_controller:
            self._mw._selector_controller.show_unified_selector_dialog(
                target_node=None,
                target_property="selector",
                initial_mode="desktop",
            )

    @Slot()
    def on_open_desktop_selector_builder(self) -> None:
        """Legacy handler - delegates to unified picker desktop tab."""
        self.on_pick_element_desktop()

    # ==================== Recording Actions ====================

    @Slot(bool)
    def on_toggle_browser_recording(self, checked: bool) -> None:
        """Toggle browser recording mode using BrowserRecorder."""
        if checked:
            asyncio.create_task(self._start_browser_recording())
        else:
            asyncio.create_task(self._stop_browser_recording())

    async def _start_browser_recording(self) -> None:
        """Start recording browser interactions."""
        try:
            page = None
            if self._mw._selector_controller:
                page = self._mw._selector_controller.get_browser_page()

            if not page:
                from PySide6.QtWidgets import QMessageBox

                QMessageBox.warning(
                    self._mw,
                    "Recording Error",
                    "No browser page available. Please run a workflow with " "Open Browser first.",
                )
                self._mw.action_record_workflow.setChecked(False)
                return

            # Use application service instead of infrastructure import
            from casare_rpa.application.services import get_browser_recording_service

            recording_service = get_browser_recording_service()
            self._browser_recorder = recording_service.create_recorder(page)

            def on_stop_from_browser():
                QTimer.singleShot(0, self._on_recording_stop_requested)

            recording_service.set_recorder_callbacks(
                self._browser_recorder,
                on_recording_stopped=on_stop_from_browser,
            )

            await recording_service.start_recording(self._browser_recorder)
            self._show_recording_panel()
            logger.info("Browser recording started")

        except Exception as e:
            logger.error(f"Failed to start browser recording: {e}")
            self._mw.action_record_workflow.setChecked(False)

    def _on_recording_stop_requested(self) -> None:
        """Handle stop request from browser (Escape pressed)."""
        if self._recording_stop_in_progress:
            return
        self._recording_stop_in_progress = True

        logger.info("Recording stop requested from browser")
        self._mw.action_record_workflow.blockSignals(True)
        self._mw.action_record_workflow.setChecked(False)
        self._mw.action_record_workflow.blockSignals(False)
        self.on_toggle_browser_recording(False)

    async def _stop_browser_recording(self) -> None:
        """Stop browser recording and convert to workflow."""
        try:
            if not self._browser_recorder:
                return

            recorder = self._browser_recorder
            self._browser_recorder = None

            # Use application service instead of infrastructure import
            from casare_rpa.application.services import get_browser_recording_service

            recording_service = get_browser_recording_service()
            actions = await recording_service.stop_recording(recorder)

            if actions:
                workflow_data = recording_service.generate_workflow_from_actions(actions)
                nodes = list(workflow_data.get("nodes", {}).values())

                if nodes:
                    from casare_rpa.presentation.canvas.ui.dialogs import (
                        RecordingReviewDialog,
                    )

                    dialog = RecordingReviewDialog(nodes, parent=self._mw)
                    dialog.accepted_with_data.connect(self._on_recording_review_accepted)
                    dialog.exec()

            logger.info(f"Recording stopped: {len(actions) if actions else 0} actions")

        except Exception as e:
            logger.error(f"Failed to stop browser recording: {e}")
        finally:
            self._recording_stop_in_progress = False

    def _show_recording_panel(self) -> None:
        """Show the browser recording panel."""
        logger.debug("Recording panel: recording in progress...")

    def _on_recording_review_accepted(self, nodes_data: list, include_waits: bool) -> None:
        """Handle accepted recording review - create nodes on canvas."""
        if not nodes_data:
            return

        final_nodes: dict[str, dict[str, Any]] = {}
        connections = []

        for i, node in enumerate(nodes_data):
            node_id = node.get("node_id", f"action_{i+1}")
            final_nodes[node_id] = node

            if include_waits and i < len(nodes_data) - 1:
                wait_time = node.get("config", {}).get("wait_after", 500)
                if wait_time > 0:
                    wait_id = f"wait_{i+1}"
                    final_nodes[wait_id] = {
                        "node_id": wait_id,
                        "node_type": "WaitNode",
                        "name": f"Wait {wait_time}ms",
                        "config": {"duration": wait_time},
                    }
                    connections.append(
                        {
                            "source_node": node_id,
                            "source_port": "exec_out",
                            "target_node": wait_id,
                            "target_port": "exec_in",
                        }
                    )
                    next_node = nodes_data[i + 1]
                    next_id = next_node.get("node_id", f"action_{i+2}")
                    connections.append(
                        {
                            "source_node": wait_id,
                            "source_port": "exec_out",
                            "target_node": next_id,
                            "target_port": "exec_in",
                        }
                    )
            elif i < len(nodes_data) - 1:
                next_node = nodes_data[i + 1]
                next_id = next_node.get("node_id", f"action_{i+2}")
                connections.append(
                    {
                        "source_node": node_id,
                        "source_port": "exec_out",
                        "target_node": next_id,
                        "target_port": "exec_in",
                    }
                )

        workflow_data = {"nodes": final_nodes, "connections": connections}
        self._create_workflow_from_recording(workflow_data)

    def _create_workflow_from_recording(self, workflow_data: dict) -> None:
        """Add recorded browser actions to canvas."""
        graph = self._mw.get_graph()
        if not graph:
            return

        VISUAL_NODE_TYPE_MAP = {
            "ClickElementNode": "casare_rpa.interaction.VisualClickElementNode",
            "TypeTextNode": "casare_rpa.interaction.VisualTypeTextNode",
            "PressEnterNode": "casare_rpa.interaction.VisualTypeTextNode",
            "SelectDropdownNode": "casare_rpa.interaction.VisualSelectDropdownNode",
            "SelectOptionNode": "casare_rpa.interaction.VisualSelectDropdownNode",
            "CheckboxNode": "casare_rpa.desktop.VisualCheckCheckboxNode",
            "SendHotKeyNode": "casare_rpa.desktop.VisualSendHotKeyNode",
            "WaitNode": "casare_rpa.wait.VisualWaitNode",
        }

        nodes_data = workflow_data.get("nodes", {})
        connections_data = workflow_data.get("connections", [])
        if not nodes_data:
            return

        launch_browser_node = None
        start_x, start_y = 500, 200
        for node in graph.all_nodes():
            if "LaunchBrowser" in node.type_ or "Launch Browser" in node.name():
                launch_browser_node = node
                pos = node.pos()
                start_x = pos[0] + 400
                start_y = pos[1]
                break

        created_nodes = {}
        current_x = start_x
        first_node = None
        NODE_SPACING = 450

        for node_id, node_data in nodes_data.items():
            node_type = node_data.get("node_type")
            visual_type = VISUAL_NODE_TYPE_MAP.get(node_type)
            if not visual_type:
                continue

            node = graph.create_node(visual_type, pos=[current_x, start_y])
            if node:
                created_nodes[node_id] = node
                if first_node is None:
                    first_node = node
                for key, value in node_data.get("config", {}).items():
                    try:
                        node.set_property(key, value)
                    except Exception:
                        pass
                if node_type == "PressEnterNode":
                    try:
                        node.set_property("text", "")
                        node.set_property("press_enter_after", True)
                    except Exception:
                        pass
                current_x += NODE_SPACING

        if launch_browser_node and first_node:
            try:
                lb_exec = launch_browser_node.get_output("exec_out")
                first_exec = first_node.get_input("exec_in")
                if lb_exec and first_exec:
                    lb_exec.connect_to(first_exec)
                lb_page = launch_browser_node.get_output("page")
                first_page = first_node.get_input("page")
                if lb_page and first_page:
                    lb_page.connect_to(first_page)
            except Exception:
                pass

        for conn in connections_data:
            from_node = created_nodes.get(conn.get("source_node"))
            to_node = created_nodes.get(conn.get("target_node"))
            if from_node and to_node:
                try:
                    out_port = from_node.get_output(conn.get("source_port", "exec_out"))
                    in_port = to_node.get_input(conn.get("target_port", "exec_in"))
                    if out_port and in_port:
                        out_port.connect_to(in_port)
                except Exception:
                    pass

        if created_nodes:
            graph.clear_selection()
            for node in created_nodes.values():
                node.set_selected(True)
            if hasattr(graph, "fit_to_selection"):
                graph.fit_to_selection()
            logger.info(f"Added {len(created_nodes)} nodes")

    # ==================== Project Management ====================

    @Slot()
    def on_project_manager(self) -> None:
        """Open the project manager dialog."""
        if self._mw._project_controller:
            self._mw._project_controller.show_project_manager()

    @Slot(str)
    def on_project_opened(self, project_id: str) -> None:
        """Handle project opened from Project Explorer."""
        logger.info(f"Opening project: {project_id}")
        if self._mw._project_controller:
            self._mw._project_controller.load_project(project_id)

    @Slot(str)
    def on_project_selected(self, project_id: str) -> None:
        """Handle project selection from Project Explorer."""
        logger.debug(f"Project selected: {project_id}")

    @Slot(str)
    def on_credential_updated(self, credential_id: str) -> None:
        """Handle credential updated - refresh nodes that use credentials."""
        logger.info(f"Credential updated: {credential_id}")
        graph = self._mw.get_graph()
        if graph:
            for node in graph.all_nodes():
                if hasattr(node, "refresh_credential"):
                    node.refresh_credential(credential_id)

    @Slot()
    def on_open_credential_manager(self) -> None:
        """Open the Credential Manager dialog."""
        try:
            from casare_rpa.presentation.canvas.ui.dialogs.credential_manager_dialog import (
                CredentialManagerDialog,
            )

            dialog = CredentialManagerDialog(self._mw)
            dialog.exec()
        except Exception as e:
            logger.error(f"Failed to open Credential Manager: {e}")

    @Slot()
    def on_fleet_dashboard(self) -> None:
        """Open the fleet management dashboard dialog."""
        self._mw._fleet_dashboard_manager.open_dashboard()

    # ==================== AI Assistant ====================

    @Slot(dict)
    def on_ai_workflow_ready(self, workflow_data: dict) -> None:
        """
        Handle AI-generated workflow ready for canvas.

        Args:
            workflow_data: Validated workflow JSON from AI Assistant
                          Can be either:
                          - New nodes: {"nodes": {...}, "connections": [...]}
                          - Edits: {"action": "edit", "modifications": [...]}
        """
        logger.info("=" * 60)
        logger.info("AI workflow ready - processing response")
        logger.info(
            f"Workflow data keys: {list(workflow_data.keys()) if workflow_data else 'None'}"
        )

        if not workflow_data:
            logger.warning("Empty workflow data from AI Assistant")
            return

        # Check if this is an edit response
        if workflow_data.get("action") == "edit":
            logger.info("Processing EDIT response - modifying existing nodes")
            self._apply_ai_edits(workflow_data.get("modifications", []))
            return

        # Otherwise, add new nodes to canvas
        logger.info("Processing ADD response - creating new nodes")

        graph = self._mw.get_graph()
        logger.info(f"Graph obtained: {graph is not None}")
        if not graph:
            logger.warning("No graph available for AI workflow")
            return

        nodes_data = workflow_data.get("nodes", {})
        connections_data = workflow_data.get("connections", [])
        logger.info(
            f"Nodes data type: {type(nodes_data).__name__}, count: {len(nodes_data) if nodes_data else 0}"
        )
        logger.info(f"Connections count: {len(connections_data)}")

        if not nodes_data:
            logger.warning("No nodes in AI workflow")
            return

        if not isinstance(nodes_data, dict):
            logger.warning(f"Invalid nodes_data format: {type(nodes_data)}")
            return
        nodes_items = list(nodes_data.items())

        # Build node type map from registered nodes
        node_type_map = self._build_ai_node_type_map(graph)
        logger.info(f"Node type map has {len(node_type_map)} entries")
        logger.info(f"Sample node types: {list(node_type_map.keys())[:10]}")

        # Find position to place new nodes (avoid overlap)
        start_x, start_y = self._find_ai_workflow_position(graph)
        logger.info(f"Start position: ({start_x}, {start_y})")

        # Create nodes
        created_nodes = {}
        skipped_nodes = []  # Track skipped nodes for user feedback
        for node_id, node_data in nodes_items:
            node_type = node_data.get("node_type")
            logger.info(f"Processing node: {node_id} -> {node_type}")
            if not node_type:
                logger.warning(f"Node {node_id} has no node_type (keys: {list(node_data.keys())})")
                skipped_nodes.append((node_id, "no node_type", None))
                continue

            # Find the NodeGraphQt identifier
            identifier = node_type_map.get(node_type)

            # Case-insensitive fallback if exact match not found
            if not identifier:
                node_type_lower = node_type.lower()
                for key, value in node_type_map.items():
                    if key.lower() == node_type_lower:
                        identifier = value
                        logger.info(f"  Found case-insensitive match: {node_type} -> {key}")
                        break

            logger.info(f"  Identifier for {node_type}: {identifier}")
            if not identifier:
                logger.warning(f"Unknown node type: {node_type} (not in map)")
                logger.warning(f"  Available types: {list(node_type_map.keys())}")
                skipped_nodes.append((node_id, node_type, "not registered"))
                continue

            # Calculate position with offset from workflow data
            pos = node_data.get("position", [0, 0])
            if isinstance(pos, list | tuple) and len(pos) >= 2:
                node_x = start_x + float(pos[0])
                node_y = start_y + float(pos[1])
            else:
                node_x = start_x
                node_y = start_y

            try:
                logger.info(f"  Creating node at ({node_x}, {node_y})")
                visual_node = graph.create_node(identifier, pos=[node_x, node_y])
                logger.info(f"  Created node: {visual_node}")
                if visual_node:
                    created_nodes[node_id] = visual_node
                    logger.info(f"  SUCCESS: Node {node_id} created")

                    # Set node_id property
                    try:
                        visual_node.set_property("node_id", node_id)
                    except Exception:
                        pass

                    # Apply config
                    config = node_data.get("config", {})
                    for key, value in config.items():
                        try:
                            visual_node.set_property(key, value)
                        except Exception:
                            pass
                else:
                    logger.warning(f"  FAILED: create_node returned None for {node_type}")

            except Exception as e:
                logger.error(f"Failed to create node {node_type}: {e}", exc_info=True)

        # Create connections
        for conn in connections_data:
            source_id = conn.get("source_node") or conn.get("from_node")
            target_id = conn.get("target_node") or conn.get("to_node")
            source_port = conn.get("source_port") or conn.get("from_port", "exec_out")
            target_port = conn.get("target_port") or conn.get("to_port", "exec_in")

            source_node = created_nodes.get(source_id)
            target_node = created_nodes.get(target_id)

            if source_node and target_node:
                try:
                    out_port = source_node.get_output(source_port)
                    in_port = target_node.get_input(target_port)
                    if out_port and in_port:
                        out_port.connect_to(in_port)
                except Exception as e:
                    logger.debug(f"Failed to connect {source_id}->{target_id}: {e}")

        # Select new nodes and center view
        if created_nodes:
            graph.clear_selection()
            for node in created_nodes.values():
                node.set_selected(True)
            if hasattr(graph, "fit_to_selection"):
                graph.fit_to_selection()

            logger.info(f"Added {len(created_nodes)} AI-generated nodes to canvas")

        # Show summary to user via status bar
        total_requested = len(nodes_items)
        total_created = len(created_nodes)

        if skipped_nodes:
            skipped_types = [f"{nid}:{ntype}" for nid, ntype, reason in skipped_nodes]
            logger.warning(f"Skipped {len(skipped_nodes)} nodes: {skipped_types}")

            # Show warning in status bar
            if hasattr(self._mw, "show_status_message"):
                self._mw.show_status_message(
                    f"Added {total_created}/{total_requested} nodes. "
                    f"Skipped: {', '.join(skipped_types[:3])}{'...' if len(skipped_types) > 3 else ''}",
                    timeout=8000,
                )
        else:
            if hasattr(self._mw, "show_status_message"):
                self._mw.show_status_message(
                    f"Added {total_created} nodes from AI workflow", timeout=5000
                )

        # Mark workflow as modified
        self._mw.set_modified(True)

    def _build_ai_node_type_map(self, graph) -> dict:
        """Build mapping from node types to NodeGraphQt identifiers."""
        type_map = {}
        try:
            for identifier in graph.registered_nodes():
                parts = identifier.split(".")
                if parts:
                    visual_name = parts[-1]

                    # Map 1: VisualXxxNode -> XxxNode
                    if visual_name.startswith("Visual"):
                        node_type = visual_name[6:]  # Remove "Visual" prefix
                        type_map[node_type] = identifier
                        # Also map the full visual name
                        type_map[visual_name] = identifier
                    else:
                        # Map 2: Non-visual nodes directly
                        type_map[visual_name] = identifier

                    # Map 3: Also map full identifier for flexibility
                    type_map[identifier] = identifier

            # Add common aliases that AI might generate
            # These are fallbacks for when the AI doesn't use exact node names
            aliases = {
                "Start": "StartNode",
                "End": "EndNode",
                "Wait": "WaitNode",
                "Click": "ClickElementNode",
                "Type": "TypeTextNode",
                "GoTo": "GoToURLNode",
                "GoToURL": "GoToURLNode",
                "Navigate": "GoToURLNode",
                "NavigateNode": "GoToURLNode",
                "SetVariable": "SetVariableNode",
                "GetVariable": "GetVariableNode",
                "Debug": "LogNode",
                "Log": "LogNode",
                "If": "IfNode",
                "ForLoop": "ForLoopStartNode",
                "ForEach": "ForLoopStartNode",
                "LaunchBrowser": "LaunchBrowserNode",
                "CloseBrowser": "CloseBrowserNode",
                # Directory operations
                "ListDirectory": "ListDirectoryNode",
                "ListDir": "ListDirectoryNode",
                "ListFolder": "ListDirectoryNode",
                "ListFolders": "ListDirectoryNode",
                "CreateDirectory": "CreateDirectoryNode",
                "CreateDir": "CreateDirectoryNode",
                "MakeDirectory": "CreateDirectoryNode",
                "MakeDir": "CreateDirectoryNode",
                "Mkdir": "CreateDirectoryNode",
                "NewFolder": "CreateDirectoryNode",
            }
            for alias, target in aliases.items():
                if target in type_map and alias not in type_map:
                    type_map[alias] = type_map[target]

        except Exception as e:
            logger.warning(f"Could not build node type map: {e}")
        return type_map

    def _find_ai_workflow_position(self, graph) -> tuple:
        """Find a good position to place AI workflow nodes."""
        max_x = 100
        max_y = 100
        try:
            for node in graph.all_nodes():
                pos = node.pos()
                if pos[0] > max_x:
                    max_x = pos[0]
                if pos[1] > max_y:
                    max_y = pos[1]
        except Exception:
            pass
        # Place new nodes to the right of existing nodes
        return max_x + 200, max_y - 100

    def _apply_ai_edits(self, modifications: list) -> None:
        """
        Apply AI-generated edits to existing nodes on canvas.

        Args:
            modifications: List of modification dicts:
                [{"node_id": "...", "changes": {"property": "value"}}]
        """
        if not modifications:
            logger.warning("No modifications to apply")
            return

        graph = self._mw.get_graph()
        if not graph:
            logger.warning("No graph available for edits")
            return

        modified_count = 0
        failed_count = 0

        for mod in modifications:
            node_id = mod.get("node_id")
            changes = mod.get("changes", {})

            if not node_id or not changes:
                logger.warning(f"Invalid modification: {mod}")
                continue

            # Find the node on canvas
            target_node = None
            for node in graph.all_nodes():
                # Check both the visual node ID and the custom node_id property
                try:
                    custom_node_id = node.get_property("node_id")
                    if custom_node_id == node_id or node.id == node_id:
                        target_node = node
                        break
                except Exception:
                    pass

            if not target_node:
                logger.warning(f"Node not found for edit: {node_id}")
                failed_count += 1
                continue

            # Apply changes
            for prop_name, new_value in changes.items():
                try:
                    target_node.set_property(prop_name, new_value)
                    logger.info(f"Set {node_id}.{prop_name} = {new_value}")
                    modified_count += 1
                except Exception as e:
                    logger.warning(f"Failed to set {prop_name} on {node_id}: {e}")
                    failed_count += 1

        # Show status
        if hasattr(self._mw, "show_status_message"):
            if failed_count == 0:
                self._mw.show_status_message(f"Modified {modified_count} properties", timeout=5000)
            else:
                self._mw.show_status_message(
                    f"Modified {modified_count} properties, {failed_count} failed",
                    timeout=8000,
                )

        # Mark as modified
        self._mw.set_modified(True)
        logger.info(f"Applied {modified_count} edits, {failed_count} failed")

    # ==================== Validation/Navigation ====================

    @Slot()
    def on_validate_workflow(self) -> None:
        """Handle validate workflow action."""
        self._mw.validate_current_workflow()

    @Slot(str)
    def on_validation_issue_clicked(self, location: str) -> None:
        """Handle click on validation issue - navigate to node."""
        if location and location.startswith("node:"):
            self._select_node_by_id(location.split(":", 1)[1])

    @Slot(str)
    def on_navigate_to_node(self, node_id: str) -> None:
        """Navigate to and select a node."""
        self._select_node_by_id(node_id)

    def _select_node_by_id(self, node_id: str) -> None:
        """Select node by ID and center view."""
        logger.info(f"_select_node_by_id called with node_id: {node_id}")

        if not self._mw._central_widget or not hasattr(self._mw._central_widget, "graph"):
            logger.warning("No central widget or graph found")
            return

        try:
            graph = self._mw._central_widget.graph
            graph.clear_selection()
            all_nodes = graph.all_nodes()
            logger.info(f"Searching {len(all_nodes)} nodes for {node_id}")

            for node in all_nodes:
                # Check multiple ways node_id might be stored
                visual_node_id = None
                if hasattr(node, "get_property"):
                    visual_node_id = node.get_property("node_id")
                if not visual_node_id:
                    visual_node_id = getattr(node, "node_id", None)

                # node.id is a property, not a method
                graph_node_id = node.id if hasattr(node, "id") else None

                if graph_node_id == node_id or visual_node_id == node_id:
                    logger.info(f"Found node! Selecting: {graph_node_id}")
                    node.set_selected(True)
                    graph.fit_to_selection()
                    return

            logger.warning(f"No node found matching: {node_id}")
        except Exception as e:
            logger.exception(f"Could not select node {node_id}: {e}")

    @Slot(str, str, object)
    def on_property_panel_changed(self, node_id: str, prop_name: str, value) -> None:
        """Handle property panel value change."""
        self._mw.set_modified(True)

        graph = self._mw.get_graph()
        if graph:
            for visual_node in graph.all_nodes():
                if visual_node.get_property("node_id") == node_id:
                    casare_node = (
                        visual_node.get_casare_node()
                        if hasattr(visual_node, "get_casare_node")
                        else None
                    )
                    if casare_node and hasattr(casare_node, "config"):
                        casare_node.config[prop_name] = value
                        logger.debug(f"Updated casare_node.config['{prop_name}'] = {value}")
                    break

    @Slot(dict)
    def on_panel_variables_changed(self, variables: dict) -> None:
        """Handle variables changed in panel."""
        self._mw.set_modified(True)
        logger.debug(f"Variables updated: {len(variables)} variables")

    # ==================== Layout and Alignment Actions ====================

    @Slot()
    def on_auto_layout(self) -> None:
        """Automatically arrange all nodes using layered layout algorithm."""
        graph = self._mw.get_graph()
        if not graph:
            self._mw.show_status("No graph available", 2000)
            return

        try:
            from casare_rpa.presentation.canvas.graph.auto_layout_manager import (
                get_auto_layout_manager,
            )

            layout_manager = get_auto_layout_manager()
            layout_manager.set_graph(graph)
            layout_manager.layout_workflow(direction="LR")
            self._mw.set_modified(True)
            self._mw.show_status("Auto-layout applied", 2000)
            logger.debug("Auto-layout applied to workflow")
        except Exception as e:
            logger.error(f"Auto-layout failed: {e}")
            self._mw.show_status(f"Auto-layout failed: {e}", 3000)

    @Slot()
    def on_layout_selection(self) -> None:
        """Automatically arrange selected nodes."""
        graph = self._mw.get_graph()
        if not graph:
            self._mw.show_status("No graph available", 2000)
            return

        selected = graph.selected_nodes()
        if len(selected) < 2:
            self._mw.show_status("Select at least 2 nodes for layout", 2000)
            return

        try:
            from casare_rpa.presentation.canvas.graph.auto_layout_manager import (
                get_auto_layout_manager,
            )

            layout_manager = get_auto_layout_manager()
            layout_manager.set_graph(graph)
            layout_manager.layout_selection(selected, direction="LR")
            self._mw.set_modified(True)
            self._mw.show_status(f"Layout applied to {len(selected)} nodes", 2000)
            logger.debug(f"Layout applied to {len(selected)} selected nodes")
        except Exception as e:
            logger.error(f"Layout selection failed: {e}")
            self._mw.show_status(f"Layout selection failed: {e}", 3000)

    @Slot(bool)
    def on_toggle_grid_snap(self, checked: bool) -> None:
        """Toggle snap-to-grid mode."""
        try:
            from casare_rpa.presentation.canvas.graph.grid_snap_manager import (
                get_grid_snap_manager,
            )

            snap_manager = get_grid_snap_manager()
            snap_manager.set_enabled(checked)

            status = "enabled" if checked else "disabled"
            self._mw.show_status(f"Snap to grid {status}", 2000)
            logger.debug(f"Grid snap: {status}")
        except Exception as e:
            logger.error(f"Failed to toggle grid snap: {e}")
