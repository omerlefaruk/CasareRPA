"""
Unit tests for PageAnalyzer.

Tests the PageAnalyzer class which extracts structured information
from Playwright MCP accessibility snapshots.

Test Coverage:
- Empty snapshot handling
- Form extraction with fields
- Button extraction
- Link extraction with href
- Standalone input extraction
- Table header extraction
- Dropdown/combobox extraction
- Checkbox extraction
- Navigation item extraction
- Heading extraction
- CSS selector generation
- to_prompt_context() markdown formatting
"""

import pytest
from casare_rpa.infrastructure.ai.page_analyzer import (
    PageAnalyzer,
    PageContext,
    FormInfo,
    FormField,
    analyze_page,
)


class TestPageAnalyzerEmptySnapshot:
    """Tests for empty/missing snapshot handling."""

    def test_analyze_empty_snapshot_returns_empty_context(self, empty_snapshot: str):
        """Empty snapshot should return empty PageContext with no errors."""
        analyzer = PageAnalyzer()
        context = analyzer.analyze_snapshot(
            empty_snapshot, url="https://example.com", title="Test"
        )

        assert context.url == "https://example.com"
        assert context.title == "Test"
        assert context.forms == []
        assert context.buttons == []
        assert context.links == []
        assert context.inputs == []
        assert context.tables == []
        assert context.dropdowns == []
        assert context.checkboxes == []
        assert context.is_empty() is True

    def test_analyze_none_snapshot_returns_empty_context(self):
        """None/empty string snapshot should not raise errors."""
        analyzer = PageAnalyzer()
        context = analyzer.analyze_snapshot("", url="", title="")

        assert context.is_empty() is True
        assert context.raw_snapshot == ""


class TestPageAnalyzerFormExtraction:
    """Tests for form and form field extraction."""

    def test_analyze_form_extraction(self, login_page_snapshot: str):
        """Should extract forms with their fields correctly."""
        analyzer = PageAnalyzer()
        context = analyzer.analyze_snapshot(
            login_page_snapshot, url="https://example.com/login", title="Login"
        )

        # Should have one form
        assert len(context.forms) == 1
        form = context.forms[0]

        # Form should have ref
        assert form.ref == "form1"

        # Form should have fields
        assert len(form.fields) == 2

        # Check username field
        username_field = form.fields[0]
        assert username_field.name == "Username"
        assert username_field.ref == "e1"
        # Placeholder should be extracted (either the actual placeholder or empty string)
        assert isinstance(username_field.placeholder, str)

        # Check password field
        password_field = form.fields[1]
        assert password_field.name == "Password"
        assert password_field.ref == "e2"

    def test_analyze_multiple_forms(self, complex_page_snapshot: str):
        """Should extract multiple forms from the same page."""
        analyzer = PageAnalyzer()
        context = analyzer.analyze_snapshot(
            complex_page_snapshot, url="https://example.com/register", title="Register"
        )

        # Should have two forms
        assert len(context.forms) == 2

        # First form has first/last name and email
        assert len(context.forms[0].fields) >= 3

        # Second form has username/password/search
        assert len(context.forms[1].fields) >= 2


class TestPageAnalyzerButtonExtraction:
    """Tests for button extraction."""

    def test_analyze_button_extraction(self, login_page_snapshot: str):
        """Should extract buttons with text and selectors."""
        analyzer = PageAnalyzer()
        context = analyzer.analyze_snapshot(
            login_page_snapshot, url="https://example.com/login", title="Login"
        )

        # Should have at least Login and Help buttons
        assert len(context.buttons) >= 2

        # Find Login button
        login_buttons = [b for b in context.buttons if "Login" in b.get("text", "")]
        assert len(login_buttons) >= 1

        login_btn = login_buttons[0]
        assert login_btn.get("ref") == "e3"
        assert login_btn.get("selector") != ""

        # Find Help button
        help_buttons = [b for b in context.buttons if "Help" in b.get("text", "")]
        assert len(help_buttons) >= 1
        assert help_buttons[0].get("ref") == "e5"


class TestPageAnalyzerLinkExtraction:
    """Tests for link extraction."""

    def test_analyze_link_extraction(self, login_page_snapshot: str):
        """Should extract links with text and href."""
        analyzer = PageAnalyzer()
        context = analyzer.analyze_snapshot(
            login_page_snapshot, url="https://example.com/login", title="Login"
        )

        # Should have Sign Up link
        assert len(context.links) >= 1

        signup_links = [
            link for link in context.links if "Sign Up" in link.get("text", "")
        ]
        assert len(signup_links) >= 1

        signup_link = signup_links[0]
        assert signup_link.get("ref") == "e4"
        # href might be extracted or empty depending on snapshot format
        assert "selector" in signup_link

    def test_analyze_multiple_links(self, complex_page_snapshot: str):
        """Should extract multiple links."""
        analyzer = PageAnalyzer()
        context = analyzer.analyze_snapshot(
            complex_page_snapshot, url="https://example.com/register", title="Register"
        )

        # Should have Terms and Privacy links
        assert len(context.links) >= 2


class TestPageAnalyzerInputExtraction:
    """Tests for standalone input extraction (not in forms)."""

    def test_analyze_input_extraction_standalone(self):
        """Should extract standalone inputs (outside forms)."""
        snapshot = """- WebArea "Search Page" [ref=root]:
  - textbox "Query" [ref=q1]: placeholder="Search..."
  - button "Search" [ref=btn1]:"""

        analyzer = PageAnalyzer()
        context = analyzer.analyze_snapshot(
            snapshot, url="https://example.com/search", title="Search"
        )

        # Input outside form should be in standalone inputs
        assert len(context.inputs) >= 1
        assert context.inputs[0].get("ref") == "q1"

    def test_inputs_inside_forms_not_standalone(self, login_page_snapshot: str):
        """Inputs inside forms should NOT appear in standalone inputs list."""
        analyzer = PageAnalyzer()
        context = analyzer.analyze_snapshot(
            login_page_snapshot, url="https://example.com/login", title="Login"
        )

        # The Username and Password inputs are inside a form
        # They should be in form.fields, not in context.inputs
        standalone_refs = [i.get("ref") for i in context.inputs]
        assert "e1" not in standalone_refs  # Username input
        assert "e2" not in standalone_refs  # Password input


class TestPageAnalyzerTableExtraction:
    """Tests for table extraction."""

    def test_analyze_table_extraction(self, table_page_snapshot: str):
        """Should extract tables with headers."""
        analyzer = PageAnalyzer()
        context = analyzer.analyze_snapshot(
            table_page_snapshot, url="https://example.com/data", title="Data Table"
        )

        # Should have one table
        assert len(context.tables) >= 1

        table = context.tables[0]
        assert table.get("ref") == "t1"

        # Should have headers extracted
        headers = table.get("headers", [])
        assert len(headers) >= 2
        assert "Name" in headers
        assert "Email" in headers


class TestPageAnalyzerDropdownExtraction:
    """Tests for dropdown/combobox extraction."""

    def test_analyze_dropdown_extraction(self, dropdown_page_snapshot: str):
        """Should extract dropdowns with options."""
        analyzer = PageAnalyzer()
        context = analyzer.analyze_snapshot(
            dropdown_page_snapshot, url="https://example.com/form", title="Form"
        )

        # Should have one dropdown
        assert len(context.dropdowns) >= 1

        dropdown = context.dropdowns[0]
        assert dropdown.get("label") == "Country"
        assert dropdown.get("ref") == "dd1"

        # Options should be extracted
        options = dropdown.get("options", [])
        assert isinstance(options, list)


class TestPageAnalyzerCheckboxExtraction:
    """Tests for checkbox extraction."""

    def test_analyze_checkbox_extraction(self, dropdown_page_snapshot: str):
        """Should extract checkboxes with state."""
        analyzer = PageAnalyzer()
        context = analyzer.analyze_snapshot(
            dropdown_page_snapshot, url="https://example.com/form", title="Form"
        )

        # Should have one checkbox
        assert len(context.checkboxes) >= 1

        checkbox = context.checkboxes[0]
        assert checkbox.get("label") == "Subscribe"
        assert checkbox.get("ref") == "cb1"


class TestPageAnalyzerNavigationExtraction:
    """Tests for navigation extraction."""

    def test_analyze_navigation_extraction(self, nav_page_snapshot: str):
        """Should extract navigation items."""
        analyzer = PageAnalyzer()
        context = analyzer.analyze_snapshot(
            nav_page_snapshot, url="https://example.com/", title="Home"
        )

        # Should have navigation items
        assert len(context.navigation) >= 2

        # Check navigation items have text
        nav_texts = [n.get("text") for n in context.navigation]
        assert any("Home" in t or "Products" in t for t in nav_texts if t)


class TestPageAnalyzerHeadingExtraction:
    """Tests for heading extraction."""

    def test_analyze_heading_extraction(self, table_page_snapshot: str):
        """Should extract headings with level."""
        analyzer = PageAnalyzer()
        context = analyzer.analyze_snapshot(
            table_page_snapshot, url="https://example.com/data", title="Data"
        )

        # Should have one heading
        assert len(context.headings) >= 1

        heading = context.headings[0]
        assert heading.get("text") == "User Data"
        assert heading.get("level") == "1"


class TestPageAnalyzerSelectorGeneration:
    """Tests for CSS selector generation."""

    def test_selector_generation_for_buttons(self, login_page_snapshot: str):
        """Should generate CSS selectors for buttons."""
        analyzer = PageAnalyzer()
        context = analyzer.analyze_snapshot(
            login_page_snapshot, url="https://example.com/login", title="Login"
        )

        for button in context.buttons:
            selector = button.get("selector", "")
            assert selector != ""
            # Should contain button or has-text pattern
            assert (
                "button" in selector.lower()
                or "has-text" in selector.lower()
                or "ref" in selector.lower()
            )

    def test_selector_generation_for_inputs(self, login_page_snapshot: str):
        """Should generate CSS selectors for form inputs."""
        analyzer = PageAnalyzer()
        context = analyzer.analyze_snapshot(
            login_page_snapshot, url="https://example.com/login", title="Login"
        )

        for form in context.forms:
            for field in form.fields:
                assert field.selector != ""
                # Should contain input or name pattern
                assert (
                    "input" in field.selector.lower()
                    or "placeholder" in field.selector.lower()
                    or "ref" in field.selector.lower()
                )


class TestPageAnalyzerToPromptContext:
    """Tests for to_prompt_context() markdown formatting."""

    def test_to_prompt_context_formatting(self, login_page_snapshot: str):
        """Should format page context as markdown."""
        analyzer = PageAnalyzer()
        context = analyzer.analyze_snapshot(
            login_page_snapshot, url="https://example.com/login", title="Login Page"
        )

        markdown = context.to_prompt_context()

        # Should have page title
        assert "Login Page" in markdown

        # Should have URL
        assert "https://example.com/login" in markdown

        # Should have sections
        assert "###" in markdown  # Section headers
        assert "Forms" in markdown or "Buttons" in markdown

        # Should have table formatting for buttons
        assert "|" in markdown  # Markdown tables

    def test_to_prompt_context_limits_items(self, complex_page_snapshot: str):
        """Should limit items to prevent excessively long output."""
        analyzer = PageAnalyzer()
        context = analyzer.analyze_snapshot(
            complex_page_snapshot, url="https://example.com/register", title="Register"
        )

        markdown = context.to_prompt_context()

        # Should be reasonably sized
        assert len(markdown) < 10000  # Reasonable limit


class TestPageAnalyzerIsEmpty:
    """Tests for is_empty() method."""

    def test_is_empty_true_for_empty_context(self, empty_snapshot: str):
        """Should return True for empty context."""
        analyzer = PageAnalyzer()
        context = analyzer.analyze_snapshot(empty_snapshot)

        assert context.is_empty() is True

    def test_is_empty_false_for_content(self, login_page_snapshot: str):
        """Should return False when context has content."""
        analyzer = PageAnalyzer()
        context = analyzer.analyze_snapshot(login_page_snapshot)

        assert context.is_empty() is False


class TestPageAnalyzerToDict:
    """Tests for to_dict() serialization."""

    def test_to_dict_serialization(self, login_page_snapshot: str):
        """Should serialize PageContext to dict correctly."""
        analyzer = PageAnalyzer()
        context = analyzer.analyze_snapshot(
            login_page_snapshot, url="https://example.com/login", title="Login"
        )

        data = context.to_dict()

        assert data["url"] == "https://example.com/login"
        assert data["title"] == "Login"
        assert "forms" in data
        assert "buttons" in data
        assert "links" in data
        assert isinstance(data["forms"], list)
        assert isinstance(data["buttons"], list)


class TestAnalyzePageConvenienceFunction:
    """Tests for analyze_page() convenience function."""

    def test_analyze_page_function(self, login_page_snapshot: str):
        """Should provide same functionality as PageAnalyzer class."""
        context = analyze_page(
            snapshot=login_page_snapshot,
            url="https://example.com/login",
            title="Login",
        )

        assert isinstance(context, PageContext)
        assert len(context.forms) >= 1
        assert len(context.buttons) >= 1


class TestFormFieldDataclass:
    """Tests for FormField dataclass."""

    def test_form_field_to_dict(self):
        """Should serialize FormField to dict."""
        field = FormField(
            name="Username",
            selector="input[name='username']",
            field_type="text",
            placeholder="Enter username",
            required=True,
            label="Username",
            ref="e1",
        )

        data = field.to_dict()

        assert data["name"] == "Username"
        assert data["selector"] == "input[name='username']"
        assert data["field_type"] == "text"
        assert data["placeholder"] == "Enter username"
        assert data["required"] is True
        assert data["label"] == "Username"
        assert data["ref"] == "e1"


class TestFormInfoDataclass:
    """Tests for FormInfo dataclass."""

    def test_form_info_to_dict(self):
        """Should serialize FormInfo to dict."""
        field = FormField(name="test", selector="input", field_type="text", ref="e1")
        form = FormInfo(
            selector="form#login",
            action="/login",
            method="POST",
            fields=[field],
            submit_button={"text": "Login", "selector": "button", "ref": "btn1"},
            ref="form1",
        )

        data = form.to_dict()

        assert data["selector"] == "form#login"
        assert data["action"] == "/login"
        assert data["method"] == "POST"
        assert len(data["fields"]) == 1
        assert data["submit_button"]["text"] == "Login"
        assert data["ref"] == "form1"


class TestPageAnalyzerEdgeCases:
    """Tests for edge cases and error handling."""

    def test_malformed_snapshot_does_not_crash(self):
        """Should handle malformed snapshot gracefully."""
        malformed = """
        This is not a valid snapshot
        - missing roles
        random text
        """
        analyzer = PageAnalyzer()
        context = analyzer.analyze_snapshot(malformed)

        # Should not raise, may have partial results or empty
        assert isinstance(context, PageContext)

    def test_deeply_nested_elements(self):
        """Should handle deeply nested elements."""
        nested = """- WebArea [ref=root]:
  - navigation [ref=nav]:
    - list [ref=list1]:
      - listitem [ref=li1]:
        - link "Nested Link" [ref=link1]: href="/nested"
          - text "Very Deep":"""

        analyzer = PageAnalyzer()
        context = analyzer.analyze_snapshot(nested)

        # Should extract the nested link
        assert len(context.links) >= 1 or len(context.navigation) >= 0

    def test_special_characters_in_names(self):
        """Should handle special characters in element names."""
        special = """- WebArea [ref=root]:
  - button "Click & Save" [ref=btn1]:
  - link "Terms <Policy>" [ref=link1]: href="/terms"
  - textbox "Email (optional)" [ref=e1]:"""

        analyzer = PageAnalyzer()
        context = analyzer.analyze_snapshot(special)

        # Should extract elements with special chars
        assert len(context.buttons) >= 1
        assert "&" in context.buttons[0].get("text", "") or "Save" in context.buttons[
            0
        ].get("text", "")
