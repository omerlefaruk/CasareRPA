"""
Template Loader Utility

Provides functionality to discover, load, and instantiate workflow templates.
Templates are organized in categories and can be loaded into the GUI or run programmatically.

Security: Templates are sandboxed to only allow importing from approved modules
and are validated before execution.
"""

import importlib.util
import inspect
import ast
import re
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any, Set
from dataclasses import dataclass

from loguru import logger


# Allowed modules that templates can import
ALLOWED_TEMPLATE_MODULES: Set[str] = {
    # Core workflow modules
    "casare_rpa.core",
    "casare_rpa.core.workflow_schema",
    "casare_rpa.core.base_node",
    "casare_rpa.core.types",
    # Node modules
    "casare_rpa.nodes",
    "casare_rpa.nodes.basic_nodes",
    "casare_rpa.nodes.browser_nodes",
    "casare_rpa.nodes.navigation_nodes",
    "casare_rpa.nodes.interaction_nodes",
    "casare_rpa.nodes.data_nodes",
    "casare_rpa.nodes.control_flow_nodes",
    "casare_rpa.nodes.error_handling_nodes",
    "casare_rpa.nodes.data_operation_nodes",
    "casare_rpa.nodes.desktop_nodes",
    # Safe standard library
    "typing",
    "datetime",
    "uuid",
    "json",
    "re",
    "math",
    "collections",
    "dataclasses",
    "enum",
    "functools",
    "itertools",
}

# Dangerous patterns that are not allowed in templates
DANGEROUS_PATTERNS = [
    r"\beval\s*\(",  # eval() function
    r"\bexec\s*\(",  # exec() function
    r"\bcompile\s*\(",  # compile() function
    r"__import__\s*\(",  # __import__() function
    r"\bopen\s*\(",  # open() for file access
    r"\bos\.(system|popen|exec|spawn)",  # OS command execution
    r"\bsubprocess\.",  # subprocess module
    r"\bsocket\.",  # socket module
    r"\brequests\.",  # requests module (use HTTP node instead)
    r"\burllib\.",  # urllib module
    r"\bpickle\.",  # pickle (deserialization attacks)
    r"\bshelve\.",  # shelve module
    r"\bglobals\s*\(\)",  # globals() access
    r"\blocals\s*\(\)",  # locals() access
    r"\bsetattr\s*\(",  # setattr() for attribute modification
    r"\bdelattr\s*\(",  # delattr()
    r"__builtins__",  # builtins access
    r"__code__",  # code object access
    r"__globals__",  # globals access
]


class TemplateValidationError(Exception):
    """Raised when template validation fails."""

    pass


def validate_template_code(file_path: Path) -> List[str]:
    """
    Validate template code for security issues.

    Args:
        file_path: Path to the template file

    Returns:
        List of validation warnings/errors (empty if valid)

    Raises:
        TemplateValidationError: If critical security issues are found
    """
    issues = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        raise TemplateValidationError(f"Cannot read template file: {e}")

    # Check for dangerous patterns
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, content):
            issues.append(f"Dangerous pattern detected: {pattern}")

    # Parse AST to check imports
    try:
        tree = ast.parse(content)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_name = alias.name.split(".")[0]
                    if not _is_allowed_module(alias.name):
                        issues.append(f"Disallowed import: {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    if not _is_allowed_module(node.module):
                        issues.append(f"Disallowed import from: {node.module}")

    except SyntaxError as e:
        issues.append(f"Syntax error in template: {e}")

    if issues:
        logger.warning(f"Template validation issues in {file_path}: {issues}")

    return issues


def _is_allowed_module(module_name: str) -> bool:
    """Check if a module is in the allowed list."""
    # Check exact match
    if module_name in ALLOWED_TEMPLATE_MODULES:
        return True

    # Check if it's a submodule of an allowed module
    for allowed in ALLOWED_TEMPLATE_MODULES:
        if module_name.startswith(allowed + "."):
            return True
        if allowed.startswith(module_name + "."):
            return True

    return False


@dataclass
class TemplateInfo:
    """Information about a workflow template."""

    name: str
    """Display name of the template"""

    category: str
    """Category (basic, control_flow, debugging, automation)"""

    description: str
    """Short description of what the template does"""

    file_path: Path
    """Path to the template file"""

    create_function: Optional[Callable] = None
    """Function that creates the workflow (loaded on demand)"""

    tags: List[str] = None
    """Optional tags for filtering/searching"""

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class TemplateLoader:
    """
    Utility class for loading and managing workflow templates.

    Templates are Python files that contain a `create_*_workflow()` function
    that returns a Workflow instance.
    """

    def __init__(self, templates_dir: Optional[Path] = None):
        """
        Initialize the template loader.

        Args:
            templates_dir: Path to templates directory (defaults to templates/ in project root)
        """
        if templates_dir is None:
            # Default to templates/ directory in project root
            # __file__ is src/casare_rpa/utils/template_loader.py
            # parent = utils/, parent.parent = casare_rpa/, parent.parent.parent = src/
            # We need one more parent to get to project root
            project_root = Path(__file__).parent.parent.parent.parent
            templates_dir = project_root / "templates"

        self.templates_dir = Path(templates_dir)
        self._templates: Dict[str, List[TemplateInfo]] = {}
        self._loaded = False

    def discover_templates(self) -> Dict[str, List[TemplateInfo]]:
        """
        Discover all available templates by scanning the templates directory.

        Returns:
            Dictionary mapping category names to lists of TemplateInfo objects
        """
        if self._loaded:
            return self._templates

        self._templates = {}

        if not self.templates_dir.exists():
            logger.warning(f"Templates directory not found: {self.templates_dir}")
            return self._templates

        # Scan each category subdirectory
        for category_dir in self.templates_dir.iterdir():
            if not category_dir.is_dir():
                continue

            category_name = category_dir.name
            templates = []

            # Scan for Python files in category
            for template_file in category_dir.glob("*.py"):
                if template_file.name.startswith("__"):
                    continue

                try:
                    template_info = self._load_template_info(
                        template_file, category_name
                    )
                    if template_info:
                        templates.append(template_info)
                        logger.debug(
                            f"Discovered template: {category_name}/{template_info.name}"
                        )
                except Exception as e:
                    logger.error(f"Failed to load template {template_file}: {e}")

            if templates:
                self._templates[category_name] = templates

        self._loaded = True
        logger.info(
            f"Discovered {sum(len(t) for t in self._templates.values())} templates in {len(self._templates)} categories"
        )
        return self._templates

    def _load_template_info(
        self, file_path: Path, category: str
    ) -> Optional[TemplateInfo]:
        """
        Load template information from a Python file.

        Args:
            file_path: Path to template file
            category: Category name

        Returns:
            TemplateInfo object or None if not a valid template
        """
        # Extract name from filename
        name = file_path.stem.replace("_", " ").title()

        # Read docstring for description
        description = "No description available"
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

                # Extract first docstring
                lines = content.split("\n")
                in_docstring = False
                docstring_lines = []

                for line in lines:
                    if '"""' in line:
                        if not in_docstring:
                            in_docstring = True
                            # Check if docstring ends on same line
                            if line.count('"""') == 2:
                                docstring_lines.append(line.split('"""')[1])
                                break
                            continue
                        else:
                            break
                    elif in_docstring:
                        docstring_lines.append(line.strip())

                if docstring_lines:
                    # Use first non-empty line as description
                    for line in docstring_lines:
                        if line and not line.startswith("Usage:"):
                            description = line
                            break
        except Exception as e:
            logger.warning(f"Failed to read docstring from {file_path}: {e}")

        # Extract tags from category and filename
        tags = [category]
        filename_lower = file_path.stem.lower()
        if "loop" in filename_lower:
            tags.append("loop")
        if "condition" in filename_lower or "if" in filename_lower:
            tags.append("conditional")
        if "debug" in filename_lower or "breakpoint" in filename_lower:
            tags.append("debug")
        if "error" in filename_lower:
            tags.append("error-handling")
        if "file" in filename_lower:
            tags.append("file-io")
        if "data" in filename_lower:
            tags.append("data")
        if "web" in filename_lower or "scraping" in filename_lower:
            tags.append("web")

        return TemplateInfo(
            name=name,
            category=category,
            description=description,
            file_path=file_path,
            tags=tags,
        )

    def load_template_function(
        self, template_info: TemplateInfo, validate: bool = True
    ) -> Optional[Callable]:
        """
        Load the create function from a template file.

        Args:
            template_info: Template information
            validate: If True, validate template code before loading (default: True)

        Returns:
            Create function or None if not found

        Raises:
            TemplateValidationError: If validation fails and validate=True
        """
        if template_info.create_function:
            return template_info.create_function

        try:
            # Validate template before loading
            if validate:
                issues = validate_template_code(template_info.file_path)
                if issues:
                    error_msg = f"Template validation failed: {'; '.join(issues)}"
                    logger.error(error_msg)
                    raise TemplateValidationError(error_msg)

            # Load module from file
            spec = importlib.util.spec_from_file_location(
                f"template_{template_info.category}_{template_info.file_path.stem}",
                template_info.file_path,
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find create function (starts with "create_" and ends with "_workflow")
            for name, obj in inspect.getmembers(module):
                if (
                    callable(obj)
                    and name.startswith("create_")
                    and name.endswith("_workflow")
                ):
                    template_info.create_function = obj
                    logger.debug(
                        f"Loaded create function: {name} from {template_info.file_path.name}"
                    )
                    return obj

            logger.warning(f"No create function found in {template_info.file_path}")
            return None

        except Exception as e:
            logger.error(
                f"Failed to load template function from {template_info.file_path}: {e}"
            )
            return None

    def get_templates_by_category(self, category: str) -> List[TemplateInfo]:
        """
        Get all templates in a specific category.

        Args:
            category: Category name

        Returns:
            List of TemplateInfo objects
        """
        if not self._loaded:
            self.discover_templates()

        return self._templates.get(category, [])

    def get_all_templates(self) -> List[TemplateInfo]:
        """
        Get all available templates.

        Returns:
            List of all TemplateInfo objects
        """
        if not self._loaded:
            self.discover_templates()

        templates = []
        for category_templates in self._templates.values():
            templates.extend(category_templates)
        return templates

    def get_categories(self) -> List[str]:
        """
        Get list of all available categories.

        Returns:
            List of category names
        """
        if not self._loaded:
            self.discover_templates()

        return list(self._templates.keys())

    def search_templates(self, query: str) -> List[TemplateInfo]:
        """
        Search templates by name, description, or tags.

        Args:
            query: Search query (case-insensitive)

        Returns:
            List of matching TemplateInfo objects
        """
        if not self._loaded:
            self.discover_templates()

        query_lower = query.lower()
        results = []

        for templates in self._templates.values():
            for template in templates:
                # Search in name, description, and tags
                if (
                    query_lower in template.name.lower()
                    or query_lower in template.description.lower()
                    or any(query_lower in tag for tag in template.tags)
                ):
                    results.append(template)

        return results

    async def create_workflow_from_template(
        self, template_info: TemplateInfo, **kwargs
    ) -> Any:
        """
        Create a workflow instance from a template.

        Args:
            template_info: Template information
            **kwargs: Arguments to pass to the create function

        Returns:
            Workflow instance
        """
        create_func = self.load_template_function(template_info)
        if not create_func:
            raise ValueError(
                f"Could not load create function from template: {template_info.name}"
            )

        # Check if function is async
        if inspect.iscoroutinefunction(create_func):
            return await create_func(**kwargs)
        else:
            return create_func(**kwargs)


# Thread-safe singleton holder
from casare_rpa.application.dependency_injection.singleton import Singleton

_template_loader_holder = Singleton(TemplateLoader, name="TemplateLoader")


def get_template_loader() -> TemplateLoader:
    """
    Get the global template loader instance.

    Returns:
        TemplateLoader instance
    """
    return _template_loader_holder.get()


def reset_template_loader() -> None:
    """Reset the template loader instance (for testing)."""
    _template_loader_holder.reset()
