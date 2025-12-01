"""Tests for Process Mining module.

Tests AI-powered process discovery from execution logs.
"""

from datetime import datetime, timedelta

import pytest

from casare_rpa.infrastructure.analytics.process_mining import (
    Activity,
    ActivityStatus,
    ConformanceChecker,
    ConformanceReport,
    DeviationType,
    DirectFollowsEdge,
    ExecutionTrace,
    InsightCategory,
    ProcessDiscovery,
    ProcessEnhancer,
    ProcessEventLog,
    ProcessInsight,
    ProcessMiner,
    ProcessModel,
    get_process_miner,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_activity() -> Activity:
    """Create sample activity."""
    return Activity(
        node_id="node_1",
        node_type="click",
        timestamp=datetime.now(),
        duration_ms=1500,
        status=ActivityStatus.COMPLETED,
        inputs={"selector": "#button"},
        outputs={"result": "success"},
    )


@pytest.fixture
def sample_trace() -> ExecutionTrace:
    """Create sample execution trace."""
    now = datetime.now()
    activities = [
        Activity(
            node_id="start",
            node_type="start",
            timestamp=now,
            duration_ms=100,
            status=ActivityStatus.COMPLETED,
        ),
        Activity(
            node_id="click_1",
            node_type="click",
            timestamp=now + timedelta(milliseconds=100),
            duration_ms=500,
            status=ActivityStatus.COMPLETED,
        ),
        Activity(
            node_id="type_1",
            node_type="type",
            timestamp=now + timedelta(milliseconds=600),
            duration_ms=300,
            status=ActivityStatus.COMPLETED,
        ),
        Activity(
            node_id="end",
            node_type="end",
            timestamp=now + timedelta(milliseconds=900),
            duration_ms=50,
            status=ActivityStatus.COMPLETED,
        ),
    ]
    return ExecutionTrace(
        case_id="trace_001",
        workflow_id="wf_test",
        workflow_name="Test Workflow",
        activities=activities,
        start_time=now,
        end_time=now + timedelta(milliseconds=950),
        status="completed",
        robot_id="robot_1",
    )


@pytest.fixture
def multiple_traces() -> list[ExecutionTrace]:
    """Create multiple traces for testing."""
    traces = []
    base_time = datetime.now()

    # Trace 1: Normal path
    traces.append(
        ExecutionTrace(
            case_id="trace_001",
            workflow_id="wf_test",
            workflow_name="Test Workflow",
            activities=[
                Activity(
                    node_id="start",
                    node_type="start",
                    timestamp=base_time,
                    duration_ms=100,
                    status=ActivityStatus.COMPLETED,
                ),
                Activity(
                    node_id="click_1",
                    node_type="click",
                    timestamp=base_time + timedelta(milliseconds=100),
                    duration_ms=500,
                    status=ActivityStatus.COMPLETED,
                ),
                Activity(
                    node_id="end",
                    node_type="end",
                    timestamp=base_time + timedelta(milliseconds=600),
                    duration_ms=50,
                    status=ActivityStatus.COMPLETED,
                ),
            ],
            start_time=base_time,
            end_time=base_time + timedelta(milliseconds=650),
            status="completed",
        )
    )

    # Trace 2: Same path (same variant)
    traces.append(
        ExecutionTrace(
            case_id="trace_002",
            workflow_id="wf_test",
            workflow_name="Test Workflow",
            activities=[
                Activity(
                    node_id="start",
                    node_type="start",
                    timestamp=base_time,
                    duration_ms=120,
                    status=ActivityStatus.COMPLETED,
                ),
                Activity(
                    node_id="click_1",
                    node_type="click",
                    timestamp=base_time + timedelta(milliseconds=120),
                    duration_ms=450,
                    status=ActivityStatus.COMPLETED,
                ),
                Activity(
                    node_id="end",
                    node_type="end",
                    timestamp=base_time + timedelta(milliseconds=570),
                    duration_ms=60,
                    status=ActivityStatus.COMPLETED,
                ),
            ],
            start_time=base_time,
            end_time=base_time + timedelta(milliseconds=630),
            status="completed",
        )
    )

    # Trace 3: Different path (different variant)
    traces.append(
        ExecutionTrace(
            case_id="trace_003",
            workflow_id="wf_test",
            workflow_name="Test Workflow",
            activities=[
                Activity(
                    node_id="start",
                    node_type="start",
                    timestamp=base_time,
                    duration_ms=100,
                    status=ActivityStatus.COMPLETED,
                ),
                Activity(
                    node_id="click_1",
                    node_type="click",
                    timestamp=base_time + timedelta(milliseconds=100),
                    duration_ms=500,
                    status=ActivityStatus.COMPLETED,
                ),
                Activity(
                    node_id="type_1",
                    node_type="type",
                    timestamp=base_time + timedelta(milliseconds=600),
                    duration_ms=300,
                    status=ActivityStatus.COMPLETED,
                ),
                Activity(
                    node_id="end",
                    node_type="end",
                    timestamp=base_time + timedelta(milliseconds=900),
                    duration_ms=50,
                    status=ActivityStatus.COMPLETED,
                ),
            ],
            start_time=base_time,
            end_time=base_time + timedelta(milliseconds=950),
            status="completed",
        )
    )

    return traces


# =============================================================================
# Activity Tests
# =============================================================================


class TestActivity:
    """Tests for Activity dataclass."""

    def test_create_activity(self, sample_activity: Activity) -> None:
        """Test activity creation."""
        assert sample_activity.node_id == "node_1"
        assert sample_activity.node_type == "click"
        assert sample_activity.duration_ms == 1500
        assert sample_activity.status == ActivityStatus.COMPLETED

    def test_activity_to_dict(self, sample_activity: Activity) -> None:
        """Test activity serialization."""
        data = sample_activity.to_dict()
        assert data["node_id"] == "node_1"
        assert data["status"] == "completed"
        assert "timestamp" in data

    def test_activity_from_dict(self, sample_activity: Activity) -> None:
        """Test activity deserialization."""
        data = sample_activity.to_dict()
        restored = Activity.from_dict(data)
        assert restored.node_id == sample_activity.node_id
        assert restored.status == sample_activity.status


class TestActivityStatus:
    """Tests for ActivityStatus enum."""

    def test_status_values(self) -> None:
        """Test status enum values."""
        assert ActivityStatus.COMPLETED.value == "completed"
        assert ActivityStatus.FAILED.value == "failed"
        assert ActivityStatus.SKIPPED.value == "skipped"
        assert ActivityStatus.TIMEOUT.value == "timeout"


# =============================================================================
# ExecutionTrace Tests
# =============================================================================


class TestExecutionTrace:
    """Tests for ExecutionTrace dataclass."""

    def test_create_trace(self, sample_trace: ExecutionTrace) -> None:
        """Test trace creation."""
        assert sample_trace.case_id == "trace_001"
        assert sample_trace.workflow_id == "wf_test"
        assert len(sample_trace.activities) == 4

    def test_trace_variant(self, sample_trace: ExecutionTrace) -> None:
        """Test variant calculation."""
        variant = sample_trace.variant
        assert isinstance(variant, str)
        assert len(variant) == 8  # MD5 hash prefix

    def test_trace_total_duration(self, sample_trace: ExecutionTrace) -> None:
        """Test total duration calculation."""
        duration = sample_trace.total_duration_ms
        assert duration > 0

    def test_trace_activity_sequence(self, sample_trace: ExecutionTrace) -> None:
        """Test activity sequence extraction."""
        sequence = sample_trace.activity_sequence
        assert sequence == ["start", "click_1", "type_1", "end"]

    def test_trace_success_rate(self, sample_trace: ExecutionTrace) -> None:
        """Test success rate calculation."""
        rate = sample_trace.success_rate
        assert rate == 1.0  # All completed

    def test_trace_to_dict(self, sample_trace: ExecutionTrace) -> None:
        """Test trace serialization."""
        data = sample_trace.to_dict()
        assert data["case_id"] == "trace_001"
        assert data["workflow_id"] == "wf_test"
        assert len(data["activities"]) == 4


# =============================================================================
# ProcessEventLog Tests
# =============================================================================


class TestProcessEventLog:
    """Tests for ProcessEventLog."""

    def test_init(self) -> None:
        """Test event log initialization."""
        log = ProcessEventLog(max_traces=100)
        assert log.get_trace_count() == 0

    def test_add_trace(self, sample_trace: ExecutionTrace) -> None:
        """Test adding trace."""
        log = ProcessEventLog()
        log.add_trace(sample_trace)
        assert log.get_trace_count() == 1

    def test_get_trace(self, sample_trace: ExecutionTrace) -> None:
        """Test retrieving trace by ID."""
        log = ProcessEventLog()
        log.add_trace(sample_trace)
        retrieved = log.get_trace("trace_001")
        assert retrieved is not None
        assert retrieved.case_id == "trace_001"

    def test_get_traces_for_workflow(
        self, multiple_traces: list[ExecutionTrace]
    ) -> None:
        """Test getting traces for workflow."""
        log = ProcessEventLog()
        for trace in multiple_traces:
            log.add_trace(trace)

        traces = log.get_traces_for_workflow("wf_test")
        assert len(traces) == 3

    def test_max_traces_eviction(self) -> None:
        """Test trace eviction when at capacity."""
        log = ProcessEventLog(max_traces=2)

        for i in range(3):
            trace = ExecutionTrace(
                case_id=f"trace_{i}",
                workflow_id="wf_test",
                workflow_name="Test",
                activities=[],
                start_time=datetime.now(),
            )
            log.add_trace(trace)

        assert log.get_trace_count() == 2
        assert log.get_trace("trace_0") is None  # Evicted
        assert log.get_trace("trace_2") is not None

    def test_clear(self, sample_trace: ExecutionTrace) -> None:
        """Test clearing event log."""
        log = ProcessEventLog()
        log.add_trace(sample_trace)
        log.clear()
        assert log.get_trace_count() == 0


# =============================================================================
# ProcessDiscovery Tests
# =============================================================================


class TestProcessDiscovery:
    """Tests for ProcessDiscovery."""

    def test_init(self) -> None:
        """Test discovery initialization."""
        discovery = ProcessDiscovery()
        assert discovery is not None

    def test_discover_empty(self) -> None:
        """Test discovery with empty traces."""
        discovery = ProcessDiscovery()
        model = discovery.discover([])
        assert model.workflow_id == "unknown"
        assert len(model.nodes) == 0

    def test_discover_single_trace(self, sample_trace: ExecutionTrace) -> None:
        """Test discovery with single trace."""
        discovery = ProcessDiscovery()
        model = discovery.discover([sample_trace])

        assert model.workflow_id == "wf_test"
        assert len(model.nodes) == 4
        assert "start" in model.nodes
        assert "end" in model.nodes
        assert "start" in model.entry_nodes
        assert "end" in model.exit_nodes

    def test_discover_edges(self, sample_trace: ExecutionTrace) -> None:
        """Test edge discovery."""
        discovery = ProcessDiscovery()
        model = discovery.discover([sample_trace])

        # Check edges exist
        assert "start" in model.edges
        assert "click_1" in model.edges["start"]

    def test_discover_variants(self, multiple_traces: list[ExecutionTrace]) -> None:
        """Test variant discovery."""
        discovery = ProcessDiscovery()
        model = discovery.discover(multiple_traces)

        assert len(model.variants) == 2  # Two distinct paths
        assert model.trace_count == 3

    def test_discover_variant_groups(
        self, multiple_traces: list[ExecutionTrace]
    ) -> None:
        """Test grouping traces by variant."""
        discovery = ProcessDiscovery()
        variants = discovery.discover_variants(multiple_traces)

        assert len(variants) == 2
        # Most common variant has 2 traces
        max_count = max(len(traces) for traces in variants.values())
        assert max_count == 2


# =============================================================================
# ProcessModel Tests
# =============================================================================


class TestProcessModel:
    """Tests for ProcessModel."""

    def test_create_model(self) -> None:
        """Test model creation."""
        model = ProcessModel(workflow_id="wf_test")
        assert model.workflow_id == "wf_test"
        assert len(model.nodes) == 0

    def test_get_edge_frequency(self) -> None:
        """Test edge frequency lookup."""
        model = ProcessModel(workflow_id="wf_test")
        model.edges["a"] = {"b": DirectFollowsEdge(source="a", target="b", frequency=5)}

        assert model.get_edge_frequency("a", "b") == 5
        assert model.get_edge_frequency("a", "c") == 0

    def test_to_dict(self, multiple_traces: list[ExecutionTrace]) -> None:
        """Test model serialization."""
        discovery = ProcessDiscovery()
        model = discovery.discover(multiple_traces)
        data = model.to_dict()

        assert data["workflow_id"] == "wf_test"
        assert "nodes" in data
        assert "edges" in data
        assert "variants" in data

    def test_to_mermaid(self, multiple_traces: list[ExecutionTrace]) -> None:
        """Test Mermaid diagram export."""
        discovery = ProcessDiscovery()
        model = discovery.discover(multiple_traces)
        mermaid = model.to_mermaid()

        assert mermaid.startswith("graph LR")
        assert "start" in mermaid
        assert "-->" in mermaid


# =============================================================================
# ConformanceChecker Tests
# =============================================================================


class TestConformanceChecker:
    """Tests for ConformanceChecker."""

    def test_init(self) -> None:
        """Test conformance checker initialization."""
        checker = ConformanceChecker()
        assert checker is not None

    def test_check_conformance_perfect(
        self, sample_trace: ExecutionTrace, multiple_traces: list[ExecutionTrace]
    ) -> None:
        """Test conformance with perfect fit."""
        discovery = ProcessDiscovery()
        model = discovery.discover(multiple_traces)

        checker = ConformanceChecker()
        report = checker.check_conformance(multiple_traces[2], model)

        assert report.fitness_score > 0.8
        assert report.is_conformant

    def test_check_conformance_deviation(
        self, multiple_traces: list[ExecutionTrace]
    ) -> None:
        """Test conformance with deviations."""
        discovery = ProcessDiscovery()
        model = discovery.discover(multiple_traces[:2])  # Build model from subset

        # Create trace with unexpected node
        deviant_trace = ExecutionTrace(
            case_id="deviant",
            workflow_id="wf_test",
            workflow_name="Test",
            activities=[
                Activity(
                    node_id="start",
                    node_type="start",
                    timestamp=datetime.now(),
                    duration_ms=100,
                    status=ActivityStatus.COMPLETED,
                ),
                Activity(
                    node_id="unexpected",
                    node_type="unknown",
                    timestamp=datetime.now(),
                    duration_ms=100,
                    status=ActivityStatus.COMPLETED,
                ),
                Activity(
                    node_id="end",
                    node_type="end",
                    timestamp=datetime.now(),
                    duration_ms=100,
                    status=ActivityStatus.COMPLETED,
                ),
            ],
            start_time=datetime.now(),
            status="completed",
        )

        checker = ConformanceChecker()
        report = checker.check_conformance(deviant_trace, model)

        assert len(report.unexpected_activities) > 0
        assert "unexpected" in report.unexpected_activities

    def test_batch_check(self, multiple_traces: list[ExecutionTrace]) -> None:
        """Test batch conformance checking."""
        discovery = ProcessDiscovery()
        model = discovery.discover(multiple_traces)

        checker = ConformanceChecker()
        result = checker.batch_check(multiple_traces, model)

        assert result["total_traces"] == 3
        assert "average_fitness" in result
        assert "conformance_rate" in result


# =============================================================================
# ProcessEnhancer Tests
# =============================================================================


class TestProcessEnhancer:
    """Tests for ProcessEnhancer."""

    def test_init(self) -> None:
        """Test enhancer initialization."""
        enhancer = ProcessEnhancer()
        assert enhancer is not None

    def test_analyze_empty(self) -> None:
        """Test analysis with empty data."""
        enhancer = ProcessEnhancer()
        model = ProcessModel(workflow_id="wf_test")
        insights = enhancer.analyze(model, [])
        assert isinstance(insights, list)

    def test_find_slow_nodes(self) -> None:
        """Test slow node detection."""
        enhancer = ProcessEnhancer()

        # Create trace with slow node
        slow_trace = ExecutionTrace(
            case_id="slow",
            workflow_id="wf_test",
            workflow_name="Test",
            activities=[
                Activity(
                    node_id="start",
                    node_type="start",
                    timestamp=datetime.now(),
                    duration_ms=100,
                    status=ActivityStatus.COMPLETED,
                ),
                Activity(
                    node_id="slow_node",
                    node_type="http",
                    timestamp=datetime.now(),
                    duration_ms=10000,  # 10 seconds
                    status=ActivityStatus.COMPLETED,
                ),
                Activity(
                    node_id="end",
                    node_type="end",
                    timestamp=datetime.now(),
                    duration_ms=100,
                    status=ActivityStatus.COMPLETED,
                ),
            ],
            start_time=datetime.now(),
            status="completed",
        )

        discovery = ProcessDiscovery()
        model = discovery.discover([slow_trace])

        insights = enhancer.analyze(model, [slow_trace])

        # Should find bottleneck insight
        bottleneck_insights = [
            i for i in insights if i.category == InsightCategory.BOTTLENECK
        ]
        assert len(bottleneck_insights) > 0

    def test_find_error_patterns(self) -> None:
        """Test error pattern detection."""
        enhancer = ProcessEnhancer()

        # Create traces with failing node
        traces = []
        for i in range(10):
            status = ActivityStatus.FAILED if i < 3 else ActivityStatus.COMPLETED
            traces.append(
                ExecutionTrace(
                    case_id=f"trace_{i}",
                    workflow_id="wf_test",
                    workflow_name="Test",
                    activities=[
                        Activity(
                            node_id="start",
                            node_type="start",
                            timestamp=datetime.now(),
                            duration_ms=100,
                            status=ActivityStatus.COMPLETED,
                        ),
                        Activity(
                            node_id="error_prone",
                            node_type="click",
                            timestamp=datetime.now(),
                            duration_ms=500,
                            status=status,
                        ),
                        Activity(
                            node_id="end",
                            node_type="end",
                            timestamp=datetime.now(),
                            duration_ms=100,
                            status=ActivityStatus.COMPLETED,
                        ),
                    ],
                    start_time=datetime.now(),
                    status="completed",
                )
            )

        discovery = ProcessDiscovery()
        model = discovery.discover(traces)

        insights = enhancer.analyze(model, traces)

        # Should find error pattern insight
        error_insights = [
            i for i in insights if i.category == InsightCategory.ERROR_PATTERN
        ]
        assert len(error_insights) > 0


# =============================================================================
# ProcessMiner (Main Orchestrator) Tests
# =============================================================================


class TestProcessMiner:
    """Tests for ProcessMiner."""

    def test_init(self) -> None:
        """Test miner initialization."""
        miner = ProcessMiner()
        assert miner is not None
        assert miner.event_log is not None
        assert miner.discovery is not None

    def test_record_trace(self, sample_trace: ExecutionTrace) -> None:
        """Test recording trace."""
        miner = ProcessMiner()
        miner.record_trace(sample_trace)
        assert miner.event_log.get_trace_count() == 1

    def test_record_activity(self) -> None:
        """Test recording individual activity."""
        miner = ProcessMiner()
        miner.record_activity(
            case_id="case_001",
            workflow_id="wf_test",
            workflow_name="Test",
            node_id="node_1",
            node_type="click",
            duration_ms=500,
            status=ActivityStatus.COMPLETED,
        )

        trace = miner.event_log.get_trace("case_001")
        assert trace is not None
        assert len(trace.activities) == 1

    def test_complete_trace(self) -> None:
        """Test completing trace."""
        miner = ProcessMiner()
        miner.record_activity(
            case_id="case_001",
            workflow_id="wf_test",
            workflow_name="Test",
            node_id="node_1",
            node_type="click",
            duration_ms=500,
            status=ActivityStatus.COMPLETED,
        )
        miner.complete_trace("case_001", status="completed")

        trace = miner.event_log.get_trace("case_001")
        assert trace.status == "completed"
        assert trace.end_time is not None

    def test_discover_process(self, multiple_traces: list[ExecutionTrace]) -> None:
        """Test process discovery."""
        miner = ProcessMiner()
        for trace in multiple_traces:
            miner.record_trace(trace)

        model = miner.discover_process("wf_test", min_traces=2)
        assert model is not None
        assert model.workflow_id == "wf_test"

    def test_discover_insufficient_traces(self) -> None:
        """Test discovery with insufficient data."""
        miner = ProcessMiner()
        trace = ExecutionTrace(
            case_id="single",
            workflow_id="wf_test",
            workflow_name="Test",
            activities=[],
            start_time=datetime.now(),
        )
        miner.record_trace(trace)

        model = miner.discover_process("wf_test", min_traces=10)
        assert model is None

    def test_get_variants(self, multiple_traces: list[ExecutionTrace]) -> None:
        """Test variant analysis."""
        miner = ProcessMiner()
        for trace in multiple_traces:
            miner.record_trace(trace)

        variants = miner.get_variants("wf_test")
        assert variants["total_traces"] == 3
        assert variants["variant_count"] == 2

    def test_get_process_summary(self, multiple_traces: list[ExecutionTrace]) -> None:
        """Test process summary."""
        miner = ProcessMiner()
        for trace in multiple_traces:
            miner.record_trace(trace)

        miner.discover_process("wf_test", min_traces=2)
        summary = miner.get_process_summary("wf_test")

        assert summary["workflow_id"] == "wf_test"
        assert summary["trace_count"] == 3
        assert summary["has_model"]
        assert "node_count" in summary

    def test_get_insights(self, multiple_traces: list[ExecutionTrace]) -> None:
        """Test getting optimization insights."""
        miner = ProcessMiner()
        for trace in multiple_traces:
            miner.record_trace(trace)

        insights = miner.get_insights("wf_test")
        assert isinstance(insights, list)


class TestGetProcessMiner:
    """Tests for singleton accessor."""

    def test_get_process_miner(self) -> None:
        """Test singleton pattern."""
        miner1 = get_process_miner()
        miner2 = get_process_miner()
        assert miner1 is miner2


# =============================================================================
# Integration Tests
# =============================================================================


class TestProcessMiningIntegration:
    """Integration tests for process mining workflow."""

    def test_full_mining_workflow(self) -> None:
        """Test complete mining workflow."""
        miner = ProcessMiner()

        # Simulate workflow executions
        for i in range(15):
            case_id = f"case_{i}"

            # Start
            miner.record_activity(
                case_id=case_id,
                workflow_id="invoice_process",
                workflow_name="Invoice Processing",
                node_id="start",
                node_type="start",
                duration_ms=50,
                status=ActivityStatus.COMPLETED,
            )

            # Open browser
            miner.record_activity(
                case_id=case_id,
                workflow_id="invoice_process",
                workflow_name="Invoice Processing",
                node_id="open_browser",
                node_type="browser",
                duration_ms=2000,
                status=ActivityStatus.COMPLETED,
            )

            # Navigate (sometimes slow)
            miner.record_activity(
                case_id=case_id,
                workflow_id="invoice_process",
                workflow_name="Invoice Processing",
                node_id="navigate",
                node_type="navigate",
                duration_ms=3000 if i % 3 == 0 else 1000,
                status=ActivityStatus.COMPLETED,
            )

            # Extract data (sometimes fails)
            miner.record_activity(
                case_id=case_id,
                workflow_id="invoice_process",
                workflow_name="Invoice Processing",
                node_id="extract_data",
                node_type="extract",
                duration_ms=500,
                status=ActivityStatus.FAILED
                if i % 5 == 0
                else ActivityStatus.COMPLETED,
            )

            # End
            miner.record_activity(
                case_id=case_id,
                workflow_id="invoice_process",
                workflow_name="Invoice Processing",
                node_id="end",
                node_type="end",
                duration_ms=50,
                status=ActivityStatus.COMPLETED,
            )

            miner.complete_trace(case_id)

        # Discover process
        model = miner.discover_process("invoice_process", min_traces=10)
        assert model is not None
        assert len(model.nodes) == 5

        # Check conformance
        traces = miner.event_log.get_traces_for_workflow("invoice_process")
        report = miner.conformance.batch_check(traces, model)
        assert report["conformance_rate"] > 0.8

        # Get insights
        insights = miner.get_insights("invoice_process")
        assert len(insights) > 0

        # Get variants
        variants = miner.get_variants("invoice_process")
        assert variants["variant_count"] == 1  # All same path

        # Get summary
        summary = miner.get_process_summary("invoice_process")
        assert summary["has_model"]
        assert summary["node_count"] == 5
