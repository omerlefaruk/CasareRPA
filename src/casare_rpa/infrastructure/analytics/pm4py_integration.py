"""
CasareRPA - PM4Py Integration Module

Provides advanced process discovery and conformance checking capabilities
by integrating with the PM4Py library.

PM4Py Reference: https://pm4py.fit.fraunhofer.de/

Features:
- Multiple discovery algorithms (Alpha, Inductive, Heuristic Miner)
- BPMN model generation
- Token-based replay conformance checking
- Alignment-based conformance checking
- Process model visualization
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

from loguru import logger

from casare_rpa.infrastructure.analytics.process_mining import (
    ExecutionTrace,
)

# =============================================================================
# Discovery Algorithm Enum
# =============================================================================


class DiscoveryAlgorithm(str, Enum):
    """Available process discovery algorithms."""

    ALPHA = "alpha"  # Alpha Miner - Simple, educational
    ALPHA_PLUS = "alpha_plus"  # Alpha+ with handling for loops
    INDUCTIVE = "inductive"  # Inductive Miner - Robust, recommended
    INDUCTIVE_INFREQUENT = "inductive_infrequent"  # Handles noise
    HEURISTIC = "heuristic"  # Heuristic Miner - Noise tolerant
    DFG = "dfg"  # Direct-Follows Graph


class ConformanceMethod(str, Enum):
    """Available conformance checking methods."""

    TOKEN_REPLAY = "token_replay"
    ALIGNMENTS = "alignments"


# =============================================================================
# Result Data Classes
# =============================================================================


@dataclass
class PetriNetResult:
    """Result of Petri net discovery."""

    net: Any  # pm4py PetriNet object
    initial_marking: Any  # pm4py Marking object
    final_marking: Any  # pm4py Marking object
    places: list[str] = field(default_factory=list)
    transitions: list[str] = field(default_factory=list)
    arcs: list[tuple[str, str]] = field(default_factory=list)
    algorithm: str = ""
    discovery_time_ms: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary (excluding pm4py objects)."""
        return {
            "places": self.places,
            "transitions": self.transitions,
            "arcs": self.arcs,
            "algorithm": self.algorithm,
            "discovery_time_ms": self.discovery_time_ms,
        }


@dataclass
class BPMNResult:
    """Result of BPMN model discovery."""

    model: Any  # pm4py BPMN object
    nodes: list[dict[str, str]] = field(default_factory=list)
    flows: list[dict[str, str]] = field(default_factory=list)
    gateways: list[str] = field(default_factory=list)
    algorithm: str = ""
    discovery_time_ms: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary (excluding pm4py objects)."""
        return {
            "nodes": self.nodes,
            "flows": self.flows,
            "gateways": self.gateways,
            "algorithm": self.algorithm,
            "discovery_time_ms": self.discovery_time_ms,
        }


@dataclass
class AlignmentResult:
    """Result of alignment-based conformance checking."""

    trace_id: str
    fitness: float  # 0.0 - 1.0
    aligned_traces: list[dict[str, Any]] = field(default_factory=list)
    deviations: list[dict[str, str]] = field(default_factory=list)
    cost: float = 0.0
    is_conformant: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "trace_id": self.trace_id,
            "fitness": self.fitness,
            "aligned_traces": self.aligned_traces,
            "deviations": self.deviations,
            "cost": self.cost,
            "is_conformant": self.is_conformant,
        }


@dataclass
class TokenReplayResult:
    """Result of token-based replay conformance checking."""

    trace_id: str
    fitness: float  # 0.0 - 1.0
    produced_tokens: int = 0
    consumed_tokens: int = 0
    missing_tokens: int = 0
    remaining_tokens: int = 0
    is_conformant: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "trace_id": self.trace_id,
            "fitness": self.fitness,
            "produced_tokens": self.produced_tokens,
            "consumed_tokens": self.consumed_tokens,
            "missing_tokens": self.missing_tokens,
            "remaining_tokens": self.remaining_tokens,
            "is_conformant": self.is_conformant,
        }


@dataclass
class ConformanceSummary:
    """Summary of conformance checking results."""

    total_traces: int
    conformant_traces: int
    average_fitness: float
    precision: float = 0.0
    generalization: float = 0.0
    simplicity: float = 0.0
    method: str = ""
    individual_results: list[AlignmentResult | TokenReplayResult] = field(default_factory=list)

    @property
    def conformance_rate(self) -> float:
        """Calculate conformance rate."""
        if self.total_traces == 0:
            return 0.0
        return self.conformant_traces / self.total_traces

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_traces": self.total_traces,
            "conformant_traces": self.conformant_traces,
            "conformance_rate": self.conformance_rate,
            "average_fitness": self.average_fitness,
            "precision": self.precision,
            "generalization": self.generalization,
            "simplicity": self.simplicity,
            "method": self.method,
        }


# =============================================================================
# PM4Py Integration Class
# =============================================================================


class PM4PyIntegration:
    """
    Integration layer for PM4Py process mining library.

    Provides lazy loading of pm4py to avoid import overhead when
    process mining features are not used.

    Usage:
        integration = PM4PyIntegration()
        petri_net = integration.discover_petri_net(traces)
        conformance = integration.check_conformance(traces, petri_net)
    """

    def __init__(self) -> None:
        """Initialize PM4Py integration with lazy loading."""
        self._pm4py: Any | None = None
        self._pandas: Any | None = None
        self._available: bool | None = None

    @property
    def is_available(self) -> bool:
        """Check if PM4Py is available."""
        if self._available is None:
            try:
                import pm4py

                self._pm4py = pm4py
                self._available = True
                logger.debug(f"PM4Py version {pm4py.__version__} available")
            except ImportError:
                self._available = False
                logger.warning("PM4Py not installed. Install with: pip install pm4py>=2.7.0")
        return self._available

    def _ensure_pm4py(self) -> Any:
        """Ensure PM4Py is available and return module."""
        if not self.is_available:
            raise RuntimeError("PM4Py is not installed. Install with: pip install pm4py>=2.7.0")
        return self._pm4py

    def _get_pandas(self) -> Any:
        """Get pandas module (required by PM4Py)."""
        if self._pandas is None:
            import pandas as pd

            self._pandas = pd
        return self._pandas

    # =========================================================================
    # Conversion Methods
    # =========================================================================

    def traces_to_dataframe(self, traces: list[ExecutionTrace]) -> Any:
        """
        Convert CasareRPA traces to PM4Py-compatible DataFrame.

        Args:
            traces: List of ExecutionTrace objects.

        Returns:
            pandas DataFrame in PM4Py event log format.
        """
        pd = self._get_pandas()

        events = []
        for trace in traces:
            for activity in trace.activities:
                events.append(
                    {
                        "case:concept:name": trace.case_id,
                        "concept:name": activity.node_type,
                        "time:timestamp": activity.timestamp,
                        "org:resource": trace.robot_id or "default",
                        "lifecycle:transition": "complete",
                        "casare:node_id": activity.node_id,
                        "casare:duration_ms": activity.duration_ms,
                        "casare:status": activity.status.value,
                        "casare:workflow_id": trace.workflow_id,
                    }
                )

        df = pd.DataFrame(events)

        # Ensure timestamp is datetime
        df["time:timestamp"] = pd.to_datetime(df["time:timestamp"])

        return df

    def traces_to_event_log(self, traces: list[ExecutionTrace]) -> Any:
        """
        Convert CasareRPA traces to PM4Py EventLog object.

        Args:
            traces: List of ExecutionTrace objects.

        Returns:
            pm4py EventLog object.
        """
        pm4py = self._ensure_pm4py()
        df = self.traces_to_dataframe(traces)
        return pm4py.convert_to_event_log(df)

    # =========================================================================
    # Discovery Methods
    # =========================================================================

    def discover_petri_net(
        self,
        traces: list[ExecutionTrace],
        algorithm: DiscoveryAlgorithm = DiscoveryAlgorithm.INDUCTIVE,
        noise_threshold: float = 0.0,
    ) -> PetriNetResult:
        """
        Discover Petri net model from execution traces.

        Args:
            traces: List of ExecutionTrace objects.
            algorithm: Discovery algorithm to use.
            noise_threshold: Noise filtering threshold (0.0 - 1.0).

        Returns:
            PetriNetResult with discovered model.

        Raises:
            RuntimeError: If PM4Py is not available.
            ValueError: If traces list is empty.
        """
        if not traces:
            raise ValueError("Cannot discover model from empty trace list")

        pm4py = self._ensure_pm4py()
        start_time = datetime.now()

        log = self.traces_to_event_log(traces)

        try:
            if algorithm == DiscoveryAlgorithm.ALPHA:
                net, im, fm = pm4py.discover_petri_net_alpha(log)
            elif algorithm == DiscoveryAlgorithm.ALPHA_PLUS:
                net, im, fm = pm4py.discover_petri_net_alpha_plus(log)
            elif algorithm == DiscoveryAlgorithm.INDUCTIVE:
                net, im, fm = pm4py.discover_petri_net_inductive(
                    log, noise_threshold=noise_threshold
                )
            elif algorithm == DiscoveryAlgorithm.INDUCTIVE_INFREQUENT:
                net, im, fm = pm4py.discover_petri_net_inductive(
                    log, noise_threshold=max(noise_threshold, 0.2)
                )
            elif algorithm == DiscoveryAlgorithm.HEURISTIC:
                net, im, fm = pm4py.discover_petri_net_heuristics(log)
            else:
                # Default to inductive
                net, im, fm = pm4py.discover_petri_net_inductive(log)

            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            # Extract model structure
            places = [p.name for p in net.places]
            transitions = [t.name or t.label or "tau" for t in net.transitions]
            arcs = [
                (a.source.name or str(a.source), a.target.name or str(a.target)) for a in net.arcs
            ]

            logger.info(
                f"Discovered Petri net using {algorithm.value}: "
                f"{len(places)} places, {len(transitions)} transitions"
            )

            return PetriNetResult(
                net=net,
                initial_marking=im,
                final_marking=fm,
                places=places,
                transitions=transitions,
                arcs=arcs,
                algorithm=algorithm.value,
                discovery_time_ms=duration_ms,
            )

        except Exception as e:
            logger.error(f"Petri net discovery failed: {e}")
            raise

    def discover_bpmn(
        self,
        traces: list[ExecutionTrace],
        algorithm: DiscoveryAlgorithm = DiscoveryAlgorithm.INDUCTIVE,
    ) -> BPMNResult:
        """
        Discover BPMN model from execution traces.

        Args:
            traces: List of ExecutionTrace objects.
            algorithm: Discovery algorithm to use.

        Returns:
            BPMNResult with discovered BPMN model.

        Raises:
            RuntimeError: If PM4Py is not available.
            ValueError: If traces list is empty.
        """
        if not traces:
            raise ValueError("Cannot discover model from empty trace list")

        pm4py = self._ensure_pm4py()
        start_time = datetime.now()

        log = self.traces_to_event_log(traces)

        try:
            # Discover BPMN directly or convert from Petri net
            if hasattr(pm4py, "discover_bpmn_inductive"):
                bpmn_model = pm4py.discover_bpmn_inductive(log)
            else:
                # Discover Petri net first, then convert
                net, im, fm = pm4py.discover_petri_net_inductive(log)
                from pm4py.objects.conversion.wf_net import (
                    converter as wf_net_converter,
                )

                bpmn_model = wf_net_converter.apply(net, im, fm)

            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            # Extract BPMN structure
            nodes = []
            flows = []
            gateways = []

            if hasattr(bpmn_model, "get_nodes"):
                for node in bpmn_model.get_nodes():
                    node_type = type(node).__name__
                    node_info = {
                        "id": str(node.get_id()) if hasattr(node, "get_id") else str(id(node)),
                        "name": str(node.get_name()) if hasattr(node, "get_name") else str(node),
                        "type": node_type,
                    }
                    nodes.append(node_info)
                    if "Gateway" in node_type:
                        gateways.append(node_info["name"])

            if hasattr(bpmn_model, "get_flows"):
                for flow in bpmn_model.get_flows():
                    flow_info = {
                        "source": str(flow.get_source()) if hasattr(flow, "get_source") else "?",
                        "target": str(flow.get_target()) if hasattr(flow, "get_target") else "?",
                    }
                    flows.append(flow_info)

            logger.info(f"Discovered BPMN model: {len(nodes)} nodes, {len(flows)} flows")

            return BPMNResult(
                model=bpmn_model,
                nodes=nodes,
                flows=flows,
                gateways=gateways,
                algorithm=algorithm.value,
                discovery_time_ms=duration_ms,
            )

        except Exception as e:
            logger.error(f"BPMN discovery failed: {e}")
            raise

    def discover_dfg(self, traces: list[ExecutionTrace]) -> dict[str, Any]:
        """
        Discover Direct-Follows Graph from traces.

        Args:
            traces: List of ExecutionTrace objects.

        Returns:
            Dictionary with DFG structure and statistics.
        """
        if not traces:
            raise ValueError("Cannot discover DFG from empty trace list")

        pm4py = self._ensure_pm4py()
        log = self.traces_to_event_log(traces)

        try:
            dfg, start_activities, end_activities = pm4py.discover_dfg(log)

            return {
                "edges": [{"source": k[0], "target": k[1], "frequency": v} for k, v in dfg.items()],
                "start_activities": dict(start_activities),
                "end_activities": dict(end_activities),
                "node_count": len(set(k[0] for k in dfg.keys()) | set(k[1] for k in dfg.keys())),
                "edge_count": len(dfg),
            }

        except Exception as e:
            logger.error(f"DFG discovery failed: {e}")
            raise

    # =========================================================================
    # Conformance Checking Methods
    # =========================================================================

    def check_conformance_token_replay(
        self,
        traces: list[ExecutionTrace],
        petri_net_result: PetriNetResult,
    ) -> ConformanceSummary:
        """
        Check conformance using token-based replay.

        Args:
            traces: List of ExecutionTrace objects.
            petri_net_result: Previously discovered Petri net.

        Returns:
            ConformanceSummary with individual trace results.
        """
        pm4py = self._ensure_pm4py()
        log = self.traces_to_event_log(traces)

        try:
            replayed_traces = pm4py.conformance_diagnostics_token_based_replay(
                log,
                petri_net_result.net,
                petri_net_result.initial_marking,
                petri_net_result.final_marking,
            )

            results = []
            total_fitness = 0.0
            conformant_count = 0

            for i, result in enumerate(replayed_traces):
                trace_id = traces[i].case_id if i < len(traces) else f"trace_{i}"
                fitness = result.get("trace_fitness", 0.0)
                is_fit = result.get("trace_is_fit", False)

                token_result = TokenReplayResult(
                    trace_id=trace_id,
                    fitness=fitness,
                    produced_tokens=result.get("produced_tokens", 0),
                    consumed_tokens=result.get("consumed_tokens", 0),
                    missing_tokens=result.get("missing_tokens", 0),
                    remaining_tokens=result.get("remaining_tokens", 0),
                    is_conformant=is_fit,
                )
                results.append(token_result)
                total_fitness += fitness
                if is_fit:
                    conformant_count += 1

            avg_fitness = total_fitness / len(results) if results else 0.0

            logger.info(
                f"Token replay conformance: {conformant_count}/{len(results)} conformant, "
                f"avg fitness: {avg_fitness:.3f}"
            )

            return ConformanceSummary(
                total_traces=len(results),
                conformant_traces=conformant_count,
                average_fitness=avg_fitness,
                method=ConformanceMethod.TOKEN_REPLAY.value,
                individual_results=results,
            )

        except Exception as e:
            logger.error(f"Token replay conformance check failed: {e}")
            raise

    def check_conformance_alignments(
        self,
        traces: list[ExecutionTrace],
        petri_net_result: PetriNetResult,
    ) -> ConformanceSummary:
        """
        Check conformance using alignment-based method.

        More accurate than token replay but computationally expensive.

        Args:
            traces: List of ExecutionTrace objects.
            petri_net_result: Previously discovered Petri net.

        Returns:
            ConformanceSummary with individual trace results.
        """
        pm4py = self._ensure_pm4py()
        log = self.traces_to_event_log(traces)

        try:
            aligned_traces = pm4py.conformance_diagnostics_alignments(
                log,
                petri_net_result.net,
                petri_net_result.initial_marking,
                petri_net_result.final_marking,
            )

            results = []
            total_fitness = 0.0
            conformant_count = 0

            for i, result in enumerate(aligned_traces):
                trace_id = traces[i].case_id if i < len(traces) else f"trace_{i}"
                fitness = result.get("fitness", 0.0)
                cost = result.get("cost", 0.0)

                # Extract deviations from alignment
                deviations = []
                alignment = result.get("alignment", [])
                for step in alignment:
                    if step[0] != step[1]:  # Deviation
                        deviations.append(
                            {
                                "log_move": str(step[0]) if step[0] else ">>",
                                "model_move": str(step[1]) if step[1] else ">>",
                            }
                        )

                is_conformant = fitness >= 0.95 and cost == 0

                align_result = AlignmentResult(
                    trace_id=trace_id,
                    fitness=fitness,
                    aligned_traces=[{"alignment": alignment}],
                    deviations=deviations,
                    cost=cost,
                    is_conformant=is_conformant,
                )
                results.append(align_result)
                total_fitness += fitness
                if is_conformant:
                    conformant_count += 1

            avg_fitness = total_fitness / len(results) if results else 0.0

            # Calculate precision if available
            precision = 0.0
            try:
                from pm4py.algo.evaluation.precision import (
                    algorithm as precision_evaluator,
                )

                precision = precision_evaluator.apply(
                    log,
                    petri_net_result.net,
                    petri_net_result.initial_marking,
                    petri_net_result.final_marking,
                )
            except Exception:
                pass

            logger.info(
                f"Alignment conformance: {conformant_count}/{len(results)} conformant, "
                f"avg fitness: {avg_fitness:.3f}, precision: {precision:.3f}"
            )

            return ConformanceSummary(
                total_traces=len(results),
                conformant_traces=conformant_count,
                average_fitness=avg_fitness,
                precision=precision,
                method=ConformanceMethod.ALIGNMENTS.value,
                individual_results=results,
            )

        except Exception as e:
            logger.error(f"Alignment conformance check failed: {e}")
            raise

    # =========================================================================
    # Visualization Methods
    # =========================================================================

    def visualize_petri_net(
        self,
        petri_net_result: PetriNetResult,
        output_path: str,
        format: str = "png",
    ) -> str:
        """
        Visualize Petri net model as image.

        Args:
            petri_net_result: Discovered Petri net.
            output_path: Path for output file (without extension).
            format: Image format (png, svg, pdf).

        Returns:
            Path to generated image file.

        Requires:
            graphviz to be installed on the system.
        """
        pm4py = self._ensure_pm4py()

        try:
            pm4py.save_vis_petri_net(
                petri_net_result.net,
                petri_net_result.initial_marking,
                petri_net_result.final_marking,
                f"{output_path}.{format}",
            )
            logger.info(f"Saved Petri net visualization: {output_path}.{format}")
            return f"{output_path}.{format}"

        except Exception as e:
            logger.error(f"Petri net visualization failed: {e}")
            raise

    def visualize_bpmn(
        self,
        bpmn_result: BPMNResult,
        output_path: str,
        format: str = "png",
    ) -> str:
        """
        Visualize BPMN model as image.

        Args:
            bpmn_result: Discovered BPMN model.
            output_path: Path for output file (without extension).
            format: Image format (png, svg, pdf).

        Returns:
            Path to generated image file.
        """
        pm4py = self._ensure_pm4py()

        try:
            pm4py.save_vis_bpmn(
                bpmn_result.model,
                f"{output_path}.{format}",
            )
            logger.info(f"Saved BPMN visualization: {output_path}.{format}")
            return f"{output_path}.{format}"

        except Exception as e:
            logger.error(f"BPMN visualization failed: {e}")
            raise

    def visualize_dfg(
        self,
        traces: list[ExecutionTrace],
        output_path: str,
        format: str = "png",
    ) -> str:
        """
        Visualize Direct-Follows Graph as image.

        Args:
            traces: List of execution traces.
            output_path: Path for output file (without extension).
            format: Image format (png, svg, pdf).

        Returns:
            Path to generated image file.
        """
        pm4py = self._ensure_pm4py()
        log = self.traces_to_event_log(traces)

        try:
            dfg, start, end = pm4py.discover_dfg(log)
            pm4py.save_vis_dfg(
                dfg,
                start,
                end,
                f"{output_path}.{format}",
            )
            logger.info(f"Saved DFG visualization: {output_path}.{format}")
            return f"{output_path}.{format}"

        except Exception as e:
            logger.error(f"DFG visualization failed: {e}")
            raise


# =============================================================================
# Singleton Instance
# =============================================================================

_pm4py_integration: PM4PyIntegration | None = None


def get_pm4py_integration() -> PM4PyIntegration:
    """Get singleton PM4PyIntegration instance."""
    global _pm4py_integration
    if _pm4py_integration is None:
        _pm4py_integration = PM4PyIntegration()
    return _pm4py_integration


__all__ = [
    "PM4PyIntegration",
    "DiscoveryAlgorithm",
    "ConformanceMethod",
    "PetriNetResult",
    "BPMNResult",
    "AlignmentResult",
    "TokenReplayResult",
    "ConformanceSummary",
    "get_pm4py_integration",
]
