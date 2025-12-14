"""Persistence layer for orchestrator."""

from casare_rpa.infrastructure.orchestrator.persistence.local_job_repository import (
    LocalJobRepository,
)
from casare_rpa.infrastructure.orchestrator.persistence.local_robot_repository import (
    LocalRobotRepository,
)
from casare_rpa.infrastructure.orchestrator.persistence.local_schedule_repository import (
    LocalScheduleRepository,
)
from casare_rpa.infrastructure.orchestrator.persistence.local_storage_repository import (
    LocalStorageRepository,
)
from casare_rpa.infrastructure.orchestrator.persistence.local_trigger_repository import (
    LocalTriggerRepository,
)
from casare_rpa.infrastructure.orchestrator.persistence.local_workflow_repository import (
    LocalWorkflowRepository,
)
from casare_rpa.infrastructure.orchestrator.persistence.pg_robot_repository import (
    PgRobotRepository,
    CREATE_ROBOTS_TABLE_SQL,
)

__all__ = [
    "LocalStorageRepository",
    "LocalJobRepository",
    "LocalRobotRepository",
    "LocalWorkflowRepository",
    "LocalScheduleRepository",
    "LocalTriggerRepository",
    # PostgreSQL repositories
    "PgRobotRepository",
    "CREATE_ROBOTS_TABLE_SQL",
]
