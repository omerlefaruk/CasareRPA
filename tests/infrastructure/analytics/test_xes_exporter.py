"""
Tests for XES Exporter module.

Tests XES export functionality including:
- XML structure compliance
- Attribute handling
- File export
- Import functionality
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List
import tempfile
import xml.etree.ElementTree as ET

import pytest

from casare_rpa.infrastructure.analytics.process_mining import (
    Activity,
    ActivityStatus,
    ExecutionTrace,
)
from casare_rpa.infrastructure.analytics.xes_exporter import (
    XESExporter,
    XESImporter,
    XES_NAMESPACE,
    XES_VERSION,
)


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def sample_activities() -> List[Activity]:
    """Create sample activities for testing."""
    base_time = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
    return [
        Activity(
            node_id="node_1",
            node_type="StartNode",
            timestamp=base_time,
            duration_ms=100,
            status=ActivityStatus.COMPLETED,
            inputs={"trigger": "manual"},
            outputs={"started": True},
        ),
        Activity(
            node_id="node_2",
            node_type="BrowserNode",
            timestamp=base_time + timedelta(seconds=1),
            duration_ms=2500,
            status=ActivityStatus.COMPLETED,
            inputs={"url": "https://example.com"},
            outputs={"page_title": "Example"},
        ),
        Activity(
            node_id="node_3",
            node_type="DataNode",
            timestamp=base_time + timedelta(seconds=5),
            duration_ms=500,
            status=ActivityStatus.COMPLETED,
            inputs={"data_source": "api"},
            outputs={"records": 100},
        ),
        Activity(
            node_id="node_4",
            node_type="EndNode",
            timestamp=base_time + timedelta(seconds=6),
            duration_ms=50,
            status=ActivityStatus.COMPLETED,
        ),
    ]


@pytest.fixture
def sample_trace(sample_activities: List[Activity]) -> ExecutionTrace:
    """Create sample execution trace."""
    return ExecutionTrace(
        case_id="trace-001",
        workflow_id="wf-123",
        workflow_name="Test Workflow",
        activities=sample_activities,
        start_time=sample_activities[0].timestamp,
        end_time=sample_activities[-1].timestamp,
        status="completed",
        robot_id="robot-001",
    )


@pytest.fixture
def multiple_traces(sample_activities: List[Activity]) -> List[ExecutionTrace]:
    """Create multiple execution traces."""
    base_time = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

    traces = []
    for i in range(3):
        offset = timedelta(hours=i)
        activities = [
            Activity(
                node_id=a.node_id,
                node_type=a.node_type,
                timestamp=a.timestamp + offset,
                duration_ms=a.duration_ms + (i * 100),
                status=a.status,
                inputs=a.inputs,
                outputs=a.outputs,
            )
            for a in sample_activities
        ]

        trace = ExecutionTrace(
            case_id=f"trace-{i:03d}",
            workflow_id="wf-123",
            workflow_name="Test Workflow",
            activities=activities,
            start_time=activities[0].timestamp,
            end_time=activities[-1].timestamp,
            status="completed" if i < 2 else "failed",
            robot_id=f"robot-{i:03d}",
        )
        traces.append(trace)

    return traces


@pytest.fixture
def xes_exporter() -> XESExporter:
    """Create XES exporter instance."""
    return XESExporter()


@pytest.fixture
def xes_importer() -> XESImporter:
    """Create XES importer instance."""
    return XESImporter()


# =============================================================================
# XES Exporter Tests
# =============================================================================


class TestXESExporter:
    """Test XES export functionality."""

    def test_export_single_trace(
        self,
        xes_exporter: XESExporter,
        sample_trace: ExecutionTrace,
    ) -> None:
        """Test exporting a single trace to XES format."""
        xes_content = xes_exporter.export_to_xes([sample_trace])

        assert xes_content is not None
        assert len(xes_content) > 0
        assert "<?xml" in xes_content
        assert "<log" in xes_content
        assert "</log>" in xes_content

    def test_export_multiple_traces(
        self,
        xes_exporter: XESExporter,
        multiple_traces: List[ExecutionTrace],
    ) -> None:
        """Test exporting multiple traces to XES format."""
        xes_content = xes_exporter.export_to_xes(multiple_traces)

        # Count trace elements
        trace_count = xes_content.count("<trace>")
        assert trace_count == 3

    def test_xes_structure_compliance(
        self,
        xes_exporter: XESExporter,
        sample_trace: ExecutionTrace,
    ) -> None:
        """Test XES structure compliance."""
        xes_content = xes_exporter.export_to_xes([sample_trace])

        # Parse XML
        root = ET.fromstring(xes_content)

        # Check root element
        assert root.tag == "log"
        assert root.get("xes.version") == XES_VERSION

        # Check for extensions
        extensions = root.findall("extension")
        assert len(extensions) >= 4  # Concept, Time, Lifecycle, Org

    def test_export_with_attributes(
        self,
        xes_exporter: XESExporter,
        sample_trace: ExecutionTrace,
    ) -> None:
        """Test exporting with input/output attributes."""
        xes_content = xes_exporter.export_to_xes(
            [sample_trace],
            include_attributes=True,
        )

        # Check for attribute inclusion
        assert "casare:inputs" in xes_content or "inputs" in xes_content.lower()

    def test_export_without_attributes(
        self,
        xes_exporter: XESExporter,
        sample_trace: ExecutionTrace,
    ) -> None:
        """Test exporting without input/output attributes."""
        xes_content = xes_exporter.export_to_xes(
            [sample_trace],
            include_attributes=False,
        )

        # Attributes should not be present
        assert "casare:inputs:" not in xes_content

    def test_export_with_lifecycle(
        self,
        xes_exporter: XESExporter,
        sample_trace: ExecutionTrace,
    ) -> None:
        """Test exporting with lifecycle transitions."""
        xes_content = xes_exporter.export_to_xes(
            [sample_trace],
            include_lifecycle=True,
        )

        assert "lifecycle:transition" in xes_content

    def test_export_empty_traces_raises(self, xes_exporter: XESExporter) -> None:
        """Test that exporting empty traces raises ValueError."""
        with pytest.raises(ValueError, match="empty"):
            xes_exporter.export_to_xes([])

    def test_export_to_file(
        self,
        xes_exporter: XESExporter,
        sample_trace: ExecutionTrace,
    ) -> None:
        """Test exporting to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_export"
            result_path = xes_exporter.export_to_file(
                [sample_trace],
                output_path,
            )

            # Check file was created with .xes extension
            assert result_path.endswith(".xes")
            assert Path(result_path).exists()

            # Verify content
            content = Path(result_path).read_text()
            assert "<log" in content

    def test_export_file_adds_extension(
        self,
        xes_exporter: XESExporter,
        sample_trace: ExecutionTrace,
    ) -> None:
        """Test that .xes extension is added if missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_no_ext"
            result_path = xes_exporter.export_to_file([sample_trace], output_path)

            assert result_path.endswith(".xes")

    def test_export_trace_with_failed_activity(
        self,
        xes_exporter: XESExporter,
    ) -> None:
        """Test exporting trace with failed activity."""
        base_time = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

        activities = [
            Activity(
                node_id="node_1",
                node_type="StartNode",
                timestamp=base_time,
                duration_ms=100,
                status=ActivityStatus.COMPLETED,
            ),
            Activity(
                node_id="node_2",
                node_type="FailingNode",
                timestamp=base_time + timedelta(seconds=1),
                duration_ms=5000,
                status=ActivityStatus.FAILED,
                error_message="Connection timeout",
            ),
        ]

        trace = ExecutionTrace(
            case_id="trace-fail",
            workflow_id="wf-123",
            workflow_name="Failing Workflow",
            activities=activities,
            start_time=base_time,
            end_time=base_time + timedelta(seconds=6),
            status="failed",
        )

        xes_content = xes_exporter.export_to_xes([trace])

        # Check error message is included
        assert "error:message" in xes_content or "Connection timeout" in xes_content


# =============================================================================
# XES Importer Tests
# =============================================================================


class TestXESImporter:
    """Test XES import functionality."""

    def test_import_exported_content(
        self,
        xes_exporter: XESExporter,
        xes_importer: XESImporter,
        sample_trace: ExecutionTrace,
    ) -> None:
        """Test importing content that was exported."""
        xes_content = xes_exporter.export_to_xes([sample_trace])
        imported_traces = xes_importer.import_from_string(xes_content)

        assert len(imported_traces) == 1
        imported = imported_traces[0]

        assert imported.case_id == sample_trace.case_id
        assert imported.workflow_id == sample_trace.workflow_id
        assert len(imported.activities) == len(sample_trace.activities)

    def test_import_multiple_traces(
        self,
        xes_exporter: XESExporter,
        xes_importer: XESImporter,
        multiple_traces: List[ExecutionTrace],
    ) -> None:
        """Test importing multiple traces."""
        xes_content = xes_exporter.export_to_xes(multiple_traces)
        imported_traces = xes_importer.import_from_string(xes_content)

        assert len(imported_traces) == len(multiple_traces)

    def test_import_from_file(
        self,
        xes_exporter: XESExporter,
        xes_importer: XESImporter,
        sample_trace: ExecutionTrace,
    ) -> None:
        """Test importing from file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.xes"
            xes_exporter.export_to_file([sample_trace], output_path)

            imported_traces = xes_importer.import_from_file(output_path)

            assert len(imported_traces) == 1
            assert imported_traces[0].case_id == sample_trace.case_id

    def test_import_nonexistent_file_raises(
        self,
        xes_importer: XESImporter,
    ) -> None:
        """Test that importing nonexistent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            xes_importer.import_from_file("/nonexistent/path/file.xes")

    def test_import_invalid_xml_raises(
        self,
        xes_importer: XESImporter,
    ) -> None:
        """Test that importing invalid XML raises ValueError."""
        with pytest.raises(ValueError, match="Invalid XES"):
            xes_importer.import_from_string("<invalid>not closed")

    def test_roundtrip_preserves_data(
        self,
        xes_exporter: XESExporter,
        xes_importer: XESImporter,
        multiple_traces: List[ExecutionTrace],
    ) -> None:
        """Test that export->import roundtrip preserves essential data."""
        xes_content = xes_exporter.export_to_xes(multiple_traces)
        imported = xes_importer.import_from_string(xes_content)

        for original, imported_trace in zip(multiple_traces, imported):
            assert imported_trace.case_id == original.case_id
            assert imported_trace.workflow_id == original.workflow_id
            assert imported_trace.workflow_name == original.workflow_name

            # Activity count should match
            assert len(imported_trace.activities) == len(original.activities)


# =============================================================================
# Integration Tests
# =============================================================================


class TestXESIntegration:
    """Integration tests for XES export/import."""

    def test_export_large_trace(self, xes_exporter: XESExporter) -> None:
        """Test exporting trace with many activities."""
        base_time = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

        # Create 100 activities
        activities = [
            Activity(
                node_id=f"node_{i}",
                node_type=f"Node{i % 5}",
                timestamp=base_time + timedelta(seconds=i),
                duration_ms=100 + i,
                status=ActivityStatus.COMPLETED,
            )
            for i in range(100)
        ]

        trace = ExecutionTrace(
            case_id="large-trace",
            workflow_id="wf-large",
            workflow_name="Large Workflow",
            activities=activities,
            start_time=base_time,
            end_time=base_time + timedelta(seconds=100),
            status="completed",
        )

        xes_content = xes_exporter.export_to_xes([trace])

        # Should have 100 events
        event_count = xes_content.count("<event>")
        assert event_count == 100

    def test_export_with_special_characters(
        self,
        xes_exporter: XESExporter,
    ) -> None:
        """Test exporting activities with special characters."""
        base_time = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

        activities = [
            Activity(
                node_id="node_special",
                node_type="DataNode<Test>",  # Contains < >
                timestamp=base_time,
                duration_ms=100,
                status=ActivityStatus.COMPLETED,
                inputs={"query": "SELECT * FROM users WHERE name='John'"},
                outputs={"result": "Success & Done"},
            ),
        ]

        trace = ExecutionTrace(
            case_id="special-trace",
            workflow_id="wf-special",
            workflow_name="Workflow with 'Special' & <Characters>",
            activities=activities,
            start_time=base_time,
            status="completed",
        )

        # Should not raise
        xes_content = xes_exporter.export_to_xes([trace])

        # Should be valid XML (no parsing error)
        ET.fromstring(xes_content)
