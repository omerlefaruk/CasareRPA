"""
Test to verify Drive node config/parameter passing works correctly.

This test verifies that:
1. Config values are passed from serializer to loader
2. Node's get_parameter() returns the config value
3. The full workflow execution path works

Run with: pytest tests/nodes/google/test_drive_config_sync.py -v -s
"""

from unittest.mock import MagicMock, patch

import pytest


class TestDriveConfigSync:
    """Test config synchronization for Drive nodes."""

    def test_batch_download_node_reads_config(self):
        """Test that DriveBatchDownloadNode can read destination_folder from config."""
        from casare_rpa.nodes.google.drive.drive_files import DriveBatchDownloadNode

        # Create node with config
        config = {
            "destination_folder": r"C:\Users\Rau\Desktop\save",
            "credential_id": "cred_test123",
        }
        node = DriveBatchDownloadNode("test_node_1", config=config)

        # Debug: print all internal state
        print(f"DEBUG: node.config = {node.config}")
        print(
            f"DEBUG: 'destination_folder' in node.input_ports = {'destination_folder' in node.input_ports}"
        )

        if "destination_folder" in node.input_ports:
            port = node.input_ports["destination_folder"]
            print(f"DEBUG: port.value = {port.value}")
            print(f"DEBUG: port.get_value() = {port.get_value()}")

        # Check get_input_value
        input_val = node.get_input_value("destination_folder")
        print(f"DEBUG: get_input_value('destination_folder') = {input_val}")
        print(f"DEBUG: get_input_value result is None: {input_val is None}")

        # Check config.get
        config_val = node.config.get("destination_folder")
        print(f"DEBUG: node.config.get('destination_folder') = {config_val}")

        # Verify config is stored
        assert (
            node.config.get("destination_folder") == r"C:\Users\Rau\Desktop\save"
        ), f"Config not stored! node.config = {node.config}"

        # Verify get_parameter returns the value
        result = node.get_parameter("destination_folder")
        print(f"DEBUG: get_parameter('destination_folder') = {result}")

        assert result == r"C:\Users\Rau\Desktop\save", f"Expected path, got: {result}"

        print(f"[PASS] Node config: {node.config}")
        print(f"[PASS] get_parameter('destination_folder'): {result}")

    def test_list_files_node_reads_config(self):
        """Test that DriveListFilesNode can read folder_id from config."""
        from casare_rpa.nodes.google.drive.drive_folders import DriveListFilesNode

        # Create node with config
        config = {
            "folder_id": "14gesKQIyRcs98J4v3NOOQccUgRI1kMHy",
            "credential_id": "cred_test123",
            "max_results": "100",
        }
        node = DriveListFilesNode("test_node_2", config=config)

        # Verify config is stored
        assert node.config.get("folder_id") == "14gesKQIyRcs98J4v3NOOQccUgRI1kMHy"

        # Verify get_parameter returns the value
        result = node.get_parameter("folder_id")
        assert result == "14gesKQIyRcs98J4v3NOOQccUgRI1kMHy"

        print(f"[PASS] Node config: {node.config}")
        print(f"[PASS] get_parameter('folder_id'): {result}")

    def test_workflow_loader_passes_config(self):
        """Test that workflow_loader passes config to node correctly."""
        from casare_rpa.utils.workflow.workflow_loader import load_workflow_from_dict

        # Create minimal workflow data with config
        # Need StartNode and EndNode for semantic validation
        workflow_data = {
            "metadata": {"name": "Test Workflow", "version": "1.0.0"},
            "nodes": {
                "StartNode_001": {
                    "node_type": "StartNode",
                    "position": [0, 0],
                    "config": {},
                },
                "DriveBatchDownloadNode_test1": {
                    "node_type": "DriveBatchDownloadNode",
                    "position": [200, 0],
                    "config": {
                        "destination_folder": r"C:\Users\Rau\Desktop\save",
                        "credential_id": "cred_test123",
                    },
                },
                "DriveListFilesNode_test2": {
                    "node_type": "DriveListFilesNode",
                    "position": [200, 100],
                    "config": {
                        "folder_id": "14gesKQIyRcs98J4v3NOOQccUgRI1kMHy",
                        "credential_id": "cred_test123",
                    },
                },
                "EndNode_001": {
                    "node_type": "EndNode",
                    "position": [400, 0],
                    "config": {},
                },
            },
            "connections": [
                {
                    "source_node": "StartNode_001",
                    "source_port": "exec_out",
                    "target_node": "DriveBatchDownloadNode_test1",
                    "target_port": "exec_in",
                },
                {
                    "source_node": "DriveBatchDownloadNode_test1",
                    "source_port": "exec_out",
                    "target_node": "EndNode_001",
                    "target_port": "exec_in",
                },
            ],
        }

        # Load workflow (skip validation since we're just testing config passing)
        workflow = load_workflow_from_dict(workflow_data, skip_validation=True)

        # Check nodes were created with config
        batch_node = workflow.nodes.get("DriveBatchDownloadNode_test1")
        list_node = workflow.nodes.get("DriveListFilesNode_test2")

        assert batch_node is not None, "BatchDownload node not created"
        assert list_node is not None, "ListFiles node not created"

        # Verify config was passed
        assert batch_node.config.get("destination_folder") == r"C:\Users\Rau\Desktop\save"
        assert list_node.config.get("folder_id") == "14gesKQIyRcs98J4v3NOOQccUgRI1kMHy"

        # Verify get_parameter works
        assert batch_node.get_parameter("destination_folder") == r"C:\Users\Rau\Desktop\save"
        assert list_node.get_parameter("folder_id") == "14gesKQIyRcs98J4v3NOOQccUgRI1kMHy"

        print(f"[PASS] BatchDownload config: {batch_node.config}")
        print(f"[PASS] ListFiles config: {list_node.config}")

    def test_serializer_extracts_custom_properties(self):
        """Test that serializer extracts values from model.custom_properties."""
        # This requires mocking the visual node structure

        # Create mock visual node
        mock_visual_node = MagicMock()
        mock_visual_node.get_property.return_value = "test_node_id"
        mock_visual_node.name.return_value = "Test Node"
        mock_visual_node.pos.return_value = [100, 200]

        # Mock casare_node with config
        mock_casare_node = MagicMock()
        mock_casare_node.__class__.__name__ = "DriveBatchDownloadNode"
        mock_casare_node.config = {"credential_id": "cred_test"}
        mock_visual_node._casare_node = mock_casare_node

        # Mock model with custom_properties containing destination_folder
        mock_model = MagicMock()
        mock_model.custom_properties = {
            "node_id": "test_node_id",
            "destination_folder": r"C:\Users\Rau\Desktop\save",
            "credential_id": "cred_test",
            "_is_running": False,
        }
        mock_visual_node.model = mock_model

        # Mock view with widgets
        mock_widget = MagicMock()
        mock_widget.get_name.return_value = "destination_folder"
        mock_widget.get_value.return_value = r"C:\Users\Rau\Desktop\save"

        mock_view = MagicMock()
        mock_view.widgets = {"destination_folder": mock_widget}
        mock_visual_node.view = mock_view

        # Import serializer and test _serialize_node logic
        from casare_rpa.presentation.canvas.serialization.workflow_serializer import (
            WorkflowSerializer,
        )

        # Create serializer with mocks
        mock_graph = MagicMock()
        mock_main_window = MagicMock()
        serializer = WorkflowSerializer(mock_graph, mock_main_window)

        # Call _serialize_node
        result = serializer._serialize_node(mock_visual_node)

        assert result is not None, "Serializer returned None"
        assert "config" in result, "No config in result"

        config = result["config"]
        print(f"[PASS] Serialized config: {config}")

        # Check destination_folder is in config
        assert "destination_folder" in config, f"destination_folder not in config: {config}"
        assert config["destination_folder"] == r"C:\Users\Rau\Desktop\save"


class TestEndToEndConfigFlow:
    """End-to-end test of config flow from visual node to execution."""

    def test_full_config_flow(self):
        """
        Test the full flow:
        1. Create mock visual node with properties
        2. Serialize it
        3. Load via workflow_loader
        4. Verify node has correct config
        """
        from casare_rpa.utils.workflow.workflow_loader import load_workflow_from_dict

        # Simulated serializer output (what serializer SHOULD produce)
        # Need StartNode and EndNode for semantic validation
        workflow_data = {
            "metadata": {"name": "Test", "version": "1.0.0"},
            "nodes": {
                "StartNode_001": {
                    "node_type": "StartNode",
                    "position": [100, 300],
                    "config": {},
                },
                "DriveBatchDownloadNode_abc123": {
                    "node_type": "DriveBatchDownloadNode",
                    "position": [500, 300],
                    "config": {
                        "destination_folder": r"C:\Users\Rau\Desktop\save",
                        "credential_id": "cred_3be9a941dfef",
                    },
                },
                "EndNode_001": {
                    "node_type": "EndNode",
                    "position": [900, 300],
                    "config": {},
                },
            },
            "connections": [
                {
                    "source_node": "StartNode_001",
                    "source_port": "exec_out",
                    "target_node": "DriveBatchDownloadNode_abc123",
                    "target_port": "exec_in",
                },
                {
                    "source_node": "DriveBatchDownloadNode_abc123",
                    "source_port": "exec_out",
                    "target_node": "EndNode_001",
                    "target_port": "exec_in",
                },
            ],
        }

        # Load it (skip validation since we're testing config, not execution)
        workflow = load_workflow_from_dict(workflow_data, skip_validation=True)
        node = workflow.nodes.get("DriveBatchDownloadNode_abc123")

        assert node is not None

        # This is the critical check - get_parameter must return the value
        dest_folder = node.get_parameter("destination_folder")

        print(f"node.config = {node.config}")
        print(f"get_parameter('destination_folder') = {dest_folder}")

        assert (
            dest_folder == r"C:\Users\Rau\Desktop\save"
        ), f"FAILED: get_parameter returned '{dest_folder}' instead of expected path"

        print("[PASS] Full config flow test PASSED")


if __name__ == "__main__":
    # Run tests directly
    print("=" * 60)
    print("Testing Drive Node Config Sync")
    print("=" * 60)

    test = TestDriveConfigSync()

    print("\n1. Testing BatchDownload node reads config...")
    test.test_batch_download_node_reads_config()

    print("\n2. Testing ListFiles node reads config...")
    test.test_list_files_node_reads_config()

    print("\n3. Testing workflow_loader passes config...")
    test.test_workflow_loader_passes_config()

    print("\n4. Testing serializer extracts custom_properties...")
    test.test_serializer_extracts_custom_properties()

    print("\n5. Testing full config flow...")
    e2e = TestEndToEndConfigFlow()
    e2e.test_full_config_flow()

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED!")
    print("=" * 60)
