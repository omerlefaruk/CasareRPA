"""
CasareRPA - Common Workflow Templates.

Provides reusable workflow templates for common automation patterns.
Templates are JSON workflow structures with placeholder values that
can be customized based on user requirements.

Template Format:
    Each template is a WorkflowTemplate dataclass containing:
    - template_id: Unique identifier for the template
    - name: Human-readable template name
    - description: What the template does
    - keywords: Keywords for template matching
    - workflow: Base workflow JSON structure
    - placeholders: Dict of placeholder names to descriptions

Placeholder Syntax:
    Use {{placeholder_name}} in workflow values.
    Example: {"url": "{{target_url}}"} -> {"url": "https://example.com"}
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from casare_rpa.domain.logging import get_domain_logger

logger = get_domain_logger()

# Template IDs
TEMPLATE_WEB_LOGIN = "web_login"
TEMPLATE_WEB_SCRAPING = "web_scraping"
TEMPLATE_FORM_FILLING = "form_filling"
TEMPLATE_FILE_DOWNLOAD = "file_download"
TEMPLATE_API_CALL = "api_call"
TEMPLATE_DESKTOP_CLICK = "desktop_click"


@dataclass
class WorkflowTemplate:
    """
    Reusable workflow template.

    Attributes:
        template_id: Unique identifier
        name: Human-readable name
        description: What this template does
        keywords: Keywords for matching user requests
        workflow: Base workflow JSON structure
        placeholders: Placeholder names with descriptions
        category: Template category (web, desktop, data, etc.)
    """

    template_id: str
    name: str
    description: str
    keywords: list[str]
    workflow: dict[str, Any]
    placeholders: dict[str, str] = field(default_factory=dict)
    category: str = "general"

    def apply_values(self, values: dict[str, Any]) -> dict[str, Any]:
        """
        Apply placeholder values to template.

        Args:
            values: Dict mapping placeholder names to actual values

        Returns:
            Workflow with placeholders replaced
        """
        import json

        workflow_str = json.dumps(self.workflow)

        for placeholder, value in values.items():
            pattern = f"{{{{{placeholder}}}}}"
            if isinstance(value, str):
                workflow_str = workflow_str.replace(pattern, value)
            else:
                # For non-strings, replace the quoted placeholder
                workflow_str = workflow_str.replace(f'"{pattern}"', json.dumps(value))

        return json.loads(workflow_str)

    def get_missing_placeholders(self, values: dict[str, Any]) -> list[str]:
        """Get list of placeholders not provided in values."""
        return [p for p in self.placeholders.keys() if p not in values]

    def to_dict(self) -> dict[str, Any]:
        """Serialize template metadata (without full workflow)."""
        return {
            "template_id": self.template_id,
            "name": self.name,
            "description": self.description,
            "keywords": self.keywords,
            "placeholders": self.placeholders,
            "category": self.category,
        }


class TemplateRegistry:
    """
    Registry of available workflow templates.

    Provides template lookup by ID, keywords, and category.
    """

    def __init__(self) -> None:
        """Initialize empty registry."""
        self._templates: dict[str, WorkflowTemplate] = {}
        self._keyword_index: dict[str, list[str]] = {}

    def register(self, template: WorkflowTemplate) -> None:
        """Register a template."""
        self._templates[template.template_id] = template

        # Index by keywords
        for keyword in template.keywords:
            keyword_lower = keyword.lower()
            if keyword_lower not in self._keyword_index:
                self._keyword_index[keyword_lower] = []
            self._keyword_index[keyword_lower].append(template.template_id)

        logger.debug(f"Template registered: {template.template_id}")

    def get(self, template_id: str) -> WorkflowTemplate | None:
        """Get template by ID."""
        return self._templates.get(template_id)

    def find_by_keywords(self, text: str) -> list[WorkflowTemplate]:
        """Find templates matching keywords in text."""
        text_lower = text.lower()
        matches: dict[str, int] = {}

        for keyword, template_ids in self._keyword_index.items():
            if keyword in text_lower:
                for tid in template_ids:
                    matches[tid] = matches.get(tid, 0) + 1

        # Sort by match count
        sorted_ids = sorted(matches.keys(), key=lambda x: matches[x], reverse=True)
        return [self._templates[tid] for tid in sorted_ids if tid in self._templates]

    def find_by_category(self, category: str) -> list[WorkflowTemplate]:
        """Find templates by category."""
        return [t for t in self._templates.values() if t.category == category]

    def list_all(self) -> list[WorkflowTemplate]:
        """List all templates."""
        return list(self._templates.values())

    def list_ids(self) -> list[str]:
        """List all template IDs."""
        return list(self._templates.keys())


# =============================================================================
# TEMPLATE DEFINITIONS
# =============================================================================


_WEB_LOGIN_TEMPLATE = WorkflowTemplate(
    template_id=TEMPLATE_WEB_LOGIN,
    name="Web Login",
    description="Standard web login flow with username and password",
    keywords=[
        "login",
        "sign in",
        "authenticate",
        "authentication",
        "username password",
    ],
    category="web",
    placeholders={
        "login_url": "URL of the login page",
        "username_selector": "CSS selector for username field",
        "password_selector": "CSS selector for password field",
        "submit_selector": "CSS selector for submit/login button",
        "username": "Username to enter",
        "password": "Password to enter",
    },
    workflow={
        "metadata": {
            "name": "Web Login Workflow",
            "description": "Automated login to {{login_url}}",
            "version": "1.0.0",
        },
        "nodes": {
            "navigate_to_login": {
                "node_id": "navigate_to_login",
                "node_type": "GoToURLNode",
                "config": {
                    "url": "{{login_url}}",
                    "timeout": 30000,
                },
                "position": [0, 0],
            },
            "wait_for_username": {
                "node_id": "wait_for_username",
                "node_type": "WaitForElementNode",
                "config": {
                    "selector": "{{username_selector}}",
                    "timeout": 5000,
                    "state": "visible",
                },
                "position": [400, 0],
            },
            "enter_username": {
                "node_id": "enter_username",
                "node_type": "TypeTextNode",
                "config": {
                    "selector": "{{username_selector}}",
                    "text": "{{username}}",
                    "clear_first": True,
                },
                "position": [800, 0],
            },
            "enter_password": {
                "node_id": "enter_password",
                "node_type": "TypeTextNode",
                "config": {
                    "selector": "{{password_selector}}",
                    "text": "{{password}}",
                    "clear_first": True,
                },
                "position": [1200, 0],
            },
            "click_submit": {
                "node_id": "click_submit",
                "node_type": "ClickElementNode",
                "config": {
                    "selector": "{{submit_selector}}",
                    "timeout": 5000,
                },
                "position": [1600, 0],
            },
        },
        "connections": [
            {
                "source_node": "navigate_to_login",
                "source_port": "exec_out",
                "target_node": "wait_for_username",
                "target_port": "exec_in",
            },
            {
                "source_node": "wait_for_username",
                "source_port": "exec_out",
                "target_node": "enter_username",
                "target_port": "exec_in",
            },
            {
                "source_node": "enter_username",
                "source_port": "exec_out",
                "target_node": "enter_password",
                "target_port": "exec_in",
            },
            {
                "source_node": "enter_password",
                "source_port": "exec_out",
                "target_node": "click_submit",
                "target_port": "exec_in",
            },
        ],
        "variables": {},
        "settings": {
            "stop_on_error": True,
            "timeout": 60,
            "retry_count": 0,
        },
    },
)


_WEB_SCRAPING_TEMPLATE = WorkflowTemplate(
    template_id=TEMPLATE_WEB_SCRAPING,
    name="Web Scraping",
    description="Extract data from a web page",
    keywords=["scrape", "scraping", "extract", "data extraction", "get data", "crawl"],
    category="web",
    placeholders={
        "target_url": "URL of the page to scrape",
        "data_selector": "CSS selector for data elements",
        "output_variable": "Variable name to store extracted data",
    },
    workflow={
        "metadata": {
            "name": "Web Scraping Workflow",
            "description": "Extract data from {{target_url}}",
            "version": "1.0.0",
        },
        "nodes": {
            "navigate_to_page": {
                "node_id": "navigate_to_page",
                "node_type": "GoToURLNode",
                "config": {
                    "url": "{{target_url}}",
                    "timeout": 30000,
                },
                "position": [0, 0],
            },
            "wait_for_content": {
                "node_id": "wait_for_content",
                "node_type": "WaitForElementNode",
                "config": {
                    "selector": "{{data_selector}}",
                    "timeout": 10000,
                    "state": "visible",
                },
                "position": [400, 0],
            },
            "extract_data": {
                "node_id": "extract_data",
                "node_type": "ExtractTextNode",
                "config": {
                    "selector": "{{data_selector}}",
                    "extract_all": True,
                },
                "position": [800, 0],
            },
            "store_data": {
                "node_id": "store_data",
                "node_type": "SetVariableNode",
                "config": {
                    "variable_name": "{{output_variable}}",
                    "value": "{{extracted_text}}",
                },
                "position": [1200, 0],
            },
        },
        "connections": [
            {
                "source_node": "navigate_to_page",
                "source_port": "exec_out",
                "target_node": "wait_for_content",
                "target_port": "exec_in",
            },
            {
                "source_node": "wait_for_content",
                "source_port": "exec_out",
                "target_node": "extract_data",
                "target_port": "exec_in",
            },
            {
                "source_node": "extract_data",
                "source_port": "exec_out",
                "target_node": "store_data",
                "target_port": "exec_in",
            },
            {
                "source_node": "extract_data",
                "source_port": "text",
                "target_node": "store_data",
                "target_port": "value",
            },
        ],
        "variables": {},
        "settings": {
            "stop_on_error": True,
            "timeout": 60,
            "retry_count": 0,
        },
    },
)


_FORM_FILLING_TEMPLATE = WorkflowTemplate(
    template_id=TEMPLATE_FORM_FILLING,
    name="Form Filling",
    description="Fill out a web form",
    keywords=["form", "fill form", "form filling", "submit form", "input fields"],
    category="web",
    placeholders={
        "form_url": "URL of the form page",
        "field_1_selector": "CSS selector for first field",
        "field_1_value": "Value for first field",
        "submit_selector": "CSS selector for submit button",
    },
    workflow={
        "metadata": {
            "name": "Form Filling Workflow",
            "description": "Fill form at {{form_url}}",
            "version": "1.0.0",
        },
        "nodes": {
            "navigate_to_form": {
                "node_id": "navigate_to_form",
                "node_type": "GoToURLNode",
                "config": {
                    "url": "{{form_url}}",
                    "timeout": 30000,
                },
                "position": [0, 0],
            },
            "wait_for_form": {
                "node_id": "wait_for_form",
                "node_type": "WaitForElementNode",
                "config": {
                    "selector": "{{field_1_selector}}",
                    "timeout": 5000,
                    "state": "visible",
                },
                "position": [400, 0],
            },
            "fill_field_1": {
                "node_id": "fill_field_1",
                "node_type": "TypeTextNode",
                "config": {
                    "selector": "{{field_1_selector}}",
                    "text": "{{field_1_value}}",
                    "clear_first": True,
                },
                "position": [800, 0],
            },
            "submit_form": {
                "node_id": "submit_form",
                "node_type": "ClickElementNode",
                "config": {
                    "selector": "{{submit_selector}}",
                    "timeout": 5000,
                },
                "position": [1200, 0],
            },
        },
        "connections": [
            {
                "source_node": "navigate_to_form",
                "source_port": "exec_out",
                "target_node": "wait_for_form",
                "target_port": "exec_in",
            },
            {
                "source_node": "wait_for_form",
                "source_port": "exec_out",
                "target_node": "fill_field_1",
                "target_port": "exec_in",
            },
            {
                "source_node": "fill_field_1",
                "source_port": "exec_out",
                "target_node": "submit_form",
                "target_port": "exec_in",
            },
        ],
        "variables": {},
        "settings": {
            "stop_on_error": True,
            "timeout": 60,
            "retry_count": 0,
        },
    },
)


_FILE_DOWNLOAD_TEMPLATE = WorkflowTemplate(
    template_id=TEMPLATE_FILE_DOWNLOAD,
    name="File Download",
    description="Download a file from the web",
    keywords=["download", "file download", "save file", "download file"],
    category="web",
    placeholders={
        "download_url": "URL of the file to download",
        "save_path": "Local path to save the file",
    },
    workflow={
        "metadata": {
            "name": "File Download Workflow",
            "description": "Download file from {{download_url}}",
            "version": "1.0.0",
        },
        "nodes": {
            "download_file": {
                "node_id": "download_file",
                "node_type": "DownloadFileNode",
                "config": {
                    "url": "{{download_url}}",
                    "save_path": "{{save_path}}",
                    "timeout": 60000,
                },
                "position": [0, 0],
            },
        },
        "connections": [],
        "variables": {},
        "settings": {
            "stop_on_error": True,
            "timeout": 120,
            "retry_count": 1,
        },
    },
)


_API_CALL_TEMPLATE = WorkflowTemplate(
    template_id=TEMPLATE_API_CALL,
    name="API Call",
    description="Make a REST API request",
    keywords=["api", "rest", "http", "request", "api call", "endpoint"],
    category="data",
    placeholders={
        "api_url": "API endpoint URL",
        "http_method": "HTTP method (GET, POST, etc.)",
        "response_variable": "Variable to store response",
    },
    workflow={
        "metadata": {
            "name": "API Call Workflow",
            "description": "Call API at {{api_url}}",
            "version": "1.0.0",
        },
        "nodes": {
            "make_request": {
                "node_id": "make_request",
                "node_type": "HttpRequestNode",
                "config": {
                    "url": "{{api_url}}",
                    "method": "{{http_method}}",
                    "timeout": 30000,
                },
                "position": [0, 0],
            },
            "store_response": {
                "node_id": "store_response",
                "node_type": "SetVariableNode",
                "config": {
                    "variable_name": "{{response_variable}}",
                    "value": "{{response_body}}",
                },
                "position": [400, 0],
            },
        },
        "connections": [
            {
                "source_node": "make_request",
                "source_port": "exec_out",
                "target_node": "store_response",
                "target_port": "exec_in",
            },
            {
                "source_node": "make_request",
                "source_port": "response",
                "target_node": "store_response",
                "target_port": "value",
            },
        ],
        "variables": {},
        "settings": {
            "stop_on_error": True,
            "timeout": 60,
            "retry_count": 1,
        },
    },
)


_DESKTOP_CLICK_TEMPLATE = WorkflowTemplate(
    template_id=TEMPLATE_DESKTOP_CLICK,
    name="Desktop Click",
    description="Click a button or element in a desktop application",
    keywords=["desktop", "click", "button", "application", "window"],
    category="desktop",
    placeholders={
        "app_name": "Name or title of the application window",
        "element_name": "Name or automation ID of the element to click",
    },
    workflow={
        "metadata": {
            "name": "Desktop Click Workflow",
            "description": "Click element in {{app_name}}",
            "version": "1.0.0",
        },
        "nodes": {
            "focus_window": {
                "node_id": "focus_window",
                "node_type": "FocusWindowNode",
                "config": {
                    "window_title": "{{app_name}}",
                    "timeout": 5000,
                },
                "position": [0, 0],
            },
            "click_element": {
                "node_id": "click_element",
                "node_type": "DesktopClickNode",
                "config": {
                    "element_name": "{{element_name}}",
                    "timeout": 5000,
                },
                "position": [400, 0],
            },
        },
        "connections": [
            {
                "source_node": "focus_window",
                "source_port": "exec_out",
                "target_node": "click_element",
                "target_port": "exec_in",
            },
        ],
        "variables": {},
        "settings": {
            "stop_on_error": True,
            "timeout": 30,
            "retry_count": 0,
        },
    },
)


# =============================================================================
# GLOBAL REGISTRY
# =============================================================================

_global_registry: TemplateRegistry | None = None


def get_template_registry() -> TemplateRegistry:
    """Get global template registry (singleton)."""
    global _global_registry

    if _global_registry is None:
        _global_registry = TemplateRegistry()

        # Register all built-in templates
        _global_registry.register(_WEB_LOGIN_TEMPLATE)
        _global_registry.register(_WEB_SCRAPING_TEMPLATE)
        _global_registry.register(_FORM_FILLING_TEMPLATE)
        _global_registry.register(_FILE_DOWNLOAD_TEMPLATE)
        _global_registry.register(_API_CALL_TEMPLATE)
        _global_registry.register(_DESKTOP_CLICK_TEMPLATE)

        logger.debug(
            f"Template registry initialized with {len(_global_registry.list_ids())} templates"
        )

    return _global_registry


def get_template(template_id: str) -> WorkflowTemplate | None:
    """Get template by ID."""
    return get_template_registry().get(template_id)


def get_template_by_keywords(text: str) -> WorkflowTemplate | None:
    """Get best matching template for text."""
    matches = get_template_registry().find_by_keywords(text)
    return matches[0] if matches else None


def list_templates() -> list[dict[str, Any]]:
    """List all available templates (metadata only)."""
    return [t.to_dict() for t in get_template_registry().list_all()]


__all__ = [
    "WorkflowTemplate",
    "TemplateRegistry",
    "get_template",
    "get_template_by_keywords",
    "list_templates",
    "get_template_registry",
    "TEMPLATE_WEB_LOGIN",
    "TEMPLATE_WEB_SCRAPING",
    "TEMPLATE_FORM_FILLING",
    "TEMPLATE_FILE_DOWNLOAD",
    "TEMPLATE_API_CALL",
    "TEMPLATE_DESKTOP_CLICK",
]
