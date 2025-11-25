"""
Tests for recorder module - Recording session and workflow generation.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock


class TestActionType:
    """Test ActionType enum."""

    def test_action_types_defined(self):
        """Test that all action types are defined."""
        from casare_rpa.recorder.recording_session import ActionType

        assert ActionType.CLICK
        assert ActionType.TYPE
        assert ActionType.SELECT
        assert ActionType.NAVIGATE
        assert ActionType.WAIT

    def test_action_type_values(self):
        """Test action type string values."""
        from casare_rpa.recorder.recording_session import ActionType

        assert ActionType.CLICK.value == "click"
        assert ActionType.TYPE.value == "type"
        assert ActionType.SELECT.value == "select"
        assert ActionType.NAVIGATE.value == "navigate"
        assert ActionType.WAIT.value == "wait"


class TestRecordedAction:
    """Test RecordedAction dataclass."""

    def test_create_click_action(self):
        """Test creating a click action."""
        from casare_rpa.recorder.recording_session import RecordedAction, ActionType

        action = RecordedAction(
            action_type=ActionType.CLICK,
            selector="#button",
        )

        assert action.action_type == ActionType.CLICK
        assert action.selector == "#button"
        assert isinstance(action.timestamp, datetime)

    def test_create_type_action(self):
        """Test creating a type action."""
        from casare_rpa.recorder.recording_session import RecordedAction, ActionType

        action = RecordedAction(
            action_type=ActionType.TYPE,
            selector="#input",
            value="Hello World"
        )

        assert action.action_type == ActionType.TYPE
        assert action.value == "Hello World"

    def test_create_navigate_action(self):
        """Test creating a navigate action."""
        from casare_rpa.recorder.recording_session import RecordedAction, ActionType

        action = RecordedAction(
            action_type=ActionType.NAVIGATE,
            selector="",
            url="https://example.com"
        )

        assert action.action_type == ActionType.NAVIGATE
        assert action.url == "https://example.com"

    def test_action_with_element_metadata(self):
        """Test action with element metadata."""
        from casare_rpa.recorder.recording_session import RecordedAction, ActionType

        action = RecordedAction(
            action_type=ActionType.CLICK,
            selector="#submit",
            element_text="Submit",
            element_id="submit",
            element_tag="button",
            element_class="btn btn-primary"
        )

        assert action.element_text == "Submit"
        assert action.element_id == "submit"
        assert action.element_tag == "button"
        assert action.element_class == "btn btn-primary"

    def test_action_to_dict(self):
        """Test converting action to dictionary."""
        from casare_rpa.recorder.recording_session import RecordedAction, ActionType

        action = RecordedAction(
            action_type=ActionType.CLICK,
            selector="#button",
            value="test"
        )

        data = action.to_dict()

        assert data["action_type"] == "click"
        assert data["selector"] == "#button"
        assert data["value"] == "test"
        assert "timestamp" in data

    def test_action_from_dict(self):
        """Test creating action from dictionary."""
        from casare_rpa.recorder.recording_session import RecordedAction, ActionType

        data = {
            "action_type": "click",
            "selector": "#button",
            "timestamp": datetime.now().isoformat(),
            "value": None,
            "element_info": {},
            "url": None
        }

        action = RecordedAction.from_dict(data)

        assert action.action_type == ActionType.CLICK
        assert action.selector == "#button"


class TestRecordingSession:
    """Test RecordingSession class."""

    @pytest.fixture
    def session(self):
        """Create a fresh recording session."""
        from casare_rpa.recorder.recording_session import RecordingSession
        return RecordingSession()

    def test_session_initial_state(self, session):
        """Test initial session state."""
        assert session.actions == []
        assert session.start_time is None
        assert session.end_time is None
        assert not session.is_recording
        assert not session.is_paused

    def test_start_recording(self, session):
        """Test starting a recording session."""
        session.start()

        assert session.is_recording
        assert not session.is_paused
        assert session.start_time is not None
        assert session.actions == []

    def test_start_already_recording(self, session):
        """Test starting when already recording does nothing."""
        session.start()
        first_start_time = session.start_time

        session.start()  # Should not change anything

        assert session.start_time == first_start_time

    def test_pause_recording(self, session):
        """Test pausing a recording session."""
        session.start()
        session.pause()

        assert session.is_recording
        assert session.is_paused

    def test_pause_without_recording(self, session):
        """Test pausing without active recording."""
        session.pause()  # Should not raise

        assert not session.is_paused

    def test_resume_recording(self, session):
        """Test resuming a paused recording."""
        session.start()
        session.pause()
        session.resume()

        assert session.is_recording
        assert not session.is_paused

    def test_resume_without_recording(self, session):
        """Test resuming without active recording."""
        session.resume()  # Should not raise

        assert not session.is_recording

    def test_stop_recording(self, session):
        """Test stopping a recording session."""
        session.start()
        session.stop()

        assert not session.is_recording
        assert not session.is_paused
        assert session.end_time is not None

    def test_stop_without_recording(self, session):
        """Test stopping without active recording."""
        session.stop()  # Should not raise

        assert session.end_time is None

    def test_add_action(self, session):
        """Test adding an action during recording."""
        from casare_rpa.recorder.recording_session import RecordedAction, ActionType

        session.start()
        action = RecordedAction(ActionType.CLICK, "#button")
        session.add_action(action)

        assert len(session.actions) == 1
        assert session.actions[0] == action

    def test_add_action_when_not_recording(self, session):
        """Test adding action when not recording is ignored."""
        from casare_rpa.recorder.recording_session import RecordedAction, ActionType

        action = RecordedAction(ActionType.CLICK, "#button")
        session.add_action(action)

        assert len(session.actions) == 0

    def test_add_action_when_paused(self, session):
        """Test adding action when paused is ignored."""
        from casare_rpa.recorder.recording_session import RecordedAction, ActionType

        session.start()
        session.pause()
        action = RecordedAction(ActionType.CLICK, "#button")
        session.add_action(action)

        assert len(session.actions) == 0

    def test_get_actions(self, session):
        """Test getting recorded actions returns a copy."""
        from casare_rpa.recorder.recording_session import RecordedAction, ActionType

        session.start()
        action = RecordedAction(ActionType.CLICK, "#button")
        session.add_action(action)

        actions = session.get_actions()
        actions.append(RecordedAction(ActionType.TYPE, "#input"))

        # Original should be unchanged
        assert len(session.actions) == 1

    def test_clear_session(self, session):
        """Test clearing a recording session."""
        from casare_rpa.recorder.recording_session import RecordedAction, ActionType

        session.start()
        session.add_action(RecordedAction(ActionType.CLICK, "#button"))
        session.clear()

        assert session.actions == []
        assert session.start_time is None
        assert session.end_time is None
        assert not session.is_recording

    def test_get_duration(self, session):
        """Test getting session duration."""
        assert session.get_duration() == 0.0

        session.start()
        duration = session.get_duration()
        assert duration >= 0.0

    def test_session_to_dict(self, session):
        """Test converting session to dictionary."""
        from casare_rpa.recorder.recording_session import RecordedAction, ActionType

        session.start()
        session.add_action(RecordedAction(ActionType.CLICK, "#button"))
        session.stop()

        data = session.to_dict()

        assert "start_time" in data
        assert "end_time" in data
        assert "duration" in data
        assert "action_count" in data
        assert "actions" in data
        assert data["action_count"] == 1


class TestWorkflowGenerator:
    """Test WorkflowGenerator class."""

    @pytest.fixture
    def generator(self):
        """Create a workflow generator."""
        from casare_rpa.recorder.workflow_generator import WorkflowGenerator
        return WorkflowGenerator()

    def test_generator_initialization(self, generator):
        """Test generator initialization."""
        assert generator.node_spacing > 0
        assert generator.start_x > 0
        assert generator.start_y > 0

    def test_generate_empty_workflow(self, generator):
        """Test generating workflow from no actions."""
        nodes = generator.generate_workflow([])
        assert nodes == []

    def test_generate_click_action(self, generator):
        """Test generating workflow from click action."""
        from casare_rpa.recorder.recording_session import RecordedAction, ActionType

        actions = [RecordedAction(ActionType.CLICK, "#button")]
        nodes = generator.generate_workflow(actions)

        assert len(nodes) == 1
        assert nodes[0]["type"] == "ClickElement"
        assert nodes[0]["config"]["selector"] == "#button"

    def test_generate_type_action(self, generator):
        """Test generating workflow from type action."""
        from casare_rpa.recorder.recording_session import RecordedAction, ActionType

        actions = [RecordedAction(ActionType.TYPE, "#input", value="Hello")]
        nodes = generator.generate_workflow(actions)

        assert len(nodes) == 1
        assert nodes[0]["type"] == "TypeText"
        assert nodes[0]["config"]["text"] == "Hello"

    def test_generate_select_action(self, generator):
        """Test generating workflow from select action."""
        from casare_rpa.recorder.recording_session import RecordedAction, ActionType

        actions = [RecordedAction(ActionType.SELECT, "#dropdown", value="option1")]
        nodes = generator.generate_workflow(actions)

        assert len(nodes) == 1
        assert nodes[0]["type"] == "SelectDropdown"
        assert nodes[0]["config"]["value"] == "option1"

    def test_generate_navigate_action(self, generator):
        """Test generating workflow from navigate action."""
        from casare_rpa.recorder.recording_session import RecordedAction, ActionType

        actions = [RecordedAction(ActionType.NAVIGATE, "", url="https://example.com")]
        nodes = generator.generate_workflow(actions)

        assert len(nodes) == 1
        assert nodes[0]["type"] == "GoToURL"
        assert nodes[0]["config"]["url"] == "https://example.com"

    def test_generate_wait_action(self, generator):
        """Test generating workflow from wait action."""
        from casare_rpa.recorder.recording_session import RecordedAction, ActionType

        actions = [RecordedAction(ActionType.WAIT, "#element")]
        nodes = generator.generate_workflow(actions)

        assert len(nodes) == 1
        assert nodes[0]["type"] == "WaitForElement"
        assert nodes[0]["config"]["selector"] == "#element"

    def test_generate_multiple_actions(self, generator):
        """Test generating workflow from multiple actions."""
        from casare_rpa.recorder.recording_session import RecordedAction, ActionType

        actions = [
            RecordedAction(ActionType.NAVIGATE, "", url="https://example.com"),
            RecordedAction(ActionType.CLICK, "#button"),
            RecordedAction(ActionType.TYPE, "#input", value="test"),
        ]
        nodes = generator.generate_workflow(actions)

        assert len(nodes) == 3
        # Should be connected sequentially
        assert nodes[0]["connections"] == [1]
        assert nodes[1]["connections"] == [2]
        assert nodes[2]["connections"] == []

    def test_generate_with_custom_position(self, generator):
        """Test generating workflow with custom start position."""
        from casare_rpa.recorder.recording_session import RecordedAction, ActionType

        actions = [RecordedAction(ActionType.CLICK, "#button")]
        nodes = generator.generate_workflow(actions, start_position={"x": 500, "y": 300})

        assert nodes[0]["position"]["x"] == 500
        assert nodes[0]["position"]["y"] == 300

    def test_node_positions_increment(self, generator):
        """Test that node positions increment vertically."""
        from casare_rpa.recorder.recording_session import RecordedAction, ActionType

        actions = [
            RecordedAction(ActionType.CLICK, "#button1"),
            RecordedAction(ActionType.CLICK, "#button2"),
        ]
        nodes = generator.generate_workflow(actions)

        assert nodes[1]["position"]["y"] > nodes[0]["position"]["y"]
        assert nodes[0]["position"]["x"] == nodes[1]["position"]["x"]

    def test_truncate_selector(self, generator):
        """Test selector truncation."""
        long_selector = "a" * 100
        truncated = generator._truncate_selector(long_selector, max_length=30)

        assert len(truncated) <= 33  # 30 + "..."
        assert truncated.endswith("...")

    def test_truncate_selector_short(self, generator):
        """Test selector truncation with short selector."""
        short_selector = "#btn"
        result = generator._truncate_selector(short_selector, max_length=30)

        assert result == short_selector

    def test_truncate_text(self, generator):
        """Test text truncation."""
        long_text = "This is a very long text that should be truncated"
        truncated = generator._truncate_text(long_text, max_length=20)

        assert len(truncated) <= 23
        assert truncated.endswith("...")

    def test_truncate_url(self, generator):
        """Test URL truncation."""
        long_url = "https://example.com/very/long/path/that/goes/on/and/on"
        truncated = generator._truncate_url(long_url, max_length=40)

        assert len(truncated) <= 43
        assert truncated.endswith("...")

    def test_get_element_label_with_text(self, generator):
        """Test element label extraction with text."""
        from casare_rpa.recorder.recording_session import RecordedAction, ActionType

        action = RecordedAction(
            ActionType.CLICK,
            "#button",
            element_text="Submit Form"
        )

        label = generator._get_element_label(action)
        assert "Submit Form" in label

    def test_get_element_label_with_id(self, generator):
        """Test element label extraction with ID."""
        from casare_rpa.recorder.recording_session import RecordedAction, ActionType

        action = RecordedAction(
            ActionType.CLICK,
            "#button",
            element_id="submit-btn"
        )

        label = generator._get_element_label(action)
        assert "submit-btn" in label

    def test_node_names_are_descriptive(self, generator):
        """Test that generated node names are descriptive."""
        from casare_rpa.recorder.recording_session import RecordedAction, ActionType

        actions = [
            RecordedAction(ActionType.CLICK, "#button", element_text="Submit"),
            RecordedAction(ActionType.TYPE, "#input", value="test@email.com"),
        ]
        nodes = generator.generate_workflow(actions)

        assert "Click" in nodes[0]["name"]
        assert "Type" in nodes[1]["name"]
