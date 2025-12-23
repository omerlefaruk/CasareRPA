"""
CasareRPA - Template Management Use Cases

Application layer use cases for project template operations.
Handles built-in and user templates for quick project creation.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import orjson
from loguru import logger

from casare_rpa.domain.entities.project import (
    CredentialBinding,
    CredentialBindingsFile,
    Project,
    ProjectTemplate,
    Scenario,
    TemplateCategory,
    VariableScope,
    VariablesFile,
    generate_project_id,
    generate_scenario_id,
)
from casare_rpa.domain.entities.project.template import (
    TemplateCredential,
    TemplateVariable,
    generate_template_id,
)
from casare_rpa.domain.entities.variable import Variable
from casare_rpa.infrastructure.persistence.environment_storage import EnvironmentStorage
from casare_rpa.infrastructure.persistence.template_storage import TemplateStorage

# =============================================================================
# Result Types
# =============================================================================


@dataclass
class TemplateResult:
    """Result of a template operation."""

    success: bool
    template: ProjectTemplate | None = None
    error: str | None = None


@dataclass
class TemplateListResult:
    """Result of listing templates."""

    success: bool
    templates: list[ProjectTemplate] = None
    error: str | None = None

    def __post_init__(self):
        if self.templates is None:
            self.templates = []


@dataclass
class ProjectFromTemplateResult:
    """Result of creating project from template."""

    success: bool
    project: Project | None = None
    template: ProjectTemplate | None = None
    error: str | None = None


# =============================================================================
# List Templates Use Case
# =============================================================================


class ListTemplatesUseCase:
    """List all available templates."""

    async def execute(
        self,
        category: TemplateCategory | None = None,
        user_templates_dir: Path | None = None,
    ) -> TemplateListResult:
        """
        List templates.

        Args:
            category: Filter by category (optional)
            user_templates_dir: Directory for user templates

        Returns:
            TemplateListResult with list of templates
        """
        try:
            if category:
                templates = TemplateStorage.get_templates_by_category(category)
            else:
                templates = TemplateStorage.get_all_templates(user_templates_dir)

            # Sort by category, then name
            templates.sort(key=lambda t: (t.category.value, t.name))

            return TemplateListResult(success=True, templates=templates)

        except Exception as e:
            logger.error(f"Failed to list templates: {e}")
            return TemplateListResult(success=False, error=str(e))


# =============================================================================
# Get Template Use Case
# =============================================================================


class GetTemplateUseCase:
    """Get a specific template by ID."""

    async def execute(self, template_id: str) -> TemplateResult:
        """
        Get template by ID.

        Args:
            template_id: Template identifier

        Returns:
            TemplateResult with template or error
        """
        try:
            template = TemplateStorage.load_template(template_id)

            if not template:
                return TemplateResult(
                    success=False,
                    error=f"Template not found: {template_id}",
                )

            return TemplateResult(success=True, template=template)

        except Exception as e:
            logger.error(f"Failed to get template: {e}")
            return TemplateResult(success=False, error=str(e))


# =============================================================================
# Create Project From Template Use Case
# =============================================================================


class CreateProjectFromTemplateUseCase:
    """Create a new project from a template."""

    async def execute(
        self,
        template_id: str,
        project_name: str,
        project_path: Path,
        author: str = "",
        description: str = "",
        create_default_environments: bool = True,
    ) -> ProjectFromTemplateResult:
        """
        Create project from template.

        Args:
            template_id: Template to use
            project_name: Name for new project
            project_path: Path for new project
            author: Project author
            description: Project description (uses template if empty)
            create_default_environments: Whether to create dev/staging/prod

        Returns:
            ProjectFromTemplateResult with created project
        """
        try:
            # Load template
            template = TemplateStorage.load_template(template_id)
            if not template:
                return ProjectFromTemplateResult(
                    success=False,
                    error=f"Template not found: {template_id}",
                )

            # Check path
            if project_path.exists() and any(project_path.iterdir()):
                return ProjectFromTemplateResult(
                    success=False,
                    error=f"Directory not empty: {project_path}",
                )

            # Create project directory structure
            project_path.mkdir(parents=True, exist_ok=True)
            (project_path / "scenarios").mkdir(exist_ok=True)
            (project_path / "environments").mkdir(exist_ok=True)

            # Create project entity
            project = Project(
                id=generate_project_id(),
                name=project_name,
                description=description or template.description,
                author=author or template.author,
                tags=template.tags.copy(),
                settings=template.default_settings,
                template_id=template_id,
            )
            project._path = project_path

            # Create default environments
            if create_default_environments:
                environments = EnvironmentStorage.create_default_environments(
                    project.environments_dir
                )
                project.environment_ids = [e.id for e in environments]
                project.active_environment_id = environments[0].id

            # Create variables from template
            if template.default_variables:
                variables_file = VariablesFile(scope=VariableScope.PROJECT)
                for tmpl_var in template.default_variables:
                    var = Variable(
                        name=tmpl_var.name,
                        type=tmpl_var.data_type,
                        default_value=tmpl_var.default_value,
                        description=tmpl_var.description,
                    )
                    variables_file.set_variable(var)

                # Save variables
                variables_path = project.variables_file
                variables_path.write_bytes(
                    orjson.dumps(variables_file.to_dict(), option=orjson.OPT_INDENT_2)
                )

            # Create credential bindings from template
            if template.default_credentials:
                bindings_file = CredentialBindingsFile()
                for tmpl_cred in template.default_credentials:
                    binding = CredentialBinding(
                        alias=tmpl_cred.alias,
                        vault_path="",  # User needs to configure
                        credential_type=tmpl_cred.credential_type,
                        description=tmpl_cred.description,
                        required=tmpl_cred.required,
                    )
                    bindings_file.set_binding(binding)

                # Save credentials
                creds_path = project.credentials_file
                creds_path.write_bytes(
                    orjson.dumps(bindings_file.to_dict(), option=orjson.OPT_INDENT_2)
                )

            # Create starter workflow from template
            if template.base_workflow:
                scenario = Scenario(
                    id=generate_scenario_id(),
                    name="Main Workflow",
                    project_id=project.id,
                    workflow=template.base_workflow,
                    tags=["template"],
                )

                # Save scenario
                scenario_path = project.scenarios_dir / f"{scenario.id}.json"
                scenario_path.write_bytes(
                    orjson.dumps(scenario.to_dict(), option=orjson.OPT_INDENT_2)
                )

            # Save project.json
            project_file = project.project_file
            project_file.write_bytes(orjson.dumps(project.to_dict(), option=orjson.OPT_INDENT_2))

            # Create .casare_project marker
            marker = project_path / ".casare_project"
            marker.touch()

            logger.info(f"Created project '{project_name}' from template '{template.name}'")
            return ProjectFromTemplateResult(
                success=True,
                project=project,
                template=template,
            )

        except Exception as e:
            logger.error(f"Failed to create project from template: {e}")
            return ProjectFromTemplateResult(success=False, error=str(e))


# =============================================================================
# Save User Template Use Case
# =============================================================================


class SaveUserTemplateUseCase:
    """Save a user-created template."""

    async def execute(
        self,
        template: ProjectTemplate,
        templates_dir: Path,
    ) -> TemplateResult:
        """
        Save user template.

        Args:
            template: Template to save
            templates_dir: Directory for user templates

        Returns:
            TemplateResult with saved template
        """
        try:
            template.is_builtin = False
            template.touch_modified()

            TemplateStorage.save_user_template(template, templates_dir)

            logger.info(f"Saved user template: {template.name}")
            return TemplateResult(success=True, template=template)

        except Exception as e:
            logger.error(f"Failed to save user template: {e}")
            return TemplateResult(success=False, error=str(e))


# =============================================================================
# Delete User Template Use Case
# =============================================================================


class DeleteUserTemplateUseCase:
    """Delete a user-created template."""

    async def execute(
        self,
        template_id: str,
        templates_dir: Path,
    ) -> TemplateResult:
        """
        Delete user template.

        Args:
            template_id: Template to delete
            templates_dir: Directory for user templates

        Returns:
            TemplateResult indicating success
        """
        try:
            deleted = TemplateStorage.delete_user_template(template_id, templates_dir)

            if not deleted:
                return TemplateResult(
                    success=False,
                    error=f"Template not found: {template_id}",
                )

            logger.info(f"Deleted user template: {template_id}")
            return TemplateResult(success=True)

        except Exception as e:
            logger.error(f"Failed to delete user template: {e}")
            return TemplateResult(success=False, error=str(e))


# =============================================================================
# Create Template From Project Use Case
# =============================================================================


class CreateTemplateFromProjectUseCase:
    """Create a template from an existing project."""

    async def execute(
        self,
        project: Project,
        template_name: str,
        category: TemplateCategory = TemplateCategory.CUSTOM,
        description: str = "",
        workflow: dict | None = None,
    ) -> TemplateResult:
        """
        Create template from project.

        Args:
            project: Source project
            template_name: Name for template
            category: Template category
            description: Template description
            workflow: Specific workflow to use (optional)

        Returns:
            TemplateResult with created template
        """
        try:
            # Load project variables
            template_variables = []
            if project.variables_file and project.variables_file.exists():
                var_data = orjson.loads(project.variables_file.read_bytes())
                variables_file = VariablesFile.from_dict(var_data)
                for name, var in variables_file.variables.items():
                    template_variables.append(
                        TemplateVariable(
                            name=var.name,
                            data_type=var.type,  # Variable uses 'type' attribute
                            default_value=var.default_value,
                            description=var.description,
                        )
                    )

            # Load project credentials
            template_credentials = []
            if project.credentials_file and project.credentials_file.exists():
                cred_data = orjson.loads(project.credentials_file.read_bytes())
                creds_file = CredentialBindingsFile.from_dict(cred_data)
                for alias, binding in creds_file.bindings.items():
                    template_credentials.append(
                        TemplateCredential(
                            alias=binding.alias,
                            credential_type=binding.credential_type,
                            description=binding.description,
                            required=binding.required,
                        )
                    )

            # Create template
            template = ProjectTemplate(
                id=generate_template_id(),
                name=template_name,
                description=description or f"Template created from {project.name}",
                category=category,
                tags=project.tags.copy(),
                base_workflow=workflow or {},
                default_variables=template_variables,
                default_credentials=template_credentials,
                default_settings=project.settings,
                author=project.author,
                is_builtin=False,
                is_public=False,
            )

            logger.info(f"Created template from project: {project.name}")
            return TemplateResult(success=True, template=template)

        except Exception as e:
            logger.error(f"Failed to create template from project: {e}")
            return TemplateResult(success=False, error=str(e))


# =============================================================================
# Import .env File Use Case
# =============================================================================


class ImportEnvFileUseCase:
    """Import variables from a .env file."""

    async def execute(
        self,
        env_file_path: Path,
    ) -> "EnvImportResult":
        """
        Import variables from .env file.

        Args:
            env_file_path: Path to .env file

        Returns:
            EnvImportResult with imported variables
        """
        try:
            if not env_file_path.exists():
                return EnvImportResult(
                    success=False,
                    error=f"File not found: {env_file_path}",
                )

            variables = {}
            content = env_file_path.read_text(encoding="utf-8")

            for line in content.splitlines():
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith("#"):
                    continue

                # Parse KEY=value
                if "=" in line:
                    key, _, value = line.partition("=")
                    key = key.strip()
                    value = value.strip()

                    # Remove quotes
                    if (value.startswith('"') and value.endswith('"')) or (
                        value.startswith("'") and value.endswith("'")
                    ):
                        value = value[1:-1]

                    variables[key] = value

            logger.info(f"Imported {len(variables)} variables from {env_file_path}")
            return EnvImportResult(success=True, variables=variables)

        except Exception as e:
            logger.error(f"Failed to import .env file: {e}")
            return EnvImportResult(success=False, error=str(e))


@dataclass
class EnvImportResult:
    """Result of importing .env file."""

    success: bool
    variables: dict[str, str] = None
    error: str | None = None

    def __post_init__(self):
        if self.variables is None:
            self.variables = {}
