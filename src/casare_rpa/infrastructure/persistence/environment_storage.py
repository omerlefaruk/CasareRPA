"""
CasareRPA - Environment Storage

Infrastructure service for loading and managing project environments.
"""

import orjson
from loguru import logger
from pathlib import Path
from typing import Any, Dict, List, Optional

from casare_rpa.domain.entities.project.environment import (
    Environment,
    EnvironmentType,
    ENVIRONMENT_INHERITANCE,
)


class EnvironmentStorage:
    """
    Static adapter for environment file operations.

    Environments are stored per-project in environments/ directory.
    """

    @staticmethod
    def save_environment(environment: Environment, environments_dir: Path) -> None:
        """
        Save an environment to file.

        Args:
            environment: Environment to save
            environments_dir: Project's environments directory
        """
        environments_dir.mkdir(parents=True, exist_ok=True)

        # Use environment type as filename for standard envs, id for custom
        if environment.env_type == EnvironmentType.CUSTOM:
            filename = f"{environment.id}.json"
        else:
            filename = f"{environment.env_type.value}.json"

        env_file = environments_dir / filename
        env_data = environment.to_dict()

        env_file.write_bytes(orjson.dumps(env_data, option=orjson.OPT_INDENT_2))

    @staticmethod
    def load_environment(env_id: str, environments_dir: Path) -> Optional[Environment]:
        """
        Load an environment by ID.

        Args:
            env_id: Environment identifier
            environments_dir: Project's environments directory

        Returns:
            Environment if found, None otherwise
        """
        if not environments_dir.exists():
            return None

        for env_file in environments_dir.glob("*.json"):
            try:
                data = orjson.loads(env_file.read_bytes())
                if data.get("id") == env_id:
                    return Environment.from_dict(data)
            except Exception:
                continue

        return None

    @staticmethod
    def load_environment_by_type(
        env_type: EnvironmentType, environments_dir: Path
    ) -> Optional[Environment]:
        """
        Load an environment by type.

        Args:
            env_type: Environment type
            environments_dir: Project's environments directory

        Returns:
            Environment if found, None otherwise
        """
        if not environments_dir.exists():
            return None

        # Standard environments use type as filename
        env_file = environments_dir / f"{env_type.value}.json"

        if env_file.exists():
            try:
                data = orjson.loads(env_file.read_bytes())
                return Environment.from_dict(data)
            except Exception:
                pass

        return None

    @staticmethod
    def load_all_environments(environments_dir: Path) -> List[Environment]:
        """
        Load all environments for a project.

        Args:
            environments_dir: Project's environments directory

        Returns:
            List of all environments
        """
        environments = []

        if not environments_dir.exists():
            return environments

        for env_file in environments_dir.glob("*.json"):
            try:
                data = orjson.loads(env_file.read_bytes())
                env = Environment.from_dict(data)
                environments.append(env)
            except Exception as e:
                logger.warning(f"Error loading environment {env_file}: {e}")

        # Sort by type order: dev, staging, prod, custom
        type_order = {
            EnvironmentType.DEVELOPMENT: 0,
            EnvironmentType.STAGING: 1,
            EnvironmentType.PRODUCTION: 2,
            EnvironmentType.CUSTOM: 3,
        }
        environments.sort(key=lambda e: type_order.get(e.env_type, 99))

        return environments

    @staticmethod
    def delete_environment(env_id: str, environments_dir: Path) -> bool:
        """
        Delete an environment.

        Args:
            env_id: Environment to delete
            environments_dir: Project's environments directory

        Returns:
            True if deleted, False if not found
        """
        if not environments_dir.exists():
            return False

        for env_file in environments_dir.glob("*.json"):
            try:
                data = orjson.loads(env_file.read_bytes())
                if data.get("id") == env_id:
                    env_file.unlink()
                    return True
            except Exception:
                continue

        return False

    @staticmethod
    def create_default_environments(environments_dir: Path) -> List[Environment]:
        """
        Create default dev/staging/prod environments for a new project.

        Args:
            environments_dir: Project's environments directory

        Returns:
            List of created environments
        """
        environments = Environment.create_default_environments()

        for env in environments:
            EnvironmentStorage.save_environment(env, environments_dir)

        return environments

    @staticmethod
    def resolve_variables_with_inheritance(
        environment: Environment, environments_dir: Path
    ) -> Dict[str, Any]:
        """
        Resolve environment variables with inheritance chain.

        staging inherits from development, production from staging.

        Args:
            environment: Current environment
            environments_dir: Project's environments directory

        Returns:
            Merged variables with inheritance applied
        """
        # Build inheritance chain
        chain = [environment]
        current = environment

        while True:
            parent_type = ENVIRONMENT_INHERITANCE.get(current.env_type)
            if not parent_type:
                break

            parent = EnvironmentStorage.load_environment_by_type(
                parent_type, environments_dir
            )
            if not parent:
                break

            chain.insert(0, parent)
            current = parent

        # Merge variables from ancestors to current
        merged_variables = {}
        for env in chain:
            merged_variables.update(env.variables)

        return merged_variables

    @staticmethod
    def get_active_environment(
        environment_ids: List[str],
        active_env_id: Optional[str],
        environments_dir: Path,
    ) -> Optional[Environment]:
        """
        Get the active environment for a project.

        Args:
            environment_ids: List of environment IDs in project
            active_env_id: Currently active environment ID
            environments_dir: Project's environments directory

        Returns:
            Active environment, or development if not set
        """
        if active_env_id:
            env = EnvironmentStorage.load_environment(active_env_id, environments_dir)
            if env:
                return env

        # Default to development environment
        dev_env = EnvironmentStorage.load_environment_by_type(
            EnvironmentType.DEVELOPMENT, environments_dir
        )
        if dev_env:
            return dev_env

        # If no development, return first available
        all_envs = EnvironmentStorage.load_all_environments(environments_dir)
        return all_envs[0] if all_envs else None
