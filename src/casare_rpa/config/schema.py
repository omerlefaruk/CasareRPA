"""
CasareRPA Configuration Schema.

Pydantic models for typed, validated configuration.
All settings have sensible defaults for development.
"""

from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class DatabaseConfig(BaseModel):
    """Database connection configuration."""

    enabled: bool = Field(default=True, description="Enable database (false = in-memory fallback)")
    url: Optional[str] = Field(default=None, description="Full connection URL")

    # Individual components (used if url not provided)
    host: str = Field(default="localhost")
    port: int = Field(default=5432, ge=1, le=65535)
    name: str = Field(default="casare_rpa")
    user: str = Field(default="casare_user")
    password: str = Field(default="")

    # Pool settings
    pool_min_size: int = Field(default=2, ge=1)
    pool_max_size: int = Field(default=10, ge=1)
    command_timeout: float = Field(default=60.0, ge=1.0)
    max_inactive_lifetime: float = Field(default=300.0, ge=0.0)

    @property
    def connection_url(self) -> str:
        """Get connection URL (explicit or built from components)."""
        if self.url:
            return self.url
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"

    @field_validator("url", mode="before")
    @classmethod
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate database URL format."""
        if v and not v.startswith(("postgresql://", "postgres://")):
            raise ValueError("Database URL must start with postgresql:// or postgres://")
        return v


class SupabaseConfig(BaseModel):
    """Supabase cloud configuration."""

    url: Optional[str] = Field(default=None, description="Supabase project URL")
    key: Optional[str] = Field(default=None, description="Supabase anon key")
    service_key: Optional[str] = Field(default=None, description="Supabase service role key")

    @property
    def is_configured(self) -> bool:
        """Check if Supabase is configured."""
        return bool(self.url and self.key)

    @field_validator("url", mode="before")
    @classmethod
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate Supabase URL format."""
        if v and not v.startswith("https://"):
            raise ValueError("Supabase URL must start with https://")
        return v


class SecurityConfig(BaseModel):
    """Security and authentication configuration."""

    api_secret: Optional[str] = Field(default=None, description="JWT signing secret")
    jwt_expiration_seconds: int = Field(default=3600, ge=60)
    robot_auth_enabled: bool = Field(default=False, description="Require robot API keys")
    verify_ssl: bool = Field(default=True, description="Verify SSL certificates")

    # mTLS settings
    ca_cert_path: Optional[Path] = Field(default=None)
    client_cert_path: Optional[Path] = Field(default=None)
    client_key_path: Optional[Path] = Field(default=None)

    @property
    def uses_mtls(self) -> bool:
        """Check if mTLS is configured."""
        return all([self.ca_cert_path, self.client_cert_path, self.client_key_path])

    @model_validator(mode="after")
    def validate_mtls(self) -> "SecurityConfig":
        """Validate mTLS configuration (all or nothing)."""
        mtls_paths = [self.ca_cert_path, self.client_cert_path, self.client_key_path]
        mtls_set = sum(1 for p in mtls_paths if p is not None)
        if mtls_set > 0 and mtls_set < 3:
            raise ValueError(
                "mTLS requires all three: ca_cert_path, client_cert_path, client_key_path"
            )
        return self


class OrchestratorConfig(BaseModel):
    """Orchestrator API configuration."""

    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000, ge=1, le=65535)
    workers: int = Field(default=1, ge=1)
    cors_origins: List[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://localhost:8000"]
    )

    # SSL
    ssl_keyfile: Optional[Path] = Field(default=None)
    ssl_certfile: Optional[Path] = Field(default=None)

    @property
    def uses_ssl(self) -> bool:
        """Check if SSL is configured."""
        return bool(self.ssl_keyfile and self.ssl_certfile)


class RobotConfig(BaseModel):
    """Robot agent configuration."""

    id: Optional[str] = Field(default=None, description="Robot ID (auto-generated if not set)")
    name: Optional[str] = Field(default=None, description="Robot display name")
    environment: str = Field(default="production")
    max_concurrent_jobs: int = Field(default=1, ge=1)
    heartbeat_interval: int = Field(default=30, ge=1)
    capabilities: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)

    # Connection settings
    reconnect_delay: float = Field(default=1.0, ge=0.1)
    max_reconnect_delay: float = Field(default=60.0, ge=1.0)
    job_timeout: float = Field(default=3600.0, ge=1.0)


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: str = Field(default="INFO")
    file: Optional[Path] = Field(default=None)
    rotation_size_mb: int = Field(default=10, ge=1)
    retention_days: int = Field(default=7, ge=1)

    @field_validator("level", mode="before")
    @classmethod
    def validate_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v_upper


class QueueConfig(BaseModel):
    """Job queue configuration."""

    url: Optional[str] = Field(default=None, description="PgQueuer database URL")
    use_memory_queue: bool = Field(default=False, description="Use in-memory queue (dev only)")
    poll_interval: float = Field(default=1.0, ge=0.1)
    job_timeout_default: int = Field(default=3600, ge=1)


class TimeoutConfig(BaseModel):
    """Timeout configuration."""

    robot_heartbeat: int = Field(
        default=90, ge=10, description="Seconds without heartbeat = offline"
    )
    ws_ping_interval: int = Field(default=30, ge=5)
    ws_send_timeout: float = Field(default=1.0, ge=0.1)


class RateLimitConfig(BaseModel):
    """Rate limiting configuration."""

    enabled: bool = Field(default=True)
    requests_per_minute: int = Field(default=100, ge=1)


class MetricsConfig(BaseModel):
    """Metrics collection configuration."""

    enabled: bool = Field(default=True)
    collection_interval: int = Field(default=5, ge=1)
    event_history_size: int = Field(default=1000, ge=100)


class VaultConfig(BaseModel):
    """HashiCorp Vault configuration."""

    addr: Optional[str] = Field(default=None, description="Vault server address")
    token: Optional[str] = Field(default=None, description="Vault token")
    role_id: Optional[str] = Field(default=None, description="AppRole role ID")
    secret_id: Optional[str] = Field(default=None, description="AppRole secret ID")

    @property
    def is_configured(self) -> bool:
        """Check if Vault is configured."""
        return bool(self.addr and (self.token or (self.role_id and self.secret_id)))

    @property
    def auth_method(self) -> Optional[str]:
        """Get configured authentication method."""
        if not self.addr:
            return None
        if self.token:
            return "token"
        if self.role_id and self.secret_id:
            return "approle"
        return None


class StorageConfig(BaseModel):
    """Workflow storage configuration."""

    workflows_dir: Path = Field(default=Path("./workflows"))
    backup_enabled: bool = Field(default=True)


class CloudflareConfig(BaseModel):
    """Cloudflare Tunnel configuration."""

    api_url: Optional[str] = Field(default=None)
    webhook_url: Optional[str] = Field(default=None)
    robot_ws_url: Optional[str] = Field(default=None)


class Config(BaseModel):
    """
    Root configuration class.

    Contains all configuration sections with sensible defaults.
    Validates configuration on construction.
    """

    # Core
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    supabase: SupabaseConfig = Field(default_factory=SupabaseConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)

    # Services
    orchestrator: OrchestratorConfig = Field(default_factory=OrchestratorConfig)
    robot: RobotConfig = Field(default_factory=RobotConfig)

    # Operations
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    queue: QueueConfig = Field(default_factory=QueueConfig)
    timeouts: TimeoutConfig = Field(default_factory=TimeoutConfig)
    rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig)
    metrics: MetricsConfig = Field(default_factory=MetricsConfig)

    # Optional integrations
    vault: VaultConfig = Field(default_factory=VaultConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    cloudflare: CloudflareConfig = Field(default_factory=CloudflareConfig)

    # Development
    debug: bool = Field(default=False)
    reload: bool = Field(default=False)

    # Multi-tenant
    tenant_id: Optional[str] = Field(default=None)

    class Config:
        """Pydantic config."""

        extra = "ignore"  # Ignore unknown fields

    def get_summary(self, mask_secrets: bool = True) -> dict:
        """
        Get configuration summary for logging.

        Args:
            mask_secrets: Whether to mask sensitive values

        Returns:
            Dictionary with configuration summary
        """
        summary = {
            "database": {
                "enabled": self.database.enabled,
                "host": self.database.host,
                "port": self.database.port,
                "name": self.database.name,
                "pool_size": f"{self.database.pool_min_size}-{self.database.pool_max_size}",
            },
            "supabase": {
                "configured": self.supabase.is_configured,
                "url": self.supabase.url[:50] + "..." if self.supabase.url else None,
            },
            "orchestrator": {
                "host": self.orchestrator.host,
                "port": self.orchestrator.port,
                "workers": self.orchestrator.workers,
                "ssl": self.orchestrator.uses_ssl,
            },
            "robot": {
                "id": self.robot.id,
                "name": self.robot.name,
                "environment": self.robot.environment,
                "max_concurrent_jobs": self.robot.max_concurrent_jobs,
            },
            "security": {
                "api_secret_set": bool(self.security.api_secret),
                "robot_auth_enabled": self.security.robot_auth_enabled,
                "uses_mtls": self.security.uses_mtls,
            },
            "logging": {
                "level": self.logging.level,
                "file": str(self.logging.file) if self.logging.file else None,
            },
            "debug": self.debug,
        }
        return summary
