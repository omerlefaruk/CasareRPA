"""
Task analyzer for automatic task decomposition.

Uses keyword matching, structural analysis, and heuristics to
extract work items from task descriptions.
"""

import re
from dataclasses import dataclass
from typing import Any

from casare_rpa.domain.entities.chain import AgentType


@dataclass
class WorkItem:
    """A detected work item from task analysis."""

    title: str
    agent_type: AgentType
    layer: str | None = None
    requires_parallel: bool = False
    description: str = ""


class TaskAnalyzer:
    """
    Analyzes task descriptions and extracts work items.

    Uses keyword matching, structural analysis, and heuristics.
    """

    # Layer-specific patterns
    LAYER_PATTERNS: dict[str, list[str]] = {
        "domain": ["entity", "value object", "aggregate", "domain event", "domain service"],
        "application": ["use case", "query", "command", "orchestrator", "workflow"],
        "infrastructure": ["adapter", "repository", "external api", "http client", "persistence"],
        "presentation": ["widget", "panel", "dialog", "canvas", "visual node", "ui component"],
        "nodes": ["node", "automation", "browser", "desktop", "control flow"],
    }

    # Work item patterns
    WORK_PATTERNS: dict[str, tuple[list[str], AgentType, str | None]] = {
        "node": (["node", "automation", "action"], AgentType.BUILDER, "nodes"),
        "entity": (["entity", "model", "domain object"], AgentType.ARCHITECT, "domain"),
        "use_case": (["use case", "workflow", "orchestration"], AgentType.ARCHITECT, "application"),
        "api": (
            ["api", "http", "rest", "graphql", "integration"],
            AgentType.INTEGRATIONS,
            "infrastructure",
        ),
        "ui": (["widget", "dialog", "panel", "screen", "form"], AgentType.UI, "presentation"),
        "test": (["test", "testing", "coverage"], AgentType.QUALITY, None),
        "docs": (["documentation", "docs", "readme", "guide"], AgentType.DOCS, None),
        "fix": (["fix", "bug", "issue", "debug"], AgentType.BUILDER, None),
        "refactor": (["refactor", "clean", "modernize", "optimize"], AgentType.REFACTOR, None),
        "research": (["research", "investigate", "explore", "analyze"], AgentType.RESEARCHER, None),
        # Generic patterns (must be checked after specific ones)
        "implement": (
            ["implement", "add", "create", "build", "new", "feature"],
            AgentType.BUILDER,
            None,
        ),
    }

    # Conjunction patterns indicating parallel work
    PARALLEL_INDICATORS = [
        r"\b(?:and|with|also|plus|along with)\s+(?:a|another|separate)\s+\w+",
        r"\bboth\s+\w+\s+and\s+\w+",
        r"\b(?:additionally|simultaneously|in parallel)\s+",
        r"\W,\s*\w+",  # Comma-separated items
    ]

    def analyze(
        self, task_description: str, context: dict[str, Any] | None = None
    ) -> list[WorkItem]:
        """
        Analyze task and extract work items.

        Args:
            task_description: The task to analyze
            context: Optional context (layer, scope, etc.)

        Returns:
            List of detected work items
        """
        context = context or {}
        work_items = []

        # Split on common delimiters
        segments = self._split_task(task_description)

        for segment in segments:
            pattern_match = self._match_work_pattern(segment, context)
            if pattern_match:
                work_items.append(pattern_match)

        # Always add explore phase if not explicit
        if not any(w.agent_type == AgentType.EXPLORE for w in work_items):
            explore_count = min(len([w for w in work_items if w.layer]), 3)
            explore_count = max(explore_count, 1)
            for i in range(explore_count):
                work_items.insert(
                    i,
                    WorkItem(
                        title=f"Explore codebase patterns ({i+1})",
                        agent_type=AgentType.EXPLORE,
                        requires_parallel=(explore_count > 1),
                        description="Find existing patterns and architecture",
                    ),
                )

        # Add architect if implementation detected and not present
        has_implementation = any(
            w.agent_type in [AgentType.BUILDER, AgentType.UI, AgentType.INTEGRATIONS]
            for w in work_items
        )
        if has_implementation and not any(w.agent_type == AgentType.ARCHITECT for w in work_items):
            # Insert architect after explore phases
            explore_count = len([w for w in work_items if w.agent_type == AgentType.EXPLORE])
            work_items.insert(
                explore_count,
                WorkItem(
                    title="Design architecture",
                    agent_type=AgentType.ARCHITECT,
                    requires_parallel=False,
                    description="Create implementation plan",
                ),
            )

        # Add quality + reviewer if implementation detected
        if has_implementation:
            if not any(w.agent_type == AgentType.QUALITY for w in work_items):
                work_items.append(
                    WorkItem(
                        title="Write tests",
                        agent_type=AgentType.QUALITY,
                        requires_parallel=False,
                        description="Create test coverage",
                    )
                )
            if not any(w.agent_type == AgentType.REVIEWER for w in work_items):
                work_items.append(
                    WorkItem(
                        title="Review implementation",
                        agent_type=AgentType.REVIEWER,
                        requires_parallel=False,
                        description="Code review and validation",
                    )
                )

        return work_items

    def _split_task(self, task: str) -> list[str]:
        """Split task into work segments."""
        delimiters = [r"\.\s+", r"\n\s*[-*]\s*", r";\s*"]
        segments = [task]

        for delimiter in delimiters:
            new_segments = []
            for seg in segments:
                new_segments.extend(re.split(delimiter, seg))
            if len(new_segments) > len(segments):
                segments = new_segments
                break

        return [s.strip() for s in segments if s.strip()]

    def _match_work_pattern(self, segment: str, context: dict[str, Any]) -> WorkItem | None:
        """Match segment to a work pattern."""
        segment_lower = segment.lower()

        # Check explicit layer context
        layer_hint = context.get("layer")

        for pattern_name, (keywords, agent_type, layer) in self.WORK_PATTERNS.items():
            for keyword in keywords:
                if keyword in segment_lower:
                    return WorkItem(
                        title=segment.strip()[:100],
                        agent_type=agent_type,
                        layer=layer_hint or layer,
                        requires_parallel=self._check_parallel_indicators(segment),
                        description=segment.strip(),
                    )

        return None

    def _check_parallel_indicators(self, segment: str) -> bool:
        """Check if segment indicates parallelizable work."""
        for pattern in self.PARALLEL_INDICATORS:
            if re.search(pattern, segment.lower()):
                return True
        return False
