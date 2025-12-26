"""
Chain executor service for orchestrating multi-agent workflows.

This service coordinates agent execution based on task type,
handles loop-based error recovery, and manages gates.

Test Strategy:
- Use MockAgentOrchestrator to control agent outputs
- Test sequencing, loops, gates, and parallel execution
- Never spawn real AI agents in tests
"""

import asyncio
import time
from dataclasses import dataclass, field

from loguru import logger

from casare_rpa.domain.entities.chain import (
    CHAIN_TEMPLATES,
    AgentResult,
    AgentType,
    ChainConfig,
    ChainResult,
    ChainStatus,
    TaskType,
)
from casare_rpa.domain.interfaces.agent_orchestrator import IAgentOrchestrator

# Parallel chain templates: each phase is a list of agents that can run in parallel
PARALLEL_CHAIN_TEMPLATES: dict[TaskType, list[list[AgentType]]] = {
    TaskType.IMPLEMENT: [
        # Phase 1: Parallel exploration (domain, tests, patterns)
        [AgentType.EXPLORE, AgentType.EXPLORE, AgentType.EXPLORE],
        # Phase 2: Architecture (uses explore results)
        [AgentType.ARCHITECT],
        # Phase 3: Parallel implementation (backend, UI, integrations)
        [AgentType.BUILDER, AgentType.UI, AgentType.INTEGRATIONS],
        # Phase 4: Parallel validation (tests, docs)
        [AgentType.QUALITY, AgentType.DOCS],
        # Phase 5: Review
        [AgentType.REVIEWER],
    ],
    TaskType.EXTEND: [
        # Phase 1: Explore
        [AgentType.EXPLORE],
        # Phase 2: Architecture
        [AgentType.ARCHITECT],
        # Phase 3: Parallel implementation
        [AgentType.BUILDER, AgentType.UI],
        # Phase 4: Validation
        [AgentType.QUALITY],
        # Phase 5: Review
        [AgentType.REVIEWER],
    ],
    TaskType.UI: [
        # Phase 1: Explore
        [AgentType.EXPLORE],
        # Phase 2: UI implementation
        [AgentType.UI],
        # Phase 3: Validation
        [AgentType.QUALITY],
        # Phase 4: Review
        [AgentType.REVIEWER],
    ],
    TaskType.INTEGRATION: [
        # Phase 1: Explore
        [AgentType.EXPLORE],
        # Phase 2: Integration
        [AgentType.INTEGRATIONS],
        # Phase 3: Validation
        [AgentType.QUALITY],
        # Phase 4: Review
        [AgentType.REVIEWER],
    ],
    TaskType.FIX: [
        # Phase 1: Explore
        [AgentType.EXPLORE],
        # Phase 2: Fix
        [AgentType.BUILDER],
        # Phase 3: Validation
        [AgentType.QUALITY],
        # Phase 4: Review
        [AgentType.REVIEWER],
    ],
    TaskType.REFACTOR: [
        # Phase 1: Explore
        [AgentType.EXPLORE],
        # Phase 2: Refactor
        [AgentType.REFACTOR],
        # Phase 3: Validation
        [AgentType.QUALITY],
        # Phase 4: Review
        [AgentType.REVIEWER],
    ],
}


@dataclass
class ChainMetrics:
    """Metrics collected during chain execution."""

    start_time: float = 0.0
    end_time: float = 0.0
    iterations: int = 0
    agent_calls: dict[AgentType, int] = field(default_factory=dict)
    total_tokens: int = 0


class ChainClassifier:
    """Classifies user requests into task types."""

    # Keywords that map to task types
    # Order matters: more specific keywords first
    KEYWORD_MAP: dict[str, TaskType] = {
        # DOCS (most specific - before api)
        "document": TaskType.DOCS,
        "docs": TaskType.DOCS,
        # UI (before create/build)
        "ui": TaskType.UI,
        "interface": TaskType.UI,
        # FIX
        "bug": TaskType.FIX,
        "debug": TaskType.FIX,
        "repair": TaskType.FIX,
        # Security
        "security": TaskType.SECURITY,
        "audit": TaskType.SECURITY,
        # Integration
        "integration": TaskType.INTEGRATION,
        "api": TaskType.INTEGRATION,
        # REFACTOR
        "refactor": TaskType.REFACTOR,
        "clean": TaskType.REFACTOR,
        "optimize": TaskType.REFACTOR,
        # RESEARCH
        "research": TaskType.RESEARCH,
        "investigate": TaskType.RESEARCH,
        "analyze": TaskType.RESEARCH,
        # EXTEND
        "enhance": TaskType.EXTEND,
        "extend": TaskType.EXTEND,
        # CLONE
        "clone": TaskType.CLONE,
        "duplicate": TaskType.CLONE,
        "copy": TaskType.CLONE,
        # TEST
        "test": TaskType.TEST,
        "verify": TaskType.TEST,
        # FIX
        "fix": TaskType.FIX,
        # IMPLEMENT (must be last - most generic)
        "implement": TaskType.IMPLEMENT,
        "add": TaskType.IMPLEMENT,
        "create": TaskType.IMPLEMENT,
        "build": TaskType.IMPLEMENT,
        "new": TaskType.IMPLEMENT,
    }

    @classmethod
    def classify(cls, description: str, explicit_type: TaskType | None = None) -> TaskType:
        """
        Classify a description into a task type.

        Args:
            description: The task description
            explicit_type: If provided, skips classification

        Returns:
            The classified TaskType
        """
        if explicit_type:
            return explicit_type

        desc_lower = description.lower()

        # Check for explicit keywords with word boundary matching
        import re

        for keyword, task_type in cls.KEYWORD_MAP.items():
            # Use word boundary to avoid "ui" matching "build"
            pattern = r"\b" + re.escape(keyword) + r"\b"
            if re.search(pattern, desc_lower):
                return task_type

        # Default: IMPLEMENT for "create/add" patterns
        if any(word in desc_lower for word in ["new", "feature", "node", "component"]):
            return TaskType.IMPLEMENT

        # Fallback
        return TaskType.IMPLEMENT


class ChainExecutor:
    """
    Orchestrates multi-agent chain execution with loop recovery.

    Responsibilities:
    - Classify task type
    - Execute agents in sequence
    - Handle parallel execution
    - Loop on reviewer issues
    - Manage approval gates
    """

    def __init__(
        self,
        orchestrator: IAgentOrchestrator,
        default_max_iterations: int = 3,
        enable_parallel: bool = False,
    ):
        """
        Initialize the chain executor.

        Args:
            orchestrator: Agent orchestrator (real or mock)
            default_max_iterations: Default max loop iterations
            enable_parallel: Enable parallel execution of compatible agents
        """
        self.orchestrator = orchestrator
        self.default_max_iterations = default_max_iterations
        self.enable_parallel = enable_parallel
        self.metrics = ChainMetrics()

    def classify(self, description: str, task_type: TaskType | None = None) -> TaskType:
        """
        Classify a description into a task type.

        Args:
            description: The task description
            task_type: Optional explicit task type

        Returns:
            The classified TaskType
        """
        return ChainClassifier.classify(description, task_type)

    def get_chain_template(self, task_type: TaskType) -> list[AgentType]:
        """
        Get the agent chain for a task type.

        Args:
            task_type: The type of task

        Returns:
            List of agent types in execution order
        """
        return CHAIN_TEMPLATES.get(task_type, CHAIN_TEMPLATES[TaskType.IMPLEMENT])

    async def execute(
        self,
        description: str,
        task_type: TaskType | None = None,
        max_iterations: int | None = None,
        dry_run: bool = False,
        parallel: bool | None = None,
        **config_kwargs: object,
    ) -> ChainResult:
        """
        Execute a chain for the given description.

        Args:
            description: Task description
            task_type: Optional explicit task type
            max_iterations: Override max iterations
            dry_run: Preview without execution
            parallel: Override parallel setting (None = use instance setting)
            **config_kwargs: Additional config options

        Returns:
            ChainResult with execution outcome
        """
        # Determine if parallel execution should be used
        use_parallel = parallel if parallel is not None else self.enable_parallel

        # Classify task type
        classified_type = self.classify(description, task_type)

        # Build configuration
        config = ChainConfig(
            task_type=classified_type,
            description=description,
            max_iterations=max_iterations or self.default_max_iterations,
            dry_run=dry_run,
            parallel_agents=use_parallel,
            **config_kwargs,  # type: ignore[arg-type]
        )

        # Initialize result
        result = ChainResult(
            task_type=classified_type,
            status=ChainStatus.RUNNING,
        )

        # Dry run: show the plan
        if dry_run:
            result.status = ChainStatus.PENDING
            if use_parallel:
                result.message = self._format_parallel_plan(classified_type)
            else:
                result.message = f"Would execute: {self.get_chain_template(classified_type)}"
            return result

        # Start execution
        self.metrics = ChainMetrics(start_time=time.time())

        try:
            if use_parallel:
                result = await self._execute_parallel_chain(classified_type, config, result)
            else:
                chain = self.get_chain_template(classified_type)
                result = await self._execute_chain(chain, config, result)
        except Exception as e:
            result.status = ChainStatus.FAILED
            result.message = f"Chain failed: {e}"
        finally:
            self.metrics.end_time = time.time()

        result.total_time_ms = int((self.metrics.end_time - self.metrics.start_time) * 1000)
        result.iterations = self.metrics.iterations

        return result

    async def _execute_chain(
        self,
        chain: list[AgentType],
        config: ChainConfig,
        result: ChainResult,
    ) -> ChainResult:
        """
        Execute the agent chain with loop recovery.

        Args:
            chain: List of agent types to execute
            config: Chain configuration
            result: Current result object

        Returns:
            Updated ChainResult
        """
        # Check if chain has REVIEWER (determines if we loop)
        has_reviewer = AgentType.REVIEWER in chain

        # Chains without REVIEWER (like RESEARCH) run once, no loop
        if not has_reviewer:
            return await self._execute_chain_once(chain, config, result)

        # Chains with REVIEWER support loop recovery
        return await self._execute_chain_with_loop(chain, config, result)

    async def _execute_chain_once(
        self,
        chain: list[AgentType],
        config: ChainConfig,
        result: ChainResult,
    ) -> ChainResult:
        """
        Execute a chain once (no loop recovery).

        Used for chains like RESEARCH that don't have a REVIEWER.

        Args:
            chain: List of agent types to execute
            config: Chain configuration
            result: Current result object

        Returns:
            Updated ChainResult
        """
        for agent_type in chain:
            agent_result = await self._execute_agent(agent_type, config, result)
            result.agent_results[agent_type] = agent_result

            # Track agent calls
            self.metrics.agent_calls[agent_type] = self.metrics.agent_calls.get(agent_type, 0) + 1

            # Handle approval gates
            if agent_result.requires_approval:
                approved = await self.orchestrator.request_approval(
                    agent_type,
                    f"Review plan for {config.description}",
                    {"data": agent_result.data},
                )
                if not approved:
                    result.status = ChainStatus.HALTED
                    result.message = "Plan rejected by user"
                    return result

        result.status = ChainStatus.APPROVED
        result.message = "Chain completed successfully"
        return result

    async def _execute_chain_with_loop(
        self,
        chain: list[AgentType],
        config: ChainConfig,
        result: ChainResult,
    ) -> ChainResult:
        """
        Execute a chain with loop recovery on reviewer issues.

        Args:
            chain: List of agent types to execute (must include REVIEWER)
            config: Chain configuration
            result: Current result object

        Returns:
            Updated ChainResult
        """
        iteration = 0

        # Find the index of agents to repeat on loop (after ARCHITECT)
        # Loop only repeats from BUILDER onward, not EXPLORE or ARCHITECT
        loop_start_index = 0
        for i, agent_type in enumerate(chain):
            if agent_type == AgentType.BUILDER:
                loop_start_index = i
                break
            elif agent_type == AgentType.ARCHITECT:
                # Next agent after ARCHITECT is the loop start
                loop_start_index = i + 1
                break

        # First iteration: run full chain
        while iteration < config.max_iterations:
            iteration += 1
            self.metrics.iterations = iteration

            # On subsequent iterations, only run from loop_start_index
            start_index = 0 if iteration == 1 else loop_start_index

            # Execute each agent in the chain (or partial chain on loop)
            for agent_type in chain[start_index:]:
                agent_result = await self._execute_agent(agent_type, config, result)
                result.agent_results[agent_type] = agent_result

                # Track agent calls
                self.metrics.agent_calls[agent_type] = (
                    self.metrics.agent_calls.get(agent_type, 0) + 1
                )

                # Handle approval gates (before REVIEWER)
                if agent_result.requires_approval:
                    approved = await self.orchestrator.request_approval(
                        agent_type,
                        f"Review plan for {config.description}",
                        {"data": agent_result.data},
                    )
                    if not approved:
                        result.status = ChainStatus.HALTED
                        result.message = "Plan rejected by user"
                        return result

                # Check for reviewer decision (only on REVIEWER agent)
                if agent_type == AgentType.REVIEWER:
                    if agent_result.status == "APPROVED":
                        result.status = ChainStatus.APPROVED
                        result.message = "Chain completed successfully"
                        # Run DOCS phase after approval
                        await self._run_docs_phase(config, result)
                        return result
                    elif agent_result.status == "ISSUES":
                        if iteration >= config.max_iterations:
                            # Max iterations reached - escalate
                            result.status = ChainStatus.ESCALATED
                            result.issues = agent_result.issues
                            result.escalated_reason = (
                                f"Max iterations ({config.max_iterations}) exceeded"
                            )
                            return result
                        # Continue to next iteration for fixes
                        break

        # If we exit loop without approval, escalate
        result.status = ChainStatus.ESCALATED
        result.escalated_reason = f"Max iterations ({config.max_iterations}) exceeded"

        return result

    async def _execute_agent(
        self,
        agent_type: AgentType,
        config: ChainConfig,
        result: ChainResult,
    ) -> AgentResult:
        """
        Execute a single agent.

        Args:
            agent_type: Type of agent to execute
            config: Chain configuration
            result: Current chain result

        Returns:
            AgentResult from the agent execution
        """
        prompt = self._build_prompt(agent_type, config, result)

        start = time.time()
        agent_result = await self.orchestrator.launch(agent_type, prompt, config)
        agent_result.execution_time_ms = int((time.time() - start) * 1000)

        return agent_result

    async def _run_docs_phase(self, config: ChainConfig, result: ChainResult) -> None:
        """
        Run the DOCS phase after successful completion.

        Args:
            config: Chain configuration
            result: Current chain result
        """
        if config.task_type in [TaskType.RESEARCH, TaskType.TEST]:
            return  # No docs needed for these

        prompt = self._build_prompt(AgentType.DOCS, config, result)
        docs_result = await self.orchestrator.launch(AgentType.DOCS, prompt, config)
        result.agent_results[AgentType.DOCS] = docs_result

    def _build_prompt(
        self,
        agent_type: AgentType,
        config: ChainConfig,
        result: ChainResult,
    ) -> str:
        """
        Build the prompt for an agent.

        Args:
            agent_type: Type of agent
            config: Chain configuration
            result: Current chain result

        Returns:
            The prompt string
        """
        base_prompt = f"Task: {config.description}\n"

        # Add context from previous agents
        if result.agent_results:
            context_lines = ["\nPrevious agent outputs:"]
            for at, ar in result.agent_results.items():
                if ar.data:
                    context_lines.append(f"\n{at.value}: {ar.data}")
            base_prompt += "\n".join(context_lines)

        # Add iteration context for fix attempts
        if self.metrics.iterations > 1 and agent_type == AgentType.BUILDER:
            base_prompt += f"\n\nFIX ITERATION {self.metrics.iterations - 1}:"
            if result.issues:
                base_prompt += "\nIssues to fix:"
                for issue in result.issues:
                    base_prompt += f"\n- Line {issue.line}: {issue.description}"

        return base_prompt

    def can_run_parallel(self, agent_type: AgentType, other: AgentType) -> bool:
        """
        Check if two agent types can run in parallel.

        Args:
            agent_type: First agent type
            other: Second agent type

        Returns:
            True if agents can run in parallel
        """
        return self.orchestrator.can_run_parallel(agent_type, other)

    async def _execute_parallel_chain(
        self,
        task_type: TaskType,
        config: ChainConfig,
        result: ChainResult,
    ) -> ChainResult:
        """
        Execute a chain with parallel phases.

        Args:
            task_type: Type of task being executed
            config: Chain configuration
            result: Current result object

        Returns:
            Updated ChainResult
        """
        phases = PARALLEL_CHAIN_TEMPLATES.get(
            task_type,
            [[AgentType.EXPLORE, AgentType.BUILDER, AgentType.QUALITY, AgentType.REVIEWER]],
        )

        for phase_idx, phase_agents in enumerate(phases):
            logger.info(f"Phase {phase_idx + 1}/{len(phases)}: {[a.value for a in phase_agents]}")

            # Check if phase can run in parallel
            can_parallel = self._can_phase_run_parallel(phase_agents)

            if can_parallel and len(phase_agents) > 1:
                phase_results = await self._execute_parallel_phase(phase_agents, config, result)
            else:
                phase_results = await self._execute_sequential_phase(phase_agents, config, result)

            # Merge results
            for agent_result in phase_results:
                result.agent_results[agent_result.agent_type] = agent_result

                # Track metrics
                self.metrics.agent_calls[agent_result.agent_type] = (
                    self.metrics.agent_calls.get(agent_result.agent_type, 0) + 1
                )

            # Check for approval gates (after ARCHITECT)
            if AgentType.ARCHITECT in phase_agents:
                architect_result = result.agent_results.get(AgentType.ARCHITECT)
                if architect_result and architect_result.requires_approval:
                    approved = await self.orchestrator.request_approval(
                        AgentType.ARCHITECT,
                        f"Review plan for {config.description}",
                        {"data": architect_result.data},
                    )
                    if not approved:
                        result.status = ChainStatus.HALTED
                        result.message = "Plan rejected by user"
                        return result

            # Check for reviewer decision
            if AgentType.REVIEWER in phase_agents:
                reviewer_result = result.agent_results.get(AgentType.REVIEWER)
                if reviewer_result:
                    if reviewer_result.status == "APPROVED":
                        result.status = ChainStatus.APPROVED
                        result.message = "Parallel chain completed successfully"
                        return result
                    elif reviewer_result.status == "ISSUES":
                        result.status = ChainStatus.ESCALATED
                        result.issues = reviewer_result.issues
                        result.escalated_reason = "Review found issues"
                        return result

        result.status = ChainStatus.APPROVED
        result.message = "Parallel chain completed"
        return result

    async def _execute_parallel_phase(
        self,
        agent_types: list[AgentType],
        config: ChainConfig,
        result: ChainResult,
    ) -> list[AgentResult]:
        """
        Execute a phase of agents in parallel.

        Args:
            agent_types: List of agent types to execute
            config: Chain configuration
            result: Current chain result

        Returns:
            List of AgentResults
        """
        tasks = [self._execute_agent(agent_type, config, result) for agent_type in agent_types]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        processed_results = []
        for i, agent_result in enumerate(results):
            if isinstance(agent_result, Exception):
                logger.error(f"Agent {agent_types[i]} failed: {agent_result}")
                processed_results.append(
                    AgentResult(
                        success=False,
                        agent_type=agent_types[i],
                        error_message=str(agent_result),
                    )
                )
            else:
                processed_results.append(agent_result)

        return processed_results

    async def _execute_sequential_phase(
        self,
        agent_types: list[AgentType],
        config: ChainConfig,
        result: ChainResult,
    ) -> list[AgentResult]:
        """
        Execute a phase of agents sequentially.

        Args:
            agent_types: List of agent types to execute
            config: Chain configuration
            result: Current chain result

        Returns:
            List of AgentResults
        """
        results = []
        for agent_type in agent_types:
            agent_result = await self._execute_agent(agent_type, config, result)
            results.append(agent_result)
        return results

    def _can_phase_run_parallel(self, agent_types: list[AgentType]) -> bool:
        """
        Check if all agents in a phase can run in parallel.

        Args:
            agent_types: List of agent types to check

        Returns:
            True if all can run in parallel
        """
        for i, a1 in enumerate(agent_types):
            for a2 in agent_types[i + 1 :]:
                if not self.orchestrator.can_run_parallel(a1, a2):
                    return False
        return True

    def _format_parallel_plan(self, task_type: TaskType) -> str:
        """Format a parallel execution plan for display."""
        phases = PARALLEL_CHAIN_TEMPLATES.get(
            task_type,
            [[AgentType.EXPLORE, AgentType.BUILDER, AgentType.QUALITY, AgentType.REVIEWER]],
        )
        lines = [f"Parallel execution plan for {task_type.value}:"]
        for i, phase in enumerate(phases):
            agent_names = [a.value for a in phase]
            can_parallel = len(phase) > 1 and self._can_phase_run_parallel(phase)
            mode = "parallel" if can_parallel else "sequential"
            lines.append(f"  Phase {i + 1}: {', '.join(agent_names)} ({mode})")
        return "\n".join(lines)

    def get_parallel_plan(self, task_type: TaskType | None, description: str) -> str:
        """
        Get the parallel execution plan for a task.

        Args:
            task_type: Optional explicit task type
            description: Task description (for classification)

        Returns:
            Formatted execution plan
        """
        classified_type = self.classify(description, task_type)
        return self._format_parallel_plan(classified_type)
