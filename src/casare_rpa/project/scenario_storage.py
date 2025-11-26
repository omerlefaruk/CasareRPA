"""
CasareRPA - Scenario Storage
Handles file I/O operations for scenarios.
"""

from pathlib import Path
from typing import List, Optional
import orjson
from loguru import logger

from ..core.project_schema import (
    Project,
    Scenario,
    generate_scenario_id,
)


def _sanitize_filename(name: str) -> str:
    """Convert a name to a safe filename."""
    # Replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    result = name
    for char in invalid_chars:
        result = result.replace(char, '_')
    # Limit length
    return result[:50].strip()


class ScenarioStorage:
    """
    Handles file I/O operations for scenarios.

    Scenarios are stored as JSON files in the project's scenarios/ folder.
    Each scenario embeds its complete workflow for portability.
    """

    @staticmethod
    def save_scenario(scenario: Scenario, project: Project) -> Path:
        """
        Save a scenario to the project's scenarios folder.

        Args:
            scenario: Scenario to save
            project: Parent project

        Returns:
            Path to saved scenario file

        Raises:
            ValueError: If project path is not set
        """
        if project.path is None or project.scenarios_dir is None:
            raise ValueError("Project path is not set")

        # Ensure scenarios directory exists
        project.scenarios_dir.mkdir(exist_ok=True)

        # Generate filename from scenario ID and name
        safe_name = _sanitize_filename(scenario.name)
        filename = f"{scenario.id}_{safe_name}.json"
        file_path = project.scenarios_dir / filename

        # Update scenario's file path
        scenario.file_path = file_path
        scenario.touch_modified()

        # Serialize and save
        json_data = orjson.dumps(
            scenario.to_dict(),
            option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS,
        )
        file_path.write_bytes(json_data)
        logger.debug(f"Saved scenario to {file_path}")

        return file_path

    @staticmethod
    def load_scenario(file_path: Path) -> Scenario:
        """
        Load a scenario from a JSON file.

        Args:
            file_path: Path to scenario file

        Returns:
            Scenario instance

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is invalid
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Scenario file not found: {file_path}")

        try:
            json_data = file_path.read_bytes()
            data = orjson.loads(json_data)
            scenario = Scenario.from_dict(data)
            scenario.file_path = file_path
            logger.debug(f"Loaded scenario from {file_path}")
            return scenario
        except Exception as e:
            logger.error(f"Failed to load scenario: {e}")
            raise ValueError(f"Invalid scenario file: {e}") from e

    @staticmethod
    def load_all_scenarios(project: Project) -> List[Scenario]:
        """
        Load all scenarios from a project.

        Args:
            project: Project to load scenarios from

        Returns:
            List of Scenario instances
        """
        scenarios = []

        if project.path is None or project.scenarios_dir is None:
            return scenarios

        if not project.scenarios_dir.exists():
            return scenarios

        for file_path in sorted(project.scenarios_dir.glob("*.json")):
            try:
                scenario = ScenarioStorage.load_scenario(file_path)
                scenarios.append(scenario)
            except Exception as e:
                logger.warning(f"Failed to load scenario {file_path}: {e}")

        logger.debug(f"Loaded {len(scenarios)} scenarios from {project.name}")
        return scenarios

    @staticmethod
    def delete_scenario(scenario: Scenario) -> bool:
        """
        Delete a scenario file.

        Args:
            scenario: Scenario to delete

        Returns:
            True if deleted, False if file didn't exist
        """
        if scenario.file_path is None:
            return False

        if not scenario.file_path.exists():
            return False

        scenario.file_path.unlink()
        logger.info(f"Deleted scenario: {scenario.name}")
        return True

    @staticmethod
    def rename_scenario(scenario: Scenario, new_name: str, project: Project) -> Path:
        """
        Rename a scenario (updates both name and filename).

        Args:
            scenario: Scenario to rename
            new_name: New name for the scenario
            project: Parent project

        Returns:
            New file path
        """
        old_path = scenario.file_path

        # Update scenario name
        scenario.name = new_name

        # Save with new name (creates new file)
        new_path = ScenarioStorage.save_scenario(scenario, project)

        # Delete old file if it exists and is different
        if old_path and old_path.exists() and old_path != new_path:
            old_path.unlink()
            logger.debug(f"Removed old scenario file: {old_path}")

        return new_path

    @staticmethod
    def duplicate_scenario(
        scenario: Scenario,
        new_name: str,
        project: Project
    ) -> Scenario:
        """
        Create a copy of a scenario with a new name.

        Args:
            scenario: Scenario to duplicate
            new_name: Name for the new scenario
            project: Parent project

        Returns:
            New Scenario instance
        """
        # Create new scenario from existing
        new_scenario = Scenario.create_new(
            name=new_name,
            project_id=project.id,
            workflow=scenario.workflow.copy() if scenario.workflow else {},
            description=f"Copy of {scenario.name}",
            tags=scenario.tags.copy(),
            variable_values=scenario.variable_values.copy(),
            credential_bindings=scenario.credential_bindings.copy(),
        )

        # Save the new scenario
        ScenarioStorage.save_scenario(new_scenario, project)

        logger.info(f"Duplicated scenario '{scenario.name}' as '{new_name}'")
        return new_scenario

    @staticmethod
    def scenario_exists(scenario_id: str, project: Project) -> bool:
        """
        Check if a scenario with the given ID exists in the project.

        Args:
            scenario_id: Scenario ID to check
            project: Project to search in

        Returns:
            True if scenario exists
        """
        if project.scenarios_dir is None or not project.scenarios_dir.exists():
            return False

        for file_path in project.scenarios_dir.glob("*.json"):
            if file_path.name.startswith(scenario_id):
                return True
        return False

    @staticmethod
    def find_scenario_by_name(name: str, project: Project) -> Optional[Scenario]:
        """
        Find a scenario by name in a project.

        Args:
            name: Scenario name to search for
            project: Project to search in

        Returns:
            Scenario if found, None otherwise
        """
        scenarios = ScenarioStorage.load_all_scenarios(project)
        for scenario in scenarios:
            if scenario.name == name:
                return scenario
        return None
