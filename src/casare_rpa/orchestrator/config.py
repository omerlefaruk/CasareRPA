"""
Orchestrator Configuration.

Defines configuration for the OrchestratorEngine, supporting both in-memory
and distributed (PgQueuer) queue backends.
"""

from typing import Optional
from pydantic import BaseModel, Field


class OrchestratorConfig(BaseModel):
    """
    Configuration for Orchestrator Engine.

    Attributes:
        use_pgqueuer: If True, use PgQueuer for distributed queue; otherwise use in-memory JobQueue
        postgres_url: PostgreSQL connection URL (required if use_pgqueuer=True)
        tenant_id: Tenant ID for multi-tenancy (optional)
        load_balancing: Robot selection strategy (round_robin, least_loaded, random, affinity)
        dispatch_interval: Seconds between dispatch attempts
        timeout_check_interval: Seconds between timeout checks
        default_job_timeout: Default job timeout in seconds
        trigger_webhook_port: Port for trigger webhook server

    Example:
        ```python
        # In-memory configuration (development)
        config = OrchestratorConfig(use_pgqueuer=False)

        # PgQueuer configuration (production)
        config = OrchestratorConfig(
            use_pgqueuer=True,
            postgres_url="postgresql://user:pass@localhost/casare_rpa",
            tenant_id="tenant-001"
        )
        ```
    """

    # Queue Backend
    use_pgqueuer: bool = Field(
        default=False,
        description="Use PgQueuer for distributed queue (True) or in-memory queue (False)",
    )
    postgres_url: Optional[str] = Field(
        default=None,
        description="PostgreSQL URL for PgQueuer (required if use_pgqueuer=True)",
    )
    tenant_id: Optional[str] = Field(
        default=None, description="Tenant ID for multi-tenancy"
    )

    # Dispatcher
    load_balancing: str = Field(
        default="least_loaded",
        description="Load balancing strategy: round_robin, least_loaded, random, affinity",
    )
    dispatch_interval: int = Field(
        default=5, description="Seconds between dispatch attempts"
    )

    # Timeouts
    timeout_check_interval: int = Field(
        default=30, description="Seconds between timeout checks"
    )
    default_job_timeout: int = Field(
        default=3600, description="Default job timeout in seconds"
    )

    # Triggers
    trigger_webhook_port: int = Field(
        default=8766, description="Port for trigger webhook server"
    )

    class Config:
        frozen = True  # Immutable

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return self.model_dump()


# Default configurations for common use cases

IN_MEMORY_CONFIG = OrchestratorConfig(
    use_pgqueuer=False,
    load_balancing="least_loaded",
)

PGQUEUER_CONFIG_TEMPLATE = OrchestratorConfig(
    use_pgqueuer=True,
    postgres_url="postgresql://user:password@localhost:5432/casare_rpa",
    tenant_id=None,
    load_balancing="least_loaded",
)
