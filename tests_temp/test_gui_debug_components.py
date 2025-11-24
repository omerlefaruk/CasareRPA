"""
Comprehensive tests for GUI debug components.

Tests for:
- DebugToolbar functionality
- VariableInspectorPanel functionality
- ExecutionHistoryViewer functionality
- Integration with WorkflowRunner
"""

import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QTimer
from casare_rpa.canvas.debug_toolbar import DebugToolbar
from casare_rpa.canvas.variable_inspector import VariableInspectorPanel
from casare_rpa.canvas.execution_history_viewer import ExecutionHistoryViewer
from casare_rpa.core.workflow_schema import WorkflowSchema, NodeConnection, WorkflowMetadata
from casare_rpa.runner.workflow_runner import WorkflowRunner
from casare_rpa.nodes.basic_nodes import StartNode, EndNode
from casare_rpa.nodes.variable_nodes import SetVariableNode
import sys


# Ensure QApplication exists for GUI tests
@pytest.fixture(scope="session")
def qapp():
    """Create QApplication for GUI tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


class TestDebugToolbar:
    """Tests for DebugToolbar widget."""
    
    def test_toolbar_creation(self, qapp):
        """Test that toolbar can be created."""
        toolbar = DebugToolbar()
        assert toolbar is not None
        assert toolbar.windowTitle() == "Debug"
    
    def test_debug_mode_toggle(self, qapp):
        """Test debug mode toggle."""
        toolbar = DebugToolbar()
        
        # Initially unchecked
        assert not toolbar.action_debug_mode.isChecked()
        
        # Check it
        toolbar.action_debug_mode.setChecked(True)
        assert toolbar.action_debug_mode.isChecked()
        
        # Uncheck it
        toolbar.action_debug_mode.setChecked(False)
        assert not toolbar.action_debug_mode.isChecked()
    
    def test_debug_mode_signal(self, qapp):
        """Test that debug mode toggle emits signal."""
        toolbar = DebugToolbar()
        
        signal_received = []
        toolbar.debug_mode_toggled.connect(lambda enabled: signal_received.append(enabled))
        
        toolbar.action_debug_mode.setChecked(True)
        
        assert len(signal_received) == 1
        assert signal_received[0] is True
    
    def test_step_mode_toggle(self, qapp):
        """Test step mode toggle."""
        toolbar = DebugToolbar()
        
        # Enable debug mode first
        toolbar.action_debug_mode.setChecked(True)
        
        # Initially unchecked
        assert not toolbar.action_step_mode.isChecked()
        
        # Check it
        toolbar.action_step_mode.setChecked(True)
        assert toolbar.action_step_mode.isChecked()
    
    def test_step_mode_requires_debug_mode(self, qapp):
        """Test that step mode is disabled without debug mode."""
        toolbar = DebugToolbar()
        
        # Step mode should be disabled initially
        assert not toolbar.action_step_mode.isEnabled()
        
        # Enable debug mode
        toolbar.action_debug_mode.setChecked(True)
        
        # Step mode should now be enabled
        assert toolbar.action_step_mode.isEnabled()
    
    def test_step_signal(self, qapp):
        """Test that step button emits signal."""
        toolbar = DebugToolbar()
        
        signal_received = []
        toolbar.step_requested.connect(lambda: signal_received.append(True))
        
        # Enable debug and step mode
        toolbar.action_debug_mode.setChecked(True)
        toolbar.action_step_mode.setChecked(True)
        
        # Trigger step action
        toolbar.action_step.trigger()
        
        assert len(signal_received) == 1
    
    def test_continue_signal(self, qapp):
        """Test that continue button emits signal."""
        toolbar = DebugToolbar()
        
        signal_received = []
        toolbar.continue_requested.connect(lambda: signal_received.append(True))
        
        # Enable debug mode
        toolbar.action_debug_mode.setChecked(True)
        
        # Trigger continue action
        toolbar.action_continue.trigger()
        
        assert len(signal_received) == 1
    
    def test_clear_breakpoints_signal(self, qapp):
        """Test that clear breakpoints button emits signal."""
        toolbar = DebugToolbar()
        
        signal_received = []
        toolbar.clear_breakpoints_requested.connect(lambda: signal_received.append(True))
        
        # Enable debug mode
        toolbar.action_debug_mode.setChecked(True)
        
        # Trigger clear breakpoints action
        toolbar.action_clear_breakpoints.trigger()
        
        assert len(signal_received) == 1
    
    def test_execution_state_updates(self, qapp):
        """Test toolbar updates based on execution state."""
        toolbar = DebugToolbar()
        toolbar.action_debug_mode.setChecked(True)
        
        # Simulate execution starting
        toolbar.set_execution_state(True)
        
        # Debug/step mode changes should be disabled during execution
        assert not toolbar.action_debug_mode.isEnabled()
        assert not toolbar.action_step_mode.isEnabled()
        
        # Stop should be enabled
        assert toolbar.action_stop.isEnabled()
        
        # Simulate execution stopping
        toolbar.set_execution_state(False)
        
        # Debug/step mode changes should be enabled again
        assert toolbar.action_debug_mode.isEnabled()
        
        # Stop should be disabled
        assert not toolbar.action_stop.isEnabled()


class TestVariableInspectorPanel:
    """Tests for VariableInspectorPanel widget."""
    
    def test_panel_creation(self, qapp):
        """Test that panel can be created."""
        panel = VariableInspectorPanel()
        assert panel is not None
        assert panel.windowTitle() == "Variable Inspector"
    
    def test_update_variables_empty(self, qapp):
        """Test updating with empty variables."""
        panel = VariableInspectorPanel()
        
        panel.update_variables({})
        
        assert panel.table.rowCount() == 0
        assert "Variables: 0" in panel.label_count.text()
    
    def test_update_variables_single(self, qapp):
        """Test updating with single variable."""
        panel = VariableInspectorPanel()
        
        panel.update_variables({"var1": "value1"})
        
        assert panel.table.rowCount() == 1
        assert panel.table.item(0, 0).text() == "var1"
        assert panel.table.item(0, 1).text() == '"value1"'
        assert "Variables: 1" in panel.label_count.text()
    
    def test_update_variables_multiple(self, qapp):
        """Test updating with multiple variables."""
        panel = VariableInspectorPanel()
        
        variables = {
            "var1": "value1",
            "var2": 123,
            "var3": True,
            "var4": None
        }
        
        panel.update_variables(variables)
        
        assert panel.table.rowCount() == 4
        assert "Variables: 4" in panel.label_count.text()
    
    def test_update_variables_formats_values(self, qapp):
        """Test that values are formatted correctly."""
        panel = VariableInspectorPanel()
        
        variables = {
            "string": "test",
            "number": 42,
            "boolean": True,
            "none": None,
            "list": [1, 2, 3],
            "dict": {"key": "value"}
        }
        
        panel.update_variables(variables)
        
        # Check some formatting
        for row in range(panel.table.rowCount()):
            name = panel.table.item(row, 0).text()
            value = panel.table.item(row, 1).text()
            
            if name == "string":
                assert value == '"test"'
            elif name == "number":
                assert value == "42"
            elif name == "boolean":
                assert value == "True"
            elif name == "none":
                assert value == "None"
            elif name == "list":
                assert "[1, 2, 3]" in value
            elif name == "dict":
                assert "key" in value
    
    def test_update_variables_long_string(self, qapp):
        """Test that long strings are truncated."""
        panel = VariableInspectorPanel()
        
        long_value = "a" * 200
        panel.update_variables({"var": long_value})
        
        value_text = panel.table.item(0, 1).text()
        assert len(value_text) < len(long_value) + 2  # +2 for quotes
        assert "..." in value_text
    
    def test_clear_variables(self, qapp):
        """Test clearing variables."""
        panel = VariableInspectorPanel()
        
        panel.update_variables({"var1": "value1", "var2": "value2"})
        assert panel.table.rowCount() == 2
        
        panel.clear()
        
        assert panel.table.rowCount() == 0
        assert "Variables: 0" in panel.label_count.text()
    
    def test_refresh_signal(self, qapp):
        """Test that refresh button emits signal."""
        panel = VariableInspectorPanel()
        
        signal_received = []
        panel.refresh_requested.connect(lambda: signal_received.append(True))
        
        panel.btn_refresh.click()
        
        assert len(signal_received) == 1
    
    def test_auto_refresh_toggle(self, qapp):
        """Test auto-refresh toggle."""
        panel = VariableInspectorPanel()
        
        assert not panel.btn_auto_refresh.isChecked()
        assert not panel._auto_refresh_timer.isActive()
        
        # Enable auto-refresh
        panel.btn_auto_refresh.setChecked(True)
        
        assert panel._auto_refresh_timer.isActive()
        assert "Disable" in panel.btn_auto_refresh.text()
        
        # Disable auto-refresh
        panel.btn_auto_refresh.setChecked(False)
        
        assert not panel._auto_refresh_timer.isActive()
        assert "Enable" in panel.btn_auto_refresh.text()


class TestExecutionHistoryViewer:
    """Tests for ExecutionHistoryViewer widget."""
    
    def test_viewer_creation(self, qapp):
        """Test that viewer can be created."""
        viewer = ExecutionHistoryViewer()
        assert viewer is not None
        assert viewer.windowTitle() == "Execution History"
    
    def test_update_history_empty(self, qapp):
        """Test updating with empty history."""
        viewer = ExecutionHistoryViewer()
        
        viewer.update_history([])
        
        assert viewer.table.rowCount() == 0
        assert "Entries: 0" in viewer.label_count.text()
    
    def test_update_history_single(self, qapp):
        """Test updating with single entry."""
        viewer = ExecutionHistoryViewer()
        
        history = [{
            "timestamp": "2024-01-01T12:00:00.000000",
            "node_id": "node1",
            "node_type": "StartNode",
            "execution_time": 0.001,
            "status": "success"
        }]
        
        viewer.update_history(history)
        
        assert viewer.table.rowCount() == 1
        assert viewer.table.item(0, 2).text() == "node1"
        assert viewer.table.item(0, 3).text() == "StartNode"
        assert "Entries: 1" in viewer.label_count.text()
    
    def test_update_history_multiple(self, qapp):
        """Test updating with multiple entries."""
        viewer = ExecutionHistoryViewer()
        
        history = [
            {
                "timestamp": f"2024-01-01T12:00:0{i}.000000",
                "node_id": f"node{i}",
                "node_type": "TestNode",
                "execution_time": 0.001 * i,
                "status": "success"
            }
            for i in range(10)
        ]
        
        viewer.update_history(history)
        
        assert viewer.table.rowCount() == 10
        assert "Entries: 10" in viewer.label_count.text()
    
    def test_append_entry(self, qapp):
        """Test appending single entry."""
        viewer = ExecutionHistoryViewer()
        
        entry = {
            "timestamp": "2024-01-01T12:00:00.000000",
            "node_id": "node1",
            "node_type": "StartNode",
            "execution_time": 0.001,
            "status": "success"
        }
        
        viewer.append_entry(entry)
        
        assert viewer.table.rowCount() == 1
    
    def test_status_color_coding(self, qapp):
        """Test that success/failure are color coded."""
        viewer = ExecutionHistoryViewer()
        
        history = [
            {
                "timestamp": "2024-01-01T12:00:00.000000",
                "node_id": "success_node",
                "node_type": "TestNode",
                "execution_time": 0.001,
                "status": "success"
            },
            {
                "timestamp": "2024-01-01T12:00:01.000000",
                "node_id": "failed_node",
                "node_type": "TestNode",
                "execution_time": 0.001,
                "status": "failed"
            }
        ]
        
        viewer.update_history(history)
        
        # Check color coding (status is in column 5)
        success_item = viewer.table.item(0, 5)
        failed_item = viewer.table.item(1, 5)
        
        # Success should have greenish background
        assert success_item.background().color().green() > 200
        
        # Failed should have reddish background
        assert failed_item.background().color().red() > 200
    
    def test_filter_by_status(self, qapp):
        """Test filtering by status."""
        viewer = ExecutionHistoryViewer()
        
        history = [
            {"timestamp": "2024-01-01T12:00:00.000000", "node_id": "node1",
             "node_type": "TestNode", "execution_time": 0.001, "status": "success"},
            {"timestamp": "2024-01-01T12:00:01.000000", "node_id": "node2",
             "node_type": "TestNode", "execution_time": 0.001, "status": "failed"},
            {"timestamp": "2024-01-01T12:00:02.000000", "node_id": "node3",
             "node_type": "TestNode", "execution_time": 0.001, "status": "success"},
        ]
        
        viewer.update_history(history)
        
        # Initially show all
        assert viewer.table.rowCount() == 3
        
        # Filter to success only
        viewer.combo_filter.setCurrentText("Success")
        assert viewer.table.rowCount() == 2
        
        # Filter to failed only
        viewer.combo_filter.setCurrentText("Failed")
        assert viewer.table.rowCount() == 1
        
        # Back to all
        viewer.combo_filter.setCurrentText("All")
        assert viewer.table.rowCount() == 3
    
    def test_statistics_calculation(self, qapp):
        """Test that statistics are calculated correctly."""
        viewer = ExecutionHistoryViewer()
        
        history = [
            {"timestamp": "2024-01-01T12:00:00.000000", "node_id": "node1",
             "node_type": "TestNode", "execution_time": 0.1, "status": "success"},
            {"timestamp": "2024-01-01T12:00:01.000000", "node_id": "node2",
             "node_type": "TestNode", "execution_time": 0.2, "status": "success"},
            {"timestamp": "2024-01-01T12:00:02.000000", "node_id": "node3",
             "node_type": "TestNode", "execution_time": 0.3, "status": "failed"},
        ]
        
        viewer.update_history(history)
        
        # Check statistics
        total_text = viewer.label_total_time.text()
        avg_text = viewer.label_avg_time.text()
        success_text = viewer.label_success_rate.text()
        
        assert "0.6" in total_text  # Total time
        assert "0.2" in avg_text  # Average time
        assert "67" in success_text  # Success rate (2/3 = 67%)
    
    def test_clear_history(self, qapp):
        """Test clearing history."""
        viewer = ExecutionHistoryViewer()
        
        history = [
            {"timestamp": "2024-01-01T12:00:00.000000", "node_id": "node1",
             "node_type": "TestNode", "execution_time": 0.001, "status": "success"}
        ]
        
        viewer.update_history(history)
        assert viewer.table.rowCount() == 1
        
        viewer.clear()
        
        assert viewer.table.rowCount() == 0
        assert "Entries: 0" in viewer.label_count.text()
    
    def test_node_selection_signal(self, qapp):
        """Test that selecting a node emits signal."""
        viewer = ExecutionHistoryViewer()
        
        history = [
            {"timestamp": "2024-01-01T12:00:00.000000", "node_id": "test_node",
             "node_type": "TestNode", "execution_time": 0.001, "status": "success"}
        ]
        
        viewer.update_history(history)
        
        signal_received = []
        viewer.node_selected.connect(lambda node_id: signal_received.append(node_id))
        
        # Select the row
        viewer.table.selectRow(0)
        
        assert len(signal_received) == 1
        assert signal_received[0] == "test_node"


@pytest.mark.asyncio
class TestDebugIntegration:
    """Integration tests for debug components with WorkflowRunner."""
    
    def create_test_workflow(self):
        """Helper to create a test workflow."""
        start = StartNode("start")
        set1 = SetVariableNode("set1", variable_name="var1", default_value="value1")
        set2 = SetVariableNode("set2", variable_name="var2", default_value="value2")
        end = EndNode("end")
        
        workflow = WorkflowSchema(WorkflowMetadata(name="test"))
        workflow.nodes = {"start": start, "set1": set1, "set2": set2, "end": end}
        workflow.connections = [
            NodeConnection("start", "exec_out", "set1", "exec_in"),
            NodeConnection("set1", "exec_out", "set2", "exec_in"),
            NodeConnection("set2", "exec_out", "end", "exec_in")
        ]
        
        return workflow
    
    async def test_variable_inspector_integration(self, qapp):
        """Test variable inspector with actual workflow."""
        workflow = self.create_test_workflow()
        runner = WorkflowRunner(workflow)
        runner.enable_debug_mode(True)
        
        panel = VariableInspectorPanel()
        
        # Run workflow
        await runner.run()
        
        # Update panel with variables
        variables = runner.get_variables()
        panel.update_variables(variables)
        
        # Should have 2 variables
        assert panel.table.rowCount() == 2
        
        # Check variable names
        var_names = [panel.table.item(i, 0).text() for i in range(panel.table.rowCount())]
        assert "var1" in var_names
        assert "var2" in var_names
    
    async def test_execution_history_integration(self, qapp):
        """Test execution history with actual workflow."""
        workflow = self.create_test_workflow()
        runner = WorkflowRunner(workflow)
        runner.enable_debug_mode(True)
        
        viewer = ExecutionHistoryViewer()
        
        # Run workflow
        await runner.run()
        
        # Update viewer with history
        history = runner.get_execution_history()
        viewer.update_history(history)
        
        # Should have 4 entries (start, set1, set2, end)
        assert viewer.table.rowCount() == 4
        
        # Check node IDs
        node_ids = [viewer.table.item(i, 2).text() for i in range(viewer.table.rowCount())]
        assert "start" in node_ids
        assert "set1" in node_ids
        assert "set2" in node_ids
        assert "end" in node_ids


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
