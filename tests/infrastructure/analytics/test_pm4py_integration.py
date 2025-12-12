"""
Tests for PM4Py Integration module.

Tests PM4Py integration including:
- Discovery algorithms (Alpha, Inductive, Heuristic)
- Conformance checking (Token Replay, Alignments)
- Model conversion and structure extraction
- Lazy loading and availability checks
"""

from datetime import datetime, timedelta, timezone
from typing import List
from unittest.mock import MagicMock, patch

import pytest

from casare_rpa.infrastructure.analytics.process_mining import (
    Activity,
    ActivityStatus,
    ExecutionTrace,
)
from casare_rpa.infrastructure.analytics.pm4py_integration import (
    PM4PyIntegration,
    DiscoveryAlgorithm,
    ConformanceMethod,
    PetriNetResult,
    BPMNResult,
    AlignmentResult,
    TokenReplayResult,
    ConformanceSummary,
    get_pm4py_integration,
)


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def sample_traces() -> List[ExecutionTrace]:
    """Create sample execution traces for testing."""
    base_time = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

    traces = []
    for i in range(10):
        offset = timedelta(hours=i)
        activities = [
            Activity(
                node_id="start",
                node_type="StartNode",
                timestamp=base_time + offset,
                duration_ms=100,
                status=ActivityStatus.COMPLETED,
            ),
            Activity(
                node_id="process_a",
                node_type="ProcessA",
                timestamp=base_time + offset + timedelta(seconds=1),
                duration_ms=500,
                status=ActivityStatus.COMPLETED,
            ),
            Activity(
                node_id="process_b",
                node_type="ProcessB",
                timestamp=base_time + offset + timedelta(seconds=2),
                duration_ms=300,
                status=ActivityStatus.COMPLETED,
            ),
            Activity(
                node_id="end",
                node_type="EndNode",
                timestamp=base_time + offset + timedelta(seconds=3),
                duration_ms=50,
                status=ActivityStatus.COMPLETED,
            ),
        ]

        trace = ExecutionTrace(
            case_id=f"trace-{i:03d}",
            workflow_id="wf-test",
            workflow_name="Test Workflow",
            activities=activities,
            start_time=activities[0].timestamp,
            end_time=activities[-1].timestamp,
            status="completed",
            robot_id=f"robot-{i % 2}",
        )
        traces.append(trace)

    return traces


@pytest.fixture
def variant_traces() -> List[ExecutionTrace]:
    """Create traces with different variants for testing."""
    base_time = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

    traces = []

    # Variant 1: A -> B -> C (5 traces)
    for i in range(5):
        offset = timedelta(hours=i)
        activities = [
            Activity(
                node_id="start",
                node_type="Start",
                timestamp=base_time + offset,
                duration_ms=100,
                status=ActivityStatus.COMPLETED,
            ),
            Activity(
                node_id="task_a",
                node_type="TaskA",
                timestamp=base_time + offset + timedelta(seconds=1),
                duration_ms=500,
                status=ActivityStatus.COMPLETED,
            ),
            Activity(
                node_id="task_b",
                node_type="TaskB",
                timestamp=base_time + offset + timedelta(seconds=2),
                duration_ms=300,
                status=ActivityStatus.COMPLETED,
            ),
            Activity(
                node_id="task_c",
                node_type="TaskC",
                timestamp=base_time + offset + timedelta(seconds=3),
                duration_ms=200,
                status=ActivityStatus.COMPLETED,
            ),
            Activity(
                node_id="end",
                node_type="End",
                timestamp=base_time + offset + timedelta(seconds=4),
                duration_ms=50,
                status=ActivityStatus.COMPLETED,
            ),
        ]
        trace = ExecutionTrace(
            case_id=f"variant1-{i}",
            workflow_id="wf-variants",
            workflow_name="Variant Workflow",
            activities=activities,
            start_time=activities[0].timestamp,
            end_time=activities[-1].timestamp,
            status="completed",
        )
        traces.append(trace)

    # Variant 2: A -> C -> B (3 traces)
    for i in range(3):
        offset = timedelta(hours=5 + i)
        activities = [
            Activity(
                node_id="start",
                node_type="Start",
                timestamp=base_time + offset,
                duration_ms=100,
                status=ActivityStatus.COMPLETED,
            ),
            Activity(
                node_id="task_a",
                node_type="TaskA",
                timestamp=base_time + offset + timedelta(seconds=1),
                duration_ms=500,
                status=ActivityStatus.COMPLETED,
            ),
            Activity(
                node_id="task_c",
                node_type="TaskC",
                timestamp=base_time + offset + timedelta(seconds=2),
                duration_ms=200,
                status=ActivityStatus.COMPLETED,
            ),
            Activity(
                node_id="task_b",
                node_type="TaskB",
                timestamp=base_time + offset + timedelta(seconds=3),
                duration_ms=300,
                status=ActivityStatus.COMPLETED,
            ),
            Activity(
                node_id="end",
                node_type="End",
                timestamp=base_time + offset + timedelta(seconds=4),
                duration_ms=50,
                status=ActivityStatus.COMPLETED,
            ),
        ]
        trace = ExecutionTrace(
            case_id=f"variant2-{i}",
            workflow_id="wf-variants",
            workflow_name="Variant Workflow",
            activities=activities,
            start_time=activities[0].timestamp,
            end_time=activities[-1].timestamp,
            status="completed",
        )
        traces.append(trace)

    return traces


@pytest.fixture
def pm4py_integration() -> PM4PyIntegration:
    """Create PM4Py integration instance."""
    return PM4PyIntegration()


# =============================================================================
# Availability Tests
# =============================================================================


class TestPM4PyAvailability:
    """Test PM4Py availability detection."""

    def test_is_available_property(self, pm4py_integration: PM4PyIntegration) -> None:
        """Test that is_available property works."""
        # Should return True or False without raising
        result = pm4py_integration.is_available
        assert isinstance(result, bool)

    def test_singleton_instance(self) -> None:
        """Test that get_pm4py_integration returns singleton."""
        instance1 = get_pm4py_integration()
        instance2 = get_pm4py_integration()
        assert instance1 is instance2


# =============================================================================
# Conversion Tests
# =============================================================================


class TestTraceConversion:
    """Test trace conversion to PM4Py formats."""

    @pytest.mark.skipif(
        not PM4PyIntegration().is_available,
        reason="PM4Py not installed",
    )
    def test_traces_to_dataframe(
        self,
        pm4py_integration: PM4PyIntegration,
        sample_traces: List[ExecutionTrace],
    ) -> None:
        """Test conversion to pandas DataFrame."""
        df = pm4py_integration.traces_to_dataframe(sample_traces)

        assert df is not None
        assert len(df) == len(sample_traces) * 4  # 4 activities per trace
        assert "case:concept:name" in df.columns
        assert "concept:name" in df.columns
        assert "time:timestamp" in df.columns

    @pytest.mark.skipif(
        not PM4PyIntegration().is_available,
        reason="PM4Py not installed",
    )
    def test_traces_to_event_log(
        self,
        pm4py_integration: PM4PyIntegration,
        sample_traces: List[ExecutionTrace],
    ) -> None:
        """Test conversion to PM4Py EventLog."""
        log = pm4py_integration.traces_to_event_log(sample_traces)

        assert log is not None
        assert len(log) == len(sample_traces)


# =============================================================================
# Discovery Tests
# =============================================================================


class TestProcessDiscovery:
    """Test process discovery algorithms."""

    @pytest.mark.skipif(
        not PM4PyIntegration().is_available,
        reason="PM4Py not installed",
    )
    def test_discover_petri_net_inductive(
        self,
        pm4py_integration: PM4PyIntegration,
        sample_traces: List[ExecutionTrace],
    ) -> None:
        """Test Petri net discovery with Inductive Miner."""
        result = pm4py_integration.discover_petri_net(
            sample_traces,
            algorithm=DiscoveryAlgorithm.INDUCTIVE,
        )

        assert isinstance(result, PetriNetResult)
        assert result.net is not None
        assert result.initial_marking is not None
        assert result.final_marking is not None
        assert len(result.places) > 0
        assert len(result.transitions) > 0
        assert result.algorithm == "inductive"

    @pytest.mark.skipif(
        not PM4PyIntegration().is_available,
        reason="PM4Py not installed",
    )
    def test_discover_petri_net_alpha(
        self,
        pm4py_integration: PM4PyIntegration,
        sample_traces: List[ExecutionTrace],
    ) -> None:
        """Test Petri net discovery with Alpha Miner."""
        result = pm4py_integration.discover_petri_net(
            sample_traces,
            algorithm=DiscoveryAlgorithm.ALPHA,
        )

        assert isinstance(result, PetriNetResult)
        assert result.algorithm == "alpha"

    @pytest.mark.skipif(
        not PM4PyIntegration().is_available,
        reason="PM4Py not installed",
    )
    def test_discover_petri_net_heuristic(
        self,
        pm4py_integration: PM4PyIntegration,
        sample_traces: List[ExecutionTrace],
    ) -> None:
        """Test Petri net discovery with Heuristic Miner."""
        result = pm4py_integration.discover_petri_net(
            sample_traces,
            algorithm=DiscoveryAlgorithm.HEURISTIC,
        )

        assert isinstance(result, PetriNetResult)
        assert result.algorithm == "heuristic"

    @pytest.mark.skipif(
        not PM4PyIntegration().is_available,
        reason="PM4Py not installed",
    )
    def test_discover_bpmn(
        self,
        pm4py_integration: PM4PyIntegration,
        sample_traces: List[ExecutionTrace],
    ) -> None:
        """Test BPMN model discovery."""
        result = pm4py_integration.discover_bpmn(sample_traces)

        assert isinstance(result, BPMNResult)
        assert result.model is not None
        assert result.algorithm is not None

    @pytest.mark.skipif(
        not PM4PyIntegration().is_available,
        reason="PM4Py not installed",
    )
    def test_discover_dfg(
        self,
        pm4py_integration: PM4PyIntegration,
        sample_traces: List[ExecutionTrace],
    ) -> None:
        """Test Direct-Follows Graph discovery."""
        result = pm4py_integration.discover_dfg(sample_traces)

        assert isinstance(result, dict)
        assert "edges" in result
        assert "start_activities" in result
        assert "end_activities" in result
        assert result["node_count"] > 0

    def test_discover_empty_traces_raises(
        self,
        pm4py_integration: PM4PyIntegration,
    ) -> None:
        """Test that discovery with empty traces raises ValueError."""
        with pytest.raises(ValueError, match="empty"):
            pm4py_integration.discover_petri_net([])


# =============================================================================
# Conformance Tests
# =============================================================================


class TestConformanceChecking:
    """Test conformance checking methods."""

    @pytest.mark.skipif(
        not PM4PyIntegration().is_available,
        reason="PM4Py not installed",
    )
    def test_token_replay_conformance(
        self,
        pm4py_integration: PM4PyIntegration,
        sample_traces: List[ExecutionTrace],
    ) -> None:
        """Test token-based replay conformance checking."""
        # First discover model
        petri_net = pm4py_integration.discover_petri_net(sample_traces)

        # Then check conformance
        result = pm4py_integration.check_conformance_token_replay(
            sample_traces,
            petri_net,
        )

        assert isinstance(result, ConformanceSummary)
        assert result.total_traces == len(sample_traces)
        assert 0.0 <= result.average_fitness <= 1.0
        assert result.method == "token_replay"

    @pytest.mark.skipif(
        not PM4PyIntegration().is_available,
        reason="PM4Py not installed",
    )
    def test_alignment_conformance(
        self,
        pm4py_integration: PM4PyIntegration,
        sample_traces: List[ExecutionTrace],
    ) -> None:
        """Test alignment-based conformance checking."""
        # First discover model
        petri_net = pm4py_integration.discover_petri_net(sample_traces)

        # Then check conformance
        result = pm4py_integration.check_conformance_alignments(
            sample_traces,
            petri_net,
        )

        assert isinstance(result, ConformanceSummary)
        assert result.total_traces == len(sample_traces)
        assert 0.0 <= result.average_fitness <= 1.0
        assert result.method == "alignments"

    @pytest.mark.skipif(
        not PM4PyIntegration().is_available,
        reason="PM4Py not installed",
    )
    def test_conformance_with_variants(
        self,
        pm4py_integration: PM4PyIntegration,
        variant_traces: List[ExecutionTrace],
    ) -> None:
        """Test conformance with multiple process variants."""
        petri_net = pm4py_integration.discover_petri_net(variant_traces)

        result = pm4py_integration.check_conformance_token_replay(
            variant_traces,
            petri_net,
        )

        # Should have high conformance since model discovered from same traces
        assert result.average_fitness >= 0.5
        assert result.total_traces == len(variant_traces)


# =============================================================================
# Result Data Class Tests
# =============================================================================


class TestResultDataClasses:
    """Test result data class functionality."""

    def test_petri_net_result_to_dict(self) -> None:
        """Test PetriNetResult.to_dict()."""
        result = PetriNetResult(
            net=None,
            initial_marking=None,
            final_marking=None,
            places=["p1", "p2"],
            transitions=["t1", "t2"],
            arcs=[("p1", "t1"), ("t1", "p2")],
            algorithm="inductive",
            discovery_time_ms=100,
        )

        d = result.to_dict()

        assert d["places"] == ["p1", "p2"]
        assert d["transitions"] == ["t1", "t2"]
        assert d["algorithm"] == "inductive"
        assert "net" not in d  # PM4Py object excluded

    def test_bpmn_result_to_dict(self) -> None:
        """Test BPMNResult.to_dict()."""
        result = BPMNResult(
            model=None,
            nodes=[{"id": "1", "name": "Start", "type": "StartEvent"}],
            flows=[{"source": "1", "target": "2"}],
            gateways=["XOR"],
            algorithm="inductive",
            discovery_time_ms=150,
        )

        d = result.to_dict()

        assert len(d["nodes"]) == 1
        assert len(d["flows"]) == 1
        assert "model" not in d

    def test_alignment_result_to_dict(self) -> None:
        """Test AlignmentResult.to_dict()."""
        result = AlignmentResult(
            trace_id="trace-001",
            fitness=0.95,
            aligned_traces=[{"alignment": [("A", "A")]}],
            deviations=[{"log_move": ">>", "model_move": "B"}],
            cost=1.0,
            is_conformant=True,
        )

        d = result.to_dict()

        assert d["trace_id"] == "trace-001"
        assert d["fitness"] == 0.95
        assert len(d["deviations"]) == 1

    def test_conformance_summary_rate(self) -> None:
        """Test ConformanceSummary.conformance_rate property."""
        summary = ConformanceSummary(
            total_traces=10,
            conformant_traces=8,
            average_fitness=0.9,
            method="token_replay",
        )

        assert summary.conformance_rate == 0.8

    def test_conformance_summary_rate_zero_traces(self) -> None:
        """Test conformance rate with zero traces."""
        summary = ConformanceSummary(
            total_traces=0,
            conformant_traces=0,
            average_fitness=0.0,
            method="token_replay",
        )

        assert summary.conformance_rate == 0.0


# =============================================================================
# Error Handling Tests
# =============================================================================


class TestErrorHandling:
    """Test error handling in PM4Py integration."""

    def test_pm4py_not_available_raises(self) -> None:
        """Test that operations raise when PM4Py not available."""
        integration = PM4PyIntegration()
        integration._available = False

        with pytest.raises(RuntimeError, match="PM4Py is not installed"):
            integration._ensure_pm4py()

    def test_discover_empty_list_raises(
        self,
        pm4py_integration: PM4PyIntegration,
    ) -> None:
        """Test that discovery raises on empty input."""
        with pytest.raises(ValueError):
            pm4py_integration.discover_petri_net([])

        with pytest.raises(ValueError):
            pm4py_integration.discover_bpmn([])

        with pytest.raises(ValueError):
            pm4py_integration.discover_dfg([])


# =============================================================================
# Enum Tests
# =============================================================================


class TestEnums:
    """Test enum definitions."""

    def test_discovery_algorithm_values(self) -> None:
        """Test DiscoveryAlgorithm enum values."""
        assert DiscoveryAlgorithm.ALPHA.value == "alpha"
        assert DiscoveryAlgorithm.INDUCTIVE.value == "inductive"
        assert DiscoveryAlgorithm.HEURISTIC.value == "heuristic"
        assert DiscoveryAlgorithm.DFG.value == "dfg"

    def test_conformance_method_values(self) -> None:
        """Test ConformanceMethod enum values."""
        assert ConformanceMethod.TOKEN_REPLAY.value == "token_replay"
        assert ConformanceMethod.ALIGNMENTS.value == "alignments"
