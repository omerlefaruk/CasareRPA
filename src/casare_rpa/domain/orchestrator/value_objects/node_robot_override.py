"""NodeRobotOverride value object for node-level robot routing."""

from dataclasses import dataclass, field
from datetime import datetime

from casare_rpa.domain.orchestrator.entities.robot import RobotCapability
from casare_rpa.utils.datetime_helpers import parse_datetime


@dataclass(frozen=True)
class NodeRobotOverride:
    """Value object for node-level robot override within a workflow.

    NodeRobotOverride allows specific nodes within a workflow to target a
    different robot than the workflow's default. This is useful for:
    - Nodes requiring specific capabilities (GPU, desktop automation)
    - Load balancing specific heavy operations
    - Routing sensitive operations to secure robots

    When a node has an override, the RobotSelectionService will use the
    override's robot_id instead of the workflow's default assignment.

    Attributes:
        workflow_id: ID of the workflow containing the node.
        node_id: ID of the node to override.
        robot_id: ID of the specific robot to use (None = use capability matching).
        required_capabilities: Capabilities required (if robot_id is None).
        reason: Human-readable explanation for the override.
        created_at: When this override was created.
        created_by: User/system that created this override.
        is_active: Whether this override is currently active.
    """

    workflow_id: str
    node_id: str
    robot_id: str | None = None
    required_capabilities: frozenset = field(default_factory=frozenset)
    reason: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str = ""
    is_active: bool = True

    def __post_init__(self):
        """Validate override invariants."""
        if not self.workflow_id or not self.workflow_id.strip():
            raise ValueError("workflow_id cannot be empty")
        if not self.node_id or not self.node_id.strip():
            raise ValueError("node_id cannot be empty")
        # Must have either robot_id or required_capabilities
        if self.robot_id is None and not self.required_capabilities:
            raise ValueError("Must specify either robot_id or required_capabilities for override")

    @property
    def is_specific_robot(self) -> bool:
        """Check if this override targets a specific robot.

        Returns:
            True if override specifies a robot_id, False if capability-based.
        """
        return self.robot_id is not None

    @property
    def is_capability_based(self) -> bool:
        """Check if this override is based on required capabilities.

        Returns:
            True if override uses capability matching, False if specific robot.
        """
        return self.robot_id is None and bool(self.required_capabilities)

    def to_dict(self) -> dict:
        """Serialize override to dictionary.

        Returns:
            Dictionary representation of the override.
        """
        return {
            "workflow_id": self.workflow_id,
            "node_id": self.node_id,
            "robot_id": self.robot_id,
            "required_capabilities": [
                cap.value if isinstance(cap, RobotCapability) else cap
                for cap in self.required_capabilities
            ],
            "reason": self.reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "created_by": self.created_by,
            "is_active": self.is_active,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "NodeRobotOverride":
        """Create NodeRobotOverride from dictionary.

        Args:
            data: Dictionary with override data.

        Returns:
            NodeRobotOverride instance.
        """
        created_at = parse_datetime(data.get("created_at"))
        if created_at is None:
            created_at = datetime.utcnow()

        # Parse capabilities
        raw_capabilities = data.get("required_capabilities", [])
        capabilities: set[RobotCapability] = set()
        for cap in raw_capabilities:
            if isinstance(cap, str):
                try:
                    capabilities.add(RobotCapability(cap))
                except ValueError:
                    pass  # Skip unknown capabilities
            elif isinstance(cap, RobotCapability):
                capabilities.add(cap)

        return cls(
            workflow_id=data["workflow_id"],
            node_id=data["node_id"],
            robot_id=data.get("robot_id"),
            required_capabilities=frozenset(capabilities),
            reason=data.get("reason"),
            created_at=created_at,
            created_by=data.get("created_by", ""),
            is_active=data.get("is_active", True),
        )

    def __repr__(self) -> str:
        """String representation."""
        target = self.robot_id or f"caps:{list(self.required_capabilities)}"
        return (
            f"NodeRobotOverride(workflow_id={self.workflow_id!r}, "
            f"node_id={self.node_id!r}, target={target})"
        )
