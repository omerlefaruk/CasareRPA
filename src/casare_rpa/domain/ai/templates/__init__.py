"""
CasareRPA - Workflow Templates Module.

Provides predefined workflow templates for common automation patterns.
Templates can be selected via intent classification for fast workflow
generation without requiring full LLM calls.

Available Templates:
    - web_login: Standard web login flow
    - web_scraping: Data extraction from web pages
    - form_filling: Form completion automation
    - file_download: File download automation
    - file_upload: File upload automation
    - excel_processing: Excel/spreadsheet operations
    - email_automation: Email sending automation
    - api_call: REST API request automation
    - desktop_automation: Desktop application automation
"""

from casare_rpa.domain.ai.templates.common_templates import (
    WorkflowTemplate,
    TemplateRegistry,
    get_template,
    get_template_by_keywords,
    list_templates,
    get_template_registry,
    # Template IDs
    TEMPLATE_WEB_LOGIN,
    TEMPLATE_WEB_SCRAPING,
    TEMPLATE_FORM_FILLING,
    TEMPLATE_FILE_DOWNLOAD,
    TEMPLATE_API_CALL,
    TEMPLATE_DESKTOP_CLICK,
)

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
