"""
DBOS Cloud Deployment Client.

Provides a Python wrapper around the DBOS Cloud CLI for automated deployment,
scaling, and monitoring of CasareRPA services.

Features:
- One-command deployment to DBOS Cloud
- Auto-scaling configuration (min/max instances, target CPU)
- Managed PostgreSQL setup
- Environment variable management
- Zero-downtime deployment support
- Health check endpoint integration
- Deployment status monitoring
"""

import asyncio
import json
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from loguru import logger
from pydantic import BaseModel, Field


class DeploymentState(str, Enum):
    """Deployment state enumeration."""

    PENDING = "pending"
    DEPLOYING = "deploying"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"
    UNKNOWN = "unknown"


class EnvironmentVariable(BaseModel):
    """Environment variable configuration."""

    name: str = Field(..., description="Environment variable name")
    value: str = Field(..., description="Environment variable value")
    secret: bool = Field(default=False, description="Whether this is a secret value")


class ScalingConfig(BaseModel):
    """Auto-scaling configuration for DBOS Cloud."""

    min_instances: int = Field(default=1, ge=1, le=100, description="Minimum instances")
    max_instances: int = Field(default=10, ge=1, le=100, description="Maximum instances")
    target_cpu_percent: int = Field(
        default=70, ge=10, le=90, description="Target CPU utilization percentage"
    )
    scale_up_cooldown_seconds: int = Field(
        default=60, ge=30, le=600, description="Cooldown after scale up"
    )
    scale_down_cooldown_seconds: int = Field(
        default=300, ge=60, le=1800, description="Cooldown after scale down"
    )


class PostgresConfig(BaseModel):
    """Managed PostgreSQL configuration."""

    enabled: bool = Field(default=True, description="Enable managed PostgreSQL")
    version: str = Field(default="15", description="PostgreSQL version")
    storage_gb: int = Field(default=10, ge=1, le=1000, description="Storage size in GB")
    high_availability: bool = Field(default=False, description="Enable HA with replicas")


class HealthCheckConfig(BaseModel):
    """Health check configuration."""

    path: str = Field(default="/health", description="Health check endpoint path")
    interval_seconds: int = Field(default=30, ge=10, le=300, description="Check interval")
    timeout_seconds: int = Field(default=10, ge=5, le=60, description="Check timeout")
    healthy_threshold: int = Field(default=2, ge=1, le=10, description="Healthy threshold")
    unhealthy_threshold: int = Field(default=3, ge=1, le=10, description="Unhealthy threshold")


class DBOSConfig(BaseModel):
    """DBOS Cloud deployment configuration."""

    app_name: str = Field(..., description="Application name in DBOS Cloud")
    environment: str = Field(default="production", description="Deployment environment")
    region: str = Field(default="us-east-1", description="Deployment region")
    scaling: ScalingConfig = Field(default_factory=ScalingConfig)
    postgres: PostgresConfig = Field(default_factory=PostgresConfig)
    health_check: HealthCheckConfig = Field(default_factory=HealthCheckConfig)
    env_vars: list[EnvironmentVariable] = Field(default_factory=list)
    deploy_timeout_seconds: int = Field(
        default=600, ge=60, le=3600, description="Deployment timeout"
    )
    rollback_on_failure: bool = Field(
        default=True, description="Auto-rollback on deployment failure"
    )


@dataclass
class DeploymentStatus:
    """Deployment status information."""

    app_name: str
    environment: str
    state: DeploymentState
    version: str
    instances_running: int
    instances_desired: int
    cpu_utilization: float
    memory_utilization: float
    last_deployed: datetime | None
    health_status: str
    url: str | None
    postgres_url: str | None
    error_message: str | None = None
    raw_response: dict[str, Any] = field(default_factory=dict)


class DBOSCloudError(Exception):
    """DBOS Cloud operation error."""

    def __init__(self, message: str, exit_code: int | None = None, stderr: str = ""):
        super().__init__(message)
        self.exit_code = exit_code
        self.stderr = stderr


class DBOSCloudClient:
    """
    DBOS Cloud deployment client.

    Wraps the DBOS Cloud CLI to provide programmatic deployment,
    scaling, and monitoring capabilities for CasareRPA services.

    Usage:
        client = DBOSCloudClient()
        await client.login()

        config = DBOSConfig(
            app_name="casare-rpa",
            environment="production",
            scaling=ScalingConfig(min_instances=2, max_instances=10),
        )
        await client.deploy(config)

        status = await client.get_status("casare-rpa", "production")
        print(f"State: {status.state}, Instances: {status.instances_running}")
    """

    CLI_COMMAND = "dbos-cloud"
    NPM_PACKAGE = "@dbos-inc/dbos-cloud"

    def __init__(
        self,
        config_path: Path | None = None,
        working_dir: Path | None = None,
    ):
        """
        Initialize DBOS Cloud client.

        Args:
            config_path: Path to dbos-config.yaml (default: project root)
            working_dir: Working directory for CLI commands (default: project root)
        """
        self.config_path = config_path or Path.cwd() / "dbos-config.yaml"
        self.working_dir = working_dir or Path.cwd()
        self._cli_available: bool | None = None

    async def ensure_cli_installed(self) -> bool:
        """
        Ensure DBOS Cloud CLI is installed.

        Returns:
            True if CLI is available, False otherwise

        Raises:
            DBOSCloudError: If CLI installation fails
        """
        if self._cli_available is not None:
            return self._cli_available

        if shutil.which(self.CLI_COMMAND):
            self._cli_available = True
            logger.debug("DBOS Cloud CLI found in PATH")
            return True

        logger.info("DBOS Cloud CLI not found, attempting installation...")
        try:
            result = await self._run_command(
                ["npm", "install", "-g", self.NPM_PACKAGE],
                capture_output=True,
                check=False,
            )
            if result.returncode == 0:
                self._cli_available = True
                logger.info("DBOS Cloud CLI installed successfully")
                return True
            else:
                logger.error(f"Failed to install DBOS Cloud CLI: {result.stderr}")
                self._cli_available = False
                return False
        except FileNotFoundError:
            logger.error("npm not found. Please install Node.js and npm first.")
            self._cli_available = False
            return False

    async def login(self, token: str | None = None) -> bool:
        """
        Authenticate with DBOS Cloud.

        Args:
            token: Optional API token (uses interactive login if not provided)

        Returns:
            True if login successful

        Raises:
            DBOSCloudError: If login fails
        """
        await self.ensure_cli_installed()

        cmd = [self.CLI_COMMAND, "login"]
        if token:
            cmd.extend(["--token", token])

        logger.info("Authenticating with DBOS Cloud...")
        result = await self._run_command(cmd, capture_output=True)

        if result.returncode != 0:
            raise DBOSCloudError(
                f"Login failed: {result.stderr}",
                exit_code=result.returncode,
                stderr=result.stderr,
            )

        logger.info("Successfully authenticated with DBOS Cloud")
        return True

    async def deploy(
        self,
        config: DBOSConfig,
        wait: bool = True,
        dry_run: bool = False,
    ) -> DeploymentStatus:
        """
        Deploy application to DBOS Cloud.

        Performs a zero-downtime deployment with automatic rollback
        on failure if configured.

        Args:
            config: Deployment configuration
            wait: Wait for deployment to complete
            dry_run: Validate without deploying

        Returns:
            Deployment status after deployment

        Raises:
            DBOSCloudError: If deployment fails
        """
        await self.ensure_cli_installed()

        logger.info(f"Deploying {config.app_name} to {config.environment} environment...")

        # Build deploy command
        cmd = [
            self.CLI_COMMAND,
            "app",
            "deploy",
            "--app",
            config.app_name,
        ]

        # Add PostgreSQL configuration
        if config.postgres.enabled:
            cmd.append("--postgres")
            if config.postgres.high_availability:
                cmd.append("--postgres-ha")

        # Add environment variables
        for env_var in config.env_vars:
            cmd.extend(["--env", f"{env_var.name}={env_var.value}"])

        if dry_run:
            cmd.append("--dry-run")

        if not wait:
            cmd.append("--no-wait")

        try:
            result = await self._run_command(
                cmd,
                capture_output=True,
                timeout=config.deploy_timeout_seconds,
            )

            if result.returncode != 0:
                error_msg = f"Deployment failed: {result.stderr}"
                logger.error(error_msg)

                if config.rollback_on_failure and not dry_run:
                    logger.info("Attempting automatic rollback...")
                    try:
                        await self.rollback(config.app_name, config.environment)
                        logger.info("Rollback completed successfully")
                    except DBOSCloudError as rollback_error:
                        logger.error(f"Rollback failed: {rollback_error}")

                raise DBOSCloudError(
                    error_msg,
                    exit_code=result.returncode,
                    stderr=result.stderr,
                )

            logger.info(f"Deployment of {config.app_name} completed successfully")

            # Apply scaling configuration
            if not dry_run:
                await self.configure_scaling(
                    config.app_name,
                    config.environment,
                    config.scaling,
                )

            return await self.get_status(config.app_name, config.environment)

        except TimeoutError:
            raise DBOSCloudError(
                f"Deployment timed out after {config.deploy_timeout_seconds} seconds"
            )

    async def configure_scaling(
        self,
        app_name: str,
        environment: str,
        scaling: ScalingConfig,
    ) -> bool:
        """
        Configure auto-scaling for deployed application.

        Args:
            app_name: Application name
            environment: Deployment environment
            scaling: Scaling configuration

        Returns:
            True if scaling configured successfully

        Raises:
            DBOSCloudError: If scaling configuration fails
        """
        await self.ensure_cli_installed()

        logger.info(
            f"Configuring auto-scaling for {app_name}: "
            f"min={scaling.min_instances}, max={scaling.max_instances}, "
            f"target_cpu={scaling.target_cpu_percent}%"
        )

        cmd = [
            self.CLI_COMMAND,
            "app",
            "scale",
            "--app",
            app_name,
            "--min-instances",
            str(scaling.min_instances),
            "--max-instances",
            str(scaling.max_instances),
            "--target-cpu",
            str(scaling.target_cpu_percent),
        ]

        result = await self._run_command(cmd, capture_output=True)

        if result.returncode != 0:
            raise DBOSCloudError(
                f"Failed to configure scaling: {result.stderr}",
                exit_code=result.returncode,
                stderr=result.stderr,
            )

        logger.info("Auto-scaling configured successfully")
        return True

    async def get_status(
        self,
        app_name: str,
        environment: str = "production",
    ) -> DeploymentStatus:
        """
        Get deployment status for an application.

        Args:
            app_name: Application name
            environment: Deployment environment

        Returns:
            Current deployment status

        Raises:
            DBOSCloudError: If status retrieval fails
        """
        await self.ensure_cli_installed()

        cmd = [
            self.CLI_COMMAND,
            "app",
            "status",
            "--app",
            app_name,
            "--output",
            "json",
        ]

        result = await self._run_command(cmd, capture_output=True)

        if result.returncode != 0:
            raise DBOSCloudError(
                f"Failed to get status: {result.stderr}",
                exit_code=result.returncode,
                stderr=result.stderr,
            )

        try:
            data = json.loads(result.stdout) if result.stdout.strip() else {}
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse status JSON: {result.stdout}")
            data = {}

        return self._parse_status(app_name, environment, data)

    async def get_logs(
        self,
        app_name: str,
        environment: str = "production",
        tail: int = 100,
        follow: bool = False,
    ) -> str:
        """
        Retrieve application logs.

        Args:
            app_name: Application name
            environment: Deployment environment
            tail: Number of lines to retrieve
            follow: Stream logs continuously

        Returns:
            Log output string

        Raises:
            DBOSCloudError: If log retrieval fails
        """
        await self.ensure_cli_installed()

        cmd = [
            self.CLI_COMMAND,
            "app",
            "logs",
            "--app",
            app_name,
            "--tail",
            str(tail),
        ]

        if follow:
            cmd.append("--follow")

        result = await self._run_command(cmd, capture_output=True)

        if result.returncode != 0:
            raise DBOSCloudError(
                f"Failed to get logs: {result.stderr}",
                exit_code=result.returncode,
                stderr=result.stderr,
            )

        return result.stdout

    async def rollback(
        self,
        app_name: str,
        environment: str = "production",
        version: str | None = None,
    ) -> DeploymentStatus:
        """
        Rollback to previous deployment version.

        Args:
            app_name: Application name
            environment: Deployment environment
            version: Specific version to rollback to (default: previous)

        Returns:
            Deployment status after rollback

        Raises:
            DBOSCloudError: If rollback fails
        """
        await self.ensure_cli_installed()

        logger.info(f"Rolling back {app_name}...")

        cmd = [
            self.CLI_COMMAND,
            "app",
            "rollback",
            "--app",
            app_name,
        ]

        if version:
            cmd.extend(["--version", version])

        result = await self._run_command(cmd, capture_output=True)

        if result.returncode != 0:
            raise DBOSCloudError(
                f"Rollback failed: {result.stderr}",
                exit_code=result.returncode,
                stderr=result.stderr,
            )

        logger.info("Rollback completed successfully")
        return await self.get_status(app_name, environment)

    async def destroy(
        self,
        app_name: str,
        environment: str = "production",
        force: bool = False,
    ) -> bool:
        """
        Destroy deployed application.

        WARNING: This permanently deletes the application and its data.

        Args:
            app_name: Application name
            environment: Deployment environment
            force: Skip confirmation

        Returns:
            True if destruction successful

        Raises:
            DBOSCloudError: If destruction fails
        """
        await self.ensure_cli_installed()

        logger.warning(f"Destroying {app_name} in {environment}...")

        cmd = [
            self.CLI_COMMAND,
            "app",
            "destroy",
            "--app",
            app_name,
        ]

        if force:
            cmd.append("--force")

        result = await self._run_command(cmd, capture_output=True)

        if result.returncode != 0:
            raise DBOSCloudError(
                f"Destroy failed: {result.stderr}",
                exit_code=result.returncode,
                stderr=result.stderr,
            )

        logger.info(f"Application {app_name} destroyed successfully")
        return True

    async def set_env_vars(
        self,
        app_name: str,
        env_vars: list[EnvironmentVariable],
        restart: bool = True,
    ) -> bool:
        """
        Set environment variables for deployed application.

        Args:
            app_name: Application name
            env_vars: Environment variables to set
            restart: Restart application after setting variables

        Returns:
            True if successful

        Raises:
            DBOSCloudError: If operation fails
        """
        await self.ensure_cli_installed()

        logger.info(f"Setting {len(env_vars)} environment variables for {app_name}")

        for env_var in env_vars:
            cmd = [
                self.CLI_COMMAND,
                "app",
                "env",
                "set",
                "--app",
                app_name,
                env_var.name,
                env_var.value,
            ]

            if env_var.secret:
                cmd.append("--secret")

            result = await self._run_command(cmd, capture_output=True)

            if result.returncode != 0:
                raise DBOSCloudError(
                    f"Failed to set env var {env_var.name}: {result.stderr}",
                    exit_code=result.returncode,
                    stderr=result.stderr,
                )

        if restart:
            logger.info("Restarting application to apply environment changes...")
            await self._restart_app(app_name)

        logger.info("Environment variables set successfully")
        return True

    async def health_check(
        self,
        app_name: str,
        environment: str = "production",
    ) -> dict[str, Any]:
        """
        Perform health check on deployed application.

        Args:
            app_name: Application name
            environment: Deployment environment

        Returns:
            Health check response

        Raises:
            DBOSCloudError: If health check fails
        """
        status = await self.get_status(app_name, environment)

        if not status.url:
            raise DBOSCloudError(f"Application {app_name} has no URL configured")

        # Build health check URL
        health_url = f"{status.url.rstrip('/')}/health"

        logger.info(f"Performing health check at {health_url}")

        # Use UnifiedHttpClient for async HTTP request
        try:
            from casare_rpa.infrastructure.http.unified_http_client import UnifiedHttpClient

            client = UnifiedHttpClient()
            response = await client.get(health_url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                logger.info(f"Health check passed: {data}")
                return data
            else:
                raise DBOSCloudError(f"Health check failed with status {response.status_code}")
        except Exception as e:
            if "HTTP failed" in str(e) or "request failed" in str(e):
                raise DBOSCloudError(f"Health check request failed: {e}") from e
            raise

    async def get_metrics(
        self,
        app_name: str,
        environment: str = "production",
        time_range: str = "1h",
    ) -> dict[str, Any]:
        """
        Retrieve application metrics from DBOS Cloud.

        Args:
            app_name: Application name
            environment: Deployment environment
            time_range: Time range for metrics (e.g., "1h", "24h", "7d")

        Returns:
            Metrics data

        Raises:
            DBOSCloudError: If metrics retrieval fails
        """
        await self.ensure_cli_installed()

        cmd = [
            self.CLI_COMMAND,
            "app",
            "metrics",
            "--app",
            app_name,
            "--range",
            time_range,
            "--output",
            "json",
        ]

        result = await self._run_command(cmd, capture_output=True)

        if result.returncode != 0:
            raise DBOSCloudError(
                f"Failed to get metrics: {result.stderr}",
                exit_code=result.returncode,
                stderr=result.stderr,
            )

        try:
            return json.loads(result.stdout) if result.stdout.strip() else {}
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse metrics JSON: {result.stdout}")
            return {}

    async def list_deployments(self) -> list[dict[str, Any]]:
        """
        List all deployed applications.

        Returns:
            List of deployment information

        Raises:
            DBOSCloudError: If listing fails
        """
        await self.ensure_cli_installed()

        cmd = [
            self.CLI_COMMAND,
            "app",
            "list",
            "--output",
            "json",
        ]

        result = await self._run_command(cmd, capture_output=True)

        if result.returncode != 0:
            raise DBOSCloudError(
                f"Failed to list deployments: {result.stderr}",
                exit_code=result.returncode,
                stderr=result.stderr,
            )

        try:
            return json.loads(result.stdout) if result.stdout.strip() else []
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse deployments JSON: {result.stdout}")
            return []

    async def get_postgres_connection_string(
        self,
        app_name: str,
    ) -> str:
        """
        Get managed PostgreSQL connection string.

        Args:
            app_name: Application name

        Returns:
            PostgreSQL connection string

        Raises:
            DBOSCloudError: If retrieval fails
        """
        await self.ensure_cli_installed()

        cmd = [
            self.CLI_COMMAND,
            "db",
            "connection-string",
            "--app",
            app_name,
        ]

        result = await self._run_command(cmd, capture_output=True)

        if result.returncode != 0:
            raise DBOSCloudError(
                f"Failed to get PostgreSQL connection string: {result.stderr}",
                exit_code=result.returncode,
                stderr=result.stderr,
            )

        return result.stdout.strip()

    async def _restart_app(self, app_name: str) -> None:
        """Restart application deployment."""
        cmd = [
            self.CLI_COMMAND,
            "app",
            "restart",
            "--app",
            app_name,
        ]

        result = await self._run_command(cmd, capture_output=True)

        if result.returncode != 0:
            raise DBOSCloudError(
                f"Failed to restart application: {result.stderr}",
                exit_code=result.returncode,
                stderr=result.stderr,
            )

    async def _run_command(
        self,
        cmd: list[str],
        capture_output: bool = True,
        timeout: int | None = None,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        """
        Run CLI command asynchronously.

        Args:
            cmd: Command and arguments
            capture_output: Capture stdout/stderr
            timeout: Command timeout in seconds
            check: Raise exception on non-zero exit

        Returns:
            Completed process result
        """
        logger.debug(f"Running command: {' '.join(cmd)}")

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE if capture_output else None,
            stderr=asyncio.subprocess.PIPE if capture_output else None,
            cwd=str(self.working_dir),
        )

        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout,
            )
            stdout = stdout_bytes.decode("utf-8") if stdout_bytes else ""
            stderr = stderr_bytes.decode("utf-8") if stderr_bytes else ""

            return subprocess.CompletedProcess(
                args=cmd,
                returncode=proc.returncode or 0,
                stdout=stdout,
                stderr=stderr,
            )
        except TimeoutError:
            proc.kill()
            raise

    def _parse_status(
        self,
        app_name: str,
        environment: str,
        data: dict[str, Any],
    ) -> DeploymentStatus:
        """Parse status response into DeploymentStatus object."""
        state_str = data.get("state", "unknown").lower()
        try:
            state = DeploymentState(state_str)
        except ValueError:
            state = DeploymentState.UNKNOWN

        last_deployed_str = data.get("last_deployed")
        last_deployed = None
        if last_deployed_str:
            try:
                last_deployed = datetime.fromisoformat(last_deployed_str.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                pass

        return DeploymentStatus(
            app_name=app_name,
            environment=environment,
            state=state,
            version=data.get("version", "unknown"),
            instances_running=data.get("instances_running", 0),
            instances_desired=data.get("instances_desired", 0),
            cpu_utilization=data.get("cpu_utilization", 0.0),
            memory_utilization=data.get("memory_utilization", 0.0),
            last_deployed=last_deployed,
            health_status=data.get("health_status", "unknown"),
            url=data.get("url"),
            postgres_url=data.get("postgres_url"),
            error_message=data.get("error_message"),
            raw_response=data,
        )


def load_config_from_yaml(config_path: Path) -> DBOSConfig:
    """
    Load DBOS configuration from YAML file.

    Args:
        config_path: Path to dbos-config.yaml

    Returns:
        Parsed DBOSConfig

    Raises:
        FileNotFoundError: If config file not found
        ValueError: If config is invalid
    """
    import yaml

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not data:
        raise ValueError("Empty configuration file")

    # Parse environment variables
    env_vars = []
    for env_item in data.get("env_vars", []):
        if isinstance(env_item, dict):
            env_vars.append(EnvironmentVariable(**env_item))
        elif isinstance(env_item, str) and "=" in env_item:
            name, value = env_item.split("=", 1)
            env_vars.append(EnvironmentVariable(name=name, value=value))

    # Parse scaling config
    scaling_data = data.get("scaling", {})
    scaling = ScalingConfig(**scaling_data) if scaling_data else ScalingConfig()

    # Parse postgres config
    postgres_data = data.get("postgres", {})
    postgres = PostgresConfig(**postgres_data) if postgres_data else PostgresConfig()

    # Parse health check config
    health_data = data.get("health_check", {})
    health_check = HealthCheckConfig(**health_data) if health_data else HealthCheckConfig()

    return DBOSConfig(
        app_name=data.get("app_name", "casare-rpa"),
        environment=data.get("environment", "production"),
        region=data.get("region", "us-east-1"),
        scaling=scaling,
        postgres=postgres,
        health_check=health_check,
        env_vars=env_vars,
        deploy_timeout_seconds=data.get("deploy_timeout_seconds", 600),
        rollback_on_failure=data.get("rollback_on_failure", True),
    )


async def deploy_from_config(
    config_path: Path | None = None,
    environment: str | None = None,
    dry_run: bool = False,
) -> DeploymentStatus:
    """
    Deploy CasareRPA from configuration file.

    Convenience function for one-command deployment.

    Args:
        config_path: Path to dbos-config.yaml (default: project root)
        environment: Override environment from config
        dry_run: Validate without deploying

    Returns:
        Deployment status

    Raises:
        DBOSCloudError: If deployment fails
    """
    config_path = config_path or Path.cwd() / "dbos-config.yaml"
    config = load_config_from_yaml(config_path)

    if environment:
        config.environment = environment

    client = DBOSCloudClient(config_path=config_path)
    return await client.deploy(config, wait=True, dry_run=dry_run)
