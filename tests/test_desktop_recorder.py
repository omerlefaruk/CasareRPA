"""
Unit tests for Desktop Recorder

Tests DesktopRecorder, DesktopRecordedAction, WorkflowGenerator
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from casare_rpa.desktop.desktop_recorder import (
    DesktopRecorder,
    DesktopRecordedAction,
    DesktopActionType,
    WorkflowGenerator
)


class TestDesktopRecordedAction:
    """Test suite for DesktopRecordedAction"""

    def test_action_creation(self):
        """Test creating a recorded action"""
        action = DesktopRecordedAction(
            action_type=DesktopActionType.MOUSE_CLICK,
            x=100,
            y=200
        )
        assert action.action_type == DesktopActionType.MOUSE_CLICK
        assert action.x == 100
        assert action.y == 200

    def test_action_to_dict(self):
        """Test converting action to dictionary"""
        action = DesktopRecordedAction(
            action_type=DesktopActionType.KEYBOARD_TYPE,
            text="Hello World"
        )
        data = action.to_dict()
        assert data['action_type'] == 'keyboard_type'
        assert data['text'] == 'Hello World'
        assert 'timestamp' in data

    def test_action_description_click(self):
        """Test action description for click"""
        action = DesktopRecordedAction(
            action_type=DesktopActionType.MOUSE_CLICK,
            x=100,
            y=200,
            element_name="OK Button"
        )
        assert "OK Button" in action.get_description()

    def test_action_description_type(self):
        """Test action description for typing"""
        action = DesktopRecordedAction(
            action_type=DesktopActionType.KEYBOARD_TYPE,
            text="Test text"
        )
        assert "Test text" in action.get_description()

    def test_action_description_hotkey(self):
        """Test action description for hotkey"""
        action = DesktopRecordedAction(
            action_type=DesktopActionType.KEYBOARD_HOTKEY,
            keys=["Ctrl", "C"]
        )
        assert "Ctrl+C" in action.get_description()

    def test_action_description_double_click(self):
        """Test action description for double-click"""
        action = DesktopRecordedAction(
            action_type=DesktopActionType.MOUSE_DOUBLE_CLICK,
            x=50,
            y=50
        )
        assert "Double-click" in action.get_description()

    def test_action_description_right_click(self):
        """Test action description for right-click"""
        action = DesktopRecordedAction(
            action_type=DesktopActionType.MOUSE_RIGHT_CLICK,
            x=50,
            y=50
        )
        assert "Right-click" in action.get_description()

    def test_action_description_drag(self):
        """Test action description for drag"""
        action = DesktopRecordedAction(
            action_type=DesktopActionType.MOUSE_DRAG,
            x=0,
            y=0,
            end_x=100,
            end_y=100
        )
        assert "Drag" in action.get_description()

    def test_action_description_window_activate(self):
        """Test action description for window activation"""
        action = DesktopRecordedAction(
            action_type=DesktopActionType.WINDOW_ACTIVATE,
            window_title="Notepad"
        )
        assert "Notepad" in action.get_description()


class TestDesktopRecorder:
    """Test suite for DesktopRecorder"""

    def test_recorder_initialization(self):
        """Test recorder initializes correctly"""
        recorder = DesktopRecorder()
        assert recorder.is_recording is False
        assert recorder.is_paused is False
        assert len(recorder.actions) == 0

    def test_recorder_callbacks(self):
        """Test setting callbacks"""
        recorder = DesktopRecorder()

        callback_mock = Mock()
        recorder.set_callbacks(
            on_action_recorded=callback_mock,
            on_recording_started=callback_mock,
            on_recording_stopped=callback_mock,
            on_recording_paused=callback_mock
        )

        assert recorder._on_action_recorded == callback_mock
        assert recorder._on_recording_started == callback_mock
        assert recorder._on_recording_stopped == callback_mock
        assert recorder._on_recording_paused == callback_mock

    def test_recorder_clear(self):
        """Test clearing recorder"""
        recorder = DesktopRecorder()
        recorder.actions.append(DesktopRecordedAction(
            action_type=DesktopActionType.MOUSE_CLICK
        ))
        recorder.clear()
        assert len(recorder.actions) == 0

    def test_recorder_get_actions(self):
        """Test getting actions returns a copy"""
        recorder = DesktopRecorder()
        action = DesktopRecordedAction(action_type=DesktopActionType.MOUSE_CLICK)
        recorder.actions.append(action)

        actions = recorder.get_actions()
        assert len(actions) == 1
        assert actions is not recorder.actions  # Should be a copy

    @patch('casare_rpa.desktop.desktop_recorder.HAS_PYNPUT', False)
    def test_recorder_start_without_pynput(self):
        """Test starting recorder without pynput raises error"""
        recorder = DesktopRecorder()
        with pytest.raises(RuntimeError, match="pynput not installed"):
            recorder.start()

    def test_recorder_pause_without_recording(self):
        """Test pausing when not recording does nothing"""
        recorder = DesktopRecorder()
        recorder.pause()  # Should not raise
        assert recorder.is_paused is False

    def test_recorder_resume_without_recording(self):
        """Test resuming when not recording does nothing"""
        recorder = DesktopRecorder()
        recorder.resume()  # Should not raise

    def test_recorder_stop_without_recording(self):
        """Test stopping when not recording returns empty list"""
        recorder = DesktopRecorder()
        result = recorder.stop()
        assert result == []


class TestWorkflowGenerator:
    """Test suite for WorkflowGenerator"""

    def test_generate_empty_workflow(self):
        """Test generating workflow from empty actions"""
        workflow = WorkflowGenerator.generate_workflow_data([])

        assert 'nodes' in workflow
        assert 'connections' in workflow
        # Should have start and end nodes
        assert len(workflow['nodes']) >= 2

    def test_generate_workflow_with_click(self):
        """Test generating workflow with click action"""
        actions = [
            DesktopRecordedAction(
                action_type=DesktopActionType.MOUSE_CLICK,
                x=100,
                y=200
            )
        ]

        workflow = WorkflowGenerator.generate_workflow_data(actions)

        # Find the click node
        click_node = None
        for node in workflow['nodes']:
            if 'Click' in node['name']:
                click_node = node
                break

        assert click_node is not None

    def test_generate_workflow_with_type(self):
        """Test generating workflow with type action"""
        actions = [
            DesktopRecordedAction(
                action_type=DesktopActionType.KEYBOARD_TYPE,
                text="Hello World"
            )
        ]

        workflow = WorkflowGenerator.generate_workflow_data(actions)

        # Find the type node
        type_node = None
        for node in workflow['nodes']:
            if 'Type' in node['name']:
                type_node = node
                break

        assert type_node is not None

    def test_generate_workflow_with_hotkey(self):
        """Test generating workflow with hotkey action"""
        actions = [
            DesktopRecordedAction(
                action_type=DesktopActionType.KEYBOARD_HOTKEY,
                keys=["Ctrl", "S"]
            )
        ]

        workflow = WorkflowGenerator.generate_workflow_data(actions)

        # Find the hotkey node
        hotkey_node = None
        for node in workflow['nodes']:
            if 'Hotkey' in node['name']:
                hotkey_node = node
                break

        assert hotkey_node is not None

    def test_generate_workflow_connections(self):
        """Test that workflow has proper connections"""
        actions = [
            DesktopRecordedAction(
                action_type=DesktopActionType.MOUSE_CLICK,
                x=100,
                y=200
            ),
            DesktopRecordedAction(
                action_type=DesktopActionType.KEYBOARD_TYPE,
                text="Test"
            )
        ]

        workflow = WorkflowGenerator.generate_workflow_data(actions)

        # Should have connections for: start->click, click->type, type->end
        assert len(workflow['connections']) == 3

    def test_generate_workflow_with_element_selector(self):
        """Test generating workflow with element selector"""
        actions = [
            DesktopRecordedAction(
                action_type=DesktopActionType.MOUSE_CLICK,
                x=100,
                y=200,
                element_name="OK Button",
                selector={'automation_id': 'okBtn', 'name': 'OK Button'}
            )
        ]

        workflow = WorkflowGenerator.generate_workflow_data(actions)

        # Should use element-based click node
        click_node = None
        for node in workflow['nodes']:
            if node['type'] == 'DesktopClickElementNode':
                click_node = node
                break

        assert click_node is not None

    def test_generate_workflow_metadata(self):
        """Test workflow has proper metadata"""
        actions = [
            DesktopRecordedAction(
                action_type=DesktopActionType.MOUSE_CLICK,
                x=100,
                y=200
            )
        ]

        workflow = WorkflowGenerator.generate_workflow_data(actions)

        assert 'name' in workflow
        assert 'description' in workflow
        assert 'Recorded' in workflow['name']

    def test_generate_workflow_node_positions(self):
        """Test that nodes have proper positions"""
        actions = [
            DesktopRecordedAction(action_type=DesktopActionType.MOUSE_CLICK, x=100, y=200),
            DesktopRecordedAction(action_type=DesktopActionType.MOUSE_CLICK, x=150, y=250),
        ]

        workflow = WorkflowGenerator.generate_workflow_data(actions)

        # Check that nodes have position arrays
        for node in workflow['nodes']:
            assert 'position' in node
            assert isinstance(node['position'], list)
            assert len(node['position']) == 2


class TestDesktopActionType:
    """Test suite for DesktopActionType enum"""

    def test_action_types_exist(self):
        """Test all action types exist"""
        assert DesktopActionType.MOUSE_CLICK.value == "mouse_click"
        assert DesktopActionType.MOUSE_DOUBLE_CLICK.value == "mouse_double_click"
        assert DesktopActionType.MOUSE_RIGHT_CLICK.value == "mouse_right_click"
        assert DesktopActionType.KEYBOARD_TYPE.value == "keyboard_type"
        assert DesktopActionType.KEYBOARD_HOTKEY.value == "keyboard_hotkey"
        assert DesktopActionType.MOUSE_DRAG.value == "mouse_drag"
        assert DesktopActionType.WINDOW_ACTIVATE.value == "window_activate"
