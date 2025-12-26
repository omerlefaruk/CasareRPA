"""
Dependency Manager - Handle cross-chain dependencies and conflict detection.

This service provides:
- Dependency graph management
- Execution order determination
- Conflict detection and resolution
"""

from collections import defaultdict, deque
from typing import Any

from loguru import logger

from casare_rpa.domain.entities.chain_types import (
    ChainSpec,
    ChainStatus,
    Conflict,
    DependencyType,
)


class DependencyManager:
    """Manage cross-chain dependencies."""

    def __init__(self):
        # Chain specifications by chain_id
        self.chain_specs: dict[str, ChainSpec] = {}
        # Chain execution statuses by chain_id
        self.chain_statuses: dict[str, ChainStatus] = {}
        # Forward graph: chain_id -> set of dependent chain_ids
        self.forward_graph: dict[str, set[str]] = defaultdict(set)
        # Reverse graph: chain_id -> set of dependency chain_ids
        self.reverse_graph: dict[str, set[str]] = defaultdict(set)
        # Provided features: feature_name -> chain_id
        self.feature_providers: dict[str, str] = {}
        logger.info("DependencyManager initialized")

    def register_chain(self, spec: ChainSpec) -> None:
        """
        Register a chain with its dependencies.

        Args:
            spec: The chain specification to register
        """
        if spec.chain_id in self.chain_specs:
            logger.warning(f"Chain {spec.chain_id} already registered, overwriting")

        self.chain_specs[spec.chain_id] = spec
        # Initialize status as pending
        if spec.chain_id not in self.chain_statuses:
            self.chain_statuses[spec.chain_id] = ChainStatus.PENDING

        # Register provided features
        for feature in spec.provides:
            self.feature_providers[feature.name] = spec.chain_id

        # Build dependency graph
        for dep in spec.depends_on:
            # Add edge from dependency to this chain
            self.forward_graph[dep.target_chain_id].add(spec.chain_id)
            # Add edge from this chain to its dependencies
            self.reverse_graph[spec.chain_id].add(dep.target_chain_id)

        logger.debug(f"Registered chain {spec.chain_id} with {len(spec.depends_on)} dependencies")

    def unregister_chain(self, chain_id: str) -> None:
        """
        Unregister a chain and its dependencies.

        Args:
            chain_id: The chain ID to unregister
        """
        if chain_id not in self.chain_specs:
            logger.warning(f"Chain {chain_id} not found, cannot unregister")
            return

        spec = self.chain_specs[chain_id]

        # Remove status
        if chain_id in self.chain_statuses:
            del self.chain_statuses[chain_id]

        # Remove provided features
        for feature in spec.provides:
            if self.feature_providers.get(feature.name) == chain_id:
                del self.feature_providers[feature.name]

        # Remove from graphs
        for dep in spec.depends_on:
            self.forward_graph[dep.target_chain_id].discard(chain_id)
        self.reverse_graph[chain_id].clear()
        for dependent in list(self.forward_graph[chain_id]):
            dependent_spec = self.chain_specs.get(dependent)
            if dependent_spec:
                dependent_spec.depends_on = [
                    d for d in dependent_spec.depends_on if d.target_chain_id != chain_id
                ]
        self.forward_graph[chain_id].clear()

        del self.chain_specs[chain_id]
        logger.debug(f"Unregistered chain {chain_id}")

    def update_chain_status(self, chain_id: str, status: ChainStatus) -> None:
        """
        Update the status of a chain.

        Args:
            chain_id: The chain ID
            status: The new status
        """
        if chain_id not in self.chain_specs:
            logger.warning(f"Chain {chain_id} not registered, cannot update status")
            return

        self.chain_statuses[chain_id] = status
        logger.debug(f"Updated chain {chain_id} status to {status.value}")

    def can_start(self, chain_id: str) -> tuple[bool, list[str]]:
        """
        Check if a chain can start (all dependencies satisfied).

        Args:
            chain_id: The chain to check

        Returns:
            Tuple of (can_start, list of blocking chain_ids)
        """
        if chain_id not in self.chain_specs:
            return False, [f"Chain {chain_id} not registered"]

        spec = self.chain_specs[chain_id]
        blocking = []

        for dep in spec.depends_on:
            if dep.target_chain_id not in self.chain_specs:
                blocking.append(f"Dependency {dep.target_chain_id} not registered")
                continue

            # Check if dependency is satisfied based on type
            if dep.dependency_type == DependencyType.BLOCKED_BY:
                # Must complete before this chain can start
                dep_status = self.chain_statuses.get(dep.target_chain_id)
                if dep_status != ChainStatus.COMPLETED:
                    blocking.append(dep.target_chain_id)

        return len(blocking) == 0, blocking

    def get_execution_order(self, chain_ids: list[str], strategy: str = "topological") -> list[str]:
        """
        Get safe execution order for multiple chains.

        Args:
            chain_ids: List of chain IDs to order
            strategy: Ordering strategy (topological, parallel, priority)

        Returns:
            List of chain IDs in execution order
        """
        if not chain_ids:
            return []

        if strategy == "parallel":
            return self._get_parallel_order(chain_ids)
        elif strategy == "priority":
            return self._get_priority_order(chain_ids)
        else:
            return self._get_topological_order(chain_ids)

    def _get_topological_order(self, chain_ids: list[str]) -> list[str]:
        """
        Get topological sort order for chain execution.

        Uses Kahn's algorithm for topological sorting.
        """
        # Filter to only registered chains
        valid_ids = [cid for cid in chain_ids if cid in self.chain_specs]
        if not valid_ids:
            return []

        # Build subgraph for requested chains
        in_degree: dict[str, int] = {cid: 0 for cid in valid_ids}
        dependencies: dict[str, set[str]] = {cid: set() for cid in valid_ids}

        for cid in valid_ids:
            spec = self.chain_specs[cid]
            for dep in spec.depends_on:
                if dep.target_chain_id in valid_ids:
                    dependencies[cid].add(dep.target_chain_id)
                    in_degree[cid] += 1

        # Kahn's algorithm
        queue = deque([cid for cid in valid_ids if in_degree[cid] == 0])
        result = []

        while queue:
            current = queue.popleft()
            result.append(current)

            # Find chains that depend on current
            for dependent in valid_ids:
                if current in dependencies[dependent]:
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        queue.append(dependent)

        # Check for cycles
        if len(result) != len(valid_ids):
            remaining = set(valid_ids) - set(result)
            logger.warning(f"Cycle detected involving chains: {remaining}")
            # Add remaining chains in priority order (arbitrary but deterministic)
            result.extend(sorted(remaining))

        return result

    def _get_parallel_order(self, chain_ids: list[str]) -> list[str]:
        """
        Get order that maximizes parallel execution.

        Groups independent chains together.
        """
        if not chain_ids:
            return []

        # Get topological order first
        topo_order = self._get_topological_order(chain_ids)

        # Group into waves
        waves: list[list[str]] = []
        completed: set[str] = set()

        for chain_id in topo_order:
            spec = self.chain_specs[chain_id]
            # Check if all dependencies are in completed
            deps_satisfied = all(
                dep.target_chain_id in completed
                for dep in spec.depends_on
                if dep.target_chain_id in self.chain_specs
            )

            if deps_satisfied:
                # Add to current wave or create new wave
                wave_sets = [
                    self.forward_graph.get(w, set()) or set() for wave in waves for w in wave
                ]
                if waves and all(chain_id not in ws for ws in wave_sets):
                    waves[-1].append(chain_id)
                else:
                    waves.append([chain_id])
                completed.add(chain_id)

        # Flatten waves with separator markers
        result = []
        for i, wave in enumerate(waves):
            if i > 0:
                result.append(f"=== WAVE {i} ===")
            result.extend(wave)

        return result

    def _get_priority_order(self, chain_ids: list[str]) -> list[str]:
        """
        Get order based on priority (higher priority first).
        """
        if not chain_ids:
            return []

        # Get valid chain specs
        valid_specs = [(cid, self.chain_specs[cid]) for cid in chain_ids if cid in self.chain_specs]

        # Sort by priority (higher first), then by chain_id for determinism
        sorted_specs = sorted(valid_specs, key=lambda x: (-x[1].priority, x[0]))

        # Get topological order within same priority
        priority_groups: dict[int, list[str]] = defaultdict(list)
        for cid, spec in sorted_specs:
            priority_groups[spec.priority].append(cid)

        # Order each priority group topologically
        result = []
        for priority in sorted(priority_groups.keys(), reverse=True):
            group_order = self._get_topological_order(priority_groups[priority])
            result.extend(group_order)

        return result

    def get_dependency_tree(self, chain_id: str) -> dict[str, Any]:
        """
        Get the dependency tree for a chain.

        Args:
            chain_id: The chain to get dependencies for

        Returns:
            Dict representing the dependency tree
        """
        if chain_id not in self.chain_specs:
            return {"error": f"Chain {chain_id} not found"}

        def build_tree(cid: str, depth: int = 0, visited: set[str] | None = None) -> dict:
            if visited is None:
                visited = set()
            if cid in visited:
                return {"id": cid, "circular": True}
            visited.add(cid)

            spec = self.chain_specs.get(cid)
            if not spec:
                return {"id": cid, "error": "not registered"}

            return {
                "id": cid,
                "task_type": spec.task_type.value,
                "description": spec.description,
                "depends_on": [
                    build_tree(dep.target_chain_id, depth + 1, visited.copy())
                    for dep in spec.depends_on
                    if dep.target_chain_id in self.chain_specs
                ],
                "provides": [f.name for f in spec.provides],
            }

        return build_tree(chain_id)

    def find_chain_by_feature(self, feature_name: str) -> str | None:
        """
        Find a chain that provides a specific feature.

        Args:
            feature_name: The feature name to find

        Returns:
            Chain ID that provides the feature, or None
        """
        return self.feature_providers.get(feature_name)

    def get_blocked_chains(self) -> dict[str, list[str]]:
        """
        Get all chains that are blocked by unmet dependencies.

        Returns:
            Dict mapping blocked chain_id to list of blocking chain_ids
        """
        blocked = {}
        for chain_id in self.chain_specs:
            can_start, blocking = self.can_start(chain_id)
            if not can_start:
                blocked[chain_id] = blocking
        return blocked


class ConflictDetector:
    """Detect conflicts between chains."""

    # Common conflict patterns
    CONFLICT_PATTERNS: dict[str, dict[str, Any]] = {
        "file_overwrite": {
            "description": "Both chains modify the same file",
            "severity": "high",
            "resolution": "Sequential execution or merge strategy",
        },
        "api_conflict": {
            "description": "Both modify the same API endpoint",
            "severity": "critical",
            "resolution": "Coordinate changes or implement versioning",
        },
        "schema_conflict": {
            "description": "Both change the same data schema",
            "severity": "critical",
            "resolution": "Schema migration strategy required",
        },
        "resource_conflict": {
            "description": "Both require exclusive resource access",
            "severity": "high",
            "resolution": "Sequential execution",
        },
        "breaking_change": {
            "description": "One chain introduces breaking changes",
            "severity": "critical",
            "resolution": "Deprecation strategy or feature flag",
        },
    }

    def detect_conflicts(self, chain_a: ChainSpec, chain_b: ChainSpec) -> list[Conflict]:
        """
        Detect conflicts between two chains.

        Args:
            chain_a: First chain specification
            chain_b: Second chain specification

        Returns:
            List of detected conflicts
        """
        conflicts = []

        # Check for file conflicts (would need file tracking in real impl)
        # For now, use description-based heuristics
        if self._similar_description(chain_a.description, chain_b.description):
            if chain_a.task_type == chain_b.task_type:
                conflicts.append(
                    Conflict(
                        conflict_type="duplicate_work",
                        chain_a=chain_a.chain_id,
                        chain_b=chain_b.chain_id,
                        description=f"Chains appear to target the same functionality: {chain_a.description[:50]}...",
                        resolution_suggestion="Consider merging or canceling one chain",
                    )
                )

        # Check for breaking change potential
        if self._introduces_breaking_change(chain_a) and self._introduces_breaking_change(chain_b):
            conflicts.append(
                Conflict(
                    conflict_type="breaking_change",
                    chain_a=chain_a.chain_id,
                    chain_b=chain_b.chain_id,
                    description="Both chains may introduce breaking changes",
                    resolution_suggestion="Implement feature flags or versioning",
                )
            )

        # Check for API conflicts
        if self._modifies_api(chain_a) and self._modifies_api(chain_b):
            conflicts.append(
                Conflict(
                    conflict_type="api_conflict",
                    chain_a=chain_a.chain_id,
                    chain_b=chain_b.chain_id,
                    description="Both chains may modify API endpoints",
                    resolution_suggestion="Coordinate API changes or use versioning",
                )
            )

        return conflicts

    def _similar_description(self, desc_a: str, desc_b: str, threshold: float = 0.7) -> bool:
        """Check if two descriptions are similar."""
        words_a = set(desc_a.lower().split())
        words_b = set(desc_b.lower().split())

        if not words_a or not words_b:
            return False

        intersection = words_a & words_b
        union = words_a | words_b

        jaccard = len(intersection) / len(union)
        return jaccard >= threshold

    def _introduces_breaking_change(self, spec: ChainSpec) -> bool:
        """Check if a chain likely introduces breaking changes."""
        breaking_keywords = ["refactor", "redesign", "breaking", "migration", "deprecation"]
        return any(kw in spec.description.lower() for kw in breaking_keywords)

    def _modifies_api(self, spec: ChainSpec) -> bool:
        """Check if a chain likely modifies an API."""
        api_keywords = ["api", "endpoint", "route", "endpoint", "rest", "graphql"]
        return any(kw in spec.description.lower() for kw in api_keywords)

    def detect_all_conflicts(self, specs: list[ChainSpec]) -> dict[tuple[str, str], list[Conflict]]:
        """
        Detect all conflicts in a list of chains.

        Args:
            specs: List of chain specifications

        Returns:
            Dict mapping chain pairs to their conflicts
        """
        conflicts: dict[tuple[str, str], list[Conflict]] = {}

        for i, spec_a in enumerate(specs):
            for spec_b in specs[i + 1 :]:
                pair_conflicts = self.detect_conflicts(spec_a, spec_b)
                if pair_conflicts:
                    key = (spec_a.chain_id, spec_b.chain_id)
                    conflicts[key] = pair_conflicts

        return conflicts

    def suggest_resolution(self, conflict: Conflict) -> str:
        """
        Suggest a resolution for a conflict.

        Args:
            conflict: The conflict to resolve

        Returns:
            Resolution suggestion
        """
        pattern = self.CONFLICT_PATTERNS.get(conflict.conflict_type, {})
        return pattern.get("resolution", "Manual review required")
