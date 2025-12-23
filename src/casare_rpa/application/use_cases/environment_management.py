"""
CasareRPA - Environment Management Use Cases

Application layer use cases for environment CRUD operations.
Handles dev/staging/prod environments with variable inheritance.
"""

from dataclasses import dataclass
from typing import Any

from loguru import logger

from casare_rpa.domain.entities.project import (
    Environment,
    EnvironmentType,
    Project,
)
from casare_rpa.infrastructure.persistence.environment_storage import EnvironmentStorage

# =============================================================================
# Result Types
# =============================================================================


@dataclass
class EnvironmentResult:
    """Result of an environment operation."""

    success: bool
    environment: Environment | None = None
    error: str | None = None


@dataclass
class EnvironmentListResult:
    """Result of listing environments."""

    success: bool
    environments: list[Environment] = None
    error: str | None = None

    def __post_init__(self):
        if self.environments is None:
            self.environments = []


@dataclass
class VariablesResult:
    """Result of resolving variables."""

    success: bool
    variables: dict[str, Any] = None
    error: str | None = None

    def __post_init__(self):
        if self.variables is None:
            self.variables = {}


# =============================================================================
# Create Environment Use Case
# =============================================================================


class CreateEnvironmentUseCase:
    """
    Create a new environment in a project.

    Can create default environments (dev/staging/prod) or custom.
    """

    async def execute(
        self,
        project: Project,
        name: str,
        env_type: EnvironmentType = EnvironmentType.CUSTOM,
        description: str = "",
        variables: dict[str, Any] | None = None,
        is_default: bool = False,
    ) -> EnvironmentResult:
        """
        Create a new environment.

        Args:
            project: Parent project
            name: Environment name
            env_type: Environment type
            description: Environment description
            variables: Initial variables
            is_default: Whether this is the default environment

        Returns:
            EnvironmentResult with created environment or error
        """
        try:
            if not project.path:
                return EnvironmentResult(
                    success=False,
                    error="Project path not set",
                )

            environments_dir = project.environments_dir

            # Check if environment type already exists (for standard types)
            if env_type != EnvironmentType.CUSTOM:
                existing = EnvironmentStorage.load_environment_by_type(env_type, environments_dir)
                if existing:
                    return EnvironmentResult(
                        success=False,
                        error=f"Environment type '{env_type.value}' already exists",
                    )

            # Create environment
            from casare_rpa.domain.entities.project.environment import (
                generate_environment_id,
            )

            environment = Environment(
                id=generate_environment_id(),
                name=name,
                env_type=env_type,
                description=description,
                variables=variables or {},
                is_default=is_default,
            )

            # Save environment
            EnvironmentStorage.save_environment(environment, environments_dir)

            # Update project's environment list
            project.environment_ids.append(environment.id)
            if is_default:
                project.active_environment_id = environment.id

            logger.info(f"Created environment: {name} ({env_type.value})")
            return EnvironmentResult(success=True, environment=environment)

        except Exception as e:
            logger.error(f"Failed to create environment: {e}")
            return EnvironmentResult(success=False, error=str(e))


class CreateDefaultEnvironmentsUseCase:
    """Create default dev/staging/prod environments for a project."""

    async def execute(self, project: Project) -> EnvironmentListResult:
        """
        Create default environments.

        Args:
            project: Parent project

        Returns:
            EnvironmentListResult with created environments
        """
        try:
            if not project.path:
                return EnvironmentListResult(
                    success=False,
                    error="Project path not set",
                )

            environments_dir = project.environments_dir
            environments = EnvironmentStorage.create_default_environments(environments_dir)

            # Update project
            project.environment_ids = [e.id for e in environments]
            project.active_environment_id = environments[0].id  # Dev is default

            logger.info(f"Created {len(environments)} default environments")
            return EnvironmentListResult(success=True, environments=environments)

        except Exception as e:
            logger.error(f"Failed to create default environments: {e}")
            return EnvironmentListResult(success=False, error=str(e))


# =============================================================================
# Update Environment Use Case
# =============================================================================


class UpdateEnvironmentUseCase:
    """Update an existing environment."""

    async def execute(
        self,
        project: Project,
        environment_id: str,
        name: str | None = None,
        description: str | None = None,
        variables: dict[str, Any] | None = None,
        credential_overrides: dict[str, str] | None = None,
    ) -> EnvironmentResult:
        """
        Update environment.

        Args:
            project: Parent project
            environment_id: Environment to update
            name: New name (optional)
            description: New description (optional)
            variables: New variables (optional, replaces existing)
            credential_overrides: New credential overrides (optional)

        Returns:
            EnvironmentResult with updated environment
        """
        try:
            environments_dir = project.environments_dir
            environment = EnvironmentStorage.load_environment(environment_id, environments_dir)

            if not environment:
                return EnvironmentResult(
                    success=False,
                    error=f"Environment not found: {environment_id}",
                )

            # Update fields
            if name is not None:
                environment.name = name
            if description is not None:
                environment.description = description
            if variables is not None:
                environment.variables = variables
            if credential_overrides is not None:
                environment.credential_overrides = credential_overrides

            environment.touch_modified()

            # Save
            EnvironmentStorage.save_environment(environment, environments_dir)

            logger.info(f"Updated environment: {environment.name}")
            return EnvironmentResult(success=True, environment=environment)

        except Exception as e:
            logger.error(f"Failed to update environment: {e}")
            return EnvironmentResult(success=False, error=str(e))


# =============================================================================
# Delete Environment Use Case
# =============================================================================


class DeleteEnvironmentUseCase:
    """Delete an environment from a project."""

    async def execute(
        self,
        project: Project,
        environment_id: str,
    ) -> EnvironmentResult:
        """
        Delete an environment.

        Args:
            project: Parent project
            environment_id: Environment to delete

        Returns:
            EnvironmentResult indicating success
        """
        try:
            environments_dir = project.environments_dir

            # Don't allow deleting the last environment
            all_envs = EnvironmentStorage.load_all_environments(environments_dir)
            if len(all_envs) <= 1:
                return EnvironmentResult(
                    success=False,
                    error="Cannot delete the last environment",
                )

            # Delete
            deleted = EnvironmentStorage.delete_environment(environment_id, environments_dir)

            if not deleted:
                return EnvironmentResult(
                    success=False,
                    error=f"Environment not found: {environment_id}",
                )

            # Update project
            if environment_id in project.environment_ids:
                project.environment_ids.remove(environment_id)
            if project.active_environment_id == environment_id:
                # Switch to first available
                remaining = EnvironmentStorage.load_all_environments(environments_dir)
                project.active_environment_id = remaining[0].id if remaining else None

            logger.info(f"Deleted environment: {environment_id}")
            return EnvironmentResult(success=True)

        except Exception as e:
            logger.error(f"Failed to delete environment: {e}")
            return EnvironmentResult(success=False, error=str(e))


# =============================================================================
# Switch Environment Use Case
# =============================================================================


class SwitchEnvironmentUseCase:
    """Switch the active environment for a project."""

    async def execute(
        self,
        project: Project,
        environment_id: str,
    ) -> EnvironmentResult:
        """
        Switch active environment.

        Args:
            project: Parent project
            environment_id: Environment to switch to

        Returns:
            EnvironmentResult with new active environment
        """
        try:
            environments_dir = project.environments_dir
            environment = EnvironmentStorage.load_environment(environment_id, environments_dir)

            if not environment:
                return EnvironmentResult(
                    success=False,
                    error=f"Environment not found: {environment_id}",
                )

            # Update project
            project.active_environment_id = environment_id

            logger.info(f"Switched to environment: {environment.name}")
            return EnvironmentResult(success=True, environment=environment)

        except Exception as e:
            logger.error(f"Failed to switch environment: {e}")
            return EnvironmentResult(success=False, error=str(e))


# =============================================================================
# Clone Environment Use Case
# =============================================================================


class CloneEnvironmentUseCase:
    """Clone an existing environment."""

    async def execute(
        self,
        project: Project,
        source_environment_id: str,
        new_name: str,
    ) -> EnvironmentResult:
        """
        Clone an environment.

        Args:
            project: Parent project
            source_environment_id: Environment to clone
            new_name: Name for the clone

        Returns:
            EnvironmentResult with cloned environment
        """
        try:
            environments_dir = project.environments_dir
            source = EnvironmentStorage.load_environment(source_environment_id, environments_dir)

            if not source:
                return EnvironmentResult(
                    success=False,
                    error=f"Source environment not found: {source_environment_id}",
                )

            # Create clone
            from casare_rpa.domain.entities.project.environment import (
                generate_environment_id,
            )

            clone = Environment(
                id=generate_environment_id(),
                name=new_name,
                env_type=EnvironmentType.CUSTOM,  # Clones are always custom
                description=f"Cloned from {source.name}",
                variables=source.variables.copy(),
                credential_overrides=source.credential_overrides.copy(),
                settings=source.settings,
                is_default=False,
            )

            # Save clone
            EnvironmentStorage.save_environment(clone, environments_dir)

            # Update project
            project.environment_ids.append(clone.id)

            logger.info(f"Cloned environment: {source.name} -> {new_name}")
            return EnvironmentResult(success=True, environment=clone)

        except Exception as e:
            logger.error(f"Failed to clone environment: {e}")
            return EnvironmentResult(success=False, error=str(e))


# =============================================================================
# Resolve Variables Use Case
# =============================================================================


class ResolveEnvironmentVariablesUseCase:
    """Resolve environment variables with inheritance."""

    async def execute(
        self,
        project: Project,
        environment_id: str | None = None,
    ) -> VariablesResult:
        """
        Resolve variables with inheritance chain.

        Args:
            project: Parent project
            environment_id: Environment to resolve (uses active if not specified)

        Returns:
            VariablesResult with resolved variables
        """
        try:
            environments_dir = project.environments_dir
            env_id = environment_id or project.active_environment_id

            if not env_id:
                return VariablesResult(
                    success=False,
                    error="No environment specified or active",
                )

            environment = EnvironmentStorage.load_environment(env_id, environments_dir)
            if not environment:
                return VariablesResult(
                    success=False,
                    error=f"Environment not found: {env_id}",
                )

            # Resolve with inheritance
            variables = EnvironmentStorage.resolve_variables_with_inheritance(
                environment, environments_dir
            )

            return VariablesResult(success=True, variables=variables)

        except Exception as e:
            logger.error(f"Failed to resolve variables: {e}")
            return VariablesResult(success=False, error=str(e))


# =============================================================================
# List Environments Use Case
# =============================================================================


class ListEnvironmentsUseCase:
    """List all environments in a project."""

    async def execute(self, project: Project) -> EnvironmentListResult:
        """
        List environments.

        Args:
            project: Parent project

        Returns:
            EnvironmentListResult with list of environments
        """
        try:
            environments_dir = project.environments_dir
            environments = EnvironmentStorage.load_all_environments(environments_dir)

            return EnvironmentListResult(success=True, environments=environments)

        except Exception as e:
            logger.error(f"Failed to list environments: {e}")
            return EnvironmentListResult(success=False, error=str(e))
