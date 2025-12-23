"""
Tenant domain entity.

Represents a tenant in a multi-tenant CasareRPA deployment.
Tenants have isolated robot fleets, workflows, and API keys.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Set
from uuid import uuid4


@dataclass(frozen=True)
class TenantId:
    """Value Object: Tenant identifier."""

    value: str

    def __post_init__(self) -> None:
        if not self.value or not self.value.strip():
            raise ValueError("TenantId cannot be empty")

    @classmethod
    def generate(cls) -> "TenantId":
        """Generate a new unique TenantId."""
        return cls(str(uuid4()))

    def __str__(self) -> str:
        return self.value


@dataclass
class TenantSettings:
    """Settings for a tenant."""

    max_robots: int = 10
    max_concurrent_jobs: int = 20
    allowed_capabilities: List[str] = field(default_factory=list)
    max_api_keys_per_robot: int = 5
    job_retention_days: int = 30
    enable_audit_logging: bool = True
    custom_settings: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.max_robots < 0:
            raise ValueError(f"max_robots must be >= 0, got {self.max_robots}")
        if self.max_concurrent_jobs < 0:
            raise ValueError(f"max_concurrent_jobs must be >= 0, got {self.max_concurrent_jobs}")
        if self.max_api_keys_per_robot < 1:
            raise ValueError(
                f"max_api_keys_per_robot must be >= 1, got {self.max_api_keys_per_robot}"
            )
        if self.job_retention_days < 1:
            raise ValueError(f"job_retention_days must be >= 1, got {self.job_retention_days}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "max_robots": self.max_robots,
            "max_concurrent_jobs": self.max_concurrent_jobs,
            "allowed_capabilities": self.allowed_capabilities,
            "max_api_keys_per_robot": self.max_api_keys_per_robot,
            "job_retention_days": self.job_retention_days,
            "enable_audit_logging": self.enable_audit_logging,
            "custom_settings": self.custom_settings,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TenantSettings":
        """Create from dictionary."""
        return cls(
            max_robots=data.get("max_robots", 10),
            max_concurrent_jobs=data.get("max_concurrent_jobs", 20),
            allowed_capabilities=data.get("allowed_capabilities", []),
            max_api_keys_per_robot=data.get("max_api_keys_per_robot", 5),
            job_retention_days=data.get("job_retention_days", 30),
            enable_audit_logging=data.get("enable_audit_logging", True),
            custom_settings=data.get("custom_settings", {}),
        )


@dataclass
class Tenant:
    """
    Tenant domain entity.

    Represents an organization or client in a multi-tenant deployment.
    Each tenant has isolated robots, workflows, and API keys.
    """

    id: TenantId
    name: str
    settings: TenantSettings = field(default_factory=TenantSettings)
    admin_emails: List[str] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_active: bool = True
    description: str = ""
    contact_email: Optional[str] = None
    # Robot IDs belonging to this tenant
    robot_ids: Set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        """Validate domain invariants."""
        if isinstance(self.id, str):
            object.__setattr__(self, "id", TenantId(self.id))
        if not self.name or not self.name.strip():
            raise ValueError("Tenant name cannot be empty")
        if self.created_at is None:
            object.__setattr__(self, "created_at", datetime.now(timezone.utc))

    @property
    def robot_count(self) -> int:
        """Get count of robots in this tenant."""
        return len(self.robot_ids)

    @property
    def can_add_robot(self) -> bool:
        """Check if tenant can add more robots."""
        return self.robot_count < self.settings.max_robots

    def add_robot(self, robot_id: str) -> None:
        """
        Add a robot to this tenant.

        Args:
            robot_id: ID of robot to add.

        Raises:
            ValueError: If tenant is at robot capacity.
        """
        if not self.can_add_robot:
            raise ValueError(
                f"Tenant {self.name} has reached max robots ({self.settings.max_robots})"
            )
        self.robot_ids.add(robot_id)
        self.updated_at = datetime.now(timezone.utc)

    def remove_robot(self, robot_id: str) -> None:
        """
        Remove a robot from this tenant.

        Args:
            robot_id: ID of robot to remove.
        """
        self.robot_ids.discard(robot_id)
        self.updated_at = datetime.now(timezone.utc)

    def has_robot(self, robot_id: str) -> bool:
        """Check if robot belongs to this tenant."""
        return robot_id in self.robot_ids

    def add_admin(self, email: str) -> None:
        """Add an admin email to the tenant."""
        email = email.lower().strip()
        if email and email not in self.admin_emails:
            self.admin_emails.append(email)
            self.updated_at = datetime.now(timezone.utc)

    def remove_admin(self, email: str) -> None:
        """Remove an admin email from the tenant."""
        email = email.lower().strip()
        if email in self.admin_emails:
            self.admin_emails.remove(email)
            self.updated_at = datetime.now(timezone.utc)

    def is_admin(self, email: str) -> bool:
        """Check if email is an admin of this tenant."""
        return email.lower().strip() in self.admin_emails

    def deactivate(self) -> None:
        """Deactivate the tenant (soft delete)."""
        self.is_active = False
        self.updated_at = datetime.now(timezone.utc)

    def activate(self) -> None:
        """Activate the tenant."""
        self.is_active = True
        self.updated_at = datetime.now(timezone.utc)

    def update_settings(self, settings: TenantSettings) -> None:
        """Update tenant settings."""
        self.settings = settings
        self.updated_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "settings": self.settings.to_dict(),
            "admin_emails": self.admin_emails,
            "contact_email": self.contact_email,
            "robot_ids": list(self.robot_ids),
            "robot_count": self.robot_count,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Tenant":
        """Create Tenant from dictionary."""
        from casare_rpa.utils.datetime_helpers import parse_datetime

        settings = data.get("settings", {})
        if isinstance(settings, dict):
            settings = TenantSettings.from_dict(settings)

        robot_ids = data.get("robot_ids", [])
        if isinstance(robot_ids, list):
            robot_ids = set(robot_ids)

        return cls(
            id=TenantId(data["id"]),
            name=data["name"],
            description=data.get("description", ""),
            settings=settings,
            admin_emails=data.get("admin_emails", []),
            contact_email=data.get("contact_email"),
            robot_ids=robot_ids,
            is_active=data.get("is_active", True),
            created_at=parse_datetime(data.get("created_at")),
            updated_at=parse_datetime(data.get("updated_at")),
        )

    def __repr__(self) -> str:
        return f"Tenant(id={self.id}, name={self.name!r}, robots={self.robot_count})"


__all__ = [
    "Tenant",
    "TenantId",
    "TenantSettings",
]
