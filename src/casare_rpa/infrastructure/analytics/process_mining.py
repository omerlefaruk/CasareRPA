"""
CasareRPA - Process Mining Module

AI-powered process discovery from execution logs.
Discovers, monitors, and improves workflows by analyzing execution patterns.
"""

from __future__ import annotations

import hashlib
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from loguru import logger

# =============================================================================
# Data Models
# =============================================================================


class ActivityStatus(str, Enum):
    """Status of an activity execution."""

    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    TIMEOUT = "timeout"


class DeviationType(str, Enum):
    """Type of deviation from expected process."""

    MISSING_ACTIVITY = "missing_activity"
    UNEXPECTED_ACTIVITY = "unexpected_activity"
    WRONG_ORDER = "wrong_order"
    EXTRA_LOOP = "extra_loop"
    SKIPPED_BRANCH = "skipped_branch"


class InsightCategory(str, Enum):
    """Category of process insight."""

    BOTTLENECK = "bottleneck"
    PARALLELIZATION = "parallelization"
    SIMPLIFICATION = "simplification"
    ERROR_PATTERN = "error_pattern"
    VARIANT_ANALYSIS = "variant_analysis"


@dataclass
class Activity:
    """Single activity/node execution in a trace."""

    node_id: str
    node_type: str
    timestamp: datetime
    duration_ms: int
    status: ActivityStatus
    inputs: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "timestamp": self.timestamp.isoformat(),
            "duration_ms": self.duration_ms,
            "status": self.status.value,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "error_message": self.error_message,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Activity:
        """Create from dictionary."""
        return cls(
            node_id=data["node_id"],
            node_type=data["node_type"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            duration_ms=data["duration_ms"],
            status=ActivityStatus(data["status"]),
            inputs=data.get("inputs", {}),
            outputs=data.get("outputs", {}),
            error_message=data.get("error_message"),
        )


@dataclass
class ExecutionTrace:
    """Complete execution trace for a workflow run."""

    case_id: str
    workflow_id: str
    workflow_name: str
    activities: list[Activity]
    start_time: datetime
    end_time: datetime | None = None
    status: str = "running"
    robot_id: str | None = None

    @property
    def variant(self) -> str:
        """Get variant hash based on activity sequence."""
        sequence = "->".join(a.node_id for a in self.activities)
        return hashlib.md5(sequence.encode()).hexdigest()[:8]

    @property
    def total_duration_ms(self) -> int:
        """Calculate total duration."""
        if self.end_time and self.start_time:
            return int((self.end_time - self.start_time).total_seconds() * 1000)
        return sum(a.duration_ms for a in self.activities)

    @property
    def activity_sequence(self) -> list[str]:
        """Get ordered list of node IDs."""
        return [a.node_id for a in self.activities]

    @property
    def success_rate(self) -> float:
        """Calculate success rate of activities."""
        if not self.activities:
            return 0.0
        completed = sum(1 for a in self.activities if a.status == ActivityStatus.COMPLETED)
        return completed / len(self.activities)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "case_id": self.case_id,
            "workflow_id": self.workflow_id,
            "workflow_name": self.workflow_name,
            "activities": [a.to_dict() for a in self.activities],
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "status": self.status,
            "robot_id": self.robot_id,
            "variant": self.variant,
            "total_duration_ms": self.total_duration_ms,
        }


@dataclass
class DirectFollowsEdge:
    """Edge in Direct-Follows Graph."""

    source: str
    target: str
    frequency: int = 0
    avg_duration_ms: float = 0.0
    error_rate: float = 0.0


@dataclass
class ProcessModel:
    """Discovered process model from execution logs."""

    workflow_id: str
    nodes: set[str] = field(default_factory=set)
    node_types: dict[str, str] = field(default_factory=dict)
    edges: dict[str, dict[str, DirectFollowsEdge]] = field(default_factory=dict)
    variants: dict[str, int] = field(default_factory=dict)
    variant_paths: dict[str, list[str]] = field(default_factory=dict)
    entry_nodes: set[str] = field(default_factory=set)
    exit_nodes: set[str] = field(default_factory=set)
    loop_nodes: set[str] = field(default_factory=set)
    parallel_pairs: list[tuple[str, str]] = field(default_factory=list)
    trace_count: int = 0

    def get_edge_frequency(self, source: str, target: str) -> int:
        """Get frequency of edge transition."""
        if source in self.edges and target in self.edges[source]:
            return self.edges[source][target].frequency
        return 0

    def get_most_common_path(self) -> list[str]:
        """Get the most frequently executed path.

        Returns:
            Ordered list of node IDs representing the most common execution path.
            Returns empty list if no variants have been recorded.
        """
        if not self.variants:
            return []

        # Find the variant hash with highest count
        most_common_hash = max(self.variants.keys(), key=lambda h: self.variants[h])

        # Return the actual path for that variant
        if most_common_hash in self.variant_paths:
            return self.variant_paths[most_common_hash]

        # Fallback: reconstruct path from edges using frequency-based traversal
        return self._reconstruct_path_from_edges()

    def _reconstruct_path_from_edges(self) -> list[str]:
        """Reconstruct most likely path by following highest-frequency edges.

        Returns:
            Ordered list of node IDs representing the reconstructed path.
        """
        if not self.entry_nodes:
            return []

        # Start from entry node with highest outgoing frequency
        current = self._select_best_entry_node()
        if current is None:
            return []

        path = [current]
        visited = {current}
        max_steps = len(self.nodes) + 5  # Prevent infinite loops

        while len(path) < max_steps:
            # Get outgoing edges from current node
            if current not in self.edges:
                break

            # Select next node with highest frequency
            next_node = self._select_next_node(current, visited)
            if next_node is None:
                break

            path.append(next_node)
            visited.add(next_node)
            current = next_node

            # Stop if we reached an exit node
            if current in self.exit_nodes:
                break

        return path

    def _select_best_entry_node(self) -> str | None:
        """Select entry node with highest total outgoing frequency."""
        best_entry: str | None = None
        best_freq = -1

        for entry in self.entry_nodes:
            total_freq = sum(edge.frequency for edge in self.edges.get(entry, {}).values())
            if total_freq > best_freq:
                best_freq = total_freq
                best_entry = entry

        return best_entry

    def _select_next_node(self, current: str, visited: set[str]) -> str | None:
        """Select next node with highest frequency, preferring unvisited nodes.

        Args:
            current: Current node ID.
            visited: Set of already visited node IDs.

        Returns:
            Next node ID or None if no valid transition exists.
        """
        if current not in self.edges:
            return None

        candidates = self.edges[current]
        if not candidates:
            return None

        # Prefer unvisited nodes, then highest frequency
        unvisited = [(n, e) for n, e in candidates.items() if n not in visited]
        if unvisited:
            return max(unvisited, key=lambda x: x[1].frequency)[0]

        # All visited - check if we should allow revisit (loops)
        if current in self.loop_nodes:
            return max(candidates.items(), key=lambda x: x[1].frequency)[0]

        return None

    def get_variant_path(self, variant_hash: str) -> list[str]:
        """Get the actual path for a specific variant hash.

        Args:
            variant_hash: The variant hash to look up.

        Returns:
            Ordered list of node IDs for the variant, or empty list if not found.
        """
        return self.variant_paths.get(variant_hash, [])

    def get_all_variant_paths(self) -> dict[str, tuple[list[str], int]]:
        """Get all variants with their paths and counts.

        Returns:
            Dictionary mapping variant hash to (path, count) tuples.
        """
        result: dict[str, tuple[list[str], int]] = {}
        for variant_hash, count in self.variants.items():
            path = self.variant_paths.get(variant_hash, [])
            result[variant_hash] = (path, count)
        return result

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        edges_dict = {}
        for source, targets in self.edges.items():
            edges_dict[source] = {}
            for target, edge in targets.items():
                edges_dict[source][target] = {
                    "frequency": edge.frequency,
                    "avg_duration_ms": edge.avg_duration_ms,
                    "error_rate": edge.error_rate,
                }

        return {
            "workflow_id": self.workflow_id,
            "nodes": list(self.nodes),
            "node_types": self.node_types,
            "edges": edges_dict,
            "variants": self.variants,
            "variant_paths": self.variant_paths,
            "entry_nodes": list(self.entry_nodes),
            "exit_nodes": list(self.exit_nodes),
            "loop_nodes": list(self.loop_nodes),
            "parallel_pairs": self.parallel_pairs,
            "trace_count": self.trace_count,
        }

    def to_mermaid(self) -> str:
        """Export as Mermaid diagram."""
        lines = ["graph LR"]

        # Add nodes
        for node in self.nodes:
            node_type = self.node_types.get(node, "unknown")
            label = f"{node}[{node_type}]"
            if node in self.entry_nodes:
                label = f"{node}(({node_type}))"
            elif node in self.exit_nodes:
                label = f"{node}[/{node_type}/]"
            lines.append(f"    {label}")

        # Add edges with frequencies
        for source, targets in self.edges.items():
            for target, edge in targets.items():
                if edge.frequency > 0:
                    lines.append(f"    {source} -->|{edge.frequency}| {target}")

        return "\n".join(lines)


@dataclass
class Deviation:
    """Deviation from expected process."""

    deviation_type: DeviationType
    location: str
    expected: str | None = None
    actual: str | None = None
    severity: str = "medium"
    description: str = ""


@dataclass
class ConformanceReport:
    """Report on conformance between execution and model."""

    trace_id: str
    workflow_id: str
    fitness_score: float  # 0.0 - 1.0, how well trace fits model
    precision_score: float  # 0.0 - 1.0, how much of model was used
    deviations: list[Deviation] = field(default_factory=list)
    missing_activities: list[str] = field(default_factory=list)
    unexpected_activities: list[str] = field(default_factory=list)
    is_conformant: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "trace_id": self.trace_id,
            "workflow_id": self.workflow_id,
            "fitness_score": self.fitness_score,
            "precision_score": self.precision_score,
            "deviations": [
                {
                    "type": d.deviation_type.value,
                    "location": d.location,
                    "expected": d.expected,
                    "actual": d.actual,
                    "severity": d.severity,
                    "description": d.description,
                }
                for d in self.deviations
            ],
            "missing_activities": self.missing_activities,
            "unexpected_activities": self.unexpected_activities,
            "is_conformant": self.is_conformant,
        }


@dataclass
class ProcessInsight:
    """Actionable insight from process analysis."""

    category: InsightCategory
    title: str
    description: str
    impact: str  # high, medium, low
    affected_nodes: list[str] = field(default_factory=list)
    recommendation: str = ""
    metrics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "category": self.category.value,
            "title": self.title,
            "description": self.description,
            "impact": self.impact,
            "affected_nodes": self.affected_nodes,
            "recommendation": self.recommendation,
            "metrics": self.metrics,
        }


# =============================================================================
# Process Event Log - Storage for Execution Traces
# =============================================================================


class ProcessEventLog:
    """
    Storage and retrieval of execution traces for process mining.

    Supports hybrid storage mode:
    - In-memory: Fast access to recent traces (configurable limit)
    - Database: Persistent storage for older traces (via TraceRepository)

    When persistence is enabled, traces are automatically archived to the
    database when evicted from memory, and can be retrieved from database
    when not found in memory.
    """

    def __init__(
        self,
        max_traces: int = 10000,
        enable_persistence: bool = False,
        retention_days: int = 90,
    ) -> None:
        """Initialize event log.

        Args:
            max_traces: Maximum number of traces to store in memory.
            enable_persistence: Enable database persistence for traces.
            retention_days: Days to retain traces in database.
        """
        self._traces: dict[str, ExecutionTrace] = {}
        self._workflow_traces: dict[str, list[str]] = defaultdict(list)
        self._max_traces = max_traces
        self._enable_persistence = enable_persistence
        self._retention_days = retention_days
        self._repository: Any | None = None
        self._pending_archive: list[ExecutionTrace] = []
        self._archive_batch_size = 50
        logger.debug(
            f"ProcessEventLog initialized (max_traces={max_traces}, "
            f"persistence={enable_persistence})"
        )

    async def initialize_persistence(self) -> None:
        """
        Initialize database persistence.

        Must be called before using persistence features.
        Creates tables if they don't exist.
        """
        if not self._enable_persistence:
            return

        try:
            from casare_rpa.infrastructure.persistence.repositories.trace_repository import (
                TraceRepository,
            )

            self._repository = TraceRepository()
            await self._repository.ensure_tables()
            logger.info("ProcessEventLog persistence initialized")
        except Exception as e:
            logger.error(f"Failed to initialize persistence: {e}")
            self._enable_persistence = False
            raise

    def add_trace(self, trace: ExecutionTrace) -> None:
        """Add execution trace to log."""
        # Evict oldest if at capacity
        if len(self._traces) >= self._max_traces:
            oldest_key = next(iter(self._traces))
            old_trace = self._traces.pop(oldest_key)
            if old_trace.workflow_id in self._workflow_traces:
                wf_traces = self._workflow_traces[old_trace.workflow_id]
                if oldest_key in wf_traces:
                    wf_traces.remove(oldest_key)

            # Queue for archival if persistence is enabled
            if self._enable_persistence:
                self._pending_archive.append(old_trace)

        self._traces[trace.case_id] = trace
        self._workflow_traces[trace.workflow_id].append(trace.case_id)
        logger.debug(f"Added trace {trace.case_id} for workflow {trace.workflow_id}")

    async def add_trace_async(self, trace: ExecutionTrace) -> None:
        """
        Add execution trace with immediate persistence.

        Args:
            trace: ExecutionTrace to add.
        """
        self.add_trace(trace)

        if self._enable_persistence and self._repository:
            try:
                await self._repository.save_trace(trace)
            except Exception as e:
                logger.error(f"Failed to persist trace {trace.case_id}: {e}")

    async def flush_archive(self) -> int:
        """
        Flush pending traces to database.

        Returns:
            Number of traces archived.
        """
        if not self._enable_persistence or not self._repository:
            return 0

        if not self._pending_archive:
            return 0

        try:
            count = await self._repository.save_traces_batch(self._pending_archive)
            self._pending_archive.clear()
            logger.debug(f"Flushed {count} traces to archive")
            return count
        except Exception as e:
            logger.error(f"Failed to flush trace archive: {e}")
            return 0

    def get_trace(self, case_id: str) -> ExecutionTrace | None:
        """Get trace by case ID from memory."""
        return self._traces.get(case_id)

    async def get_trace_async(self, case_id: str) -> ExecutionTrace | None:
        """
        Get trace by case ID, checking database if not in memory.

        Args:
            case_id: Trace ID to retrieve.

        Returns:
            ExecutionTrace if found, None otherwise.
        """
        # Check memory first
        trace = self._traces.get(case_id)
        if trace:
            return trace

        # Check database if persistence enabled
        if self._enable_persistence and self._repository:
            try:
                return await self._repository.get_trace(case_id)
            except Exception as e:
                logger.error(f"Failed to get trace {case_id} from database: {e}")

        return None

    def get_traces_for_workflow(
        self,
        workflow_id: str,
        limit: int | None = None,
        status: str | None = None,
    ) -> list[ExecutionTrace]:
        """Get traces for a workflow from memory."""
        case_ids = self._workflow_traces.get(workflow_id, [])
        traces = [self._traces[cid] for cid in case_ids if cid in self._traces]

        if status:
            traces = [t for t in traces if t.status == status]

        if limit:
            traces = traces[-limit:]

        return traces

    async def get_traces_for_workflow_async(
        self,
        workflow_id: str,
        limit: int | None = None,
        status: str | None = None,
        include_archived: bool = True,
    ) -> list[ExecutionTrace]:
        """
        Get traces for a workflow, optionally including archived.

        Args:
            workflow_id: Workflow ID to filter by.
            limit: Maximum traces to return.
            status: Optional status filter.
            include_archived: Include traces from database.

        Returns:
            List of ExecutionTrace objects.
        """
        # Get from memory
        memory_traces = self.get_traces_for_workflow(workflow_id, limit, status)

        if not include_archived or not self._enable_persistence or not self._repository:
            return memory_traces

        # Get from database
        try:
            memory_ids = {t.case_id for t in memory_traces}
            db_traces = await self._repository.get_traces_for_workflow(
                workflow_id=workflow_id,
                limit=limit or 1000,
                status=status,
            )
            # Filter out duplicates
            db_traces = [t for t in db_traces if t.case_id not in memory_ids]

            # Combine and sort
            all_traces = memory_traces + db_traces
            all_traces.sort(key=lambda t: t.start_time, reverse=True)

            if limit:
                all_traces = all_traces[:limit]

            return all_traces

        except Exception as e:
            logger.error(f"Failed to get archived traces: {e}")
            return memory_traces

    def get_traces_in_timerange(
        self,
        start_time: datetime,
        end_time: datetime,
        workflow_id: str | None = None,
    ) -> list[ExecutionTrace]:
        """Get traces within time range from memory."""
        traces = []
        for trace in self._traces.values():
            if start_time <= trace.start_time <= end_time:
                if workflow_id is None or trace.workflow_id == workflow_id:
                    traces.append(trace)
        return sorted(traces, key=lambda t: t.start_time)

    async def get_traces_in_timerange_async(
        self,
        start_time: datetime,
        end_time: datetime,
        workflow_id: str | None = None,
        include_archived: bool = True,
    ) -> list[ExecutionTrace]:
        """
        Get traces within time range, optionally including archived.

        Args:
            start_time: Range start.
            end_time: Range end.
            workflow_id: Optional workflow filter.
            include_archived: Include traces from database.

        Returns:
            List of ExecutionTrace objects sorted by start_time.
        """
        memory_traces = self.get_traces_in_timerange(start_time, end_time, workflow_id)

        if not include_archived or not self._enable_persistence or not self._repository:
            return memory_traces

        try:
            memory_ids = {t.case_id for t in memory_traces}
            db_traces = await self._repository.get_traces(
                workflow_id=workflow_id,
                start_date=start_time,
                end_date=end_time,
            )
            db_traces = [t for t in db_traces if t.case_id not in memory_ids]

            all_traces = memory_traces + db_traces
            return sorted(all_traces, key=lambda t: t.start_time)

        except Exception as e:
            logger.error(f"Failed to get archived traces in timerange: {e}")
            return memory_traces

    def get_all_workflows(self) -> list[str]:
        """Get list of all workflow IDs with traces in memory."""
        return list(self._workflow_traces.keys())

    async def get_all_workflows_async(self) -> list[str]:
        """
        Get list of all workflow IDs including archived.

        Returns:
            List of unique workflow IDs.
        """
        memory_workflows = set(self._workflow_traces.keys())

        if self._enable_persistence and self._repository:
            try:
                db_workflows = await self._repository.get_workflow_ids()
                return list(memory_workflows | set(db_workflows))
            except Exception as e:
                logger.error(f"Failed to get archived workflow IDs: {e}")

        return list(memory_workflows)

    def get_trace_count(self, workflow_id: str | None = None) -> int:
        """Get count of traces in memory."""
        if workflow_id:
            return len(self._workflow_traces.get(workflow_id, []))
        return len(self._traces)

    async def get_trace_count_async(
        self,
        workflow_id: str | None = None,
        include_archived: bool = True,
    ) -> int:
        """
        Get count of traces including archived.

        Args:
            workflow_id: Optional workflow filter.
            include_archived: Include database traces.

        Returns:
            Total trace count.
        """
        memory_count = self.get_trace_count(workflow_id)

        if not include_archived or not self._enable_persistence or not self._repository:
            return memory_count

        try:
            db_count = await self._repository.get_trace_count(workflow_id)
            return memory_count + db_count
        except Exception as e:
            logger.error(f"Failed to get archived trace count: {e}")
            return memory_count

    def clear(self, workflow_id: str | None = None) -> None:
        """Clear traces from memory."""
        if workflow_id:
            case_ids = self._workflow_traces.pop(workflow_id, [])
            for cid in case_ids:
                self._traces.pop(cid, None)
        else:
            self._traces.clear()
            self._workflow_traces.clear()

    async def cleanup_archived(self) -> dict[str, Any]:
        """
        Cleanup old archived traces based on retention policy.

        Returns:
            Cleanup results dictionary.
        """
        if not self._enable_persistence or not self._repository:
            return {"status": "persistence_disabled"}

        try:
            return await self._repository.cleanup_old_traces(self._retention_days)
        except Exception as e:
            logger.error(f"Failed to cleanup archived traces: {e}")
            return {"status": "error", "error": str(e)}

    @property
    def persistence_enabled(self) -> bool:
        """Check if persistence is enabled and initialized."""
        return self._enable_persistence and self._repository is not None

    @property
    def pending_archive_count(self) -> int:
        """Get count of traces pending archival."""
        return len(self._pending_archive)


# =============================================================================
# Process Discovery - Build Process Models from Logs
# =============================================================================


class ProcessDiscovery:
    """Discover process models from execution traces."""

    def __init__(self) -> None:
        """Initialize process discovery."""
        self._edge_durations: dict[str, dict[str, list[int]]] = defaultdict(
            lambda: defaultdict(list)
        )
        self._edge_errors: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    def discover(self, traces: list[ExecutionTrace]) -> ProcessModel:
        """Discover process model from traces.

        Uses Direct-Follows Graph (DFG) algorithm with enhancements.

        Args:
            traces: List of execution traces to analyze.

        Returns:
            Discovered process model.
        """
        if not traces:
            return ProcessModel(workflow_id="unknown")

        workflow_id = traces[0].workflow_id
        model = ProcessModel(workflow_id=workflow_id, trace_count=len(traces))

        # Reset tracking
        self._edge_durations = defaultdict(lambda: defaultdict(list))
        self._edge_errors = defaultdict(lambda: defaultdict(int))

        # Build DFG
        for trace in traces:
            self._process_trace(trace, model)

        # Calculate edge statistics
        self._calculate_edge_stats(model)

        # Detect loops
        model.loop_nodes = self._detect_loops(model)

        # Detect parallel activities
        model.parallel_pairs = self._detect_parallelism(traces, model)

        logger.info(
            f"Discovered model: {len(model.nodes)} nodes, "
            f"{len(model.variants)} variants, {len(model.loop_nodes)} loops"
        )

        return model

    def _process_trace(self, trace: ExecutionTrace, model: ProcessModel) -> None:
        """Process single trace to update model."""
        activities = trace.activities
        if not activities:
            return

        # Track variant with actual path
        variant = trace.variant
        model.variants[variant] = model.variants.get(variant, 0) + 1

        # Store the actual path for this variant (first occurrence wins)
        if variant not in model.variant_paths:
            model.variant_paths[variant] = trace.activity_sequence

        # Process activities
        prev_activity: Activity | None = None
        for i, activity in enumerate(activities):
            node_id = activity.node_id
            model.nodes.add(node_id)
            model.node_types[node_id] = activity.node_type

            # Entry node
            if i == 0:
                model.entry_nodes.add(node_id)

            # Exit node
            if i == len(activities) - 1:
                model.exit_nodes.add(node_id)

            # Build edge from previous activity
            if prev_activity:
                prev_id = prev_activity.node_id
                if prev_id not in model.edges:
                    model.edges[prev_id] = {}

                if node_id not in model.edges[prev_id]:
                    model.edges[prev_id][node_id] = DirectFollowsEdge(
                        source=prev_id, target=node_id
                    )

                model.edges[prev_id][node_id].frequency += 1

                # Track duration and errors
                self._edge_durations[prev_id][node_id].append(activity.duration_ms)
                if activity.status == ActivityStatus.FAILED:
                    self._edge_errors[prev_id][node_id] += 1

            prev_activity = activity

    def _calculate_edge_stats(self, model: ProcessModel) -> None:
        """Calculate average duration and error rate for edges."""
        for source, targets in model.edges.items():
            for target, edge in targets.items():
                durations = self._edge_durations[source][target]
                if durations:
                    edge.avg_duration_ms = sum(durations) / len(durations)

                errors = self._edge_errors[source][target]
                if edge.frequency > 0:
                    edge.error_rate = errors / edge.frequency

    def _detect_loops(self, model: ProcessModel) -> set[str]:
        """Detect nodes that are part of loops."""
        loop_nodes: set[str] = set()

        # Simple loop detection: node appears in edges to itself
        # or in a cycle of length 2
        for source, targets in model.edges.items():
            # Self-loop
            if source in targets:
                loop_nodes.add(source)

            # 2-node cycle
            for target in targets:
                if target in model.edges and source in model.edges[target]:
                    loop_nodes.add(source)
                    loop_nodes.add(target)

        return loop_nodes

    def _detect_parallelism(
        self, traces: list[ExecutionTrace], model: ProcessModel
    ) -> list[tuple[str, str]]:
        """Detect potentially parallel activities.

        Two activities are potentially parallel if:
        1. They both follow the same predecessor
        2. They have similar execution times
        3. No direct dependency between them
        """
        parallel_pairs: list[tuple[str, str]] = []

        # Find nodes with multiple successors (potential parallel split)
        for source, targets in model.edges.items():
            successors = list(targets.keys())
            if len(successors) >= 2:
                # Check pairs of successors
                for i, s1 in enumerate(successors):
                    for s2 in successors[i + 1 :]:
                        # Check if they're independent (not connected)
                        s1_to_s2 = s2 in model.edges.get(s1, {})
                        s2_to_s1 = s1 in model.edges.get(s2, {})

                        if not s1_to_s2 and not s2_to_s1:
                            parallel_pairs.append((s1, s2))

        return parallel_pairs

    def discover_variants(self, traces: list[ExecutionTrace]) -> dict[str, list[ExecutionTrace]]:
        """Group traces by their execution variant.

        Returns:
            Dictionary mapping variant hash to list of traces.
        """
        variants: dict[str, list[ExecutionTrace]] = defaultdict(list)
        for trace in traces:
            variants[trace.variant].append(trace)
        return dict(variants)


# =============================================================================
# Conformance Checker - Compare Actual vs Expected
# =============================================================================


class ConformanceChecker:
    """Check conformance between execution traces and process model."""

    def check_conformance(
        self,
        trace: ExecutionTrace,
        model: ProcessModel,
    ) -> ConformanceReport:
        """Check if trace conforms to process model.

        Args:
            trace: Execution trace to check.
            model: Expected process model.

        Returns:
            Conformance report with fitness score and deviations.
        """
        report = ConformanceReport(
            trace_id=trace.case_id,
            workflow_id=trace.workflow_id,
            fitness_score=1.0,
            precision_score=1.0,
        )

        if not trace.activities:
            report.fitness_score = 0.0
            report.is_conformant = False
            return report

        # Check activities against model
        trace_nodes = set(a.node_id for a in trace.activities)
        model_nodes = model.nodes

        # Find missing activities (in model but not in trace)
        report.missing_activities = list(model_nodes - trace_nodes)

        # Find unexpected activities (in trace but not in model)
        report.unexpected_activities = list(trace_nodes - model_nodes)

        # Check edge conformance
        deviations = []
        prev_activity: Activity | None = None

        for activity in trace.activities:
            node_id = activity.node_id

            if prev_activity:
                prev_id = prev_activity.node_id

                # Check if this transition exists in model
                if prev_id not in model.edges or node_id not in model.edges.get(prev_id, {}):
                    deviations.append(
                        Deviation(
                            deviation_type=DeviationType.WRONG_ORDER,
                            location=node_id,
                            expected=f"transition from {prev_id}",
                            actual=f"{prev_id} -> {node_id}",
                            severity="medium",
                            description=f"Unexpected transition from {prev_id} to {node_id}",
                        )
                    )

            # Check for unexpected activity
            if node_id not in model_nodes:
                deviations.append(
                    Deviation(
                        deviation_type=DeviationType.UNEXPECTED_ACTIVITY,
                        location=node_id,
                        actual=node_id,
                        severity="high",
                        description=f"Activity {node_id} not in expected model",
                    )
                )

            prev_activity = activity

        report.deviations = deviations

        # Calculate fitness score
        total_checks = len(trace.activities) + len(model_nodes)
        violations = len(deviations) + len(report.unexpected_activities)
        if total_checks > 0:
            report.fitness_score = max(0.0, 1.0 - (violations / total_checks))

        # Calculate precision score (how much of model was used)
        if model_nodes:
            report.precision_score = len(trace_nodes & model_nodes) / len(model_nodes)

        # Determine conformance
        report.is_conformant = (
            report.fitness_score >= 0.8
            and len(report.unexpected_activities) == 0
            and all(d.severity != "high" for d in deviations)
        )

        return report

    def batch_check(
        self,
        traces: list[ExecutionTrace],
        model: ProcessModel,
    ) -> dict[str, Any]:
        """Check conformance for multiple traces.

        Returns:
            Summary statistics and individual reports.
        """
        reports = [self.check_conformance(trace, model) for trace in traces]

        conformant_count = sum(1 for r in reports if r.is_conformant)
        avg_fitness = sum(r.fitness_score for r in reports) / len(reports) if reports else 0.0
        avg_precision = sum(r.precision_score for r in reports) / len(reports) if reports else 0.0

        # Aggregate deviations
        deviation_counts: dict[str, int] = defaultdict(int)
        for report in reports:
            for deviation in report.deviations:
                deviation_counts[deviation.deviation_type.value] += 1

        return {
            "total_traces": len(traces),
            "conformant_traces": conformant_count,
            "conformance_rate": conformant_count / len(traces) if traces else 0.0,
            "average_fitness": avg_fitness,
            "average_precision": avg_precision,
            "deviation_summary": dict(deviation_counts),
            "reports": [r.to_dict() for r in reports],
        }


# =============================================================================
# Process Enhancer - Optimization Suggestions
# =============================================================================


class ProcessEnhancer:
    """Analyze process models and suggest optimizations."""

    def __init__(self) -> None:
        """Initialize process enhancer."""
        self._slow_threshold_ms = 5000  # 5 seconds
        self._error_threshold = 0.1  # 10% error rate

    def analyze(
        self,
        model: ProcessModel,
        traces: list[ExecutionTrace],
    ) -> list[ProcessInsight]:
        """Analyze process and generate optimization insights.

        Args:
            model: Discovered process model.
            traces: Execution traces used to build model.

        Returns:
            List of actionable insights.
        """
        insights: list[ProcessInsight] = []

        # Analyze slow paths
        insights.extend(self._find_slow_paths(model, traces))

        # Analyze parallelization opportunities
        insights.extend(self._find_parallelization_opportunities(model))

        # Analyze error patterns
        insights.extend(self._find_error_patterns(model, traces))

        # Analyze variant simplification
        insights.extend(self._find_simplification_opportunities(model, traces))

        # Sort by impact
        impact_order = {"high": 0, "medium": 1, "low": 2}
        insights.sort(key=lambda x: impact_order.get(x.impact, 2))

        logger.info(f"Generated {len(insights)} process insights")
        return insights

    def _find_slow_paths(
        self,
        model: ProcessModel,
        traces: list[ExecutionTrace],
    ) -> list[ProcessInsight]:
        """Find slow execution paths."""
        insights: list[ProcessInsight] = []

        # Find slow edges
        for source, targets in model.edges.items():
            for target, edge in targets.items():
                if edge.avg_duration_ms > self._slow_threshold_ms:
                    insights.append(
                        ProcessInsight(
                            category=InsightCategory.BOTTLENECK,
                            title=f"Slow Transition: {source} -> {target}",
                            description=(
                                f"Transition from {source} to {target} "
                                f"takes {edge.avg_duration_ms:.0f}ms on average"
                            ),
                            impact="high" if edge.avg_duration_ms > 10000 else "medium",
                            affected_nodes=[source, target],
                            recommendation=(
                                f"Investigate why {target} takes so long after {source}. "
                                "Consider caching, parallel execution, or optimization."
                            ),
                            metrics={
                                "avg_duration_ms": edge.avg_duration_ms,
                                "frequency": edge.frequency,
                            },
                        )
                    )

        # Find slow nodes overall
        node_durations: dict[str, list[int]] = defaultdict(list)
        for trace in traces:
            for activity in trace.activities:
                node_durations[activity.node_id].append(activity.duration_ms)

        for node_id, durations in node_durations.items():
            avg_duration = sum(durations) / len(durations)
            if avg_duration > self._slow_threshold_ms:
                insights.append(
                    ProcessInsight(
                        category=InsightCategory.BOTTLENECK,
                        title=f"Slow Node: {node_id}",
                        description=(
                            f"Node {node_id} takes {avg_duration:.0f}ms on average "
                            f"across {len(durations)} executions"
                        ),
                        impact="high" if avg_duration > 10000 else "medium",
                        affected_nodes=[node_id],
                        recommendation=(
                            "Profile this node to identify bottlenecks. "
                            "Consider async operations or caching."
                        ),
                        metrics={
                            "avg_duration_ms": avg_duration,
                            "min_duration_ms": min(durations),
                            "max_duration_ms": max(durations),
                            "execution_count": len(durations),
                        },
                    )
                )

        return insights

    def _find_parallelization_opportunities(
        self,
        model: ProcessModel,
    ) -> list[ProcessInsight]:
        """Find opportunities for parallel execution."""
        insights: list[ProcessInsight] = []

        for node1, node2 in model.parallel_pairs:
            # Check if both nodes have significant duration
            edge_info_1 = None
            edge_info_2 = None

            for source, targets in model.edges.items():
                if node1 in targets:
                    edge_info_1 = targets[node1]
                if node2 in targets:
                    edge_info_2 = targets[node2]

            if edge_info_1 and edge_info_2:
                combined_time = edge_info_1.avg_duration_ms + edge_info_2.avg_duration_ms
                if combined_time > 2000:  # Only suggest if savings > 2s
                    insights.append(
                        ProcessInsight(
                            category=InsightCategory.PARALLELIZATION,
                            title=f"Parallel Opportunity: {node1} & {node2}",
                            description=(
                                f"Nodes {node1} and {node2} appear to be independent "
                                "and could run in parallel"
                            ),
                            impact="medium",
                            affected_nodes=[node1, node2],
                            recommendation=(
                                "Consider restructuring workflow to execute "
                                f"{node1} and {node2} in parallel for potential "
                                f"time savings of {combined_time/2:.0f}ms"
                            ),
                            metrics={
                                "potential_savings_ms": combined_time / 2,
                                "node1_duration_ms": edge_info_1.avg_duration_ms,
                                "node2_duration_ms": edge_info_2.avg_duration_ms,
                            },
                        )
                    )

        return insights

    def _find_error_patterns(
        self,
        model: ProcessModel,
        traces: list[ExecutionTrace],
    ) -> list[ProcessInsight]:
        """Find error-prone paths and patterns."""
        insights: list[ProcessInsight] = []

        # Node error rates
        node_errors: dict[str, int] = defaultdict(int)
        node_executions: dict[str, int] = defaultdict(int)

        for trace in traces:
            for activity in trace.activities:
                node_executions[activity.node_id] += 1
                if activity.status == ActivityStatus.FAILED:
                    node_errors[activity.node_id] += 1

        # Find high-error nodes
        for node_id, error_count in node_errors.items():
            total = node_executions[node_id]
            error_rate = error_count / total if total > 0 else 0

            if error_rate > self._error_threshold:
                insights.append(
                    ProcessInsight(
                        category=InsightCategory.ERROR_PATTERN,
                        title=f"High Error Rate: {node_id}",
                        description=(
                            f"Node {node_id} has {error_rate*100:.1f}% error rate "
                            f"({error_count}/{total} executions)"
                        ),
                        impact="high",
                        affected_nodes=[node_id],
                        recommendation=(
                            "Add error handling, retry logic, or investigate root cause. "
                            "Consider adding pre-condition checks."
                        ),
                        metrics={
                            "error_rate": error_rate,
                            "error_count": error_count,
                            "total_executions": total,
                        },
                    )
                )

        # Find error-prone edges
        for source, targets in model.edges.items():
            for target, edge in targets.items():
                if edge.error_rate > self._error_threshold and edge.frequency >= 5:
                    insights.append(
                        ProcessInsight(
                            category=InsightCategory.ERROR_PATTERN,
                            title=f"Error-Prone Transition: {source} -> {target}",
                            description=(
                                f"Transition {source} to {target} fails "
                                f"{edge.error_rate*100:.1f}% of the time"
                            ),
                            impact="medium",
                            affected_nodes=[source, target],
                            recommendation=(
                                f"Add validation before {target} or error recovery "
                                f"after {source}"
                            ),
                            metrics={
                                "error_rate": edge.error_rate,
                                "frequency": edge.frequency,
                            },
                        )
                    )

        return insights

    def _find_simplification_opportunities(
        self,
        model: ProcessModel,
        traces: list[ExecutionTrace],
    ) -> list[ProcessInsight]:
        """Find opportunities to simplify process."""
        insights: list[ProcessInsight] = []

        # Too many variants suggest overly complex process
        variant_count = len(model.variants)
        if variant_count > 10:
            # Find rare variants
            rare_variants = [(v, c) for v, c in model.variants.items() if c == 1]

            insights.append(
                ProcessInsight(
                    category=InsightCategory.SIMPLIFICATION,
                    title="High Process Variability",
                    description=(
                        f"Process has {variant_count} distinct variants, "
                        f"with {len(rare_variants)} occurring only once"
                    ),
                    impact="medium",
                    affected_nodes=[],
                    recommendation=(
                        "Review process for unnecessary complexity. "
                        "Consider standardizing common paths."
                    ),
                    metrics={
                        "total_variants": variant_count,
                        "rare_variants": len(rare_variants),
                        "trace_count": model.trace_count,
                    },
                )
            )

        # Nodes that are rarely executed
        node_counts: dict[str, int] = defaultdict(int)
        for trace in traces:
            for activity in trace.activities:
                node_counts[activity.node_id] += 1

        total_executions = len(traces)
        for node_id, count in node_counts.items():
            usage_rate = count / total_executions if total_executions > 0 else 0
            if usage_rate < 0.1 and count >= 2:  # Less than 10% usage
                insights.append(
                    ProcessInsight(
                        category=InsightCategory.SIMPLIFICATION,
                        title=f"Rarely Used Node: {node_id}",
                        description=(
                            f"Node {node_id} is only used in {usage_rate*100:.1f}% " "of executions"
                        ),
                        impact="low",
                        affected_nodes=[node_id],
                        recommendation=(
                            "Consider if this node is necessary or "
                            "could be moved to a separate workflow"
                        ),
                        metrics={
                            "usage_rate": usage_rate,
                            "execution_count": count,
                            "total_traces": total_executions,
                        },
                    )
                )

        return insights


# =============================================================================
# Main Process Miner - Orchestrates All Components
# =============================================================================


class ProcessMiner:
    """Main process mining engine combining all capabilities."""

    def __init__(self, max_traces: int = 10000) -> None:
        """Initialize process miner.

        Args:
            max_traces: Maximum traces to store in memory.
        """
        self.event_log = ProcessEventLog(max_traces=max_traces)
        self.discovery = ProcessDiscovery()
        self.conformance = ConformanceChecker()
        self.enhancer = ProcessEnhancer()
        self._models: dict[str, ProcessModel] = {}
        logger.info("ProcessMiner initialized")

    def record_trace(self, trace: ExecutionTrace) -> None:
        """Record execution trace for mining."""
        self.event_log.add_trace(trace)

    def record_activity(
        self,
        case_id: str,
        workflow_id: str,
        workflow_name: str,
        node_id: str,
        node_type: str,
        duration_ms: int,
        status: ActivityStatus,
        robot_id: str | None = None,
        inputs: dict[str, Any] | None = None,
        outputs: dict[str, Any] | None = None,
        error_message: str | None = None,
    ) -> None:
        """Record single activity to existing or new trace."""
        trace = self.event_log.get_trace(case_id)

        if trace is None:
            trace = ExecutionTrace(
                case_id=case_id,
                workflow_id=workflow_id,
                workflow_name=workflow_name,
                activities=[],
                start_time=datetime.now(),
                robot_id=robot_id,
            )
            self.event_log.add_trace(trace)

        activity = Activity(
            node_id=node_id,
            node_type=node_type,
            timestamp=datetime.now(),
            duration_ms=duration_ms,
            status=status,
            inputs=inputs or {},
            outputs=outputs or {},
            error_message=error_message,
        )
        trace.activities.append(activity)

    def complete_trace(self, case_id: str, status: str = "completed") -> None:
        """Mark trace as complete."""
        trace = self.event_log.get_trace(case_id)
        if trace:
            trace.end_time = datetime.now()
            trace.status = status

    def discover_process(
        self,
        workflow_id: str,
        min_traces: int = 10,
    ) -> ProcessModel | None:
        """Discover process model for workflow.

        Args:
            workflow_id: Workflow to analyze.
            min_traces: Minimum traces required for discovery.

        Returns:
            Discovered process model or None if insufficient data.
        """
        traces = self.event_log.get_traces_for_workflow(workflow_id)

        if len(traces) < min_traces:
            logger.warning(
                f"Insufficient traces for {workflow_id}: " f"{len(traces)} < {min_traces}"
            )
            return None

        model = self.discovery.discover(traces)
        self._models[workflow_id] = model
        return model

    def check_conformance(
        self,
        trace: ExecutionTrace,
        workflow_id: str | None = None,
    ) -> ConformanceReport | None:
        """Check trace conformance against discovered model."""
        wf_id = workflow_id or trace.workflow_id
        model = self._models.get(wf_id)

        if model is None:
            logger.warning(f"No model found for workflow {wf_id}")
            return None

        return self.conformance.check_conformance(trace, model)

    def get_insights(
        self,
        workflow_id: str,
    ) -> list[ProcessInsight]:
        """Get optimization insights for workflow."""
        model = self._models.get(workflow_id)
        if model is None:
            # Try to discover first
            model = self.discover_process(workflow_id, min_traces=5)
            if model is None:
                return []

        traces = self.event_log.get_traces_for_workflow(workflow_id)
        return self.enhancer.analyze(model, traces)

    def get_variants(
        self,
        workflow_id: str,
    ) -> dict[str, Any]:
        """Get variant analysis for workflow."""
        traces = self.event_log.get_traces_for_workflow(workflow_id)
        if not traces:
            return {"variants": [], "total_traces": 0}

        variant_groups = self.discovery.discover_variants(traces)

        variants = []
        for variant_hash, variant_traces in variant_groups.items():
            sample_trace = variant_traces[0]
            variants.append(
                {
                    "variant_id": variant_hash,
                    "count": len(variant_traces),
                    "percentage": len(variant_traces) / len(traces) * 100,
                    "avg_duration_ms": sum(t.total_duration_ms for t in variant_traces)
                    / len(variant_traces),
                    "success_rate": sum(t.success_rate for t in variant_traces)
                    / len(variant_traces),
                    "sample_path": sample_trace.activity_sequence,
                }
            )

        # Sort by frequency
        variants.sort(key=lambda x: x["count"], reverse=True)

        return {
            "workflow_id": workflow_id,
            "total_traces": len(traces),
            "variant_count": len(variants),
            "variants": variants,
        }

    def get_process_summary(self, workflow_id: str) -> dict[str, Any]:
        """Get comprehensive process summary."""
        traces = self.event_log.get_traces_for_workflow(workflow_id)
        model = self._models.get(workflow_id)

        if not traces:
            return {
                "workflow_id": workflow_id,
                "status": "no_data",
                "message": "No execution traces available",
            }

        # Basic stats
        total_duration = sum(t.total_duration_ms for t in traces)
        avg_duration = total_duration / len(traces)
        success_count = sum(1 for t in traces if t.status == "completed")

        summary = {
            "workflow_id": workflow_id,
            "trace_count": len(traces),
            "avg_duration_ms": avg_duration,
            "success_rate": success_count / len(traces),
            "has_model": model is not None,
        }

        if model:
            summary.update(
                {
                    "node_count": len(model.nodes),
                    "variant_count": len(model.variants),
                    "has_loops": len(model.loop_nodes) > 0,
                    "parallel_opportunities": len(model.parallel_pairs),
                    "model": model.to_dict(),
                }
            )

            # Add insights
            insights = self.get_insights(workflow_id)
            summary["insights"] = [i.to_dict() for i in insights[:5]]  # Top 5

        return summary


# =============================================================================
# Singleton Instance
# =============================================================================

_process_miner: ProcessMiner | None = None


def get_process_miner() -> ProcessMiner:
    """Get singleton ProcessMiner instance."""
    global _process_miner
    if _process_miner is None:
        _process_miner = ProcessMiner()
    return _process_miner
