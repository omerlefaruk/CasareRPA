"""
Template Loader Utility

Provides functionality to discover, load, and instantiate workflow templates.
Templates are organized in categories and can be loaded into the GUI or run programmatically.
"""

import os
import importlib.util
import inspect
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass

from loguru import logger


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
                    template_info = self._load_template_info(template_file, category_name)
                    if template_info:
                        templates.append(template_info)
                        logger.debug(f"Discovered template: {category_name}/{template_info.name}")
                except Exception as e:
                    logger.error(f"Failed to load template {template_file}: {e}")
            
            if templates:
                self._templates[category_name] = templates
        
        self._loaded = True
        logger.info(f"Discovered {sum(len(t) for t in self._templates.values())} templates in {len(self._templates)} categories")
        return self._templates
    
    def _load_template_info(self, file_path: Path, category: str) -> Optional[TemplateInfo]:
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
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Extract first docstring
                lines = content.split('\n')
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
            tags=tags
        )
    
    def load_template_function(self, template_info: TemplateInfo) -> Optional[Callable]:
        """
        Load the create function from a template file.
        
        Args:
            template_info: Template information
        
        Returns:
            Create function or None if not found
        """
        if template_info.create_function:
            return template_info.create_function
        
        try:
            # Load module from file
            spec = importlib.util.spec_from_file_location(
                f"template_{template_info.category}_{template_info.file_path.stem}",
                template_info.file_path
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find create function (starts with "create_" and ends with "_workflow")
            for name, obj in inspect.getmembers(module):
                if (callable(obj) and 
                    name.startswith("create_") and 
                    name.endswith("_workflow")):
                    template_info.create_function = obj
                    logger.debug(f"Loaded create function: {name} from {template_info.file_path.name}")
                    return obj
            
            logger.warning(f"No create function found in {template_info.file_path}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to load template function from {template_info.file_path}: {e}")
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
                if (query_lower in template.name.lower() or
                    query_lower in template.description.lower() or
                    any(query_lower in tag for tag in template.tags)):
                    results.append(template)
        
        return results
    
    async def create_workflow_from_template(self, template_info: TemplateInfo, **kwargs) -> Any:
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
            raise ValueError(f"Could not load create function from template: {template_info.name}")
        
        # Check if function is async
        if inspect.iscoroutinefunction(create_func):
            return await create_func(**kwargs)
        else:
            return create_func(**kwargs)


# Global template loader instance
_global_loader: Optional[TemplateLoader] = None


def get_template_loader() -> TemplateLoader:
    """
    Get the global template loader instance.
    
    Returns:
        TemplateLoader instance
    """
    global _global_loader
    if _global_loader is None:
        _global_loader = TemplateLoader()
    return _global_loader
