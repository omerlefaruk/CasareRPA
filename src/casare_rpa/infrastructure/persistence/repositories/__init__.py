"""
CasareRPA - Infrastructure Persistence Repositories

Repository implementations for robot orchestration entities.
Supports PostgreSQL (asyncpg) and SQLite (aiosqlite) backends.
"""

from casare_rpa.infrastructure.persistence.repositories.api_key_repository import (
    ApiKeyRepository,
)
from casare_rpa.infrastructure.persistence.repositories.audit_repository import (
    AuditRepository,
    get_audit_repository,
)
from casare_rpa.infrastructure.persistence.repositories.job_repository import (
    JobRepository,
)
from casare_rpa.infrastructure.persistence.repositories.log_repository import (
    LogRepository,
)
from casare_rpa.infrastructure.persistence.repositories.node_override_repository import (
    NodeOverrideRepository,
)
from casare_rpa.infrastructure.persistence.repositories.robot_repository import (
    RobotRepository,
)
from casare_rpa.infrastructure.persistence.repositories.tenant_repository import (
    TenantRepository,
)
from casare_rpa.infrastructure.persistence.repositories.trace_repository import (
    TraceRepository,
)
from casare_rpa.infrastructure.persistence.repositories.user_repository import (
    UserRepository,
)
from casare_rpa.infrastructure.persistence.repositories.workflow_assignment_repository import (
    WorkflowAssignmentRepository,
)

__all__ = [
    "ApiKeyRepository",
    "AuditRepository",
    "get_audit_repository",
    "JobRepository",
    "LogRepository",
    "NodeOverrideRepository",
    "RobotRepository",
    "TenantRepository",
    "TraceRepository",
    "UserRepository",
    "WorkflowAssignmentRepository",
]
