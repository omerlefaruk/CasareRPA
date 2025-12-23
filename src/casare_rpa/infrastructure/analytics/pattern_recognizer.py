"""
CasareRPA - Pattern Recognizer

ML-based pattern recognition for identifying repetitive task patterns
using DBSCAN clustering and n-gram feature extraction.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

from casare_rpa.infrastructure.analytics.process_mining import (
    ActivityStatus,
    ExecutionTrace,
)


@dataclass
class RecognizedPattern:
    """A recognized pattern from execution traces."""

    pattern_id: str
    activity_sequence: list[str]
    frequency: int
    avg_duration: float
    cluster_id: int
    representative_traces: list[str]
    automation_potential: float  # 0-1 score
    node_types: list[str] = field(default_factory=list)
    success_rate: float = 1.0
    variance_score: float = 0.0  # Low variance = more automatable
    time_pattern: str | None = None  # e.g., "morning", "weekday"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "pattern_id": self.pattern_id,
            "activity_sequence": self.activity_sequence,
            "frequency": self.frequency,
            "avg_duration": self.avg_duration,
            "cluster_id": self.cluster_id,
            "representative_traces": self.representative_traces,
            "automation_potential": round(self.automation_potential, 3),
            "node_types": self.node_types,
            "success_rate": round(self.success_rate, 3),
            "variance_score": round(self.variance_score, 3),
            "time_pattern": self.time_pattern,
        }


@dataclass
class PatternFeatures:
    """Feature vector for a trace used in clustering."""

    trace_id: str
    ngrams: dict[str, int]  # n-gram -> count
    duration_features: list[float]
    time_features: list[float]  # hour, day_of_week
    activity_count: int
    unique_activities: int
    success_rate: float


class PatternRecognizer:
    """
    ML-based pattern recognition for execution traces.

    Uses DBSCAN clustering to identify repetitive task patterns.
    sklearn is lazy-loaded to avoid startup overhead.
    """

    def __init__(self) -> None:
        """Initialize pattern recognizer."""
        self._sklearn = None
        self._numpy = None
        logger.debug("PatternRecognizer initialized")

    def _load_sklearn(self) -> bool:
        """Lazy load sklearn and numpy."""
        if self._sklearn is not None:
            return True

        try:
            import numpy as np
            from sklearn.cluster import DBSCAN
            from sklearn.preprocessing import StandardScaler

            self._numpy = np
            self._sklearn = {
                "DBSCAN": DBSCAN,
                "StandardScaler": StandardScaler,
            }
            return True
        except ImportError:
            logger.warning("sklearn not available - pattern recognition disabled")
            return False

    def extract_patterns(
        self,
        traces: list[ExecutionTrace],
        min_samples: int = 3,
        eps: float = 0.5,
        ngram_sizes: tuple[int, ...] = (2, 3),
    ) -> list[RecognizedPattern]:
        """
        Extract patterns from execution traces using DBSCAN clustering.

        Args:
            traces: List of execution traces to analyze.
            min_samples: Minimum samples for DBSCAN cluster.
            eps: Maximum distance between samples for DBSCAN.
            ngram_sizes: Tuple of n-gram sizes to extract (default: bigrams, trigrams).

        Returns:
            List of recognized patterns sorted by automation potential.
        """
        if not traces:
            return []

        if len(traces) < min_samples:
            logger.info(f"Insufficient traces ({len(traces)}) for pattern recognition")
            return []

        if not self._load_sklearn():
            return self._fallback_pattern_extraction(traces)

        # Extract features for each trace
        features_list = [self._extract_features(trace, ngram_sizes) for trace in traces]

        # Build feature matrix
        feature_matrix, ngram_vocab = self._build_feature_matrix(features_list)

        if feature_matrix.shape[0] < min_samples:
            return self._fallback_pattern_extraction(traces)

        # Scale features
        scaler = self._sklearn["StandardScaler"]()
        scaled_features = scaler.fit_transform(feature_matrix)

        # Apply DBSCAN clustering
        dbscan = self._sklearn["DBSCAN"](eps=eps, min_samples=min_samples)
        cluster_labels = dbscan.fit_predict(scaled_features)

        # Group traces by cluster
        clusters: dict[int, list[tuple[ExecutionTrace, PatternFeatures]]] = defaultdict(list)
        for trace, features, label in zip(traces, features_list, cluster_labels, strict=False):
            if label != -1:  # Ignore noise points
                clusters[label].append((trace, features))

        # Build patterns from clusters
        patterns = []
        for cluster_id, cluster_traces in clusters.items():
            pattern = self._build_pattern_from_cluster(cluster_id, cluster_traces, ngram_vocab)
            if pattern:
                patterns.append(pattern)

        # Sort by automation potential (descending)
        patterns.sort(key=lambda p: p.automation_potential, reverse=True)

        logger.info(f"Extracted {len(patterns)} patterns from {len(traces)} traces")
        return patterns

    def _extract_features(
        self, trace: ExecutionTrace, ngram_sizes: tuple[int, ...]
    ) -> PatternFeatures:
        """Extract feature vector from a single trace."""
        activities = trace.activities
        sequence = [a.node_id for a in activities]

        # Extract n-grams
        ngrams: dict[str, int] = {}
        for n in ngram_sizes:
            for i in range(len(sequence) - n + 1):
                ngram = "->".join(sequence[i : i + n])
                ngrams[ngram] = ngrams.get(ngram, 0) + 1

        # Duration features
        durations = [a.duration_ms for a in activities]
        if durations:
            duration_features = [
                sum(durations) / len(durations),  # mean
                max(durations) - min(durations),  # range
                sum(durations),  # total
            ]
        else:
            duration_features = [0.0, 0.0, 0.0]

        # Time features (normalized hour and day)
        hour = trace.start_time.hour / 24.0
        day = trace.start_time.weekday() / 7.0
        time_features = [hour, day]

        # Success rate
        if activities:
            success_count = sum(1 for a in activities if a.status == ActivityStatus.COMPLETED)
            success_rate = success_count / len(activities)
        else:
            success_rate = 1.0

        return PatternFeatures(
            trace_id=trace.case_id,
            ngrams=ngrams,
            duration_features=duration_features,
            time_features=time_features,
            activity_count=len(activities),
            unique_activities=len(set(sequence)),
            success_rate=success_rate,
        )

    def _build_feature_matrix(
        self, features_list: list[PatternFeatures]
    ) -> tuple[Any, dict[str, int]]:
        """Build feature matrix from pattern features."""
        np = self._numpy

        # Build vocabulary from all n-grams
        all_ngrams: set = set()
        for features in features_list:
            all_ngrams.update(features.ngrams.keys())

        ngram_vocab = {ngram: idx for idx, ngram in enumerate(sorted(all_ngrams))}
        vocab_size = len(ngram_vocab)

        # Build feature matrix
        rows = []
        for features in features_list:
            # N-gram features (sparse)
            ngram_vec = [0.0] * vocab_size
            for ngram, count in features.ngrams.items():
                if ngram in ngram_vocab:
                    ngram_vec[ngram_vocab[ngram]] = count

            # Combine all features
            row = (
                ngram_vec
                + features.duration_features
                + features.time_features
                + [
                    features.activity_count,
                    features.unique_activities,
                    features.success_rate,
                ]
            )
            rows.append(row)

        return np.array(rows), ngram_vocab

    def _build_pattern_from_cluster(
        self,
        cluster_id: int,
        cluster_traces: list[tuple[ExecutionTrace, PatternFeatures]],
        ngram_vocab: dict[str, int],
    ) -> RecognizedPattern | None:
        """Build a recognized pattern from a cluster of traces."""
        if not cluster_traces:
            return None

        traces = [t for t, _ in cluster_traces]
        features = [f for _, f in cluster_traces]

        # Find common sequence (most frequent activity order)
        sequences = [tuple(a.node_id for a in t.activities) for t in traces]
        sequence_counts = Counter(sequences)
        most_common_seq, freq = sequence_counts.most_common(1)[0]

        # Calculate statistics
        durations = [t.total_duration_ms for t in traces]
        avg_duration = sum(durations) / len(durations) if durations else 0.0

        success_rates = [f.success_rate for f in features]
        avg_success = sum(success_rates) / len(success_rates) if success_rates else 1.0

        # Calculate variance score (lower is better for automation)
        if len(durations) > 1:
            mean_dur = sum(durations) / len(durations)
            variance = sum((d - mean_dur) ** 2 for d in durations) / len(durations)
            std_dev = variance**0.5
            variance_score = std_dev / mean_dur if mean_dur > 0 else 1.0
        else:
            variance_score = 0.0

        # Get representative node types
        node_types = []
        if traces:
            sample_trace = traces[0]
            node_types = [a.node_type for a in sample_trace.activities]

        # Calculate automation potential
        automation_potential = self._calculate_automation_potential(
            frequency=len(traces),
            success_rate=avg_success,
            variance_score=variance_score,
            avg_duration=avg_duration,
        )

        # Detect time pattern
        time_pattern = self._detect_time_pattern(traces)

        return RecognizedPattern(
            pattern_id=f"P{cluster_id:03d}",
            activity_sequence=list(most_common_seq),
            frequency=len(traces),
            avg_duration=avg_duration,
            cluster_id=cluster_id,
            representative_traces=[t.case_id for t in traces[:5]],
            automation_potential=automation_potential,
            node_types=node_types,
            success_rate=avg_success,
            variance_score=variance_score,
            time_pattern=time_pattern,
        )

    def _calculate_automation_potential(
        self,
        frequency: int,
        success_rate: float,
        variance_score: float,
        avg_duration: float,
    ) -> float:
        """
        Calculate automation potential score (0-1).

        Higher score = better automation candidate.
        Factors:
        - Frequency: More frequent = more value from automation
        - Success rate: High success = more predictable
        - Variance: Low variance = more consistent, easier to automate
        - Duration: Longer tasks = more time savings
        """
        # Frequency factor (log scale, max at ~100)
        freq_score = min(1.0, (frequency / 100) ** 0.5)

        # Success factor
        success_score = success_rate

        # Variance factor (lower is better)
        variance_factor = max(0.0, 1.0 - variance_score)

        # Duration factor (longer = more valuable, cap at 1 hour)
        duration_score = min(1.0, avg_duration / 3600000)  # 1 hour in ms

        # Weighted combination
        weights = {
            "frequency": 0.3,
            "success": 0.3,
            "variance": 0.25,
            "duration": 0.15,
        }

        potential = (
            weights["frequency"] * freq_score
            + weights["success"] * success_score
            + weights["variance"] * variance_factor
            + weights["duration"] * duration_score
        )

        return min(1.0, max(0.0, potential))

    def _detect_time_pattern(self, traces: list[ExecutionTrace]) -> str | None:
        """Detect time-based patterns in trace execution."""
        if not traces:
            return None

        hours = [t.start_time.hour for t in traces]
        days = [t.start_time.weekday() for t in traces]

        # Check for morning/afternoon/evening pattern
        morning = sum(1 for h in hours if 6 <= h < 12)
        afternoon = sum(1 for h in hours if 12 <= h < 18)
        evening = sum(1 for h in hours if 18 <= h < 22)

        total = len(hours)
        threshold = 0.6  # 60% concentration

        if morning / total > threshold:
            return "morning"
        if afternoon / total > threshold:
            return "afternoon"
        if evening / total > threshold:
            return "evening"

        # Check for weekday/weekend pattern
        weekdays = sum(1 for d in days if d < 5)
        if weekdays / total > 0.8:
            return "weekdays"
        if (total - weekdays) / total > 0.6:
            return "weekends"

        return None

    def _fallback_pattern_extraction(self, traces: list[ExecutionTrace]) -> list[RecognizedPattern]:
        """
        Fallback pattern extraction without sklearn.

        Uses simple frequency-based grouping.
        """
        # Group by activity sequence
        sequence_groups: dict[tuple, list[ExecutionTrace]] = defaultdict(list)
        for trace in traces:
            seq = tuple(a.node_id for a in trace.activities)
            sequence_groups[seq].append(trace)

        patterns = []
        for idx, (seq, group_traces) in enumerate(sequence_groups.items()):
            if len(group_traces) < 2:
                continue

            durations = [t.total_duration_ms for t in group_traces]
            avg_duration = sum(durations) / len(durations)

            success_rates = [t.success_rate for t in group_traces]
            avg_success = sum(success_rates) / len(success_rates)

            # Calculate variance
            if len(durations) > 1:
                mean_dur = avg_duration
                variance = sum((d - mean_dur) ** 2 for d in durations) / len(durations)
                variance_score = (variance**0.5) / mean_dur if mean_dur > 0 else 1.0
            else:
                variance_score = 0.0

            node_types = []
            if group_traces:
                node_types = [a.node_type for a in group_traces[0].activities]

            automation_potential = self._calculate_automation_potential(
                frequency=len(group_traces),
                success_rate=avg_success,
                variance_score=variance_score,
                avg_duration=avg_duration,
            )

            patterns.append(
                RecognizedPattern(
                    pattern_id=f"P{idx:03d}",
                    activity_sequence=list(seq),
                    frequency=len(group_traces),
                    avg_duration=avg_duration,
                    cluster_id=idx,
                    representative_traces=[t.case_id for t in group_traces[:5]],
                    automation_potential=automation_potential,
                    node_types=node_types,
                    success_rate=avg_success,
                    variance_score=variance_score,
                    time_pattern=self._detect_time_pattern(group_traces),
                )
            )

        patterns.sort(key=lambda p: p.automation_potential, reverse=True)
        return patterns

    def find_similar_patterns(
        self,
        pattern: RecognizedPattern,
        all_patterns: list[RecognizedPattern],
        similarity_threshold: float = 0.7,
    ) -> list[RecognizedPattern]:
        """
        Find patterns similar to a given pattern.

        Args:
            pattern: Pattern to compare against.
            all_patterns: All patterns to search.
            similarity_threshold: Minimum similarity score (0-1).

        Returns:
            List of similar patterns.
        """
        similar = []
        pattern_set = set(pattern.activity_sequence)

        for other in all_patterns:
            if other.pattern_id == pattern.pattern_id:
                continue

            other_set = set(other.activity_sequence)

            # Jaccard similarity
            intersection = len(pattern_set & other_set)
            union = len(pattern_set | other_set)

            if union > 0:
                similarity = intersection / union
                if similarity >= similarity_threshold:
                    similar.append(other)

        return similar


__all__ = [
    "PatternRecognizer",
    "RecognizedPattern",
    "PatternFeatures",
]
