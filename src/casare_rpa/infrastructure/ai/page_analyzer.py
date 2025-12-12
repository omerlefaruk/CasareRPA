"""
Page Analyzer for extracting structured information from Playwright MCP snapshots.

Parses accessibility tree snapshots to extract forms, buttons, links, inputs,
and other interactive elements for LLM-based workflow generation.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger


@dataclass
class FormField:
    """Represents a form input field."""

    name: str
    selector: str
    field_type: str  # text, password, email, number, etc.
    placeholder: str = ""
    required: bool = False
    label: str = ""
    ref: str = ""  # MCP element reference

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "selector": self.selector,
            "field_type": self.field_type,
            "placeholder": self.placeholder,
            "required": self.required,
            "label": self.label,
            "ref": self.ref,
        }


@dataclass
class FormInfo:
    """Represents a form on the page."""

    selector: str
    action: str = ""
    method: str = "GET"
    fields: List[FormField] = field(default_factory=list)
    submit_button: Optional[Dict[str, str]] = None
    ref: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "selector": self.selector,
            "action": self.action,
            "method": self.method,
            "fields": [f.to_dict() for f in self.fields],
            "submit_button": self.submit_button,
            "ref": self.ref,
        }


@dataclass
class PageContext:
    """
    Structured context extracted from a page snapshot.

    Contains all interactive elements found on the page,
    organized by type for easy consumption by LLM.
    """

    url: str
    title: str
    forms: List[FormInfo] = field(default_factory=list)
    buttons: List[Dict[str, str]] = field(default_factory=list)
    links: List[Dict[str, str]] = field(default_factory=list)
    tables: List[Dict[str, Any]] = field(default_factory=list)
    inputs: List[Dict[str, str]] = field(default_factory=list)  # Standalone inputs
    text_areas: List[Dict[str, str]] = field(default_factory=list)
    dropdowns: List[Dict[str, Any]] = field(default_factory=list)
    checkboxes: List[Dict[str, str]] = field(default_factory=list)
    navigation: List[Dict[str, str]] = field(default_factory=list)
    headings: List[Dict[str, str]] = field(default_factory=list)
    raw_snapshot: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "url": self.url,
            "title": self.title,
            "forms": [f.to_dict() for f in self.forms],
            "buttons": self.buttons,
            "links": self.links,
            "tables": self.tables,
            "inputs": self.inputs,
            "text_areas": self.text_areas,
            "dropdowns": self.dropdowns,
            "checkboxes": self.checkboxes,
            "navigation": self.navigation,
            "headings": self.headings,
        }

    def to_prompt_context(self) -> str:
        """
        Format page context as markdown for LLM prompt injection.

        Returns:
            Markdown-formatted string describing the page structure
        """
        lines = [
            f"### Page: {self.title}",
            f"**URL:** {self.url}",
            "",
        ]

        # Forms section
        if self.forms:
            lines.append("#### Forms")
            for i, form in enumerate(self.forms, 1):
                lines.append(f"**Form {i}:** `{form.selector}` (ref: `{form.ref}`)")
                if form.fields:
                    lines.append("| Field | Selector | Type | Ref |")
                    lines.append("|-------|----------|------|-----|")
                    for f in form.fields:
                        label = f.label or f.name or f.placeholder or "unnamed"
                        lines.append(
                            f"| {label} | `{f.selector}` | {f.field_type} | `{f.ref}` |"
                        )
                if form.submit_button:
                    lines.append(
                        f"- Submit: `{form.submit_button.get('selector', '')}` "
                        f"(ref: `{form.submit_button.get('ref', '')}`)"
                    )
                lines.append("")

        # Buttons section
        if self.buttons:
            lines.append("#### Buttons")
            lines.append("| Text | Selector | Ref |")
            lines.append("|------|----------|-----|")
            for btn in self.buttons[:15]:  # Limit to 15
                text = btn.get("text", "")[:30]
                lines.append(
                    f"| {text} | `{btn.get('selector', '')}` | `{btn.get('ref', '')}` |"
                )
            if len(self.buttons) > 15:
                lines.append(f"*... and {len(self.buttons) - 15} more buttons*")
            lines.append("")

        # Links section
        if self.links:
            lines.append("#### Links")
            lines.append("| Text | Href | Ref |")
            lines.append("|------|------|-----|")
            for link in self.links[:10]:  # Limit to 10
                text = link.get("text", "")[:25]
                href = link.get("href", "")[:40]
                lines.append(f"| {text} | {href} | `{link.get('ref', '')}` |")
            if len(self.links) > 10:
                lines.append(f"*... and {len(self.links) - 10} more links*")
            lines.append("")

        # Standalone inputs (not in forms)
        if self.inputs:
            lines.append("#### Input Fields (Standalone)")
            lines.append("| Label | Selector | Type | Ref |")
            lines.append("|-------|----------|------|-----|")
            for inp in self.inputs[:10]:
                label = inp.get("label", inp.get("placeholder", ""))[:20]
                lines.append(
                    f"| {label} | `{inp.get('selector', '')}` | "
                    f"{inp.get('type', 'text')} | `{inp.get('ref', '')}` |"
                )
            lines.append("")

        # Dropdowns
        if self.dropdowns:
            lines.append("#### Dropdowns")
            for dd in self.dropdowns[:5]:
                options = dd.get("options", [])[:5]
                options_str = ", ".join(f'"{o}"' for o in options)
                lines.append(
                    f"- `{dd.get('selector', '')}` (ref: `{dd.get('ref', '')}`): [{options_str}]"
                )
            lines.append("")

        # Tables
        if self.tables:
            lines.append("#### Tables")
            for i, table in enumerate(self.tables[:3], 1):
                headers = table.get("headers", [])
                lines.append(
                    f"- Table {i}: `{table.get('selector', '')}` "
                    f"(ref: `{table.get('ref', '')}`) - Headers: {headers}"
                )
            lines.append("")

        # Navigation
        if self.navigation:
            lines.append("#### Navigation")
            nav_items = [f"`{n.get('text', '')}`" for n in self.navigation[:8]]
            lines.append(f"- Items: {', '.join(nav_items)}")
            lines.append("")

        return "\n".join(lines)

    def is_empty(self) -> bool:
        """Check if context has any meaningful content."""
        return not any(
            [
                self.forms,
                self.buttons,
                self.links,
                self.inputs,
                self.dropdowns,
                self.tables,
            ]
        )


class PageAnalyzer:
    """
    Analyzes Playwright MCP accessibility snapshots.

    Parses the text-based accessibility tree to extract structured
    information about page elements.
    """

    # Regex patterns for parsing snapshot
    ROLE_PATTERN = re.compile(
        r'^(\s*)- (\w+)(?: "([^"]*)")?(?: \[ref=([^\]]+)\])?:?\s*(.*)$'
    )
    ATTR_PATTERN = re.compile(r'(\w+)="([^"]*)"')

    def __init__(self) -> None:
        """Initialize page analyzer."""
        self._current_form: Optional[FormInfo] = None
        self._form_fields: List[FormField] = []

    def analyze_snapshot(
        self,
        snapshot: str,
        url: str = "",
        title: str = "",
    ) -> PageContext:
        """
        Analyze accessibility snapshot and extract page context.

        Args:
            snapshot: Raw accessibility tree text from browser_snapshot
            url: Page URL
            title: Page title

        Returns:
            PageContext with extracted elements
        """
        logger.debug(f"Analyzing snapshot ({len(snapshot)} chars) for {url}")

        context = PageContext(
            url=url,
            title=title,
            raw_snapshot=snapshot,
        )

        if not snapshot:
            return context

        # Parse line by line
        lines = snapshot.split("\n")
        current_indent = 0
        element_stack: List[Tuple[int, str, str, str]] = []  # (indent, role, name, ref)

        for line in lines:
            parsed = self._parse_line(line)
            if not parsed:
                continue

            indent, role, name, ref, extra = parsed
            role_lower = role.lower()

            # Track element hierarchy
            while element_stack and element_stack[-1][0] >= indent:
                element_stack.pop()
            element_stack.append((indent, role, name, ref))

            # Extract elements based on role
            selector = self._generate_selector(role, name, ref)

            if role_lower == "button":
                context.buttons.append(
                    {
                        "text": name or extra,
                        "selector": selector,
                        "ref": ref,
                    }
                )

            elif role_lower == "link":
                href = self._extract_attr(extra, "href") or ""
                context.links.append(
                    {
                        "text": name or extra,
                        "href": href,
                        "selector": selector,
                        "ref": ref,
                    }
                )

            elif role_lower in ("textbox", "searchbox"):
                field_type = "text"
                if "password" in name.lower() or "password" in extra.lower():
                    field_type = "password"
                elif "email" in name.lower():
                    field_type = "email"
                elif "search" in role_lower:
                    field_type = "search"

                placeholder = self._extract_attr(extra, "placeholder") or ""

                input_info = {
                    "label": name,
                    "selector": selector,
                    "type": field_type,
                    "placeholder": placeholder,
                    "ref": ref,
                }

                # Check if we're inside a form
                in_form = any(s[1].lower() == "form" for s in element_stack[:-1])
                if in_form:
                    self._form_fields.append(
                        FormField(
                            name=name,
                            selector=selector,
                            field_type=field_type,
                            placeholder=placeholder,
                            ref=ref,
                            label=name,
                        )
                    )
                else:
                    context.inputs.append(input_info)

            elif role_lower == "combobox":
                options = self._extract_options(extra)
                context.dropdowns.append(
                    {
                        "label": name,
                        "selector": selector,
                        "ref": ref,
                        "options": options,
                    }
                )

            elif role_lower == "checkbox":
                checked = "checked" in extra.lower()
                context.checkboxes.append(
                    {
                        "label": name,
                        "selector": selector,
                        "ref": ref,
                        "checked": str(checked),
                    }
                )

            elif role_lower == "form":
                # Save previous form if any
                if self._current_form and self._form_fields:
                    self._current_form.fields = self._form_fields.copy()
                    context.forms.append(self._current_form)

                # Start new form
                action = self._extract_attr(extra, "action") or ""
                method = self._extract_attr(extra, "method") or "GET"
                self._current_form = FormInfo(
                    selector=selector,
                    action=action,
                    method=method.upper(),
                    ref=ref,
                )
                self._form_fields = []

            elif role_lower == "table":
                headers = self._extract_table_headers(lines, lines.index(line))
                context.tables.append(
                    {
                        "selector": selector,
                        "ref": ref,
                        "headers": headers,
                    }
                )

            elif role_lower == "navigation":
                nav_items = self._extract_navigation_items(
                    lines, lines.index(line), indent
                )
                context.navigation.extend(nav_items)

            elif role_lower == "heading":
                level = self._extract_heading_level(extra)
                context.headings.append(
                    {
                        "text": name,
                        "level": str(level),
                        "selector": selector,
                        "ref": ref,
                    }
                )

        # Finalize last form
        if self._current_form:
            if self._form_fields:
                self._current_form.fields = self._form_fields.copy()
            context.forms.append(self._current_form)
            self._current_form = None
            self._form_fields = []

        # Find submit buttons for forms
        self._associate_submit_buttons(context)

        logger.debug(
            f"Extracted: {len(context.forms)} forms, {len(context.buttons)} buttons, "
            f"{len(context.links)} links, {len(context.inputs)} inputs"
        )

        return context

    def _parse_line(self, line: str) -> Optional[Tuple[int, str, str, str, str]]:
        """
        Parse a single line from snapshot.

        Returns:
            Tuple of (indent, role, name, ref, extra) or None
        """
        if not line.strip():
            return None

        # Calculate indent
        stripped = line.lstrip()
        indent = len(line) - len(stripped)

        # Try to match role pattern
        match = self.ROLE_PATTERN.match(line)
        if match:
            _, role, name, ref, extra = match.groups()
            return (indent, role, name or "", ref or "", extra or "")

        # Fallback: try simpler parsing
        parts = stripped.split(":", 1)
        if len(parts) >= 1:
            role_part = parts[0].strip("- ")
            # Extract ref if present
            ref_match = re.search(r"\[ref=([^\]]+)\]", role_part)
            ref = ref_match.group(1) if ref_match else ""
            # Extract name (in quotes)
            name_match = re.search(r'"([^"]*)"', role_part)
            name = name_match.group(1) if name_match else ""
            # Extract role (first word)
            role = role_part.split()[0] if role_part else ""
            extra = parts[1].strip() if len(parts) > 1 else ""
            return (indent, role, name, ref, extra)

        return None

    def _generate_selector(self, role: str, name: str, ref: str) -> str:
        """Generate CSS selector from role and name."""
        role_lower = role.lower()

        # Map accessibility roles to CSS selectors
        role_map = {
            "button": "button",
            "link": "a",
            "textbox": "input[type='text']",
            "searchbox": "input[type='search']",
            "checkbox": "input[type='checkbox']",
            "combobox": "select",
            "form": "form",
            "table": "table",
            "heading": "h1, h2, h3, h4, h5, h6",
            "navigation": "nav",
        }

        base = role_map.get(role_lower, role_lower)

        if name:
            # Escape quotes in name
            escaped_name = name.replace('"', '\\"')
            # Create attribute selector based on role
            if role_lower in ("button", "link"):
                return f'{base}:has-text("{escaped_name}")'
            elif role_lower in ("textbox", "searchbox"):
                return f'input[placeholder*="{escaped_name}"], input[name*="{escaped_name.lower()}"]'
            else:
                return f'{base}[aria-label*="{escaped_name}"]'

        # If we have a ref, that's the most reliable identifier
        if ref:
            return f'[data-ref="{ref}"]'

        return base

    def _extract_attr(self, text: str, attr_name: str) -> Optional[str]:
        """Extract attribute value from text."""
        for match in self.ATTR_PATTERN.finditer(text):
            if match.group(1) == attr_name:
                return match.group(2)
        return None

    def _extract_options(self, text: str) -> List[str]:
        """Extract dropdown options from text."""
        options = []
        # Look for option patterns
        option_matches = re.findall(r'option[:\s]*"([^"]*)"', text, re.IGNORECASE)
        options.extend(option_matches)
        return options[:10]  # Limit to 10 options

    def _extract_table_headers(self, lines: List[str], start_idx: int) -> List[str]:
        """Extract table headers from following lines."""
        headers = []
        for i in range(start_idx + 1, min(start_idx + 20, len(lines))):
            line = lines[i]
            if "columnheader" in line.lower() or "rowheader" in line.lower():
                # Extract text in quotes
                match = re.search(r'"([^"]*)"', line)
                if match:
                    headers.append(match.group(1))
            elif line.strip() and not line.strip().startswith("-"):
                break
        return headers[:10]  # Limit to 10 headers

    def _extract_navigation_items(
        self, lines: List[str], start_idx: int, base_indent: int
    ) -> List[Dict[str, str]]:
        """Extract navigation items from following lines."""
        items = []
        for i in range(start_idx + 1, min(start_idx + 30, len(lines))):
            line = lines[i]
            stripped = line.lstrip()
            indent = len(line) - len(stripped)

            if indent <= base_indent:
                break

            if "link" in stripped.lower():
                match = re.search(r'"([^"]*)"', stripped)
                if match:
                    items.append({"text": match.group(1), "type": "link"})

        return items[:10]

    def _extract_heading_level(self, text: str) -> int:
        """Extract heading level from text."""
        match = re.search(r"level[=:\s]*(\d+)", text, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return 1

    def _associate_submit_buttons(self, context: PageContext) -> None:
        """Associate submit buttons with forms."""
        submit_keywords = [
            "submit",
            "login",
            "sign in",
            "register",
            "send",
            "save",
            "continue",
        ]

        for form in context.forms:
            # Look for submit button among all buttons
            for btn in context.buttons:
                text = btn.get("text", "").lower()
                if any(kw in text for kw in submit_keywords):
                    form.submit_button = {
                        "text": btn.get("text", ""),
                        "selector": btn.get("selector", ""),
                        "ref": btn.get("ref", ""),
                    }
                    break


def analyze_page(
    snapshot: str,
    url: str = "",
    title: str = "",
) -> PageContext:
    """
    Convenience function to analyze a page snapshot.

    Args:
        snapshot: Raw accessibility tree text
        url: Page URL
        title: Page title

    Returns:
        PageContext with extracted elements
    """
    analyzer = PageAnalyzer()
    return analyzer.analyze_snapshot(snapshot, url, title)
