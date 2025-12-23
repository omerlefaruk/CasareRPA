"""
CasareRPA - Frequent Pattern Miner

Finds frequent activity subsequences in execution traces
using a PrefixSpan-inspired algorithm.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple

from loguru import logger

from casare_rpa.infrastructure.analytics.process_mining import (
    ExecutionTrace,
)


@dataclass
class FrequentSubsequence:
    """A frequently occurring subsequence of activities."""

    sequence: list[str]
    support: int  # Number of traces containing this subsequence
    support_ratio: float  # support / total_traces
    avg_duration_ms: float
    node_types: list[str]
    positions: dict[str, list[int]]  # trace_id -> list of start positions

    @property
    def length(self) -> int:
        """Length of the subsequence."""
        return len(self.sequence)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "sequence": self.sequence,
            "support": self.support,
            "support_ratio": round(self.support_ratio, 3),
            "avg_duration_ms": round(self.avg_duration_ms, 2),
            "node_types": self.node_types,
            "length": self.length,
        }


@dataclass
class FrequentPatternResult:
    """Result of frequent pattern mining."""

    min_support: float
    total_traces: int
    subsequences: list[FrequentSubsequence]
    mining_time_ms: float

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "min_support": self.min_support,
            "total_traces": self.total_traces,
            "pattern_count": len(self.subsequences),
            "mining_time_ms": round(self.mining_time_ms, 2),
            "subsequences": [s.to_dict() for s in self.subsequences],
        }


class FrequentPatternMiner:
    """
    Find frequent activity subsequences in execution traces.

    Uses a simplified PrefixSpan algorithm for sequential pattern mining.
    """

    def __init__(self) -> None:
        """Initialize frequent pattern miner."""
        logger.debug("FrequentPatternMiner initialized")

    def mine_patterns(
        self,
        traces: list[ExecutionTrace],
        min_support: float = 0.3,
        max_length: int = 10,
        min_length: int = 2,
    ) -> FrequentPatternResult:
        """
        Mine frequent sequential patterns from execution traces.

        Args:
            traces: List of execution traces to analyze.
            min_support: Minimum support threshold (0-1).
                A pattern needs to appear in at least min_support * len(traces) traces.
            max_length: Maximum pattern length to mine.
            min_length: Minimum pattern length to return.

        Returns:
            FrequentPatternResult with discovered patterns.
        """
        import time

        start_time = time.time()

        if not traces:
            return FrequentPatternResult(
                min_support=min_support,
                total_traces=0,
                subsequences=[],
                mining_time_ms=0.0,
            )

        total_traces = len(traces)
        min_support_count = max(1, int(min_support * total_traces))

        # Extract sequences and build activity info
        sequences: list[list[str]] = []
        activity_info: dict[str, dict[str, Any]] = {}  # node_id -> {type, durations}

        for trace in traces:
            seq = []
            for activity in trace.activities:
                node_id = activity.node_id
                seq.append(node_id)

                if node_id not in activity_info:
                    activity_info[node_id] = {
                        "type": activity.node_type,
                        "durations": [],
                    }
                activity_info[node_id]["durations"].append(activity.duration_ms)

            sequences.append(seq)

        # Mine frequent patterns using PrefixSpan approach
        frequent_patterns = self._prefixspan(
            sequences=sequences,
            min_support_count=min_support_count,
            max_length=max_length,
        )

        # Build subsequence objects
        subsequences = []
        for pattern, support, positions in frequent_patterns:
            if len(pattern) < min_length:
                continue

            # Calculate average duration
            durations = []
            for node_id in pattern:
                if node_id in activity_info:
                    durations.extend(activity_info[node_id]["durations"])
            avg_duration = sum(durations) / len(durations) if durations else 0.0

            # Get node types
            node_types = [
                activity_info.get(node_id, {}).get("type", "unknown") for node_id in pattern
            ]

            subsequences.append(
                FrequentSubsequence(
                    sequence=list(pattern),
                    support=support,
                    support_ratio=support / total_traces,
                    avg_duration_ms=avg_duration,
                    node_types=node_types,
                    positions=positions,
                )
            )

        # Sort by support (descending), then by length (descending)
        subsequences.sort(key=lambda s: (s.support, s.length), reverse=True)

        elapsed_ms = (time.time() - start_time) * 1000

        logger.info(
            f"Mined {len(subsequences)} frequent patterns from {total_traces} traces "
            f"(min_support={min_support}, time={elapsed_ms:.1f}ms)"
        )

        return FrequentPatternResult(
            min_support=min_support,
            total_traces=total_traces,
            subsequences=subsequences,
            mining_time_ms=elapsed_ms,
        )

    def _prefixspan(
        self,
        sequences: list[list[str]],
        min_support_count: int,
        max_length: int,
    ) -> list[tuple[tuple[str, ...], int, dict[str, list[int]]]]:
        """
        PrefixSpan algorithm for sequential pattern mining.

        Returns list of (pattern, support, positions) tuples.
        """
        # Find frequent 1-sequences
        item_counts: dict[str, int] = defaultdict(int)
        item_positions: dict[str, dict[int, list[int]]] = defaultdict(lambda: defaultdict(list))

        for seq_idx, seq in enumerate(sequences):
            seen: set[str] = set()
            for pos, item in enumerate(seq):
                if item not in seen:
                    item_counts[item] += 1
                    seen.add(item)
                item_positions[item][seq_idx].append(pos)

        # Filter frequent items
        frequent_items = [item for item, count in item_counts.items() if count >= min_support_count]

        if not frequent_items:
            return []

        # Results
        results: list[tuple[tuple[str, ...], int, dict[str, list[int]]]] = []

        # Add frequent 1-sequences
        for item in frequent_items:
            positions = {
                str(seq_idx): pos_list for seq_idx, pos_list in item_positions[item].items()
            }
            results.append(((item,), item_counts[item], positions))

        # Grow patterns using prefix-projected databases
        for item in frequent_items:
            prefix = (item,)
            projected_db = self._build_projected_database(sequences, prefix, item_positions[item])
            self._prefixspan_recursive(
                prefix=prefix,
                projected_db=projected_db,
                sequences=sequences,
                min_support_count=min_support_count,
                max_length=max_length,
                results=results,
            )

        return results

    def _build_projected_database(
        self,
        sequences: list[list[str]],
        prefix: tuple[str, ...],
        start_positions: dict[int, list[int]],
    ) -> dict[int, list[tuple[int, list[str]]]]:
        """
        Build projected database for a prefix.

        Returns dict: seq_idx -> list of (start_pos, suffix) tuples.
        """
        projected: dict[int, list[tuple[int, list[str]]]] = {}

        for seq_idx, positions in start_positions.items():
            seq = sequences[seq_idx]
            suffixes = []

            for pos in positions:
                # Get suffix after the prefix occurrence
                suffix_start = pos + len(prefix)
                if suffix_start < len(seq):
                    suffix = seq[suffix_start:]
                    suffixes.append((pos, suffix))

            if suffixes:
                projected[seq_idx] = suffixes

        return projected

    def _prefixspan_recursive(
        self,
        prefix: tuple[str, ...],
        projected_db: dict[int, list[tuple[int, list[str]]]],
        sequences: list[list[str]],
        min_support_count: int,
        max_length: int,
        results: list[tuple[tuple[str, ...], int, dict[str, list[int]]]],
    ) -> None:
        """Recursive PrefixSpan pattern growth."""
        if len(prefix) >= max_length:
            return

        # Find frequent items in projected database
        item_counts: dict[str, int] = defaultdict(int)
        item_positions: dict[str, dict[int, list[int]]] = defaultdict(lambda: defaultdict(list))

        for seq_idx, suffixes in projected_db.items():
            seen: set[str] = set()
            for start_pos, suffix in suffixes:
                for i, item in enumerate(suffix):
                    if item not in seen:
                        item_counts[item] += 1
                        seen.add(item)
                    item_positions[item][seq_idx].append(start_pos + len(prefix) + i)

        # Grow with each frequent item
        for item, count in item_counts.items():
            if count < min_support_count:
                continue

            new_prefix = prefix + (item,)

            # Record positions
            positions = {
                str(seq_idx): pos_list for seq_idx, pos_list in item_positions[item].items()
            }
            results.append((new_prefix, count, positions))

            # Build new projected database
            new_projected = self._build_projected_database_from_suffix(projected_db, item)

            if new_projected:
                self._prefixspan_recursive(
                    prefix=new_prefix,
                    projected_db=new_projected,
                    sequences=sequences,
                    min_support_count=min_support_count,
                    max_length=max_length,
                    results=results,
                )

    def _build_projected_database_from_suffix(
        self,
        projected_db: dict[int, list[tuple[int, list[str]]]],
        item: str,
    ) -> dict[int, list[tuple[int, list[str]]]]:
        """Build new projected database by extending suffixes with item."""
        new_projected: dict[int, list[tuple[int, list[str]]]] = {}

        for seq_idx, suffixes in projected_db.items():
            new_suffixes = []

            for start_pos, suffix in suffixes:
                # Find first occurrence of item in suffix
                try:
                    item_pos = suffix.index(item)
                    # New suffix starts after the item
                    new_suffix_start = item_pos + 1
                    if new_suffix_start < len(suffix):
                        new_suffix = suffix[new_suffix_start:]
                        new_suffixes.append((start_pos + item_pos, new_suffix))
                except ValueError:
                    continue

            if new_suffixes:
                new_projected[seq_idx] = new_suffixes

        return new_projected

    def find_maximal_patterns(self, result: FrequentPatternResult) -> list[FrequentSubsequence]:
        """
        Find maximal frequent patterns (not subsumed by longer patterns).

        A pattern is maximal if no frequent supersequence exists.

        Args:
            result: Result from mine_patterns().

        Returns:
            List of maximal frequent subsequences.
        """
        if not result.subsequences:
            return []

        # Sort by length descending to check longer patterns first
        sorted_seqs = sorted(result.subsequences, key=lambda s: s.length, reverse=True)

        maximal: list[FrequentSubsequence] = []
        maximal_sequences: set[tuple[str, ...]] = set()

        for subseq in sorted_seqs:
            seq_tuple = tuple(subseq.sequence)

            # Check if this is subsumed by any maximal pattern
            is_subsumed = False
            for max_seq in maximal_sequences:
                if self._is_subsequence(seq_tuple, max_seq):
                    is_subsumed = True
                    break

            if not is_subsumed:
                maximal.append(subseq)
                maximal_sequences.add(seq_tuple)

        return maximal

    def _is_subsequence(self, short: tuple[str, ...], long: tuple[str, ...]) -> bool:
        """Check if short is a subsequence of long."""
        if len(short) >= len(long):
            return False

        short_idx = 0
        for item in long:
            if short_idx < len(short) and item == short[short_idx]:
                short_idx += 1

        return short_idx == len(short)

    def find_pattern_gaps(
        self,
        traces: list[ExecutionTrace],
        pattern: FrequentSubsequence,
    ) -> dict[str, Any]:
        """
        Analyze gaps between pattern elements in traces.

        Useful for understanding timing between pattern activities.

        Args:
            traces: Execution traces.
            pattern: Pattern to analyze.

        Returns:
            Dict with gap statistics.
        """
        gaps: list[list[int]] = [[] for _ in range(len(pattern.sequence) - 1)]

        for trace in traces:
            activities = trace.activities
            if len(activities) < len(pattern.sequence):
                continue

            # Find pattern in trace
            pattern_idx = 0
            prev_end_time: int | None = None

            for pos, activity in enumerate(activities):
                if activity.node_id == pattern.sequence[pattern_idx]:
                    if prev_end_time is not None and pattern_idx > 0:
                        gap = activity.duration_ms  # Simplified: use duration as proxy
                        gaps[pattern_idx - 1].append(gap)

                    prev_end_time = activity.duration_ms
                    pattern_idx += 1

                    if pattern_idx >= len(pattern.sequence):
                        break

        # Calculate statistics
        gap_stats = []
        for i, gap_list in enumerate(gaps):
            if gap_list:
                gap_stats.append(
                    {
                        "gap_index": i,
                        "from": pattern.sequence[i],
                        "to": pattern.sequence[i + 1],
                        "min_ms": min(gap_list),
                        "max_ms": max(gap_list),
                        "avg_ms": sum(gap_list) / len(gap_list),
                        "samples": len(gap_list),
                    }
                )
            else:
                gap_stats.append(
                    {
                        "gap_index": i,
                        "from": pattern.sequence[i],
                        "to": pattern.sequence[i + 1],
                        "min_ms": 0,
                        "max_ms": 0,
                        "avg_ms": 0,
                        "samples": 0,
                    }
                )

        return {
            "pattern": pattern.sequence,
            "gap_count": len(gaps),
            "gaps": gap_stats,
        }


__all__ = [
    "FrequentPatternMiner",
    "FrequentSubsequence",
    "FrequentPatternResult",
]
